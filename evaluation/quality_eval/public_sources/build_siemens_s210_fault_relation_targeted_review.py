"""Build the five-record expert re-review bundle for fault relations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TARGET_IDS = ["RAG-021", "RAG-027", "RAG-028", "RAG-029", "RAG-030"]


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_bundle(dataset: dict[str, Any], targeted: dict[str, Any]) -> dict[str, Any]:
    questions = {
        str(item.get("query_id")): item
        for item in dataset.get("queries", [])
        if isinstance(item, dict)
    }
    records = []
    for response in targeted.get("responses", []):
        query_id = str(response.get("query_id"))
        question = questions.get(query_id, {})
        records.append(
            {
                "query_id": query_id,
                "question": response.get("question", question.get("question", "")),
                "expected_fault_codes": question.get("expected_fault_codes", []),
                "retrieval_reused_from": response.get("retrieval_reused_from", ""),
                "model_answer": response.get("answer", {}),
                "relations": response.get("relations", []),
                "relation_evidence": [
                    evidence
                    for relation in response.get("relations", [])
                    for evidence in relation.get("evidence", [])
                ],
                "expert_annotation": {
                    "relation_completeness": None,
                    "relation_type_correctness": None,
                    "relation_evidence_support": None,
                    "unsupported_parameter_semantics": None,
                    "overall_decision": None,
                    "review_notes": "",
                    "reviewer": "",
                    "review_date": "",
                },
            }
        )
    if [record["query_id"] for record in records] != TARGET_IDS:
        raise ValueError("targeted regression does not contain exactly the five target queries")
    return {
        "bundle_type": "siemens_s210_fault_relation_targeted_expert_review_v1",
        "created_at": "2026-09-21",
        "status": "ready_for_expert_targeted_rereview",
        "authority_notice": "本清单不预填专家结论；原始 30 条中这 5 条已被专家标记为 revise，本清单只复审关系层修正。",
        "scope": {
            "query_count": 5,
            "query_ids": TARGET_IDS,
            "retrieval_changed": False,
            "reranker_changed": False,
            "router_changed": False,
        },
        "annotation_standard": {
            "relation_completeness": ["complete", "partial", "incorrect", "unclear"],
            "relation_type_correctness": ["correct", "incorrect", "unclear"],
            "relation_evidence_support": ["supported", "partial", "unsupported", "unclear"],
            "unsupported_parameter_semantics": ["no", "yes", "unclear"],
            "overall_decision": ["pass", "revise", "insufficient_evidence", "unclear"],
            "rules": [
                "关系完整：问题涉及的配对故障/消息码或共享参数关系均已展示。",
                "关系类型正确：paired_fault_message 或 shared_parameter 与证据语义一致。",
                "关系证据支持：每个关系两端都能在引用证据中找到对应故障码、描述、原因或参数。",
                "参数语义边界：如果原文没有解释参数具体值或映射，不得把推测写成确定含义；应标 yes 或 revise。",
                "只审核关系层修正；原先已通过的原因、处理措施和跨故障污染不需要重新扩大审核范围，但发现新问题仍应记录。",
            ],
        },
        "records": records,
    }


def render_markdown(bundle: dict[str, Any]) -> str:
    def clean_multiline_text(value: Any) -> str:
        return "\n".join(line.rstrip() for line in str(value or "").splitlines()).strip()

    lines = [
        "# Siemens S210 Fault Relation v1 专家复审清单",
        "",
        "> 只复审原专家标记的 5 条关系问题，不重新审核全部 30 条。模型回答和关系证据已列出，专家结论栏为空。",
        "",
        "## 审核范围",
        "",
        "- RAG-021、RAG-027、RAG-028、RAG-029、RAG-030",
        "- Retrieval、Reranker、Router 均复用原结果，没有重新调参。",
        "- 重点确认：关系是否完整、关系类型是否正确、关系证据是否充分、参数语义是否被过度解释。",
        "",
        "## 标注标准",
        "",
        "- 关系完整性：`complete / partial / incorrect / unclear`",
        "- 关系类型：`correct / incorrect / unclear`",
        "- 关系证据：`supported / partial / unsupported / unclear`",
        "- 无依据参数语义：`no / yes / unclear`",
        "- 总体结论：`pass / revise / insufficient_evidence / unclear`",
        "",
        "**判定原则：只依据列出的原文引用；原文未解释的参数值含义必须保持不确定，不能靠工程常识补全。**",
        "",
    ]
    for record in bundle["records"]:
        lines += [
            f"## {record['query_id']}",
            "",
            f"**用户问题：** {record['question']}",
            "",
            f"**评测参考故障码：** `{', '.join(record['expected_fault_codes'])}`",
            "",
            "### 修正后的模型回答",
            "",
            "```text",
            clean_multiline_text(record["model_answer"].get("text")),
            "```",
            "",
            "### Fault Relation 结构",
            "",
            "```json",
            json.dumps(record["relations"], ensure_ascii=False, indent=2),
            "```",
            "",
            "### 关系证据",
            "",
        ]
        for evidence in record["relation_evidence"]:
            lines.append(
                f"- `{evidence.get('citation_id')}` · `{evidence.get('fault_code')}` · "
                f"`{evidence.get('field')}`：{str(evidence.get('quote') or '').replace(chr(10), ' ')}"
            )
        lines += [
            "",
            "### 专家填写",
            "",
            "| 标注项 | 可选值 | 专家结论 | 备注 |",
            "|---|---|---|---|",
            "| 关系完整性 | complete / partial / incorrect / unclear |  |  |",
            "| 关系类型 | correct / incorrect / unclear |  |  |",
            "| 关系证据支持 | supported / partial / unsupported / unclear |  |  |",
            "| 无依据参数语义 | no / yes / unclear |  |  |",
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
    parser.add_argument("--targeted", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()
    bundle = build_bundle(load_json(args.dataset), load_json(args.targeted))
    Path(args.json_output).write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_markdown(bundle), encoding="utf-8")
    print(json.dumps(bundle["scope"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
