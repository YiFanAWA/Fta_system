#!/usr/bin/env python3
"""Build active FTA research manifest v29 for the offline v5 prompt candidate."""

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

V28_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v28.json"
V29_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v28.json": (
        "fta-baseline-manifest-v28-snapshot", "historical_baseline_manifest", "historical",
        "Immutable prior active snapshot; v29 preserves its file bytes and records an offline-only v5 prompt candidate.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v29.py": (
        "fta-baseline-manifest-v29-builder", "reproducibility_tool", "current",
        "Builds v29 from frozen v28 and records v5 as prepared offline, not model-run; hashes registered artifacts.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v29.py": (
        "fta-baseline-manifest-v29-tests", "manifest_regression_tests", "current",
        "Protects the v28 snapshot, no-request boundary, v4 latest-run status, and false readiness.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5", "evaluation_prompt", "prepared_not_run",
        "Offline prompt candidate clarifies conditional cause scope and alternative-path grouping; no live model result or accuracy claim.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5-tests", "evaluation_prompt_tests", "current",
        "Checks conditional orientation, preservation of alternative paths, and exclusion of reference labels from model input.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v29-default", "validation_tool", "current",
        "Validates registered repository paths and SHA-256 fingerprints; defaults to active manifest v29.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v29-default", "validation_tool_tests", "current",
        "Covers artifact hash validation and the active v29 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v29-doc-index", "current_truth_index", "current",
        "Points to active manifest v29 and states v5 is offline-only while v4 remains the latest actual model run.",
    ),
    "docs/current-state-audit.md": (
        "fta-v29-current-state-audit", "current_state_document", "current",
        "Records the offline v5 prompt candidate, passing local prompt tests, unchanged v4 observation, and false readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v29-acceptance-record", "acceptance_document", "current",
        "Records the offline prompt regression evidence and explicitly excludes a live v5 inference claim.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v29-candidate-generation-policy", "current_fta_policy_document", "current",
        "Describes v5 causal-path prompt refinement as prepared, unrun, and non-production.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v29-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks the v5 offline regression and requires fresh explicit authorization for any model call.",
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
    v28 = json.loads(V28_PATH.read_text(encoding="utf-8"))
    if v28.get("manifest_id") != "candidate_fta_research_baseline_v28":
        raise ValueError("v29 must extend the frozen v28 manifest")
    active = v28.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v29 must preserve false FTA/production readiness")
    run = v28.get("event_scope_model_v4", {})
    if run.get("status") != "completed_seen_development_only_blocked":
        raise ValueError("v29 requires v4 to remain the recorded latest actual model run")

    manifest = deepcopy(v28)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v29"
    manifest["baseline_version"] = "v29"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "offline-only event-scope prompt v5 candidate clarifying conditional causal orientation and complete alternative-path scopes, with local prompt regression tests"
    )
    manifest["scope"]["excludes"].extend([
        "any v5 live model request, retry, semantic result, accuracy, or improvement claim",
        "formal Gold promotion, production/API/database writes, or readiness promotion from the offline v5 candidate",
    ])
    manifest["active_baseline"].update({
        "event_scope_latest_actual_model_run": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json",
        "event_scope_latest_actual_model_run_status": "blocked_seen_development_only",
        "event_scope_prepared_prompt": "event-scope-text-only-tree-v5-causal-path-scope",
        "event_scope_prepared_prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v5.py",
        "event_scope_prepared_prompt_status": "offline_candidate_ready_not_run",
        "event_scope_prepared_prompt_live_request_count": 0,
        "event_scope_prepared_prompt_requires_new_explicit_authorization": True,
        "event_scope_prepared_prompt_accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v5"] = {
        "status": "prepared_offline_not_run",
        "prompt_version": "event-scope-text-only-tree-v5-causal-path-scope",
        "prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v5.py",
        "test_path": "evaluation/quality_eval/test_event_scope_tree_prompt_v5.py",
        "tested_behavior": [
            "A may lead to T if B: A and B are conditions for T; B is not a child event that causes A",
            "A and B, or C and D, lead to T: preserve complete alternative-path scopes instead of cross-nesting them",
            "keep model input as the validated projection without reference diagram gates or review labels",
        ],
        "offline_test_status": "passed",
        "live_request_count": 0,
        "latest_actual_model_run": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json",
        "v4_latest_actual_result": "blocked_by_single_child_S2; 9_of_9_literal_evidence_locations; all_three_gates_unknown",
        "model_accuracy_or_improvement_claim_allowed": False,
        "gold_or_production_write": False,
        "fta_ready": False,
        "production_ready": False,
        "authorization_note": "A future live request requires new explicit per-call user authorization; v29 itself does not authorize one.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v28"],
        "current_version": "v29",
        "reason": "v29 records an offline-only v5 causal-path prompt candidate and its local regressions; v4 remains the latest actual model run and its blocked result is unchanged.",
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
        current = V29_PATH.read_text(encoding="utf-8") if V29_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v29 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v29",
            "v5_prompt_status": payload["event_scope_prompt_v5"]["status"],
            "v5_live_request_count": payload["event_scope_prompt_v5"]["live_request_count"],
            "latest_actual_model_run": payload["event_scope_model_v4"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V29_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V29_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
