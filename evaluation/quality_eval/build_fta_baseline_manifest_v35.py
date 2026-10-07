#!/usr/bin/env python3
"""Build active FTA baseline v35 for the offline-only event-scope prompt candidate."""

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

V34_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v34.json"
V35_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v35.json"
PROMPT_PATH = "evaluation/quality_eval/event_scope_tree_prompt_v7.py"
PROMPT_TEST_PATH = "evaluation/quality_eval/test_event_scope_tree_prompt_v7.py"
CASES_PATH = "evaluation/quality_eval/datasets/fta_event_scope_prompt_v7_regression_cases_v1.json"
PACKET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v34.json": (
        "fta-baseline-manifest-v34-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v34 snapshot before the offline prompt v7 candidate was added.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v34.py": (
        "fta-baseline-manifest-v34-builder", "reproducibility_tool", "historical",
        "Reproduces v34; superseded as active manifest builder by v35.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v34.py": (
        "fta-baseline-manifest-v34-tests", "manifest_regression_tests", "historical",
        "Protects the v34 snapshot and its preserved v6 semantic blockers.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v6.py": (
        "event-scope-tree-prompt-v6", "evaluation_prompt", "historical_observed",
        "One-shot seen-Development prompt used for the preserved v6 run; not modified or rerun.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v6.py": (
        "event-scope-tree-prompt-v6-tests", "evaluation_prompt_tests", "historical",
        "Regression tests for the v6 prompt snapshot.",
    ),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py": (
        "event-scope-model-runner-v6", "one-shot_model_runner", "historical_used_authorization",
        "Single-request v6 runner; its authorization was consumed and any future request requires fresh user authorization.",
    ),
    PROMPT_PATH: (
        "event-scope-tree-prompt-v7", "evaluation_prompt_candidate", "current_offline_only",
        "Offline prompt candidate requiring known-gate evidence to bind child logic and the same output; not wired to an online runner.",
    ),
    PROMPT_TEST_PATH: (
        "event-scope-tree-prompt-v7-tests", "evaluation_prompt_tests", "current",
        "Offline tests for positive OR/AND evidence, co-occurrence and out-of-scope connector negatives, and label-free input.",
    ),
    CASES_PATH: (
        "event-scope-tree-prompt-v7-regression-cases", "development_policy_regressions", "current_non_gold",
        "Four policy regressions including the v6 Figure 7 S1 miss; not expert Gold or a model accuracy set.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v35.py": (
        "fta-baseline-manifest-v35-builder", "reproducibility_tool", "current",
        "Builds v35 from v34 and records the offline prompt candidate without promoting semantic or production readiness.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v35.py": (
        "fta-baseline-manifest-v35-tests", "manifest_regression_tests", "current",
        "Protects prompt v7's offline-only, non-Gold status and preserves the v6 semantic miss and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v35-default", "validation_tool", "current",
        "Validates the active v35 artifact snapshot by repo-contained paths and SHA-256.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v35-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v35 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v35-doc-index", "current_truth_index", "current",
        "Points to v35 and explicitly labels prompt v7 as offline-only and not semantically accepted.",
    ),
    "docs/current-state-audit.md": (
        "fta-v35-current-state-audit", "current_state_document", "current",
        "Records the offline prompt candidate, regression scope, and remaining live/semantic verification boundary.",
    ),
    "docs/acceptance.md": (
        "fta-v35-acceptance-record", "acceptance_document", "current",
        "Records the prompt v7 offline test and manifest integrity commands/results.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v35-candidate-generation-policy", "current_fta_policy_document", "current",
        "Links the v7 offline evidence-binding candidate while preserving Preview-only and readiness boundaries.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v35-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks offline prompt v7 as a candidate, with a fresh-authorized model run and independent validation still outstanding.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register(artifacts: list[dict[str, Any]], relative_path: str, entry: dict[str, Any]) -> None:
    existing = next((item for item in artifacts if item.get("path") == relative_path), None)
    registered = {**(existing or {}), **entry, "path": relative_path}
    for index, item in enumerate(artifacts):
        if item.get("path") == relative_path:
            artifacts[index] = registered
            return
    artifacts.append(registered)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v34 = json.loads(V34_PATH.read_text(encoding="utf-8"))
    active_v34 = v34.get("active_baseline", {})
    if v34.get("manifest_id") != "candidate_fta_research_baseline_v34":
        raise ValueError("v35 must extend immutable v34")
    if active_v34.get("fta_ready") is not False or active_v34.get("production_ready") is not False:
        raise ValueError("v35 must preserve false FTA/production readiness")
    if active_v34.get("event_scope_model_v6_semantic_acceptance") is not False:
        raise ValueError("v35 must preserve the unresolved v6 semantic result")

    cases = json.loads((ROOT / CASES_PATH).read_text(encoding="utf-8"))
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    case_ids = {case.get("case_id") for case in cases.get("cases", [])}
    required_case_ids = {
        "FIG7-S1-OR-EVIDENCE-BINDING",
        "EXPLICIT-JOINT-CONDITION-AND",
        "COOCCURRENCE-IS-NOT-AND",
        "UNSCOPED-ALTERNATIVE-IS-NOT-OR",
    }
    if cases.get("dataset_status") != "offline_policy_regressions_not_gold":
        raise ValueError("v7 regression fixture must remain non-Gold")
    if cases.get("human_expert_gold") is not False or cases.get("accuracy_claim_allowed") is not False:
        raise ValueError("v7 regression fixture must not support Gold or accuracy claims")
    if not required_case_ids.issubset(case_ids):
        raise ValueError("v7 regression fixture is incomplete")
    if cases.get("guardrails", {}).get("model_request_performed") is not False:
        raise ValueError("v35 must not claim or perform a model request")

    observed = next(
        gate for gate in run["model_output"]["parsed_json"]["gates"] if gate.get("scope_id") == "S1"
    )
    if observed.get("gate") != "unknown" or observed.get("logic_evidence") is not None:
        raise ValueError("v35 must preserve the original v6 S1 finding")
    source = next(
        segment["text"]
        for segment in packet["model_input"]["source_segments"]
        if segment.get("segment_id") == observed["scope_evidence"]["segment_id"]
    )
    if observed["scope_evidence"]["quote"] not in source or "or" not in observed["scope_evidence"]["quote"].lower():
        raise ValueError("v35 expects the source-pinned v6 alternative-path evidence")

    manifest = deepcopy(v34)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v35"
    manifest["baseline_version"] = "v35"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v34",
        "path": V34_PATH.relative_to(ROOT).as_posix(),
        "reason": "v35 adds an offline-only prompt candidate that explicitly binds known gate labels to the child relation and the same output, plus non-Gold regressions; it does not run a model or alter Gold/production behavior.",
    }
    manifest["scope"]["includes"].append(
        "offline event-scope prompt v7 candidate and four non-Gold regressions for child-logic/output evidence binding, explicit joint conditions, co-occurrence, and out-of-scope connectors"
    )
    manifest["scope"]["excludes"].extend([
        "any online inference or semantic-quality claim for prompt v7",
        "automatic semantic parsing/repair, Gold promotion, database/production changes, or readiness promotion from prompt v7 offline tests",
    ])
    manifest["active_baseline"].update({
        "event_scope_prompt_v7_candidate_status": "offline_candidate_not_run",
        "event_scope_prompt_v7_candidate_path": PROMPT_PATH,
        "event_scope_prompt_v7_candidate_test_path": PROMPT_TEST_PATH,
        "event_scope_prompt_v7_regression_cases_path": CASES_PATH,
        "event_scope_prompt_v7_regression_case_status": "offline_policy_regressions_not_gold",
        "event_scope_prompt_v7_live_request_performed": False,
        "event_scope_prompt_v7_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v7_candidate"] = {
        "status": "offline_candidate_not_run",
        "prompt_version": "event-scope-text-only-tree-v7-bound-logic-evidence",
        "prompt_path": PROMPT_PATH,
        "test_path": PROMPT_TEST_PATH,
        "regression_cases_path": CASES_PATH,
        "runner_wired": False,
        "live_request_performed": False,
        "source_packet_path": "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json",
        "v6_run_preserved_unmodified": True,
        "human_expert_gold": False,
        "semantic_acceptance": False,
        "accuracy_or_calibration_claim_allowed": False,
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "reason": "Offline tests cover evidence-binding instructions and label-free input only. The prompt has not been run against a model; any future live call needs fresh explicit user authorization.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v34"],
        "current_version": "v35",
        "reason": "v35 tracks the v7 offline candidate without changing the v6 one-shot observation or promoting semantic/FTA readiness.",
    })

    repo_root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": note,
            "sha256": _sha256(target),
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
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
        current = V35_PATH.read_text(encoding="utf-8") if V35_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v35 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v35",
            "prompt_v7_status": payload["active_baseline"]["event_scope_prompt_v7_candidate_status"],
            "v6_finding": payload["active_baseline"]["event_scope_v6_semantic_regression_status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V35_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V35_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
