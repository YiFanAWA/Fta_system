#!/usr/bin/env python3
"""Build active FTA baseline v39 after two synthetic semantic smoke observations."""

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

V38_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v38.json"
V39_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v39.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29_assessment.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29.attempt.json"
COMPARISON_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29_offline_comparison.json"

CURRENT_ARTIFACTS = {
    RUN_PATH: (
        "fta-semantic-smoke-SMOKE-002-run", "single_model_run", "current_non_gold_observation",
        "One explicitly authorized DeepSeek call on synthetic SMOKE-002; implicit AND output, strict JSON, zero retries; not expert Gold or accuracy evidence.",
    ),
    ASSESSMENT_PATH: (
        "fta-semantic-smoke-SMOKE-002-assessment", "mechanical_contract_assessment", "current_non_gold_observation",
        "Structure contract valid and all five evidence locations matched; semantic correctness remains unassessed.",
    ),
    ATTEMPT_PATH: (
        "fta-semantic-smoke-SMOKE-002-attempt", "request_attempt_receipt", "current_audit_record",
        "Records exactly one user-authorized request and zero SDK retries without storing credentials or hidden reasoning.",
    ),
    COMPARISON_PATH: (
        "fta-semantic-smoke-SMOKE-002-policy-comparison", "offline_non_gold_comparison", "current_non_gold_observation",
        "Post-run comparison to isolated authored policy expectation; observed AND matches expected AND; not expert validation or a metric.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v38.py": (
        "fta-baseline-manifest-v38-builder", "reproducibility_tool", "historical",
        "Builds immutable historical v38 from v37 after validating SMOKE-001; superseded by v39.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v38.py": (
        "fta-baseline-manifest-v38-tests", "manifest_regression_tests", "historical",
        "Protects historical v38 one-case state and false readiness.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v38.json": (
        "fta-baseline-manifest-v38-snapshot", "historical_baseline_manifest", "historical",
        "Immutable historical snapshot after SMOKE-001; superseded as active baseline by v39.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v39.py": (
        "fta-baseline-manifest-v39-builder", "reproducibility_tool", "current",
        "Builds active v39 from v38 after validating both preserved synthetic smoke observations and their isolated offline comparisons.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v39.py": (
        "fta-baseline-manifest-v39-tests", "manifest_regression_tests", "current",
        "Checks two-case qualitative scope, no Gold/accuracy promotion, v38 immutability, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v39-default", "validation_tool", "current",
        "Validates active v39 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v39-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v39 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v39-doc-index", "current_truth_index", "current",
        "Points to active v39 and both synthetic SMOKE-001/002 observations.",
    ),
    "docs/current-state-audit.md": (
        "fta-v39-current-state-audit", "current_state_document", "current",
        "Records two qualitative synthetic runs while retaining unresolved semantic acceptance and false readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v39-acceptance-record", "acceptance_document", "current",
        "Records both one-shot invocations, offline non-Gold comparisons, tests and artifact validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v39-candidate-generation-policy", "current_fta_policy_document", "current",
        "Explains both synthetic observations without promoting them to general accuracy or readiness.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v39-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks two completed qualitative smoke observations and remaining source-grounded validation.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register(artifacts: list[dict[str, Any]], relative_path: str, entry: dict[str, Any]) -> None:
    existing = next((item for item in artifacts if item.get("path") == relative_path), None)
    registered = {**(existing or {}), **entry, "path": relative_path}
    for index, item in enumerate(artifacts):
        if item.get("path") == relative_path:
            artifacts[index] = registered
            return
    artifacts.append(registered)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v38 = json.loads(V38_PATH.read_text(encoding="utf-8"))
    if v38.get("manifest_id") != "candidate_fta_research_baseline_v38":
        raise ValueError("v39 must extend immutable v38")
    active_v38 = v38.get("active_baseline", {})
    if active_v38.get("fta_ready") is not False or active_v38.get("production_ready") is not False:
        raise ValueError("v39 must preserve false FTA and production readiness")
    if active_v38.get("event_scope_prompt_v8_semantic_acceptance") is not False:
        raise ValueError("v39 cannot promote semantic acceptance")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / COMPARISON_PATH).read_text(encoding="utf-8"))
    if run.get("status") != "response_received" or run.get("case", {}).get("case_id") != "SMOKE-002":
        raise ValueError("v39 requires the successful saved SMOKE-002 response")
    request = run.get("request", {})
    if request.get("request_count") != 1 or request.get("retry_count") != 0 or request.get("sdk_max_retries") != 0:
        raise ValueError("SMOKE-002 must record exactly one request and zero retries")
    if request.get("finish_reason") != "stop":
        raise ValueError("SMOKE-002 must have a completed response rather than a truncated output")
    if request.get("reference_labels_loaded") is not False or request.get("gold_included_in_model_input") is not False:
        raise ValueError("reference labels and Gold must remain outside the model request")
    if assessment.get("case_id") != "SMOKE-002":
        raise ValueError("SMOKE-002 assessment case id is required")
    output = assessment.get("output_assessment", {})
    if output.get("strict_json_parsed") is not True or output.get("structure_contract", {}).get("valid") is not True:
        raise ValueError("SMOKE-002 must pass strict JSON parsing and structural contract")
    evidence = output.get("evidence_location_check", {})
    if evidence.get("checked") != 5 or evidence.get("valid") != 5:
        raise ValueError("SMOKE-002 must retain the observed 5/5 evidence-location result")
    if output.get("semantic_correctness") != "not_assessed" or output.get("human_expert_gold") is not False:
        raise ValueError("SMOKE-002 must remain semantically unassessed and non-Gold")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0 or attempt.get("explicit_single_request_authorization") is not True:
        raise ValueError("attempt receipt must confirm one explicitly authorized request and zero SDK retries")
    if comparison.get("status") != "matched_authored_policy_expectation_not_expert_validation":
        raise ValueError("comparison must remain a qualitative non-expert policy match")
    provenance = comparison.get("provenance", {})
    reference_path = "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json"
    if (
        provenance.get("run_path") != RUN_PATH
        or provenance.get("run_sha256") != _sha256(ROOT / RUN_PATH)
        or provenance.get("assessment_path") != ASSESSMENT_PATH
        or provenance.get("assessment_sha256") != _sha256(ROOT / ASSESSMENT_PATH)
        or provenance.get("reference_path") != reference_path
        or provenance.get("reference_sha256") != _sha256(ROOT / reference_path)
        or provenance.get("reference_status") != "authored_policy_reference_not_expert_reviewed"
    ):
        raise ValueError("comparison provenance must bind the exact saved run, assessment, and non-Gold reference")
    observed = comparison.get("comparison", {})
    if observed.get("expected_gate") != "AND" or observed.get("observed_gate") != "AND" or observed.get("qualitative_smoke_match") is not True:
        raise ValueError("SMOKE-002 expected/observed gate comparison changed")
    parsed = run.get("model_output", {}).get("parsed_json", {})
    gates = parsed.get("gates") if isinstance(parsed, dict) else None
    if not isinstance(gates, list) or len(gates) != 1 or gates[0].get("gate") != "AND":
        raise ValueError("saved SMOKE-002 model output must contain exactly one AND gate")
    claims = comparison.get("claim_boundaries", {})
    if claims.get("human_expert_gold") is not False or claims.get("accuracy_or_calibration_claim_allowed") is not False:
        raise ValueError("SMOKE-002 cannot be promoted to expert Gold or accuracy")

    manifest = deepcopy(v38)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v39"
    manifest["baseline_version"] = "v39"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v38",
        "path": V38_PATH.relative_to(ROOT).as_posix(),
        "reason": "v39 adds one explicitly authorized synthetic SMOKE-002 observation (implicit AND) and its isolated offline non-Gold comparison; it does not establish semantic accuracy or readiness.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly user-authorized, no-retry prompt-v8 synthetic semantic smoke request for SMOKE-002, with preserved response/assessment/attempt receipt and isolated post-run comparison to a non-expert policy expectation"
    )
    manifest["scope"]["excludes"] = [
        item.replace(
            "any model request for SMOKE-002 through SMOKE-005 without separate fresh explicit user authorization",
            "any model request for SMOKE-003 through SMOKE-005 without separate fresh explicit user authorization",
        )
        for item in manifest["scope"].get("excludes", [])
    ]
    manifest["scope"]["excludes"].append(
        "expert semantic validation, source-corpus evaluation, aggregate model accuracy/calibration, and generalization claims from the two synthetic SMOKE-001/SMOKE-002 observations"
    )

    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "two_case_qualitative_matches_non_gold",
        "event_scope_semantic_smoke_live_request_performed": True,
        "event_scope_semantic_smoke_requests_performed": 2,
        "event_scope_semantic_smoke_completed_case_ids": ["SMOKE-001", "SMOKE-002"],
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    smoke = manifest["event_scope_semantic_smoke_v1"]
    smoke.update({
        "status": "two_cases_completed_qualitative_non_gold",
        "live_request_performed": True,
        "request_count": 2,
        "retry_count": 0,
        "completed_case_ids": ["SMOKE-001", "SMOKE-002"],
        "not_run_case_ids": ["SMOKE-003", "SMOKE-004", "SMOKE-005"],
        "case_results": [
            {"case_id": "SMOKE-001", "expected_gate": "OR", "observed_gate": "OR", "policy_expectation_match": True, "structure_contract_valid": True, "evidence_locations_checked": 5, "evidence_locations_valid": 5},
            {"case_id": "SMOKE-002", "expected_gate": "AND", "observed_gate": "AND", "policy_expectation_match": True, "structure_contract_valid": True, "evidence_locations_checked": 5, "evidence_locations_valid": 5},
        ],
        "observed_gate": None,
        "authored_policy_expected_gate": None,
        "policy_expectation_match": None,
        "structure_contract_valid": True,
        "evidence_locations_checked": 10,
        "evidence_locations_valid": 10,
        "semantic_acceptance": False,
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "next_gate": "retain both as synthetic behavioral observations only; any further model request requires separate fresh explicit authorization; source-grounded semantic validation remains outstanding",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v38"],
        "current_version": "v39",
        "reason": "v39 records two authorized synthetic qualitative observations and their isolated non-Gold policy comparisons while preserving false semantic acceptance and readiness.",
    })

    repo_root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": note,
            "sha256": _sha256(target),
        })

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
        current = V39_PATH.read_text(encoding="utf-8") if V39_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v39 differs from generated content\n")
        smoke = payload["event_scope_semantic_smoke_v1"]
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v39",
            "smoke_status": smoke["status"],
            "completed_case_ids": smoke["completed_case_ids"],
            "not_run_case_ids": smoke["not_run_case_ids"],
            "semantic_acceptance": smoke["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V39_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V39_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
