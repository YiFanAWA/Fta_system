#!/usr/bin/env python3
"""Build active FTA research manifest v30 for the single v5 Development run."""

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

V29_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v29.json"
V30_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v30.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v29.json": (
        "fta-baseline-manifest-v29-snapshot", "historical_baseline_manifest", "historical",
        "Immutable prior snapshot recording v5 as prepared but not run; v30 records the one subsequently authorized request.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v30.py": (
        "fta-baseline-manifest-v30-builder", "reproducibility_tool", "current",
        "Builds v30 from frozen v29, validates the actual one-shot v5 run bundle, and hashes registered artifacts.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v30.py": (
        "fta-baseline-manifest-v30-tests", "manifest_regression_tests", "current",
        "Protects the no-retry run facts, blocked contract assessment, immutable v29 snapshot, and false readiness.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v5.py": (
        "event-scope-model-runner-v5", "evaluation_tool", "current",
        "One-shot, explicit-authorization, no-retry runner for prompt v5; writes isolated run, assessment, and attempt receipt.",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v5.py": (
        "event-scope-model-runner-v5-tests", "evaluation_tool_tests", "current",
        "Checks offline preflight, authorization guard, one-call/no-retry behavior, and no hidden reasoning persistence.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json": (
        "event-scope-v5-raw-model-run", "evaluation_run_artifact", "immutable_observation",
        "Raw visible response from exactly one explicitly authorized DeepSeek request; seen Development only.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v5_2026-09-29.json": (
        "event-scope-v5-contract-assessment", "evaluation_assessment", "immutable_observation",
        "Offline assessment: strict JSON, 15/15 literal evidence locations, tree contract blocked, semantic entailment unassessed.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.attempt.json": (
        "event-scope-v5-attempt-receipt", "evaluation_attempt_receipt", "immutable_observation",
        "Records one authorized attempt, zero retries, prompt/input hashes, and run/assessment hashes.",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_model_run_v5_dev_comparison_2026-09-29.md": (
        "event-scope-v5-qualitative-comparison", "evaluation_report", "current",
        "Non-scoring comparison describing local condition-orientation observation and remaining hierarchy/schema blockers.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5", "evaluation_prompt", "current_used_once",
        "Prompt used by the single v5 run; conditional orientation and alternative-path scopes are not thereby validated generally.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5-tests", "evaluation_prompt_tests", "current",
        "Checks conditional direction, alternative-path language, and label-free model input projection.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v30-default", "validation_tool", "current",
        "Validates registered repository paths and SHA-256 fingerprints; defaults to active manifest v30.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v30-default", "validation_tool_tests", "current",
        "Covers artifact hash validation and the active v30 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v30-doc-index", "current_truth_index", "current",
        "Points to v30 and distinguishes the actual blocked v5 run from prompt-only claims.",
    ),
    "docs/current-state-audit.md": (
        "fta-v30-current-state-audit", "current_state_document", "current",
        "Records v5 request facts, blocker details, evidence-location scope, and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v30-acceptance-record", "acceptance_document", "current",
        "Records v5 run, offline checks, and explicit non-acceptance as an FTA Preview tree.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v30-candidate-generation-policy", "current_fta_policy_document", "current",
        "Records v5 as one blocked seen-Dev observation and preserves fail-closed policy.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v30-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks remaining hierarchy and output-schema defects without claiming prompt success or FTA readiness.",
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
    v29 = json.loads(V29_PATH.read_text(encoding="utf-8"))
    if v29.get("manifest_id") != "candidate_fta_research_baseline_v29":
        raise ValueError("v30 must extend the frozen v29 manifest")
    if v29.get("event_scope_prompt_v5", {}).get("status") != "prepared_offline_not_run":
        raise ValueError("v30 must preserve v29 as the pre-run snapshot")
    if v29.get("active_baseline", {}).get("fta_ready") is not False or v29.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v30 must preserve false FTA/production readiness")

    run_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json"
    assessment_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v5_2026-09-29.json"
    receipt_path = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.attempt.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    request = run.get("request", {})
    output = assessment.get("output_assessment", {})
    structure = output.get("structure_contract", {})
    evidence = output.get("evidence_location_check", {})
    parsed = run.get("model_output", {}).get("parsed_json")

    if (request.get("request_count"), request.get("retry_count"), request.get("sdk_max_retries")) != (1, 0, 0):
        raise ValueError("v30 requires exactly one request and zero configured/observed retries")
    if receipt.get("request_count") != 1 or receipt.get("sdk_max_retries") != 0:
        raise ValueError("v30 attempt receipt does not confirm one no-retry request")
    if receipt.get("run_sha256") != _sha256(run_path) or receipt.get("assessment_sha256") != _sha256(assessment_path):
        raise ValueError("v5 attempt receipt hashes do not match saved artifacts")
    if assessment.get("run_artifact") != run_path.relative_to(ROOT).as_posix() or assessment.get("attempt_receipt") != receipt_path.relative_to(ROOT).as_posix():
        raise ValueError("v5 assessment artifact links do not match the run bundle")
    if run.get("status") != "response_received" or run.get("request", {}).get("finish_reason") != "stop":
        raise ValueError("v30 requires the observed complete v5 response")
    if request.get("prompt_version") != "event-scope-text-only-tree-v5-causal-path-scope":
        raise ValueError("v5 run prompt version does not match the prepared prompt")
    if run.get("case", {}).get("exposure_status") != "seen_development_only":
        raise ValueError("v30 only records the seen-Development packet")
    if output.get("strict_json_parsed") is not True or output.get("assessment_status") != "blocked":
        raise ValueError("v30 requires the parsed but structurally blocked v5 assessment")
    if (evidence.get("valid"), evidence.get("checked")) != (15, 15):
        raise ValueError("v30 requires the recorded 15/15 literal evidence-location result")
    structure_codes = [item.get("code") for item in structure.get("blockers", [])]
    if structure_codes.count("node_has_multiple_output_scopes") != 3 or "gate_scope_requires_at_least_two_children" not in structure_codes:
        raise ValueError("v30 requires the observed repeated-output-scope and one-child blockers")
    evidence_codes = [item.get("code") for item in evidence.get("blockers", [])]
    if evidence_codes != ["gate_keys_mismatch"]:
        raise ValueError("v30 requires the observed missing required gate field blocker")
    if not isinstance(parsed, dict) or len(parsed.get("nodes", [])) != 10 or len(parsed.get("gates", [])) != 4:
        raise ValueError("v30 requires the observed 10-node/4-scope v5 response")
    gate_counts = {label: sum(gate.get("gate") == label for gate in parsed["gates"]) for label in ("AND", "OR", "unknown")}
    if gate_counts != {"AND": 0, "OR": 1, "unknown": 3}:
        raise ValueError("v30 gate counts differ from the saved v5 response")

    manifest = deepcopy(v29)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v30"
    manifest["baseline_version"] = "v30"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one explicitly authorized, no-retry v5 event-scope request on the seen NASA Figure 7 Development packet, with offline hierarchy/evidence assessment and non-scoring qualitative review"
    )
    manifest["scope"]["excludes"].extend([
        "gate accuracy, F1, calibration, expert agreement, or generalization claims from the single seen-Development v5 run",
        "automatic tree repair, Gold promotion, production/API/database writes, or readiness promotion from the v5 observation",
    ])
    manifest["active_baseline"].update({
        "event_scope_latest_actual_model_run": run_path.relative_to(ROOT).as_posix(),
        "event_scope_latest_actual_model_run_status": "blocked_seen_development_only",
        "event_scope_prepared_prompt": "event-scope-text-only-tree-v5-causal-path-scope",
        "event_scope_prepared_prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v5.py",
        "event_scope_prepared_prompt_status": "run_once_seen_dev_blocked",
        "event_scope_model_live_request_count_v5": 1,
        "event_scope_model_live_request_retries_v5": 0,
        "event_scope_model_v5_assessment_status": "blocked",
        "event_scope_model_v5_strict_json_parsed": True,
        "event_scope_model_v5_structure_blocker_count": len(structure.get("blockers", [])),
        "event_scope_model_v5_evidence_location_valid": evidence["valid"],
        "event_scope_model_v5_evidence_location_checked": evidence["checked"],
        "event_scope_model_v5_gate_labels": gate_counts,
        "event_scope_model_v5_accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v5"] = {
        "status": "completed_seen_development_only_blocked",
        "prompt_version": "event-scope-text-only-tree-v5-causal-path-scope",
        "prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v5.py",
        "runner_path": "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v5.py",
        "test_path": "evaluation/quality_eval/test_run_fta_event_scope_model_v5.py",
        "run_path": run_path.relative_to(ROOT).as_posix(),
        "assessment_path": assessment_path.relative_to(ROOT).as_posix(),
        "attempt_receipt_path": receipt_path.relative_to(ROOT).as_posix(),
        "comparison_report_path": "evaluation/quality_eval/runs/fta_event_scope_model_run_v5_dev_comparison_2026-09-29.md",
        "provider_host": request.get("provider_host"),
        "requested_model": request.get("requested_model"),
        "returned_model": request.get("returned_model"),
        "authorized_request_count": request["request_count"],
        "observed_retry_count": request["retry_count"],
        "configured_max_retries": request["sdk_max_retries"],
        "thinking_mode": request.get("thinking_mode"),
        "response_format": request.get("response_format"),
        "finish_reason": request.get("finish_reason"),
        "strict_json_parsed": output.get("strict_json_parsed"),
        "prompt_sha256": request.get("prompt_sha256"),
        "model_input_sha256": run.get("case", {}).get("model_input_sha256"),
        "model_input_includes_gold": False,
        "gold_comparison": "qualitative_non_scoring_only",
        "reference_review_role": "ai_role_review_not_human_expert_gold",
        "semantic_correctness": "not_assessed",
        "structure_status": "blocked",
        "structure_blockers": structure.get("blockers", []),
        "evidence_location": {"valid": evidence["valid"], "checked": evidence["checked"], "semantic_entailment_assessed": False},
        "evidence_schema_blockers": evidence.get("blockers", []),
        "predicted_gate_counts": gate_counts,
        "local_condition_orientation_observed": True,
        "accuracy_or_calibration_claim_allowed": False,
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "reason": "The output places the cell-explosion and container-failure events under the top event in one scope, matching the intended local direction, but also emits four scopes with the same output, a single-child scope, and a missing required unknown_reason field on a known gate. The tree is not accepted or auto-repaired.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v29"],
        "current_version": "v30",
        "reason": "v30 records the single actual v5 seen-Development run and its blocked structural assessment; no accuracy, Gold, FTA readiness, or production readiness promotion is made.",
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
        current = V30_PATH.read_text(encoding="utf-8") if V30_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v30 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v30",
            "v5_run_status": payload["event_scope_prompt_v5"]["status"],
            "request_count": payload["event_scope_prompt_v5"]["authorized_request_count"],
            "retry_count": payload["event_scope_prompt_v5"]["observed_retry_count"],
            "assessment_status": payload["event_scope_prompt_v5"]["structure_status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V30_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V30_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
