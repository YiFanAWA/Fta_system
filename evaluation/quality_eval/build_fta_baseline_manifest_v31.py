#!/usr/bin/env python3
"""Build active FTA research manifest v31 for the offline event-scope prompt v6."""

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

V30_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v30.json"
V31_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v31.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v30.json": (
        "fta-baseline-manifest-v30-snapshot", "historical_baseline_manifest", "historical",
        "Immutable snapshot of the one-shot v5 run and its blocked assessment; v31 prepares prompt v6 offline only.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v30.py": (
        "fta-baseline-manifest-v30-builder", "reproducibility_tool", "historical",
        "Reproduces the immutable v30 snapshot from v29 and the saved v5 run bundle.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v30.py": (
        "fta-baseline-manifest-v30-tests", "manifest_regression_tests", "historical",
        "Protects the immutable v30 record of the blocked v5 run.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v5.py": (
        "event-scope-model-runner-v5", "evaluation_tool", "historical_used_once",
        "One-shot runner used for the blocked v5 observation; it is not wired to the v6 prompt.",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v5.py": (
        "event-scope-model-runner-v5-tests", "evaluation_tool_tests", "historical",
        "Regression tests for the v5 one-shot runner; no v6 live request is enabled.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5", "evaluation_prompt", "historical_used_once",
        "Prompt used by the single blocked v5 run; retained as immutable execution history.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v5.py": (
        "event-scope-causal-path-scope-prompt-v5-tests", "evaluation_prompt_tests", "historical",
        "Offline regressions for the v5 prompt retained for historical reproducibility.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v31.py": (
        "fta-baseline-manifest-v31-builder", "reproducibility_tool", "current",
        "Builds v31 from frozen v30, records prompt v6 as offline/unrun, and hashes registered artifacts.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v31.py": (
        "fta-baseline-manifest-v31-tests", "manifest_regression_tests", "current",
        "Protects the v5 latest-run status, v6 unrun status, immutable v30, and false readiness.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v6.py": (
        "event-scope-single-hierarchy-prompt-v6", "evaluation_prompt", "prepared_offline_not_run",
        "Offline prompt candidate for one coherent hierarchy, nested alternative paths, and complete gate fields; not yet wired to or sent by a model runner.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v6.py": (
        "event-scope-single-hierarchy-prompt-v6-tests", "evaluation_prompt_tests", "current",
        "Checks direction, one-hierarchy rules, explicit null fields, label-free projection, and a nested structural fixture.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v31-default", "validation_tool", "current",
        "Validates registered paths and SHA-256 fingerprints; defaults to active manifest v31.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v31-default", "validation_tool_tests", "current",
        "Covers artifact hash validation and the active v31 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v31-doc-index", "current_truth_index", "current",
        "Points to active v31 and distinguishes the prepared offline v6 prompt from the latest actual blocked v5 run.",
    ),
    "docs/current-state-audit.md": (
        "fta-v31-current-state-audit", "current_state_document", "current",
        "Records the offline v6 prompt candidate, v5 as latest actual run, and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v31-acceptance-record", "acceptance_document", "current",
        "Records offline v6 prompt/contract checks without claiming a new model run or accepted tree.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v31-candidate-generation-policy", "current_fta_policy_document", "current",
        "Records v6 as an offline prompt candidate only; the latest actual model run remains blocked v5.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v31-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks v6 offline prompt preparation and preserves the explicit authorization boundary for any model call.",
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
    v30 = json.loads(V30_PATH.read_text(encoding="utf-8"))
    if v30.get("manifest_id") != "candidate_fta_research_baseline_v30":
        raise ValueError("v31 must extend the frozen v30 manifest")
    if v30.get("event_scope_prompt_v5", {}).get("status") != "completed_seen_development_only_blocked":
        raise ValueError("v31 must retain v5 as the latest actual blocked model run")
    if v30.get("active_baseline", {}).get("fta_ready") is not False or v30.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v31 must preserve false FTA/production readiness")

    prompt_path = ROOT / "evaluation/quality_eval/event_scope_tree_prompt_v6.py"
    test_path = ROOT / "evaluation/quality_eval/test_event_scope_tree_prompt_v6.py"
    prompt_source = prompt_path.read_text(encoding="utf-8")
    if 'PROMPT_VERSION = "event-scope-text-only-tree-v6-single-hierarchy"' not in prompt_source:
        raise ValueError("v31 prompt source does not declare the expected v6 version")
    if not test_path.is_file():
        raise ValueError("v31 requires offline prompt regression tests")

    manifest = deepcopy(v30)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v31"
    manifest["baseline_version"] = "v31"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v30",
        "path": V30_PATH.relative_to(ROOT).as_posix(),
        "reason": "v31 records an offline-only v6 prompt candidate and its local contract tests; v5 remains the latest actual model run and remains blocked.",
    }
    manifest["scope"]["includes"].append(
        "offline preparation and regression of event-scope prompt v6 for a single hierarchy, nested alternative paths, and complete gate fields"
    )
    manifest["scope"]["excludes"].extend([
        "any v6 model request, output-quality claim, accuracy/calibration/generalization claim, or accepted FTA Preview",
        "Gold promotion, production/API/database writes, or readiness promotion from the offline prompt candidate",
    ])
    manifest["active_baseline"].update({
        "event_scope_latest_actual_model_run": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json",
        "event_scope_latest_actual_model_run_status": "blocked_seen_development_only",
        "event_scope_prepared_prompt": "event-scope-text-only-tree-v6-single-hierarchy",
        "event_scope_prepared_prompt_path": "evaluation/quality_eval/event_scope_tree_prompt_v6.py",
        "event_scope_prepared_prompt_status": "prepared_offline_not_run",
        "event_scope_model_live_request_count_v6": 0,
        "event_scope_model_v6_assessment_status": "not_run",
        "event_scope_model_v6_accuracy_claim_allowed": False,
        "event_scope_v6_runner_wired": False,
        "event_scope_v6_requires_fresh_explicit_authorization": True,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v6"] = {
        "status": "prepared_offline_not_run",
        "prompt_version": "event-scope-text-only-tree-v6-single-hierarchy",
        "prompt_path": prompt_path.relative_to(ROOT).as_posix(),
        "test_path": test_path.relative_to(ROOT).as_posix(),
        "runner_path": None,
        "runner_wired": False,
        "live_request_count": 0,
        "latest_actual_model_run_path": "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json",
        "latest_actual_model_run_status": "blocked_seen_development_only",
        "intended_offline_checks": [
            "maintain A and B as conditions associated with T without inferring an AND gate",
            "use a single coherent hierarchy with one scope per output node and nested intermediate paths only when evidence supports them",
            "avoid singleton gate scopes without inventing sibling nodes",
            "require all gate fields and explicit JSON null for unknown_reason on known gates",
            "keep model input label-free and validate the candidate structure without auto-repair",
        ],
        "model_output_observed": False,
        "semantic_correctness": "not_assessed",
        "accuracy_or_calibration_claim_allowed": False,
        "formal_gold": False,
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "requires_fresh_explicit_authorization_for_any_model_request": True,
        "reason": "The v5 run exposed three structural issues. v6 is an offline prompt candidate with local regressions only; it is not wired to a runner and has not been sent to a model. The only actual run remains the blocked v5 seen-Development observation.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v30"],
        "current_version": "v31",
        "reason": "v31 adds only an offline/unrun v6 prompt candidate and tests; it preserves the blocked v5 actual run and does not promote Gold, FTA readiness, or production readiness.",
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
        current = V31_PATH.read_text(encoding="utf-8") if V31_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v31 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v31",
            "v5_latest_actual_run_status": payload["event_scope_prompt_v5"]["status"],
            "v6_prompt_status": payload["event_scope_prompt_v6"]["status"],
            "v6_live_request_count": payload["event_scope_prompt_v6"]["live_request_count"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V31_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V31_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
