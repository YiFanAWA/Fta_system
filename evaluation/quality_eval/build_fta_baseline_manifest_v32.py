#!/usr/bin/env python3
"""Build active FTA baseline v32 with the offline-wired, not-yet-run v6 runner."""

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

V31_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v31.json"
V32_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v32.json"
RUNNER_PATH = "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py"
RUNNER_TEST_PATH = "evaluation/quality_eval/test_run_fta_event_scope_model_v6.py"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v31.json": (
        "fta-baseline-manifest-v31-snapshot", "historical_baseline_manifest", "historical",
        "Frozen manifest state before the v6 one-shot runner was wired; its latest actual run remains v5.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v31.py": (
        "fta-baseline-manifest-v31-builder", "reproducibility_tool", "historical",
        "Reproduces the v31 offline-prompt snapshot; superseded by the v32 active baseline builder.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v31.py": (
        "fta-baseline-manifest-v31-tests", "manifest_regression_tests", "historical",
        "Protects the historical v31 state in which the v6 prompt was not yet wired to a runner.",
    ),
    RUNNER_PATH: (
        "event-scope-model-runner-v6", "evaluation_tool", "current_not_run",
        "One explicitly authorized request maximum, zero retries, v6 prompt, label-free input, exclusive artifacts; preserves invalid raw output and marks the assessment blocked without repair or retry.",
    ),
    RUNNER_TEST_PATH: (
        "event-scope-model-runner-v6-tests", "evaluation_tool_tests", "current",
        "Offline tests for preflight, explicit authorization, one-shot settings, no reasoning persistence, duplicate-run rejection, and raw-output preservation on blockers.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v32.py": (
        "fta-baseline-manifest-v32-builder", "reproducibility_tool", "current",
        "Builds v32 from v31, records v6 runner wiring without claiming a model run, and hashes active artifacts.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v32.py": (
        "fta-baseline-manifest-v32-tests", "manifest_regression_tests", "current",
        "Protects v31 history, v6 runner wiring, zero model calls, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v32-default", "validation_tool", "current",
        "Validates registered paths and SHA-256 fingerprints; defaults to active manifest v32.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v32-default", "validation_tool_tests", "current",
        "Covers artifact hash validation and the active v32 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v32-doc-index", "current_truth_index", "current",
        "Points to active v32 and distinguishes the wired-but-not-run v6 runner from the latest actual v5 model run.",
    ),
    "docs/current-state-audit.md": (
        "fta-v32-current-state-audit", "current_state_document", "current",
        "Records v6 runner wiring and offline verification without claiming a live inference or accepted tree.",
    ),
    "docs/acceptance.md": (
        "fta-v32-acceptance-record", "acceptance_document", "current",
        "Records the v6 runner offline tests, preflight and manifest validation; model authorization remains separate.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v32-candidate-generation-policy", "current_fta_policy_document", "current",
        "Records the wired v6 one-shot runner as not yet executed; latest actual run is blocked v5.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v32-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks v6 runner wiring and preserves the fresh explicit authorization boundary for any live request.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v31 = json.loads(V31_PATH.read_text(encoding="utf-8"))
    if v31.get("manifest_id") != "candidate_fta_research_baseline_v31":
        raise ValueError("v32 must extend the v31 manifest")
    if v31.get("active_baseline", {}).get("fta_ready") is not False or v31.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v32 must preserve false FTA/production readiness")
    if v31.get("event_scope_prompt_v6", {}).get("status") != "prepared_offline_not_run":
        raise ValueError("v32 expects the v31 offline-only v6 prompt state")

    prompt_path = ROOT / "evaluation/quality_eval/event_scope_tree_prompt_v6.py"
    runner_path = ROOT / RUNNER_PATH
    test_path = ROOT / RUNNER_TEST_PATH
    if not prompt_path.is_file() or not runner_path.is_file() or not test_path.is_file():
        raise ValueError("v32 requires the v6 prompt, one-shot runner, and runner regression tests")

    manifest = deepcopy(v31)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v32"
    manifest["baseline_version"] = "v32"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v31",
        "path": V31_PATH.relative_to(ROOT).as_posix(),
        "reason": "v32 wires the v6 prompt to a tested one-shot evaluation runner; no live request has been made and v5 remains the latest actual model run.",
    }
    manifest["scope"]["includes"].append(
        "offline wiring and mock-tested one-shot runner for event-scope prompt v6; original model responses are retained and contract blockers are not repaired or retried"
    )
    manifest["scope"]["excludes"].extend([
        "any live v6 model request until fresh explicit user authorization",
        "semantic accuracy, gate accuracy, calibration, generalization, Gold promotion, production/API/database writes, or readiness promotion from runner wiring and mock tests",
    ])
    manifest["active_baseline"].update({
        "event_scope_model_runner": "run_fta_event_scope_model_v6",
        "event_scope_model_runner_path": RUNNER_PATH,
        "event_scope_model_runner_status": "wired_offline_verified_waiting_fresh_explicit_authorization",
        "event_scope_prepared_prompt_status": "runner_wired_not_run",
        "event_scope_v6_runner_wired": True,
        "event_scope_v6_runner_offline_verified": True,
        "event_scope_model_live_request_count_v6": 0,
        "event_scope_model_v6_assessment_status": "not_run",
        "event_scope_model_v6_accuracy_claim_allowed": False,
        "event_scope_v6_requires_fresh_explicit_authorization": True,
        "event_scope_latest_actual_model_run": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json",
        "event_scope_latest_actual_model_run_status": "blocked_seen_development_only",
        "fta_ready": False,
        "production_ready": False,
    })
    prompt_record = manifest["event_scope_prompt_v6"]
    prompt_record.update({
        "status": "runner_wired_not_run",
        "runner_path": RUNNER_PATH,
        "runner_wired": True,
        "runner_offline_verified": True,
        "runner_test_path": RUNNER_TEST_PATH,
        "live_request_count": 0,
        "latest_actual_model_run_path": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json",
        "latest_actual_model_run_status": "blocked_seen_development_only",
        "model_output_observed": False,
        "raw_model_output_preserved_on_block": True,
        "automatic_repair_performed": False,
        "automatic_retry_performed": False,
        "semantic_correctness": "not_assessed",
        "accuracy_or_calibration_claim_allowed": False,
        "requires_fresh_explicit_authorization_for_any_model_request": True,
        "reason": "The v6 one-shot runner and offline tests are wired. Preflight and mocked requests do not contact the provider. No v6 model request has been authorized or performed; v5 remains the latest actual run and remains blocked.",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v31"],
        "current_version": "v32",
        "reason": "v32 adds a locally verified v6 one-shot runner while preserving v5 as the latest actual model run, zero v6 requests, and false FTA/production readiness.",
    })

    _upsert(manifest["artifacts"], {
        "artifact_id": "fta-baseline-manifest-v31-snapshot",
        "kind": "historical_baseline_manifest",
        "lifecycle": "historical",
        "path": V31_PATH.relative_to(ROOT).as_posix(),
        "note": "Frozen manifest state before v6 runner wiring; latest actual model run recorded there is v5.",
    })
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    repo_root = ROOT.resolve(strict=True)
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
        current = V32_PATH.read_text(encoding="utf-8") if V32_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v32 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v32",
            "v5_latest_actual_run_status": payload["event_scope_prompt_v5"]["status"],
            "v6_runner_wired": payload["event_scope_prompt_v6"]["runner_wired"],
            "v6_live_request_count": payload["event_scope_prompt_v6"]["live_request_count"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V32_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V32_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
