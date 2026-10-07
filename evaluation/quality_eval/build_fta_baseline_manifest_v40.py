#!/usr/bin/env python3
"""Build active FTA baseline v40 with a third synthetic unknown-gate observation."""

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

V39_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v39.json"
V40_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v40.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_assessment.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29.attempt.json"
COMPARISON_V1_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_offline_comparison.json"
COMPARISON_V2_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_offline_comparison_v2.json"

CURRENT_ARTIFACTS = {
    RUN_PATH: (
        "fta-semantic-smoke-SMOKE-003-run", "single_model_run", "current_non_gold_observation",
        "One explicitly authorized DeepSeek call on synthetic SMOKE-003; unknown gate, null logic evidence, structured reason; not expert Gold or accuracy evidence.",
    ),
    ASSESSMENT_PATH: (
        "fta-semantic-smoke-SMOKE-003-assessment", "mechanical_contract_assessment", "current_non_gold_observation",
        "Structure contract valid and all five evidence locations matched; semantic correctness remains unassessed.",
    ),
    ATTEMPT_PATH: (
        "fta-semantic-smoke-SMOKE-003-attempt", "request_attempt_receipt", "current_audit_record",
        "Records exactly one explicitly authorized request and zero SDK retries; no credentials or hidden reasoning stored.",
    ),
    COMPARISON_V1_PATH: (
        "fta-semantic-smoke-SMOKE-003-v1-comparison-diagnostic", "historical_offline_comparison", "historical_diagnostic",
        "Preserved initial comparator-v1 result: requires_review because v1 universally demanded logic-quote binding, which is inapplicable to an unknown gate.",
    ),
    COMPARISON_V2_PATH: (
        "fta-semantic-smoke-SMOKE-003-v2-policy-comparison", "offline_non_gold_comparison", "current_non_gold_observation",
        "Comparator v2 applies the existing output contract: known gates bind direct logic evidence; unknown requires null logic evidence and an allowed reason code.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py": (
        "fta-semantic-smoke-comparator-v1", "offline_comparison_tool", "historical_policy",
        "Original comparator; its universal exact-quote condition is not applicable to unknown gates and is superseded by comparator v2.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v1.py": (
        "fta-semantic-smoke-comparator-v1-tests", "offline_comparison_tests", "historical_policy",
        "Regression coverage for comparator v1 known-gate behavior and its preserved scope; v2 owns gate-specific policy checks.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2", "offline_comparison_tool", "current",
        "Gate-specific offline comparison; makes no provider request and prohibits expert-Gold/accuracy promotion.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2-tests", "offline_comparison_tests", "current",
        "Tests known AND/OR evidence binding, unknown null-evidence/reason contract, invalid unknown cases, and saved observations.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v39.json": (
        "fta-baseline-manifest-v39-snapshot", "historical_baseline_manifest", "historical",
        "Immutable active snapshot after SMOKE-002; superseded as active baseline by v40.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v39.py": (
        "fta-baseline-manifest-v39-builder", "reproducibility_tool", "historical",
        "Builds v39 from v38; superseded by v40.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v39.py": (
        "fta-baseline-manifest-v39-tests", "manifest_regression_tests", "historical",
        "Protects historical v39 two-case state and false readiness.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v40.py": (
        "fta-baseline-manifest-v40-builder", "reproducibility_tool", "current",
        "Builds v40 from v39 after verifying the saved SMOKE-003 run, assessment, receipt, initial diagnostic, and gate-specific offline comparison.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v40.py": (
        "fta-baseline-manifest-v40-tests", "manifest_regression_tests", "current",
        "Checks three-case qualitative scope, preserved v1 diagnostic, v2 unknown contract, v39 immutability, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v40-default", "validation_tool", "current",
        "Validates active v40 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v40-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v40 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v40-doc-index", "current_truth_index", "current",
        "Points to active v40, three non-Gold smoke observations, and the gate-specific comparator correction.",
    ),
    "docs/current-state-audit.md": (
        "fta-v40-current-state-audit", "current_state_document", "current",
        "Records SMOKE-003, the preserved initial comparator diagnostic, the v2 contract correction, and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v40-acceptance-record", "acceptance_document", "current",
        "Records the authorized one-shot SMOKE-003 request, v1 diagnostic, v2 offline result, tests, and hash validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v40-candidate-generation-policy", "current_fta_policy_document", "current",
        "Explains three synthetic observations and gate-specific evidence policy without accuracy or readiness promotion.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v40-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks the unknown-gate evaluator correction and remaining source-grounded validation.",
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
    v39 = json.loads(V39_PATH.read_text(encoding="utf-8"))
    if v39.get("manifest_id") != "candidate_fta_research_baseline_v39":
        raise ValueError("v40 must extend immutable v39")
    active_v39 = v39.get("active_baseline", {})
    if active_v39.get("fta_ready") is not False or active_v39.get("production_ready") is not False:
        raise ValueError("v40 must preserve false FTA and production readiness")
    if active_v39.get("event_scope_prompt_v8_semantic_acceptance") is not False:
        raise ValueError("v40 cannot promote semantic acceptance")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    comparison_v1 = json.loads((ROOT / COMPARISON_V1_PATH).read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / COMPARISON_V2_PATH).read_text(encoding="utf-8"))

    if run.get("status") != "response_received" or run.get("case", {}).get("case_id") != "SMOKE-003":
        raise ValueError("v40 requires the saved successful SMOKE-003 response")
    request = run.get("request", {})
    if request.get("request_count") != 1 or request.get("retry_count") != 0 or request.get("sdk_max_retries") != 0:
        raise ValueError("SMOKE-003 must record one request and zero retries")
    if request.get("finish_reason") != "stop" or request.get("reference_labels_loaded") is not False or request.get("gold_included_in_model_input") is not False:
        raise ValueError("SMOKE-003 must be complete and label-free")
    if assessment.get("case_id") != "SMOKE-003":
        raise ValueError("SMOKE-003 assessment case id is required")
    output = assessment.get("output_assessment", {})
    evidence_check = output.get("evidence_location_check", {})
    if output.get("strict_json_parsed") is not True or output.get("structure_contract", {}).get("valid") is not True:
        raise ValueError("SMOKE-003 must pass strict JSON parsing and structure contract")
    if evidence_check.get("checked") != 5 or evidence_check.get("valid") != 5:
        raise ValueError("SMOKE-003 must retain the observed 5/5 evidence-location result")
    if output.get("semantic_correctness") != "not_assessed" or output.get("human_expert_gold") is not False:
        raise ValueError("SMOKE-003 must remain semantically unassessed and non-Gold")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0 or attempt.get("explicit_single_request_authorization") is not True:
        raise ValueError("attempt receipt must confirm one explicit authorization and zero SDK retries")
    if comparison_v1.get("status") != "requires_review":
        raise ValueError("the initial v1 comparison diagnostic must be preserved as observed")
    if comparison.get("artifact_version") != "v2" or comparison.get("case_id") != "SMOKE-003":
        raise ValueError("v2 comparison artifact for SMOKE-003 is required")
    if comparison.get("status") != "matched_authored_policy_expectation_not_expert_validation":
        raise ValueError("v2 comparison must remain a non-expert qualitative policy match")
    compared = comparison.get("comparison", {})
    if (
        compared.get("expected_gate") != "unknown"
        or compared.get("observed_gate") != "unknown"
        or compared.get("gate_matches_policy_expectation") is not True
        or compared.get("unknown_gate_contract_valid") is not True
        or compared.get("known_gate_logic_evidence_matches_decisive_quote") is not None
        or compared.get("decisive_source_quote_present_in_input") is not True
        or compared.get("structure_contract_valid") is not True
        or compared.get("evidence_locations_checked") != 5
        or compared.get("evidence_locations_valid") != 5
    ):
        raise ValueError("v2 comparison must validate the unknown-specific evidence policy")
    parsed = run.get("model_output", {}).get("parsed_json", {})
    gates = parsed.get("gates") if isinstance(parsed, dict) else None
    if not isinstance(gates, list) or len(gates) != 1:
        raise ValueError("SMOKE-003 must preserve exactly one gate scope")
    gate = gates[0]
    if gate.get("gate") != "unknown" or gate.get("logic_evidence") is not None:
        raise ValueError("SMOKE-003 output must keep unknown without logic evidence")
    if gate.get("unknown_reason") not in ALLOWED_UNKNOWN_REASONS:
        raise ValueError("SMOKE-003 output must contain an allowed unknown reason")
    claims = comparison.get("claim_boundaries", {})
    if claims.get("human_expert_gold") is not False or claims.get("accuracy_or_calibration_claim_allowed") is not False:
        raise ValueError("SMOKE-003 comparison cannot be promoted to expert Gold or accuracy")
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
        raise ValueError("v2 comparison provenance must bind this run, assessment, and non-Gold reference")

    manifest = deepcopy(v39)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v40"
    manifest["baseline_version"] = "v40"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v39",
        "path": V39_PATH.relative_to(ROOT).as_posix(),
        "reason": "v40 adds the authorized synthetic SMOKE-003 unknown-gate observation and corrects the offline comparator to apply gate-specific evidence requirements; it does not establish semantic accuracy or readiness.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly authorized, no-retry prompt-v8 synthetic SMOKE-003 model request, both preserved v1 diagnostic and v2 gate-specific offline comparisons, and regression coverage for the unknown-gate output contract"
    )
    manifest["scope"]["excludes"] = [
        item.replace(
            "any model request for SMOKE-003 through SMOKE-005 without separate fresh explicit user authorization",
            "any model request for SMOKE-004 through SMOKE-005 without separate fresh explicit user authorization",
        )
        for item in manifest["scope"].get("excludes", [])
    ]
    manifest["scope"]["excludes"].append(
        "expert semantic validation, source-corpus evaluation, aggregate accuracy/calibration, and generalization claims from the three synthetic SMOKE-001/002/003 observations"
    )
    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "three_case_qualitative_matches_non_gold",
        "event_scope_semantic_smoke_requests_performed": 3,
        "event_scope_semantic_smoke_completed_case_ids": ["SMOKE-001", "SMOKE-002", "SMOKE-003"],
        "event_scope_semantic_smoke_comparator_version": "v2_gate_specific_evidence_contract_v1",
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    smoke = manifest["event_scope_semantic_smoke_v1"]
    smoke.update({
        "status": "three_cases_completed_qualitative_non_gold",
        "request_count": 3,
        "retry_count": 0,
        "completed_case_ids": ["SMOKE-001", "SMOKE-002", "SMOKE-003"],
        "not_run_case_ids": ["SMOKE-004", "SMOKE-005"],
        "comparison_policy_version": "gate_specific_evidence_contract_v1",
        "case_results": [
            {"case_id": "SMOKE-001", "expected_gate": "OR", "observed_gate": "OR", "policy_expectation_match": True, "comparison_version": "v1", "structure_contract_valid": True, "evidence_locations_checked": 5, "evidence_locations_valid": 5},
            {"case_id": "SMOKE-002", "expected_gate": "AND", "observed_gate": "AND", "policy_expectation_match": True, "comparison_version": "v1", "structure_contract_valid": True, "evidence_locations_checked": 5, "evidence_locations_valid": 5},
            {"case_id": "SMOKE-003", "expected_gate": "unknown", "observed_gate": "unknown", "policy_expectation_match": True, "comparison_version": "v2", "unknown_gate_contract_valid": True, "unknown_reason": gate["unknown_reason"], "structure_contract_valid": True, "evidence_locations_checked": 5, "evidence_locations_valid": 5},
        ],
        "observed_gate": None,
        "authored_policy_expected_gate": None,
        "policy_expectation_match": None,
        "structure_contract_valid": True,
        "evidence_locations_checked": 15,
        "evidence_locations_valid": 15,
        "semantic_acceptance": False,
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "next_gate": "retain three synthetic qualitative observations only; any request for SMOKE-004 or SMOKE-005 requires separate fresh explicit authorization; source-grounded semantic validation remains outstanding",
    })
    manifest["superseded"].extend([
        {
            "artifact_family": "fta_semantic_smoke_offline_comparator",
            "superseded_versions": ["v1"],
            "current_version": "v2",
            "reason": "v2 applies known-gate direct-quote checks only to AND/OR and validates unknown by null logic_evidence plus an allowed unknown_reason, matching the existing prompt contract.",
        },
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v39"],
            "current_version": "v40",
            "reason": "v40 records the third authorized synthetic observation, preserves the initial comparator diagnostic, and applies a gate-specific offline comparison without promoting readiness.",
        },
    ])

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
        current = V40_PATH.read_text(encoding="utf-8") if V40_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v40 differs from generated content\n")
        smoke = payload["event_scope_semantic_smoke_v1"]
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v40",
            "smoke_status": smoke["status"],
            "completed_case_ids": smoke["completed_case_ids"],
            "not_run_case_ids": smoke["not_run_case_ids"],
            "semantic_acceptance": smoke["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V40_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V40_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
