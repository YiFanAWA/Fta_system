#!/usr/bin/env python3
"""Build active FTA baseline v38 for the single qualitative semantic smoke run."""

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

V37_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v37.json"
V38_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v38.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29_assessment.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29.attempt.json"
COMPARISON_PATH = "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29_offline_comparison.json"
COMPARE_TOOL_PATH = "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py"
COMPARE_TEST_PATH = "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v1.py"

CURRENT_ARTIFACTS = {
    RUN_PATH: (
        "fta-semantic-smoke-SMOKE-001-run", "single_model_run", "current_non_gold_observation",
        "One explicitly authorized DeepSeek call on synthetic SMOKE-001; OR output, strict JSON, zero retries; not expert Gold or accuracy evidence.",
    ),
    ASSESSMENT_PATH: (
        "fta-semantic-smoke-SMOKE-001-assessment", "mechanical_contract_assessment", "current_non_gold_observation",
        "Structure contract valid and all five evidence locations matched; semantic correctness remains unassessed.",
    ),
    ATTEMPT_PATH: (
        "fta-semantic-smoke-SMOKE-001-attempt", "request_attempt_receipt", "current_audit_record",
        "Records exactly one user-authorized request and zero retries without storing credentials or hidden reasoning.",
    ),
    COMPARISON_PATH: (
        "fta-semantic-smoke-SMOKE-001-policy-comparison", "offline_non_gold_comparison", "current_non_gold_observation",
        "Post-run comparison to isolated, authored policy expectation; observed OR matches expected OR; not expert validation or a metric.",
    ),
    COMPARE_TOOL_PATH: (
        "fta-semantic-smoke-offline-comparator-v1", "offline_comparison_tool", "current",
        "Loads reference only after saved model output exists; makes no provider call and rejects any expert-Gold/accuracy promotion.",
    ),
    COMPARE_TEST_PATH: (
        "fta-semantic-smoke-offline-comparator-v1-tests", "offline_comparison_tests", "current",
        "Tests non-Gold comparison bounds, evidence/structure outcome, and refusal to score failed runs or expert-Gold claims.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v37.json": (
        "fta-baseline-manifest-v37-snapshot", "historical_baseline_manifest", "historical",
        "Immutable preparation snapshot: five cases preflighted, no live request performed.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v37.py": (
        "fta-baseline-manifest-v37-builder", "reproducibility_tool", "historical",
        "Builds the immutable pre-run v37 snapshot; superseded as active manifest builder by v38.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v37.py": (
        "fta-baseline-manifest-v37-tests", "manifest_regression_tests", "historical",
        "Protects v37 preflight-only state and label isolation.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v38.py": (
        "fta-baseline-manifest-v38-builder", "reproducibility_tool", "current",
        "Builds active v38 from immutable v37 after validating the single saved run and separate non-Gold comparison.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v38.py": (
        "fta-baseline-manifest-v38-tests", "manifest_regression_tests", "current",
        "Checks one-request scope, non-Gold interpretation, preserved v37 snapshot, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v38-default", "validation_tool", "current",
        "Validates active v38 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v38-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v38 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v38-doc-index", "current_truth_index", "current",
        "Points to active v38 and the single SMOKE-001 run/assessment/comparison.",
    ),
    "docs/current-state-audit.md": (
        "fta-v38-current-state-audit", "current_state_document", "current",
        "Records one qualitative synthetic run while retaining unresolved semantic acceptance and false readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v38-acceptance-record", "acceptance_document", "current",
        "Records actual one-shot invocation, offline non-Gold comparison, tests and artifact validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v38-candidate-generation-policy", "current_fta_policy_document", "current",
        "Explains the one-case semantic observation without promoting it to general accuracy or readiness.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v38-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks completed single-case smoke observation and remaining source-grounded validation.",
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
    v37 = json.loads(V37_PATH.read_text(encoding="utf-8"))
    if v37.get("manifest_id") != "candidate_fta_research_baseline_v37":
        raise ValueError("v38 must extend immutable v37")
    if v37.get("active_baseline", {}).get("fta_ready") is not False:
        raise ValueError("v38 must preserve false FTA readiness")
    if v37.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v38 must preserve false production readiness")
    if v37.get("active_baseline", {}).get("event_scope_prompt_v8_semantic_acceptance") is not False:
        raise ValueError("v38 cannot promote semantic acceptance from one smoke case")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT_PATH).read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / COMPARISON_PATH).read_text(encoding="utf-8"))
    if run.get("status") != "response_received" or run.get("case", {}).get("case_id") != "SMOKE-001":
        raise ValueError("v38 requires the successful saved SMOKE-001 response")
    if run.get("request", {}).get("request_count") != 1 or run.get("request", {}).get("retry_count") != 0:
        raise ValueError("v38 only records one request and zero retries")
    if run.get("request", {}).get("reference_labels_loaded") is not False:
        raise ValueError("reference labels must not enter the model request")
    if assessment.get("case_id") != "SMOKE-001" or assessment.get("output_assessment", {}).get("structure_contract", {}).get("valid") is not True:
        raise ValueError("SMOKE-001 must have a valid structure contract")
    if assessment.get("output_assessment", {}).get("evidence_location_check", {}).get("valid") != 5:
        raise ValueError("SMOKE-001 must retain the observed 5/5 evidence-location check")
    if attempt.get("request_count") != 1 or attempt.get("sdk_max_retries") != 0:
        raise ValueError("attempt receipt must confirm one request with SDK retries disabled")
    if attempt.get("explicit_single_request_authorization") is not True:
        raise ValueError("the saved attempt must record explicit single-request authorization")
    if comparison.get("status") != "matched_authored_policy_expectation_not_expert_validation":
        raise ValueError("comparison must remain a non-expert qualitative policy match")
    if comparison.get("comparison", {}).get("expected_gate") != "OR" or comparison.get("comparison", {}).get("observed_gate") != "OR":
        raise ValueError("SMOKE-001 expected/observed gate record changed")
    claims = comparison.get("claim_boundaries", {})
    if claims.get("human_expert_gold") is not False or claims.get("accuracy_or_calibration_claim_allowed") is not False:
        raise ValueError("SMOKE-001 comparison cannot be promoted to expert Gold or accuracy")

    manifest = deepcopy(v37)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v38"
    manifest["baseline_version"] = "v38"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v37",
        "path": V37_PATH.relative_to(ROOT).as_posix(),
        "reason": "v38 adds one explicitly authorized synthetic SMOKE-001 model observation and a post-run offline comparison to a separate non-expert policy expectation; it does not establish semantic accuracy or readiness.",
    }
    manifest["scope"]["includes"].append(
        "one explicitly user-authorized, no-retry prompt-v8 synthetic semantic smoke request for SMOKE-001, its preserved response/assessment/attempt receipt, and an isolated post-run comparison to a non-expert policy expectation"
    )
    manifest["scope"]["excludes"].extend([
        "expert semantic validation, source-corpus evaluation, aggregate model accuracy/calibration, and generalization claims from the single synthetic SMOKE-001 observation",
        "any model request for SMOKE-002 through SMOKE-005 without separate fresh explicit user authorization",
    ])
    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "one_case_qualitative_match_non_gold",
        "event_scope_semantic_smoke_live_request_performed": True,
        "event_scope_semantic_smoke_requests_performed": 1,
        "event_scope_semantic_smoke_completed_case_ids": ["SMOKE-001"],
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_semantic_smoke_v1"].update({
        "status": "one_case_completed_qualitative_non_gold",
        "live_request_performed": True,
        "request_count": 1,
        "retry_count": 0,
        "completed_case_ids": ["SMOKE-001"],
        "not_run_case_ids": ["SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"],
        "observed_gate": "OR",
        "authored_policy_expected_gate": "OR",
        "policy_expectation_match": True,
        "structure_contract_valid": True,
        "evidence_locations_checked": 5,
        "evidence_locations_valid": 5,
        "semantic_acceptance": False,
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "next_gate": "retain this as a single synthetic behavioral observation; any further model request requires separate fresh explicit authorization; source-grounded semantic validation remains outstanding",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v37"],
        "current_version": "v38",
        "reason": "v38 records the one-case non-Gold model observation and isolated post-run policy comparison while preserving all semantic acceptance and readiness gates as false.",
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
        current = V38_PATH.read_text(encoding="utf-8") if V38_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v38 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v38",
            "smoke_status": payload["event_scope_semantic_smoke_v1"]["status"],
            "completed_case_ids": payload["event_scope_semantic_smoke_v1"]["completed_case_ids"],
            "semantic_acceptance": payload["event_scope_semantic_smoke_v1"]["semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V38_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V38_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
