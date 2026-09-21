"""Evaluate a multilingual reranker on the frozen D2 + Alarm candidate pool.

The candidate pool is read from the completed D2/Alarm experiment and is not
recomputed here.  This keeps the experiment isolated to reranking.  Two
outputs are reported:

* ``E_reranker_raw``: pure Cross-Encoder ordering;
* ``E_reranker_guarded``: the same ordering with explicit fault-code matches
  pinned first as a deterministic industrial-system safeguard.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any

from run_siemens_s210_bge_dense_ablation import _extract_fault_codes, _metrics
from run_siemens_s210_bge_hybrid_ablation import _alarm_value_section, _input_text_by_code


def _record_map(gold: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(record["fault_code"]): record
        for sample in gold["samples"]
        for record in sample.get("gold_records", [])
    }


def _candidate_text(record: dict[str, Any], alarm_section: str) -> str:
    related = ", ".join(str(value) for value in record.get("related_components") or []) or "(none)"
    causes = " | ".join(str(value) for value in record.get("causes") or []) or "(none)"
    parameters = ", ".join(str(value) for value in record.get("parameters") or []) or "(none)"
    return "\n".join([
        f"Fault code: {record.get('fault_code') or ''}",
        f"Component: {record.get('component') or '(none)'}",
        f"Related components: {related}",
        f"Description: {record.get('description') or '(none)'}",
        f"Causes: {causes}",
        f"Parameters: {parameters}",
        f"Alarm value section: {alarm_section or '(none)'}",
    ])


def _rank_by_scores(codes: list[str], scores: list[float]) -> list[str]:
    return [
        code
        for _, code in sorted(
            zip(scores, codes),
            key=lambda item: (-float(item[0]), item[1]),
        )
    ]


def _guard_explicit_fault_codes(query: str, raw_rank: list[str]) -> tuple[list[str], list[str]]:
    exact_codes = _extract_fault_codes(query)
    pinned = [code for code in raw_rank if code in exact_codes]
    remainder = [code for code in raw_rank if code not in exact_codes]
    return pinned + remainder, sorted(exact_codes)


def _method_result(
    queries: list[dict[str, Any]],
    rankings: list[list[str]],
) -> dict[str, Any]:
    from run_siemens_s210_bge_dense_ablation import _average, _group_metrics

    items = []
    for query, ranked in zip(queries, rankings):
        metric = _metrics(ranked, set(query["relevant_fault_codes"]))
        items.append({
            "query_id": query["query_id"],
            "query_type": query["query_type"],
            "difficulty": query["difficulty"],
            "ambiguity": query["ambiguity"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "top_5": ranked[:5],
            "top_10": ranked[:10],
            **metric,
        })
    return {
        "metrics": _average(items),
        "metrics_by_query_type": _group_metrics(items, "query_type"),
        "metrics_by_ambiguity": _group_metrics(items, "ambiguity"),
        "queries": items,
    }


def evaluate(
    gold: dict[str, Any],
    benchmark: dict[str, Any],
    candidate_report: dict[str, Any],
    model_name: str,
    cache_dir: str | None,
    benchmark_source: str | None = None,
    candidate_report_source: str | None = None,
) -> dict[str, Any]:
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers is required; install the retrieval environment first") from exc

    records = _record_map(gold)
    input_texts = _input_text_by_code(gold)
    queries = benchmark["queries"]
    signal_logs = candidate_report["hybrid_signal_logs"]
    if [item["query_id"] for item in signal_logs] != [query["query_id"] for query in queries]:
        raise ValueError("Candidate report query order does not match benchmark")

    candidate_pools = [list(item["candidate_pool"]) for item in signal_logs]
    pairs: list[list[str]] = []
    candidate_texts: dict[str, str] = {}
    for code, record in records.items():
        candidate_texts[code] = _candidate_text(record, _alarm_value_section(input_texts.get(code, "")))
    for query, pool in zip(queries, candidate_pools):
        pairs.extend([[str(query["query"]), candidate_texts[code]] for code in pool])

    model = CrossEncoder(model_name, max_length=512, device="cpu", cache_folder=cache_dir)
    pair_scores = model.predict(pairs, batch_size=8, show_progress_bar=True)

    raw_rankings: list[list[str]] = []
    guarded_rankings: list[list[str]] = []
    score_logs: list[dict[str, Any]] = []
    cursor = 0
    for query, pool in zip(queries, candidate_pools):
        size = len(pool)
        scores = [float(value) for value in pair_scores[cursor:cursor + size]]
        cursor += size
        raw_rank = _rank_by_scores(pool, scores)
        guarded_rank, exact_codes = _guard_explicit_fault_codes(str(query["query"]), raw_rank)
        score_by_code = dict(zip(pool, scores))
        raw_positions = {code: index + 1 for index, code in enumerate(raw_rank)}
        guarded_positions = {code: index + 1 for index, code in enumerate(guarded_rank)}
        relevant = set(query["relevant_fault_codes"])
        score_logs.append({
            "query_id": query["query_id"],
            "query": query["query"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "exact_fault_codes": exact_codes,
            "raw_first_relevant_rank": next((raw_positions[code] for code in raw_rank if code in relevant), None),
            "guarded_first_relevant_rank": next((guarded_positions[code] for code in guarded_rank if code in relevant), None),
            "candidates": [
                {
                    "fault_code": code,
                    "score": score_by_code[code],
                    "raw_rank": raw_positions[code],
                    "guarded_rank": guarded_positions[code],
                    "relevant": code in relevant,
                    "exact_fault_code_match": code in exact_codes,
                }
                for code in sorted(pool, key=lambda value: raw_positions[value])
            ],
        })
        raw_rankings.append(raw_rank)
        guarded_rankings.append(guarded_rank)

    rank_changes = []
    for candidate, raw, guarded in zip(signal_logs, raw_rankings, guarded_rankings):
        relevant = set(candidate["relevant_fault_codes"])
        rank_changes.append({
            "query_id": candidate["query_id"],
            "relevant_fault_codes": candidate["relevant_fault_codes"],
            "d2_rank": candidate["d2_rank"],
            "alarm_rank": candidate["alarm_rank"],
            "candidate_pool_size": candidate["candidate_pool_size"],
            "E_raw_rank": _metrics(raw, relevant)["first_relevant_rank"],
            "E_guarded_rank": _metrics(guarded, relevant)["first_relevant_rank"],
        })

    return {
        "evaluation_info": {
            "name": "siemens_s210_bge_reranker",
            "version": "2026-09-21",
            "model": model_name,
            "device": "cpu",
            "candidate_source": "D2 Top20 union Alarm Top10, fault_code deduplicated",
            "candidate_recall": candidate_report["candidate_pool_union"]["candidate_recall"],
            "candidate_pool_size_average": candidate_report["candidate_pool_union"]["candidate_pool_size_average"],
            "reranker_only_change": True,
            "fault_code_exact_guard_available": True,
            "gold_source": "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json",
            "benchmark_source": benchmark_source or "inline_benchmark",
            "benchmark_name": benchmark.get("dataset_info", {}).get("name"),
            "benchmark_query_count": len(queries),
            "candidate_report_source": candidate_report_source or "inline_candidate_report",
            "python": sys.version,
            "platform": platform.platform(),
        },
        "results": {
            "E_reranker_raw": _method_result(queries, raw_rankings),
            "E_reranker_guarded": _method_result(queries, guarded_rankings),
        },
        "rank_changes": rank_changes,
        "score_logs": score_logs,
    }


def render_markdown(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    lines = [
        "# Siemens S210 Reranker 精排实验报告",
        "",
        f"模型：`{info['model']}`；设备：`{info['device']}`。",
        f"候选来源：`{info['candidate_source']}`；候选召回：`{info['candidate_recall']:.4f}`；"
        f"平均候选池：{info['candidate_pool_size_average']:.2f}。",
        f"Gold、{info['benchmark_query_count']} 条查询、D2 和 Alarm 候选池均保持不变；本轮只新增 reranker。",
        "",
        "| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, result in report["results"].items():
        metrics = result["metrics"]
        lines.append(
            f"| {method} | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | "
            f"{metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | "
            f"{metrics['recall_at_20']:.4f} | {metrics['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## D2/Alarm/Reranker 排名变化",
        "",
        "`E_raw_rank` 是纯 reranker 排名；`E_guarded_rank` 在其基础上将用户明确输入的 fault_code 置顶。",
        "",
        "| Query | D2 | Alarm | E_raw | E_guarded | Pool | relevant_fault_codes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for item in report["rank_changes"]:
        def display(value: int | None) -> str:
            return str(value) if value is not None else "—"

        lines.append(
            f"| {item['query_id']} | {display(item['d2_rank'])} | {display(item['alarm_rank'])} | "
            f"{display(item['E_raw_rank'])} | {display(item['E_guarded_rank'])} | "
            f"{item['candidate_pool_size']} | {', '.join(item['relevant_fault_codes'])} |"
        )
    lines.extend([
        "",
        "## 设计说明",
        "",
        "- Reranker 输入是固定的 D2 Top20 与 Alarm Top10 去重并集，未重新召回。",
        "- `E_reranker_raw` 用于干净评估 Cross-Encoder 排序能力。",
        "- `E_reranker_guarded` 用于工业系统候选策略：明确 fault_code 时确定性置顶。",
        "- 参数、组件、description、cause、alarm section 均作为候选文本上下文，不新增固定 bonus。",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--model", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(
        json.loads(args.gold.read_text(encoding="utf-8")),
        json.loads(args.benchmark.read_text(encoding="utf-8")),
        json.loads(args.candidate_report.read_text(encoding="utf-8")),
        args.model,
        str(args.cache_dir) if args.cache_dir else None,
        str(args.benchmark),
        str(args.candidate_report),
    )
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
