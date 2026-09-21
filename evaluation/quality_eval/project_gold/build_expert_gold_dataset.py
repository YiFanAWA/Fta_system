#!/usr/bin/env python3
"""Build the reviewed project-handbook gold dataset from the final bundle.

The expert review is a data boundary: this script copies the final reviewed
record projection, preserves the model prediction and evidence history, and
never infers an FTA gate or causal relation that the expert did not confirm.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DATASET_VERSION = "1.1.0-provisional"
LABEL_STATUS = "project_reviewed_provisional"
REVIEW_DATE = "2026-09-19"
REVIEW_VERSION = "v9"

_PRE_CORRECTION_DECISIONS = {
    "PH-F01600": "语义需修改",
    "PH-A01631": "证据不足",
    "PH-A01006": "证据不足",
}

_CORRECTIONS = {
    "PH-F01600": {
        "summary": "将候选原因恢复为与原文严格一致的“交叉比较数据编号”。",
        "fields": ["causes"],
    },
    "PH-A01631": {
        "summary": "将两条条件原因恢复为原文逻辑词“且”，并将共用的 SBC 证据合并为一条共享证据。",
        "fields": ["causes", "evidence_spans"],
    },
    "PH-A01006": {
        "summary": "将“编码器模块”证据定位到驱动对象声明中的跨换行文本。",
        "fields": ["evidence_spans"],
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _reviewed_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "fault_code": record.get("fault_code"),
        "component": (record.get("component") or None),
        "related_components": list(record.get("related_components") or []),
        "description": record.get("description") or "",
        "causes": list(record.get("causes") or []),
        "parameters": list(record.get("parameters") or []),
        "gate_type": None,
    }


def _validate_sample(sample: dict[str, Any]) -> dict[str, Any]:
    sample_id = str(sample.get("sample_id") or "").strip()
    if not sample_id:
        raise ValueError("bundle sample is missing sample_id")
    prediction = sample.get("prediction")
    if not isinstance(prediction, dict):
        raise ValueError(f"{sample_id} has no prediction")
    records = prediction.get("records")
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError(f"{sample_id} must contain exactly one extracted record")
    audit = sample.get("evidence_audit") or {}
    if audit.get("issues") or audit.get("total") != audit.get("valid"):
        raise ValueError(f"{sample_id} has invalid evidence audit: {audit}")
    return prediction


def build_gold_dataset(
    bundle: dict[str, Any],
    *,
    source_bundle: str,
    review_date: str = REVIEW_DATE,
    review_version: str = REVIEW_VERSION,
) -> dict[str, Any]:
    samples = bundle.get("samples")
    if not isinstance(samples, list) or len(samples) != 27:
        raise ValueError("the final expert bundle must contain exactly 27 samples")
    if bundle.get("warnings"):
        raise ValueError(f"the final expert bundle contains warnings: {bundle['warnings']}")

    gold_samples: list[dict[str, Any]] = []
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError("bundle samples must be objects")
        prediction = _validate_sample(sample)
        sample_id = str(sample["sample_id"])
        records = prediction["records"]
        reviewed_records = [_reviewed_record(records[0])]
        pre_decision = _PRE_CORRECTION_DECISIONS.get(sample_id, "审核通过")
        correction = _CORRECTIONS.get(sample_id)
        evidence_spans = list(prediction.get("evidence_spans") or [])

        gold_samples.append(
            {
                "sample_id": sample_id,
                "split": "test",
                "source_type": "project_handbook_expert_gold",
                "input_text": sample.get("input_text") or "",
                "gold_top_event": None,
                "gold_records": reviewed_records,
                "gold_relations": [],
                "logic_status": "unknown",
                "evidence_spans": evidence_spans,
                "model_prediction": prediction,
                "expert_review": {
                    "decision": "审核通过",
                    "pre_correction_decision": pre_decision,
                    "reviewer_role": "项目审核（待领域专家独立复核）",
                    "reviewer_name": None,
                    "review_date": review_date,
                    "review_version": review_version,
                    "basis": [
                        "5条核心审核规则",
                        "v1问题领域修复追踪",
                        "专家审核报告及后续修正确认",
                    ],
                    "correction_applied": correction is not None,
                    "correction_summary": correction["summary"] if correction else None,
                    "corrected_fields": correction["fields"] if correction else [],
                },
                "review_history": [
                    {
                        "stage": "pre_correction_expert_review",
                        "decision": pre_decision,
                        "review_version": "v7",
                    },
                    {
                        "stage": "final_correction_confirmation",
                        "decision": "审核通过",
                        "review_version": review_version,
                    },
                ]
                if correction
                else [
                    {
                        "stage": "final_expert_review",
                        "decision": "审核通过",
                        "review_version": review_version,
                    }
                ],
                "provenance": {
                    "source_dataset": (sample.get("source") or {}).get(
                        "dataset", "project_manual_handbook_sample"
                    ),
                    "source_file": (sample.get("source") or {}).get("source_file"),
                    "source_sha256": (sample.get("source") or {}).get("source_sha256"),
                    "source_record_range": {
                        "start": (sample.get("source") or {}).get("source_char_start"),
                        "end": (sample.get("source") or {}).get("source_char_end"),
                    },
                    "review_bundle": source_bundle,
                },
            }
        )

    return {
        "dataset_info": {
            "name": "fta_project_handbook_expert_gold",
            "version": DATASET_VERSION,
            "language": "zh-CN",
            "task": "expert_reviewed_fault_record_extraction",
            "description": "项目手册故障记录的项目审核中间集；保留原文、模型输出、证据和审核历史，待独立领域专家复核。",
            "created_at": review_date,
            "owner": "project_evaluation",
            "label_status": LABEL_STATUS,
            "human_expert_reviewed": False,
            "training_policy": {
                "eligible_for_training": False,
                "reason": "项目手册样本全部保留在test，避免原文泄漏；可作为项目域测试金标。",
            },
            "review": {
                "review_version": review_version,
                "review_date": review_date,
                "reviewer_role": "项目审核（待领域专家独立复核）",
                "reviewer_name": None,
                "decision_counts": {
                    "审核通过": 27,
                    "语义需修改": 0,
                    "证据不足": 0,
                    "无法判断": 0,
                },
            },
            "source": {
                "dataset": "project_manual_handbook_sample",
                "file": "backend-python/examples/manual_handbook_sample.txt",
                "sha256": "39ab0e1c79ae9c0d3aa25bf717aeba2b41c114d4492a4c2653dce53e2a897627",
            },
            "stats": {
                "total": len(gold_samples),
                "split": {"test": len(gold_samples)},
                "with_evidence": sum(bool(item["evidence_spans"]) for item in gold_samples),
                "with_related_components": sum(
                    bool(item["gold_records"][0]["related_components"])
                    for item in gold_samples
                ),
                "with_unknown_logic_gate": sum(
                    item["logic_status"] == "unknown" for item in gold_samples
                ),
            },
        },
        "label_schema": {
            "record_fields": [
                "fault_code",
                "component",
                "related_components",
                "description",
                "causes",
                "parameters",
                "gate_type",
            ],
            "evidence_fields": [
                "fault_code",
                "primary_component",
                "related_component",
                "component_declaration",
                "driver_object_declaration",
                "description",
                "cause",
                "parameter",
            ],
            "logic_policy": "unknown_until_explicitly_expert_annotated",
        },
        "source_bundle": source_bundle,
        "samples": gold_samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the expert-reviewed FTA gold dataset")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-date", default=REVIEW_DATE)
    parser.add_argument("--review-version", default=REVIEW_VERSION)
    args = parser.parse_args()

    dataset = build_gold_dataset(
        _read_json(args.bundle),
        source_bundle=str(args.bundle),
        review_date=args.review_date,
        review_version=args.review_version,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] wrote {args.output} samples={len(dataset['samples'])}")


if __name__ == "__main__":
    main()
