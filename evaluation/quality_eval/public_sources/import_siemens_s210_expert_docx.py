#!/usr/bin/env python3
"""Import a completed SINAMICS S210 DOCX review checklist as a candidate dataset.

The imported data deliberately remains a review candidate.  The document's
``审核通过`` text is preserved, but it is not promoted to human-verified gold
without a verifiable reviewer identity and an explicit evidence-policy check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from docx import Document


FINAL_FIELD_MAP = {
    "故障码": "fault_code",
    "故障现象": "description",
    "主组件": "component",
    "关联组件": "related_components",
    "候选原因": "causes",
    "参数": "parameters",
    "gate_type": "gate_type",
}
EVIDENCE_FIELD_MAP = {
    "故障码": "fault_code",
    "故障现象": "description",
    "主组件": "primary_component",
    "关联组件": "related_component",
    "候选原因": "cause",
    "参数": "parameter",
}
KNOWN_RELATED_EVIDENCE_CONFLICTS = {
    "A01706": "最终关联组件为空，但证据栏填写了“The drive is stopped by message F01700.”，该句更像处置/反应上下文，不是关联组件声明。",
    "A01788": "最终关联组件为空，但证据栏填写了 STO 上下文；应改为无关联组件说明或移入故障现象/上下文证据。",
    "F30655": "最终关联组件为空，但证据栏填写了 DRIVE-CLiQ 通信故障上下文；应明确这是故障现象/原因证据，而不是关联组件证据。",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean(value: str) -> str:
    return value.replace("\r", "").strip()


def _table_rows(table: Any) -> list[list[str]]:
    return [[_clean(cell.text) for cell in row.cells] for row in table.rows]


def _parse_pair(final_table: Any, evidence_table: Any, index: int) -> dict[str, Any]:
    final_rows = _table_rows(final_table)
    evidence_rows = _table_rows(evidence_table)
    if not final_rows or final_rows[0][:2] != ["字段", "专家最终值"]:
        raise ValueError(f"record {index}: unexpected final-field table header: {final_rows[:1]}")
    if not evidence_rows or evidence_rows[0][:2] != ["字段", "原文引用"]:
        raise ValueError(f"record {index}: unexpected evidence table header: {evidence_rows[:1]}")

    final = {row[0]: row[1] for row in final_rows[1:] if len(row) >= 2 and row[0]}
    evidence = {
        row[0]: {"quote": row[1], "location": row[2] if len(row) >= 3 else ""}
        for row in evidence_rows[1:]
        if len(row) >= 2 and row[0]
    }
    fault_code = final.get("故障码", "")
    if not fault_code:
        raise ValueError(f"record {index}: missing fault code")
    if final.get("gate_type") != "unknown":
        raise ValueError(f"record {index} {fault_code}: gate_type must remain unknown")

    flags = []
    if fault_code in KNOWN_RELATED_EVIDENCE_CONFLICTS:
        flags.append(
            {
                "code": "related_component_evidence_conflict",
                "severity": "medium",
                "message": KNOWN_RELATED_EVIDENCE_CONFLICTS[fault_code],
            }
        )
    related_final = final.get("关联组件", "")
    related_evidence = evidence.get("关联组件", {}).get("quote", "")
    if related_final in {"无", "（空）", ""} and related_evidence in {
        "无明确关联组件",
        "原文未提及具体关联组件",
    }:
        flags.append(
            {
                "code": "negative_related_component_claim",
                "severity": "low",
                "message": "该字段是对原文未声明的判断，不是原文直接引文；正式金标时应保留为否定性审核结论。",
            }
        )

    final_fields = {
        FINAL_FIELD_MAP[key]: value
        for key, value in final.items()
        if key in FINAL_FIELD_MAP
    }
    evidence_fields = {
        EVIDENCE_FIELD_MAP[key]: value
        for key, value in evidence.items()
        if key in EVIDENCE_FIELD_MAP
    }
    return {
        "sample_id": f"SIEMENS_S210_2019_{fault_code}",
        "expert_final_fields": final_fields,
        "expert_evidence": evidence_fields,
        "review": {
            "decision": "审核通过",
            "review_note": "以原文为依据，各字段语义清晰、证据充分，审核通过。",
            "reviewer_role": None,
            "reviewer_name": None,
            "review_date": None,
            "human_expert_reviewed": False,
            "logic_status": "unknown",
        },
        "validation": {
            "flags": flags,
            "flag_count": len(flags),
            "document_record_index": index,
            "final_field_count": len(final_fields),
            "evidence_field_count": len(evidence_fields),
        },
    }


def parse_review_docx(path: Path) -> list[dict[str, Any]]:
    document = Document(path)
    if len(document.tables) % 2 != 0:
        raise ValueError(f"expected pairs of final/evidence tables, got {len(document.tables)}")
    return [
        _parse_pair(document.tables[index], document.tables[index + 1], index // 2 + 1)
        for index in range(0, len(document.tables), 2)
    ]


def _read_sample_dataset(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("samples"), list):
        raise ValueError("sample dataset must be an object with a samples list")
    return value


def build_candidate_dataset(review_docx: Path, sample_json: Path) -> dict[str, Any]:
    source = _read_sample_dataset(sample_json)
    imported = parse_review_docx(review_docx)
    sample_by_id = {sample["sample_id"]: sample for sample in source["samples"]}
    imported_ids = [record["sample_id"] for record in imported]
    expected_ids = [sample["sample_id"] for sample in source["samples"]]
    if len(imported) != len(expected_ids):
        raise ValueError(f"DOCX has {len(imported)} records; sample expects {len(expected_ids)}")
    if set(imported_ids) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(imported_ids))
        extra = sorted(set(imported_ids) - set(expected_ids))
        raise ValueError(f"record IDs do not match; missing={missing}, extra={extra}")

    records = []
    for imported_record in imported:
        sample = sample_by_id[imported_record["sample_id"]]
        records.append(
            {
                "sample_id": imported_record["sample_id"],
                "split": "external_expert_review_candidate",
                "source_type": "public_manual_fault_corpus",
                "input_text": sample["input_text"],
                "weak_record": sample["weak_record"],
                "expert_candidate": imported_record["expert_final_fields"],
                "evidence_candidate": imported_record["expert_evidence"],
                "review": imported_record["review"],
                "validation": imported_record["validation"],
                "provenance": {
                    **sample["provenance"],
                    "review_docx": review_docx.name,
                    "review_docx_sha256": _sha256(review_docx),
                },
            }
        )

    decision_counts = {"审核通过": 0, "证据不足": 0, "语义需修改": 0, "无法判断": 0}
    for record in records:
        decision_counts[record["review"]["decision"]] = decision_counts.get(record["review"]["decision"], 0) + 1
    flagged = sum(record["validation"]["flag_count"] > 0 for record in records)
    return {
        "dataset_info": {
            "name": "siemens_s210_public_expert_review_candidate",
            "version": "0.1.0",
            "label_status": "external_expert_review_candidate",
            "human_expert_reviewed": False,
            "training_policy": {
                "eligible_for_training": False,
                "reason": "DOCX 中未提供可验证的专家身份，且仍有证据字段对齐问题；确认前不得作为训练或正式金标。",
            },
            "selection": {"total": len(records), "message_type_counts": {"F": 20, "A": 8, "N": 2}},
            "review_rules": source["dataset_info"].get("review_rules", []),
            "logic_policy": "unknown_until_explicitly_expert_annotated",
            "review_document": {
                "file": review_docx.name,
                "sha256": _sha256(review_docx),
                "claimed_decision_counts": decision_counts,
                "reviewer_role": None,
                "reviewer_name": None,
                "review_date": None,
            },
            "validation_summary": {
                "records": len(records),
                "records_with_flags": flagged,
                "flags_total": sum(record["validation"]["flag_count"] for record in records),
                "known_flag_codes": sorted(
                    {flag["code"] for record in records for flag in record["validation"]["flags"]}
                ),
            },
        },
        "records": records,
    }


def render_candidate_report(dataset: dict[str, Any]) -> str:
    """Render a compact human-facing report without changing candidate labels."""

    info = dataset["dataset_info"]
    records = dataset["records"]
    flagged = [record for record in records if record["validation"]["flags"]]
    lines = [
        "# SINAMICS S210 外部专家审核候选集复核报告",
        "",
        "> 本报告只说明 DOCX 导入和结构化校验结果，不把候选标注升级为正式专家金标。",
        "",
        "## 导入结果",
        "",
        f"- 记录总数：{info['validation_summary']['records']}（F 20、A 8、N 2）",
        f"- DOCX 声明的审核通过数：{info['review_document']['claimed_decision_counts'].get('审核通过', 0)}",
        f"- 需要复核的记录：{info['validation_summary']['records_with_flags']}",
        f"- 疑点总数：{info['validation_summary']['flags_total']}",
        "- 当前标签：`external_expert_review_candidate`",
        "- 当前不可用于训练，也不作为正式 F1 金标",
        "",
        "## 必须确认的证据对齐问题",
        "",
        "| 样本 | 当前最终值 | 当前证据栏 | 处理建议 |",
        "|---|---|---|---|",
        "| A01706 | 关联组件=无 | The drive is stopped by message F01700 | 改为无关联组件的否定说明，或把该句移到故障上下文证据 |",
        "| A01788 | 关联组件=无 | STO 上下文 | 不要放在关联组件证据栏，改为故障现象/上下文证据 |",
        "| F30655 | 关联组件=无 | DRIVE-CLiQ 通信故障上下文 | 不要放在关联组件证据栏，改为故障现象/原因证据 |",
        "",
        "## 否定性关联组件说明",
        "",
        "以下记录最终值为无关联组件，证据栏使用了“无明确关联组件”等判断性文字。这不是错误，但正式金标中应明确标为否定性审核结论，而不是原文直接引文：",
        "",
    ]
    negative = [
        record["sample_id"].replace("SIEMENS_S210_2019_", "")
        for record in records
        if any(flag["code"] == "negative_related_component_claim" for flag in record["validation"]["flags"])
    ]
    lines.append(", ".join(negative) if negative else "无")
    lines.extend(["", "## 全部记录状态", "", "| 样本 | DOCX 结论 | 疑点 |", "|---|---|---|"])
    for record in records:
        sample_id = record["sample_id"].replace("SIEMENS_S210_2019_", "")
        flag_codes = ", ".join(flag["code"] for flag in record["validation"]["flags"]) or "无"
        lines.append(f"| {sample_id} | {record['review']['decision']} | {flag_codes} |")
    lines.extend(
        [
            "",
            "## 升级为正式金标的条件",
            "",
            "1. 补充并确认真实审核者身份、角色和审核日期。",
            "2. 明确处理 A01706、A01788、F30655 的证据字段归属。",
            "3. 确认所有组件字段是否允许根据标题/原因语义推断；若不允许，应补充直接组件声明证据。",
            "4. 完成后再生成 `human_expert_reviewed=true` 的正式外部金标，并使用独立模型输出计算 F1。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-docx", type=Path, required=True)
    parser.add_argument("--sample-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    dataset = build_candidate_dataset(args.review_docx, args.sample_json)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_candidate_report(dataset), encoding="utf-8")
    print(json.dumps(dataset["dataset_info"], ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output_json}")
    if args.output_md:
        print(f"[ok] wrote {args.output_md}")


if __name__ == "__main__":
    main()
