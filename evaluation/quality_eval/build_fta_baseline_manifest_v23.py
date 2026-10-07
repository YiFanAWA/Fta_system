#!/usr/bin/env python3
"""Build the v23 FTA baseline for a prepared but not-yet-run controlled request."""

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

V22_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v22.json"
V23_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v23.json"
RUNNER_V3 = "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py"
RUNNER_TEST_V3 = "evaluation/quality_eval/test_run_fta_event_scope_model_v3.py"

CURRENT_ARTIFACTS = {
    RUNNER_V3: (
        "nasa-battery-fig7-controlled-runner-v3",
        "evaluation_tool",
        "current_prepared_not_run",
        "Keeps v2 inputs, prompt, model, JSON mode, and token budget; explicitly disables thinking and records response metadata without persisting reasoning text.",
    ),
    RUNNER_TEST_V3: (
        "nasa-battery-fig7-controlled-runner-v3-tests",
        "evaluation_tool_tests",
        "current",
        "Offline tests for request control, redacted diagnostics, empty/truncated output, malformed shapes, credential confirmation, and repository-bounded artifact paths.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v23.py": (
        "fta-baseline-manifest-v23-builder",
        "reproducibility_tool",
        "current",
        "Builds v23 from the frozen v22 run baseline and records v3 as prepared but unexecuted.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v23.py": (
        "fta-baseline-manifest-v23-tests",
        "manifest_regression_tests",
        "current",
        "Checks that v23 preserves the v22 model-run history, records no third request, and keeps readiness false.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v23-default",
        "validation_tool",
        "current",
        "Validates registered repository paths and hashes; defaults to active manifest v23.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v23-default",
        "validation_tool_tests",
        "current",
        "Covers hash validation and the active v23 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v23-doc-index",
        "current_truth_index",
        "current",
        "Points to the v23 research manifest, v22 last completed model run, and the credential-gated v3 runner.",
    ),
    "docs/current-state-audit.md": (
        "fta-v23-current-state-audit",
        "current_state_document",
        "current",
        "Records the prepared v3 runner, offline gates, credential rotation blocker, and no additional model call.",
    ),
    "docs/acceptance.md": (
        "fta-v23-acceptance-record",
        "acceptance_document",
        "current",
        "Records offline v3 runner verification and that online comparison is not run pending credential rotation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v23-candidate-generation-policy",
        "current_fta_policy_document",
        "current",
        "Documents v23 active research state and the v3 pending one-shot boundary.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v23-validation-plan-policy",
        "current_validation_plan_document",
        "current",
        "Records the v3 controlled comparison design, offline tests, and credential rotation stop gate.",
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
    v22 = json.loads(V22_PATH.read_text(encoding="utf-8"))
    if v22.get("manifest_id") != "candidate_fta_research_baseline_v22":
        raise ValueError("v23 must extend the frozen v22 manifest")
    if v22.get("event_scope_model_inference", {}).get("request_count") != 2:
        raise ValueError("v22 must remain the last completed two-request model snapshot")

    manifest = deepcopy(v22)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v23"
    manifest["baseline_version"] = "v23"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "an offline-verified v3 one-shot runner prepared for a single controlled comparison; no additional model request is included"
    )
    manifest["scope"]["excludes"].extend([
        "any v3 model output, tree/gate prediction, Gold comparison, or accuracy claim because the request has not run",
        "any use of the previously exposed provider credential; rotation and explicit confirmation are required before the one-shot request",
    ])
    manifest["active_baseline"].update({
        "event_scope_model_run": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json",
        "event_scope_model_run_assessment": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.json",
        "event_scope_model_runner": RUNNER_V3,
        "event_scope_model_runner_status": "prepared_not_run_credential_rotation_required",
    })
    inference = manifest["event_scope_model_inference"]
    inference["status"] = "last_completed_v1_v2_unusable_v3_prepared_not_run"
    inference["latest_completed_run_path"] = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json"
    inference["next_controlled_attempt"] = {
        "status": "prepared_blocked_credential_rotation",
        "request_count": 0,
        "retry_count": 0,
        "runner_path": RUNNER_V3,
        "authorized_single_request": True,
        "credential_rotation_confirmation_required": True,
        "only_generation_parameter_changed_from_v2": "thinking_mode_disabled",
        "held_constant": [
            "validated model_input projection",
            "prompt content and prompt version",
            "model alias and provider host",
            "temperature",
            "max_tokens=8192",
            "response_format=json_object",
            "SDK retries disabled",
        ],
        "response_diagnostics": [
            "finish_reason",
            "visible_content_character_count",
            "reasoning_content_present_and_character_count_without_persisting_reasoning_text",
            "provider_reasoning_token_count_when_available",
        ],
        "blocking_reason": "old provider credential was exposed in local diagnostic output and must be revoked/rotated before use",
    }
    manifest["independent_final_validation"].update({
        "reason": "NASA Figure 7 remains a seen Development sample. The two completed requests produced no usable JSON; a v3 runner is prepared but has not executed pending provider credential rotation. No accuracy, calibration, or generalization conclusion is available.",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v22"],
        "current_version": "v23",
        "reason": "v23 records the user-authorized but not-yet-executed controlled v3 request plan and its credential rotation gate; v22 remains the last completed inference snapshot. No new model request, Gold comparison, Final creation, production write, or readiness change is included.",
    })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    repo_root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })
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
        current = V23_PATH.read_text(encoding="utf-8") if V23_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v23 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v23",
            "completed_model_request_count": payload["event_scope_model_inference"]["request_count"],
            "next_request_status": payload["event_scope_model_inference"]["next_controlled_attempt"]["status"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V23_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V23_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
