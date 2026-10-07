#!/usr/bin/env python3
"""Build the v4 FTA research baseline from immutable v3 and current review evidence."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V3_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v3.json"
V4_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v4.json"
OVERLAP_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.json"
GATE_REVIEW_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_gate_node_review_dataset_v6_locator_reconciled_ai_role_review.json"
SPLIT_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_gate_node_source_cluster_splits_v6.json"


UPDATED_NOTES = {
    "evaluation/quality_eval/public_sources/audit_siemens_s120_s150_holdout_overlap_v1.py": (
        "Current reproducible overlap audit tool; defaults to the current S210 gate review v6 and records the supplied review artifact/provenance dynamically."
    ),
    "evaluation/quality_eval/public_sources/test_audit_siemens_s120_s150_holdout_overlap_v1.py": (
        "Regression tests for overlap strata, same-code scope matching, and dynamic review-set provenance."
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v3.py": (
        "Historical v3 manifest builder retained for reproducibility; v4 is the active baseline builder."
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "Validates repository-relative artifact paths and SHA-256 fingerprints; defaults to the active v4 snapshot."
    ),
    "docs/README.md": (
        "Internal source-of-truth index points to the active FTA baseline manifest v4."
    ),
    "docs/candidate-fta-generation-v1.md": (
        "Current candidate FTA narrative; links the active manifest v4 and retains preview-only boundaries."
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "Status ledger for work items 1-4, including v6 provenance/split audit and explicit insufficient-evidence limits."
    ),
}

NEW_ARTIFACTS: tuple[dict[str, str], ...] = (
    {
        "artifact_id": "s120-s150-s210-overlap-audit-v4-json",
        "kind": "source_overlap_audit",
        "lifecycle": "current_overlap_evidence",
        "path": "evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.json",
        "note": "Recomputed against the current 55-node gate review v6; descriptive same-vendor near-transfer evidence only.",
    },
    {
        "artifact_id": "s120-s150-s210-overlap-audit-v4-report",
        "kind": "source_overlap_audit_report",
        "lifecycle": "current_overlap_evidence",
        "path": "evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.md",
        "note": "Reports the current v6 denominators and explicitly avoids independent cross-domain or calibration claims.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v3-snapshot",
        "kind": "baseline_manifest_snapshot",
        "lifecycle": "immutable_superseded_snapshot",
        "path": "evaluation/quality_eval/fta_baseline_manifest_v3.json",
        "note": "Retained unchanged as the previous active baseline; its overlap summary used the v5 54-node review population.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v4-builder",
        "kind": "reproducibility_tool",
        "lifecycle": "current",
        "path": "evaluation/quality_eval/build_fta_baseline_manifest_v4.py",
        "note": "Recomputes gate provenance and source-cluster split summaries from v6 inputs and links the current overlap audit.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v4-tests",
        "kind": "manifest_regression_tests",
        "lifecycle": "current",
        "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v4.py",
        "note": "Checks current review provenance, split leakage, overlap denominators, readiness boundaries, and artifact fingerprints.",
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _upsert_artifact(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def _fault_source_group_count(nodes: list[dict[str, Any]]) -> int:
    parent: dict[tuple[str, str], tuple[str, str]] = {}

    def find(item: tuple[str, str]) -> tuple[str, str]:
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(left: tuple[str, str], right: tuple[str, str]) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for node in nodes:
        union(("fault", node["fault_code"]), ("source", node["source_cluster_id"]))
    return len({find(("fault", node["fault_code"])) for node in nodes})


def _gate_review_and_split_summary() -> tuple[dict[str, Any], dict[str, Any]]:
    review = _load_json(GATE_REVIEW_PATH)
    split_map = _load_json(SPLIT_PATH)
    nodes = review.get("gate_nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("gate review v6 must contain gate_nodes")
    if review.get("reviewer_is_human_expert") is not False:
        raise ValueError("gate review v6 provenance must explicitly say reviewer_is_human_expert=false")
    if review.get("formal_gold") is not False:
        raise ValueError("gate review v6 must remain explicitly non-Gold")

    reviewed = [node for node in nodes if node.get("review_status") == "reviewed"]
    class_counts = Counter(node.get("gate_label") for node in reviewed)
    if set(class_counts) - {"AND", "OR", "unknown"}:
        raise ValueError("reviewed gate labels contain unsupported values")
    reviewer_provenance_counts = Counter(
        node["reviewer_provenance"]
        for node in reviewed
        if isinstance(node.get("reviewer_provenance"), str) and node["reviewer_provenance"].strip()
    )
    if sum(reviewer_provenance_counts.values()) != len(reviewed):
        raise ValueError("each reviewed gate node must declare reviewer provenance")

    by_split: dict[str, dict[str, Any]] = {
        split_name: {"gate_counts": Counter(), "fault_codes": set(), "source_clusters": set(), "node_count": 0}
        for split_name in ("calibration", "validation")
    }
    fault_splits: dict[str, set[str]] = defaultdict(set)
    cluster_splits: dict[str, set[str]] = defaultdict(set)
    for node in reviewed:
        cluster_id = node.get("source_cluster_id")
        fault_code = node.get("fault_code")
        if not isinstance(cluster_id, str) or cluster_id not in split_map:
            raise ValueError(f"reviewed gate node has no source-cluster split: {node.get('gate_node_id')}")
        if not isinstance(fault_code, str) or not fault_code.strip():
            raise ValueError(f"reviewed gate node has no fault_code: {node.get('gate_node_id')}")
        split_name = split_map[cluster_id]
        if split_name not in by_split:
            raise ValueError(f"unsupported source-cluster split: {split_name}")
        bucket = by_split[split_name]
        bucket["node_count"] += 1
        bucket["gate_counts"][node["gate_label"]] += 1
        bucket["fault_codes"].add(fault_code)
        bucket["source_clusters"].add(cluster_id)
        fault_splits[fault_code].add(split_name)
        cluster_splits[cluster_id].add(split_name)

    used_clusters = {node["source_cluster_id"] for node in reviewed}
    if used_clusters != set(split_map):
        raise ValueError("source-cluster split map and reviewed v6 population do not match exactly")

    split_support = {
        split_name: {
            "gate_nodes": bucket["node_count"],
            "fault_codes": len(bucket["fault_codes"]),
            "source_clusters": len(bucket["source_clusters"]),
            "gate_counts": dict(sorted(bucket["gate_counts"].items())),
        }
        for split_name, bucket in by_split.items()
    }
    split_summary = {
        "source_clusters": len(used_clusters),
        "fault_source_groups": _fault_source_group_count(reviewed),
        "cross_split_fault_code_count": sum(len(splits) > 1 for splits in fault_splits.values()),
        "cross_split_source_cluster_count": sum(len(splits) > 1 for splits in cluster_splits.values()),
        "split_class_support": split_support,
        "calibration_status": "insufficient_evidence",
        "calibration_limit_reasons": [
            "gate-node labels are user-authorized AI-role review, not human expert Gold",
            "named human logic Gold has six events and zero AND examples",
            "the validation subset is small and is descriptive only",
            "calibration and validation are within the S210 source, not an independent source validation",
        ],
        "independent_source_validation": False,
    }
    gate_summary = {
        "nodes": len(nodes),
        "reviewed": len(reviewed),
        "pending": sum(node.get("review_status") == "pending" for node in nodes),
        "and": class_counts.get("AND", 0),
        "or": class_counts.get("OR", 0),
        "unknown": class_counts.get("unknown", 0),
        "class_counts": {"AND": class_counts.get("AND", 0), "OR": class_counts.get("OR", 0), "unknown": class_counts.get("unknown", 0)},
        "reviewer_is_human_expert": False,
        "formal_gold": False,
        "reviewer_provenance_counts": dict(sorted(reviewer_provenance_counts.items())),
        "provenance": "user-authorized AI role review; not human expert Gold or calibration truth",
    }
    expected = review.get("summary", {}).get("class_counts_reviewed_only")
    if expected != gate_summary["class_counts"]:
        raise ValueError("gate review v6 declared class counts do not match its reviewed rows")
    expected_groups = review.get("summary", {}).get("fault_and_source_split_group_count")
    if expected_groups != split_summary["fault_source_groups"]:
        raise ValueError("gate review v6 declared fault/source groups do not match its reviewed rows")
    return gate_summary, split_summary


def _current_overlap_summary() -> dict[str, Any]:
    report = _load_json(OVERLAP_PATH)
    sources = report.get("sources", {})
    gate_source = sources.get("s210_gate_node_review", {})
    expected_gate_name = GATE_REVIEW_PATH.name
    if gate_source.get("artifact_name") != expected_gate_name:
        raise ValueError("overlap report is not bound to the active v6 gate review artifact")
    if gate_source.get("sha256") != sha256_file(GATE_REVIEW_PATH):
        raise ValueError("overlap report gate review hash is stale")
    if gate_source.get("reviewer_is_human_expert") is not False:
        raise ValueError("overlap report must preserve non-human review provenance")

    summary = report["summary"]
    gate_count = summary["s210_reviewed_gate_nodes"]
    same_code_count = summary["s210_reviewed_gate_nodes_with_same_fault_code_in_s120"]
    exact_scope_count = summary["s210_reviewed_gate_nodes_with_same_code_and_exact_scope_anchor_text_in_s120"]
    return {
        "audit_artifact": OVERLAP_PATH.relative_to(ROOT).as_posix(),
        "s120_s150_records": sources["s120_s150_holdout_v2"]["record_count"],
        "s120_s150_unique_fault_codes": sources["s120_s150_holdout_v2"]["unique_fault_code_count"],
        "s210_records": sources["s210_public_corpus_v1"]["record_count"],
        "shared_fault_codes": summary["unique_fault_code_intersection_s120_s210"],
        "s120_s150_records_with_shared_fault_code": summary["s120_records_with_s210_fault_code"],
        "s210_gate_review_artifact": expected_gate_name,
        "s210_gate_nodes": gate_count,
        "gate_nodes_with_same_code_in_s120_s150": same_code_count,
        "scope_quotes_exactly_repeated_among_same_code_nodes": exact_scope_count,
        "overall_exact_scope_quote_overlap_ratio": f"{exact_scope_count}/{gate_count}",
        "conditional_exact_scope_quote_overlap_ratio": f"{exact_scope_count}/{same_code_count}",
        "classification": "same-vendor cross-manual/version near-transfer; not independent cross-domain holdout",
        "calibration_claim": "insufficient_evidence; this single S120/S150 source cluster does not support calibration",
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    original = _load_json(V3_PATH)
    manifest = deepcopy(original)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v4"
    manifest["baseline_version"] = "v4"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["supersedes_manifest"] = {
        "manifest_id": original["manifest_id"],
        "path": V3_PATH.relative_to(ROOT).as_posix(),
        "reason": "Rebinds the overlap audit to the current v6 review population, recomputes source-cluster split support, and explicitly records insufficient calibration and independent-source evidence.",
    }

    manifest["scope"]["includes"].append(
        "v6 gate-review provenance, source-cluster split integrity, and corrected S120/S150 near-transfer audit"
    )

    gate_summary, split_summary = _gate_review_and_split_summary()
    manifest["label_and_evaluation_scope"]["gate_node_v6"].update(gate_summary)
    manifest["label_and_evaluation_scope"]["gate_node_split_v6"].update(split_summary)
    manifest["s120_s150_overlap_audit"] = _current_overlap_summary()

    artifacts = manifest["artifacts"]
    for artifact in artifacts:
        path = ROOT / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest artifact is missing: {artifact['path']}")
        artifact["sha256"] = sha256_file(path)
        if artifact["path"] in UPDATED_NOTES:
            artifact["note"] = UPDATED_NOTES[artifact["path"]]
        if artifact["path"] == "evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v3_2026-09-27.json":
            artifact["lifecycle"] = "historical_superseded_evidence"
            artifact["note"] = "Historical audit of the superseded v5 54-node review set; not the active v6 overlap denominator."
        if artifact["path"] == "evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v3_2026-09-27.md":
            artifact["lifecycle"] = "historical_superseded_evidence"
            artifact["note"] = "Historical report of v5 54-node scope overlap; retained unchanged for audit history."
        if artifact["path"] == "evaluation/quality_eval/build_fta_baseline_manifest_v3.py":
            artifact["lifecycle"] = "superseded_historical_tool"

    for addition in NEW_ARTIFACTS:
        path = ROOT / addition["path"]
        if not path.is_file():
            raise FileNotFoundError(f"new manifest artifact is missing: {addition['path']}")
        _upsert_artifact(artifacts, {**addition, "sha256": sha256_file(path)})

    manifest["superseded"].append(
        {
            "artifact_family": "s120_s150_s210_overlap_audit",
            "superseded_versions": ["v3"],
            "current_version": "v4",
            "reason": "v3 audited the v5 54-node population; v4 recomputes against the current v6 55-node review set and records the correct 34/55 and 34/53 denominators.",
        }
    )
    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v3"],
            "current_version": "v4",
            "reason": "v3 remains an unchanged historical snapshot; v4 records current v6 provenance/split evidence and the corrected overlap audit.",
        }
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic snapshot regeneration")
    parser.add_argument("--check", action="store_true", help="compare generated content without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V4_PATH.read_text(encoding="utf-8") if V4_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v4 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"])}, ensure_ascii=False))
        return 0
    V4_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V4_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
