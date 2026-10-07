#!/usr/bin/env python3
"""Build active FTA baseline v49 with the P2 real-source contract audit."""

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


V48_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v48.json"
V49_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v49.json"
EXPECTED_V48_SHA256 = "5069522f51b9892004dc6e10d43a1b070f40562f295bf2adc6cc7d150bd469ca"
AUDIT_JSON_PATH = "evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.json"
AUDIT_MD_PATH = "evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.md"
PLAN_PATH = "docs/fta-validation-reliability-plan-v1.md"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v48.json": (
        "fta-baseline-manifest-v48-snapshot", "historical_baseline_manifest", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v48.py": (
        "fta-baseline-manifest-v48-builder", "reproducibility_tool", "historical",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v48.py": (
        "fta-baseline-manifest-v48-tests", "manifest_regression_tests", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v49.py": (
        "fta-baseline-manifest-v49-builder", "reproducibility_tool", "current",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v49.py": (
        "fta-baseline-manifest-v49-tests", "manifest_regression_tests", "current",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v49-default", "validation_tool", "current",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v49-default", "validation_tool_tests", "current",
    ),
    AUDIT_JSON_PATH: (
        "fta-real-source-contract-audit-v1-json", "engineering_audit_artifact", "current",
    ),
    AUDIT_MD_PATH: (
        "fta-real-source-contract-audit-v1-report", "engineering_audit_report", "current",
    ),
    "backend-python/fta/cause_disposition_service.py": (
        "fta-cause-disposition-current-source", "semantic_disposition_owner", "current",
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "candidate-fta-current-source", "candidate_tree_owner", "current",
    ),
    "backend-python/tests/test_fta_cause_disposition.py": (
        "fta-cause-disposition-current-tests", "contract_regression_tests", "current",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-extraction-tests", "contract_regression_tests", "current",
    ),
    "backend-python/tests/test_recursive_candidate_fta_extraction_service.py": (
        "recursive-candidate-fta-tests", "contract_regression_tests", "current",
    ),
    "backend-python/tests/test_candidate_fta_application_service.py": (
        "candidate-fta-application-tests", "contract_regression_tests", "current",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v8.py": (
        "event-scope-tree-prompt-v8", "evaluation_policy", "current",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v8.py": (
        "event-scope-tree-prompt-v8-tests", "evaluation_policy_tests", "current",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py": (
        "event-scope-model-runner-v6", "bounded_evaluation_runner", "current",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v6.py": (
        "event-scope-model-runner-v6-tests", "bounded_evaluation_runner_tests", "current",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.json": (
        "historical-f01681-cause-disposition-v4", "historical_model_run", "historical",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_2026-09-28.json": (
        "historical-f30027-cause-disposition-v2", "historical_model_run", "historical",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_cause_disposition_v2_2026-09-28.json": (
        "historical-f30021-cause-disposition-v2", "historical_model_run", "historical",
    ),
    "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_cause_disposition_v2_2026-09-28.json": (
        "historical-f06000-cause-disposition-v2", "historical_model_run", "historical",
    ),
    "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_cause_disposition_v2_2026-09-28.json": (
        "historical-f35400-cause-disposition-v2", "historical_model_run", "historical",
    ),
    "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json": (
        "historical-nasa-figure7-event-scope-v6", "historical_model_run", "historical",
    ),
    "docs/README.md": (
        "fta-v49-doc-index", "current_truth_index", "current",
    ),
    "docs/current-state-audit.md": (
        "fta-v49-current-state-audit", "current_state_document", "current",
    ),
    "docs/acceptance.md": (
        "fta-v49-acceptance-record", "acceptance_document", "current",
    ),
    PLAN_PATH: (
        "fta-v49-validation-plan-status", "active_validation_plan", "current",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v49-candidate-generation-policy", "current_fta_policy_document", "current",
    ),
}


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V48_PATH) != EXPECTED_V48_SHA256:
        raise ValueError("v48 snapshot hash changed; refusing to derive v49")
    source = json.loads(V48_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v48":
        raise ValueError("v49 must derive from the preserved v48 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v49 must preserve false FTA and production readiness")

    audit = json.loads((ROOT / AUDIT_JSON_PATH).read_text(encoding="utf-8"))
    if (
        audit.get("artifact_type") != "fta_real_source_development_contract_audit"
        or audit.get("artifact_version") != "v1"
        or audit.get("audit_status") != "completed_read_only_contract_and_historical_run_audit"
        or audit.get("reviewer_provenance") != "agent_engineering_audit_not_human_expert_review"
        or audit.get("safety_scope", {}).get("model_requests_performed") != 0
        or audit.get("safety_scope", {}).get("gold_changed") is not False
        or audit.get("safety_scope", {}).get("database_written") is not False
        or audit.get("safety_scope", {}).get("production_api_called") is not False
        or audit.get("safety_scope", {}).get("fta_ready") is not False
        or audit.get("current_runtime", {}).get("cause_disposition_prompt_version") != "fta-cause-disposition-v5"
    ):
        raise ValueError("P2 audit does not meet provenance, no-call, and current-version requirements")
    expected_cases = {"F01681", "F30027", "F30021", "F06000", "F35400", "NASA-Figure-7"}
    observed_cases = {item.get("case_id") for item in audit.get("cases", []) if isinstance(item, dict)}
    if observed_cases != expected_cases:
        raise ValueError("P2 audit case set does not match the approved six-case scope")
    for item in audit.get("offline_verification", []):
        if not isinstance(item, dict) or item.get("result") != "passed":
            raise ValueError("P2 audit contains a missing or failed offline verification")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v49"
    manifest["baseline_version"] = "v49"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V48_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V48_SHA256,
        "reason": "Records the read-only P2 audit of six real-source development cases, current cause-disposition v5 contract, offline regression results, and historical prompt-version boundary; no model call, Gold/database/production write, or readiness promotion.",
    }
    manifest["scope"]["includes"].append(
        "P2 read-only contract and historical-run audit for F01681, F30027, F30021, F06000, F35400, and NASA Figure 7, with no model request"
    )
    manifest["scope"]["excludes"].append(
        "current v5 real-source model results, semantic defect closure, expert Gold, independent Final, and readiness promotion"
    )

    plan = manifest.setdefault("next_stage_plan_v1", {})
    plan.update({
        "path": PLAN_PATH,
        "status": "in_progress_P2_contract_and_historical_case_audit_complete_live_validation_pending",
        "current_stage": "P2_real_source_development_semantics",
        "milestones": {
            "P0_status_and_offline_contracts": "complete_within_documented_scope",
            "P1_observation_live_boundary": "complete_for_one_synthetic_non_gold_case; no aggregate accuracy or generalization claim",
            "P2_real_source_development_semantics": "contract_and_six_case_historical_audit_complete; current v5 real-source runs pending fresh explicit authorization",
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
        "p2_current_model_run_performed": False,
        "p2_model_requests_performed_this_audit": 0,
        "p2_semantic_defects_closed": 0,
        "p2_next_action_requires_fresh_explicit_authorization": True,
        "p2_audit_artifact": AUDIT_JSON_PATH,
        "p2_audit_report": AUDIT_MD_PATH,
        "runtime_behavior_changed": False,
        "gold_or_database_changed": False,
    })
    manifest["active_baseline"]["execution_plan_path"] = PLAN_PATH
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v48"],
        "current_version": "v49",
        "reason": "v49 records the P2 read-only contract and historical-case audit; current-version semantic validation remains pending and readiness remains false.",
    })

    for path, (artifact_id, kind, lifecycle) in CURRENT_ARTIFACTS.items():
        _register(manifest["artifacts"], path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v49 records an engineering-only P2 historical audit; archived outputs stay historical, no model call or readiness promotion occurred.",
        })

    repo_root = ROOT.resolve(strict=True)
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id, path = artifact["artifact_id"], artifact["path"]
        if artifact_id in seen_ids or path in seen_paths:
            raise ValueError(f"duplicate artifact identity: {artifact_id} / {path}")
        seen_ids.add(artifact_id)
        seen_paths.add(path)
        target = (ROOT / path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {path}")
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
        if not V49_PATH.exists() or V49_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v49 differs from generated content\n")
    else:
        V49_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "baseline_version": "v49",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "p2_historical_case_audit_count": 6,
        "p2_current_model_run_performed": False,
        "p2_semantic_defects_closed": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
