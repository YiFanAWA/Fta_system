#!/usr/bin/env python3
"""Build active FTA baseline v41 after the authorized SMOKE-004 run."""

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

from evaluation.quality_eval.compare_fta_event_scope_semantic_smoke_run_v2 import (  # noqa: E402
    ALLOWED_UNKNOWN_REASONS,
)

V40_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v40.json"
V41_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v41.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29_assessment.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29.attempt.json"
COMPARISON_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29_offline_comparison_v2.json"

CURRENT_ARTIFACTS = {
    RUN_PATH: (
        "fta-semantic-smoke-SMOKE-004-run", "single_model_run", "current_non_gold_observation",
        "One explicitly authorized DeepSeek call on synthetic SMOKE-004; event co-occurrence retained as unknown, zero retries; not expert Gold or accuracy evidence.",
    ),
    ASSESSMENT_PATH: (
        "fta-semantic-smoke-SMOKE-004-assessment", "mechanical_contract_assessment", "current_non_gold_observation",
        "Structure contract valid and all four evidence locations matched; semantic correctness remains unassessed.",
    ),
    ATTEMPT_PATH: (
        "fta-semantic-smoke-SMOKE-004-attempt", "request_attempt_receipt", "current_audit_record",
        "Records exactly one explicitly authorized request and zero SDK retries; no credentials or hidden reasoning stored.",
    ),
    COMPARISON_PATH: (
        "fta-semantic-smoke-SMOKE-004-v2-policy-comparison", "offline_non_gold_comparison", "current_non_gold_observation",
        "Comparator v2 confirms unknown/null-logic-evidence/allowed-reason contract and the authored non-Gold expectation; no provider request.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v40.json": (
        "fta-baseline-manifest-v40-snapshot", "historical_baseline_manifest", "historical",
        "Immutable active snapshot after SMOKE-003; superseded as active baseline by v41.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v40.py": (
        "fta-baseline-manifest-v40-builder", "reproducibility_tool", "historical",
        "Builds v40 from v39; superseded by v41.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v40.py": (
        "fta-baseline-manifest-v40-tests", "manifest_regression_tests", "historical",
        "Protects historical v40 three-case state and false readiness.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v41.py": (
        "fta-baseline-manifest-v41-builder", "reproducibility_tool", "current",
        "Builds v41 from v40 after verifying the saved SMOKE-004 response, assessment, receipt, and v2 offline comparison.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v41.py": (
        "fta-baseline-manifest-v41-tests", "manifest_regression_tests", "current",
        "Checks four-case qualitative scope, unknown co-occurrence outcome, v40 immutability, and false readiness.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2", "offline_comparison_tool", "current",
        "Gate-specific offline comparison; makes no provider request and prohibits expert-Gold/accuracy promotion.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2-tests", "offline_comparison_tests", "current",
        "Tests AND/OR direct-quote policy, unknown null-evidence/reason contract, and saved qualitative observations.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v41-default", "validation_tool", "current",
        "Validates active v41 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v41-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v41 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v41-doc-index", "current_truth_index", "current",
        "Points to active v41 and four non-Gold smoke cases, including co-occurrence unknown behavior.",
    ),
    "docs/current-state-audit.md": (
        "fta-v41-current-state-audit", "current_state_document", "current",
        "Records SMOKE-004 and its unknown-gate comparison with unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v41-acceptance-record", "acceptance_document", "current",
        "Records authorized SMOKE-004 request, v2 comparison, tests, and v41 artifact validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v41-candidate-generation-policy", "current_fta_policy_document", "current",
        "Explains four synthetic observations without accuracy or readiness promotion.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v41-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks co-occurrence unknown behavior and remaining source-grounded validation.",
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
    v40 = json.loads(V40_PATH.read_text(encoding="utf-8"))
    if v40.get("manifest_id") != "candidate_fta_research_baseline_v40":
        raise ValueError("v41 must extend immutable v40")
    active_v40 = v40.get("active_baseline", {})
    if active_v40.get("fta_ready") is not False or active_v40.get("production_ready") is not False:
        raise ValueError("v41 must preserve false FTA and production readiness")
    if active_v40.get("event_scope_prompt_v8_semantic_acceptance") is not False:
        raise ValueError("v41 cannot promote semantic acceptance")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / COMPARISON_PATH).read_text(encoding="utf-8"))
    if run.get("status") != "response_received" or run.get("case", {}).get("case_id") != "SMOKE-004":
        raise ValueError("v41 requires the saved successful SMOKE-004 response")
    request = run.get("request", {})
    if request.get("request_count") != 1 or request.get("retry_count") != 0 or request.get("sdk_max_retries") != 0:
        raise ValueError("SMOKE-004 must record one request and zero retries")
    if request.get("finish_reason") != "stop" or request.get("reference_labels_loaded") is not False or request.get("gold_included_in_model_input") is not False:
        raise ValueError("SMOKE-004 must be complete and label-free")
    if assessment.get("case_id") != "SMOKE-004":
        raise ValueError("SMOKE-004 assessment case id is required")
    output = assessment.get("output_assessment", {})
    evidence_check = output.get("evidence_location_check", {})
    if output.get("strict_json_parsed") is not True or output.get("structure_contract", {}).get("valid") is not True:
        raise ValueError("SMOKE-004 must pass strict JSON parsing and structure contract")
    if evidence_check.get("checked") != 4 or evidence_check.get("valid") != 4:
        raise ValueError("SMOKE-004 must retain the observed 4/4 evidence-location result")
    if output.get("semantic_correctness") != "not_assessed" or output.get("human_expert_gold") is not False:
        raise ValueError("SMOKE-004 must remain semantically unassessed and non-Gold")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0 or attempt.get("explicit_single_request_authorization") is not True:
        raise ValueError("attempt receipt must confirm one explicit authorization and zero SDK retries")
    if comparison.get("artifact_version") != "v2" or comparison.get("case_id") != "SMOKE-004":
        raise ValueError("v2 comparison artifact for SMOKE-004 is required")
    if comparison.get("status") != "matched_authored_policy_expectation_not_expert_validation":
        raise ValueError("SMOKE-004 comparison must remain a qualitative non-expert match")
    compared = comparison.get("comparison", {})
    if (
        compared.get("expected_gate") != "unknown"
        or compared.get("observed_gate") != "unknown"
        or compared.get("gate_matches_policy_expectation") is not True
        or compared.get("unknown_gate_contract_valid") is not True
        or compared.get("decisive_source_quote_present_in_input") is not True
        or compared.get("structure_contract_valid") is not True
        or compared.get("evidence_locations_checked") != 4
        or compared.get("evidence_locations_valid") != 4
    ):
        raise ValueError("v2 comparison must validate the SMOKE-004 unknown policy")
    parsed = run.get("model_output", {}).get("parsed_json", {})
    gates = parsed.get("gates") if isinstance(parsed, dict) else None
    if not isinstance(gates, list) or len(gates) != 1:
        raise ValueError("SMOKE-004 must preserve exactly one gate scope")
    gate = gates[0]
    if gate.get("gate") != "unknown" or gate.get("logic_evidence") is not None:
        raise ValueError("SMOKE-004 output must keep unknown without logic evidence")
    if gate.get("unknown_reason") not in ALLOWED_UNKNOWN_REASONS:
        raise ValueError("SMOKE-004 output must contain an allowed unknown reason")
    claims = comparison.get("claim_boundaries", {})
    if claims.get("human_expert_gold") is not False or claims.get("accuracy_or_calibration_claim_allowed") is not False:
        raise ValueError("SMOKE-004 comparison cannot be promoted to expert Gold or accuracy")
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
        raise ValueError("SMOKE-004 comparison provenance must bind the exact run, assessment, and non-Gold reference")

    manifest = deepcopy(v40)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v41"
    manifest["baseline_version"] = "v41"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v40",
        "path": V40_PATH.relative_to(ROOT).as_posix(),
        "reason": "v41 adds one explicitly authorized synthetic SMOKE-004 co-occurrence observation and its gate-specific offline comparison; it does not establish semantic accuracy or readiness.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly user-authorized, no-retry prompt-v8 synthetic SMOKE-004 model request and its preserved response, assessment, attempt receipt, and v2 offline comparison"
    )
    manifest["scope"]["excludes"] = [
        item.replace(
            "any model request for SMOKE-004 through SMOKE-005 without separate fresh explicit user authorization",
            "any model request for SMOKE-005 without separate fresh explicit user authorization",
        )
        for item in manifest["scope"].get("excludes", [])
    ]
    manifest["scope"]["excludes"].append(
        "expert semantic validation, source-corpus evaluation, aggregate accuracy/calibration, and generalization claims from the four synthetic SMOKE-001/002/003/004 observations"
    )
    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "four_case_qualitative_matches_non_gold",
        "event_scope_semantic_smoke_requests_performed": 4,
        "event_scope_semantic_smoke_completed_case_ids": ["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004"],
        "event_scope_semantic_smoke_comparator_version": "v2_gate_specific_evidence_contract_v1",
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    smoke = manifest["event_scope_semantic_smoke_v1"]
    smoke["status"] = "four_cases_completed_qualitative_non_gold"
    smoke["request_count"] = 4
    smoke["retry_count"] = 0
    smoke["completed_case_ids"] = ["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004"]
    smoke["not_run_case_ids"] = ["SMOKE-005"]
    smoke["case_results"].append({
        "case_id": "SMOKE-004",
        "expected_gate": "unknown",
        "observed_gate": "unknown",
        "policy_expectation_match": True,
        "comparison_version": "v2",
        "unknown_gate_contract_valid": True,
        "unknown_reason": gate["unknown_reason"],
        "structure_contract_valid": True,
        "evidence_locations_checked": 4,
        "evidence_locations_valid": 4,
    })
    smoke["evidence_locations_checked"] = 19
    smoke["evidence_locations_valid"] = 19
    smoke["semantic_acceptance"] = False
    smoke["human_expert_gold"] = False
    smoke["accuracy_or_calibration_claim_allowed"] = False
    smoke["next_gate"] = "retain four synthetic qualitative observations only; SMOKE-005 requires separate fresh explicit authorization; source-grounded semantic validation remains outstanding"
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v40"],
        "current_version": "v41",
        "reason": "v41 records the authorized SMOKE-004 co-occurrence unknown observation and its v2 offline comparison, while preserving false semantic acceptance and readiness.",
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
        current = V41_PATH.read_text(encoding="utf-8") if V41_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v41 differs from generated content\n")
        smoke = payload["event_scope_semantic_smoke_v1"]
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v41",
            "smoke_status": smoke["status"],
            "completed_case_ids": smoke["completed_case_ids"],
            "not_run_case_ids": smoke["not_run_case_ids"],
            "semantic_acceptance": smoke["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V41_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V41_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
