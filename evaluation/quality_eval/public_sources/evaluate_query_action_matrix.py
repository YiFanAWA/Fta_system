"""Compare retrieval baseline, Rule Router v1, and Rule Router + action layer."""

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

from query_decision import QueryDecisionPolicy  # noqa: E402


METRIC_KEYS = ("recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "recall_at_20", "mrr")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _average(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {key: 0.0 for key in METRIC_KEYS}
    return {key: sum(float(row[key]) for row in rows) / len(rows) for key in METRIC_KEYS}


def _zero_metrics() -> dict[str, Any]:
    return {**{key: 0.0 for key in METRIC_KEYS}, "first_relevant_rank": None}


def _gold_action(row: dict[str, Any]) -> str:
    return str(row["action"])


def _action_metrics(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    labels = ("retrieve", "retrieve_with_warning", "clarify")
    pairs = [(row["action_predictions"][stage], _gold_action(row["action_gold"])) for row in rows]
    confusion = {pred: {gold: 0 for gold in labels} for pred in labels}
    for predicted, gold in pairs:
        if predicted not in confusion or gold not in labels:
            raise ValueError(f"unsupported action pair: {predicted}, {gold}")
        confusion[predicted][gold] += 1
    per_class: dict[str, dict[str, float]] = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[label][other] for other in labels if other != label)
        fn = sum(confusion[other][label] for other in labels if other != label)
        per_class[label] = {
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "support": sum(confusion[other][label] for other in labels),
        }
    return {
        "accuracy": sum(predicted == gold for predicted, gold in pairs) / len(pairs),
        "predicted_distribution": dict(Counter(predicted for predicted, _ in pairs)),
        "gold_distribution": dict(Counter(gold for _, gold in pairs)),
        "per_action": per_class,
        "confusion_matrix": confusion,
    }


def _retrieval_metrics(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    candidate = _average([row[stage]["candidate_metrics"] for row in rows])
    ranked = _average([row[stage]["ranked_metrics"] for row in rows])
    contamination: dict[str, float] = {}
    for k in (1, 3, 5, 10, 20):
        contamination[f"wrong_domain_at_{k}"] = sum(
            float(row[stage]["candidate_contamination"][f"at_{k}"]["wrong_domain_presence"])
            for row in rows
        ) / len(rows)
    return {"candidate_recall": candidate, "ranked_metrics": ranked, "candidate_contamination": contamination}


def _action_layer_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    candidate: list[dict[str, Any]] = []
    ranked: list[dict[str, Any]] = []
    contamination = {f"wrong_domain_at_{k}": [] for k in (1, 3, 5, 10, 20)}
    for row in rows:
        if row["rule_router_v1_plus_decision"]["action"] == "clarify":
            candidate.append(_zero_metrics())
            ranked.append(_zero_metrics())
            continue
        base = row["rule_router_v1"]
        candidate.append(base["candidate_metrics"])
        ranked.append(base["ranked_metrics"])
        for k in (1, 3, 5, 10, 20):
            contamination[f"wrong_domain_at_{k}"].append(
                float(base["candidate_contamination"][f"at_{k}"]["wrong_domain_presence"])
            )
    return {
        "candidate_recall": _average(candidate),
        "ranked_metrics": _average(ranked),
        "candidate_contamination": {
            key: sum(values) / len(rows) for key, values in contamination.items()
        },
        "abstain_count": sum(row["rule_router_v1_plus_decision"]["action"] == "clarify" for row in rows),
        "conditional_candidate_recall_non_clarified": _average([
            row["rule_router_v1"]["candidate_metrics"]
            for row in rows
            if row["rule_router_v1_plus_decision"]["action"] != "clarify"
        ]),
        "conditional_ranked_metrics_non_clarified": _average([
            row["rule_router_v1"]["ranked_metrics"]
            for row in rows
            if row["rule_router_v1_plus_decision"]["action"] != "clarify"
        ]),
    }


def _scope_metrics(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    total = len(rows)
    scoped = 0
    false_scope = 0
    filtered_relevant = 0
    for row in rows:
        decision = row["router_decisions"][stage]
        if decision["mode"] != "scoped":
            continue
        scoped += 1
        scope_domain = "industrial_drive" if decision["selected_scope_ids"] == ["siemens_s210"] else "aerospace"
        if scope_domain != row["action_gold"]["domain_decision"]:
            false_scope += 1
        if not set(row[stage]["candidate_pool"]) & set(row["relevant_entity_ids"]):
            filtered_relevant += 1
    return {
        "scoped_count": scoped,
        "false_scope_count": false_scope,
        "false_scope_rate_all_queries": false_scope / total,
        "false_scope_rate_among_scoped": false_scope / scoped if scoped else 0.0,
        "candidate_miss_count_among_scoped": filtered_relevant,
        "candidate_miss_rate_among_scoped": filtered_relevant / scoped if scoped else 0.0,
    }


def evaluate(comparison: dict[str, Any], action_gold: dict[str, Any]) -> dict[str, Any]:
    gold_by_id = {str(row["query_id"]): row for row in action_gold["queries"]}
    rows: list[dict[str, Any]] = []
    policy = QueryDecisionPolicy()
    for source in comparison["queries"]:
        query_id = str(source["query_id"])
        if query_id not in gold_by_id:
            raise ValueError(f"missing action Gold for {query_id}")
        row = {**source, "action_gold": gold_by_id[query_id]}
        route = source["router_decisions"]["rule_router_v1"]
        sufficiency = source["rule_router_v1"]["clarification"]["sufficiency_decision"]
        decision = policy.decide(route_mode=route["mode"], sufficiency_level=sufficiency["level"])
        row["action_predictions"] = {
            "no_router": "retrieve",
            "rule_router_v1": "retrieve",
            "rule_router_v1_plus_query_decision": decision.action,
        }
        row["rule_router_v1_plus_decision"] = decision.to_dict()
        rows.append(row)

    no_router_retrieval = _retrieval_metrics(rows, "no_router")
    rule_retrieval = _retrieval_metrics(rows, "rule_router_v1")
    action_retrieval = _action_layer_metrics(rows)
    stages = {
        "no_router": {
            "action": _action_metrics(rows, "no_router"),
            "retrieval": no_router_retrieval,
            "scope": {"scoped_count": 0, "false_scope_count": 0, "false_scope_rate_all_queries": 0.0, "false_scope_rate_among_scoped": 0.0, "candidate_miss_count_among_scoped": 0, "candidate_miss_rate_among_scoped": 0.0},
        },
        "rule_router_v1": {
            "action": _action_metrics(rows, "rule_router_v1"),
            "retrieval": rule_retrieval,
            "scope": _scope_metrics(rows, "rule_router_v1"),
        },
        "rule_router_v1_plus_query_decision": {
            "action": _action_metrics(rows, "rule_router_v1_plus_query_decision"),
            "retrieval": action_retrieval,
            "scope": _scope_metrics(rows, "rule_router_v1"),
        },
    }
    baseline_r20 = stages["no_router"]["retrieval"]["candidate_recall"]["recall_at_20"]
    for stage in stages.values():
        stage["retrieval"]["candidate_recall_loss_vs_no_router"] = baseline_r20 - stage["retrieval"]["candidate_recall"]["recall_at_20"]
    return {
        "evaluation_info": {
            "name": "query_action_matrix_v2",
            "version": "2026-09-21",
            "action_gold": "query_action_gold_v2",
            "comparison_source": comparison["evaluation_info"]["name"],
            "query_count": len(rows),
            "production_claim": False,
            "decision_layer": "Rule Router v1 + QueryDecisionPolicy; no Retrieval core change",
        },
        "stages": stages,
        "queries": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Query Action Gold v2 实验矩阵",
        "",
        "本报告冻结 Generic Retrieval v1，只比较 No Router、Rule Router v1、Rule Router v1 + Query Decision Layer。",
        "",
        "## 主要指标",
        "",
        "| 方案 | Action Accuracy | Candidate Recall@20 | Candidate Recall Loss | R@1 | MRR | WrongDomain@1 | False Scope@all | Scoped Candidate Miss@scoped |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (
        ("no_router", "No Router"),
        ("rule_router_v1", "Rule Router v1"),
        ("rule_router_v1_plus_query_decision", "Rule Router v1 + Query Decision"),
    ):
        stage = report["stages"][key]
        retrieval = stage["retrieval"]
        scope = stage["scope"]
        lines.append(
            f"| {label} | {stage['action']['accuracy']:.4f} | {retrieval['candidate_recall']['recall_at_20']:.4f} | {retrieval['candidate_recall_loss_vs_no_router']:.4f} | {retrieval['ranked_metrics']['recall_at_1']:.4f} | {retrieval['ranked_metrics']['mrr']:.4f} | {retrieval['candidate_contamination']['wrong_domain_at_1']:.4f} | {scope['false_scope_rate_all_queries']:.4f} | {scope['candidate_miss_rate_among_scoped']:.4f} |"
        )
    lines.extend([
        "",
        "## Action 分类",
        "",
        "Gold action：`retrieve=9`、`retrieve_with_warning=70`、`clarify=0`。",
        "",
        "| 方案 | retrieve Precision/Recall | warning Precision/Recall | clarify Precision/Recall | 澄清数 |",
        "|---|---:|---:|---:|---:|",
    ])
    for key, label in (
        ("no_router", "No Router"),
        ("rule_router_v1", "Rule Router v1"),
        ("rule_router_v1_plus_query_decision", "Rule Router v1 + Query Decision"),
    ):
        action = report["stages"][key]["action"]
        lines.append(
            f"| {label} | {action['per_action']['retrieve']['precision']:.4f}/{action['per_action']['retrieve']['recall']:.4f} | {action['per_action']['retrieve_with_warning']['precision']:.4f}/{action['per_action']['retrieve_with_warning']['recall']:.4f} | {action['per_action']['clarify']['precision']:.4f}/{action['per_action']['clarify']['recall']:.4f} | {action['predicted_distribution'].get('clarify', 0)} |"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        "- `false_scope` 只统计 Router 已缩小到错误领域的情况；cross_domain 不算错误缩小。",
        "- Query Decision Layer 的 `clarify` 会产生空检索结果，因此全量 Recall 会下降；同时报告未澄清查询的条件召回，区分“安全停下”和“检索能力下降”。",
        "- `retrieve_with_warning` 不阻断检索，只影响回答层提示。",
        "- 本轮没有接入生产 API/前端，也没有修改 Generic Retrieval v1、embedding 或 reranker。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--action-gold", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(_read(args.comparison), _read(args.action_gold))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
