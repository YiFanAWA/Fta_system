#!/usr/bin/env python3
"""Build the active FTA research manifest with a canonical tree hierarchy contract."""

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

V25_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v25.json"
V26_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v26.json"
COMPARISON_JSON = "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/event_scope_tree_contract.py": (
        "event-scope-tree-hierarchy-contract-v1",
        "evaluation_contract",
        "current",
        "Evaluation-only structural tree validator: gate scopes own hierarchy; legacy parent_id is checked, conflicts block without repair.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v3.py": (
        "event-scope-gate-scopes-canonical-prompt-v3",
        "evaluation_prompt",
        "current_not_run",
        "Prepared evaluation-only prompt that emits gate scopes as the sole hierarchy; not submitted to a model in this baseline.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_contract.py": (
        "event-scope-tree-hierarchy-contract-tests-v1",
        "evaluation_contract_tests",
        "current",
        "Covers valid nested OR/AND hierarchy, current v3 blockers, non-repair behavior, and malformed child identifiers.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py": (
        "figure7-v3-qualitative-comparison-builder-v2",
        "evaluation_tool",
        "current",
        "Adds the structural hierarchy contract to the existing offline qualitative comparison; no score or model call.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_model_run_v3_dev.py": (
        "figure7-v3-qualitative-comparison-tests-v2",
        "evaluation_tool_tests",
        "current",
        "Checks that the saved v3 output is structurally blocked and preserved without mutation.",
    ),
    COMPARISON_JSON: (
        "figure7-v3-qualitative-comparison-json-v2",
        "development_comparison_report",
        "current",
        "Offline-only recheck records hierarchy blockers on the seen Dev output; not a human expert assessment or score.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md": (
        "figure7-v3-qualitative-comparison-report-v2",
        "development_comparison_report",
        "current",
        "Human-readable offline comparison states that conflicts block and raw model output is not repaired.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v25.py": (
        "fta-baseline-manifest-v25-builder",
        "reproducibility_tool",
        "historical",
        "Historical v25 snapshot builder; v26 is the active baseline.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v25.py": (
        "fta-baseline-manifest-v25-tests",
        "manifest_regression_tests",
        "historical",
        "Historical tests for the v25 snapshot; v26 adds the structural hierarchy contract.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v26.py": (
        "fta-baseline-manifest-v26-builder",
        "reproducibility_tool",
        "current",
        "Builds active v26 from frozen v25 and rehashes registered artifacts without changing readiness.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v26.py": (
        "fta-baseline-manifest-v26-tests",
        "manifest_regression_tests",
        "current",
        "Verifies hierarchy policy, preserved readiness boundaries, artifact registration, and frozen v25 immutability.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v26-default",
        "validation_tool",
        "current",
        "Validates registered repository paths and hashes; defaults to active manifest v26.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v26-default",
        "validation_tool_tests",
        "current",
        "Covers hash validation and the active v26 repository snapshot.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v25.json": (
        "fta-baseline-manifest-v25-snapshot",
        "historical_baseline_manifest",
        "historical",
        "Immutable historical snapshot; its hashes describe the v25 capture and are not rewritten by v26.",
    ),
    "docs/README.md": (
        "fta-v26-doc-index",
        "current_truth_index",
        "current",
        "Points to active v26 and the fail-closed tree hierarchy contract.",
    ),
    "docs/current-state-audit.md": (
        "fta-v26-current-state-audit",
        "current_state_document",
        "current",
        "Records the structural contract result against the preserved v3 output and keeps readiness false.",
    ),
    "docs/acceptance.md": (
        "fta-v26-acceptance-record",
        "acceptance_document",
        "current",
        "Records positive nested-tree, negative conflict, actual v3, and manifest verification evidence.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v26-candidate-generation-policy",
        "current_fta_policy_document",
        "current",
        "Defines gate scopes as sole hierarchy owner in the evaluation contract; production remains unchanged.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v26-validation-plan-policy",
        "current_validation_plan_document",
        "current",
        "Tracks structural fail-closed hierarchy validation as the next completed bounded repair.",
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
    v25 = _load("evaluation/quality_eval/fta_baseline_manifest_v25.json")
    comparison = _load(COMPARISON_JSON)
    if v25.get("manifest_id") != "candidate_fta_research_baseline_v25":
        raise ValueError("v26 must extend the frozen v25 manifest")
    if comparison.get("summary", {}).get("semantic_tree_status") != "not_accepted_for_fta_preview":
        raise ValueError("v26 requires the existing non-accepted Dev comparison")
    hierarchy = comparison.get("summary", {}).get("tree_hierarchy_contract", {})
    if hierarchy.get("status") != "blocked" or hierarchy.get("output_mutated") is not False:
        raise ValueError("v26 requires a blocked, non-mutating hierarchy contract result")
    if comparison.get("summary", {}).get("quantitative_score") is not None:
        raise ValueError("qualitative Dev comparison must not carry a quantitative score")

    manifest = deepcopy(v25)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v26"
    manifest["baseline_version"] = "v26"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "offline structural hierarchy validation of the saved Figure 7 v3 output using gate scopes as the sole parent-child source"
    )
    manifest["scope"]["excludes"].append(
        "automatic tree repair, model rerun using the prepared v3 prompt, production FTA changes, formal Gold promotion, or readiness promotion"
    )
    manifest["active_baseline"].update({
        "event_scope_model_comparison_status": "qualitative_dev_comparison_and_hierarchy_contract_blocked",
        "event_scope_tree_hierarchy_contract": "event_scope_tree_hierarchy_contract_v1",
        "event_scope_hierarchy_owner": "gate_scopes",
        "event_scope_parent_id_policy": "validate_projection_only_block_conflict_preserve_output",
        "event_scope_prepared_prompt": "event-scope-text-only-tree-v3-gate-scopes-canonical",
        "event_scope_prepared_prompt_status": "not_run",
        "event_scope_model_semantic_acceptance": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_model_post_run_comparison"].update({
        "status": "qualitative_dev_comparison_and_hierarchy_contract_blocked",
        "tree_hierarchy_contract": "event_scope_tree_hierarchy_contract_v1",
        "hierarchy_owner": "gate_scopes",
        "parent_id_policy": "validate_projection_only_block_conflict_preserve_output",
        "hierarchy_contract_blocker_count": hierarchy["blocker_count"],
        "raw_model_output_modified": False,
        "prepared_prompt_submitted": False,
        "semantic_tree_accepted": False,
        "fta_ready": False,
        "production_ready": False,
    })
    inference = manifest["event_scope_model_inference"]
    inference["status"] = "saved_v3_output_rechecked_by_non_mutating_hierarchy_contract_blocked"
    inference["hierarchy_contract_note"] = (
        "Gate scopes are the sole hierarchy authority. Legacy parent_id is checked only as a derived projection; conflicts block the candidate and preserve the saved output. The prepared evaluation prompt was not run."
    )
    manifest["independent_final_validation"]["reason"] = (
        "The only model case remains a seen Development sample with AI-role-reviewed reference labels. The saved v3 output is blocked by the non-mutating hierarchy contract; no score, human-expert conclusion, independent final, or generalization claim is available."
    )
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v25"],
        "current_version": "v26",
        "reason": "v26 registers the gate-scope canonical hierarchy contract and records the saved v3 output as blocked without repair; prompt is prepared but not run; no score or readiness promotion.",
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
        current = V26_PATH.read_text(encoding="utf-8") if V26_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v26 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v26",
            "hierarchy_contract": payload["active_baseline"]["event_scope_tree_hierarchy_contract"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V26_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V26_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
