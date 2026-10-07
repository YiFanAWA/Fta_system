#!/usr/bin/env python3
"""Run exactly one DeepSeek inference on a validated event-scope model input."""

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


PACKET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.json"
ATTEMPT_PATH = RUN_PATH.with_name(RUN_PATH.stem + ".attempt.json")
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_HOST = "api.deepseek.com"
TEMPERATURE = 0
MAX_TOKENS = 3000
SDK_MAX_RETRIES = 0
PROMPT_VERSION = "event-scope-text-only-tree-v1"


class InferenceRunError(RuntimeError):
    """Raised when the bounded one-request run cannot be prepared or saved."""


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_prompt(model_input: dict[str, Any]) -> str:
    """Construct the sole model prompt from the packet's validated projection."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, indent=2)
    return (
        "你是故障树结构抽取器。本任务只判断给定原文直接支持的单一顶事件结构；"
        "只能使用下方 model_input 中的内容，不得调用外部知识，不得假设看到了图示。\n"
        "请从原文识别有证据支持的事件/条件及其层级，并对每个有至少两个直接子项的"
        "组合范围判断 AND、OR 或 unknown。时间先后、因果解释、并列列举本身不自动构成逻辑门；"
        "只有原文直接说明多个子事件如何共同或择一形成同一输出事件时才选 AND/OR。"
        "无法把门型唯一绑定到精确事件范围时选 unknown，并解释歧义。不得仅凭门型置信度替代文本证据。\n"
        "所有 evidence_quote 必须是 source_segments.text 中逐字连续的原文；没有直接支持时设为 null。"
        "节点只保留原文明确支持的事件，不从上下文补造部件、事件或现场状态。"
        "同一短语在原文多次出现时可以复用引文文本，但不要声称字符位置或猜测出现位置。\n"
        "严格只输出一个 JSON 对象，不要 Markdown，不要解释 JSON 以外的内容。格式：\n"
        '{"nodes":[{"node_id":"n1","text":"事件/条件","node_type":"top_event|intermediate_event|basic_event|undeveloped_event",'
        '"parent_node_id":null,"evidence_quote":"原文连续引文"}],'
        '"gate_scopes":[{"scope_id":"g1","output_node_id":"n1","child_node_ids":["n2","n3"],'
        '"gate":"AND|OR|unknown","evidence_quote":"直接支持门型的原文连续引文或null",'
        '"reason":"简短说明；unknown时说明具体缺失/歧义"}],'
        '"unresolved_questions":["仍无法从给定原文确定的问题"]}\n\n'
        "model_input:\n" + payload
    )


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
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "model_input_top_level_keys": sorted(model_input),
        "prompt_char_count": len(prompt),
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run_once(
    *, packet_path: Path = PACKET_PATH, run_path: Path = RUN_PATH
) -> dict[str, Any]:
    attempt_path = run_path.with_name(run_path.stem + ".attempt.json")
    if run_path.exists() or attempt_path.exists():
        raise InferenceRunError(
            "one-shot guard exists; refusing a second inference attempt"
        )
    if not OPENAI_API_KEY:
        raise InferenceRunError("configured DeepSeek credential is unavailable")
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    if host != EXPECTED_HOST or OPENAI_MODEL != EXPECTED_MODEL:
        raise InferenceRunError(
            "effective provider/model differs from the authorized DeepSeek lock"
        )

    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model_input = model_input_payload(packet)
    prompt = build_prompt(model_input)
    packet_relative = packet_path.resolve().relative_to(ROOT.resolve()).as_posix()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    attempt_receipt = {
        "artifact_type": "fta_event_scope_model_inference_attempt",
        "artifact_version": "v1",
        "status": "started_no_retry",
        "started_at_utc": now,
        "packet_id": packet["packet_id"],
        "packet_path": packet_relative,
        "model_input_sha256": canonical_sha256(model_input),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "provider_host": host,
        "model": OPENAI_MODEL,
        "authorized_max_request_count": 1,
        "sdk_max_retries": SDK_MAX_RETRIES,
    }
    _write_json_exclusive(attempt_path, attempt_receipt)

    request_count = 1
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
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        response_text = (
            response.choices[0].message.content
            if response.choices
            else ""
        ) or ""
        parsed: Any = None
        parse_error = None
        try:
            parsed = json.loads(response_text)
            if not isinstance(parsed, dict):
                parse_error = "top_level_response_is_not_object"
                parsed = None
        except json.JSONDecodeError:
            parse_error = "response_is_not_strict_json"

        usage = getattr(response, "usage", None)
        usage_payload = None
        if usage is not None:
            usage_payload = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        result = {
            "artifact_type": "fta_event_scope_model_inference_run",
            "artifact_version": "v1",
            "status": "succeeded",
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "case": {
                "packet_id": packet["packet_id"],
                "source_cluster_id": packet["source_provenance"]["source_cluster_id"],
                "exposure_status": packet["source_provenance"]["exposure_status"],
                "packet_path": packet_relative,
                "model_input_sha256": canonical_sha256(model_input),
            },
            "request": {
                "request_count": request_count,
                "retry_count": 0,
                "retry_policy": "disabled_one_attempt_only",
                "provider_host": host,
                "requested_model": OPENAI_MODEL,
                "returned_model": getattr(response, "model", None),
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
                "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
                "sdk_max_retries": SDK_MAX_RETRIES,
                "prompt_version": PROMPT_VERSION,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "openai_package_version": openai.__version__,
                "provider_request_id": getattr(response, "_request_id", None),
                "usage": usage_payload,
                "finish_reason": (
                    response.choices[0].finish_reason if response.choices else None
                ),
            },
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
    except Exception as exc:  # one shot: capture a safe error, never retry
        status_code = getattr(exc, "status_code", None)
        result = {
            "artifact_type": "fta_event_scope_model_inference_run",
            "artifact_version": "v1",
            "status": "failed_no_retry",
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "case": {
                "packet_id": packet["packet_id"],
                "source_cluster_id": packet["source_provenance"]["source_cluster_id"],
                "exposure_status": packet["source_provenance"]["exposure_status"],
                "packet_path": packet_relative,
                "model_input_sha256": canonical_sha256(model_input),
            },
            "request": {
                "request_count": request_count,
                "retry_count": 0,
                "retry_policy": "disabled_one_attempt_only",
                "provider_host": host,
                "requested_model": OPENAI_MODEL,
                "temperature": TEMPERATURE,
                "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
                "sdk_max_retries": SDK_MAX_RETRIES,
                "prompt_version": PROMPT_VERSION,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            },
            "error": {
                "type": type(exc).__name__,
                "status_code": status_code,
                "message": "Provider call failed; details intentionally omitted to avoid credential leakage.",
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

    _write_json_exclusive(run_path, result)
    attempt_receipt["status"] = result["status"]
    attempt_receipt["completed_at_utc"] = result["recorded_at_utc"]
    attempt_receipt["request_count"] = request_count
    attempt_receipt["run_artifact"] = run_path.resolve().relative_to(ROOT.resolve()).as_posix()
    attempt_receipt["run_sha256"] = hashlib.sha256(run_path.read_bytes()).hexdigest()
    attempt_path.write_text(
        json.dumps(attempt_receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="validate inputs without an API request")
    parser.add_argument("--packet", type=Path, default=PACKET_PATH)
    parser.add_argument("--output", type=Path, default=RUN_PATH)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.packet), ensure_ascii=False, indent=2))
        return 0
    try:
        result = run_once(packet_path=args.packet, run_path=args.output)
    except (OSError, ValueError, InferenceRunError) as exc:
        parser.exit(2, f"one-shot inference not started: {exc}\n")
    summary = {
        "status": result["status"],
        "request_count": result["request"]["request_count"],
        "retry_count": result["request"]["retry_count"],
        "run_artifact": str(args.output),
        "attempt_receipt": str(args.output.with_name(args.output.stem + ".attempt.json")),
    }
    if result["status"] == "succeeded":
        summary["gate_scope_count"] = len(
            (result.get("model_output", {}).get("parsed_json") or {}).get("gate_scopes", [])
        )
        summary["json_parse_error"] = result["model_output"]["parse_error"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
