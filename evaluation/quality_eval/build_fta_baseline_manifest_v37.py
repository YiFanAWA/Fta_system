#!/usr/bin/env python3
"""Build active FTA baseline v37 for a label-separated, offline-preflighted v8 smoke set."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V36_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v36.json"
V37_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v37.json"
INPUTS_PATH = "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_inputs_v1.json"
REFERENCE_PATH = "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json"
RUNNER_PATH = "evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py"
RUNNER_TEST_PATH = "evaluation/quality_eval/test_run_fta_event_scope_semantic_smoke_v1.py"
PROMPT_PATH = "evaluation/quality_eval/event_scope_tree_prompt_v8.py"
PROMPT_TEST_PATH = "evaluation/quality_eval/test_event_scope_tree_prompt_v8.py"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v36.json": (
        "fta-baseline-manifest-v36-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v36 baseline snapshot before the semantic smoke runner and input/reference pair were added.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v36.py": (
        "fta-baseline-manifest-v36-builder", "reproducibility_tool", "historical",
        "Reproduces v36; superseded as active manifest builder by v37.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v36.py": (
        "fta-baseline-manifest-v36-tests", "manifest_regression_tests", "historical",
        "Protects the v36 offline prompt-only status and false readiness guards.",
    ),
    INPUTS_PATH: (
        "fta-semantic-smoke-inputs-v1", "constructed_behavioral_smoke_inputs", "current_non_gold",
        "Five synthetic semantic fixtures; only case.model_input is submitted to the prompt. Not source-corpus examples or accuracy data.",
    ),
    REFERENCE_PATH: (
        "fta-semantic-smoke-reference-v1", "separate_policy_reference_expectations", "current_non_gold_separate",
        "Expected gate dispositions for the synthetic fixtures; authored policy references, not expert-reviewed Gold and never loaded by the runner.",
    ),
    RUNNER_PATH: (
        "fta-semantic-smoke-runner-v1", "one_shot_evaluation_runner", "current_preflight_only",
        "Prompt-v8 runner for one explicitly authorized request per case; no retries/repairs; preserves raw visible response and does not load reference labels.",
    ),
    RUNNER_TEST_PATH: (
        "fta-semantic-smoke-runner-v1-tests", "one_shot_runner_tests", "current",
        "Offline tests for input/reference separation, authorization, no retry/repair, raw response retention, and duplicate-call blocking.",
    ),
    PROMPT_PATH: (
        "event-scope-tree-prompt-v8", "evaluation_prompt_candidate", "current_offline_only",
        "Semantic-not-keyword gate candidate; untested against a live model.",
    ),
    PROMPT_TEST_PATH: (
        "event-scope-tree-prompt-v8-tests", "evaluation_prompt_tests", "current",
        "Offline prompt regressions for implicit semantic gates and ambiguity boundaries.",
    ),
    "evaluation/quality_eval/datasets/fta_event_scope_prompt_v8_regression_cases_v1.json": (
        "event-scope-tree-prompt-v8-regressions", "development_policy_regressions", "current_non_gold",
        "Six offline policy cases, including the prior Figure 7 observation; not model outputs or accuracy data.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v37.py": (
        "fta-baseline-manifest-v37-builder", "reproducibility_tool", "current",
        "Builds active v37 from v36 while preserving false readiness and model-call authorization boundaries.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v37.py": (
        "fta-baseline-manifest-v37-tests", "manifest_regression_tests", "current",
        "Checks five input/reference cases, non-Gold status, runner separation, and unchanged readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v37-default", "validation_tool", "current",
        "Validates active v37 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v37-default", "validation_tool_tests", "current",
        "Covers manifest integrity and the active v37 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v37-doc-index", "current_truth_index", "current",
        "Points to v37 and indexes the separate synthetic smoke inputs/reference and one-shot runner.",
    ),
    "docs/current-state-audit.md": (
        "fta-v37-current-state-audit", "current_state_document", "current",
        "Records smoke preparation as offline-only; no live model result or readiness promotion.",
    ),
    "docs/acceptance.md": (
        "fta-v37-acceptance-record", "acceptance_document", "current",
        "Records the synthetic smoke runner tests, preflight boundary, and commands.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v37-candidate-generation-policy", "current_fta_policy_document", "current",
        "Keeps semantic interpretation evidence-bound and distinguishes synthetic smoke from real-source validation.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v37-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks the prepared runner, explicit per-request authorization, and outstanding source-grounded validation.",
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
    v36 = json.loads(V36_PATH.read_text(encoding="utf-8"))
    active_v36 = v36.get("active_baseline", {})
    if v36.get("manifest_id") != "candidate_fta_research_baseline_v36":
        raise ValueError("v37 must extend immutable v36")
    if active_v36.get("fta_ready") is not False or active_v36.get("production_ready") is not False:
        raise ValueError("v37 must preserve false FTA/production readiness")
    if active_v36.get("event_scope_model_v6_semantic_acceptance") is not False:
        raise ValueError("v37 must preserve the unresolved v6 semantic result")

    inputs = json.loads((ROOT / INPUTS_PATH).read_text(encoding="utf-8"))
    reference = json.loads((ROOT / REFERENCE_PATH).read_text(encoding="utf-8"))
    if inputs.get("dataset_status") != "constructed_behavioral_smoke_inputs_not_source_corpus":
        raise ValueError("smoke inputs must remain explicitly synthetic")
    if inputs.get("human_expert_gold") is not False or inputs.get("accuracy_claim_allowed") is not False:
        raise ValueError("smoke inputs must not claim expert Gold or accuracy")
    if inputs.get("guardrails", {}).get("reference_labels_included") is not False:
        raise ValueError("reference labels must remain outside model inputs")
    if inputs.get("guardrails", {}).get("model_request_performed") is not False:
        raise ValueError("v37 preparation must not perform a model request")
    if reference.get("reference_status") != "authored_policy_reference_not_expert_reviewed":
        raise ValueError("separate expectations must not be promoted to expert Gold")
    if reference.get("human_expert_gold") is not False or reference.get("accuracy_claim_allowed") is not False:
        raise ValueError("reference expectations cannot support accuracy claims")

    input_by_id = {case.get("case_id"): case for case in inputs.get("cases", [])}
    reference_by_id = {case.get("case_id"): case for case in reference.get("cases", [])}
    expected_ids = {"SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"}
    if set(input_by_id) != expected_ids or set(reference_by_id) != expected_ids:
        raise ValueError("v37 requires exactly five aligned smoke inputs and separate references")
    if any(case.get("expected_candidate_gate") not in {"AND", "OR", "unknown"} for case in reference_by_id.values()):
        raise ValueError("unsupported expected reference gate")
    for case_id in expected_ids:
        model_input = input_by_id[case_id].get("model_input")
        if not isinstance(model_input, dict):
            raise ValueError(f"missing model_input for {case_id}")
        if any(key in model_input for key in ("expected_gate", "expected_candidate_gate", "reference_labels", "gold")):
            raise ValueError(f"reference leakage in model input: {case_id}")
        source = "\n".join(segment.get("text", "") for segment in model_input.get("source_segments", []))
        top_event = model_input.get("top_event", {}).get("text", "")
        if top_event not in source:
            raise ValueError(f"top event not present in input source for {case_id}")
        quote = reference_by_id[case_id].get("decisive_source_quote", "")
        if not quote or quote not in source:
            raise ValueError(f"reference evidence quote not pinned to input for {case_id}")
    for case_id in ("SMOKE-001", "SMOKE-002"):
        source = "\n".join(segment["text"] for segment in input_by_id[case_id]["model_input"]["source_segments"])
        if re.search(r"\b(?:and|or)\b", source, flags=re.IGNORECASE):
            raise ValueError(f"implicit gate case unexpectedly contains a literal operator: {case_id}")

    manifest = deepcopy(v36)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v37"
    manifest["baseline_version"] = "v37"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v36",
        "path": V36_PATH.relative_to(ROOT).as_posix(),
        "reason": "v37 adds five constructed semantic smoke cases with separate non-Gold reference expectations and a one-case, one-request prompt-v8 runner; no live model request is performed.",
    }
    manifest["scope"]["includes"].append(
        "five constructed prompt-v8 semantic behavior smoke cases with strict input/reference separation and a no-retry, explicit-authorization, one-case runner preflight"
    )
    manifest["scope"]["excludes"].extend([
        "source-corpus or real-manual generalization claims from constructed smoke cases",
        "expert Gold, accuracy/calibration claims, automatic response repair/retry, model calls without fresh explicit authorization, and production/readiness promotion from smoke preparation",
    ])
    manifest["active_baseline"].update({
        "event_scope_semantic_smoke_status": "preflight_ready_not_run",
        "event_scope_semantic_smoke_input_path": INPUTS_PATH,
        "event_scope_semantic_smoke_reference_path": REFERENCE_PATH,
        "event_scope_semantic_smoke_runner_path": RUNNER_PATH,
        "event_scope_semantic_smoke_case_count": len(inputs["cases"]),
        "event_scope_semantic_smoke_input_reference_separated": True,
        "event_scope_semantic_smoke_live_request_performed": False,
        "event_scope_prompt_v8_semantic_acceptance": False,
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_semantic_smoke_v1"] = {
        "status": "preflight_ready_not_run",
        "input_path": INPUTS_PATH,
        "reference_path": REFERENCE_PATH,
        "runner_path": RUNNER_PATH,
        "runner_test_path": RUNNER_TEST_PATH,
        "case_count": len(inputs["cases"]),
        "case_ids": sorted(expected_ids),
        "dataset_kind": "constructed_behavioral_smoke_not_source_corpus",
        "reference_status": reference["reference_status"],
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "runner_reads_reference": False,
        "one_case_per_request": True,
        "requests_per_authorization": 1,
        "automatic_retries": False,
        "automatic_repairs": False,
        "raw_visible_response_preserved": True,
        "live_request_performed": False,
        "source_corpus_validation": False,
        "fta_ready": False,
        "production_ready": False,
        "next_gate": "obtain fresh explicit authorization for one selected case, run once, then compare the saved output offline against the separate reference without auto-repair",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v36"],
        "current_version": "v37",
        "reason": "v37 records the synthetic, label-separated smoke and guarded prompt-v8 runner preparation; no model or readiness result is added.",
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
        current = V37_PATH.read_text(encoding="utf-8") if V37_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v37 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v37",
            "semantic_smoke_status": payload["event_scope_semantic_smoke_v1"]["status"],
            "case_count": payload["event_scope_semantic_smoke_v1"]["case_count"],
            "live_request_performed": payload["event_scope_semantic_smoke_v1"]["live_request_performed"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V37_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V37_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
