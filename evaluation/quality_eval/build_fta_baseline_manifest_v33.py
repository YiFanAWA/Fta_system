#!/usr/bin/env python3
"""Build active FTA baseline v33 with the completed one-shot v6 development run."""

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

V32_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v32.json"
V33_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v33.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v6_2026-09-29.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.attempt.json"
COMPARISON_PATH = "evaluation/quality_eval/runs/fta_event_scope_model_run_v6_dev_comparison_2026-09-29.md"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v32.json": (
        "fta-baseline-manifest-v32-snapshot", "historical_baseline_manifest", "historical",
        "Frozen state immediately before the authorized v6 request; accurately records v6 as not yet run.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v32.py": (
        "fta-baseline-manifest-v32-builder", "reproducibility_tool", "historical",
        "Reproduces the pre-inference v32 state; superseded as active baseline by v33.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v32.py": (
        "fta-baseline-manifest-v32-tests", "manifest_regression_tests", "historical",
        "Protects the v32 pre-inference snapshot.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py": (
        "event-scope-model-runner-v6", "evaluation_tool", "current",
        "One explicitly authorized request maximum, zero retries, v6 prompt and label-free input; preserves outputs without automatic repair.",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v6.py": (
        "event-scope-model-runner-v6-tests", "evaluation_tool_tests", "current",
        "Offline tests for authorization, one-shot settings, raw output preservation and no retry/repair.",
    ),
    RUN_PATH: (
        "event-scope-model-run-v6", "development_model_run", "current_seen_development",
        "Single explicitly authorized NASA Figure 7 Dev response; strict JSON, 7 nodes/3 scopes, structural contract valid, semantics unassessed.",
    ),
    ASSESSMENT_PATH: (
        "event-scope-model-assessment-v6", "offline_contract_assessment", "current_seen_development",
        "Mechanical assessment: structure valid, 10/10 evidence locations valid; explicitly not semantic acceptance or Gold comparison.",
    ),
    ATTEMPT_PATH: (
        "event-scope-model-attempt-v6", "request_audit_receipt", "current_audit",
        "Records the single request authorization and confirms request_count=1 and retry_count=0.",
    ),
    COMPARISON_PATH: (
        "event-scope-model-v6-qualitative-review", "qualitative_development_review", "current_seen_development",
        "Records structural improvements and unresolved semantic risks without an accuracy or Gold claim.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v33.py": (
        "fta-baseline-manifest-v33-builder", "reproducibility_tool", "current",
        "Builds v33 from immutable v32, verifies one-shot run facts, registers artifacts and hashes current truth files.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v33.py": (
        "fta-baseline-manifest-v33-tests", "manifest_regression_tests", "current",
        "Protects v32 history, actual v6 run metadata, semantic non-acceptance, artifact registration and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v33-default", "validation_tool", "current",
        "Validates repository artifact paths and SHA-256 fingerprints; defaults to active manifest v33.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v33-default", "validation_tool_tests", "current",
        "Covers artifact hashes and the active v33 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v33-doc-index", "current_truth_index", "current",
        "Points to active v33 and distinguishes structural/locational validity from unassessed semantics.",
    ),
    "docs/current-state-audit.md": (
        "fta-v33-current-state-audit", "current_state_document", "current",
        "Records the one-shot v6 run, exact structural/evidence results, semantic risks and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v33-acceptance-record", "acceptance_document", "current",
        "Records the authorized one-shot inference and non-network reproducibility checks.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v33-candidate-generation-policy", "current_fta_policy_document", "current",
        "Updates latest single-event sample status to v6; keeps it Dev-only and semantically unaccepted.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v33-validation-plan-policy", "current_validation_plan_document", "current",
        "Records v6 structural progress and retains semantic type, truth, independent validation and readiness work.",
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
    v32 = json.loads(V32_PATH.read_text(encoding="utf-8"))
    if v32.get("manifest_id") != "candidate_fta_research_baseline_v32":
        raise ValueError("v33 must extend the v32 manifest")
    if v32.get("active_baseline", {}).get("fta_ready") is not False or v32.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v33 must preserve false FTA/production readiness")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    expected_packet = "NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001"
    if run.get("status") != "response_received" or run.get("case", {}).get("packet_id") != expected_packet:
        raise ValueError("v33 requires the completed Figure 7 v6 development run")
    if run.get("request", {}).get("request_count") != 1 or run.get("request", {}).get("retry_count") != 0:
        raise ValueError("v33 requires exactly one request and zero retries")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0:
        raise ValueError("v33 attempt receipt does not confirm the authorized one-shot policy")
    output_assessment = assessment.get("output_assessment", {})
    evidence_check = output_assessment.get("evidence_location_check", {})
    if output_assessment.get("structure_contract", {}).get("valid") is not True:
        raise ValueError("v33 requires the v6 structural contract to pass")
    if evidence_check.get("checked") != 10 or evidence_check.get("valid") != 10:
        raise ValueError("v33 requires all 10 v6 evidence locations to validate")
    if output_assessment.get("semantic_correctness") != "not_assessed":
        raise ValueError("v33 must not imply semantic review was performed")

    manifest = deepcopy(v32)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v33"
    manifest["baseline_version"] = "v33"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v32",
        "path": V32_PATH.relative_to(ROOT).as_posix(),
        "reason": "v33 records the one explicitly authorized v6 seen-Development run and its structural/evidence assessment; semantic acceptance and readiness remain false.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly authorized, no-retry v6 NASA Figure 7 seen-Development inference with preserved raw response, structural contract pass, 10/10 evidence-location pass, and qualitative semantic-risk review"
    )
    manifest["scope"]["excludes"].extend([
        "semantic acceptance, gate accuracy, calibration, human-expert Gold, independent Final validation, production/API/database writes, or readiness promotion from the single v6 Development run",
        "any additional live model request or automatic retry under the one-request authorization",
    ])
    manifest["active_baseline"].update({
        "event_scope_model_runner_status": "one_shot_completed_seen_development_semantics_unassessed",
        "event_scope_prepared_prompt_status": "v6_seen_development_run_completed_semantics_unassessed",
        "event_scope_model_live_request_count_v6": 1,
        "event_scope_model_v6_assessment_status": output_assessment.get("assessment_status"),
        "event_scope_model_v6_strict_json_parsed": output_assessment.get("strict_json_parsed"),
        "event_scope_model_v6_structure_valid": output_assessment.get("structure_contract", {}).get("valid"),
        "event_scope_model_v6_structure_blocker_count": len(output_assessment.get("structure_contract", {}).get("blockers", [])),
        "event_scope_model_v6_evidence_location_valid": evidence_check.get("valid"),
        "event_scope_model_v6_evidence_location_checked": evidence_check.get("checked"),
        "event_scope_model_v6_gate_labels": {"AND": 0, "OR": 0, "unknown": 3},
        "event_scope_model_v6_semantic_correctness": "not_assessed",
        "event_scope_model_v6_accuracy_claim_allowed": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_requires_fresh_explicit_authorization": True,
        "event_scope_latest_actual_model_run": RUN_PATH,
        "event_scope_latest_actual_model_run_status": "completed_seen_development_only_semantics_unassessed",
        "event_scope_model_run_assessment": ASSESSMENT_PATH,
        "event_scope_model_comparison": COMPARISON_PATH,
        "event_scope_model_comparison_status": "qualitative_dev_review_structure_and_location_valid_semantics_not_accepted",
        "event_scope_model_semantic_acceptance": False,
        "fta_ready": False,
        "production_ready": False,
    })
    prompt_record = manifest["event_scope_prompt_v6"]
    prompt_record.update({
        "status": "completed_seen_development_only_semantics_unassessed",
        "live_request_count": 1,
        "latest_actual_model_run_path": RUN_PATH,
        "latest_actual_model_run_status": "completed_seen_development_only_semantics_unassessed",
        "model_output_observed": True,
        "assessment_path": ASSESSMENT_PATH,
        "qualitative_review_path": COMPARISON_PATH,
        "strict_json_parsed": True,
        "structure_contract_valid": True,
        "structure_blocker_count": 0,
        "evidence_location_valid": 10,
        "evidence_location_checked": 10,
        "gate_labels": {"AND": 0, "OR": 0, "unknown": 3},
        "semantic_correctness": "not_assessed",
        "semantic_acceptance": False,
        "accuracy_or_calibration_claim_allowed": False,
        "requires_fresh_explicit_authorization_for_any_model_request": True,
        "raw_model_output_preserved_on_block": True,
        "automatic_repair_performed": False,
        "automatic_retry_performed": False,
        "reason": "One explicitly authorized request returned valid JSON; the hierarchy contract and all 10 evidence locations passed. Qualitative inspection identifies unresolved semantic issues, so the result is not accepted as a tree and makes no accuracy/generalization claim. Any further request requires fresh authorization.",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v32"],
        "current_version": "v33",
        "reason": "v33 records the actual v6 one-shot Development run without promoting semantic acceptance, Gold, FTA readiness, or production readiness.",
    })

    _upsert(manifest["artifacts"], {
        "artifact_id": "fta-baseline-manifest-v32-snapshot",
        "kind": "historical_baseline_manifest",
        "lifecycle": "historical",
        "path": V32_PATH.relative_to(ROOT).as_posix(),
        "note": "Immutable pre-inference snapshot; its statement that v6 had not run was correct at capture time.",
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
        current = V33_PATH.read_text(encoding="utf-8") if V33_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v33 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v33",
            "v6_request_count": payload["event_scope_prompt_v6"]["live_request_count"],
            "v6_assessment_status": payload["event_scope_prompt_v6"]["status"],
            "v6_semantic_acceptance": payload["event_scope_prompt_v6"]["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V33_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V33_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
