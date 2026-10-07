#!/usr/bin/env python3
"""Build the active FTA research manifest after the v3 qualitative Dev comparison."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V24_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v24.json"
V25_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v25.json"
COMPARISON_JSON = "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json"
COMPARISON_MD = "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py": (
        "figure7-v3-qualitative-comparison-builder",
        "evaluation_tool",
        "current",
        "Creates a bounded qualitative comparison against text-authorized labels; validates packet/hash identity and literal source quote matching, without computing a score.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_model_run_v3_dev.py": (
        "figure7-v3-qualitative-comparison-tests",
        "evaluation_tool_tests",
        "current",
        "Regression checks that the Dev comparison identifies topology/scope mismatches, keeps diagram labels separate, and does not promote readiness.",
    ),
    COMPARISON_JSON: (
        "figure7-v3-qualitative-comparison-json",
        "development_comparison_report",
        "current",
        "Post-run qualitative error analysis; AI engineering review, not a human expert assessment or an accuracy score.",
    ),
    COMPARISON_MD: (
        "figure7-v3-qualitative-comparison-report",
        "development_comparison_report",
        "current",
        "Human-readable qualitative report documenting tree topology and gate-scope mismatches in the one seen Dev output.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v24.py": (
        "fta-baseline-manifest-v24-builder",
        "reproducibility_tool",
        "historical",
        "Historical builder for the v24 structural/quote-only snapshot.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v24.py": (
        "fta-baseline-manifest-v24-tests",
        "manifest_regression_tests",
        "historical",
        "Historical tests for the v24 request facts and readiness boundary.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v25.py": (
        "fta-baseline-manifest-v25-builder",
        "reproducibility_tool",
        "current",
        "Builds v25 from v24, registering the bounded qualitative comparison without treating it as formal Gold or a score.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v25.py": (
        "fta-baseline-manifest-v25-tests",
        "manifest_regression_tests",
        "current",
        "Verifies comparison status, retained development-only limits, and unchanged readiness flags.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v25-default",
        "validation_tool",
        "current",
        "Validates registered repository paths and hashes; defaults to active manifest v25.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v25-default",
        "validation_tool_tests",
        "current",
        "Covers hash validation and the active v25 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v25-doc-index",
        "current_truth_index",
        "current",
        "Points to the active v25 baseline and the qualitative finding that the single Dev tree is not semantically accepted.",
    ),
    "docs/current-state-audit.md": (
        "fta-v25-current-state-audit",
        "current_state_document",
        "current",
        "Records the qualitative topology/scope findings alongside the successful JSON and literal quote checks.",
    ),
    "docs/acceptance.md": (
        "fta-v25-acceptance-record",
        "acceptance_document",
        "current",
        "Records the exact offline comparison and focused validations, with no quantitative or readiness claim.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v25-candidate-generation-policy",
        "current_fta_policy_document",
        "current",
        "Documents why the v3 seen-Dev output is not accepted as a semantically valid tree.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v25-validation-plan-policy",
        "current_validation_plan_document",
        "current",
        "Records qualitative Dev failure analysis and next bounded engineering step.",
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


def _load(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return value


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v24 = _load("evaluation/quality_eval/fta_baseline_manifest_v24.json")
    comparison = _load(COMPARISON_JSON)
    if v24.get("manifest_id") != "candidate_fta_research_baseline_v24":
        raise ValueError("v25 must extend the frozen v24 manifest")
    if v24.get("event_scope_model_inference", {}).get("request_count") != 3:
        raise ValueError("v24 must retain the three bounded model attempts")
    if comparison.get("summary", {}).get("semantic_tree_status") != "not_accepted_for_fta_preview":
        raise ValueError("v25 requires the recorded semantic non-acceptance finding")
    if comparison.get("summary", {}).get("quantitative_score") is not None:
        raise ValueError("qualitative Dev comparison must not carry a quantitative score")
    if comparison.get("case", {}).get("exposure_status") != "seen_development_only":
        raise ValueError("v25 comparison must remain seen Development-only")

    manifest = deepcopy(v24)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v25"
    manifest["baseline_version"] = "v25"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one offline qualitative comparison of the completed v3 Figure 7 Dev output against text-authorized AI-role-reviewed labels; no score"
    )
    manifest["scope"]["excludes"].append(
        "human-expert approval, formal Gold promotion, quantitative accuracy/F1/calibration, or independent generalization inferred from the qualitative Dev comparison"
    )
    manifest["active_baseline"].update({
        "event_scope_model_comparison": COMPARISON_JSON,
        "event_scope_model_comparison_status": "qualitative_dev_comparison_complete_tree_not_accepted",
        "event_scope_model_semantic_acceptance": False,
    })
    manifest["event_scope_model_post_run_comparison"] = {
        "status": "qualitative_dev_comparison_complete_tree_not_accepted",
        "report_json": COMPARISON_JSON,
        "report_markdown": COMPARISON_MD,
        "scoring_performed": False,
        "reference_is_human_expert_gold": False,
        "diagram_gate_labels_used_as_text_gold": False,
        "semantic_tree_accepted": False,
        "fta_ready": False,
        "production_ready": False,
    }
    inference = manifest["event_scope_model_inference"]
    inference["status"] = "v3_completed_json_quotes_checked_qualitative_comparison_found_scope_and_topology_mismatches"
    inference["scope_note"] = (
        "v3 returned parseable JSON and its emitted quotes match the input, but offline qualitative comparison against AI-role-reviewed text labels found tree topology and scope mismatches. No quantitative score, human expert conclusion, or generalization claim is made."
    )
    inference["controlled_attempt_v3"]["gold_comparison"] = "qualitative_non_scoring_comparison_performed"
    inference["controlled_attempt_v3"]["semantic_correctness"] = "qualitative_review_found_mismatches_not_accepted"
    manifest["independent_final_validation"].update({
        "reason": "The only model case is a seen Development sample. The v3 response is parseable and its quotes match the input, but qualitative comparison found topology/scope mismatches; the reference is AI-role-reviewed rather than human-expert Gold. No score or independent generalization conclusion is available."
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v24"],
        "current_version": "v25",
        "reason": "v25 adds a qualitative post-run comparison and records that the v3 candidate topology/scope is not accepted; it does not score accuracy, promote Gold, create an independent Final, write production data, or promote readiness.",
    })

    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    repo_root = ROOT.resolve(strict=True)
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
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
        current = V25_PATH.read_text(encoding="utf-8") if V25_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v25 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v25",
            "semantic_tree_accepted": payload["event_scope_model_post_run_comparison"]["semantic_tree_accepted"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V25_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V25_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
