#!/usr/bin/env python3
"""Build active FTA baseline v50 with the bounded F30021 current-prompt run."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.build_fta_baseline_manifest_v45 import _register, _sha256  # noqa: E402


V49_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v49.json"
V50_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v50.json"
EXPECTED_V49_SHA256 = "109390949c9e73aa6f294604a93936ca980df85ffa0764b489ddc700f52c098e"
RAW_JSON = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json"
RAW_MD = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.md"
OFFLINE_V1_JSON = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v1_2026-10-07.json"
OFFLINE_V1_MD = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v1_2026-10-07.md"
OFFLINE_V2_JSON = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.json"
OFFLINE_V2_MD = "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.md"
AUDIT_JSON = "evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.json"
AUDIT_MD = "evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.md"


ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v49.json": ("fta-baseline-manifest-v49-snapshot", "historical_baseline_manifest", "historical"),
    "evaluation/quality_eval/build_fta_baseline_manifest_v49.py": ("fta-baseline-manifest-v49-builder", "reproducibility_tool", "historical"),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v49.py": ("fta-baseline-manifest-v49-tests", "manifest_regression_tests", "historical"),
    "evaluation/quality_eval/build_fta_baseline_manifest_v50.py": ("fta-baseline-manifest-v50-builder", "reproducibility_tool", "current"),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v50.py": ("fta-baseline-manifest-v50-tests", "manifest_regression_tests", "current"),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-v50-default", "validation_tool", "current"),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-tests-v50-default", "validation_tool_tests", "current"),
    "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py": ("candidate-fta-raw-source-runner-current", "bounded_evaluation_runner", "current"),
    "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py": ("candidate-fta-raw-source-runner-tests-current", "bounded_evaluation_runner_tests", "current"),
    RAW_JSON: ("f30021-current-v5-raw-model-run-json", "raw_model_run", "current"),
    RAW_MD: ("f30021-current-v5-raw-model-run-report", "raw_model_run_report", "current"),
    OFFLINE_V1_JSON: ("f30021-current-v5-offline-audit-v1-json", "historical_derived_run_audit", "historical"),
    OFFLINE_V1_MD: ("f30021-current-v5-offline-audit-v1-report", "historical_derived_run_report", "historical"),
    OFFLINE_V2_JSON: ("f30021-current-v5-offline-audit-v2-json", "derived_run_audit", "current"),
    OFFLINE_V2_MD: ("f30021-current-v5-offline-audit-v2-report", "derived_run_report", "current"),
    AUDIT_JSON: ("fta-real-source-case-audit-v2-json", "engineering_audit_artifact", "current"),
    AUDIT_MD: ("fta-real-source-case-audit-v2-report", "engineering_audit_report", "current"),
    "backend-python/extraction/text_extraction_adapter.py": ("text-extraction-adapter-current", "evidence_occurrence_source_owner", "current"),
    "backend-python/contracts/extraction_contract.py": ("extraction-evidence-contract-current", "evidence_contract", "current"),
    "backend-python/fta/cause_disposition_service.py": ("fta-cause-disposition-current-source", "semantic_disposition_owner", "current"),
    "backend-python/tests/test_evidence_mapping.py": ("text-evidence-mapping-regressions-current", "evidence_regression_tests", "current"),
    "backend-python/tests/test_fta_cause_disposition.py": ("fta-cause-disposition-regressions-current", "contract_regression_tests", "current"),
    "docs/README.md": ("fta-v50-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": ("fta-v50-current-state-audit", "current_state_document", "current"),
    "docs/acceptance.md": ("fta-v50-acceptance-record", "acceptance_document", "current"),
    "docs/fta-validation-reliability-plan-v1.md": ("fta-v50-validation-plan", "active_validation_plan", "current"),
    "docs/candidate-fta-generation-v1.md": ("fta-v50-candidate-generation-policy", "current_fta_policy_document", "current"),
}


def _load_json(relative_path: str) -> dict:
    payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {relative_path}")
    return payload


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V49_PATH) != EXPECTED_V49_SHA256:
        raise ValueError("v49 snapshot hash changed; refusing to derive v50")
    source = _load_json("evaluation/quality_eval/fta_baseline_manifest_v49.json")
    if source.get("manifest_id") != "candidate_fta_research_baseline_v49":
        raise ValueError("v50 must derive from the preserved v49 snapshot")
    if source.get("active_baseline", {}).get("fta_ready") is not False or source.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v50 must preserve false global readiness")

    run = _load_json(RAW_JSON)
    audit = _load_json(AUDIT_JSON)
    derivative = _load_json(OFFLINE_V2_JSON)
    if (
        run.get("artifact_type") != "candidate_fta_raw_source_development_probe"
        or run.get("source", {}).get("sample_id") != "SIEMENS_S210_2019_F30021"
        or run.get("prompt_versions", {}).get("cause_disposition") != "fta-cause-disposition-v5"
        or run.get("model", {}).get("request_attempt_count") != 4
        or run.get("model", {}).get("outer_max_retries") != 0
        or run.get("model", {}).get("sdk_max_retries") != 0
        or run.get("request_budget", {}).get("max_model_calls") != 4
        or run.get("request_budget", {}).get("calls_started") != 4
        or audit.get("audit_status") != "completed_single_case_current_prompt_run_blocked_with_findings"
        or audit.get("reviewer_provenance") != "agent_engineering_audit_of_user_authorized_live_model_run_not_human_expert_review"
        or audit.get("run", {}).get("model_calls") != 4
        or audit.get("run", {}).get("cause_disposition_prompt_version") != "fta-cause-disposition-v5"
        or audit.get("final_outcome", {}).get("status") != "blocked"
        or audit.get("final_outcome", {}).get("semantic_defects_closed") != 0
        or derivative.get("cause_disposition_counts") != {"fta_event_candidate": 3, "relation_only": 1, "unresolved": 1}
        or audit.get("readiness", {}).get("fta_ready") is not False
        or audit.get("readiness", {}).get("production_ready") is not False
    ):
        raise ValueError("F30021 run/audit does not match the authorized bounded blocked-run evidence")
    if run.get("model", {}).get("request_attempt_count") > run.get("request_budget", {}).get("max_model_calls"):
        raise ValueError("F30021 run exceeded its request budget")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v50"
    manifest["baseline_version"] = "v50"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V49_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V49_SHA256,
        "reason": "Records one explicitly authorized F30021 current cause-disposition v5 run (4 provider calls, zero retries), its fail-closed blocked outcome, and offline audit; no semantic defect was closed and no Gold/database/readiness changed.",
    }
    manifest["scope"]["includes"].append(
        "one user-authorized current-prompt v5 F30021 raw-source development run, its immutable raw responses, host-effective evidence audit, and runner request-budget regression"
    )
    manifest["scope"]["includes"].append(
        "offline F30021 repeated-cause occurrence regression proving both Possible causes and Fault value spans are retained and the cause remains unresolved without automatic location selection"
    )
    manifest["scope"]["excludes"].append(
        "expert semantic approval, formal Gold, accuracy/calibration/generalization claims, automatic evidence disambiguation, and global or production readiness promotion"
    )
    manifest["active_baseline"].update({
        "cause_disposition_prompt": "fta-cause-disposition-v5",
        "latest_real_source_development_run": RAW_JSON,
        "latest_real_source_development_run_status": "blocked_on_ambiguous_evidence_and_incomplete_child_set",
        "latest_real_source_model_calls": 4,
        "latest_real_source_retries": 0,
        "latest_real_source_semantic_acceptance": False,
        "fta_ready": False,
        "production_ready": False,
    })

    plan = manifest.setdefault("next_stage_plan_v1", {})
    plan.update({
        "path": "docs/fta-validation-reliability-plan-v1.md",
        "status": "in_progress_P2_current_prompt_single_case_blocked_occurrence_scope_design_next",
        "current_stage": "P2_real_source_development_semantics",
        "milestones": {
            "P0_status_and_offline_contracts": "complete_within_documented_scope",
            "P1_observation_live_boundary": "complete_for_one_synthetic_non_gold_case; no aggregate accuracy or generalization claim",
            "P2_real_source_development_semantics": "one current v5 F30021 run completed with 4 calls and zero retries; blocked by repeated occurrence evidence, ambiguous top-event quote, incomplete child set, and unavailable gate confidence policy; semantic defects closed 0",
            "P3_independent_gold_and_source_isolation": "pending",
            "P4_frozen_final_validation": "pending",
            "P5_scoped_structure_acceptance": "pending",
            "P6_production_shadow_and_api": "pending_separate_design",
            "P7_quantitative_fta": "pending_real_device_data",
        },
        "p2_contract_audit_complete": True,
        "p2_historical_case_audit_complete": True,
        "p2_historical_case_count": 6,
        "p2_current_cause_disposition_prompt_version": "fta-cause-disposition-v5",
        "p2_current_model_run_performed": True,
        "p2_model_requests_performed_this_run": 4,
        "p2_model_request_limit_this_run": 4,
        "p2_model_retries_performed": 0,
        "p2_current_run_sample_id": "SIEMENS_S210_2019_F30021",
        "p2_current_run_status": "blocked",
        "p2_semantic_defects_closed": 0,
        "p2_occurrence_scope_regression_status": "passed_fail_closed_with_both_exact_offsets_and_context_spans",
        "p2_occurrence_scope_regression_test_count": 2,
        "p2_backend_targeted_test_count": 86,
        "p2_runner_test_count": 15,
        "p2_event_scope_test_count": 8,
        "p2_shared_evidence_contract_changed": False,
        "p2_host_effective_dispositions": {"fta_event_candidate": 3, "relation_only": 1, "unresolved": 1},
        "p2_next_action": "continue offline source-occurrence/manual-review boundary audit; do not select a repeated match automatically",
        "p2_next_model_request_requires_fresh_explicit_authorization": True,
        "p2_run_artifact": RAW_JSON,
        "p2_offline_audit_artifact": OFFLINE_V2_JSON,
        "p2_case_audit_artifact": AUDIT_JSON,
        "runtime_behavior_changed": False,
        "gold_or_database_changed": False,
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v49"],
        "current_version": "v50",
        "reason": "v50 records the bounded F30021 current-prompt run and its blocked offline audit; v49 remains immutable as the pre-run state snapshot.",
    })

    for relative_path, (artifact_id, kind, lifecycle) in ARTIFACTS.items():
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v50 records one bounded F30021 development run; original responses are retained, ambiguity is not auto-repaired, and readiness remains false.",
        })

    repo_root = ROOT.resolve(strict=True)
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id, relative_path = artifact["artifact_id"], artifact["path"]
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact identity: {artifact_id} / {relative_path}")
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
        if not V50_PATH.exists() or V50_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v50 differs from generated content\n")
    else:
        V50_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "baseline_version": "v50",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "p2_current_run": payload["next_stage_plan_v1"]["p2_current_run_status"],
        "p2_model_calls": payload["next_stage_plan_v1"]["p2_model_requests_performed_this_run"],
        "p2_retries": payload["next_stage_plan_v1"]["p2_model_retries_performed"],
        "p2_semantic_defects_closed": payload["next_stage_plan_v1"]["p2_semantic_defects_closed"],
        "p2_occurrence_scope_regression": payload["next_stage_plan_v1"]["p2_occurrence_scope_regression_status"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
