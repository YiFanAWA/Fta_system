#!/usr/bin/env python3
"""Build the v24 FTA baseline after the single controlled Figure 7 run."""

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

V23_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v23.json"
V24_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v24.json"
RUN_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json"
ATTEMPT_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.attempt.json"
ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v3_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py": (
        "nasa-battery-fig7-controlled-runner-v3",
        "evaluation_tool",
        "completed_single_request_structural_quote_check_no_gold_comparison",
        "Keeps v2 inputs and generation settings except explicitly disabling thinking; records response metadata without persisting reasoning text.",
    ),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v3.py": (
        "nasa-battery-fig7-controlled-runner-v3-tests",
        "evaluation_tool_tests",
        "current",
        "Offline tests for request control, redacted diagnostics, empty/truncated output, malformed shapes, credential confirmation, and repository-bounded artifact paths.",
    ),
    RUN_PATH: (
        "nasa-battery-fig7-model-run-v3",
        "model_run",
        "completed_development_run",
        "One bounded thinking-disabled request on a seen Dev packet; usable JSON, no Gold comparison or accuracy claim.",
    ),
    ATTEMPT_PATH: (
        "nasa-battery-fig7-model-run-v3-attempt",
        "model_run_attempt_receipt",
        "completed",
        "Records exactly one request and zero retries; contains no credential or persisted reasoning text.",
    ),
    ASSESSMENT_PATH: (
        "nasa-battery-fig7-model-run-v3-assessment",
        "model_run_assessment",
        "completed_structural_evidence_check",
        "Checks JSON structure and source-quote matching only; Gold and semantic correctness were not assessed.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v24.py": (
        "fta-baseline-manifest-v24-builder",
        "reproducibility_tool",
        "current",
        "Builds v24 from v23 and the recorded v3 run, assessment, and attempt receipt.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v24.py": (
        "fta-baseline-manifest-v24-tests",
        "manifest_regression_tests",
        "current",
        "Verifies the third request facts, no Gold comparison, and unchanged readiness gates.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v24-default",
        "validation_tool",
        "current",
        "Validates registered repository paths and hashes; defaults to active manifest v24.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v24-default",
        "validation_tool_tests",
        "current",
        "Covers hash validation and the active v24 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v24-doc-index",
        "current_truth_index",
        "current",
        "Points to the active v24 research manifest and bounded v3 structural/evidence result.",
    ),
    "docs/current-state-audit.md": (
        "fta-v24-current-state-audit",
        "current_state_document",
        "current",
        "Records the completed one-shot v3 call, output checks, and unchanged Gold/readiness state.",
    ),
    "docs/acceptance.md": (
        "fta-v24-acceptance-record",
        "acceptance_document",
        "current",
        "Records offline gates and the completed one-shot online response/quote validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v24-candidate-generation-policy",
        "current_fta_policy_document",
        "current",
        "Documents v24 active state and limits of the seen Figure 7 Dev run.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v24-validation-plan-policy",
        "current_validation_plan_document",
        "current",
        "Records the completed controlled contrast without promoting semantic or readiness claims.",
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


def _load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    v23 = _load_json("evaluation/quality_eval/fta_baseline_manifest_v23.json")
    if v23.get("manifest_id") != "candidate_fta_research_baseline_v23":
        raise ValueError("v24 must extend the frozen v23 manifest")
    if v23.get("event_scope_model_inference", {}).get("request_count") != 2:
        raise ValueError("v23 must remain the frozen two-request predecessor")

    assessment = _load_json(ASSESSMENT_PATH)
    observation = assessment.get("request_observation", {})
    output_assessment = assessment.get("output_assessment", {})
    if observation.get("request_count") != 1 or observation.get("retry_count") != 0:
        raise ValueError("v3 must be exactly one request with no retries")
    if observation.get("thinking_mode") != {"type": "disabled"}:
        raise ValueError("v3 must be the explicitly thinking-disabled contrast")
    if observation.get("finish_reason") != "stop" or not output_assessment.get("strict_json_parsed"):
        raise ValueError("v3 output must be complete and parseable before it can become the active run")
    if output_assessment.get("gold_comparison") != "not_performed":
        raise ValueError("v3 must not compare against the isolated reference Gold")

    manifest = deepcopy(v23)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v24"
    manifest["baseline_version"] = "v24"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one completed, bounded, thinking-disabled Figure 7 Dev request with structural and source-quote checks only"
    )
    obsolete_exclusions = {
        "any v3 model output, tree/gate prediction, Gold comparison, or accuracy claim because the request has not run",
        "any use of the previously exposed provider credential; rotation and explicit confirmation are required before the one-shot request",
    }
    manifest["scope"]["excludes"] = [
        item for item in manifest["scope"]["excludes"] if item not in obsolete_exclusions
    ]
    manifest["scope"]["excludes"].extend([
        "semantic correctness, gate-label accuracy, calibration, or generalization claims from this single seen Development sample",
        "Gold comparison, production API/database writes, or any readiness promotion",
    ])

    manifest["active_baseline"].update({
        "event_scope_model_run": RUN_PATH,
        "event_scope_model_run_assessment": ASSESSMENT_PATH,
        "event_scope_model_runner": "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py",
        "event_scope_model_runner_status": "completed_single_request_structural_quote_check_no_gold_comparison",
    })
    inference = manifest["event_scope_model_inference"]
    inference.update({
        "status": "v3_completed_usable_json_structural_quotes_checked_no_gold_comparison",
        "request_count": 3,
        "retry_count": 0,
        "latest_prompt_version": observation["prompt_version"],
        "latest_prompt_sha256": observation["prompt_sha256"],
        "latest_max_tokens": observation["max_tokens"],
        "latest_temperature": observation["temperature"],
        "latest_completion_tokens": observation["usage"]["completion_tokens"],
        "usable_json": output_assessment["strict_json_parsed"],
        "run_path": RUN_PATH,
        "attempt_receipt_path": ATTEMPT_PATH,
        "assessment_path": ASSESSMENT_PATH,
        "latest_completed_run_path": RUN_PATH,
        "root_cause": "undetermined; one thinking-disabled controlled contrast returned a usable response",
        "scope_note": "The single seen-Development v3 response is parseable and its quotes match the input; no reference Gold comparison, semantic correctness, accuracy, calibration, or generalization claim is made.",
        "controlled_attempt_v3": {
            "status": "completed",
            "request_count": observation["request_count"],
            "retry_count": observation["retry_count"],
            "thinking_mode": observation["thinking_mode"],
            "finish_reason": observation["finish_reason"],
            "completion_tokens": observation["usage"]["completion_tokens"],
            "visible_content_character_count": observation["visible_content_character_count"],
            "reasoning_content_present": observation["reasoning_content_present"],
            "reasoning_text_persisted": observation["reasoning_text_persisted"],
            "reasoning_tokens": observation["reasoning_tokens"],
            "strict_json_parsed": output_assessment["strict_json_parsed"],
            "node_count": output_assessment["node_count"],
            "gate_scope_count": output_assessment["gate_scope_count"],
            "quote_checks": output_assessment["quote_checks"],
            "invalid_quotes": output_assessment["invalid_quotes"],
            "structural_errors": output_assessment["structural_errors"],
            "gold_comparison": output_assessment["gold_comparison"],
        },
        "next_controlled_attempt": {
            "status": "not_planned",
            "request_count": 0,
            "retry_count": 0,
            "reason": "The single user-authorized controlled contrast is complete; no additional request is included in this baseline.",
        },
    })
    inference["attempts"].append({
        "run_path": RUN_PATH,
        "attempt_receipt_path": ATTEMPT_PATH,
        "assessment_path": ASSESSMENT_PATH,
        "max_tokens": observation["max_tokens"],
        "response_format": observation["response_format"]["type"],
        "thinking_mode": observation["thinking_mode"]["type"],
        "finish_reason": observation["finish_reason"],
        "completion_tokens": observation["usage"]["completion_tokens"],
        "raw_output_character_count": observation["visible_content_character_count"],
        "usable_json": output_assessment["strict_json_parsed"],
        "quote_checks": output_assessment["quote_checks"],
        "invalid_quotes": output_assessment["invalid_quotes"],
        "gold_comparison": output_assessment["gold_comparison"],
    })
    manifest["independent_final_validation"].update({
        "reason": "The Figure 7 sample is already seen Development data. The v3 response is structurally parseable and all checked quotes match the input, but reference Gold was deliberately not compared; no semantic accuracy or generalization conclusion is available."
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v23"],
        "current_version": "v24",
        "reason": "v24 registers the one authorized thinking-disabled v3 request and its structural/source-quote assessment. It does not compare Gold, create an independent Final, write production data, or promote readiness.",
    })

    for artifact in manifest["artifacts"]:
        if artifact.get("path") in {
            "evaluation/quality_eval/build_fta_baseline_manifest_v23.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v23.py",
        }:
            artifact["lifecycle"] = "historical"
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
        current = V24_PATH.read_text(encoding="utf-8") if V24_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v24 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v24",
            "completed_model_request_count": payload["event_scope_model_inference"]["request_count"],
            "latest_finish_reason": payload["event_scope_model_inference"]["controlled_attempt_v3"]["finish_reason"],
            "usable_json": payload["event_scope_model_inference"]["usable_json"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V24_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V24_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
