"""Build an evidence-first, expert-annotatable RAG review bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LABELS = {
    "fault_identification": ["correct", "partial", "incorrect", "unclear"],
    "cause_correctness": ["correct", "partial", "incorrect", "not_applicable", "unclear"],
    "remedy_correctness": ["correct", "partial", "incorrect", "not_applicable", "unclear"],
    "citation_support": ["supported", "partial", "unsupported", "unclear"],
    "unsupported_claims": ["no", "yes", "unclear"],
    "cross_fault_contamination": ["no", "yes", "unclear"],
    "overall_decision": ["pass", "revise", "insufficient_evidence", "unclear"],
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _citation_map(response: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for context in _as_list(response.get("contexts")):
        if not isinstance(context, dict):
            continue
        for evidence in _as_list(context.get("evidence")):
            if isinstance(evidence, dict) and evidence.get("citation_id"):
                result[str(evidence["citation_id"])] = evidence
    return result


def build_bundle(dataset: dict[str, Any], responses: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    queries = {
        str(item.get("query_id")): item
        for item in _as_list(dataset.get("queries"))
        if isinstance(item, dict) and item.get("query_id")
    }
    response_by_id = {
        str(item.get("query_id")): item
        for item in _as_list(responses.get("responses"))
        if isinstance(item, dict) and item.get("query_id")
    }
    contract_by_id = {
        str(item.get("query_id")): item
        for item in _as_list(contract.get("per_query"))
        if isinstance(item, dict) and item.get("query_id")
    }

    records: list[dict[str, Any]] = []
    for query_id, query in queries.items():
        response = response_by_id.get(query_id, {})
        answer = response.get("answer") if isinstance(response.get("answer"), dict) else {}
        citation_map = _citation_map(response)
        citation_ids = [str(item) for item in _as_list(answer.get("citations")) if str(item)]
        cited_evidence = []
        for citation_id in citation_ids:
            evidence = citation_map.get(citation_id)
            if evidence:
                cited_evidence.append(
                    {
                        "citation_id": citation_id,
                        "field": evidence.get("field", ""),
                        "quote": evidence.get("quote", ""),
                        "source_id": evidence.get("source_id", ""),
                        "source_file": evidence.get("source_file", ""),
                        "start": evidence.get("start"),
                        "end": evidence.get("end"),
                    }
                )
        contract_row = contract_by_id.get(query_id, {})
        records.append(
            {
                "query_id": query_id,
                "question": query.get("question", ""),
                "query_type": query.get("query_type", ""),
                "difficulty": query.get("difficulty", ""),
                "evaluation_reference": {
                    "expected_fault_codes": query.get("expected_fault_codes", []),
                    "required_evidence_fields": query.get("required_evidence_fields", []),
                    "ambiguity": query.get("ambiguity", ""),
                    "note": "仅供评测追踪；专家可以指出 expected_fault_codes 过窄或不正确。",
                },
                "model_answer": {
                    "text": answer.get("text", ""),
                    "citations": citation_ids,
                    "cited_evidence": cited_evidence,
                },
                "automated_contract_reference": {
                    "fault_code_hit": contract_row.get("fault_code_hit"),
                    "citations_valid": contract_row.get("citations_valid"),
                    "citations_aligned": contract_row.get("citations_aligned"),
                    "answer_contract_pass": contract_row.get("answer_contract_pass"),
                    "warning": "这是自动结构检查，不是专家语义结论。",
                },
                "expert_annotation": {
                    "fault_identification": None,
                    "cause_correctness": None,
                    "remedy_correctness": None,
                    "citation_support": None,
                    "unsupported_claims": None,
                    "cross_fault_contamination": None,
                    "overall_decision": None,
                    "review_notes": "",
                    "reviewer": "",
                    "review_date": "",
                },
            }
        )
    return {
        "bundle_type": "siemens_s210_rag_semantic_expert_review_bundle_v1",
        "created_at": "2026-09-21",
        "status": "ready_for_domain_expert_annotation",
        "authority_notice": "本文件不预填专家结论。模型回答和原文证据并列展示，专家必须基于证据独立标注。",
        "scope": {
            "query_count": len(records),
            "source_dataset": "siemens_s210_rag_semantic_gold_v1_2026-09-21",
            "response_run": "siemens_s210_rag_semantic_responses_v1_2026-09-21",
            "expert_required": True,
        },
        "annotation_standard": {
            "principle": "只依据所列原文证据判断；工程常识可以帮助理解，但不能替代原文支持。",
            "labels": LABELS,
            "decision_rules": [
                "fault_identification=correct：回答的故障码/故障实体与问题和证据一致；配对故障码或共享参数只要属于 expected_fault_codes 即可，再由专家判断是否应补码。",
                "cause_correctness=correct：回答中的原因与证据原文语义一致；仅仅合理推测但原文没有，不得标 correct。",
                "remedy_correctness=correct：处理措施可由 Remedy 证据直接支持；检查、更换、复位等动作不能凭工程经验补写。",
                "citation_support=supported：引用的原文能够支持回答中的对应陈述；只能证明同一故障码不等于支持原因或处理措施。",
                "unsupported_claims=yes：回答出现原文和证据均无法支持的事实、参数、原因、维修动作或确定性结论。",
                "cross_fault_contamination=yes：回答把其他故障记录的原因、参数或处理措施混入当前故障，且没有明确说明这是相关故障。",
                "overall_decision=pass：核心回答正确、证据支持且无关键无依据陈述；其余情况按问题严重性选择 revise/insufficient_evidence/unclear。",
                "如果原文证据不足，不要依据模型的自信程度判定正确，应使用 insufficient_evidence 或 unclear。",
            ],
            "expert_workflow": [
                "先读问题和模型回答。",
                "逐条打开引用证据，核对故障码、原因、处理措施是否被原文支持。",
                "对每个字段填写标签；没有涉及的原因/处理措施填写 not_applicable。",
                "在 review_notes 中写明具体错误句子、对应 citation_id 和建议修改。",
                "最后填写 overall_decision、reviewer 和 review_date。",
            ],
        },
        "records": records,
    }


def render_markdown(bundle: dict[str, Any]) -> str:
    standard = bundle["annotation_standard"]
    lines = [
        "# Siemens S210 RAG 故障回答专家审核清单 v1",
        "",
        "> 本清单用于领域专家逐条审核，不预填专家结论。模型回答、引用证据和自动合同状态仅供核验。",
        "",
        "## 一、审核范围",
        "",
        "- 样本：30 条全新中文 RAG 查询。",
        "- 审核对象：当前 `/api/rag/query` 实际生成的回答。",
        "- 证据：每条回答下方列出模型实际引用的原文片段、字段和字符位置。",
        "- 注意：`expected_fault_codes` 只是评测参考，不限制专家发现配对故障码、消息码或共享参数。",
        "",
        "## 二、统一标注标准",
        "",
        f"**总原则：** {standard['principle']}",
        "",
    ]
    for name, labels in standard["labels"].items():
        lines.append(f"- `{name}`：`{'` / `'.join(labels)}`")
    lines += ["", "### 判定规则", ""]
    for index, rule in enumerate(standard["decision_rules"], 1):
        lines.append(f"{index}. {rule}")
    lines += ["", "### 审核步骤", ""]
    for index, step in enumerate(standard["expert_workflow"], 1):
        lines.append(f"{index}. {step}")
    lines += ["", "## 三、逐条审核记录", ""]

    for record in bundle["records"]:
        lines += [
            f"### {record['query_id']} · {record['query_type']} · {record['difficulty']}",
            "",
            f"**用户问题：** {record['question']}",
            "",
            f"**评测参考故障码：** `{', '.join(record['evaluation_reference']['expected_fault_codes'])}`  ",
            f"**必需证据字段：** `{', '.join(record['evaluation_reference']['required_evidence_fields'])}`  ",
            f"**歧义说明：** {record['evaluation_reference']['ambiguity']}",
            "",
            "#### 模型回答",
            "",
            "```text",
            record["model_answer"]["text"].strip(),
            "```",
            "",
            "#### 模型引用的原文证据",
            "",
        ]
        for evidence in record["model_answer"]["cited_evidence"]:
            location = f"{evidence['start']}–{evidence['end']}" if evidence["start"] is not None else "未提供"
            quote = evidence["quote"].replace("\n", " ")
            lines.append(
                f"- `{evidence['citation_id']}` · 字段 `{evidence['field']}` · 字符 `{location}`：{quote}"
            )
        lines += [
            "",
            "#### 专家填写",
            "",
            "| 标注项 | 可选值 | 专家结论 | 依据/备注 |",
            "|---|---|---|---|",
            "| 故障识别 | correct / partial / incorrect / unclear |  |  |",
            "| 原因正确性 | correct / partial / incorrect / not_applicable / unclear |  |  |",
            "| 处理措施正确性 | correct / partial / incorrect / not_applicable / unclear |  |  |",
            "| 引用支持 | supported / partial / unsupported / unclear |  |  |",
            "| 无证据声明 | no / yes / unclear |  |  |",
            "| 跨故障污染 | no / yes / unclear |  |  |",
            "| 总体结论 | pass / revise / insufficient_evidence / unclear |  |  |",
            "",
            "专家：____________________    日期：____________________",
            "",
            "---",
            "",
        ]
    return "\n".join(line.rstrip() for line in lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--contract-report", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()

    bundle = build_bundle(
        load_json(args.dataset),
        load_json(args.responses),
        load_json(args.contract_report),
    )
    Path(args.json_output).write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_markdown(bundle), encoding="utf-8")
    print(json.dumps(bundle["scope"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
