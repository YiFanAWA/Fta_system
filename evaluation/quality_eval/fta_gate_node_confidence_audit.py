"""Audit confidence evidence for independently scoped FTA gate nodes.

This module evaluates reviewed node labels and paired model probabilities. It
does not fit a calibration transform or select an acceptance threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


GATES = ("AND", "OR", "unknown")
SPLITS = ("calibration", "validation")
DIAGNOSTIC_PROBABILITY_THRESHOLDS = (0.80, 0.90, 0.95, 0.98, 0.99)
DIAGNOSTIC_MINIMUM_MARGIN = 0.50


def _non_empty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _source_anchor(value: Any, name: str) -> tuple[str, int, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    quote = _non_empty(value.get("quote"), f"{name}.quote")
    start, end = value.get("start"), value.get("end")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in (start, end)):
        raise ValueError(f"{name} offsets must be integers")
    if start < 0 or end <= start or end - start != len(quote):
        raise ValueError(f"{name} must use exact Python-string [start,end) offsets")
    return quote, start, end


def _reviewed_nodes(
    dataset: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, int]]:
    rows = dataset.get("gate_nodes")
    if not isinstance(rows, list):
        raise ValueError("review dataset must contain a gate_nodes array")
    if dataset.get("artifact_type") != "fta_gate_node_review_dataset":
        raise ValueError("unexpected gate-node review dataset artifact_type")
    _non_empty(dataset.get("reviewer_provenance"), "reviewer_provenance")
    if not isinstance(dataset.get("reviewer_is_human_expert"), bool):
        raise ValueError("reviewer_is_human_expert must explicitly preserve reviewer type")
    if dataset.get("formal_gold") is not False:
        raise ValueError("this readiness audit accepts review artifacts, not formal Gold")

    reviewed: dict[str, dict[str, Any]] = {}
    status_counts = {"reviewed": 0, "pending": 0, "excluded": 0}
    support = {gate: 0 for gate in GATES}
    seen_source_faults: dict[tuple[str, str], str] = {}

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each gate_nodes item must be an object")
        status = row.get("review_status")
        if status not in status_counts:
            raise ValueError("review_status must be reviewed, pending, or excluded")
        status_counts[status] += 1
        if status != "reviewed":
            continue

        node_id = _non_empty(row.get("gate_node_id"), "gate_node_id")
        if node_id in reviewed:
            raise ValueError(f"duplicate gate_node_id: {node_id}")
        fault_code = _non_empty(row.get("fault_code"), f"{node_id}.fault_code")
        source_cluster_id = _non_empty(row.get("source_cluster_id"), f"{node_id}.source_cluster_id")
        scope_type = _non_empty(row.get("scope_type"), f"{node_id}.scope_type")
        source_sha256 = _non_empty(row.get("source_sha256"), f"{node_id}.source_sha256")
        if len(source_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in source_sha256
        ):
            raise ValueError(f"{node_id}.source_sha256 must be lowercase SHA-256")
        anchor = _source_anchor(row.get("scope_anchor"), f"{node_id}.scope_anchor")
        source_spans = [anchor]
        gate = row.get("gate_label")
        if gate not in GATES:
            raise ValueError(f"{node_id}.gate_label must be AND, OR, or unknown")
        if row.get("scope_appropriate") is not True:
            raise ValueError(f"{node_id} must be explicitly reviewed as a gate scope")
        if row.get("child_set_complete") is not True:
            raise ValueError(f"{node_id} is not an evaluable complete child set")
        children = row.get("children")
        if not isinstance(children, list) or len(children) < 2:
            raise ValueError(f"{node_id} requires at least two reviewed children")
        child_ids: set[str] = set()
        cited_child_spans: set[tuple[str, int, int]] = set()
        for child in children:
            if not isinstance(child, dict):
                raise ValueError(f"{node_id} children must be objects")
            child_id = _non_empty(child.get("child_id"), f"{node_id}.child_id")
            if child_id in child_ids:
                raise ValueError(f"{node_id} has duplicate child_id: {child_id}")
            child_ids.add(child_id)
            evidence = child.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise ValueError(f"{node_id}/{child_id} is missing child evidence")
            for index, span in enumerate(evidence):
                child_anchor = _source_anchor(span, f"{node_id}/{child_id}.evidence[{index}]")
                if child_anchor[1] < anchor[1] or child_anchor[2] > anchor[2]:
                    raise ValueError(
                        f"{node_id}/{child_id} evidence falls outside its scope anchor"
                    )
                if child_anchor in cited_child_spans:
                    raise ValueError(
                        f"{node_id} reuses one child evidence span for multiple children"
                    )
                cited_child_spans.add(child_anchor)
                source_spans.append(child_anchor)
        gate_evidence = row.get("gate_evidence")
        if gate in {"AND", "OR"}:
            if not isinstance(gate_evidence, list) or not gate_evidence:
                raise ValueError(f"{node_id} needs direct gate evidence for {gate}")
            for index, span in enumerate(gate_evidence):
                gate_anchor = _source_anchor(span, f"{node_id}.gate_evidence[{index}]")
                if gate_anchor[1] < anchor[1] or gate_anchor[2] > anchor[2]:
                    raise ValueError(f"{node_id} gate evidence falls outside its scope anchor")
                source_spans.append(gate_anchor)
        elif gate_evidence not in (None, []):
            if not isinstance(gate_evidence, list):
                raise ValueError(f"{node_id}.gate_evidence must be a list")
            for index, span in enumerate(gate_evidence):
                gate_anchor = _source_anchor(span, f"{node_id}.gate_evidence[{index}]")
                if gate_anchor[1] < anchor[1] or gate_anchor[2] > anchor[2]:
                    raise ValueError(f"{node_id} gate evidence falls outside its scope anchor")
                source_spans.append(gate_anchor)

        scope_explanatory_evidence = row.get("scope_explanatory_evidence", [])
        if not isinstance(scope_explanatory_evidence, list):
            raise ValueError(f"{node_id}.scope_explanatory_evidence must be a list")
        for index, span in enumerate(scope_explanatory_evidence):
            if not isinstance(span, dict):
                raise ValueError(
                    f"{node_id}.scope_explanatory_evidence[{index}] must be an object"
                )
            explanatory_anchor = _source_anchor(
                span, f"{node_id}.scope_explanatory_evidence[{index}]"
            )
            # Explanatory evidence may intentionally be contextual and outside
            # the gate span. It is source-checked, but never substitutes for the
            # in-scope direct gate evidence validated above.
            applies_to = span.get("applies_to_child_ids", [])
            if not isinstance(applies_to, list) or any(
                child_id not in child_ids for child_id in applies_to
            ):
                raise ValueError(
                    f"{node_id}.scope_explanatory_evidence[{index}] references an unknown child"
                )
            source_spans.append(explanatory_anchor)

        source_fault_key = (source_sha256, fault_code)
        previous_cluster = seen_source_faults.setdefault(source_fault_key, source_cluster_id)
        if previous_cluster != source_cluster_id:
            raise ValueError("same source/fault pair must use one source_cluster_id")
        reviewed[node_id] = {
            "gate_node_id": node_id,
            "fault_code": fault_code,
            "source_cluster_id": source_cluster_id,
            "scope_type": scope_type,
            "source_sha256": source_sha256,
            "scope_anchor": anchor,
            "source_spans": tuple(source_spans),
            "gate_label": gate,
        }
        support[gate] += 1
    return reviewed, support, status_counts


def _prediction_rows(
    bundle: Mapping[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    if bundle is None:
        return {}, None
    rows = bundle.get("predictions")
    if not isinstance(rows, list):
        raise ValueError("prediction artifact must contain a predictions array")
    metadata = bundle.get("metadata")
    model_id = metadata.get("model_id") if isinstance(metadata, dict) else None
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each prediction must be an object")
        node_id = _non_empty(row.get("gate_node_id"), "prediction.gate_node_id")
        if node_id in result:
            raise ValueError(f"duplicate prediction for gate_node_id: {node_id}")
        probabilities = row.get("gate_probabilities")
        if not isinstance(probabilities, dict) or set(probabilities) != set(GATES):
            raise ValueError(f"{node_id} must have AND, OR, and unknown probabilities")
        normalized: dict[str, float] = {}
        for gate in GATES:
            value = probabilities[gate]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("gate probabilities must be numeric")
            value = float(value)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("gate probabilities must be finite and in [0, 1]")
            normalized[gate] = value
        if abs(sum(normalized.values()) - 1.0) > 1e-6:
            raise ValueError(f"{node_id} gate probabilities must sum to 1")
        result[node_id] = {
            **row,
            "gate_probabilities": normalized,
            "identity": {
                "fault_code": _non_empty(row.get("fault_code"), f"{node_id}.fault_code"),
                "source_cluster_id": _non_empty(
                    row.get("source_cluster_id"),
                    f"{node_id}.source_cluster_id",
                ),
                "scope_type": _non_empty(row.get("scope_type"), f"{node_id}.scope_type"),
                "source_sha256": _non_empty(row.get("source_sha256"), f"{node_id}.source_sha256"),
                "scope_anchor": _source_anchor(row.get("scope_anchor"), f"{node_id}.scope_anchor"),
            },
        }
    return result, model_id if isinstance(model_id, str) and model_id.strip() else None


def _top_gate(probabilities: Mapping[str, float]) -> tuple[str, float, float]:
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] == ranked[1][1]:
        return "unknown", ranked[0][1], 0.0
    return ranked[0][0], ranked[0][1], ranked[0][1] - ranked[1][1]


def _metrics(
    labels: Mapping[str, str],
    predictions: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    node_ids = sorted(set(labels) & set(predictions))
    if not node_ids:
        return {
            "sample_count": 0,
            "top1_accuracy": None,
            "multiclass_brier": None,
            "log_loss": None,
            "top_label_ece_10_bins": None,
            "top_label_calibration_bins": [],
        }
    correct = 0
    brier_total = 0.0
    log_loss_total = 0.0
    bins = [
        {"count": 0, "confidence_sum": 0.0, "correct_count": 0}
        for _ in range(10)
    ]
    for node_id in node_ids:
        probabilities = predictions[node_id]
        predicted_gate, top_probability, _ = _top_gate(probabilities)
        is_correct = predicted_gate == labels[node_id]
        correct += is_correct
        bin_index = min(int(top_probability * 10), 9)
        bins[bin_index]["count"] += 1
        bins[bin_index]["confidence_sum"] += top_probability
        bins[bin_index]["correct_count"] += int(is_correct)
        brier_total += sum(
            (probabilities[gate] - float(labels[node_id] == gate)) ** 2 for gate in GATES
        )
        log_loss_total -= math.log(max(probabilities[labels[node_id]], 1e-15))
    calibration_bins = []
    ece = 0.0
    for index, item in enumerate(bins):
        count = item["count"]
        if not count:
            continue
        confidence = item["confidence_sum"] / count
        accuracy = item["correct_count"] / count
        ece += count / len(node_ids) * abs(accuracy - confidence)
        calibration_bins.append(
            {
                "lower_bound": index / 10,
                "upper_bound": (index + 1) / 10,
                "count": count,
                "mean_confidence": confidence,
                "empirical_accuracy": accuracy,
            }
        )
    return {
        "sample_count": len(node_ids),
        "top1_accuracy": correct / len(node_ids),
        "multiclass_brier": brier_total / len(node_ids),
        "log_loss": log_loss_total / len(node_ids),
        "top_label_ece_10_bins": ece,
        "top_label_calibration_bins": calibration_bins,
    }


def _selective_threshold_metrics(
    node_ids: Sequence[str],
    nodes: Mapping[str, Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, float]],
    *,
    minimum_probability: float,
    minimum_margin: float,
) -> dict[str, Any]:
    """Describe accepted-gate coverage/error for one diagnostic threshold pair."""
    accepted: list[tuple[str, str]] = []
    for node_id in node_ids:
        predicted_gate, probability, margin = _top_gate(predictions[node_id])
        if (
            predicted_gate in {"AND", "OR"}
            and probability >= minimum_probability
            and margin >= minimum_margin
        ):
            accepted.append((node_id, predicted_gate))

    labels = {node_id: nodes[node_id]["gate_label"] for node_id in node_ids}
    correct = sum(predicted_gate == labels[node_id] for node_id, predicted_gate in accepted)
    wrong = len(accepted) - correct
    accepted_gold_unknown = sum(
        labels[node_id] == "unknown" for node_id, _ in accepted
    )
    accepted_gate_type_errors = sum(
        labels[node_id] in {"AND", "OR"} and labels[node_id] != predicted_gate
        for node_id, predicted_gate in accepted
    )
    gold_decisive_count = sum(label in {"AND", "OR"} for label in labels.values())
    gold_unknown_count = sum(label == "unknown" for label in labels.values())
    accepted_gold_decisive = sum(
        labels[node_id] in {"AND", "OR"} for node_id, _ in accepted
    )
    correct_gold_decisive = sum(
        labels[node_id] in {"AND", "OR"} and labels[node_id] == predicted_gate
        for node_id, predicted_gate in accepted
    )
    clusters = {nodes[node_id]["source_cluster_id"] for node_id in node_ids}
    accepted_clusters = {
        nodes[node_id]["source_cluster_id"] for node_id, _ in accepted
    }
    sample_count = len(node_ids)
    accepted_count = len(accepted)

    return {
        "minimum_probability": minimum_probability,
        "minimum_margin": minimum_margin,
        "sample_count": sample_count,
        "source_cluster_count": len(clusters),
        "gold_decisive_count": gold_decisive_count,
        "gold_unknown_count": gold_unknown_count,
        "accepted_count": accepted_count,
        "abstained_count": sample_count - accepted_count,
        "accepted_source_cluster_count": len(accepted_clusters),
        "coverage": accepted_count / sample_count if sample_count else None,
        "decisive_case_coverage": (
            accepted_gold_decisive / gold_decisive_count
            if gold_decisive_count
            else None
        ),
        "correct_decisive_coverage": (
            correct_gold_decisive / gold_decisive_count
            if gold_decisive_count
            else None
        ),
        "accepted_correct_count": correct,
        "accepted_accuracy": correct / accepted_count if accepted_count else None,
        "empirical_risk": wrong / accepted_count if accepted_count else None,
        "wrong_accepted_count": wrong,
        "accepted_gate_type_error_count": accepted_gate_type_errors,
        "accepted_gold_unknown_count": accepted_gold_unknown,
        "gold_unknown_false_accept_rate": (
            accepted_gold_unknown / gold_unknown_count if gold_unknown_count else None
        ),
    }


def _selective_risk_coverage_report(
    nodes: Mapping[str, Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, float]],
    assignments: Mapping[str, str],
    *,
    blockers: Sequence[str],
) -> dict[str, Any]:
    """Create a diagnostic sweep; this function never selects a gate policy."""
    all_node_ids = sorted(set(nodes) & set(predictions))
    groups: dict[str, list[str]] = {
        "all": all_node_ids,
        **{
            split: [
                node_id
                for node_id in all_node_ids
                if assignments.get(nodes[node_id]["source_cluster_id"]) == split
            ]
            for split in SPLITS
        },
    }
    return {
        "status": "descriptive_only",
        "policy_selected": False,
        "thresholds_are_diagnostic_only": True,
        "minimum_margin": DIAGNOSTIC_MINIMUM_MARGIN,
        "probability_thresholds": list(DIAGNOSTIC_PROBABILITY_THRESHOLDS),
        "audit_blockers": list(blockers),
        "risk_definition": (
            "Empirical disagreement rate among accepted AND/OR proposals against the supplied reviewed labels; "
            "not operational risk, future error probability, or calibration evidence."
        ),
        "by_split": {
            group_name: [
                _selective_threshold_metrics(
                    node_ids,
                    nodes,
                    predictions,
                    minimum_probability=threshold,
                    minimum_margin=DIAGNOSTIC_MINIMUM_MARGIN,
                )
                for threshold in DIAGNOSTIC_PROBABILITY_THRESHOLDS
            ]
            for group_name, node_ids in groups.items()
        },
    }


def audit_gate_node_confidence(
    review_dataset: Mapping[str, Any],
    prediction_bundle: Mapping[str, Any] | None = None,
    split_assignments: Mapping[str, str] | None = None,
    source_text_by_sha256: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Check node-level labels, paired predictions, and leakage-safe group splits."""
    nodes, support, status_counts = _reviewed_nodes(review_dataset)
    predictions, model_id = _prediction_rows(prediction_bundle)
    assignments = dict(split_assignments or {})
    source_texts = dict(source_text_by_sha256 or {})
    if any(
        not isinstance(digest, str)
        or not isinstance(source_text, str)
        or hashlib.sha256(source_text.encode("utf-8")).hexdigest() != digest
        for digest, source_text in source_texts.items()
    ):
        raise ValueError("source_text_by_sha256 keys must match SHA-256 of each UTF-8 source")
    blockers: list[str] = []
    clusters = {row["source_cluster_id"] for row in nodes.values()}
    if set(assignments) - clusters:
        raise ValueError("split assignments reference unknown source clusters")
    if set(assignments.values()) - set(SPLITS):
        raise ValueError("split assignments must use calibration or validation")
    for cluster in clusters:
        if cluster not in assignments:
            blockers.append(f"source_cluster_missing_split:{cluster}")

    missing = sorted(set(nodes) - set(predictions))
    extra = sorted(set(predictions) - set(nodes))
    identity_mismatches: list[str] = []
    source_evidence_mismatches: list[str] = []
    missing_sources: list[str] = []
    for node_id, node in nodes.items():
        source_text = source_texts.get(node["source_sha256"])
        if source_text is None:
            missing_sources.append(node_id)
            continue
        if any(
            source_text[start:end] != quote
            for quote, start, end in node["source_spans"]
        ):
            source_evidence_mismatches.append(node_id)
    if missing_sources:
        blockers.append("source_text_for_digest_missing")
    if source_evidence_mismatches:
        blockers.append("source_quote_offset_mismatch")
    for node_id in sorted(set(nodes) & set(predictions)):
        identity_fields = (
            "fault_code",
            "source_cluster_id",
            "scope_type",
            "source_sha256",
            "scope_anchor",
        )
        expected = {key: nodes[node_id][key] for key in identity_fields}
        if predictions[node_id]["identity"] != expected:
            identity_mismatches.append(node_id)
    if missing:
        blockers.append("reviewed_gate_nodes_missing_predictions")
    if extra:
        blockers.append("predictions_without_reviewed_gate_nodes")
    if identity_mismatches:
        blockers.append("prediction_scope_or_source_identity_mismatch")
    if prediction_bundle is None:
        blockers.append("model_prediction_artifact_missing")
    elif not model_id:
        blockers.append("prediction_model_provenance_missing")
    for gate in GATES:
        if support[gate] == 0:
            blockers.append(f"missing_reviewed_gate_node_class:{gate}")

    labels = {node_id: row["gate_label"] for node_id, row in nodes.items()}
    identity_fields = (
        "fault_code",
        "source_cluster_id",
        "scope_type",
        "source_sha256",
        "scope_anchor",
    )
    joined = {}
    for node_id in set(nodes) & set(predictions):
        expected = {key: nodes[node_id][key] for key in identity_fields}
        if predictions[node_id]["identity"] == expected:
            joined[node_id] = predictions[node_id]["gate_probabilities"]

    split_support: dict[str, dict[str, int]] = {}
    split_metrics: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        split_nodes = [
            node_id
            for node_id, row in nodes.items()
            if assignments.get(row["source_cluster_id"]) == split
        ]
        split_support[split] = {
            gate: sum(labels[node_id] == gate for node_id in split_nodes) for gate in GATES
        }
        matched_split_nodes = [
            node_id
            for node_id in joined
            if assignments.get(nodes[node_id]["source_cluster_id"]) == split
        ]
        split_metrics[split] = _metrics(
            {node_id: labels[node_id] for node_id in matched_split_nodes}, joined
        )
        if not any(assignments.get(cluster) == split for cluster in clusters):
            blockers.append(f"empty_{split}_split")
        for gate in GATES:
            if split_support[split][gate] == 0:
                blockers.append(f"missing_{gate}_gate_node_in_{split}_split")

    metrics = _metrics(labels, joined)
    scope_class_support: dict[str, dict[str, int]] = {}
    scope_metrics: dict[str, dict[str, Any]] = {}
    for scope_type in sorted({row["scope_type"] for row in nodes.values()}):
        scope_node_ids = [
            node_id
            for node_id, row in nodes.items()
            if row["scope_type"] == scope_type
        ]
        scope_class_support[scope_type] = {
            gate: sum(labels[node_id] == gate for node_id in scope_node_ids)
            for gate in GATES
        }
        scope_metrics[scope_type] = _metrics(
            {node_id: labels[node_id] for node_id in scope_node_ids}, joined
        )
    return {
        "report_type": "fta_gate_node_confidence_readiness",
        "report_version": "v1",
        "calibration_status": "insufficient_evidence" if blockers else "ready_for_policy_review",
        "gate_policy_selected": False,
        "review_provenance": review_dataset.get("reviewer_provenance"),
        "human_review_claimed": review_dataset.get("reviewer_is_human_expert") is True,
        "review_status_counts": status_counts,
        "reviewed_gate_nodes": len(nodes),
        "unique_faults": len({row["fault_code"] for row in nodes.values()}),
        "independent_source_clusters": len(clusters),
        "class_support": support,
        "scope_type_class_support": scope_class_support,
        "prediction_model_id": model_id,
        "prediction_node_count": len(predictions),
        "missing_prediction_gate_node_ids": missing,
        "unmatched_prediction_gate_node_ids": extra,
        "prediction_identity_mismatch_gate_node_ids": identity_mismatches,
        "missing_source_text_gate_node_ids": missing_sources,
        "source_evidence_mismatch_gate_node_ids": source_evidence_mismatches,
        "split_class_support": split_support,
        "metrics": metrics,
        "split_metrics": split_metrics,
        "scope_type_metrics": scope_metrics,
        "selective_risk_coverage": _selective_risk_coverage_report(
            nodes,
            joined,
            assignments,
            blockers=blockers,
        ),
        "blockers": blockers,
        "note": (
            "This is a node-level evidence/readiness audit, not a calibration fit. "
            "Top-label ECE uses ten fixed confidence bins and is descriptive for small samples; "
            "scope-type class support must be inspected for class/scope confounding. "
            "Even ready_for_policy_review requires a separately reviewed risk/coverage target; "
            "AI review provenance is not represented as human expert sign-off."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--split-assignments", type=Path)
    parser.add_argument("--source-corpus", type=Path)
    args = parser.parse_args(argv)
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    predictions = (
        json.loads(args.predictions.read_text(encoding="utf-8"))
        if args.predictions
        else None
    )
    assignments = (
        json.loads(args.split_assignments.read_text(encoding="utf-8"))
        if args.split_assignments
        else None
    )
    sources: dict[str, str] = {}
    if args.source_corpus:
        with args.source_corpus.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict) or not isinstance(row.get("input_text"), str):
                    raise ValueError(f"source corpus line {line_number} must contain input_text")
                source_text = row["input_text"]
                digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
                existing = sources.setdefault(digest, source_text)
                if existing != source_text:
                    raise ValueError("SHA-256 collision while loading source corpus")
    report = audit_gate_node_confidence(gold, predictions, assignments, sources)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
