#!/usr/bin/env python3
"""Build active FTA research manifest v28 for the completed v4 Dev-only run."""

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

V27_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v27.json"
V28_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v28.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v27.json": (
        "fta-baseline-manifest-v27-snapshot", "historical_baseline_manifest", "historical",
        "Immutable prior active snapshot; v28 records the completed single v4 Development-only request without modifying v27.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v28.py": (
        "fta-baseline-manifest-v28-builder", "reproducibility_tool", "current",
        "Builds v28 from frozen v27, records the actual one-shot v4 run and qualitative assessment, and hashes registered artifacts.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v28.py": (
        "fta-baseline-manifest-v28-tests", "manifest_regression_tests", "current",
        "Protects the exact run boundary, blocked outcome, false readiness, and frozen v27 snapshot.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_model_run_v4_dev.py": (
        "event-scope-v4-qualitative-comparison", "evaluation_report_builder", "current",
        "Offline, non-scoring comparison for the single already-seen NASA Figure 7 Dev run; separates AI-reviewed prose labels from diagram gates.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_model_run_v4_dev.py": (
        "event-scope-v4-qualitative-comparison-tests", "evaluation_report_tests", "current",
        "Checks blocked structure, exact evidence-location observations, no score claims, and reference provenance boundaries.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json": (
        "event-scope-v4-raw-model-run", "evaluation_run_artifact", "immutable_observation",
        "Raw response from the one explicitly authorized DeepSeek request; seen Development only; no Gold or production write.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json": (
        "event-scope-v4-contract-assessment", "evaluation_assessment", "immutable_observation",
        "Saved offline assessment: strict JSON parsed, evidence location 9/9, hierarchy blocked by the one-child S2 scope, readiness false.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.attempt.json": (
        "event-scope-v4-attempt-receipt", "evaluation_attempt_receipt", "immutable_observation",
        "Attempt receipt records exactly one request, zero retries, thinking disabled, and response received.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.json": (
        "event-scope-v4-qualitative-comparison-json", "evaluation_report", "current",
        "Non-scoring qualitative report; no gate accuracy or calibration score is computed.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md": (
        "event-scope-v4-qualitative-comparison-markdown", "evaluation_report", "current",
        "Human-readable summary of the single seen-Dev v4 run and its structural blocker.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v28-default", "validation_tool", "current",
        "Validates registered repository paths and hashes; defaults to active manifest v28.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v28-default", "validation_tool_tests", "current",
        "Covers hash validation and the active v28 repository snapshot.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py": (
        "event-scope-model-runner-v4", "evaluation_tool", "current",
        "Isolated one-shot evaluation runner; fixed thinking disabled, zero retries, strict output/evidence checks, no Gold or production writes.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v4.py": (
        "event-scope-evidence-located-hierarchy-prompt-v4", "evaluation_prompt", "current",
        "Prompt used for the recorded v4 request; separates scope evidence from direct gate logic evidence.",
    ),
    "docs/README.md": (
        "fta-v28-doc-index", "current_truth_index", "current",
        "Points to active manifest v28 and the completed, blocked, non-scoring v4 Development observation.",
    ),
    "docs/current-state-audit.md": (
        "fta-v28-current-state-audit", "current_state_document", "current",
        "Records actual v4 request metadata, structural blocker, evidence location result, and readiness boundaries.",
    ),
    "docs/acceptance.md": (
        "fta-v28-acceptance-record", "acceptance_document", "current",
        "Records actual one-shot run, qualitative comparison, tests, and explicit non-acceptance for FTA Preview.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v28-candidate-generation-policy", "current_fta_policy_document", "current",
        "Records the v4 event-scope Development result; production candidate-tree behavior remains unchanged.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v28-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks v4 as completed one-case Dev observation with a contract blocker; future prompt experiments require separate authorization.",
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


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v27 = json.loads(V27_PATH.read_text(encoding="utf-8"))
    if v27.get("manifest_id") != "candidate_fta_research_baseline_v27":
        raise ValueError("v28 must extend the frozen v27 manifest")
    if v27.get("active_baseline", {}).get("fta_ready") is not False or v27.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v28 must preserve false FTA/production readiness")

    run_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json"
    assessment_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json"
    receipt_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.attempt.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    output = assessment.get("output_assessment", {})
    request = assessment.get("request_observation", {})
    if (request.get("request_count"), request.get("retry_count"), receipt.get("request_count")) != (1, 0, 1):
        raise ValueError("v28 records exactly one API request and zero retries")
    if run.get("request", {}).get("request_count") != request.get("request_count") or run.get("request", {}).get("retry_count") != request.get("retry_count"):
        raise ValueError("run and assessment request observations do not match")
    if receipt.get("run_sha256") != _sha256(run_path) or receipt.get("assessment_sha256") != _sha256(assessment_path):
        raise ValueError("attempt receipt hashes do not match the saved run and assessment")
    if assessment.get("run_artifact") != run_path.relative_to(ROOT).as_posix() or assessment.get("attempt_receipt") != receipt_path.relative_to(ROOT).as_posix():
        raise ValueError("assessment artifact links do not match the v4 run bundle")
    if output.get("strict_json_parsed") is not True or output.get("assessment_status") != "blocked":
        raise ValueError("v28 requires the actual parsed, blocked v4 assessment")
    evidence = output.get("evidence_location_check", {})
    if evidence.get("valid") != 9 or evidence.get("checked") != 9:
        raise ValueError("v28 requires the saved 9/9 literal evidence-location result")
    if len(output.get("structure_contract", {}).get("blockers", [])) != 1:
        raise ValueError("v28 expects the single recorded hierarchy blocker")
    if run.get("case", {}).get("exposure_status") != "seen_development_only":
        raise ValueError("v28 only records the seen-Development packet")
    parsed = run.get("model_output", {}).get("parsed_json", {})
    gates = parsed.get("gates", [])
    gate_counts = {label: sum(gate.get("gate") == label for gate in gates) for label in ("AND", "OR", "unknown")}
    if gate_counts != {"AND": 0, "OR": 0, "unknown": 3}:
        raise ValueError("v28 expects the actual output to contain three unknown gates")

    manifest = deepcopy(v27)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v28"
    manifest["baseline_version"] = "v28"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one completed, explicitly authorized v4 event-scope request on the seen NASA Figure 7 Development packet, with offline structural/evidence assessment and a non-scoring qualitative comparison"
    )
    manifest["scope"]["excludes"].extend([
        "gate accuracy, F1, calibration, or generalization claims from this single seen-Development case",
        "formal Gold promotion, production/API/database writes, or readiness promotion from the v4 observation",
    ])
    manifest["active_baseline"].update({
        "event_scope_prepared_prompt_status": "run_once_seen_dev_blocked",
        "event_scope_model_runner_status": "completed_one_request_blocked",
        "event_scope_model_live_request_count_v4": 1,
        "event_scope_model_live_request_retries_v4": 0,
        "event_scope_model_v4_assessment_status": "blocked",
        "event_scope_model_v4_strict_json_parsed": True,
        "event_scope_model_v4_structure_blocker_count": 1,
        "event_scope_model_v4_evidence_location_valid": evidence["valid"],
        "event_scope_model_v4_evidence_location_checked": evidence["checked"],
        "event_scope_model_v4_gate_labels": gate_counts,
        "event_scope_model_v4_accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_model_v4"] = {
        "status": "completed_seen_development_only_blocked",
        "packet_id": "NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001",
        "source_cluster_id": "NASA_GSFC_LISOCL2_BATTERY_SAFETY_ANALYSIS_1987",
        "exposure_status": "seen_development_only",
        "prompt_version": "event-scope-text-only-tree-v4-located-evidence",
        "prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v4.py",
        "runner_path": "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py",
        "run_path": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json",
        "assessment_path": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json",
        "attempt_receipt_path": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.attempt.json",
        "comparison_report_path": "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md",
        "provider_host": "api.deepseek.com",
        "requested_model": "deepseek-flash",
        "returned_model": request.get("returned_model"),
        "authorized_request_count": 1,
        "configured_max_retries": 0,
        "observed_retry_count": 0,
        "thinking_mode": "disabled",
        "response_format": "json_object",
        "finish_reason": request.get("finish_reason"),
        "strict_json_parsed": output.get("strict_json_parsed"),
        "model_input_includes_gold": False,
        "prompt_sha256": request.get("prompt_sha256"),
        "model_input_sha256": assessment.get("case", {}).get("model_input_sha256"),
        "gold_comparison": "qualitative_non_scoring_only",
        "reference_review_role": "ai_role_review_not_human_expert_gold",
        "semantic_correctness": "not_assessed",
        "structure_status": "blocked",
        "structure_blockers": output.get("structure_contract", {}).get("blockers", []),
        "evidence_location": {"valid": evidence["valid"], "checked": evidence["checked"], "semantic_entailment_assessed": False},
        "predicted_gate_counts": gate_counts,
        "accuracy_or_calibration_claim_allowed": False,
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "reason": "The one parsed response has one hierarchy blocker: S2 contains only one direct child. Literal evidence locations are 9/9, which does not establish semantic entailment. All three emitted gate labels are unknown. This is one seen-Development qualitative observation, not a human-expert score or generalization result.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v27"],
        "current_version": "v28",
        "reason": "v28 records the actual single v4 seen-Development request and its blocked offline assessment; it does not promote Gold, FTA readiness, or production readiness.",
    })

    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id, "kind": kind, "lifecycle": lifecycle, "path": relative_path, "note": note,
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
        current = V28_PATH.read_text(encoding="utf-8") if V28_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v28 differs from generated content\n")
        print(json.dumps({
            "status": "current", "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v28", "run_status": payload["event_scope_model_v4"]["status"],
            "request_count": payload["event_scope_model_v4"]["authorized_request_count"],
            "assessment_status": payload["event_scope_model_v4"]["structure_status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V28_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V28_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
