"""Attach explainable query-sufficiency decisions to a mixed-domain report.

This is a diagnostic layer only. It does not alter routing or retrieval and
does not claim clarification accuracy until human sufficiency labels exist.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
import sys

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from query_sufficiency import QuerySufficiencyEvaluator  # noqa: E402


def build(report: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("queries")
    if not isinstance(rows, list) or not rows:
        raise ValueError("mixed-domain report must contain queries")

    evaluator = QuerySufficiencyEvaluator()
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        router = row.get("router", {})
        decision = evaluator.assess(
            row.get("query", ""),
            domain_confidence=float(router.get("confidence", 0.0)),
            route_mode=str(router.get("mode", "cross_domain")),
        )
        output_rows.append(
            {
                "query_id": row["query_id"],
                "query": row.get("query", ""),
                "query_type": row.get("query_type"),
                "query_domain": row.get("query_domain"),
                "router_mode": router.get("mode"),
                "router_confidence": router.get("confidence", 0.0),
                "sufficiency": decision.to_dict(),
                "label_authority": "heuristic_diagnostic_only",
                "human_review_required": True,
            }
        )

    level_counts = Counter(row["sufficiency"]["level"] for row in output_rows)
    route_level_counts: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for row in output_rows:
        route_level_counts[str(row["router_mode"])][row["sufficiency"]["level"]] += 1
    clarification_count = sum(row["sufficiency"]["requires_clarification"] for row in output_rows)
    return {
        "evaluation_info": {
            "name": "mixed_domain_query_sufficiency_v1",
            "version": "2026-09-21",
            "source_report": "mixed_domain_router_comparison_v1_2026-09-21",
            "query_count": len(output_rows),
            "decision_authority": "heuristic_diagnostic_only",
            "gold_sufficiency_labels_available": False,
            "router_mutation": False,
            "retrieval_mutation": False,
            "production_claim": False,
        },
        "summary": {
            "level_counts": dict(sorted(level_counts.items())),
            "route_mode_level_counts": {
                mode: dict(sorted(counts.items())) for mode, counts in sorted(route_level_counts.items())
            },
            "clarification_rate": clarification_count / len(output_rows),
            "abstain_accuracy": None,
            "abstain_accuracy_status": "unavailable_without_human_sufficiency_labels",
        },
        "queries": output_rows,
    }


def render(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    summary = report["summary"]
    lines = [
        "# Mixed-Domain Query Sufficiency v1",
        "",
        f"查询数：{info['query_count']}。本报告只做可解释诊断，不修改 Router 或 Retrieval。",
        "",
        "## 结果",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| sufficient | {summary['level_counts'].get('sufficient', 0)} |",
        f"| partially_sufficient | {summary['level_counts'].get('partially_sufficient', 0)} |",
        f"| insufficient | {summary['level_counts'].get('insufficient', 0)} |",
        f"| Clarification Rate | {summary['clarification_rate']:.4f} |",
        "| Abstain Accuracy | N/A（缺少人工充分性金标） |",
        "",
        "## 边界",
        "",
        "- 当前等级来自规则化信息量审计，不是人工标签，不代表澄清请求一定正确。",
        "- `Clarification Rate` 是系统建议澄清的比例；`Abstain Accuracy` 必须等 Query Sufficiency Gold 建立后才能计算。",
        "- 下一步应对 low-information 查询人工确认 `sufficient / partially_sufficient / insufficient`，再比较 No Router、Rule Router v1 和 clarification 方案。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = build(json.loads(args.input.read_text(encoding="utf-8")))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render(report), encoding="utf-8")
    print(render(report))


if __name__ == "__main__":
    main()
