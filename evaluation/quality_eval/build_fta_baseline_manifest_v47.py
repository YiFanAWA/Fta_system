#!/usr/bin/env python3
"""Build active FTA baseline v47 with the observation-runner request budget gate."""

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


V46_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v46.json"
V47_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v47.json"
EXPECTED_V46_SHA256 = "7b3eae91b7d591273332e276e17e8629397f53ab2ad1c392e15491ec1d13e547"
PLAN_PATH = "docs/fta-validation-reliability-plan-v1.md"
RUNNER_PATH = "evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py"
RUNNER_TEST_PATH = "evaluation/quality_eval/public_sources/test_probe_candidate_fta_observation_boundary_v1.py"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v46.json": (
        "fta-baseline-manifest-v46-snapshot", "historical_baseline_manifest", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v46.py": (
        "fta-baseline-manifest-v46-builder", "reproducibility_tool", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v47.py": (
        "fta-baseline-manifest-v47-builder", "reproducibility_tool", "current",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v47.py": (
        "fta-baseline-manifest-v47-tests", "manifest_regression_tests", "current",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v47-default", "validation_tool", "current",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v47-default", "validation_tool_tests", "current",
    ),
    RUNNER_PATH: (
        "candidate-fta-observation-boundary-probe-v1", "evaluation_runner", "current",
    ),
    RUNNER_TEST_PATH: (
        "candidate-fta-observation-boundary-probe-tests", "evaluation_tests", "current",
    ),
    "docs/README.md": ("fta-v47-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": (
        "fta-v47-current-state-audit", "current_state_document", "current",
    ),
    "docs/acceptance.md": ("fta-v47-acceptance-record", "acceptance_document", "current"),
    PLAN_PATH: ("fta-v47-next-stage-plan", "active_validation_plan", "current"),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v47-candidate-generation-policy", "current_fta_policy_document", "current",
    ),
}


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V46_PATH) != EXPECTED_V46_SHA256:
        raise ValueError("v46 snapshot hash changed; refusing to derive v47")
    source = json.loads(V46_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v46":
        raise ValueError("v47 must derive from the preserved v46 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v47 must preserve false FTA and production readiness")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v47"
    manifest["baseline_version"] = "v47"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V46_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V46_SHA256,
        "reason": "Records the one-request budget gate and offline/preflight verification for the observation-only FTA runner; no live model request, Gold write, database write, or production behavior change.",
    }
    manifest["scope"]["includes"].append(
        "single-provider-request ceiling and offline budget-exceeded preservation behavior for the observation-only Candidate FTA runner"
    )
    manifest["scope"]["excludes"].append(
        "new live-model semantic validation, Gold/database writes, production API changes, and readiness promotion"
    )
    plan = manifest.setdefault("next_stage_plan_v1", {})
    plan.update({
        "path": PLAN_PATH,
        "status": "in_progress_offline_budget_gate_complete_live_validation_pending_authorization",
        "current_stage": "P1_observation_live_boundary_verification",
        "milestones": {
            "P0_status_and_offline_contracts": "complete_within_documented_scope",
            "P1_observation_live_boundary": "offline_single_request_budget_gate_verified_live_run_pending_fresh_explicit_authorization",
            "P2_real_source_development_semantics": "pending",
            "P3_independent_gold_and_source_isolation": "pending",
            "P4_frozen_final_validation": "pending",
            "P5_scoped_structure_acceptance": "pending",
            "P6_production_shadow_and_api": "pending_separate_design",
            "P7_quantitative_fta": "pending_real_device_data",
        },
        "live_model_request_performed": False,
        "runtime_behavior_changed": False,
        "gold_or_database_changed": False,
        "observation_runner_previous_max_model_calls": 3,
        "observation_runner_current_max_model_calls": 1,
        "observation_runner_preflight_max_model_calls": 1,
        "observation_single_request_budget_gate_verified": True,
        "observation_budget_gate_test_count": 7,
        "observation_runner_live_validation_performed": False,
        "observation_runner_preflight_output_available": True,
        "governance_debt": "existing_root_AGENTS_missing_four_adoption_guardrail_snippets",
    })
    manifest["active_baseline"]["execution_plan_path"] = PLAN_PATH
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v46"],
        "current_version": "v47",
        "reason": "v47 records the observation-runner one-request budget gate and offline verification; v46 remains immutable.",
    })

    for path, (artifact_id, kind, lifecycle) in CURRENT_ARTIFACTS.items():
        _register(manifest["artifacts"], path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v47 P1 observation-runner request-budget gate and offline/preflight evidence; no FTA Gold, database, or production behavior change.",
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
        if not V47_PATH.exists() or V47_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v47 differs from generated content\n")
    else:
        V47_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "baseline_version": "v47",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "live_model_request_performed": False,
        "observation_runner_max_model_calls": 1,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
