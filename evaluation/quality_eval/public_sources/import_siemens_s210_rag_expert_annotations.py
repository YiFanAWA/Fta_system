"""Import expert Markdown annotations into the evidence-first RAG bundle."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


ROW_RE = re.compile(r"^\s*(RAG-\d+)\s+(.+?)\s*$")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def parse_rows(*texts: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for text in texts:
        for raw_line in text.splitlines():
            match = ROW_RE.match(raw_line)
            if not match:
                continue
            query_id, remainder = match.groups()
            values = remainder.split()
            if len(values) < 7:
                continue
            row = {
                "fault_identification": values[0],
                "cause_correctness": values[1],
                "remedy_correctness": values[2],
                "citation_support": values[3],
                "unsupported_claims": values[4],
                "cross_fault_contamination": values[5],
                "overall_decision": values[6],
            }
            if query_id in rows:
                raise ValueError(f"duplicate expert annotation: {query_id}")
            rows[query_id] = row
    return rows


def parse_notes(text: str) -> dict[str, str]:
    notes: dict[str, str] = {}
    matches = list(re.finditer(r"^###\s+(RAG-\d+)\s*$", text, re.MULTILINE))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        notes[match.group(1)] = text[start:end].strip()
    return notes


def build_annotated_bundle(
    template: dict[str, Any],
    first_text: str,
    continuation_text: str,
    first_path: str,
    continuation_path: str,
) -> dict[str, Any]:
    annotations = parse_rows(first_text, continuation_text)
    notes = parse_notes(continuation_text)
    records = copy.deepcopy(template.get("records", []))
    record_ids = {str(record.get("query_id")) for record in records}
    if record_ids != set(annotations):
        missing = sorted(record_ids - set(annotations))
        extra = sorted(set(annotations) - record_ids)
        raise ValueError(f"annotation coverage mismatch: missing={missing}, extra={extra}")

    for record in records:
        query_id = str(record["query_id"])
        annotation = annotations[query_id]
        expert_annotation = record["expert_annotation"]
        expert_annotation.update(annotation)
        expert_annotation["reviewer"] = "刘武"
        expert_annotation["review_date"] = "2026-09-21"
        expert_annotation["review_notes"] = notes.get(query_id, "")

    summary = {
        "record_count": len(records),
        "overall_decision": {
            "pass": sum(r["expert_annotation"]["overall_decision"] == "pass" for r in records),
            "revise": sum(r["expert_annotation"]["overall_decision"] == "revise" for r in records),
            "insufficient_evidence": sum(
                r["expert_annotation"]["overall_decision"] == "insufficient_evidence"
                for r in records
            ),
            "unclear": sum(r["expert_annotation"]["overall_decision"] == "unclear" for r in records),
        },
        "fault_identification": {
            "correct": sum(r["expert_annotation"]["fault_identification"] == "correct" for r in records),
            "partial": sum(r["expert_annotation"]["fault_identification"] == "partial" for r in records),
            "incorrect": sum(r["expert_annotation"]["fault_identification"] == "incorrect" for r in records),
            "unclear": sum(r["expert_annotation"]["fault_identification"] == "unclear" for r in records),
        },
        "cause_correctness": {
            "correct": sum(r["expert_annotation"]["cause_correctness"] == "correct" for r in records),
            "partial": sum(r["expert_annotation"]["cause_correctness"] == "partial" for r in records),
            "incorrect": sum(r["expert_annotation"]["cause_correctness"] == "incorrect" for r in records),
        },
        "remedy_correctness": {
            "correct": sum(r["expert_annotation"]["remedy_correctness"] == "correct" for r in records),
            "partial": sum(r["expert_annotation"]["remedy_correctness"] == "partial" for r in records),
            "incorrect": sum(r["expert_annotation"]["remedy_correctness"] == "incorrect" for r in records),
        },
        "citation_support": {
            "supported": sum(r["expert_annotation"]["citation_support"] == "supported" for r in records),
            "partial": sum(r["expert_annotation"]["citation_support"] == "partial" for r in records),
            "unsupported": sum(r["expert_annotation"]["citation_support"] == "unsupported" for r in records),
        },
        "unsupported_claims_no": sum(
            r["expert_annotation"]["unsupported_claims"] == "no" for r in records
        ),
        "cross_fault_contamination_no": sum(
            r["expert_annotation"]["cross_fault_contamination"] == "no" for r in records
        ),
    }

    result = copy.deepcopy(template)
    result["bundle_type"] = "siemens_s210_rag_semantic_expert_annotated_v1"
    result["status"] = "expert_annotated_revision_required"
    result["authority_notice"] = "本文件包含刘武专家逐条标注；5 条记录需要先修正回答展示策略并复审，不能直接宣称 30 条全部通过。"
    result["expert_review"] = {
        "reviewer": "刘武",
        "review_date": "2026-09-21",
        "review_type": "RAG 语义回答专家审核",
        "source_files": [first_path, continuation_path],
        "annotation_summary": summary,
        "gold_readiness": "not_final_until_five_revision_items_are_fixed_and_re_reviewed",
    }
    result["records"] = records
    return result


def render_report(bundle: dict[str, Any]) -> str:
    review = bundle["expert_review"]
    summary = review["annotation_summary"]
    revise_ids = [
        record["query_id"]
        for record in bundle["records"]
        if record["expert_annotation"]["overall_decision"] == "revise"
    ]
    lines = [
        "# Siemens S210 RAG 专家语义审核结果 v1",
        "",
        "## 审核信息",
        "",
        "- 审核专家：刘武",
        "- 审核日期：2026-09-21",
        "- 审核范围：RAG-001～RAG-030，共 30 条",
        "- 审核依据：故障识别、原因、处理措施、引用支持、无证据声明、跨故障污染六项标准",
        "",
        "## 专家结论汇总",
        "",
        f"- 通过：{summary['overall_decision']['pass']} 条",
        f"- 需要修改：{summary['overall_decision']['revise']} 条（{', '.join(revise_ids)}）",
        f"- 明显错误：{summary['overall_decision']['insufficient_evidence']} 条",
        f"- 无法判断：{summary['overall_decision']['unclear']} 条",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| 故障识别完全正确 | {summary['fault_identification']['correct']}/30 |",
        f"| 故障识别部分正确 | {summary['fault_identification']['partial']}/30 |",
        f"| 原因正确 | {summary['cause_correctness']['correct']}/30 |",
        f"| 处理措施正确 | {summary['remedy_correctness']['correct']}/30 |",
        f"| 引用完全支持 | {summary['citation_support']['supported']}/30 |",
        f"| 引用部分支持 | {summary['citation_support']['partial']}/30 |",
        f"| 无证据声明为否 | {summary['unsupported_claims_no']}/30 |",
        f"| 跨故障污染为否 | {summary['cross_fault_contamination_no']}/30 |",
        "",
        "## 可报告指标",
        "",
        "- 故障识别严格正确率：25/30 = 83.33%。",
        "- 故障识别部分正确或完全正确覆盖率：30/30 = 100%。",
        "- 原因正确率：30/30 = 100%。",
        "- 处理措施正确率：30/30 = 100%。",
        "- 引用完全支持率：29/30 = 96.67%；另有 1 条为部分支持。",
        "- 无证据声明率：0/30。",
        "- 跨故障污染率：0/30。",
        "",
        "## 必须修正的 5 条",
        "",
        "| Query | 专家判断 | 修正方向 |",
        "|---|---|---|",
        "| RAG-021 | paired fault/message code 未完整展示 | 同时说明 A01693 与 F01679 的配对关系，不只输出 F01679 |",
        "| RAG-027 | F01682 有证据，但未说明 A01706/F01682 关联 | 参数查询返回关联故障集合并解释关系 |",
        "| RAG-028 | A30707 证据正确，但未覆盖 A01707 | 展示 A01707 与 A30707 配对关系 |",
        "| RAG-029 | A30709 证据正确，但未覆盖 A01709 | 展示 A01709 与 A30709 配对关系 |",
        "| RAG-030 | A30711 识别正确，但 r9725 映射解释不足 | 不扩大 r9725 的含义，补充或收窄参数解释 |",
        "",
        "## 最终状态",
        "",
        "这批数据已经完成专家标注，但暂不作为‘30/30 全部通过’的最终 RAG Gold。当前应保留 25 条通过、5 条待修改的专家结论；修正回答展示策略后，只需复审这 5 条，再冻结正式 Gold。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--expert-file", required=True)
    parser.add_argument("--expert-continuation", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()

    first_path = str(Path(args.expert_file).resolve())
    continuation_path = str(Path(args.expert_continuation).resolve())
    bundle = build_annotated_bundle(
        load_json(args.template),
        read_text(first_path),
        read_text(continuation_path),
        first_path,
        continuation_path,
    )
    Path(args.json_output).write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_report(bundle), encoding="utf-8")
    print(json.dumps(bundle["expert_review"]["annotation_summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
