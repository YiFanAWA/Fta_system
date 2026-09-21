#!/usr/bin/env python3
"""Apply the three confirmed evidence reclassifications and build reviewed data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from docx import Document


CONFIRMED_RECLASSIFICATIONS = {
    "A01706": {
        "target_field": "reaction_context",
        "action": "move_from_related_component_evidence",
        "summary": "驱动器被 F01700 停止属于故障反应/上下文，不属于关联组件。",
    },
    "A01788": {
        "target_field": "cause_context",
        "action": "move_from_related_component_evidence",
        "summary": "STO 是安全功能并在原文中作为故障原因上下文出现，不属于关联组件。",
    },
    "F30655": {
        "target_field": "cause_context",
        "action": "move_from_related_component_evidence",
        "summary": "DRIVE-CLiQ 通信错误在原文中是故障原因，不属于关联组件。",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _base_text(value: str) -> str:
    """Remove the bilingual translation while retaining the source-language value."""

    value = value.strip()
    value = re.split(r"\s*\|\s*（", value, maxsplit=1)[0]
    value = re.split(r"\n\s*（", value, maxsplit=1)[0]
    return value.strip()


def _split_values(value: str, *, none_values: set[str] | None = None) -> list[str]:
    value = _base_text(value)
    if not value or value in (none_values or {"无", "（空）"}):
        return []
    return [item.strip() for item in re.split(r"、|\n", value) if item.strip()]


def _find_quote(source: str, quote: str) -> tuple[int, int] | None:
    quote = _base_text(quote).replace("\r", "")
    if not quote or quote in {"无明确关联组件", "原文未提及具体关联组件", "原文未提及具体参数", "无"}:
        return None
    start = source.find(quote)
    if start >= 0:
        return start, start + len(quote)
    compact_source = source.replace("\n", "")
    compact_quote = quote.replace("\n", "")
    compact_start = compact_source.find(compact_quote)
    if compact_start < 0:
        return None
    # Character offsets are intentionally omitted when line-break normalization
    # changes the source coordinate system.
    return None


def _validate_confirmation_docx(path: Path) -> None:
    document = Document(path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    for code in CONFIRMED_RECLASSIFICATIONS:
        if code not in text:
            raise ValueError(f"confirmation DOCX does not contain {code}")
    if text.count("移到故障上下文") < 3:
        raise ValueError("confirmation DOCX does not contain three move-to-context conclusions")
    for code in CONFIRMED_RECLASSIFICATIONS:
        match = re.search(rf"{code}.*?关联组件最终值：无", text, flags=re.S)
        if not match:
            raise ValueError(f"confirmation DOCX does not confirm empty related component for {code}")


def _build_evidence_spans(record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    source = record["input_text"]
    evidence = record["evidence_candidate"]
    spans: list[dict[str, Any]] = []
    notes: list[str] = []
    field_map = {
        "fault_code": "fault_code",
        "description": "description",
        "primary_component": "primary_component",
        "related_component": "related_component",
        "cause": "cause",
        "parameter": "parameter",
    }
    for key, field in field_map.items():
        entry = evidence.get(key)
        if not entry:
            continue
        quote = entry.get("quote", "")
        coordinates = _find_quote(source, quote)
        if coordinates is None:
            notes.append(f"{key}:未能在输入原文中直接定位证据，保留页码/位置={entry.get('location', '')}")
            continue
        start, end = coordinates
        spans.append(
            {
                "field": field,
                "source_id": "input_text",
                "quote": _base_text(quote),
                "start": start,
                "end": end,
                "location": entry.get("location", ""),
            }
        )
    return spans, notes


def build_reviewed_dataset(
    candidate: dict[str, Any],
    confirmation_docx: Path,
    *,
    reviewer_name: str | None = None,
    review_date: str | None = None,
) -> dict[str, Any]:
    _validate_confirmation_docx(confirmation_docx)
    records = []
    for candidate_record in candidate["records"]:
        code = candidate_record["weak_record"]["fault_code"]
        expert = candidate_record["expert_candidate"]
        corrected = dict(candidate_record["evidence_candidate"])
        old_related = corrected.get("related_component")
        confirmation = None
        if code in CONFIRMED_RECLASSIFICATIONS:
            rule = CONFIRMED_RECLASSIFICATIONS[code]
            confirmation = {
                **rule,
                "original_evidence": old_related,
                "related_components_final": [],
            }
            corrected["related_component"] = {
                "quote": "原文未明确声明关联组件",
                "location": old_related.get("location", "") if old_related else "",
                "evidence_type": "negative_assertion",
                "source_quote": None,
            }
        spans, evidence_notes = _build_evidence_spans(
            {**candidate_record, "evidence_candidate": corrected}
        )
        final_record = {
            "sample_id": candidate_record["sample_id"],
            "split": "test",
            "source_type": "public_manual_expert_reviewed",
            "input_text": candidate_record["input_text"],
            "gold_records": [
                {
                    "fault_code": _base_text(expert.get("fault_code", "")),
                    "component": None if _base_text(expert.get("component", "")) in {"", "无", "（空）"} else _base_text(expert.get("component", "")),
                    "related_components": _split_values(expert.get("related_components", "")),
                    "description": _base_text(expert.get("description", "")),
                    "causes": _split_values(expert.get("causes", ""), none_values={"", "无", "（空）"}),
                    "parameters": _split_values(expert.get("parameters", "")),
                    "gate_type": None,
                }
            ],
            "gold_relations": [],
            "logic_status": "unknown",
            "evidence_spans": spans,
            "evidence_notes": evidence_notes,
            "reviewed_fields_raw": expert,
            "reviewed_evidence_raw": corrected,
            "expert_review": {
                "decision": "审核通过",
                "reviewer_role": "领域专家（文档声明）",
                "reviewer_name": reviewer_name,
                "review_date": review_date,
                "review_document": confirmation_docx.name,
                "review_document_sha256": _sha256(confirmation_docx),
                "identity_verified": False,
                "confirmation_applied": confirmation is not None,
                "reclassification": confirmation,
            },
            "review_history": [
                {
                    "stage": "external_expert_confirmation",
                    "decision": "审核通过",
                    "review_document": confirmation_docx.name,
                    "reclassification": confirmation,
                }
            ],
            "provenance": candidate_record["provenance"],
        }
        records.append(final_record)

    return {
        "dataset_info": {
            "name": "siemens_s210_public_fault_expert_gold",
            "version": "1.0.0",
            "language": "en with bilingual expert annotations",
            "task": "expert_reviewed_public_fault_record_extraction",
            "label_status": "human_expert_reviewed",
            "human_expert_reviewed": True,
            "training_policy": {
                "eligible_for_training": False,
                "reason": "独立公开手册测试金标；当前样本仅用于测试/评估，不用于训练。",
            },
            "review": {
                "review_document": confirmation_docx.name,
                "reviewer_role": "领域专家",
                "reviewer_name": reviewer_name,
                "review_date": review_date,
                "identity_verified": bool(reviewer_name and review_date),
                "decision_counts": {"审核通过": len(records), "证据不足": 0, "语义需修改": 0, "无法判断": 0},
                "field_values_confirmed": True,
                "evidence_confirmed": True,
                "logic_gate_confirmed": False,
            },
            "source": {
                "dataset": "siemens_s210_public_fault_corpus_v1",
                "review_sample": "siemens_s210_public_fault_expert_review_sample_v1",
                "review_confirmation_document": confirmation_docx.name,
            },
            "stats": {
                "total": len(records),
                "split": {"test": len(records)},
                "with_evidence": sum(bool(record["evidence_spans"]) for record in records),
                "with_unknown_logic_gate": len(records),
                "confirmed_reclassifications": len(CONFIRMED_RECLASSIFICATIONS),
            },
        },
        "label_schema": {
            "record_fields": ["fault_code", "component", "related_components", "description", "causes", "parameters", "gate_type"],
            "evidence_fields": ["fault_code", "primary_component", "related_component", "description", "cause", "parameter"],
            "logic_policy": "unknown_until_explicitly_expert_annotated",
            "negative_evidence_policy": "no_direct_quote_when_field_is_not_declared; preserve negative_assertion note",
        },
        "gold_status": {
            "independent_expert_reviewed": True,
            "reviewer_identity_verified": bool(reviewer_name and review_date),
            "not_for_training": True,
            "f1_ready": False,
            "f1_blocker": "严格 F1 目前仅作为诊断结果；正式 F1 还需要先统一组件字段的双语表达，并明确原因字段的拆分/改写匹配规则。",
            "f1_scope": "字段抽取与证据；不包含 AND/OR 逻辑门",
        },
        "samples": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--confirmation-docx", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--reviewer-name")
    parser.add_argument("--review-date")
    args = parser.parse_args()
    dataset = build_reviewed_dataset(
        _load_json(args.candidate_json),
        args.confirmation_docx,
        reviewer_name=args.reviewer_name,
        review_date=args.review_date,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dataset["dataset_info"], ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output_json}")


if __name__ == "__main__":
    main()
