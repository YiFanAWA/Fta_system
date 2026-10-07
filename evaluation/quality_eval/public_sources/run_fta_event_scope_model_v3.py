#!/usr/bin/env python3
"""Prepare one bounded DeepSeek JSON-mode call with thinking explicitly disabled."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend-python"))

from core.config import (  # noqa: E402
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from evaluation.quality_eval.fta_event_scope_packet_contract import (  # noqa: E402
    model_input_payload,
)
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import (  # noqa: E402
    PACKET_PATH,
    PROMPT_VERSION,
    TEMPERATURE,
    assess_output,
    build_prompt,
    canonical_sha256,
)


RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json"
ASSESSMENT_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v3_2026-09-29.json"
ATTEMPT_PATH = RUN_PATH.with_name(RUN_PATH.stem + ".attempt.json")
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_HOST = "api.deepseek.com"
MAX_TOKENS = 8192
SDK_MAX_RETRIES = 0
RESPONSE_FORMAT = {"type": "json_object"}
THINKING_MODE = {"type": "disabled"}


class InferenceRunError(RuntimeError):
    """Raised when the one-shot inference cannot safely be prepared."""


def _repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise InferenceRunError("run artifacts must stay inside the repository") from exc


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def response_diagnostics(response: Any) -> tuple[str, Any, dict[str, Any]]:
    """Extract visible output and bounded metadata; never persist reasoning text."""
    choices = _value(response, "choices", []) or []
    choice = choices[0] if choices else None
    message = _value(choice, "message") if choice is not None else None
    content = _value(message, "content", "") if message is not None else ""
    response_text = content if isinstance(content, str) else ""
    reasoning_content = _value(message, "reasoning_content") if message is not None else None
    usage = _value(response, "usage")
    completion_details = _value(usage, "completion_tokens_details") if usage is not None else None
    diagnostics = {
        "choice_count": len(choices),
        "finish_reason": _value(choice, "finish_reason") if choice is not None else None,
        "visible_content_character_count": len(response_text),
        "reasoning_content_present": isinstance(reasoning_content, str) and bool(reasoning_content),
        "reasoning_content_character_count": len(reasoning_content) if isinstance(reasoning_content, str) else 0,
        "reasoning_text_persisted": False,
        "reasoning_tokens": _value(completion_details, "reasoning_tokens") if completion_details is not None else None,
        "usage": {
            "prompt_tokens": _value(usage, "prompt_tokens") if usage is not None else None,
            "completion_tokens": _value(usage, "completion_tokens") if usage is not None else None,
            "total_tokens": _value(usage, "total_tokens") if usage is not None else None,
        } if usage is not None else None,
        "returned_model": _value(response, "model"),
        "provider_request_id": _value(response, "_request_id"),
    }
    return response_text, message, diagnostics


def preflight(packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model_input = model_input_payload(packet)
    prompt = build_prompt(model_input)
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    return {
        "packet_id": packet["packet_id"],
        "packet_path": packet_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "model_input_sha256": canonical_sha256(model_input),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "model": OPENAI_MODEL,
        "provider_host": host,
        "credential_configured": bool(OPENAI_API_KEY),
        "request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
        "prompt_version": PROMPT_VERSION,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "model_input_top_level_keys": sorted(model_input),
        "prompt_char_count": len(prompt),
        "comparison_lock": "v2 prompt/model/token budget/JSON format held; only thinking mode is explicitly disabled",
    }


def assess_v3_output(result: dict[str, Any], model_input: dict[str, Any]) -> dict[str, Any]:
    output = result.get("model_output", {})
    finish_reason = result.get("request", {}).get("finish_reason")
    try:
        assessment = assess_output(result, model_input)
    except (AttributeError, TypeError, KeyError):
        assessment = {
            "assessment_status": "structurally_invalid",
            "finish_reason": finish_reason,
            "strict_json_parsed": isinstance(output.get("parsed_json"), dict),
            "node_count": 0,
            "gate_scope_count": 0,
            "quote_checks": 0,
            "invalid_quotes": 0,
            "structural_errors": ["malformed_model_output_shape"],
            "gold_comparison": "not_performed",
            "semantic_correctness": "not_assessed",
            "accuracy_or_calibration_claim_allowed": False,
            "human_expert_gold": False,
            "fta_ready": False,
            "production_ready": False,
        }
    if finish_reason == "length":
        assessment["assessment_status"] = "truncated"
    elif not output.get("raw_text", "").strip():
        assessment["assessment_status"] = "empty_content"
        if "no_usable_json_object" not in assessment["structural_errors"]:
            assessment["structural_errors"].append("no_usable_json_object")
            assessment["structural_errors"].sort()
    return assessment


def run_once(
    *, packet_path: Path = PACKET_PATH, run_path: Path = RUN_PATH,
    assessment_path: Path = ASSESSMENT_PATH, confirm_credential_rotated: bool = False,
) -> dict[str, Any]:
    attempt_path = run_path.with_name(run_path.stem + ".attempt.json")
    if not confirm_credential_rotated:
        raise InferenceRunError("provider credential rotation must be confirmed before any API request")
    run_relative = _repo_relative_path(run_path)
    assessment_relative = _repo_relative_path(assessment_path)
    attempt_relative = _repo_relative_path(attempt_path)
    if run_path.exists() or attempt_path.exists() or assessment_path.exists():
        raise InferenceRunError("v3 one-shot artifact exists; refusing a duplicate API request")
    if not OPENAI_API_KEY:
        raise InferenceRunError("configured provider credential is unavailable")
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    if host != EXPECTED_HOST or OPENAI_MODEL != EXPECTED_MODEL:
        raise InferenceRunError("effective provider/model differs from the authorized DeepSeek lock")

    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model_input = model_input_payload(packet)
    prompt = build_prompt(model_input)
    packet_relative = packet_path.resolve().relative_to(ROOT.resolve()).as_posix()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    attempt_receipt = {
        "artifact_type": "fta_event_scope_model_inference_attempt",
        "artifact_version": "v3",
        "status": "started_no_retry",
        "started_at_utc": now,
        "packet_id": packet["packet_id"],
        "packet_path": packet_relative,
        "model_input_sha256": canonical_sha256(model_input),
        "prompt_sha256": prompt_hash,
        "provider_host": host,
        "model": OPENAI_MODEL,
        "credential_rotation_confirmed": True,
        "authorized_max_request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
    }
    _write_json_exclusive(attempt_path, attempt_receipt)
    request: dict[str, Any] = {
        "request_count": 1,
        "retry_count": 0,
        "retry_policy": "disabled_one_attempt_only",
        "provider_host": host,
        "requested_model": OPENAI_MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": prompt_hash,
        "comparison_lock": "v2 prompt/model/token budget/JSON format held; only thinking mode is explicitly disabled",
    }
    try:
        import openai

        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE,
            timeout=OPENAI_TIMEOUT_SECONDS,
            max_retries=SDK_MAX_RETRIES,
        )
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format=RESPONSE_FORMAT,
            extra_body={"thinking": THINKING_MODE},
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        response_text, _message, diagnostics = response_diagnostics(response)
        parsed: Any = None
        parse_error = None
        if not response_text.strip():
            parse_error = "empty_content"
        else:
            try:
                parsed = json.loads(response_text)
                if not isinstance(parsed, dict):
                    parse_error = "top_level_response_is_not_object"
                    parsed = None
            except json.JSONDecodeError:
                parse_error = "response_is_not_strict_json"
        request.update(diagnostics)
        request["openai_package_version"] = openai.__version__
        status = "response_received"
    except Exception as exc:  # one shot: capture a safe error, never retry
        request["error"] = {
            "type": type(exc).__name__,
            "status_code": getattr(exc, "status_code", None),
            "message": "Provider call failed; details intentionally omitted to avoid credential leakage.",
        }
        response_text = ""
        parsed = None
        parse_error = "provider_call_failed"
        status = "failed_no_retry"

    result = {
        "artifact_type": "fta_event_scope_model_inference_run",
        "artifact_version": "v3",
        "status": status,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case": {
            "packet_id": packet["packet_id"],
            "source_cluster_id": packet["source_provenance"]["source_cluster_id"],
            "exposure_status": packet["source_provenance"]["exposure_status"],
            "packet_path": packet_relative,
            "model_input_sha256": canonical_sha256(model_input),
        },
        "request": request,
        "model_output": {
            "raw_text": response_text,
            "parsed_json": parsed,
            "parse_error": parse_error,
            "raw_text_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        },
        "claim_boundaries": {
            "development_only": True,
            "human_expert_gold": False,
            "independent_final_validation": False,
            "accuracy_or_calibration_claim_allowed": False,
            "production_or_database_write": False,
            "fta_ready": False,
            "production_ready": False,
        },
    }
    assessment = {
        "artifact_type": "fta_event_scope_model_run_assessment",
        "artifact_version": "v3",
        "run_artifact": run_relative,
        "attempt_receipt": attempt_relative,
        "case": result["case"],
        "request_observation": request,
        "output_assessment": assess_v3_output(result, model_input),
        "claim_boundaries": result["claim_boundaries"],
    }
    _write_json_exclusive(run_path, result)
    _write_json_exclusive(assessment_path, assessment)
    attempt_receipt.update({
        "status": status,
        "completed_at_utc": result["recorded_at_utc"],
        "request_count": 1,
        "run_artifact": run_relative,
        "run_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(),
        "assessment_artifact": assessment_relative,
        "assessment_sha256": hashlib.sha256(assessment_path.read_bytes()).hexdigest(),
    })
    attempt_path.write_text(json.dumps(attempt_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="validate inputs without an API request")
    parser.add_argument("--packet", type=Path, default=PACKET_PATH)
    parser.add_argument("--output", type=Path, default=RUN_PATH)
    parser.add_argument("--assessment", type=Path, default=ASSESSMENT_PATH)
    parser.add_argument(
        "--confirm-credential-rotated", action="store_true",
        help="required after the previously exposed provider key has been rotated; sends exactly one request",
    )
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.packet), ensure_ascii=False, indent=2))
        return 0
    try:
        result = run_once(
            packet_path=args.packet,
            run_path=args.output,
            assessment_path=args.assessment,
            confirm_credential_rotated=args.confirm_credential_rotated,
        )
    except (OSError, ValueError, InferenceRunError) as exc:
        parser.exit(2, f"one-shot inference not started: {exc}\n")
    print(json.dumps({
        "status": result["status"],
        "request_count": result["request"]["request_count"],
        "retry_count": result["request"]["retry_count"],
        "run_artifact": str(args.output),
        "attempt_receipt": str(args.output.with_name(args.output.stem + ".attempt.json")),
        "assessment_artifact": str(args.assessment),
        "finish_reason": result["request"].get("finish_reason"),
        "strict_json_parsed": result["model_output"]["parsed_json"] is not None,
        "reasoning_content_present": result["request"].get("reasoning_content_present"),
        "reasoning_tokens": result["request"].get("reasoning_tokens"),
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "response_received" else 1


if __name__ == "__main__":
    raise SystemExit(main())
