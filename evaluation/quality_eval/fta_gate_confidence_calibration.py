"""Audit AND/OR confidence evidence without silently fitting a policy."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


GATES = ("AND", "OR", "unknown")
SPLITS = ("calibration", "validation")


def _reviewed_labels(dataset: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, int]]:
    events = dataset.get("events")
    if not isinstance(events, list):
        raise ValueError("gold dataset must contain an events array")
    labels: dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("each gold event must be an object")
        review = event.get("expert_review")
        if not isinstance(review, dict) or review.get("status") != "expert_reviewed":
            continue
        if review.get("child_set_complete") != "complete":
            continue
        decision = review.get("overall_decision")
        gate = event.get("logic_gate")
        if decision == "approve" and gate in {"AND", "OR"}:
            if review.get("logic_gate") != gate:
                raise ValueError("event and expert-review gate labels disagree")
        elif decision == "cannot_determine" and gate == "unknown":
            if review.get("logic_gate") != "unknown":
                raise ValueError("unknown gate label disagrees with expert review")
        else:
            continue
        event_node = event.get("event_node")
        code = event_node.get("fault_code") if isinstance(event_node, dict) else None
        if not isinstance(code, str) or not code:
            raise ValueError("reviewed event is missing event_node.fault_code")
        if code in labels:
            raise ValueError(f"duplicate reviewed fault_code: {code}")
        labels[code] = gate
    support = {gate: sum(label == gate for label in labels.values()) for gate in GATES}
    return labels, support


def _predictions(bundle: Mapping[str, Any] | None) -> dict[str, dict[str, float]]:
    if bundle is None:
        return {}
    rows = bundle.get("predictions")
    if not isinstance(rows, list):
        raise ValueError("prediction artifact must contain a predictions array")
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each prediction must be an object")
        code = row.get("fault_code")
        probabilities = row.get("gate_probabilities")
        if not isinstance(code, str) or not code:
            raise ValueError("prediction is missing fault_code")
        if code in result:
            raise ValueError(f"duplicate prediction for fault_code: {code}")
        if not isinstance(probabilities, dict) or set(probabilities) != set(GATES):
            raise ValueError(f"{code} must have AND, OR, and unknown probabilities")
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
            raise ValueError(f"{code} gate probabilities must sum to 1")
        result[code] = normalized
    return result


def _top_gate(probabilities: Mapping[str, float]) -> tuple[str, float, float]:
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] == ranked[1][1]:
        return "unknown", ranked[0][1], 0.0
    return ranked[0][0], ranked[0][1], ranked[0][1] - ranked[1][1]


def _metrics(
    labels: Mapping[str, str],
    predictions: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    codes = sorted(set(labels) & set(predictions))
    if not codes:
        return {"sample_count": 0, "top1_accuracy": None, "multiclass_brier": None, "log_loss": None}
    correct = 0
    brier_total = 0.0
    log_loss_total = 0.0
    for code in codes:
        probabilities = predictions[code]
        predicted_gate, _, _ = _top_gate(probabilities)
        correct += predicted_gate == labels[code]
        brier_total += sum(
            (probabilities[gate] - float(labels[code] == gate)) ** 2
            for gate in GATES
        )
        log_loss_total -= math.log(max(probabilities[labels[code]], 1e-15))
    return {
        "sample_count": len(codes),
        "top1_accuracy": correct / len(codes),
        "multiclass_brier": brier_total / len(codes),
        "log_loss": log_loss_total / len(codes),
    }


def evaluate_threshold_policy(
    labels: Mapping[str, str],
    predictions: Mapping[str, Mapping[str, float]],
    *,
    minimum_probability: float,
    minimum_margin: float,
) -> dict[str, Any]:
    """Report selective coverage/risk for explicit thresholds; never choose them."""
    for value, name in (
        (minimum_probability, "minimum_probability"),
        (minimum_margin, "minimum_margin"),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{name} must be finite and in [0, 1]")
    codes = sorted(set(labels) & set(predictions))
    accepted = 0
    correct = 0
    for code in codes:
        gate, probability, margin = _top_gate(predictions[code])
        if (
            gate in {"AND", "OR"}
            and probability >= minimum_probability
            and margin >= minimum_margin
        ):
            accepted += 1
            correct += gate == labels[code]
    return {
        "minimum_probability": float(minimum_probability),
        "minimum_margin": float(minimum_margin),
        "sample_count": len(codes),
        "accepted_count": accepted,
        "abstained_count": len(codes) - accepted,
        "coverage": accepted / len(codes) if codes else None,
        "accepted_accuracy": correct / accepted if accepted else None,
        "incorrect_accept_count": accepted - correct,
    }


def audit_calibration_readiness(
    gold_dataset: Mapping[str, Any],
    prediction_bundle: Mapping[str, Any] | None = None,
    split_assignments: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Summarize label/prediction coverage and state why calibration is blocked."""
    labels, support = _reviewed_labels(gold_dataset)
    predictions = _predictions(prediction_bundle)
    assignments = dict(split_assignments or {})
    blockers: list[str] = []
    unknown_split_codes = sorted(set(assignments) - set(labels))
    invalid_split_values = sorted(
        str(value) for value in set(assignments.values()) - set(SPLITS)
    )
    if unknown_split_codes:
        raise ValueError("split assignments reference codes absent from reviewed Gold")
    if invalid_split_values:
        raise ValueError("split assignments must use calibration or validation")
    for gate in GATES:
        if support[gate] == 0:
            blockers.append(f"missing_reviewed_gold_class:{gate}")
    if not predictions:
        blockers.append("model_prediction_artifact_missing")
    missing_predictions = sorted(set(labels) - set(predictions))
    extra_predictions = sorted(set(predictions) - set(labels))
    if missing_predictions:
        blockers.append("reviewed_cases_missing_model_predictions")
    if extra_predictions:
        blockers.append("predictions_without_reviewed_gold")

    split_support: dict[str, dict[str, int]] = {}
    for split in SPLITS:
        codes = [code for code in labels if assignments.get(code) == split]
        split_support[split] = {
            gate: sum(labels[code] == gate for code in codes)
            for gate in GATES
        }
    assigned_splits = set(assignments.values()) & set(SPLITS)
    has_independent_split = assigned_splits == set(SPLITS)
    if not has_independent_split:
        blockers.append("independent_calibration_validation_split_missing")
    else:
        for split in SPLITS:
            for gate in GATES:
                if split_support[split][gate] == 0:
                    blockers.append(f"missing_{gate}_label_in_{split}_split")

    joined = {code: value for code, value in predictions.items() if code in labels}
    if prediction_bundle is not None and joined:
        model_meta = prediction_bundle.get("metadata", {})
        if not isinstance(model_meta, dict) or not model_meta.get("model_id"):
            blockers.append("prediction_model_provenance_missing")
    elif prediction_bundle is None:
        model_meta = {}
    else:
        model_meta = prediction_bundle.get("metadata", {})

    metrics = _metrics(labels, joined)
    split_metrics = {
        split: _metrics(
            {code: label for code, label in labels.items() if assignments.get(code) == split},
            joined,
        )
        for split in SPLITS
    }
    metadata = gold_dataset.get("dataset_info", {})
    return {
        "report_type": "fta_gate_confidence_calibration_readiness",
        "report_version": "v1",
        "calibration_status": "insufficient_evidence" if blockers else "ready_for_threshold_review",
        "gate_policy_selected": False,
        "gold_dataset": {
            "name": metadata.get("name") if isinstance(metadata, dict) else None,
            "version": metadata.get("version") if isinstance(metadata, dict) else None,
            "reviewer": metadata.get("reviewer") if isinstance(metadata, dict) else None,
            "reviewed_case_count": len(labels),
            "class_support": support,
        },
        "prediction_model_id": model_meta.get("model_id") if isinstance(model_meta, dict) else None,
        "prediction_case_count": len(joined),
        "missing_prediction_fault_codes": missing_predictions,
        "unmatched_prediction_fault_codes": extra_predictions,
        "split_class_support": split_support,
        "metrics": metrics,
        "split_metrics": split_metrics,
        "blockers": blockers,
        "threshold_policy_note": (
            "This report audits evidence and metrics only. It never selects a threshold automatically; "
            "the accepted-risk/coverage target must be reviewed separately."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--split-assignments", type=Path)
    args = parser.parse_args(argv)
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    predictions = (
        json.loads(args.predictions.read_text(encoding="utf-8"))
        if args.predictions
        else None
    )
    splits = (
        json.loads(args.split_assignments.read_text(encoding="utf-8"))
        if args.split_assignments
        else None
    )
    print(json.dumps(audit_calibration_readiness(gold, predictions, splits), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
