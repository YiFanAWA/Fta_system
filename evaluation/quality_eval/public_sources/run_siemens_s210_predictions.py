#!/usr/bin/env python3
"""Generate independent predictions for the 30-record SINAMICS S210 sample."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib import error, request
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("samples"), list):
        raise ValueError("sample JSON must contain a samples list")
    return value


def _build_request_payload(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "system": "SINAMICS S210 fault extraction benchmark",
        "top_event": "fault record extraction",
        "source": "text",
        # /api/fta/generate uses the GenerateFTARequest contract, whose text
        # input field is named raw_text.  Keep this runner aligned with the
        # public API instead of silently producing 400 rows for every sample.
        "raw_text": str(sample.get("input_text", "")),
        "use_knowledge_graph": False,
        "run_analysis_report": False,
        "run_draft_review": False,
        "prompt_profile": "strict",
        "custom_instructions": (
            "只抽取原文明确支持的故障记录字段。不要补充原文未声明的组件、原因或参数；"
            "保留空字段，不要根据常识扩写；gate_type 不明确时保持 unknown。"
        ),
        "output_prefix": f"s210_eval_{sample.get('sample_id', 'unknown')}",
    }


def _request_prediction(api_url: str, sample: dict[str, Any], timeout: int) -> dict[str, Any]:
    payload = _build_request_payload(sample)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run(dataset: dict[str, Any], api_url: str, timeout: int, output: Path) -> dict[str, Any]:
    existing: dict[str, Any] = {"predictions": []}
    if output.exists():
        try:
            value = json.loads(output.read_text(encoding="utf-8"))
            if isinstance(value, dict) and isinstance(value.get("predictions"), list):
                existing = value
        except json.JSONDecodeError:
            pass
    by_id = {str(row.get("sample_id")): row for row in existing["predictions"] if isinstance(row, dict)}

    for index, sample in enumerate(dataset["samples"], start=1):
        sample_id = str(sample.get("sample_id", ""))
        if not sample_id:
            continue
        if by_id.get(sample_id, {}).get("status") == "success":
            print(f"[{index}/{len(dataset['samples'])}] skip {sample_id} (already succeeded)")
            continue
        started = time.perf_counter()
        try:
            prediction = _request_prediction(api_url, sample, timeout)
            row = {
                "sample_id": sample_id,
                "status": "success",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "prediction": prediction,
            }
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            row = {
                "sample_id": sample_id,
                "status": "http_error",
                "http_status": exc.code,
                "error": body[:1000],
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        except Exception as exc:  # preserve per-sample failure and continue
            row = {
                "sample_id": sample_id,
                "status": "runner_error",
                "error": f"{type(exc).__name__}: {exc}",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        by_id[sample_id] = row
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps({"predictions": list(by_id.values())}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[{index}/{len(dataset['samples'])}] {sample_id} {row['status']} {row.get('latency_ms')}ms")

    predictions = list(by_id.values())
    return {
        "samples": len(dataset["samples"]),
        "prediction_rows": len(predictions),
        "success": sum(row.get("status") == "success" for row in predictions),
        "failed": sum(row.get("status") != "success" for row in predictions),
        "output": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api/fta/generate")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(_load(args.dataset), args.api_url, max(1, args.timeout), args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
