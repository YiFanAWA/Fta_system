#!/usr/bin/env python3
"""Freeze the current progress and next-stage plan without changing FTA behavior."""

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


V45_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v45.json"
V46_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v46.json"
EXPECTED_V45_SHA256 = "152736cb9acd69f2ddde7db530324c630800cf7b952ac1119d86180e4114d27d"
PLAN_PATH = "docs/fta-validation-reliability-plan-v1.md"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v45.json": (
        "fta-baseline-manifest-v45-snapshot", "historical_baseline_manifest", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v45.py": (
        "fta-baseline-manifest-v45-builder", "reproducibility_tool", "historical",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v45.py": (
        "fta-baseline-manifest-v45-tests", "manifest_regression_tests", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v46.py": (
        "fta-baseline-manifest-v46-builder", "reproducibility_tool", "current",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v46-default", "validation_tool", "current",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v46-default", "validation_tool_tests", "current",
    ),
    "docs/README.md": ("fta-v46-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": (
        "fta-v46-current-state-audit", "current_state_document", "current",
    ),
    "docs/acceptance.md": ("fta-v46-acceptance-record", "acceptance_document", "current"),
    PLAN_PATH: ("fta-v46-next-stage-plan", "active_validation_plan", "current"),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v46-candidate-generation-policy", "current_fta_policy_document", "current",
    ),
}


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V45_PATH) != EXPECTED_V45_SHA256:
        raise ValueError("v45 snapshot hash changed; refusing to derive v46")
    source = json.loads(V45_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v45":
        raise ValueError("v46 must derive from the preserved v45 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v46 must preserve false FTA and production readiness")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v46"
    manifest["baseline_version"] = "v46"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V45_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V45_SHA256,
        "reason": "Documents current maturity and the ordered validation plan; no new model run, Gold write, or runtime behavior change.",
    }
    manifest["scope"]["includes"].append(
        "current progress and P1-P7 validation roadmap in the existing reliability plan owner"
    )
    manifest["next_stage_plan_v1"] = {
        "path": PLAN_PATH,
        "status": "documented_not_executed",
        "current_stage": "P1_observation_live_boundary_verification",
        "milestones": {
            "P0_status_and_offline_contracts": "complete_within_documented_scope",
            "P1_observation_live_boundary": "pending_single_request_budget_gate_and_explicit_authorization",
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
        "observation_runner_preflight_max_model_calls": 3,
        "planned_observation_runner_max_model_calls": 1,
        "observation_single_request_budget_gate_verified": False,
        "governance_debt": "existing_root_AGENTS_missing_four_adoption_guardrail_snippets",
    }
    manifest["active_baseline"]["execution_plan_path"] = PLAN_PATH
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v45"],
        "current_version": "v46",
        "reason": "v46 pins the current progress and next-stage roadmap; v45 remains immutable.",
    })

    for path, (artifact_id, kind, lifecycle) in CURRENT_ARTIFACTS.items():
        _register(manifest["artifacts"], path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v46 documentation and reproducibility bookkeeping; no FTA semantics changed.",
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
        if not V46_PATH.exists() or V46_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v46 differs from generated content\n")
    else:
        V46_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "baseline_version": "v46",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "live_model_request_performed": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
