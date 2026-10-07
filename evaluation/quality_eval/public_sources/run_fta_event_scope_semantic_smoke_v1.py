#!/usr/bin/env python3
"""Run one explicitly authorized, no-retry prompt-v8 semantic smoke case."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend-python"))

from core.config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS  # noqa: E402
from evaluation.quality_eval.event_scope_tree_contract import validate_event_scope_tree  # noqa: E402
from evaluation.quality_eval.event_scope_tree_prompt_v8 import PROMPT_VERSION, build_prompt  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v3 import response_diagnostics  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v4 import assess_output  # noqa: E402


INPUT_DATASET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_inputs_v1.json"
RUNS_DIR = ROOT / "evaluation/quality_eval/runs"
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_HOST = "api.deepseek.com"
MAX_TOKENS = 8192
SDK_MAX_RETRIES = 0
RESPONSE_FORMAT = {"type": "json_object"}
THINKING_MODE = {"type": "disabled"}
RUN_DATE = "2026-09-29"
CASE_ID_PATTERN = re.compile(r"^SMOKE-\d{3}$")
_FORBIDDEN_LABEL_KEYS = {
    "expected_gate", "expected_candidate_gate", "gold", "reference_gold", "reference_labels",
    "diagram_gates", "text_gate_reviews", "diagram_reference_gate", "text_authorized_gate",
    "gate_label", "review_provenance", "reviewer_role", "rationale", "decisive_source_quote",
}


class SmokeRunError(RuntimeError):
    """Raised when an offline smoke input or one-shot inference cannot proceed safely."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(encoded.encode("utf-8"))


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise SmokeRunError("smoke run artifacts must stay inside the repository") from exc


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _reject_labels(value: Any, path: str = "model_input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_LABEL_KEYS:
                raise SmokeRunError(f"answer/reference field is forbidden in model input: {path}.{key}")
            _reject_labels(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_labels(child, f"{path}[{index}]")


def load_case(case_id: str, dataset_path: Path = INPUT_DATASET_PATH) -> tuple[dict[str, Any], dict[str, Any]]:
    if not CASE_ID_PATTERN.fullmatch(case_id):
        raise SmokeRunError("case_id must use the fixed SMOKE-NNN format")
    dataset_bytes = dataset_path.read_bytes()
    dataset = json.loads(dataset_bytes.decode("utf-8"))
    if dataset.get("artifact_type") != "fta_event_scope_semantic_smoke_inputs":
        raise SmokeRunError("unsupported semantic smoke input artifact")
    if dataset.get("dataset_status") != "constructed_behavioral_smoke_inputs_not_source_corpus":
        raise SmokeRunError("semantic smoke inputs must remain explicitly synthetic")
    if dataset.get("human_expert_gold") is not False or dataset.get("accuracy_claim_allowed") is not False:
        raise SmokeRunError("smoke inputs cannot claim expert Gold or model accuracy")
    guardrails = dataset.get("guardrails", {})
    if guardrails.get("reference_labels_included") is not False or guardrails.get("official_source_claimed") is not False:
        raise SmokeRunError("smoke inputs must not contain references or claim an official source")
    if guardrails.get("model_request_performed") is not False or guardrails.get("database_written") is not False:
        raise SmokeRunError("input fixture must remain offline-only and not persisted to the database")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SmokeRunError("semantic smoke inputs must contain cases")
    by_id: dict[str, dict[str, Any]] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) != {"case_id", "model_input"}:
            raise SmokeRunError(f"cases[{index}] must contain exactly case_id and model_input")
        item_id = case["case_id"]
        if not isinstance(item_id, str) or not CASE_ID_PATTERN.fullmatch(item_id) or item_id in by_id:
            raise SmokeRunError(f"cases[{index}] has invalid or duplicate case_id")
        by_id[item_id] = case
    case = by_id.get(case_id)
    if case is None:
        raise SmokeRunError(f"unknown semantic smoke case_id: {case_id}")
    model_input = case["model_input"]
    if not isinstance(model_input, dict) or set(model_input) != {"event_scope_id", "top_event", "source_segments"}:
        raise SmokeRunError("model_input has an invalid top-level shape")
    _reject_labels(model_input)
    top = model_input["top_event"]
    if not isinstance(top, dict) or set(top) != {"text", "evidence"}:
        raise SmokeRunError("top_event must contain text and evidence only")
    top_evidence = top["evidence"]
    if not isinstance(top_evidence, dict) or set(top_evidence) != {"segment_id", "quote"}:
        raise SmokeRunError("top_event evidence must contain segment_id and quote only")
    segments = model_input["source_segments"]
    if not isinstance(segments, list) or not 1 <= len(segments) <= 30:
        raise SmokeRunError("source_segments must contain 1..30 items")
    segment_by_id: dict[str, dict[str, Any]] = {}
    total_chars = 0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or set(segment) != {"segment_id", "page_number", "section_locator", "text"}:
            raise SmokeRunError(f"source_segments[{index}] has an invalid shape")
        segment_id = segment["segment_id"]
        if not isinstance(segment_id, str) or not segment_id.strip() or segment_id in segment_by_id:
            raise SmokeRunError(f"source_segments[{index}] has an invalid or duplicate segment_id")
        if segment["page_number"] != 1:
            raise SmokeRunError("constructed smoke fixtures must use their synthetic page 1 locator")
        for field in ("section_locator", "text"):
            if not isinstance(segment[field], str) or not segment[field].strip():
                raise SmokeRunError(f"source_segments[{index}].{field} must be non-empty")
        if len(segment["text"]) > 12000:
            raise SmokeRunError(f"source_segments[{index}].text exceeds 12000 characters")
        total_chars += len(segment["text"])
        segment_by_id[segment_id] = segment
    if total_chars > 50000:
        raise SmokeRunError("model-visible source text exceeds 50000 characters")
    evidence_segment = segment_by_id.get(top_evidence["segment_id"])
    quote = top_evidence["quote"]
    if evidence_segment is None or not isinstance(quote, str) or not quote.strip():
        raise SmokeRunError("top-event evidence must reference a source segment and quote")
    if evidence_segment["text"].count(quote) != 1:
        raise SmokeRunError("top-event evidence quote must occur exactly once in its segment")
    if not isinstance(top["text"], str) or not top["text"].strip() or top["text"] not in quote and quote not in top["text"]:
        raise SmokeRunError("top-event text must match or be contained by its evidence quote")
    return case, {"dataset_sha256": _sha256_bytes(dataset_bytes), "model_input": model_input}


def _artifact_paths(case_id: str) -> tuple[Path, Path, Path]:
    stem = f"fta_event_scope_semantic_smoke_{case_id.lower()}_v1_{RUN_DATE}"
    return (
        RUNS_DIR / f"{stem}.json",
        RUNS_DIR / f"{stem}_assessment.json",
        RUNS_DIR / f"{stem}.attempt.json",
    )


def preflight(case_id: str) -> dict[str, Any]:
    _case, loaded = load_case(case_id)
    model_input = loaded["model_input"]
    prompt = build_prompt(model_input)
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    return {
        "case_id": case_id,
        "input_dataset_path": INPUT_DATASET_PATH.resolve().relative_to(ROOT.resolve()).as_posix(),
        "input_dataset_sha256": loaded["dataset_sha256"],
        "model_input_sha256": _canonical_sha256(model_input),
        "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
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
        "reference_labels_loaded": False,
        "gold_included_in_model_input": False,
        "live_request_performed": False,
    }


def _assess_result(result: dict[str, Any], model_input: dict[str, Any]) -> dict[str, Any]:
    parsed = result.get("model_output", {}).get("parsed_json")
    if not isinstance(parsed, dict):
        return {
            "assessment_status": "no_usable_json",
            "strict_json_parsed": False,
            "structure_contract": validate_event_scope_tree(parsed),
            "evidence_location_check": {"checked": 0, "valid": 0, "blockers": ["strict_json_object_required"]},
            "combined_blockers": ["strict_json_object_required"],
            "semantic_correctness": "not_assessed",
            "gold_comparison": "not_performed",
            "accuracy_or_calibration_claim_allowed": False,
            "human_expert_gold": False,
            "fta_ready": False,
            "production_ready": False,
        }
    try:
        return assess_output(result, model_input)
    except (AttributeError, TypeError, KeyError) as exc:
        return {
            "assessment_status": "blocked",
            "strict_json_parsed": True,
            "structure_contract": validate_event_scope_tree(parsed),
            "evidence_location_check": {"checked": 0, "valid": 0, "blockers": ["assessment_contract_error"]},
            "combined_blockers": [{"code": "assessment_contract_error", "error_type": type(exc).__name__}],
            "semantic_correctness": "not_assessed",
            "gold_comparison": "not_performed",
            "accuracy_or_calibration_claim_allowed": False,
            "human_expert_gold": False,
            "fta_ready": False,
            "production_ready": False,
        }


def run_once(*, case_id: str, authorize_single_request: bool = False) -> dict[str, Any]:
    run_path, assessment_path, attempt_path = _artifact_paths(case_id)
    if not authorize_single_request:
        raise SmokeRunError("explicit authorization for one external API request is required")
    run_relative = _relative_path(run_path)
    assessment_relative = _relative_path(assessment_path)
    attempt_relative = _relative_path(attempt_path)
    if run_path.exists() or assessment_path.exists() or attempt_path.exists():
        raise SmokeRunError("artifacts exist for this case; refusing a duplicate API request")
    if not OPENAI_API_KEY:
        raise SmokeRunError("configured provider credential is unavailable")
    if importlib.util.find_spec("openai") is None:
        raise SmokeRunError("OpenAI-compatible SDK is unavailable")
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    if host != EXPECTED_HOST or OPENAI_MODEL != EXPECTED_MODEL:
        raise SmokeRunError("effective provider/model differs from the one-shot smoke-run lock")

    case, loaded = load_case(case_id)
    model_input = loaded["model_input"]
    prompt = build_prompt(model_input)
    prompt_hash = _sha256_bytes(prompt.encode("utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    receipt = {
        "artifact_type": "fta_event_scope_semantic_smoke_attempt",
        "artifact_version": "v1",
        "status": "started_no_retry",
        "started_at_utc": now,
        "case_id": case_id,
        "input_dataset_path": _relative_path(INPUT_DATASET_PATH),
        "input_dataset_sha256": loaded["dataset_sha256"],
        "model_input_sha256": _canonical_sha256(model_input),
        "prompt_sha256": prompt_hash,
        "provider_host": host,
        "model": OPENAI_MODEL,
        "explicit_single_request_authorization": True,
        "authorized_max_request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
        "reference_labels_loaded": False,
    }
    _write_json_exclusive(attempt_path, receipt)
    request: dict[str, Any] = {
        "request_count": 1,
        "retry_count": 0,
        "retry_policy": "disabled_one_attempt_only",
        "provider_host": host,
        "requested_model": OPENAI_MODEL,
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "thinking_mode": THINKING_MODE,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": prompt_hash,
        "reference_labels_loaded": False,
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
            temperature=0,
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
    except Exception as exc:  # one provider attempt only; details never expose credentials
        request["error"] = {
            "type": type(exc).__name__,
            "status_code": getattr(exc, "status_code", None),
            "message": "Provider call failed; details intentionally omitted to avoid credential leakage.",
        }
        response_text, parsed, parse_error = "", None, "provider_call_failed"
        status = "failed_no_retry"

    result = {
        "artifact_type": "fta_event_scope_semantic_smoke_run",
        "artifact_version": "v1",
        "status": status,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case": {
            "case_id": case_id,
            "dataset_status": "constructed_behavioral_smoke_inputs_not_source_corpus",
            "input_dataset_path": _relative_path(INPUT_DATASET_PATH),
            "input_dataset_sha256": loaded["dataset_sha256"],
            "model_input_sha256": _canonical_sha256(model_input),
            "model_input": model_input,
        },
        "request": request,
        "model_output": {
            "raw_text": response_text,
            "parsed_json": parsed,
            "parse_error": parse_error,
            "raw_text_sha256": _sha256_bytes(response_text.encode("utf-8")),
        },
        "claim_boundaries": {
            "constructed_behavioral_smoke_only": True,
            "source_corpus_evaluation": False,
            "human_expert_gold": False,
            "accuracy_or_calibration_claim_allowed": False,
            "reference_comparison_performed": False,
            "gold_or_database_written": False,
            "automatic_repair_performed": False,
            "automatic_retry_performed": False,
            "production_or_database_write": False,
            "fta_ready": False,
            "production_ready": False,
        },
    }
    assessment = {
        "artifact_type": "fta_event_scope_semantic_smoke_assessment",
        "artifact_version": "v1",
        "run_artifact": run_relative,
        "attempt_receipt": attempt_relative,
        "case_id": case_id,
        "output_assessment": _assess_result(result, model_input),
        "raw_model_output_preserved": True,
        "automatic_repair_performed": False,
        "automatic_retry_performed": False,
        "reference_comparison_performed": False,
        "claim_boundaries": result["claim_boundaries"],
    }
    _write_json_exclusive(run_path, result)
    _write_json_exclusive(assessment_path, assessment)
    receipt.update({
        "status": status,
        "completed_at_utc": result["recorded_at_utc"],
        "request_count": 1,
        "run_artifact": run_relative,
        "run_sha256": _sha256_bytes(run_path.read_bytes()),
        "assessment_artifact": assessment_relative,
        "assessment_sha256": _sha256_bytes(assessment_path.read_bytes()),
    })
    attempt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="one fixed SMOKE-NNN case; each call is exactly one request")
    parser.add_argument("--preflight", action="store_true", help="validate and preview request metadata without calling the provider")
    parser.add_argument("--authorize-single-request", action="store_true", help="send exactly one external request; no retries")
    args = parser.parse_args()
    if args.preflight and args.authorize_single_request:
        parser.error("--preflight and --authorize-single-request are mutually exclusive")
    if args.preflight:
        try:
            print(json.dumps(preflight(args.case_id), ensure_ascii=False, indent=2))
        except (OSError, json.JSONDecodeError, SmokeRunError) as exc:
            parser.exit(2, f"preflight failed: {exc}\n")
        return 0
    try:
        result = run_once(case_id=args.case_id, authorize_single_request=args.authorize_single_request)
    except (OSError, json.JSONDecodeError, SmokeRunError) as exc:
        parser.exit(2, f"one-shot smoke request not started: {exc}\n")
    run_path, assessment_path, _attempt_path = _artifact_paths(args.case_id)
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    print(json.dumps({
        "case_id": args.case_id,
        "status": result["status"],
        "request_count": result["request"]["request_count"],
        "retry_count": result["request"]["retry_count"],
        "run_artifact": _relative_path(run_path),
        "assessment_artifact": _relative_path(assessment_path),
        "finish_reason": result["request"].get("finish_reason"),
        "strict_json_parsed": result["model_output"]["parsed_json"] is not None,
        "assessment_status": assessment["output_assessment"]["assessment_status"],
        "reference_comparison_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "response_received" else 1


if __name__ == "__main__":
    raise SystemExit(main())
