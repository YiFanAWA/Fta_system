#!/usr/bin/env python3
"""Import the completed 57-record Markdown review into a traceable dataset.

The source document is user-accepted as the project's expert review source.
The importer keeps the model extraction, evidence table, original text, review
decision, and corrected record side by side so the review is auditable.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DECISIONS = ("审核通过", "证据不足", "语义需修改", "无法判断")
EMPTY_VALUES = {"", "无", "（空）", "(空)", "None", "null"}

FIELD_LABELS = {
    "故障码": "fault_code",
    "主组件": "component",
    "关联组件": "related_components",
    "故障现象": "description",
    "候选原因": "causes",
    "参数": "parameters",
}

EVIDENCE_LABELS = {
    "故障码": "fault_code",
    "主组件": "primary_component",
    "关联组件": "related_component",
    "故障现象": "description",
    "候选原因": "cause",
    "参数": "parameter",
}

# These are explicit corrections written in the attached review document. They
# are data import facts, not runtime extraction rules. The original model value
# remains available in every sample under model_prediction.
CORRECTION_OVERRIDES: dict[str, dict[str, Any]] = {
    "PH-A01013": {
        "causes": ["500小时后达到风扇使用寿命", "超过50000小时使用寿命"],
    },
    "PH-F01600": {
        "causes": [
            "另一个监控通道发出停止请求",
            "控制定时器届满",
            "PROFIsafe控制故障",
        ],
    },
    "PH-F01641": {"causes": ["组件更换（含传感器更换）"]},
    "PH-F01033": {"causes": ["参考参数值为0.0"]},
    "SIEMENS_S210_2019_F01000": {"component": None},
    "SIEMENS_S210_2019_F01023": {"component": None},
    "SIEMENS_S210_2019_F01042": {"component": None},
    "SIEMENS_S210_2019_N01004": {"component": None},
}


def _split_md_row(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    parts = re.split(r"(?<!\\)\|", value)
    return [part.strip().replace("\\|", "|") for part in parts]


def _clean(value: str) -> str:
    return value.replace("\r", "").strip()


def _scalar(value: str) -> str | None:
    value = _clean(value)
    return None if value in EMPTY_VALUES else value


def _items(value: str) -> list[str]:
    value = _clean(value)
    if value in EMPTY_VALUES:
        return []
    return [item.strip() for item in value.split("、") if item.strip()]


def _table_rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        parts = _split_md_row(line)
        if not parts or all(set(part) <= {"-", ":", " "} for part in parts):
            continue
        rows.append(parts)
    # The Markdown separator row is filtered above, so only the header row
    # remains before the data rows.
    return rows[1:] if len(rows) >= 2 else []


def _section_text(text: str) -> list[tuple[str, str, str]]:
    matches = list(
        re.finditer(
            r"(?ms)^## (\d{2})\. ([^\r\n]+)\r?\n(.*?)(?=^## \d{2}\. |\Z)",
            text,
        )
    )
    return [(match.group(1), match.group(2).strip(), match.group(3)) for match in matches]


def _extract_between(section: str, start: str, end: str) -> str:
    match = re.search(
        rf"(?ms)^### {re.escape(start)}.*?\r?\n(.*?)(?=^### {re.escape(end)}|\Z)",
        section,
    )
    return match.group(1) if match else ""


def _parse_evidence(block: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for row in _table_rows(block):
        if len(row) < 5 or row[0] == "-":
            continue
        field_label, quote, location, source = row[1], row[2], row[3], row[4]
        field = EVIDENCE_LABELS.get(field_label, field_label)
        coordinates = re.search(r"(\d+)\s*[-–]\s*(\d+)", location)
        item: dict[str, Any] = {
            "field": field,
            "source_id": source or "input_text",
            "quote": quote,
            "location": location,
        }
        if coordinates:
            item["start"] = int(coordinates.group(1))
            item["end"] = int(coordinates.group(2))
        evidence.append(item)
    return evidence


def _parse_record(sequence: str, sample_id: str, section: str) -> dict[str, Any]:
    source_match = re.search(r"数据来源：([^；\r\n]+)；原文来源：([^\r\n]+)", section)
    dataset = source_match.group(1).strip() if source_match else "未知来源"
    source_file = source_match.group(2).strip() if source_match else ""

    model_block = _extract_between(section, "A. 模型抽取结果", "B. 抽取证据")
    model_values: dict[str, str] = {}
    for row in _table_rows(model_block):
        if len(row) >= 2 and row[0] in FIELD_LABELS:
            model_values[FIELD_LABELS[row[0]]] = row[1]

    model_record = {
        "fault_code": _scalar(model_values.get("fault_code", "")),
        "component": _scalar(model_values.get("component", "")),
        "related_components": _items(model_values.get("related_components", "")),
        "description": _scalar(model_values.get("description", "")),
        "causes": _items(model_values.get("causes", "")),
        "parameters": _items(model_values.get("parameters", "")),
        "gate_type": None,
    }

    evidence_block = _extract_between(section, "B. 抽取证据", "C. 原文")
    evidence = _parse_evidence(evidence_block)
    source_match = re.search(r"(?ms)^### C\. 原文.*?```text\r?\n(.*?)\r?\n```", section)
    input_text = source_match.group(1) if source_match else ""

    review_match = re.search(r"(?m)^- 审核结论：(.*)$", section)
    conclusion_line = review_match.group(1) if review_match else ""
    decision = next(
        (decision for decision in DECISIONS if f"☑ {decision}" in conclusion_line),
        "未填写",
    )
    field_match = re.search(r"(?m)^- 需修改字段：([^\r\n]*)", section)
    modified_match = re.search(r"(?m)^- 修改后内容：([^\r\n]*)", section)
    opinion_match = re.search(r"(?m)^- 专家意见：([^\r\n]*)", section)
    reviewer_match = re.search(r"(?m)^- 专家姓名：([^\r\n]*)", section)
    date_match = re.search(r"(?m)^- 审核日期：([^\r\n]*)", section)
    review = {
        "decision": decision,
        "fields_to_modify": _scalar(field_match.group(1) if field_match else ""),
        "modified_content": _scalar(modified_match.group(1) if modified_match else ""),
        "opinion": _scalar(opinion_match.group(1) if opinion_match else ""),
        "reviewer_name": _scalar(reviewer_match.group(1) if reviewer_match else ""),
        "review_date": _scalar(date_match.group(1) if date_match else ""),
        "source_sequence": int(sequence),
    }

    reviewed_record = dict(model_record)
    reviewed_record.update(CORRECTION_OVERRIDES.get(sample_id, {}))
    review["correction_applied"] = sample_id in CORRECTION_OVERRIDES
    review["correction_override"] = CORRECTION_OVERRIDES.get(sample_id, {})
    review["accepted_as_expert_by_user"] = True

    source_kind = "project_handbook" if "项目手册" in dataset else "public_s210_manual"
    return {
        "sample_id": sample_id,
        "sequence": int(sequence),
        "split": "test",
        "source_type": source_kind,
        "source_file": source_file,
        "input_text": input_text,
        "model_prediction": {
            "record": model_record,
            "evidence_spans": evidence,
        },
        "gold_records": [reviewed_record],
        "gold_relations": [],
        "logic_status": "unknown",
        "evidence_spans": evidence,
        "expert_review": review,
        "review_history": [
            {
                "stage": "user_accepted_expert_review",
                "decision": decision,
                "reviewer_name": review["reviewer_name"],
                "review_date": review["review_date"],
                "fields_to_modify": review["fields_to_modify"],
                "modified_content": review["modified_content"],
            }
        ],
        "provenance": {
            "source_document": "FTA_故障记录专家审核清单_57条_专家逐条已审核完整版.md",
            "source_document_role": "用户指定的专家审核来源",
            "source_file_declared": source_file,
        },
    }


def import_review(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    sections = _section_text(text)
    if len(sections) != 57:
        raise ValueError(f"expected 57 records, found {len(sections)}")
    records = [_parse_record(sequence, sample_id, section) for sequence, sample_id, section in sections]
    decisions = Counter(record["expert_review"]["decision"] for record in records)
    if set(decisions) - set(DECISIONS):
        raise ValueError(f"unexpected decisions: {sorted(set(decisions) - set(DECISIONS))}")

    reviewer_names = {record["expert_review"]["reviewer_name"] for record in records}
    review_dates = {record["expert_review"]["review_date"] for record in records}
    dataset_info = {
        "name": "fta_unified_expert_review_57",
        "version": "v1-user-accepted-expert-2026-09-20",
        "task": "unified_fault_record_extraction_expert_review",
        "label_status": "user_accepted_expert_reviewed",
        "human_expert_reviewed": True,
        "accepted_as_expert_by_user": True,
        "source_document": str(path),
        "reviewer_names": sorted(reviewer_names),
        "review_dates": sorted(review_dates),
        "decision_counts": {decision: decisions.get(decision, 0) for decision in DECISIONS},
        "total": len(records),
        "project_records": sum(record["source_type"] == "project_handbook" for record in records),
        "public_records": sum(record["source_type"] == "public_s210_manual" for record in records),
        "correction_count": sum(record["expert_review"]["correction_applied"] for record in records),
        "logic_gate_confirmed": False,
    }
    unresolved = decisions.get("无法判断", 0) or decisions.get("证据不足", 0)
    return {
        "dataset_info": dataset_info,
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
                "description",
                "cause",
                "parameter",
            ],
            "logic_policy": "unknown_until_explicitly_expert_annotated",
        },
        "gold_status": {
            "expert_reviewed": True,
            "accepted_as_expert_by_user": True,
            "f1_ready": unresolved == 0,
            "f1_blocker": (
                "仍有无法判断或证据不足记录；先保留审核结果和修正建议，再决定是否纳入严格 F1。"
                if unresolved
                else None
            ),
            "f1_scope": "字段抽取与证据；不包含 AND/OR 逻辑门",
            "not_for_training": True,
        },
        "samples": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = import_review(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), **dataset["dataset_info"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
