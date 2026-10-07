#!/usr/bin/env python3
"""Build the v22 FTA baseline with the second incomplete, JSON-mode Dev call."""

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

V21_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v21.json"
V22_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v22.json"
RUN_V1 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.json"
ATTEMPT_V1 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.attempt.json"
ASSESSMENT_V1 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.json"
RUN_V2 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json"
ATTEMPT_V2 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.attempt.json"
ASSESSMENT_V2 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.json"
ASSESSMENT_MD_V2 = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.md"

CURRENT_ARTIFACTS = {
    RUN_V2: ("nasa-battery-fig7-deepseek-one-shot-run-v2", "event_scope_model_inference_run", "current", "Second separately authorized single DeepSeek request; JSON mode and 8192 output tokens were used, but completion ended at length with empty content and no usable JSON."),
    ATTEMPT_V2: ("nasa-battery-fig7-one-shot-attempt-receipt-v2", "one_shot_inference_receipt", "current", "Durable receipt records one request, zero retries, JSON mode, and the 8192-token output limit."),
    ASSESSMENT_V2: ("nasa-battery-fig7-one-shot-assessment-json-v2", "model_run_assessment", "current", "Offline structure/output assessment; no Gold comparison or semantic accuracy claim."),
    ASSESSMENT_MD_V2: ("nasa-battery-fig7-one-shot-assessment-md-v2", "model_run_assessment_document", "current", "Human-readable comparison of two incomplete single-call attempts and their claim limits."),
    "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v2.py": ("fta-event-scope-one-shot-runner-v2", "evaluation_tool", "current", "Uses validated model_input only, concise output contract, JSON mode, 8192 max tokens, and SDK retries disabled."),
    "evaluation/quality_eval/test_run_fta_event_scope_model_v2.py": ("fta-event-scope-one-shot-runner-tests-v2", "evaluation_tool_tests", "current", "Offline tests for projection isolation, JSON mode, output budget, truncation handling, and evidence-quote membership checks."),
    "evaluation/quality_eval/build_fta_baseline_manifest_v22.py": ("fta-baseline-manifest-v22-builder", "reproducibility_tool", "current", "Builds v22 from the frozen v21 manifest and reconciles both single-call attempts without promoting readiness."),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v22.py": ("fta-baseline-manifest-v22-tests", "manifest_regression_tests", "current", "Checks exact request accounting, unusable output, no Gold promotion, unchanged Final status, and false readiness."),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-v22-default", "validation_tool", "current", "Validates repository paths and hashes; defaults to the active v22 manifest."),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-tests-v22-default", "validation_tool_tests", "current", "Covers hash validation and the active v22 repository snapshot."),
    "docs/README.md": ("fta-v22-doc-index", "current_truth_index", "current", "Points to active FTA baseline v22 and the two incomplete NASA Figure 7 inference requests."),
    "docs/current-state-audit.md": ("fta-v22-current-state-audit", "current_state_document", "current", "Records two one-shot attempts, no usable output, no semantic score, and unchanged readiness."),
    "docs/acceptance.md": ("fta-v22-acceptance-record", "acceptance_document", "current", "Records v2 runner tests, preflight, one API request, zero retries, and no usable JSON."),
    "docs/candidate-fta-generation-v1.md": ("fta-v22-candidate-generation-policy", "candidate_fta_policy_document", "current", "Documents the latest incomplete Dev inference without claiming model performance."),
    "docs/fta-validation-reliability-plan-v1.md": ("fta-v22-validation-plan-policy", "validation_plan_document", "current", "Updates active baseline and logs the second bounded incomplete inference."),
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
    v21 = json.loads(V21_PATH.read_text(encoding="utf-8"))
    if v21.get("manifest_id") != "candidate_fta_research_baseline_v21":
        raise ValueError("v22 must extend the frozen v21 manifest")
    run1 = json.loads((ROOT / RUN_V1).read_text(encoding="utf-8"))
    attempt1 = json.loads((ROOT / ATTEMPT_V1).read_text(encoding="utf-8"))
    assessment1 = json.loads((ROOT / ASSESSMENT_V1).read_text(encoding="utf-8"))
    run2 = json.loads((ROOT / RUN_V2).read_text(encoding="utf-8"))
    attempt2 = json.loads((ROOT / ATTEMPT_V2).read_text(encoding="utf-8"))
    assessment2 = json.loads((ROOT / ASSESSMENT_V2).read_text(encoding="utf-8"))
    request2 = run2.get("request", {})
    output2 = run2.get("model_output", {})
    assessed2 = assessment2.get("output_assessment", {})
    if run2.get("status") != "response_received":
        raise ValueError("v2 must record the observed provider response")
    if request2.get("request_count") != 1 or request2.get("retry_count") != 0:
        raise ValueError("v2 must record exactly one request and no retries")
    if request2.get("max_tokens") != 8192 or request2.get("response_format") != {"type": "json_object"}:
        raise ValueError("v2 request must use the approved JSON-mode output budget")
    if request2.get("finish_reason") != "length" or request2.get("usage", {}).get("completion_tokens") != 8192:
        raise ValueError("v2 response must match the observed output-limit exhaustion")
    if output2.get("raw_text") != "" or output2.get("parsed_json") is not None:
        raise ValueError("v2 must not claim usable model content")
    if attempt2.get("request_count") != 1 or attempt2.get("status") != "response_received":
        raise ValueError("v2 attempt receipt does not reconcile with its run")
    if assessed2.get("assessment_status") != "truncated" or assessed2.get("gold_comparison") != "not_performed":
        raise ValueError("v2 assessment must preserve the no-score boundary")
    if run1.get("request", {}).get("request_count") != 1 or attempt1.get("request_count") != 1:
        raise ValueError("v1 attempt accounting is missing")
    if assessment1.get("assessment_status") != "completed_request_but_no_usable_output":
        raise ValueError("v1 historical assessment does not match the expected incomplete result")

    manifest = deepcopy(v21)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v22"
    manifest["baseline_version"] = "v22"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "a second separately authorized NASA Figure 7 Dev inference using concise JSON-mode output and an 8192-token limit; the response again ended at length with empty content"
    )
    manifest["scope"]["excludes"].extend([
        "any inference about gate accuracy, model capability, calibration, or generalization from two unusable outputs",
        "any third request or automatic retry",
    ])
    manifest["active_baseline"].update({
        "event_scope_model_run": RUN_V2,
        "event_scope_model_run_assessment": ASSESSMENT_V2,
        "event_scope_model_prompt": "event-scope-text-only-tree-v2-compact-json",
    })
    manifest["event_scope_packet_contract"].update({
        "model_inference_run": True,
        "model_inference_request_count": 2,
        "model_inference_retry_count": 0,
        "model_inference_output_status": "two_attempts_finish_length_empty_content",
        "model_inference_comparison_status": "not_performed",
        "human_expert_reviewed": False,
    })
    manifest["event_scope_dev_case"].update({
        "model_inference_run": True,
        "model_inference_request_count": 2,
        "model_inference_retry_count": 0,
        "model_output_usable": False,
        "gate_comparison_status": "not_performed",
        "accuracy_or_calibration_claim_allowed": False,
        "model_run_path": RUN_V2,
        "model_run_assessment_path": ASSESSMENT_V2,
        "attempt_receipt_path": ATTEMPT_V2,
    })
    manifest["event_scope_model_inference"] = {
        "status": "two_single_attempts_returned_empty_truncated_content",
        "packet_id": run2["case"]["packet_id"],
        "source_cluster_id": run2["case"]["source_cluster_id"],
        "model": request2["returned_model"],
        "provider_host": request2["provider_host"],
        "request_count": 2,
        "retry_count": 0,
        "attempts": [
            {
                "run_path": RUN_V1,
                "max_tokens": run1["request"]["max_tokens"],
                "response_format": "text_default",
                "finish_reason": run1["request"]["finish_reason"],
                "completion_tokens": run1["request"]["usage"]["completion_tokens"],
                "raw_output_character_count": len(run1["model_output"]["raw_text"]),
                "usable_json": False,
            },
            {
                "run_path": RUN_V2,
                "max_tokens": request2["max_tokens"],
                "response_format": request2["response_format"]["type"],
                "finish_reason": request2["finish_reason"],
                "completion_tokens": request2["usage"]["completion_tokens"],
                "raw_output_character_count": len(output2["raw_text"]),
                "usable_json": False,
            },
        ],
        "latest_prompt_version": request2["prompt_version"],
        "latest_prompt_sha256": request2["prompt_sha256"],
        "latest_max_tokens": request2["max_tokens"],
        "latest_temperature": request2["temperature"],
        "latest_completion_tokens": request2["usage"]["completion_tokens"],
        "usable_json": False,
        "gold_comparison": "not_performed",
        "root_cause": "undetermined",
        "scope_note": "Both attempts use the seen Development packet and are not an accuracy sample. DeepSeek JSON mode can still return empty content; no third request is authorized or made. Full raw-FaultRecord multi-stage eval lock remains a separate not_run workflow.",
        "run_path": RUN_V2,
        "attempt_receipt_path": ATTEMPT_V2,
        "assessment_path": ASSESSMENT_V2,
        "formal_gold": False,
        "eligible_for_independent_final": False,
    }
    manifest["independent_final_validation"].update({
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "NASA Figure 7 is a seen Development sample. Two single DeepSeek requests (the second with JSON mode and 8192 output tokens) returned empty truncated content; neither produced a prediction or Gold comparison. This does not establish accuracy, calibration, or generalization.",
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v21"],
        "current_version": "v22",
        "reason": "v22 records a second separately authorized single request with JSON mode and an 8192-token limit; it also returned finish_reason=length with empty content. No retry, third call, Gold promotion, Final creation, production write, or readiness change.",
    })
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })
    for artifact in manifest["artifacts"]:
        if artifact.get("path") in {RUN_V1, ATTEMPT_V1, ASSESSMENT_V1}:
            artifact["lifecycle"] = "historical"

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
        current = V22_PATH.read_text(encoding="utf-8") if V22_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v22 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v22",
            "model_request_count": payload["event_scope_model_inference"]["request_count"],
            "latest_output_usable": payload["event_scope_model_inference"]["usable_json"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V22_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V22_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
