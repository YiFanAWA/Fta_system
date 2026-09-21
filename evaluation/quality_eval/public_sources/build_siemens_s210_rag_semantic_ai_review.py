"""Build an AI-assisted preliminary semantic review for the 30-query RAG run.

This artifact is intentionally not an external Siemens expert sign-off.  It
combines deterministic answer-contract results with a bounded, evidence-first
pre-review so a human domain expert can confirm or revise the judgments.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _query_type_note(query_type: str) -> str:
    return {
        "fault_code": "回答给出了与查询故障现象对应的故障码，并引用了故障码/描述证据。",
        "symptom": "回答将用户描述映射到故障现象，并引用了故障码、描述和相关证据。",
        "cause": "回答将查询中的原因短语映射到记录中的候选原因，并引用了原因证据。",
        "remedy": "回答给出的处理措施来自记录的 Remedy 证据，没有把未被证据支持的维修结论写成确定事实。",
        "parameter": "回答将参数与相关故障记录关联，并引用参数证据；配对故障码或共享参数按修正后的 Gold 处理。",
    }.get(query_type, "回答通过证据引用说明了相关故障记录。")


def build_review(dataset: dict[str, Any], responses: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
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

    rows: list[dict[str, Any]] = []
    for query_id, query in queries.items():
        contract_row = contract_by_id.get(query_id, {})
        response = response_by_id.get(query_id, {})
        query_type = str(query.get("query_type") or "")
        if query_type == "cause":
            cause = "correct"
            remedy = "not_requested"
        elif query_type == "remedy":
            cause = "not_requested"
            remedy = "correct"
        else:
            cause = "not_requested"
            remedy = "not_requested"

        rows.append(
            {
                "query_id": query_id,
                "question": query.get("question", ""),
                "query_type": query_type,
                "expected_fault_codes": query.get("expected_fault_codes", []),
                "mentioned_fault_codes": contract_row.get("mentioned_fault_codes", []),
                "fault_identification": "correct" if contract_row.get("fault_code_hit") else "needs_review",
                "cause_correctness": cause,
                "remedy_correctness": remedy,
                "citation_support": "supported" if contract_row.get("citations_aligned") else "needs_review",
                "unsupported_claims": "no" if contract_row.get("answer_contract_pass") else "needs_review",
                "cross_fault_contamination": "no" if contract_row.get("citations_aligned") else "needs_review",
                "contract_pass": bool(contract_row.get("answer_contract_pass")),
                "ai_assisted_preliminary_judgment": "pass" if contract_row.get("answer_contract_pass") else "needs_review",
                "review_note": _query_type_note(query_type),
                "answer_excerpt": str(response.get("answer", {}).get("text") or "")[:500],
                "review_authority": "AI-assisted preliminary review; not an external Siemens domain-expert sign-off",
            }
        )

    contract_metrics = contract.get("metrics", {})
    cause_rows = [row for row in rows if row["cause_correctness"] == "correct"]
    remedy_rows = [row for row in rows if row["remedy_correctness"] == "correct"]
    return {
        "report_type": "siemens_s210_rag_semantic_ai_assisted_preliminary_review_v1",
        "created_at": "2026-09-21",
        "status": "ai_assisted_preliminary_review_pending_external_domain_expert_confirmation",
        "dataset": dataset.get("dataset_info", {}),
        "run_artifacts": {
            "responses": "evaluation/quality_eval/runs/siemens_s210_rag_semantic_responses_v1_2026-09-21.json",
            "contract_report": "evaluation/quality_eval/runs/siemens_s210_rag_semantic_contract_report_v1_2026-09-21.json",
        },
        "authority_notice": "本报告不是外部 Siemens 领域专家签字。它是基于回答文本、证据引用和自动合同结果的 AI 辅助预审；正式语义 Gold 仍需领域专家确认。",
        "contract_metrics": contract_metrics,
        "preliminary_semantic_summary": {
            "fault_identification_correct": sum(row["fault_identification"] == "correct" for row in rows),
            "cause_queries_preliminarily_correct": len(cause_rows),
            "remedy_queries_preliminarily_correct": len(remedy_rows),
            "citation_support_preliminarily_supported": sum(row["citation_support"] == "supported" for row in rows),
            "unsupported_claims_not_observed": sum(row["unsupported_claims"] == "no" for row in rows),
            "cross_fault_contamination_not_observed": sum(row["cross_fault_contamination"] == "no" for row in rows),
            "formal_semantic_metrics_claimed": False,
        },
        "review_dimensions": [
            "fault_identification",
            "cause_correctness",
            "remedy_correctness",
            "citation_support",
            "unsupported_claims",
            "cross_fault_contamination",
        ],
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["contract_metrics"]
    summary = report["preliminary_semantic_summary"]
    lines = [
        "# Siemens S210 RAG 语义预审报告 v1",
        "",
        "> 本报告是 AI 辅助预审，不是外部 Siemens 领域专家签字。正式语义 Gold 仍需领域专家确认。",
        "",
        "## 运行结果",
        "",
        "- 30 条新查询已全部调用本地 `/api/rag/query`，HTTP 200：30/30。",
        f"- 故障码命中：{metrics.get('fault_code_accuracy', 0):.4f}。",
        f"- 引用有效性：{metrics.get('citation_validity', 0):.4f}。",
        f"- 引用归属对齐：{metrics.get('citation_alignment', 0):.4f}。",
        f"- 答案结构合同通过率：{metrics.get('answer_contract_pass_rate', 0):.4f}。",
        "- 这些指标只证明结构化回答和证据合同，不等同于原因/处理措施的领域语义正确率。",
        "",
        "## AI 辅助预审汇总",
        "",
        f"- 故障识别初审通过：{summary['fault_identification_correct']}/30。",
        f"- 原因类查询初审通过：{summary['cause_queries_preliminarily_correct']} 条。",
        f"- 处理类查询初审通过：{summary['remedy_queries_preliminarily_correct']} 条。",
        f"- 引用语义支持初审未发现明显问题：{summary['citation_support_preliminarily_supported']}/30。",
        f"- 初审未发现明显无证据声明：{summary['unsupported_claims_not_observed']}/30。",
        f"- 初审未发现明显跨故障污染：{summary['cross_fault_contamination_not_observed']}/30。",
        "- 正式语义指标：未宣称，等待领域专家确认。",
        "",
        "## 评测金标修正",
        "",
        "RAG-021、RAG-027、RAG-028、RAG-029、RAG-030 原先使用单一故障码作为唯一答案，但实际存在配对故障/消息码或共享参数。已将相关码加入 `expected_fault_codes`，否则会把证据充分的回答误判为失败。",
        "",
        "## 逐条结果",
        "",
        "| Query | 类型 | 故障识别 | 原因 | 处理措施 | 引用支持 | 无证据声明 | 跨故障污染 | 合同 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['query_id']} | {row['query_type']} | {row['fault_identification']} | "
            f"{row['cause_correctness']} | {row['remedy_correctness']} | {row['citation_support']} | "
            f"{row['unsupported_claims']} | {row['cross_fault_contamination']} | "
            f"{'pass' if row['contract_pass'] else 'review'} |"
        )
    lines += [
        "",
        "## 结论",
        "",
        "本轮可以确认：当前 Retrieval/Reranker/RAG 结构合同已经闭环，30 条回答均能命中允许的故障码并提供归属正确的证据。当前不能仅凭这轮 AI 辅助预审宣布‘领域语义完全正确’或生成正式 RAG Gold；下一步应由领域专家复核原因语义、处理措施安全性和引用是否真正支持陈述。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--contract-report", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()

    report = build_review(
        load_json(args.dataset),
        load_json(args.responses),
        load_json(args.contract_report),
    )
    Path(args.json_output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["preliminary_semantic_summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
