#!/usr/bin/env python3
"""Finalize a gold dataset from an independent expert annotation report."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DECISIONS = {"审核通过", "证据不足", "语义需修改", "无法判断"}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def finalize_dataset(
    provisional: dict[str, Any],
    annotations: dict[str, Any],
    *,
    source_annotation: str,
) -> dict[str, Any]:
    info = annotations.get("annotation_info") or {}
    if info.get("independent_of_model_gold") is not True:
        raise ValueError("independent annotation must explicitly declare independence")
    if info.get("field_values_confirmed") is not True:
        raise ValueError("expert annotation must confirm field values")
    if info.get("evidence_confirmed") is not True:
        raise ValueError("expert annotation must confirm evidence")

    samples = provisional.get("samples")
    decisions = annotations.get("decisions")
    if not isinstance(samples, list) or not isinstance(decisions, dict):
        raise ValueError("invalid provisional dataset or annotation decisions")
    sample_ids = {str(sample.get("sample_id")) for sample in samples}
    decision_ids = set(decisions)
    if sample_ids != decision_ids:
        raise ValueError(
            f"annotation/sample mismatch: missing={sorted(sample_ids - decision_ids)}, "
            f"extra={sorted(decision_ids - sample_ids)}"
        )

    final = deepcopy(provisional)
    dataset_info = final.setdefault("dataset_info", {})
    dataset_info["version"] = "2.0.0"
    dataset_info["label_status"] = "human_expert_reviewed"
    dataset_info["human_expert_reviewed"] = True
    dataset_info["description"] = (
        "项目手册故障记录的独立领域专家审核金标；保留原文、模型输出、证据和审核历史。"
    )
    dataset_info["review"] = {
        "review_version": info.get("report_file"),
        "review_date": info.get("review_date"),
        "reviewer_role": info.get("reviewer_role"),
        "reviewer_name": info.get("reviewer_name"),
        "source_report": source_annotation,
        "independent_of_model_gold": True,
        "field_values_confirmed": True,
        "evidence_confirmed": True,
        "logic_gate_confirmed": bool(info.get("logic_gate_confirmed")),
        "decision_counts": {decision: 0 for decision in sorted(DECISIONS)},
    }
    dataset_info["review"]["decision_counts"] = {
        decision: sum(1 for item in decisions.values() if item.get("decision") == decision)
        for decision in sorted(DECISIONS)
    }
    dataset_info["training_policy"] = {
        "eligible_for_training": False,
        "reason": "已用于独立测试金标；不得混入训练集。",
    }

    for sample in final["samples"]:
        sample_id = str(sample["sample_id"])
        annotation = decisions[sample_id]
        decision = annotation.get("decision")
        if decision not in DECISIONS:
            raise ValueError(f"{sample_id} has invalid decision: {decision}")
        review = sample.setdefault("expert_review", {})
        previous_decision = review.get("decision")
        review.update(
            {
                "decision": decision,
                "pre_correction_decision": previous_decision,
                "reviewer_role": info.get("reviewer_role"),
                "reviewer_name": info.get("reviewer_name"),
                "review_date": info.get("review_date"),
                "review_version": info.get("report_file"),
                "basis": [
                    "5条核心审核规则",
                    "v1问题领域修复追踪",
                    "独立领域专家审核结论报告",
                ],
                "correction_applied": bool(annotation.get("corrected_fields")),
                "correction_summary": annotation.get("review_note"),
                "corrected_fields": list(annotation.get("corrected_fields") or []),
                "independent_review": True,
                "field_values_confirmed": True,
                "evidence_confirmed": True,
            }
        )
        history = list(sample.get("review_history") or [])
        history.append(
            {
                "stage": "independent_expert_review",
                "decision": decision,
                "review_version": info.get("report_file"),
                "review_note": annotation.get("review_note"),
                "corrected_fields": list(annotation.get("corrected_fields") or []),
            }
        )
        sample["review_history"] = history

    final["gold_status"] = {
        "independent_expert_reviewed": True,
        "source_annotation": source_annotation,
        "logic_status": info.get("logic_status", "unknown"),
        "not_for_training": True,
        "f1_ready": True,
        "f1_scope": "字段抽取与证据；不包含AND/OR逻辑门",
    }
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provisional", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    final = finalize_dataset(
        _read_json(args.provisional),
        _read_json(args.annotations),
        source_annotation=str(args.annotations),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] wrote {args.output} samples={len(final['samples'])}")


if __name__ == "__main__":
    main()
