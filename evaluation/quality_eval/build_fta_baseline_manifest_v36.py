#!/usr/bin/env python3
"""Build active FTA baseline v36 for semantic, evidence-bound gate interpretation."""

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

V35_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v35.json"
V36_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v36.json"
PROMPT_PATH = "evaluation/quality_eval/event_scope_tree_prompt_v8.py"
PROMPT_TEST_PATH = "evaluation/quality_eval/test_event_scope_tree_prompt_v8.py"
CASES_PATH = "evaluation/quality_eval/datasets/fta_event_scope_prompt_v8_regression_cases_v1.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v35.json": (
        "fta-baseline-manifest-v35-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v35 baseline document recording the prompt v7 offline candidate.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v35.py": (
        "fta-baseline-manifest-v35-builder", "reproducibility_tool", "historical",
        "Reproduces v35; superseded as active manifest builder by v36.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v35.py": (
        "fta-baseline-manifest-v35-tests", "manifest_regression_tests", "historical",
        "Protects v35's prompt v7 offline-only status and false readiness guards.",
    ),
    "evaluation/quality_eval/event_scope_tree_prompt_v7.py": (
        "event-scope-tree-prompt-v7", "evaluation_prompt_candidate", "historical_offline_candidate",
        "Previous offline-only prompt candidate; no online model result is attributed to it.",
    ),
    "evaluation/quality_eval/test_event_scope_tree_prompt_v7.py": (
        "event-scope-tree-prompt-v7-tests", "evaluation_prompt_tests", "historical",
        "Historical offline tests for prompt v7.",
    ),
    "evaluation/quality_eval/datasets/fta_event_scope_prompt_v7_regression_cases_v1.json": (
        "event-scope-tree-prompt-v7-regressions", "development_policy_regressions", "historical_non_gold",
        "Historical v7 non-Gold policy cases; retained for audit and not an accuracy set.",
    ),
    PROMPT_PATH: (
        "event-scope-tree-prompt-v8", "evaluation_prompt_candidate", "current_offline_only",
        "Allows semantically expressed AND/OR without literal operators, while requiring direct evidence for child logic and the same output; not runner-wired or model-tested.",
    ),
    PROMPT_TEST_PATH: (
        "event-scope-tree-prompt-v8-tests", "evaluation_prompt_tests", "current",
        "Offline tests cover implicit semantic OR/AND, ambiguous listings/co-occurrence, out-of-scope lexical OR, label-free input, and preserved tree contract.",
    ),
    CASES_PATH: (
        "event-scope-tree-prompt-v8-regressions", "development_policy_regressions", "current_non_gold",
        "Six offline non-Gold cases including implicit OR/AND, counterexamples, and the source-pinned Figure 7 S1 observation; not a model accuracy set.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v36.py": (
        "fta-baseline-manifest-v36-builder", "reproducibility_tool", "current",
        "Builds the v36 active baseline from immutable v35 while preserving false readiness and no-live-call boundaries.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v36.py": (
        "fta-baseline-manifest-v36-tests", "manifest_regression_tests", "current",
        "Checks prompt v8 candidate status, non-Gold fixture guardrails, prior finding preservation, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v36-default", "validation_tool", "current",
        "Validates the active v36 artifact snapshot by repo-contained paths and SHA-256.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v36-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v36 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v36-doc-index", "current_truth_index", "current",
        "Points to v36 and distinguishes semantic interpretation policy from actual model validation.",
    ),
    "docs/current-state-audit.md": (
        "fta-v36-current-state-audit", "current_state_document", "current",
        "Records prompt v8 as offline-only and retains the unresolved v6 semantic result and readiness boundaries.",
    ),
    "docs/acceptance.md": (
        "fta-v36-acceptance-record", "acceptance_document", "current",
        "Records prompt v8 offline regression and manifest integrity commands/results.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v36-candidate-generation-policy", "current_fta_policy_document", "current",
        "States that semantic gate interpretation need not contain literal AND/OR tokens, but remains evidence-bound and review-only.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v36-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks prompt v8 as offline candidate; model validation and independent Gold remain outstanding.",
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
    v35 = json.loads(V35_PATH.read_text(encoding="utf-8"))
    active_v35 = v35.get("active_baseline", {})
    if v35.get("manifest_id") != "candidate_fta_research_baseline_v35":
        raise ValueError("v36 must extend immutable v35")
    if active_v35.get("fta_ready") is not False or active_v35.get("production_ready") is not False:
        raise ValueError("v36 must preserve false FTA/production readiness")
    if active_v35.get("event_scope_model_v6_semantic_acceptance") is not False:
        raise ValueError("v36 must preserve the unresolved v6 semantic result")

    cases = json.loads((ROOT / CASES_PATH).read_text(encoding="utf-8"))
    required_case_ids = {
        "SEMANTIC-OR-NO-OPERATOR",
        "SEMANTIC-AND-NO-OPERATOR",
        "LEXICAL-OR-OUTSIDE-SCOPE",
        "CAUSE-LIST-DOES-NOT-PROVE-OR",
        "COOCCURRENCE-DOES-NOT-PROVE-AND",
        "FIG7-S1-EXPLICIT-OR-BINDING",
    }
    case_ids = {case.get("case_id") for case in cases.get("cases", [])}
    if cases.get("dataset_status") != "offline_semantic_policy_regressions_not_gold":
        raise ValueError("v8 regression fixture must remain non-Gold")
    if cases.get("human_expert_gold") is not False or cases.get("accuracy_claim_allowed") is not False:
        raise ValueError("v8 regression fixture must not support Gold or accuracy claims")
    if not required_case_ids.issubset(case_ids):
        raise ValueError("v8 regression fixture is incomplete")
    if cases.get("guardrails", {}).get("model_request_performed") is not False:
        raise ValueError("v36 must not claim or perform a model request")

    manifest = deepcopy(v35)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v36"
    manifest["baseline_version"] = "v36"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v35",
        "path": V35_PATH.relative_to(ROOT).as_posix(),
        "reason": "v36 makes AND/OR interpretation semantic rather than keyword-dependent while retaining direct evidence requirements for the child relation and shared output; changes remain offline-only.",
    }
    manifest["scope"]["includes"].append(
        "offline event-scope prompt v8 candidate and six non-Gold regressions for implicit semantic OR/AND, ambiguous cause lists/co-occurrence, out-of-scope lexical OR, and the preserved Figure 7 S1 case"
    )
    manifest["scope"]["excludes"].extend([
        "online inference or semantic-quality claims for prompt v8",
        "keyword/phrase enumeration as a substitute for semantic judgment, automatic semantic repair, Gold promotion, database/production changes, or readiness promotion from offline prompt v8 tests",
    ])
    manifest["active_baseline"].update({
        "event_scope_prompt_v8_candidate_status": "offline_candidate_not_run",
        "event_scope_prompt_v8_candidate_path": PROMPT_PATH,
        "event_scope_prompt_v8_candidate_test_path": PROMPT_TEST_PATH,
        "event_scope_prompt_v8_regression_cases_path": CASES_PATH,
        "event_scope_prompt_v8_regression_case_status": "offline_semantic_policy_regressions_not_gold",
        "event_scope_prompt_v8_live_request_performed": False,
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v8_candidate"] = {
        "status": "offline_candidate_not_run",
        "prompt_version": "event-scope-text-only-tree-v8-semantic-gate-evidence",
        "prompt_path": PROMPT_PATH,
        "test_path": PROMPT_TEST_PATH,
        "regression_cases_path": CASES_PATH,
        "runner_wired": False,
        "live_request_performed": False,
        "human_expert_gold": False,
        "semantic_acceptance": False,
        "accuracy_or_calibration_claim_allowed": False,
        "production_or_database_write": False,
        "fta_ready": False,
        "production_ready": False,
        "policy": {
            "literal_and_or_tokens_required": False,
            "semantic_interpretation_allowed": True,
            "or_requires_alternative_child_paths_to_the_same_output": True,
            "and_requires_jointly_necessary_child_conditions_for_the_same_output": True,
            "logic_evidence_must_directly_support_children_relation_and_same_output": True,
            "mere_list_or_cooccurrence_is_sufficient": False,
            "ambiguous_or_noncontinuous_evidence_fails_closed_to_unknown": True,
        },
        "regression_case_count": len(cases["cases"]),
        "reason": "Offline tests verify prompt text, label-free input, and policy fixtures only. The prompt has not been run against a model; any future live call needs fresh explicit user authorization.",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v35"],
        "current_version": "v36",
        "reason": "v36 records semantic-not-keyword prompt guidance and non-Gold regressions without changing prior model observations or promoting semantic/FTA readiness.",
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
        current = V36_PATH.read_text(encoding="utf-8") if V36_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v36 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v36",
            "prompt_v8_status": payload["active_baseline"]["event_scope_prompt_v8_candidate_status"],
            "v6_finding": payload["active_baseline"]["event_scope_v6_semantic_regression_status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V36_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V36_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
