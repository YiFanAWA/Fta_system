#!/usr/bin/env python3
"""Make one bounded DeepSeek JSON-mode inference on an isolated event packet."""

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
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json"
ASSESSMENT_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.json"
ATTEMPT_PATH = RUN_PATH.with_name(RUN_PATH.stem + ".attempt.json")
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_HOST = "api.deepseek.com"
TEMPERATURE = 0
MAX_TOKENS = 8192
SDK_MAX_RETRIES = 0
RESPONSE_FORMAT = {"type": "json_object"}
PROMPT_VERSION = "event-scope-text-only-tree-v2-compact-json"


class InferenceRunError(RuntimeError):
    """Raised when the one-shot inference cannot safely be prepared."""


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build a compact, evidence-only prompt from the validated projection."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "根据给定原文为一个顶事件抽取最小事件树。只能依据输入文本，不看图、不用外部知识；"
        "原文未直接支持的节点、因果边或逻辑门不得补造。时间先后、并列列举、因果合理性本身"
        "不证明 AND/OR。只有文本明确支持子事件如何共同或择一形成输出事件时才标 AND/OR；"
        "门范围或子项不明确就标 unknown。每条 evidence_quote 必须是输入原文的连续子串，"
        "无法支持则为 null。不要输出推理过程，只输出符合示例结构的 JSON 对象：\n"
        '{"nodes":[{"id":"E1","text":"事件文本","type":"top_event|intermediate_event|basic_event|undeveloped_event",'
        '"parent_id":null,"evidence_quote":"原文连续引文或null"}],'
        '"gates":[{"scope_id":"S1","output_node_id":"E1","child_node_ids":["E2","E3"],'
        '"gate":"AND|OR|unknown","evidence_quote":"直接支持门型的原文连续引文或null",'
        '"reason":"不超过一句；unknown 时说明缺少的证据/范围"}],"unresolved_questions":[]}\n'
        "输入 JSON：\n" + payload
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
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "model_input_top_level_keys": sorted(model_input),
        "prompt_char_count": len(prompt),
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def assess_output(result: dict[str, Any], model_input: dict[str, Any]) -> dict[str, Any]:
    """Check JSON shape and quote membership only; never score against reference Gold."""
    parsed = result.get("model_output", {}).get("parsed_json")
    finish_reason = result.get("request", {}).get("finish_reason")
    source_texts = [segment["text"] for segment in model_input["source_segments"]]
    source_texts.append(model_input["top_event"]["evidence"]["quote"])
    errors: list[str] = []
    quote_checks = 0
    invalid_quotes = 0
    if not isinstance(parsed, dict):
        errors.append("no_usable_json_object")
    else:
        nodes = parsed.get("nodes")
        gates = parsed.get("gates")
        if not isinstance(nodes, list) or not isinstance(gates, list):
            errors.append("nodes_and_gates_must_be_arrays")
            nodes, gates = [], []
        node_ids = {item.get("id") for item in nodes if isinstance(item, dict)}
        if len(node_ids) != len(nodes):
            errors.append("node_ids_missing_or_duplicated")
        for node in nodes:
            if not isinstance(node, dict):
                errors.append("node_entry_must_be_object")
                continue
            quote = node.get("evidence_quote")
            if quote is not None:
                quote_checks += 1
                if not isinstance(quote, str) or not any(quote in text for text in source_texts):
                    invalid_quotes += 1
                    errors.append("node_quote_not_found_in_input")
        for gate in gates:
            if not isinstance(gate, dict):
                errors.append("gate_entry_must_be_object")
                continue
            quote = gate.get("evidence_quote")
            if quote is not None:
                quote_checks += 1
                if not isinstance(quote, str) or not any(quote in text for text in source_texts):
                    invalid_quotes += 1
                    errors.append("gate_quote_not_found_in_input")
            output_id = gate.get("output_node_id")
            child_ids = gate.get("child_node_ids")
            if output_id not in node_ids or not isinstance(child_ids, list) or any(item not in node_ids for item in child_ids):
                errors.append("gate_references_unknown_node")
            if gate.get("gate") not in {"AND", "OR", "unknown"}:
                errors.append("unsupported_gate_label")
    return {
        "assessment_status": "truncated" if finish_reason == "length" else ("structurally_invalid" if errors else "structure_and_quotes_checked"),
        "finish_reason": finish_reason,
        "strict_json_parsed": isinstance(parsed, dict),
        "node_count": len(parsed.get("nodes", [])) if isinstance(parsed, dict) and isinstance(parsed.get("nodes"), list) else 0,
        "gate_scope_count": len(parsed.get("gates", [])) if isinstance(parsed, dict) and isinstance(parsed.get("gates"), list) else 0,
        "quote_checks": quote_checks,
        "invalid_quotes": invalid_quotes,
        "structural_errors": sorted(set(errors)),
        "gold_comparison": "not_performed",
        "semantic_correctness": "not_assessed",
        "accuracy_or_calibration_claim_allowed": False,
        "human_expert_gold": False,
        "fta_ready": False,
        "production_ready": False,
    }


