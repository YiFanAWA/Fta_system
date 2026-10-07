#!/usr/bin/env python3
"""Build active FTA baseline v48 with the authorized P1 observation-boundary run."""

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


V47_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v47.json"
V48_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v48.json"
EXPECTED_V47_SHA256 = "e030a7f405c7c1bc3c503b8a9954bce4dcf584e0a7bfbbf3be0cd5e900dbf62a"
PLAN_PATH = "docs/fta-validation-reliability-plan-v1.md"
RUN_PATH = "evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json"
REPORT_PATH = "evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.md"
EXPECTED_RUN_SHA256 = "6db1d6bad2e6a42b04c50bd3919d148c59b86ee97c23318a5a9dcbf175159f58"
EXPECTED_REPORT_SHA256 = "4a81a34dd150765bae49638e97755541ba510d4caa761106ccab218ad01449f2"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v47.json": (
        "fta-baseline-manifest-v47-snapshot", "historical_baseline_manifest", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v47.py": (
        "fta-baseline-manifest-v47-builder", "reproducibility_tool", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v48.py": (
        "fta-baseline-manifest-v48-builder", "reproducibility_tool", "current",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v48.py": (
        "fta-baseline-manifest-v48-tests", "manifest_regression_tests", "current",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v48-default", "validation_tool", "current",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v48-default", "validation_tool_tests", "current",
    ),
    "evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py": (
        "candidate-fta-observation-boundary-probe-v1", "evaluation_runner", "current",
    ),
    "evaluation/quality_eval/public_sources/test_probe_candidate_fta_observation_boundary_v1.py": (
        "candidate-fta-observation-boundary-probe-tests", "evaluation_tests", "current",
    ),
    RUN_PATH: ("candidate-fta-observation-boundary-run-v3", "model_run_artifact", "current"),
    REPORT_PATH: ("candidate-fta-observation-boundary-report-v3", "model_run_report", "current"),
    "docs/README.md": ("fta-v48-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": (
        "fta-v48-current-state-audit", "current_state_document", "current",
    ),
    "docs/acceptance.md": ("fta-v48-acceptance-record", "acceptance_document", "current"),
    PLAN_PATH: ("fta-v48-next-stage-plan", "active_validation_plan", "current"),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v48-candidate-generation-policy", "current_fta_policy_document", "current",
    ),
}


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V47_PATH) != EXPECTED_V47_SHA256:
        raise ValueError("v47 snapshot hash changed; refusing to derive v48")
    if _sha256(ROOT / RUN_PATH) != EXPECTED_RUN_SHA256:
        raise ValueError("P1 run JSON hash changed; refusing to register another response")
    if _sha256(ROOT / REPORT_PATH) != EXPECTED_REPORT_SHA256:
        raise ValueError("P1 run report hash changed; refusing to register altered report")
    source = json.loads(V47_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v47":
        raise ValueError("v48 must derive from the preserved v47 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v48 must preserve false FTA and production readiness")

    run = json.loads((ROOT / RUN_PATH).read_text(encoding="utf-8"))
    if (
        run.get("case_id") != "OBSERVATION-COOCCURRENCE-001"
        or run.get("request_attempt_count") != 1
        or run.get("successful_response_count") != 1
        or run.get("run_status") != "response_received"
        or run.get("tree_status") != "blocked"
        or run.get("policy_assessment", {}).get("policy_boundary_match") is not True
        or run.get("model", {}).get("max_model_calls") != 1
        or run.get("model", {}).get("sdk_max_retries") != 0
        or run.get("model", {}).get("outer_retries") != 0
        or run.get("formal_gold") is not False
        or run.get("human_expert_gold") is not False
        or run.get("database_written") is not False
        or run.get("production_api_called") is not False
    ):
        raise ValueError("P1 run does not satisfy its recorded scope and safety contract")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v48"
    manifest["baseline_version"] = "v48"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V47_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V47_SHA256,
        "reason": "Records one authorized, single-request, synthetic non-Gold observation-boundary development run; no Gold, database, production API, or readiness change.",
    }
    manifest["scope"]["includes"].append(
        "one authorized P1 live-model behavior observation on a synthetic non-Gold alarm-cooccurrence input, with raw response and exact-quote evidence audit"
    )
    previous_exclusion = (
        "new live-model semantic validation, Gold/database writes, production API changes, and readiness promotion"
    )
    if previous_exclusion in manifest["scope"].get("excludes", []):
        manifest["scope"]["excludes"].remove(previous_exclusion)
    manifest["scope"]["excludes"].append(
        "general accuracy, expert-Gold, calibration, or source-generalization claims from this single synthetic observation-boundary run"
    )

    plan = manifest.setdefault("next_stage_plan_v1", {})
    plan.update({
        "path": PLAN_PATH,
        "status": "in_progress_P1_narrow_synthetic_boundary_complete_P2_next",
        "current_stage": "P2_real_source_development_semantics",
        "milestones": {
            "P0_status_and_offline_contracts": "complete_within_documented_scope",
            "P1_observation_live_boundary": "complete_for_one_synthetic_non_gold_case; no aggregate accuracy or generalization claim",
            "P2_real_source_development_semantics": "next; audit cases and contracts before any separately authorized live runs",
            "P3_independent_gold_and_source_isolation": "pending",
            "P4_frozen_final_validation": "pending",
            "P5_scoped_structure_acceptance": "pending",
            "P6_production_shadow_and_api": "pending_separate_design",
            "P7_quantitative_fta": "pending_real_device_data",
        },
        "live_model_request_performed": True,
        "runtime_behavior_changed": False,
        "gold_or_database_changed": False,
        "observation_runner_previous_max_model_calls": 3,
        "observation_runner_current_max_model_calls": 1,
        "observation_runner_preflight_max_model_calls": 1,
        "observation_single_request_budget_gate_verified": True,
        "observation_budget_gate_test_count": 7,
        "observation_runner_live_validation_performed": True,
        "observation_runner_actual_model_request_count": 1,
        "observation_runner_live_sample_status": "single_synthetic_non_gold_boundary_match",
        "observation_runner_policy_boundary_match": True,
        "observation_runner_unique_exact_evidence_reference_count": 5,
        "observation_runner_run_artifact": RUN_PATH,
        "observation_runner_run_sha256": EXPECTED_RUN_SHA256,
        "observation_runner_response_sha256": "075767d8b219f7df7528988138f83c50f231fcf6d17f340e3978f2f59c35e52c",
        "observation_runner_prompt_sha256": "032cc045af891f704828e0913f150a4f411910211205bcf820913ebb57343567",
        "governance_debt": "existing_root_AGENTS_missing_four_adoption_guardrail_snippets",
    })
    manifest["active_baseline"]["execution_plan_path"] = PLAN_PATH
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v47"],
        "current_version": "v48",
        "reason": "v48 records the authorized single synthetic observation-boundary run and P1's narrow pass; v47 remains immutable.",
    })

    for path, (artifact_id, kind, lifecycle) in CURRENT_ARTIFACTS.items():
        _register(manifest["artifacts"], path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v48 records the single authorized synthetic P1 boundary run and P1/P2 plan state; no Gold, database, production API, or readiness change.",
        })

    repo_root = ROOT.resolve(strict=True)
    seen_ids, seen_paths = set(), set()
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
        if not V48_PATH.exists() or V48_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v48 differs from generated content\n")
    else:
        V48_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "baseline_version": "v48",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "live_model_request_performed": True,
        "observation_runner_actual_model_request_count": 1,
        "p1_narrow_policy_boundary_match": True,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
