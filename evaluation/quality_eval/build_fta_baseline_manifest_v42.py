#!/usr/bin/env python3
"""Build active FTA baseline v42 after the authorized SMOKE-005 run."""

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

V41_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v41.json"
V42_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v42.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29_assessment.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29.attempt.json"
COMPARISON_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29_offline_comparison_v2.json"

CURRENT_ARTIFACTS = {
    RUN_PATH: (
        "fta-semantic-smoke-SMOKE-005-run", "single_model_run", "current_non_gold_observation",
        "One explicitly authorized DeepSeek call on synthetic SMOKE-005; unknown gate ignored the unrelated display-color OR, but the one-child tree scope was structurally blocked; zero retries.",
    ),
    ASSESSMENT_PATH: (
        "fta-semantic-smoke-SMOKE-005-assessment", "mechanical_contract_assessment", "current_non_gold_observation",
        "Strict JSON and all three evidence locations are valid, but the single-child gate scope blocks the output; semantic correctness remains unassessed.",
    ),
    ATTEMPT_PATH: (
        "fta-semantic-smoke-SMOKE-005-attempt", "request_attempt_receipt", "current_audit_record",
        "Records exactly one explicitly authorized request and zero SDK retries; no credentials or hidden reasoning stored.",
    ),
    COMPARISON_PATH: (
        "fta-semantic-smoke-SMOKE-005-v2-policy-comparison", "offline_non_gold_comparison", "current_non_gold_observation",
        "Comparator v2 records expected/observed unknown and valid unknown contract, but requires review because the tree structure has a one-child scope; not an overall smoke pass.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v41.json": (
        "fta-baseline-manifest-v41-snapshot", "historical_baseline_manifest", "historical",
        "Immutable active snapshot after SMOKE-004; superseded as active baseline by v42.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v41.py": (
        "fta-baseline-manifest-v41-builder", "reproducibility_tool", "historical",
        "Builds v41 from v40; superseded by v42.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v41.py": (
        "fta-baseline-manifest-v41-tests", "manifest_regression_tests", "historical",
        "Protects historical v41 four-case status and false readiness.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v42.py": (
        "fta-baseline-manifest-v42-builder", "reproducibility_tool", "current",
        "Builds v42 from immutable v41 after verifying SMOKE-005 request, blocked structure assessment, attempt receipt, and v2 comparison.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v42.py": (
        "fta-baseline-manifest-v42-tests", "manifest_regression_tests", "current",
        "Checks five requested cases, SMOKE-005 policy match versus structural blocker distinction, v41 immutability, and false readiness.",
    ),
    "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2", "offline_comparison_tool", "current",
        "Gate-specific offline comparison; makes no provider request and prohibits expert-Gold/accuracy promotion.",
    ),
    "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py": (
        "fta-semantic-smoke-comparator-v2-tests", "offline_comparison_tests", "current",
        "Tests AND/OR direct-quote policy, unknown null-evidence/reason contract, and both structurally valid and blocked saved observations.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v42-default", "validation_tool", "current",
        "Validates active v42 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v42-default", "validation_tool_tests", "current",
        "Covers manifest integrity and active v42 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v42-doc-index", "current_truth_index", "current",
        "Points to active v42 and documents the fifth synthetic case as a policy-gate match with a structural blocker.",
    ),
    "docs/current-state-audit.md": (
        "fta-v42-current-state-audit", "current_state_document", "current",
        "Records all five one-shot cases and preserves the SMOKE-005 structural blocker and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v42-acceptance-record", "acceptance_document", "current",
        "Records the authorized SMOKE-005 request, requires-review comparison, regression results, and v42 artifact validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v42-candidate-generation-policy", "current_fta_policy_document", "current",
        "Explains five synthetic observations and distinguishes expected unknown behavior from a structurally blocked result.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v42-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks the unrelated-OR lexical distractor result and its single-child structural blocker without accuracy claims.",
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
    v41 = json.loads(V41_PATH.read_text(encoding="utf-8"))
    if v41.get("manifest_id") != "candidate_fta_research_baseline_v41":
        raise ValueError("v42 must extend immutable v41")
    active_v41 = v41.get("active_baseline", {})
    if active_v41.get("fta_ready") is not False or active_v41.get("production_ready") is not False:
        raise ValueError("v42 must preserve false FTA and production readiness")
    if active_v41.get("event_scope_prompt_v8_semantic_acceptance") is not False:
        raise ValueError("v42 cannot promote semantic acceptance")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / COMPARISON_PATH).read_text(encoding="utf-8"))
    if run.get("status") != "response_received" or run.get("case", {}).get("case_id") != "SMOKE-005":
        raise ValueError("v42 requires the saved SMOKE-005 response")
    request = run.get("request", {})
    if request.get("request_count") != 1 or request.get("retry_count") != 0 or request.get("sdk_max_retries") != 0:
        raise ValueError("SMOKE-005 must record one request and zero retries")
    if request.get("finish_reason") != "stop" or request.get("reference_labels_loaded") is not False or request.get("gold_included_in_model_input") is not False:
        raise ValueError("SMOKE-005 must be complete and label-free")
    if assessment.get("case_id") != "SMOKE-005":
        raise ValueError("SMOKE-005 assessment case id is required")
    output = assessment.get("output_assessment", {})
    structure = output.get("structure_contract", {})
    evidence_check = output.get("evidence_location_check", {})
    if output.get("strict_json_parsed") is not True or output.get("assessment_status") != "blocked":
        raise ValueError("SMOKE-005 must preserve its parsed, blocked assessment")
    blockers = structure.get("blockers", [])
    if structure.get("valid") is not False or len(blockers) != 1:
        raise ValueError("SMOKE-005 must preserve its single structural blocker")
    if blockers[0].get("code") != "gate_scope_requires_at_least_two_children" or blockers[0].get("child_count") != 1:
        raise ValueError("SMOKE-005 blocker must identify its one-child gate scope")
    if evidence_check.get("checked") != 3 or evidence_check.get("valid") != 3:
        raise ValueError("SMOKE-005 must retain its 3/3 evidence-location result")
    if output.get("semantic_correctness") != "not_assessed" or output.get("human_expert_gold") is not False:
        raise ValueError("SMOKE-005 must remain semantically unassessed and non-Gold")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0 or attempt.get("explicit_single_request_authorization") is not True:
        raise ValueError("attempt receipt must confirm one explicit authorization and zero SDK retries")
    if comparison.get("artifact_version") != "v2" or comparison.get("case_id") != "SMOKE-005":
        raise ValueError("v2 comparison artifact for SMOKE-005 is required")
    if comparison.get("status") != "requires_review":
        raise ValueError("SMOKE-005 overall comparison must remain requires_review")
    compared = comparison.get("comparison", {})
    if (
        compared.get("expected_gate") != "unknown"
        or compared.get("observed_gate") != "unknown"
        or compared.get("gate_matches_policy_expectation") is not True
        or compared.get("unknown_gate_contract_valid") is not True
        or compared.get("decisive_source_quote_present_in_input") is not True
        or compared.get("structure_contract_valid") is not False
        or compared.get("evidence_locations_checked") != 3
        or compared.get("evidence_locations_valid") != 3
        or compared.get("qualitative_smoke_match") is not False
    ):
        raise ValueError("v2 comparison must distinguish the unknown gate match from the structure blocker")
    parsed = run.get("model_output", {}).get("parsed_json", {})
    gates = parsed.get("gates") if isinstance(parsed, dict) else None
    if not isinstance(gates, list) or len(gates) != 1:
        raise ValueError("SMOKE-005 must preserve exactly one gate scope")
    gate = gates[0]
    if gate.get("gate") != "unknown" or gate.get("logic_evidence") is not None:
        raise ValueError("SMOKE-005 output must keep unknown without logic evidence")
    if gate.get("unknown_reason") not in ALLOWED_UNKNOWN_REASONS:
        raise ValueError("SMOKE-005 output must contain an allowed unknown reason")
    if len(gate.get("child_node_ids", [])) != 1:
        raise ValueError("SMOKE-005 raw output must retain its one-child scope")
    claims = comparison.get("claim_boundaries", {})
    if claims.get("human_expert_gold") is not False or claims.get("accuracy_or_calibration_claim_allowed") is not False:
        raise ValueError("SMOKE-005 comparison cannot be promoted to expert Gold or accuracy")
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
        raise ValueError("SMOKE-005 comparison provenance must bind the exact run, assessment, and non-Gold reference")

    manifest = deepcopy(v41)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v42"
    manifest["baseline_version"] = "v42"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v41",
        "path": V41_PATH.relative_to(ROOT).as_posix(),
        "reason": "v42 records the authorized SMOKE-005 run: the unknown gate ignores an unrelated lexical OR, but the one-child scope is structurally blocked; no semantic acceptance or readiness is claimed.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly user-authorized, no-retry prompt-v8 synthetic SMOKE-005 model request and its preserved response, blocked assessment, attempt receipt, and v2 requires-review comparison"
    )
    manifest["scope"]["excludes"] = [
        item.replace(
            "any model request for SMOKE-005 without separate fresh explicit user authorization",
            "any further model request or retry for SMOKE-005",
        )
        for item in manifest["scope"].get("excludes", [])
    ]
    manifest["scope"]["excludes"].append(
        "treating SMOKE-005 as an overall qualitative pass despite its expected unknown gate, because the generated one-child scope fails the tree structure contract"
    )
    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "four_policy_matches_one_structure_blocked_non_gold",
        "event_scope_semantic_smoke_requests_performed": 5,
        "event_scope_semantic_smoke_completed_case_ids": ["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"],
        "event_scope_semantic_smoke_comparator_version": "v2_gate_specific_evidence_contract_v1",
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    smoke = manifest["event_scope_semantic_smoke_v1"]
    smoke["status"] = "five_cases_run_four_policy_matches_one_structure_blocked_non_gold"
    smoke["request_count"] = 5
    smoke["retry_count"] = 0
    smoke["completed_case_ids"] = ["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"]
    smoke["not_run_case_ids"] = []
    smoke["case_results"].append({
        "case_id": "SMOKE-005",
        "expected_gate": "unknown",
        "observed_gate": "unknown",
        "policy_expectation_match": True,
        "overall_comparison_status": "requires_review",
        "unknown_gate_contract_valid": True,
        "unknown_reason": gate["unknown_reason"],
        "structure_contract_valid": False,
        "structure_blocker_codes": ["gate_scope_requires_at_least_two_children"],
        "evidence_locations_checked": 3,
        "evidence_locations_valid": 3,
        "qualitative_smoke_match": False,
    })
    smoke["evidence_locations_checked"] = 22
    smoke["evidence_locations_valid"] = 22
    smoke["semantic_acceptance"] = False
    smoke["human_expert_gold"] = False
    smoke["accuracy_or_calibration_claim_allowed"] = False
    smoke["next_gate"] = "retain SMOKE-005 as an expected-unknown gate observation with a structural blocker; do not retry; source-grounded semantic validation remains outstanding"
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v41"],
        "current_version": "v42",
        "reason": "v42 records all five authorized synthetic smoke requests, including the SMOKE-005 unknown-gate policy match and its one-child structural blocker; readiness remains false.",
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
        current = V42_PATH.read_text(encoding="utf-8") if V42_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v42 differs from generated content\n")
        smoke = payload["event_scope_semantic_smoke_v1"]
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v42",
            "smoke_status": smoke["status"],
            "completed_case_ids": smoke["completed_case_ids"],
            "not_run_case_ids": smoke["not_run_case_ids"],
            "evidence_locations_checked": smoke["evidence_locations_checked"],
            "semantic_acceptance": smoke["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V42_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V42_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
