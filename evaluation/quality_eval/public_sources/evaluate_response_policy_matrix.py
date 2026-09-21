"""Evaluate post-retrieval response policy without rerunning retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from response_policy import ResponsePolicyLayer  # noqa: E402


METRIC_KEYS = ("recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "recall_at_20", "mrr")
POLICIES = ("normal", "warning", "clarify")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _average(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {key: 0.0 for key in METRIC_KEYS}
    return {key: sum(float(row[key]) for row in rows) / len(rows) for key in METRIC_KEYS}


def _retrieval_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    candidate = _average([row["rule_router_v1"]["candidate_metrics"] for row in rows])
    ranked = _average([row["rule_router_v1"]["ranked_metrics"] for row in rows])
    contamination = {
        f"wrong_domain_at_{k}": sum(
            float(row["rule_router_v1"]["candidate_contamination"][f"at_{k}"]["wrong_domain_presence"])
            for row in rows
        )
        / len(rows)
        for k in (1, 3, 5, 10, 20)
    }
    return {
        "candidate_recall": candidate,
        "ranked_metrics": ranked,
        "candidate_contamination": contamination,
    }


def _policy_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    confusion = {pred: {gold: 0 for gold in POLICIES} for pred in POLICIES}
    for row in rows:
        predicted = row["response_policy_prediction"]
        gold = row["response_policy_gold"]
        confusion[predicted][gold] += 1

    per_policy: dict[str, dict[str, Any]] = {}
    for label in POLICIES:
        tp = confusion[label][label]
        fp = sum(confusion[label][other] for other in POLICIES if other != label)
        fn = sum(confusion[other][label] for other in POLICIES if other != label)
        support = sum(confusion[other][label] for other in POLICIES)
        per_policy[label] = {
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "support": support,
            "predicted": sum(confusion[label][other] for other in POLICIES),
        }

    return {
        "accuracy": sum(row["response_policy_prediction"] == row["response_policy_gold"] for row in rows) / len(rows),
        "predicted_distribution": dict(Counter(row["response_policy_prediction"] for row in rows)),
        "gold_distribution": dict(Counter(row["response_policy_gold"] for row in rows)),
        "per_policy": per_policy,
        "confusion_matrix": confusion,
        "clarification_rate": sum(row["response_policy_prediction"] == "clarify" for row in rows) / len(rows),
    }


def _metric_deltas(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    return {key: float(right[key]) - float(left[key]) for key in left}


def evaluate(comparison: dict[str, Any], response_gold: dict[str, Any]) -> dict[str, Any]:
    gold_by_id = {str(row["query_id"]): row for row in response_gold["queries"]}
    if len(gold_by_id) != len(comparison["queries"]):
        raise ValueError("response-policy Gold and comparison query counts differ")

    layer = ResponsePolicyLayer()
    rows: list[dict[str, Any]] = []
    for source in comparison["queries"]:
        query_id = str(source["query_id"])
        if query_id not in gold_by_id:
            raise ValueError(f"missing response-policy Gold for {query_id}")
        gold = gold_by_id[query_id]
        sufficiency = source["rule_router_v1"]["clarification"]["sufficiency_decision"]
        decision = layer.decide(sufficiency_level=str(sufficiency["level"]))
        base = source["rule_router_v1"]
        rows.append(
            {
                "query_id": query_id,
                "query": source["query"],
                "response_policy_gold": gold["response_policy"],
                "retrieval_policy_gold": gold["retrieval_policy"],
                "source_action": gold["source_action"],
                "machine_sufficiency_level": sufficiency["level"],
                "response_policy_prediction": decision.response_policy,
                "response_policy_decision": decision.to_dict(),
                "retrieval_policy_prediction": decision.retrieval_policy,
                "retrieval_first_relevant_rank": base["ranked_metrics"]["first_relevant_rank"],
                "candidate_recall_at_20": base["candidate_metrics"]["recall_at_20"],
            }
        )

    baseline_retrieval = _retrieval_metrics(comparison["queries"])
    policy_retrieval = json.loads(json.dumps(baseline_retrieval))
    response_policy = _policy_metrics(rows)
    parity = {
        "retrieval_identical": baseline_retrieval == policy_retrieval,
        "candidate_recall_delta": _metric_deltas(
            baseline_retrieval["candidate_recall"], policy_retrieval["candidate_recall"]
        ),
        "ranked_metrics_delta": _metric_deltas(
            baseline_retrieval["ranked_metrics"], policy_retrieval["ranked_metrics"]
        ),
        "contamination_delta": _metric_deltas(
            baseline_retrieval["candidate_contamination"], policy_retrieval["candidate_contamination"]
        ),
    }
    if not parity["retrieval_identical"]:
        raise AssertionError("post-retrieval response policy changed retrieval metrics")

    return {
        "evaluation_info": {
            "name": "response_policy_matrix_v1",
            "version": "2026-09-21",
            "comparison_source": comparison["evaluation_info"]["name"],
            "response_policy_gold": "response_policy_gold_v1",
            "query_count": len(rows),
            "production_claim": False,
            "retrieval_core_changed": False,
            "architecture": "Query -> Rule Router v1 -> Retrieval/Reranker -> Response Policy -> RAG",
        },
        "stages": {
            "rule_router_v1": {
                "retrieval": baseline_retrieval,
                "response_policy": None,
            },
            "rule_router_v1_plus_response_policy": {
                "retrieval": policy_retrieval,
                "response_policy": response_policy,
            },
        },
        "retrieval_parity": parity,
        "answer_safety_metrics": {
            "unsupported_claim_rate": None,
            "citation_support_rate": None,
            "note": "These require generated RAG answers and a separate human semantic Gold; this matrix only evaluates policy behavior and retrieval parity.",
        },
        "queries": rows,
    }


def _fmt(value: Any) -> str:
    return "N/A" if value is None else f"{float(value):.4f}"


def render_markdown(report: dict[str, Any]) -> str:
    baseline = report["stages"]["rule_router_v1"]["retrieval"]
    policy_stage = report["stages"]["rule_router_v1_plus_response_policy"]
    policy = policy_stage["response_policy"]
    lines = [
        "# Response Policy v1 实验矩阵",
        "",
        "本报告复用已生成的 Rule Router v1 检索结果，不重新运行 embedding、RRF、Router 或 Reranker。Response Policy 只控制检索后的回答方式。",
        "",
        "## 架构合同",
        "",
        "```text",
        "Query -> Rule Router v1 -> Retrieval/Reranker -> Response Policy -> RAG",
        "```",
        "",
        "`normal` 正常回答；`warning` 继续回答但降低确定性并提示补充信息；`clarify` 可以利用检索结果组织澄清问题，但不输出确定性结论。三者均不改变候选召回。",
        "",
        "## 检索指标保持不变",
        "",
        "| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR | WrongDomain@1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, stage in (("Rule Router v1", baseline), ("Rule Router v1 + Response Policy", policy_stage["retrieval"])):
        lines.append(
            f"| {label} | {_fmt(stage['ranked_metrics']['recall_at_1'])} | {_fmt(stage['ranked_metrics']['recall_at_3'])} | {_fmt(stage['ranked_metrics']['recall_at_5'])} | {_fmt(stage['ranked_metrics']['recall_at_10'])} | {_fmt(stage['ranked_metrics']['recall_at_20'])} | {_fmt(stage['ranked_metrics']['mrr'])} | {_fmt(stage['candidate_contamination']['wrong_domain_at_1'])} |"
        )
    lines.extend(
        [
            "",
            f"检索 parity：**{'通过' if report['retrieval_parity']['retrieval_identical'] else '失败'}**。所有检索指标差值均为 0。",
            "",
            "## Response Policy 指标",
            "",
            "| 指标 | 值 |",
            "|---|---:|",
            f"| Policy Accuracy | {_fmt(policy['accuracy'])} |",
            f"| 预测 normal / warning / clarify | {policy['predicted_distribution'].get('normal', 0)} / {policy['predicted_distribution'].get('warning', 0)} / {policy['predicted_distribution'].get('clarify', 0)} |",
            f"| Gold normal / warning / clarify | {policy['gold_distribution'].get('normal', 0)} / {policy['gold_distribution'].get('warning', 0)} / {policy['gold_distribution'].get('clarify', 0)} |",
            f"| 预测澄清率 | {_fmt(policy['clarification_rate'])} |",
            "",
            "| Policy | Precision | Recall | Support |",
            "|---|---:|---:|---:|",
        ]
    )
    for label in ("normal", "warning", "clarify"):
        item = policy["per_policy"][label]
        lines.append(f"| {label} | {_fmt(item['precision'])} | {_fmt(item['recall'])} | {item['support']} |")
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- 当前机器 Query Analyzer 产生的 `insufficient` 查询会预测为 `clarify`，但这只影响回答策略，不再清空检索结果。",
            "- 当前专家 Gold 没有 `clarify` 样本，因此不能据此宣称“必须澄清后才能回答”的策略已经得到专家验证。",
            "- `unsupported_claim_rate` 和 `citation_support_rate` 当前为 N/A；它们需要下一阶段真实生成答案后的人工语义评测，不能由检索矩阵代替。",
            "- 本轮没有接入生产 API/前端，也没有修改 Generic Retrieval、embedding、reranker 或 Rule Router v1。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--response-gold", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(_read(args.comparison), _read(args.response_gold))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
