"""Evaluate Router v1/v2 against the full expert query-sufficiency Gold.

This consumes an already completed retrieval comparison, so it does not rerun
the embedding model. The third strategy is Expert Router v2 plus the current
machine sufficiency gate; a clarified query produces no retrieval result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


METRIC_KEYS = (
    "recall_at_1",
    "recall_at_3",
    "recall_at_5",
    "recall_at_10",
    "recall_at_20",
    "mrr",
)
SCOPE_TO_DOMAIN = {
    "siemens_s210": "industrial_drive",
    "faa_sdr": "aerospace",
}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _average(rows: Sequence[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {key: 0.0 for key in METRIC_KEYS}
    return {key: sum(float(row[key]) for row in rows) / len(rows) for key in METRIC_KEYS}


def _zero_metrics() -> dict[str, Any]:
    return {**{key: 0.0 for key in METRIC_KEYS}, "first_relevant_rank": None}


def _domain_from_decision(decision: dict[str, Any]) -> str:
    if decision.get("mode") != "scoped":
        return "cross_domain"
    scopes = decision.get("selected_scope_ids", [])
    if len(scopes) != 1:
        return "cross_domain"
    return SCOPE_TO_DOMAIN.get(scopes[0], "cross_domain")


def _domain_accuracy(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    predictions = []
    for row in rows:
        predicted = _domain_from_decision(row["router_decisions"][stage])
        predictions.append({
            "query_id": row["query_id"],
            "predicted_domain": predicted,
            "gold_domain": row["expert_gold"]["domain_decision"],
            "correct": predicted == row["expert_gold"]["domain_decision"],
        })
    return {
        "accuracy_all_queries": sum(item["correct"] for item in predictions) / len(predictions),
        "scoped_or_committed_rate": sum(item["predicted_domain"] != "cross_domain" for item in predictions) / len(predictions),
        "predictions": predictions,
    }


def _sufficiency_accuracy(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    values = []
    for row in rows:
        predicted = row[stage]["clarification"]["sufficiency_decision"]["level"]
        expected = row["expert_gold"]["sufficiency_decision"]
        values.append({
            "query_id": row["query_id"],
            "predicted": predicted,
            "gold": expected,
            "correct": predicted == expected,
        })
    return {
        "accuracy": sum(item["correct"] for item in values) / len(values),
        "predicted_distribution": _distribution([item["predicted"] for item in values]),
        "gold_distribution": _distribution([item["gold"] for item in values]),
        "predictions": values,
    }


def _distribution(values: Sequence[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _clarification(rows: Sequence[dict[str, Any]], stage: str, *, source_stage: str | None = None) -> dict[str, Any]:
    source = source_stage or stage
    predicted = [bool(row[source]["clarification"]["predicted_clarification"]) for row in rows]
    gold = [bool(row["expert_gold"]["should_clarify"]) for row in rows]
    tp = sum(p and g for p, g in zip(predicted, gold))
    fp = sum(p and not g for p, g in zip(predicted, gold))
    fn = sum((not p) and g for p, g in zip(predicted, gold))
    tn = sum((not p) and (not g) for p, g in zip(predicted, gold))
    return {
        "query_count": len(rows),
        "gold_clarification_count": sum(gold),
        "predicted_clarification_count": sum(predicted),
        "clarification_rate": sum(predicted) / len(predicted),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "accuracy": (tp + tn) / len(predicted),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "prediction_source_stage": source,
    }


def _stage_metrics(rows: Sequence[dict[str, Any]], stage: str, *, clarification_gate: bool = False) -> dict[str, Any]:
    candidate: list[dict[str, Any]] = []
    ranked: list[dict[str, Any]] = []
    for row in rows:
        base = row[stage]
        if clarification_gate and base["clarification"]["predicted_clarification"]:
            candidate.append(_zero_metrics())
            ranked.append(_zero_metrics())
        else:
            candidate.append(base["candidate_metrics"])
            ranked.append(base["ranked_metrics"])
    candidate_contamination: dict[str, float] = {}
    ranked_contamination: dict[str, float] = {}
    conditional_candidate_contamination: dict[str, float] = {}
    conditional_ranked_contamination: dict[str, float] = {}
    for prefix, field in (("candidate", "candidate_contamination"), ("ranked", "ranked_contamination")):
        for k in (1, 3, 5, 10, 20):
            values = []
            conditional_values = []
            for row in rows:
                abstained = clarification_gate and row[stage]["clarification"]["predicted_clarification"]
                values.append(0.0 if abstained else float(row[stage][field][f"at_{k}"]["wrong_domain_presence"]))
                if not abstained:
                    conditional_values.append(float(row[stage][field][f"at_{k}"]["wrong_domain_presence"]))
            target = candidate_contamination if prefix == "candidate" else ranked_contamination
            conditional_target = conditional_candidate_contamination if prefix == "candidate" else conditional_ranked_contamination
            target[f"wrong_domain_at_{k}"] = sum(values) / len(values)
            conditional_target[f"wrong_domain_at_{k}"] = (
                sum(conditional_values) / len(conditional_values) if conditional_values else 0.0
            )
    return {
        "candidate_recall": _average(candidate),
        "ranked_metrics": _average(ranked),
        "candidate_contamination": candidate_contamination,
        "ranked_contamination": ranked_contamination,
        "conditional_candidate_contamination_non_abstained": conditional_candidate_contamination,
        "conditional_ranked_contamination_non_abstained": conditional_ranked_contamination,
        "abstain_count": sum(
            clarification_gate and row[stage]["clarification"]["predicted_clarification"]
            for row in rows
        ),
        "conditional_candidate_recall_non_abstained": _average([
            row[stage]["candidate_metrics"]
            for row in rows
            if not (clarification_gate and row[stage]["clarification"]["predicted_clarification"])
        ]),
        "conditional_ranked_metrics_non_abstained": _average([
            row[stage]["ranked_metrics"]
            for row in rows
            if not (clarification_gate and row[stage]["clarification"]["predicted_clarification"])
        ]),
    }


def evaluate(comparison: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    gold_by_id = {str(row["query_id"]): row for row in gold["queries"]}
    rows = []
    for row in comparison["queries"]:
        query_id = str(row["query_id"])
        if query_id not in gold_by_id:
            raise ValueError(f"comparison query missing from Gold: {query_id}")
        rows.append({**row, "expert_gold": gold_by_id[query_id]})
    if len(rows) != len(gold_by_id):
        raise ValueError("Gold/comparison query counts do not match")

    stages = {
        "rule_router_v1": {"retrieval_stage": "rule_router_v1", "clarification_stage": "rule_router_v1", "gate": False},
        "expert_router_v2": {"retrieval_stage": "expert_router_v2", "clarification_stage": "expert_router_v2", "gate": False},
        "sufficiency_plus_router": {"retrieval_stage": "expert_router_v2", "clarification_stage": "expert_router_v2", "gate": True},
    }
    result_stages: dict[str, Any] = {}
    for name, config in stages.items():
        retrieval_stage = config["retrieval_stage"]
        clarification_stage = config["clarification_stage"]
        result_stages[name] = {
            "domain": _domain_accuracy(rows, retrieval_stage),
            "sufficiency": _sufficiency_accuracy(rows, clarification_stage),
            "clarification": _clarification(rows, clarification_stage),
            "retrieval": _stage_metrics(rows, retrieval_stage, clarification_gate=config["gate"]),
        }
    return {
        "evaluation_info": {
            "name": "query_sufficiency_gold_v1_evaluation",
            "version": "2026-09-21",
            "gold_source": "query_sufficiency_gold_v1_LiuWu_expert_review.json",
            "query_count": len(rows),
            "reviewer": gold.get("expert", "unknown"),
            "retrieval_comparison_source": comparison["evaluation_info"]["name"],
            "production_claim": False,
            "sufficiency_plus_router_definition": "Expert Router v2 route plus current machine sufficiency gate; insufficient machine queries abstain before retrieval.",
        },
        "gold_distribution": {
            "domain": _distribution([row["expert_gold"]["domain_decision"] for row in rows]),
            "sufficiency": _distribution([row["expert_gold"]["sufficiency_decision"] for row in rows]),
            "should_clarify": _distribution([str(row["expert_gold"]["should_clarify"]) for row in rows]),
        },
        "stages": result_stages,
        "queries": rows,
    }


def _fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Query Sufficiency Gold v1 专家评估",
        "",
        "本报告使用刘武审核的 79 条查询 Gold，比较 Rule Router v1、Expert Router v2 和 Sufficiency + Router。报告不代表生产切换。",
        "",
        "## Gold 分布",
        "",
        f"领域：`{report['gold_distribution']['domain']}`；充分性：`{report['gold_distribution']['sufficiency']}`；应澄清：`{report['gold_distribution']['should_clarify']}`。",
        "",
        "## 主要指标",
        "",
        "| 方案 | Domain Accuracy | Sufficiency Accuracy | Clarification Precision | Clarification Recall | 澄清比例 | Candidate Recall@20 | Ranked R@1 | WrongDomain@1（候选） |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (
        ("rule_router_v1", "Rule Router v1"),
        ("expert_router_v2", "Expert Router v2"),
        ("sufficiency_plus_router", "Sufficiency + Router"),
    ):
        stage = report["stages"][key]
        clarification = stage["clarification"]
        retrieval = stage["retrieval"]
        lines.append(
            f"| {label} | {stage['domain']['accuracy_all_queries']:.4f} | {stage['sufficiency']['accuracy']:.4f} | {_fmt(clarification['precision'])} | {_fmt(clarification['recall'])} | {clarification['clarification_rate']:.4f} | {retrieval['candidate_recall']['recall_at_20']:.4f} | {retrieval['ranked_metrics']['recall_at_1']:.4f} | {retrieval['candidate_contamination']['wrong_domain_at_1']:.4f} |"
        )
    lines.extend([
        "",
        "## 澄清门对检索的影响",
        "",
        "| 方案 | 澄清数 | 全量 Candidate Recall@20 | 未澄清查询 Candidate Recall@20 | 全量 Ranked R@1 | 未澄清查询 Ranked R@1 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for key, label in (
        ("rule_router_v1", "Rule Router v1"),
        ("expert_router_v2", "Expert Router v2"),
        ("sufficiency_plus_router", "Sufficiency + Router"),
    ):
        stage = report["stages"][key]
        retrieval = stage["retrieval"]
        lines.append(
            f"| {label} | {retrieval['abstain_count']} | {retrieval['candidate_recall']['recall_at_20']:.4f} | {retrieval['conditional_candidate_recall_non_abstained']['recall_at_20']:.4f} | {retrieval['ranked_metrics']['recall_at_1']:.4f} | {retrieval['conditional_ranked_metrics_non_abstained']['recall_at_1']:.4f} |"
        )
    lines.extend([
        "",
        "## 解释边界",
        "",
        "- Domain Accuracy 将 `cross_domain` 视为未提交具体领域，因此不会算作命中单领域 Gold。",
        "- Sufficiency + Router 使用机器 sufficiency gate，不把专家 Gold 直接写成运行时规则，避免评测泄漏。",
        "- Clarification 指标现在覆盖 79 条专家 Gold；与上一份 22 条 Gold 的结果不可直接混比。",
        "- WrongDomain@1 与其他检索明细保留在输入 comparison JSON 的逐查询结果中；本报告重点新增领域、充分性和澄清指标。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(_read(args.comparison), _read(args.gold))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
