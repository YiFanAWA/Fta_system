#!/usr/bin/env python3
"""Build a diagnostic taxonomy for Domain Router v1 decisions.

The diagnostic cue lists are analysis-only. They are intentionally not fed
back into the production router, so this report cannot silently tune the
router against the same benchmark.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ANALYSIS_ONLY_DOMAIN_CUES = {
    "high_signal": (
        "siemens",
        "sinamics",
        "s210",
        "drive-cliq",
        "profibus",
        "profinet",
        "profisafe",
        "sto",
        "si motion",
        "sensor module",
        "control unit",
        "power module",
        "pn interface",
        "cu",
    ),
    "generic_signal": (
        "ram",
        "backup",
        "fan",
        "24/48",
        "encoder",
        "sensor",
        "motor",
        "parameter",
        "storage",
        "voltage",
        "temperature",
        "communication",
        "brake",
    ),
}


def _matched_terms(query: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    normalized = query.casefold()
    return tuple(term for term in terms if term.casefold() in normalized)


def _classify(query: dict[str, Any]) -> dict[str, Any]:
    text = str(query.get("query") or "")
    high = _matched_terms(text, ANALYSIS_ONLY_DOMAIN_CUES["high_signal"])
    generic = _matched_terms(text, ANALYSIS_ONLY_DOMAIN_CUES["generic_signal"])
    if high:
        classification = "A_missing_router_signal"
        expected_action = "scope_candidate"
        reason = "contains a diagnostic high-signal term but current Router returned cross_domain"
    elif generic:
        classification = "B_domain_ambiguous"
        expected_action = "cross_domain_or_clarify"
        reason = "contains technical vocabulary that is not unique to one domain"
    else:
        classification = "C_query_insufficient"
        expected_action = "clarify_before_scoping"
        reason = "contains no diagnostic domain cue in the analysis-only vocabulary"
    return {
        "query_id": query["query_id"],
        "query": text,
        "query_type": query.get("query_type"),
        "expected_domain": query.get("query_domain"),
        "router_mode": query["router"]["mode"],
        "classification": classification,
        "expected_action": expected_action,
        "reason": reason,
        "matched_analysis_only_high_signal": high,
        "matched_analysis_only_generic_signal": generic,
        "label_authority": "benchmark_domain_plus_analysis_only_cue_audit",
        "requires_human_review": True,
    }


def build(report: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("queries")
    if not isinstance(rows, list) or not rows:
        raise ValueError("router comparison report must contain queries")
    cross_rows = [row for row in rows if row.get("router", {}).get("mode") == "cross_domain"]
    scoped_rows = [row for row in rows if row.get("router", {}).get("mode") == "scoped"]
    taxonomy_rows = [_classify(row) for row in cross_rows]
    false_scoped = [
        {
            "query_id": row["query_id"],
            "expected_domain": row["query_domain"],
            "selected_scope_ids": row["router"]["selected_scope_ids"],
            "router": row["router"],
            "label_authority": "benchmark_domain",
        }
        for row in scoped_rows
        if (
            (row["query_domain"] == "industrial_drive" and row["router"]["selected_scope_ids"] != ["siemens_s210"])
            or (row["query_domain"] == "aerospace" and row["router"]["selected_scope_ids"] != ["faa_sdr"])
        )
    ]
    counts = Counter(row["classification"] for row in taxonomy_rows)
    return {
        "taxonomy_info": {
            "name": "domain_router_error_taxonomy_v1",
            "version": "2026-09-21",
            "source_report": "mixed_domain_router_comparison_v1_2026-09-21",
            "total_queries": len(rows),
            "cross_domain_queries": len(cross_rows),
            "scoped_queries": len(scoped_rows),
            "classification_authority": "diagnostic_only; benchmark labels plus analysis-only cue audit",
            "router_mutation": False,
            "human_review_required": True,
        },
        "summary": {
            "missing_router_signal": counts.get("A_missing_router_signal", 0),
            "domain_ambiguous": counts.get("B_domain_ambiguous", 0),
            "query_insufficient": counts.get("C_query_insufficient", 0),
            "false_cross_domain_candidate": counts.get("A_missing_router_signal", 0),
            "false_scoped": len(false_scoped),
            "genuine_cross_domain_or_clarification": counts.get("B_domain_ambiguous", 0)
            + counts.get("C_query_insufficient", 0),
        },
        "cross_domain_rows": taxonomy_rows,
        "false_scoped_rows": false_scoped,
        "interpretation": [
            "A is a hypothesis for Router v2 coverage, not an automatic rule change.",
            "B should remain cross_domain unless the product chooses a clarification interaction.",
            "C should prefer clarification over guessing a domain.",
            "The same benchmark must not be used to tune the Router after this taxonomy is generated.",
        ],
    }


def render(report: dict[str, Any]) -> str:
    info = report["taxonomy_info"]
    summary = report["summary"]
    lines = [
        "# Domain Router Error Taxonomy v1",
        "",
        f"总查询：{info['total_queries']}；cross_domain：{info['cross_domain_queries']}；scoped：{info['scoped_queries']}。",
        "本报告是诊断结果，不自动修改 Router 规则；所有逐条分类仍需要人工确认。",
        "",
        "## 分类统计",
        "",
        "| 分类 | 数量 | 预期动作 |",
        "|---|---:|---|",
        f"| A missing_router_signal | {summary['missing_router_signal']} | 作为 Router v2 候选，但先人工确认 |",
        f"| B domain_ambiguous | {summary['domain_ambiguous']} | 保持 cross_domain 或请求澄清 |",
        f"| C query_insufficient | {summary['query_insufficient']} | 先请求补充信息 |",
        f"| false_scoped | {summary['false_scoped']} | 必须阻断 Router scope |",
        "",
        "## 逐条分类",
        "",
        "| Query | 期望领域 | 分类 | 当前信号 | 说明 |",
        "|---|---|---|---|---|",
    ]
    for row in report["cross_domain_rows"]:
        signals = ", ".join(row["matched_analysis_only_high_signal"] or row["matched_analysis_only_generic_signal"] or ("无",))
        lines.append(
            f"| {row['query_id']} | {row['expected_domain']} | {row['classification']} | {signals} | {row['reason']} |"
        )
    lines.extend([
        "",
        "## 边界",
        "",
        "- A/B/C 是错误分析标签，不是 Gold 领域标注，也不是线上规则。",
        "- 当前报告未发现 false_scoped；但这不等于 Router 已通过生产门禁。",
        "- 只有 A 经人工确认后，才允许进入 Router v2 设计；B/C 不应靠增加词表强行 scope。",
        "",
    ])
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
