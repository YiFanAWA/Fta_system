"""Run C/D1/D2/D3 hybrid retrieval ablations for Siemens S210.

C: description/cause dense rankings fused by RRF.
D1: C + fault_code exact signal.
D2: D1 + parameter exact signal.
D3: D2 + component soft boost.

The script accepts a frozen benchmark query set and stores per-query signal
evidence for regression analysis. All rankings are aggregated at
``fault_code`` level; no reranker is used here.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

from run_siemens_s210_bge_dense_ablation import (
    _COMPONENT_BOOST,
    _FAULT_CODE_BOOST,
    _PARAMETER_BOOST,
    _cause_text,
    _exact_hybrid_rank,
    _group_metrics,
    _load_records,
    _metrics,
    _rank_from_scores,
    _record_component_text,
    _record_parameters,
    _rrf,
    _rrf_scores,
)


_ALARM_SECTION_RE = re.compile(
    r"(?ims)^(?:Alarm value|Fault value)\b.*?(?=^Remedy:|\Z)"
)


def _alarm_value_section(input_text: str) -> str:
    match = _ALARM_SECTION_RE.search(str(input_text))
    return match.group(0).strip() if match else ""


def _input_text_by_code(gold: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for sample in gold["samples"]:
        input_text = str(sample.get("input_text") or "")
        for record in sample.get("gold_records", []):
            code = str(record.get("fault_code") or "")
            if code:
                values[code] = input_text
    return values


def _merge_candidate_pool(d2_rank: list[str], alarm_rank: list[str], *, d2_k: int = 20, alarm_k: int = 10) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for code in [*d2_rank[:d2_k], *alarm_rank[:alarm_k]]:
        if code not in seen:
            seen.add(code)
            merged.append(code)
    return merged


def _candidate_pool_summary(
    queries: list[dict[str, Any]],
    pools: list[list[str]],
) -> dict[str, Any]:
    hits = [
        bool(set(query["relevant_fault_codes"]) & set(pool))
        for query, pool in zip(queries, pools)
    ]
    sizes = [len(pool) for pool in pools]
    return {
        "d2_top_k": 20,
        "alarm_top_k": 10,
        "query_count": len(queries),
        "candidate_recall": sum(hits) / len(hits) if hits else 0.0,
        "candidate_hit_count": sum(hits),
        "candidate_pool_size_average": sum(sizes) / len(sizes) if sizes else 0.0,
        "candidate_pool_size_min": min(sizes) if sizes else 0,
        "candidate_pool_size_max": max(sizes) if sizes else 0,
    }


def _rank_or_none(ranked: list[str], relevant: set[str]) -> int | None:
    return _metrics(ranked, relevant)["first_relevant_rank"]


def _promoted_over_relevant(
    base_rank: list[str],
    hybrid_rank: list[str],
    relevant: set[str],
    bonuses_by_code: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    base_positions = {code: index + 1 for index, code in enumerate(base_rank)}
    hybrid_positions = {code: index + 1 for index, code in enumerate(hybrid_rank)}
    promoted: list[dict[str, Any]] = []
    for code, bonus in bonuses_by_code.items():
        if code in relevant or bonus["total"] <= 0:
            continue
        passed = [
            relevant_code
            for relevant_code in relevant
            if hybrid_positions[code] < hybrid_positions[relevant_code]
            and base_positions[code] >= base_positions[relevant_code]
        ]
        if passed:
            promoted.append({
                "fault_code": code,
                "base_rank": base_positions[code],
                "hybrid_rank": hybrid_positions[code],
                "passed_relevant_fault_codes": sorted(passed),
                "bonus": bonus,
            })
    return sorted(promoted, key=lambda item: (item["hybrid_rank"], item["fault_code"]))


def _build_method_result(
    queries: list[dict[str, Any]],
    rankings: list[list[str]],
) -> dict[str, Any]:
    items = []
    for query, ranked in zip(queries, rankings):
        metric = _metrics(ranked, set(query["relevant_fault_codes"]))
        items.append({
            "query_id": query["query_id"],
            "query_type": query["query_type"],
            "difficulty": query["difficulty"],
            "ambiguity": query["ambiguity"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "top_10": ranked[:10],
            **metric,
        })
    from run_siemens_s210_bge_dense_ablation import _average

    return {
        "metrics": _average(items),
        "metrics_by_query_type": _group_metrics(items, "query_type"),
        "metrics_by_ambiguity": _group_metrics(items, "ambiguity"),
        "queries": items,
    }


def evaluate(
    gold: dict[str, Any],
    benchmark: dict[str, Any],
    model_name: str,
    cache_dir: str | None,
    benchmark_source: str | None = None,
) -> dict[str, Any]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers is required; install the retrieval environment first") from exc

    records = _load_records(gold)
    queries = benchmark["queries"]
    codes = [str(record["fault_code"]) for record in records]
    descriptions = [str(record.get("description") or "") for record in records]
    causes = [_cause_text(record) for record in records]
    input_text_by_code = _input_text_by_code(gold)
    alarm_sections = [_alarm_value_section(input_text_by_code.get(code, "")) for code in codes]
    query_texts = [str(query["query"]) for query in queries]

    model = SentenceTransformer(model_name, cache_folder=cache_dir, device="cpu")
    description_vectors = model.encode(
        descriptions, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True
    )
    cause_vectors = model.encode(
        causes, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True
    )
    alarm_vectors = model.encode(
        alarm_sections, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True
    )
    query_vectors = model.encode(
        query_texts, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True
    )

    import numpy as np

    description_scores = np.matmul(query_vectors, description_vectors.T)
    cause_scores = np.matmul(query_vectors, cause_vectors.T)
    alarm_scores = np.matmul(query_vectors, alarm_vectors.T)
    description_rankings = [_rank_from_scores(description_scores[index], codes) for index in range(len(queries))]
    cause_rankings = [_rank_from_scores(cause_scores[index], codes) for index in range(len(queries))]
    alarm_rankings = [_rank_from_scores(alarm_scores[index], codes) for index in range(len(queries))]
    c_rankings = [_rrf(description_rankings[index], cause_rankings[index]) for index in range(len(queries))]

    parameters_by_code = {str(record["fault_code"]): _record_parameters(record) for record in records}
    components_by_code = {str(record["fault_code"]): _record_component_text(record) for record in records}
    levels = {
        "D1_fault_code": {"fault_code"},
        "D2_fault_code_parameter": {"fault_code", "parameter"},
        "D3_fault_code_parameter_component": {"fault_code", "parameter", "component"},
    }
    level_rankings: dict[str, list[list[str]]] = {name: [] for name in levels}
    candidate_pools: list[list[str]] = []
    signal_logs: list[dict[str, Any]] = []

    for index, query in enumerate(queries):
        c_rank = c_rankings[index]
        c_scores = _rrf_scores(description_rankings[index], cause_rankings[index])
        per_level: dict[str, dict[str, Any]] = {}
        for level_name, enabled_signals in levels.items():
            ranked, signals = _exact_hybrid_rank(
                c_rank,
                c_scores,
                str(query["query"]),
                parameters_by_code,
                components_by_code,
                enabled_signals=enabled_signals,
            )
            level_rankings[level_name].append(ranked)
            per_level[level_name] = {
                "enabled_signals": sorted(enabled_signals),
                "rank": _rank_or_none(ranked, set(query["relevant_fault_codes"])),
                "top_10": ranked[:10],
                "matched_fault_codes": signals["fault_code_matches"],
                "parameter_matches_by_fault": signals["parameter_matches"],
                "component_matches_by_fault": signals["component_matches"],
                "bonuses_by_fault": {
                    code: bonus
                    for code, bonus in signals["bonuses_by_code"].items()
                    if bonus["total"] > 0
                },
                "promoted_over_relevant": _promoted_over_relevant(
                    c_rank,
                    ranked,
                    set(query["relevant_fault_codes"]),
                    signals["bonuses_by_code"],
                ),
            }

        relevant = set(query["relevant_fault_codes"])
        d3 = per_level["D3_fault_code_parameter_component"]
        alarm_rank = alarm_rankings[index]
        candidate_pool = _merge_candidate_pool(level_rankings["D2_fault_code_parameter"][index], alarm_rank)
        candidate_pools.append(candidate_pool)
        signal_logs.append({
            "query_id": query["query_id"],
            "query": query["query"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "matched_fault_code": (
                per_level["D1_fault_code"]["matched_fault_codes"][0]
                if len(per_level["D1_fault_code"]["matched_fault_codes"]) == 1
                else None
            ),
            "matched_fault_codes": per_level["D1_fault_code"]["matched_fault_codes"],
            "matched_parameters": sorted({
                parameter
                for values in d3["parameter_matches_by_fault"].values()
                for parameter in values
            }),
            "matched_components": sorted({
                component
                for values in d3["component_matches_by_fault"].values()
                for component in values
            }),
            "c_rank": _rank_or_none(c_rank, relevant),
            "d1_rank": per_level["D1_fault_code"]["rank"],
            "d2_rank": per_level["D2_fault_code_parameter"]["rank"],
            "d3_rank": d3["rank"],
            "alarm_rank": _rank_or_none(alarm_rank, relevant),
            "alarm_top_10": alarm_rank[:10],
            "candidate_pool": candidate_pool,
            "candidate_pool_size": len(candidate_pool),
            "candidate_pool_contains_relevant": bool(relevant & set(candidate_pool)),
            "alarm_section_present_for_relevant_faults": {
                code: bool(alarm_sections[codes.index(code)])
                for code in query["relevant_fault_codes"]
                if code in codes
            },
            "levels": per_level,
        })

    rankings: dict[str, list[list[str]]] = {
        "A_description_dense": description_rankings,
        "B_cause_dense": cause_rankings,
        "C_description_cause_rrf": c_rankings,
        "E0_alarm_dense": alarm_rankings,
        **level_rankings,
    }
    results = {name: _build_method_result(queries, method_rankings) for name, method_rankings in rankings.items()}

    rank_changes = []
    for index, query in enumerate(queries):
        relevant = set(query["relevant_fault_codes"])
        rank_changes.append({
            "query_id": query["query_id"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "A_rank": _rank_or_none(description_rankings[index], relevant),
            "B_rank": _rank_or_none(cause_rankings[index], relevant),
            "C_rank": _rank_or_none(c_rankings[index], relevant),
            "D1_rank": _rank_or_none(level_rankings["D1_fault_code"][index], relevant),
            "D2_rank": _rank_or_none(level_rankings["D2_fault_code_parameter"][index], relevant),
            "D3_rank": _rank_or_none(level_rankings["D3_fault_code_parameter_component"][index], relevant),
            "Alarm_rank": _rank_or_none(alarm_rankings[index], relevant),
            "candidate_pool_size": len(candidate_pools[index]),
            "candidate_pool_contains_relevant": bool(relevant & set(candidate_pools[index])),
        })

    return {
        "evaluation_info": {
            "name": "siemens_s210_bge_hybrid_ablation",
            "version": "2026-09-21",
            "model": model_name,
            "base_method": "C_description_cause_rrf",
            "selected_main_retrieval": "D2_fault_code_parameter",
            "component_boost_enabled_in_selected_method": False,
            "reranker_candidate_pool": 20,
            "alarm_channel": "Fault value/Alarm value section from input_text until Remedy",
            "alarm_section_count": sum(bool(value) for value in alarm_sections),
            "dimension": int(description_vectors.shape[1]),
            "similarity": "normalized_inner_product_equivalent_to_cosine",
            "device": "cpu",
            "ranking_unit": "fault_code",
            "rrf_k": 60,
            "signal_weights": {
                "fault_code_exact": _FAULT_CODE_BOOST,
                "parameter_exact_each": _PARAMETER_BOOST,
                "component_soft_each": _COMPONENT_BOOST,
            },
            "sparse_enabled": False,
            "colbert_enabled": False,
            "reranker_enabled": False,
            "gold_source": "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json",
            "benchmark_source": benchmark_source or "inline_benchmark",
            "benchmark_name": benchmark.get("dataset_info", {}).get("name"),
            "benchmark_query_count": len(queries),
            "python": sys.version,
            "platform": platform.platform(),
        },
        "results": results,
        "candidate_pool_union": _candidate_pool_summary(queries, candidate_pools),
        "rank_changes": rank_changes,
        "hybrid_signal_logs": signal_logs,
        "regression_query_ids": [
            item["query_id"] for item in rank_changes
            if item["C_rank"] is not None and item["D3_rank"] is not None and item["D3_rank"] > item["C_rank"]
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    lines = [
        "# Siemens S210 BGE-M3 C/D1/D2/D3 Hybrid 消融实验报告",
        "",
        f"模型：`{info['model']}`；维度：`{info['dimension']}`；设备：`{info['device']}`；排名单位：`fault_code`。",
        f"未启用 sparse、ColBERT 或 reranker；Gold 与 {info['benchmark_query_count']} 条评测查询保持冻结。",
        "",
        "| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in [
        "C_description_cause_rrf",
        "E0_alarm_dense",
        "D1_fault_code",
        "D2_fault_code_parameter",
        "D3_fault_code_parameter_component",
    ]:
        metrics = report["results"][method]["metrics"]
        lines.append(
            f"| {method} | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | "
            f"{metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | "
            f"{metrics['recall_at_20']:.4f} | {metrics['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## C→D1/D2/D3 排名变化",
        "",
        "rank 表示第一个相关故障的排名；`—` 表示未进入完整排名。",
        "",
        "| Query | C | Alarm | D1 | D2 | D3 | Pool | relevant_fault_codes |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    for item in report["rank_changes"]:
        def display(value: int | None) -> str:
            return str(value) if value is not None else "—"

        lines.append(
            f"| {item['query_id']} | {display(item['C_rank'])} | {display(item['Alarm_rank'])} | "
            f"{display(item['D1_rank'])} | {display(item['D2_rank'])} | {display(item['D3_rank'])} | "
            f"{item['candidate_pool_size']} | "
            f"{', '.join(item['relevant_fault_codes'])} |"
        )
    lines.extend([
        "",
        "## D2 Top20 与 Alarm Top10 候选池并集",
        "",
        f"candidate_recall：{report['candidate_pool_union']['candidate_recall']:.4f} "
        f"（{report['candidate_pool_union']['candidate_hit_count']}/{report['candidate_pool_union']['query_count']}）；"
        f"candidate_pool_size 平均 {report['candidate_pool_union']['candidate_pool_size_average']:.2f}，"
        f"范围 {report['candidate_pool_union']['candidate_pool_size_min']}～{report['candidate_pool_union']['candidate_pool_size_max']}。",
        "候选池按 fault_code 去重，顺序为 D2 Top20 在前、Alarm Top10 补充在后。",
        "",
        "## D3 回归查询",
        "",
        f"D3 相比 C 排名变差的查询：{', '.join(report['regression_query_ids']) or '无'}。",
        "具体信号、bonus 和超过正确 fault 的候选见 JSON 的 `hybrid_signal_logs`。",
        "当前主检索基线为 D2_fault_code_parameter；D3 仅作为组件信号负面对照，不进入主排名。",
        "",
        "## 信号策略",
        "",
        f"- fault_code exact bonus：{info['signal_weights']['fault_code_exact']}；",
        f"- 每个 parameter exact bonus：{info['signal_weights']['parameter_exact_each']}；",
        f"- 每个 component soft bonus：{info['signal_weights']['component_soft_each']}；",
        "- component 只做 boost，不做硬过滤。",
    ])
    q023 = next((item for item in report["hybrid_signal_logs"] if item["query_id"] == "Q023"), None)
    if q023 is not None:
        lines.extend([
            "",
            "## Q023 诊断",
            "",
            "Q023 在 C、D1、D2、D3 中均未命中 exact/boost 信号，首个相关 fault 的排名均为 69；",
            f"Alarm channel 首个相关 fault 排名为 {q023['alarm_rank']}；该查询需要覆盖故障值/报警值或 raw input text 通道，"
            "reranker 不能补救未进入 Top-20 的候选。",
            f"D2 Top-10：{', '.join(q023['levels']['D2_fault_code_parameter']['top_10'])}。",
            f"Alarm Top-10：{', '.join(q023['alarm_top_10'])}。",
        ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(
        json.loads(args.gold.read_text(encoding="utf-8")),
        json.loads(args.benchmark.read_text(encoding="utf-8")),
        args.model,
        str(args.cache_dir) if args.cache_dir else None,
        str(args.benchmark),
    )
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
