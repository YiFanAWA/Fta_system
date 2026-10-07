#!/usr/bin/env python3
"""Build v15 with an explicit contract/boundary-only regression scope."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V14_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v14.json"
V15_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v15.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v14.json": (
        "fta-baseline-manifest-v14-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v14 snapshot; the v15 manifest narrows regression claims without changing its historical contents.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v15.py": (
        "fta-baseline-manifest-v15-builder", "reproducibility_tool", "current",
        "Builds v15 from v14 and records the audited scope of the seen-case contract/boundary suite.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v15.py": (
        "fta-baseline-manifest-v15-tests", "manifest_regression_tests", "current",
        "Checks the regression classification, fixture hashes, unchanged v14 snapshot, and readiness boundaries.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v15-default", "validation_tool", "current",
        "Validates repository paths and hashes; defaults to active v15.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v15-default", "validation_tool_tests", "current",
        "Validates active v15 and general path/hash failure cases.",
    ),
    "evaluation/quality_eval/public_sources/probe_fta_gate_diagram_development_v1.py": (
        "fta-gate-diagram-development-probe-v15", "development_probe", "current",
        "Checks development source clusters against the active v15 seen-case regression allocation.",
    ),
    "evaluation/quality_eval/public_sources/test_fta_gate_diagram_development_v1.py": (
        "fta-gate-diagram-development-tests-v15", "development_fixture_tests", "current",
        "Checks development provenance, label isolation, and non-overlap with active v15 regression clusters.",
    ),
    "docs/README.md": (
        "fta-v15-doc-index", "current_truth_index", "current", "Points to active FTA baseline v15.",
    ),
    "docs/current-state-audit.md": (
        "fta-v15-current-state-audit", "current_state_document", "current",
        "Records the regression-scope audit and keeps independent Final uncreated.",
    ),
    "docs/acceptance.md": (
        "fta-v15-acceptance-record", "acceptance_document", "current",
        "Records fresh regression-scope audit commands and their evidence boundaries.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v15-candidate-generation-policy", "candidate_fta_policy_document", "current",
        "Points current candidate FTA research status to v15 without changing Preview-only limits.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v15-validation-plan-policy", "validation_plan_document", "current",
        "Distinguishes fixture/contract regression from model behavior validation and preserves the Final gate.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def _classify_regression_suite(manifest: dict[str, Any]) -> dict[str, Any]:
    suite = manifest.pop("behavior_regression_suite", None)
    if not isinstance(suite, dict):
        raise ValueError("v14 must contain the frozen seen-case suite")
    cases = suite.get("cases")
    clusters = suite.get("source_clusters")
    datasets = suite.get("dataset_suites")
    if not isinstance(cases, list) or len(cases) != 36:
        raise ValueError("the audited suite must contain exactly 36 frozen cases")
    if len({row.get("gate_node_id") for row in cases if isinstance(row, dict)}) != 36:
        raise ValueError("the frozen suite must contain 36 unique gate node ids")
    if not isinstance(clusters, list) or len(clusters) != 15:
        raise ValueError("the frozen suite must retain exactly 15 source clusters")
    if not isinstance(datasets, list) or sum(item.get("sample_count", 0) for item in datasets) != 36:
        raise ValueError("dataset fixture counts must account for all 36 cases")

    expected_labels = {"AND": 9, "OR": 15, "unknown": 12}
    actual_labels: dict[str, int] = {}
    for row in cases:
        label = row.get("expected_gate")
        actual_labels[label] = actual_labels.get(label, 0) + 1
    if actual_labels != expected_labels or suite.get("label_counts") != expected_labels:
        raise ValueError("frozen case label distribution changed")

    for item in datasets:
        relative = item.get("dataset_path")
        if not isinstance(relative, str):
            raise ValueError("each fixture suite needs a dataset path")
        path = (ROOT / relative).resolve(strict=True)
        if not path.is_relative_to(ROOT.resolve(strict=True)):
            raise ValueError(f"fixture path escapes repository: {relative}")
        if _sha256(path) != item.get("dataset_sha256"):
            raise ValueError(f"fixture hash mismatch: {relative}")
        for field in ("probe_script_path", "test_file_path"):
            target = item.get(field)
            if not isinstance(target, str) or not (ROOT / target).is_file():
                raise ValueError(f"fixture suite has a missing {field}: {target}")

    suite["legacy_suite_id"] = suite.get("suite_id")
    suite["suite_id"] = "fta_gate_contract_boundary_regression_v1"
    suite["display_name"] = "Seen-case fixture, contract, and evidence-boundary regression v1"
    suite["status"] = "frozen_seen_case_contract_boundary_regression"
    suite["purpose"] = (
        "Protect known fixture provenance, evidence scope, prompt-input isolation, response/probe contracts, "
        "and abstention boundaries; this suite is not a current-model accuracy evaluation."
    )
    suite["verification_scope"] = {
        "classification": "fixture_contract_and_boundary_regression",
        "offline_tests_call_current_model": False,
        "offline_probe_test_doubles": True,
        "checks": [
            "fixture identity, source and evidence provenance",
            "model-visible input excludes labels and source/gate cues where required",
            "response parsing, probe aggregation, and declared abstention invariants using deterministic test doubles",
        ],
        "does_not_check": [
            "current provider/model predictions on all 36 cases",
            "current-model gate accuracy, calibration, or generalization",
        ],
        "accuracy_claim_allowed": False,
        "independent_final_validation_status": "not_created",
    }
    return suite


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V14_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v14":
        raise ValueError("v15 must extend the frozen v14 manifest snapshot")

    manifest = deepcopy(previous)
    suite = _classify_regression_suite(manifest)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v15"
    manifest["baseline_version"] = "v15"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "classify the 36 previously explored gate cases as fixture/contract/evidence-boundary regression only; no current-model accuracy claim"
    )
    manifest["scope"]["excludes"].append(
        "treating fixture and test-double passes as live model behavior, calibration, or independent Final evidence"
    )
    manifest["active_baseline"]["seen_case_contract_boundary_regression"] = suite["suite_id"]
    manifest["seen_case_regression_suite"] = suite
    manifest["development_gate_suite"]["overlap_with_seen_case_regression"] = manifest[
        "development_gate_suite"
    ].pop("overlap_with_seen_behavior_regression", False)
    allocation = manifest["source_cluster_allocation"]
    allocation["seen_case_contract_boundary_regression_cluster_count"] = allocation.pop(
        "seen_behavior_regression_cluster_count"
    )
    allocation["allocation_rule"] = allocation["allocation_rule"].replace(
        "seen behavior regression", "seen-case contract/boundary regression"
    )
    manifest["regression_scope_audit"] = {
        "date": "2026-09-28",
        "finding": "The 36-case inventory is reproducible as fixture and contract/boundary checks, but the offline unit tests do not call the current model.",
        "test_evidence": "The probe aggregation tests use deterministic test doubles; remaining checks validate fixture, provenance, prompt isolation, and response contracts.",
        "reclassification": "seen_case_contract_boundary_regression",
        "current_model_accuracy_evaluated": False,
        "model_replay_authorized_or_run": False,
        "independent_final_validation": "not_created",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v14"],
        "current_version": "v15",
        "reason": "v15 corrects the active evaluation-scope description; v14 and earlier manifest snapshots are not rewritten.",
    })

    root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })

    for artifact in manifest["artifacts"]:
        if artifact.get("kind") == "behavior_regression_input":
            artifact["kind"] = "contract_boundary_regression_input"
            artifact["lifecycle"] = "seen_case_contract_boundary_regression_input_not_final_test"
            artifact["classification"] = "fixture_contract_and_boundary_regression"

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        artifact["sha256"] = _sha256(target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic regeneration")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V15_PATH.read_text(encoding="utf-8") if V15_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v15 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v15",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V15_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V15_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
