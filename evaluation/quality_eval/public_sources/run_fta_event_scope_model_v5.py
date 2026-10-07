#!/usr/bin/env python3
"""Run one explicitly authorized, no-retry inference using event-scope prompt v5."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend-python"))

from core.config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS  # noqa: E402
from evaluation.quality_eval.event_scope_tree_prompt_v5 import PROMPT_VERSION, build_prompt  # noqa: E402
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH, TEMPERATURE, canonical_sha256  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v3 import response_diagnostics  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v4 import assess_output  # noqa: E402


RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json"
ASSESSMENT_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v5_2026-09-29.json"
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_HOST = "api.deepseek.com"
MAX_TOKENS = 8192
SDK_MAX_RETRIES = 0
RESPONSE_FORMAT = {"type": "json_object"}
THINKING_MODE = {"type": "disabled"}


class InferenceRunError(RuntimeError):
    """Raised when the single inference cannot safely be prepared."""


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise InferenceRunError("run artifacts must stay inside the repository") from exc


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _input(packet_path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model_input = model_input_payload(packet)
    return packet, model_input, build_prompt(model_input)


def preflight(packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    packet, model_input, prompt = _input(packet_path)
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    return {
        "packet_id": packet["packet_id"],
        "packet_path": _relative_path(packet_path),
        "model_input_sha256": canonical_sha256(model_input),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_version": PROMPT_VERSION,
        "provider_host": host,
        "model": OPENAI_MODEL,
        "credential_configured": bool(OPENAI_API_KEY),
        "sdk_available": importlib.util.find_spec("openai") is not None,
        "request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "model_input_top_level_keys": sorted(model_input),
        "prompt_char_count": len(prompt),
        "gold_included_in_model_input": False,
        "live_request_performed": False,
    }


def run_once(
    *,
    packet_path: Path = PACKET_PATH,
    run_path: Path = RUN_PATH,
    assessment_path: Path = ASSESSMENT_PATH,
    authorize_single_request: bool = False,
) -> dict[str, Any]:
    attempt_path = run_path.with_name(run_path.stem + ".attempt.json")
    if not authorize_single_request:
        raise InferenceRunError("explicit authorization for one external API request is required")
    run_relative = _relative_path(run_path)
    assessment_relative = _relative_path(assessment_path)
    attempt_relative = _relative_path(attempt_path)
    if run_path.exists() or attempt_path.exists() or assessment_path.exists():
        raise InferenceRunError("v5 artifact exists; refusing a duplicate API request")
    if not OPENAI_API_KEY:
        raise InferenceRunError("configured provider credential is unavailable")
    if importlib.util.find_spec("openai") is None:
        raise InferenceRunError("OpenAI-compatible SDK is unavailable")
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    if host != EXPECTED_HOST or OPENAI_MODEL != EXPECTED_MODEL:
        raise InferenceRunError("effective provider/model differs from the one-shot v5 lock")

    packet, model_input, prompt = _input(packet_path)
    packet_relative = _relative_path(packet_path)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    receipt = {
        "artifact_type": "fta_event_scope_model_inference_attempt",
        "artifact_version": "v5",
        "status": "started_no_retry",
        "started_at_utc": now,
        "packet_id": packet["packet_id"],
        "packet_path": packet_relative,
        "model_input_sha256": canonical_sha256(model_input),
        "prompt_sha256": prompt_hash,
        "provider_host": host,
        "model": OPENAI_MODEL,
        "explicit_single_request_authorization": True,
        "authorized_max_request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
    }
    _write_json_exclusive(attempt_path, receipt)
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
        "gold_included_in_model_input": False,
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
    except Exception as exc:  # one request only; errors are recorded safely and never retried
        request["error"] = {
            "type": type(exc).__name__,
            "status_code": getattr(exc, "status_code", None),
            "message": "Provider call failed; details intentionally omitted to avoid credential leakage.",
        }
        response_text, parsed, parse_error = "", None, "provider_call_failed"
        status = "failed_no_retry"

    result = {
        "artifact_type": "fta_event_scope_model_inference_run",
        "artifact_version": "v5",
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
            "gold_or_database_written": False,
            "production_or_database_write": False,
            "fta_ready": False,
            "production_ready": False,
        },
    }
    assessment = {
        "artifact_type": "fta_event_scope_model_run_assessment",
        "artifact_version": "v5",
        "run_artifact": run_relative,
        "attempt_receipt": attempt_relative,
        "case": result["case"],
        "request_observation": request,
        "output_assessment": assess_output(result, model_input),
        "claim_boundaries": result["claim_boundaries"],
    }
    _write_json_exclusive(run_path, result)
    _write_json_exclusive(assessment_path, assessment)
    receipt.update({
        "status": status,
        "completed_at_utc": result["recorded_at_utc"],
        "request_count": 1,
        "run_artifact": run_relative,
        "run_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(),
        "assessment_artifact": assessment_relative,
        "assessment_sha256": hashlib.sha256(assessment_path.read_bytes()).hexdigest(),
    })
    attempt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="validate inputs without calling the provider")
    parser.add_argument("--packet", type=Path, default=PACKET_PATH)
    parser.add_argument("--output", type=Path, default=RUN_PATH)
    parser.add_argument("--assessment", type=Path, default=ASSESSMENT_PATH)
    parser.add_argument("--authorize-single-request", action="store_true", help="send exactly one external request; no retries")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.packet), ensure_ascii=False, indent=2))
        return 0
    try:
        result = run_once(
            packet_path=args.packet,
            run_path=args.output,
            assessment_path=args.assessment,
            authorize_single_request=args.authorize_single_request,
        )
    except (OSError, ValueError, InferenceRunError) as exc:
        parser.exit(2, f"one-shot inference not started: {exc}\n")
    print(json.dumps({
        "status": result["status"],
        "request_count": result["request"]["request_count"],
        "retry_count": result["request"]["retry_count"],
        "run_artifact": str(args.output),
        "assessment_artifact": str(args.assessment),
        "finish_reason": result["request"].get("finish_reason"),
        "strict_json_parsed": result["model_output"]["parsed_json"] is not None,
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "response_received" else 1


if __name__ == "__main__":
    raise SystemExit(main())
