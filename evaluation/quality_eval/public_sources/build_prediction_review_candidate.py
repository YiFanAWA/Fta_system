#!/usr/bin/env python3
"""Merge saved model predictions into an auditable pending-review dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _prediction_records(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    prediction = row.get("prediction") if isinstance(row.get("prediction"), dict) else {}
    extracted = prediction.get("extracted_faults")
    records = extracted.get("records") if isinstance(extracted, dict) else None
    if not isinstance(records, list):
        return ()
    return tuple(item for item in records if isinstance(item, dict))


def _prediction_evidence(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    prediction = row.get("prediction") if isinstance(row.get("prediction"), dict) else {}
    extracted = prediction.get("extracted_faults")
    spans = extracted.get("evidence_spans") if isinstance(extracted, dict) else None
    if not isinstance(spans, list):
        return ()
    return tuple(item for item in spans if isinstance(item, dict))


def _audit_evidence(sample: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    source = str(sample.get("input_text", ""))
    invalid: list[dict[str, Any]] = []
    for span in _prediction_evidence(row):
        start = span.get("start")
        end = span.get("end")
        quote = span.get("quote")
        if not isinstance(start, int) or not isinstance(end, int) or not isinstance(quote, str):
            invalid.append({"span": span, "reason": "invalid_shape"})
            continue
        if start < 0 or end <= start or source[start:end] != quote:
            invalid.append({"span": span, "reason": "does_not_match_input"})
    return {
        "status": "valid" if not invalid else "invalid",
        "span_count": len(_prediction_evidence(row)),
        "invalid_span_count": len(invalid),
        "invalid_spans": invalid,
    }


def build_candidate_dataset(
    sample_dataset: dict[str, Any],
    prediction_run: dict[str, Any],
    *,
    prediction_run_name: str = "unknown_prediction_run",
) -> dict[str, Any]:
    samples = sample_dataset.get("samples")
    prediction_rows = prediction_run.get("predictions")
    if not isinstance(samples, list) or not isinstance(prediction_rows, list):
        raise ValueError("sample dataset and prediction run must contain lists")
    by_id = {str(row.get("sample_id")): row for row in prediction_rows if isinstance(row, dict)}
    output_samples: list[dict[str, Any]] = []
    for sample in samples:
        sample_id = str(sample.get("sample_id", ""))
        row = by_id.get(sample_id)
        if row is None:
            raise ValueError(f"missing prediction row for {sample_id}")
        status = str(row.get("status", "missing"))
        evidence_audit = _audit_evidence(sample, row) if status == "success" else {
            "status": "missing",
            "span_count": 0,
            "invalid_span_count": 0,
            "invalid_spans": [],
        }
        item = dict(sample)
        item["split"] = "expert_review_candidate"
        item["model_prediction"] = {
            "status": status,
            "record_count": len(_prediction_records(row)),
            "records": list(_prediction_records(row)),
            "evidence_spans": list(_prediction_evidence(row)),
            "latency_ms": row.get("latency_ms"),
            "error": row.get("error"),
        }
        item["review_queue"] = {
            "status": "pending",
            "reason": "awaiting_expert_confirmation",
            "decision": None,
            "reviewer": None,
            "review_date": None,
            "evidence_audit": evidence_audit,
        }
        output_samples.append(item)

    return {
        "dataset_info": {
            "name": "siemens_s210_public_fault_review_candidate",
            "version": "2026-09-20",
            "label_status": "model_prediction_pending_expert_review",
            "human_expert_reviewed": False,
            "eligible_for_training": False,
            "logic_policy": "unknown_until_explicitly_expert_annotated",
            "source_sample_dataset": sample_dataset.get("dataset_info", {}).get("name"),
            "prediction_run": prediction_run_name,
            "stats": {
                "samples": len(output_samples),
                "prediction_success": sum(
                    item["model_prediction"]["status"] == "success" for item in output_samples
                ),
                "evidence_valid": sum(
                    item["review_queue"]["evidence_audit"]["status"] == "valid"
                    for item in output_samples
                ),
                "review_pending": len(output_samples),
            },
        },
        "samples": output_samples,
    }


def render_report(dataset: dict[str, Any]) -> str:
    info = dataset["dataset_info"]
    lines = [
        "# SINAMICS S210 第二批模型抽取待审核清单",
        "",
        "> 本文件包含模型候选结果和证据，不是专家金标，不提供预审通过结论。",
        "> 专家必须以每条记录的原文为依据，独立填写最终字段、证据和审核结论。",
        "",
        f"- 样本数：{info['stats']['samples']}",
        f"- 模型抽取成功：{info['stats']['prediction_success']}",
        f"- 证据位置通过结构校验：{info['stats']['evidence_valid']}",
        f"- 待审核：{info['stats']['review_pending']}",
        "",
    ]
    for index, sample in enumerate(dataset["samples"], start=1):
        model = sample["model_prediction"]
        records = model["records"]
        lines.extend(
            [
                f"## {index:02d}. {sample['sample_id']}",
                "",
                f"- 模型状态：{model['status']}",
                f"- 模型记录数：{model['record_count']}",
                "",
                "### 模型抽取结果",
                "",
                "```json",
                json.dumps(records, ensure_ascii=False, indent=2),
                "```",
                "",
                "### 原文",
                "",
                "```text",
                str(sample.get("input_text", "")).rstrip(),
                "```",
                "",
                "### 专家审核",
                "",
                "审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）",
                "",
                "审核意见：",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-json", type=Path, required=True)
    parser.add_argument("--predictions-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--prediction-run-name", required=True)
    args = parser.parse_args()
    dataset = build_candidate_dataset(
        _load(args.sample_json),
        _load(args.predictions_json),
        prediction_run_name=args.prediction_run_name,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_report(dataset), encoding="utf-8")
    print(json.dumps(dataset["dataset_info"]["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
