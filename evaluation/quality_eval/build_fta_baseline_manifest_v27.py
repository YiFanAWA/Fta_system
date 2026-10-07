#!/usr/bin/env python3
"""Build active FTA research manifest v27 for the isolated event-scope v4 runner."""

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

V26_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v26.json"
V27_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v27.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/event_scope_tree_prompt_v4.py": (
        "event-scope-evidence-located-hierarchy-prompt-v4", "evaluation_prompt", "current_prepared_not_run",
        "Adds explicit segment-located node/scope evidence and separates scope evidence from direct gate-logic evidence; not submitted to a model.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py": (
        "event-scope-model-runner-v4", "evaluation_tool", "current_prepared_not_run",
        "Isolated one-shot evaluation runner for prompt v4; requires per-call explicit authorization, fixes thinking disabled, zero retries, validates hierarchy/evidence locations, and never writes Gold or production data.",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v4.py": (
        "event-scope-model-runner-v4-tests", "evaluation_tool_tests", "current",
        "Mock-only tests for preflight, strict output/evidence location, fail-closed hierarchy, unknown gate policy, no persisted reasoning, and one-shot API configuration.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v27.py": (
        "fta-baseline-manifest-v27-builder", "reproducibility_tool", "current",
        "Builds v27 from frozen v26, records the prepared v4 request boundary, and rehashes registered artifacts without making an API call.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v27.py": (
        "fta-baseline-manifest-v27-tests", "manifest_regression_tests", "current",
        "Protects the not-run/authorization-required state, false readiness flags, registered files, and frozen v26 immutability.",
    ),
    "evaluation/quality_eval/fta_baseline_manifest_v26.json": (
        "fta-baseline-manifest-v26-snapshot", "historical_baseline_manifest", "historical",
        "Immutable prior active snapshot; v27 extends it and does not rewrite its contents or hashes.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v27-default", "validation_tool", "current",
        "Validates registered repository paths and hashes; defaults to active manifest v27.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v27-default", "validation_tool_tests", "current",
        "Covers hash validation and the active v27 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v27-doc-index", "current_truth_index", "current",
        "Points to v27 and the prepared, not-run, authorization-gated event-scope v4 evaluation.",
    ),
    "docs/current-state-audit.md": (
        "fta-v27-current-state-audit", "current_state_document", "current",
        "Records the isolated v4 runner readiness and makes clear that no additional live model request has been sent.",
    ),
    "docs/acceptance.md": (
        "fta-v27-acceptance-record", "acceptance_document", "current",
        "Records v4 runner mock tests and offline preflight only; no live call or semantic result claimed.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v27-candidate-generation-policy", "current_fta_policy_document", "current",
        "Points at the active v27 baseline; production candidate-tree behavior remains unchanged.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v27-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks the isolated v4 runner as prepared but pending explicit live-request authorization.",
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
    v26 = json.loads(V26_PATH.read_text(encoding="utf-8"))
    if v26.get("manifest_id") != "candidate_fta_research_baseline_v26":
        raise ValueError("v27 must extend the frozen v26 manifest")
    if v26.get("active_baseline", {}).get("fta_ready") is not False or v26.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v27 must preserve false FTA/production readiness")

    manifest = deepcopy(v26)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v27"
    manifest["baseline_version"] = "v27"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "isolated event-scope prompt v4 and one-shot evaluation runner with explicit per-call authorization, thinking disabled, zero retries, strict output/evidence-location checks, and no Gold exposure"
    )
    manifest["scope"]["excludes"].extend([
        "any live v4 model request before explicit per-call user authorization",
        "semantic correctness or gate accuracy inferred from prompt, mock tests, or offline preflight",
        "formal Gold promotion, production/API/database writes, or readiness promotion from the prepared v4 runner",
    ])
    manifest["active_baseline"].update({
        "event_scope_prepared_prompt": "event-scope-text-only-tree-v4-located-evidence",
        "event_scope_prepared_prompt_status": "not_run",
        "event_scope_model_runner": "run_fta_event_scope_model_v4",
        "event_scope_model_runner_status": "prepared_explicit_authorization_required",
        "event_scope_model_live_request_count_v4": 0,
        "event_scope_model_live_request_retries_v4": 0,
        "event_scope_model_thinking_mode_v4": "disabled",
        "event_scope_hierarchy_owner": "gate_scopes",
        "event_scope_parent_id_policy": "forbidden_in_v4_output_validate_projection_only_for_legacy",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_model_v4"] = {
        "status": "prepared_not_run_authorization_required",
        "packet_id": "NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001",
        "exposure_status": "seen_development_only",
        "prompt_version": "event-scope-text-only-tree-v4-located-evidence",
        "runner_path": "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py",
        "provider_host": "api.deepseek.com",
        "requested_model": "deepseek-flash",
        "authorized_request_count": 0,
        "configured_max_retries": 0,
        "thinking_mode": "disabled",
        "response_format": "json_object",
        "model_input_includes_gold": False,
        "gold_comparison": "not_performed",
        "semantic_correctness": "not_assessed",
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "reason": "The evaluation runner and mock-only tests are prepared. A new external provider request requires explicit user authorization for that single call; no call has been sent.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v26"],
        "current_version": "v27",
        "reason": "v27 registers an isolated evidence-located prompt v4 and explicit-authorization one-shot runner; request status is not_run, and semantic/FTA/production readiness do not change.",
    })

    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id, "kind": kind, "lifecycle": lifecycle, "path": relative_path, "note": note,
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
        current = V27_PATH.read_text(encoding="utf-8") if V27_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v27 differs from generated content\n")
        print(json.dumps({
            "status": "current", "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v27",
            "prepared_prompt_status": payload["active_baseline"]["event_scope_prepared_prompt_status"],
            "live_request_count": payload["event_scope_model_v4"]["authorized_request_count"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V27_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V27_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