def run_once(
    *, packet_path: Path = PACKET_PATH, run_path: Path = RUN_PATH,
    assessment_path: Path = ASSESSMENT_PATH,
) -> dict[str, Any]:
    attempt_path = run_path.with_name(run_path.stem + ".attempt.json")
    if run_path.exists() or attempt_path.exists() or assessment_path.exists():
        raise InferenceRunError("v2 one-shot artifact exists; refusing a duplicate API request")
    if not OPENAI_API_KEY:
        raise InferenceRunError("configured DeepSeek credential is unavailable")
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    if host != EXPECTED_HOST or OPENAI_MODEL != EXPECTED_MODEL:
        raise InferenceRunError("effective provider/model differs from the authorized DeepSeek lock")

    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model_input = model_input_payload(packet)
    prompt = build_prompt(model_input)
    packet_relative = packet_path.resolve().relative_to(ROOT.resolve()).as_posix()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    attempt_receipt = {
        "artifact_type": "fta_event_scope_model_inference_attempt",
        "artifact_version": "v2",
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
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
    }
    _write_json_exclusive(attempt_path, attempt_receipt)
    request = {
        "request_count": 1,
        "retry_count": 0,
        "retry_policy": "disabled_one_attempt_only",
        "provider_host": host,
        "requested_model": OPENAI_MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": RESPONSE_FORMAT,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "sdk_max_retries": SDK_MAX_RETRIES,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
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
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        response_text = (response.choices[0].message.content if response.choices else "") or ""
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
        request.update({
            "returned_model": getattr(response, "model", None),
            "provider_request_id": getattr(response, "_request_id", None),
            "openai_package_version": openai.__version__,
            "finish_reason": response.choices[0].finish_reason if response.choices else None,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            } if usage is not None else None,
        })
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
        "artifact_version": "v2",
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
        "artifact_version": "v2",
        "run_artifact": run_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "attempt_receipt": attempt_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "case": result["case"],
        "request_observation": request,
        "output_assessment": assess_output(result, model_input),
        "claim_boundaries": result["claim_boundaries"],
    }
    _write_json_exclusive(run_path, result)
    _write_json_exclusive(assessment_path, assessment)
    attempt_receipt.update({
        "status": status,
        "completed_at_utc": result["recorded_at_utc"],
        "request_count": 1,
        "run_artifact": run_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "run_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(),
        "assessment_artifact": assessment_path.resolve().relative_to(ROOT.resolve()).as_posix(),
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
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(args.packet), ensure_ascii=False, indent=2))
        return 0
    try:
        result = run_once(packet_path=args.packet, run_path=args.output, assessment_path=args.assessment)
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
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "response_received" else 1


if __name__ == "__main__":
    raise SystemExit(main())
