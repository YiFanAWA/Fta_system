#!/usr/bin/env python3
"""Build the v21 FTA baseline recording one incomplete NASA Dev inference."""

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

from evaluation.quality_eval.build_fta_baseline_manifest_v20 import build_manifest as build_v20


V20_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v20.json"
V21_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v21.json"

RUN = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.json"
ATTEMPT = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.attempt.json"
ASSESSMENT_JSON = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.json"
ASSESSMENT_MD = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.md"
RUNNER = "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v1.py"
RUNNER_TEST = "evaluation/quality_eval/test_run_fta_event_scope_model_v1.py"
VALIDATOR = "evaluation/quality_eval/validate_fta_baseline_manifest.py"
VALIDATOR_TEST = "evaluation/quality_eval/test_validate_fta_baseline_manifest.py"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v20.json": (
        "fta-baseline-manifest-v20-snapshot",
        "baseline_manifest_snapshot",
        "historical",
        "Frozen v20 state before the single NASA Figure 7 event-scope inference attempt.",
    ),
    RUN: (
        "nasa-battery-fig7-deepseek-one-shot-run-v1",
        "event_scope_model_inference_run",
        "current",
        "One authorized DeepSeek request with retries disabled; API returned finish_reason=length and empty final content, so no usable tree or gate prediction exists.",
    ),
    ATTEMPT: (
        "nasa-battery-fig7-one-shot-attempt-receipt-v1",
        "one_shot_inference_receipt",
        "current",
        "Durable guard/receipt records the single attempt and prevents accidental repeated calls through this runner.",
    ),
    ASSESSMENT_JSON: (
        "nasa-battery-fig7-one-shot-assessment-json-v1",
        "model_run_assessment",
        "current",
        "Offline assessment: no valid output, no Gold comparison, and no accuracy or calibration metric.",
    ),
    ASSESSMENT_MD: (
        "nasa-battery-fig7-one-shot-assessment-md-v1",
        "model_run_assessment_document",
        "current",
        "Human-readable account of the single incomplete response and claim boundaries.",
    ),
    RUNNER: (
        "fta-event-scope-one-shot-runner-v1",
        "evaluation_tool",
        "current",
        "Validates and projects only model_input; DeepSeek alias is pinned, SDK retries are zero, and an attempt receipt prevents repeated calls.",
    ),
    RUNNER_TEST: (
        "fta-event-scope-one-shot-runner-tests-v1",
        "evaluation_tool_tests",
        "current",
        "Offline tests for Gold/source-envelope isolation, model projection, and one-request configuration.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v21.py": (
        "fta-baseline-manifest-v21-builder",
        "reproducibility_tool",
        "current",
        "Builds the current manifest from v20 and records the incomplete one-shot Dev run without promoting readiness.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v21.py": (
        "fta-baseline-manifest-v21-tests",
        "manifest_regression_tests",
        "current",
        "Checks exact one-call accounting, unusable output, no Gold promotion, unchanged Final count, and false readiness.",
    ),
    VALIDATOR: (
        "fta-baseline-manifest-validator-v21-default",
        "validation_tool",
        "current",
        "Validates repository paths and hashes; defaults to active v21.",
    ),
    VALIDATOR_TEST: (
        "fta-baseline-manifest-validator-tests-v21-default",
        "validation_tool_tests",
        "current",
        "Covers manifest hash validation and active v21 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v21-doc-index",
        "current_truth_index",
        "current",
        "Points to active FTA baseline v21 and the incomplete one-shot NASA Figure 7 model run.",
    ),
    "docs/current-state-audit.md": (
        "fta-v21-current-state-audit",
        "current_state_document",
        "current",
        "Records the actual one-shot output truncation and unchanged readiness boundary.",
    ),
    "docs/acceptance.md": (
        "fta-v21-acceptance-record",
        "acceptance_document",
        "current",
        "Records isolation tests, preflight, one request, no retries, and the absence of a score.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v21-candidate-generation-policy",
        "candidate_fta_policy_document",
        "current",
        "Documents the one-shot technical attempt as incomplete, non-Gold, and non-accuracy evidence.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v21-validation-plan-policy",
        "validation_plan_document",
        "current",
        "Updates the active baseline and records the incomplete single-sample inference status.",
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
    previous = json.loads(V20_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v20":
        raise ValueError("v21 must extend the frozen v20 manifest snapshot")
    run = json.loads((ROOT / RUN).read_text(encoding="utf-8"))
    attempt = json.loads((ROOT / ATTEMPT).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / ASSESSMENT_JSON).read_text(encoding="utf-8"))
    if run.get("status") != "succeeded" or run.get("request", {}).get("finish_reason") != "length":
        raise ValueError("the registered provider response must be the observed truncated response")
    if run.get("request", {}).get("request_count") != 1 or run.get("request", {}).get("retry_count") != 0:
        raise ValueError("the authorized run must record exactly one request and no retries")
    if run.get("model_output", {}).get("raw_text") != "" or run.get("model_output", {}).get("parsed_json") is not None:
        raise ValueError("the run must not claim a usable model output")
    if attempt.get("request_count") != 1 or attempt.get("status") != "succeeded":
        raise ValueError("one-shot attempt receipt does not reconcile with the run")
    if assessment.get("assessment_status") != "completed_request_but_no_usable_output":
        raise ValueError("assessment must not report a semantic score")

    manifest = deepcopy(build_v20(captured_at=captured_at))
    manifest["manifest_id"] = "candidate_fta_research_baseline_v21"
    manifest["baseline_version"] = "v21"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one authorized DeepSeek event-scope Development request on the NASA battery Figure 7 source-text projection; output was truncated and no semantic comparison was possible"
    )
    manifest["scope"]["excludes"].extend([
        "gate prediction accuracy, Gold agreement, calibration, or generalization inferred from the incomplete single response",
        "any second model request or retry under the one-request authorization",
    ])
    manifest["active_baseline"]["event_scope_model_run"] = RUN
    manifest["active_baseline"]["event_scope_model_run_assessment"] = ASSESSMENT_JSON
    manifest["active_baseline"]["event_scope_model_prompt"] = "event-scope-text-only-tree-v1"
    manifest["event_scope_packet_contract"].update({
        "model_inference_run": True,
        "model_inference_request_count": 1,
        "model_inference_retry_count": 0,
        "model_inference_output_status": "incomplete_empty_content_finish_length",
        "model_inference_comparison_status": "not_performed",
        "human_expert_reviewed": False,
    })
    manifest["event_scope_dev_case"].update({
        "model_inference_run": True,
        "model_inference_request_count": 1,
        "model_inference_retry_count": 0,
        "model_output_usable": False,
        "gate_comparison_status": "not_performed",
        "accuracy_or_calibration_claim_allowed": False,
        "model_run_path": RUN,
        "model_run_assessment_path": ASSESSMENT_JSON,
        "attempt_receipt_path": ATTEMPT,
    })
    manifest["event_scope_model_inference"] = {
        "status": "request_returned_output_incomplete",
        "packet_id": run["case"]["packet_id"],
        "source_cluster_id": run["case"]["source_cluster_id"],
        "model": run["request"]["returned_model"],
        "provider_host": run["request"]["provider_host"],
        "request_count": 1,
        "retry_count": 0,
        "finish_reason": run["request"]["finish_reason"],
        "prompt_version": run["request"]["prompt_version"],
        "prompt_sha256": run["request"]["prompt_sha256"],
        "max_tokens": run["request"]["max_tokens"],
        "temperature": run["request"]["temperature"],
        "completion_tokens": run["request"]["usage"]["completion_tokens"],
        "raw_output_character_count": len(run["model_output"]["raw_text"]),
        "usable_json": False,
        "gold_comparison": "not_performed",
        "scope_note": "This dedicated event-scope prompt is separate from fta_generation_eval_lock_v1, which still describes the multi-stage raw-FaultRecord candidate-FTA runner and remains not_run.",
        "run_path": RUN,
        "attempt_receipt_path": ATTEMPT,
        "assessment_path": ASSESSMENT_JSON,
        "formal_gold": False,
        "eligible_for_independent_final": False,
    }
    manifest["independent_final_validation"].update({
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "NASA Figure 7 is seen and allocated to Development. One DeepSeek request returned an empty truncated response, so it produced no prediction or Gold comparison; this does not create an independent Final dataset or establish accuracy, calibration, or generalization.",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v20"],
        "current_version": "v21",
        "reason": "v21 records exactly one authorized DeepSeek call for the NASA Figure 7 Dev packet; the response hit its output limit and contained no usable JSON. No retry, Gold promotion, independent Final, production write, or readiness change.",
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
        current = V21_PATH.read_text(encoding="utf-8") if V21_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v21 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v21",
            "model_request_count": payload["event_scope_model_inference"]["request_count"],
            "model_output_usable": payload["event_scope_model_inference"]["usable_json"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V21_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V21_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
