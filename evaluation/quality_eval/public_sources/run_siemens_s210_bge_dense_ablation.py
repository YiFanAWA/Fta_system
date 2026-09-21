"""Run BGE-M3 dense ablations A/B/C/D for S210 retrieval.

A: description vectors only.
B: cause vectors only.
C: independent description/cause vectors fused by reciprocal rank fusion.
D: C plus fault-code exact match, parameter exact match, and component boost.

This runner deliberately does not use BGE sparse, ColBERT, or reranking.  All
final rankings are aggregated at fault_code level.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


_FAULT_CODE_RE = re.compile(r"(?<![A-Z0-9])[AFN]\d{5}(?![A-Z0-9])", re.IGNORECASE)
_PARAMETER_RE = re.compile(r"(?<![A-Z0-9])[PR]\d{4,5}(?:\[\d+\])?(?![A-Z0-9])", re.IGNORECASE)
_COMPONENT_ALIASES: dict[str, tuple[str, ...]] = {
    "控制单元": ("CU", "CONTROL UNIT", "CONTROL MODULE"),
    "液压模块": ("HYDRAULIC MODULE", "HYDRAULIC"),
    "电机模块": ("MOTOR MODULE", "MOTOR"),
    "制动组件": ("BRAKE COMPONENT", "BRAKE"),
    "编码器": ("ENCODER",),
    "传感器": ("SENSOR",),
    "功率单元": ("POWER UNIT", "POWER MODULE"),
    "电源模块": ("POWER MODULE", "POWER UNIT"),
    "DRIVE-CLiQ": ("DRIVE-CLIQ", "DRIVE CLiQ"),
}
_FAULT_CODE_BOOST = 100.0
_PARAMETER_BOOST = 0.25
_COMPONENT_BOOST = 0.05


def _load_records(gold: dict[str, Any]) -> list[dict[str, Any]]:
    records = [record for sample in gold["samples"] for record in sample.get("gold_records", [])]
    codes = [str(record.get("fault_code") or "") for record in records]
    if not all(codes) or len(set(codes)) != len(codes):
        raise ValueError("Gold must contain one unique non-empty fault_code per record")
    return records


def _cause_text(record: dict[str, Any]) -> str:
    return " ".join(str(item) for item in record.get("causes") or [])


def _normalize_parameter(value: str) -> str:
    return re.sub(r"\[\d+\]$", "", str(value).strip().upper())


def _extract_fault_codes(text: str) -> set[str]:
    return {match.upper() for match in _FAULT_CODE_RE.findall(str(text))}


def _extract_parameters(text: str) -> set[str]:
    return {_normalize_parameter(match) for match in _PARAMETER_RE.findall(str(text))}


def _record_parameters(record: dict[str, Any]) -> set[str]:
    return {_normalize_parameter(value) for value in record.get("parameters") or []}


def _record_component_text(record: dict[str, Any]) -> str:
    values = [record.get("component") or ""]
    values.extend(record.get("related_components") or [])
    return " ".join(str(value) for value in values if str(value).strip())


def _compact_component_text(value: str) -> str:
    return re.sub(r"[\s\-_]+", "", str(value).upper())


def _query_component_aliases(query: str) -> list[str]:
    query_text = str(query)
    query_upper = query_text.upper()
    query_compact = _compact_component_text(query_text)
    matches = []
    for alias, targets in _COMPONENT_ALIASES.items():
        alias_upper = alias.upper()
        if alias_upper in query_upper or _compact_component_text(alias) in query_compact:
            matches.append(alias)
    return matches


def _matched_components(query: str, record_component_text: str) -> list[str]:
    record_upper = str(record_component_text).upper()
    record_compact = _compact_component_text(record_component_text)
    matches = []
    for alias in _query_component_aliases(query):
        targets = _COMPONENT_ALIASES[alias]
        if any(target.upper() in record_upper or _compact_component_text(target) in record_compact for target in targets):
            matches.append(alias)
    return matches


def _metrics(ranked: list[str], relevant: set[str]) -> dict[str, float | int | None]:
    first_rank = next((index + 1 for index, code in enumerate(ranked) if code in relevant), None)
    return {
        "recall_at_1": float(any(code in relevant for code in ranked[:1])),
        "recall_at_3": float(any(code in relevant for code in ranked[:3])),
        "recall_at_5": float(any(code in relevant for code in ranked[:5])),
        "recall_at_10": float(any(code in relevant for code in ranked[:10])),
        "recall_at_20": float(any(code in relevant for code in ranked[:20])),
        "reciprocal_rank": 1.0 / first_rank if first_rank else 0.0,
        "first_relevant_rank": first_rank,
    }


def _average(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        return {"recall_at_1": 0.0, "recall_at_3": 0.0, "recall_at_5": 0.0, "recall_at_10": 0.0, "recall_at_20": 0.0, "mrr": 0.0}
    return {
        "recall_at_1": sum(item["recall_at_1"] for item in items) / len(items),
        "recall_at_3": sum(item["recall_at_3"] for item in items) / len(items),
        "recall_at_5": sum(item["recall_at_5"] for item in items) / len(items),
        "recall_at_10": sum(item["recall_at_10"] for item in items) / len(items),
        "recall_at_20": sum(item["recall_at_20"] for item in items) / len(items),
        "mrr": sum(item["reciprocal_rank"] for item in items) / len(items),
    }


def _rank_from_scores(scores: np.ndarray, codes: list[str]) -> list[str]:
    order = sorted(range(len(codes)), key=lambda index: (-float(scores[index]), codes[index]))
    return [codes[index] for index in order]


def _rrf_scores(description_rank: list[str], cause_rank: list[str], *, k: int = 60) -> dict[str, float]:
    scores: defaultdict[str, float] = defaultdict(float)
    for rank, code in enumerate(description_rank, start=1):
        scores[code] += 1.0 / (k + rank)
    for rank, code in enumerate(cause_rank, start=1):
        scores[code] += 1.0 / (k + rank)
    return dict(scores)


def _rrf(description_rank: list[str], cause_rank: list[str], *, k: int = 60) -> list[str]:
    scores = _rrf_scores(description_rank, cause_rank, k=k)
    return [code for code, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def _exact_hybrid_rank(
    base_rank: list[str],
    base_scores: dict[str, float],
    query: str,
    record_parameters: dict[str, set[str]],
    record_components: dict[str, str],
    enabled_signals: set[str] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    enabled = enabled_signals or {"fault_code", "parameter", "component"}
    query_codes = sorted(_extract_fault_codes(query))
    query_parameters = sorted(_extract_parameters(query))
    query_components = _query_component_aliases(query)
    base_positions = {code: index for index, code in enumerate(base_rank)}
    scores: dict[str, float] = {}
    parameter_matches: dict[str, list[str]] = {}
    component_matches: dict[str, list[str]] = {}
    bonuses_by_code: dict[str, dict[str, float]] = {}
    code_matches: list[str] = []

    for code in base_rank:
        matched_parameters = sorted(set(query_parameters) & record_parameters.get(code, set()))
        matched_component_aliases = _matched_components(query, record_components.get(code, ""))
        code_match = code in query_codes
        if code_match:
            code_matches.append(code)
        parameter_matches[code] = matched_parameters
        component_matches[code] = matched_component_aliases
        fault_code_bonus = _FAULT_CODE_BOOST if code_match and "fault_code" in enabled else 0.0
        parameter_bonus = _PARAMETER_BOOST * len(matched_parameters) if "parameter" in enabled else 0.0
        component_bonus = _COMPONENT_BOOST * len(matched_component_aliases) if "component" in enabled else 0.0
        scores[code] = base_scores[code] + fault_code_bonus + parameter_bonus + component_bonus
        bonuses_by_code[code] = {
            "fault_code": fault_code_bonus,
            "parameter": parameter_bonus,
            "component": component_bonus,
            "total": fault_code_bonus + parameter_bonus + component_bonus,
        }

    active_code_matches = set(code_matches) if "fault_code" in enabled else set()
    ranked = sorted(
        base_rank,
        key=lambda code: (
            0 if code in active_code_matches else 1,
            -scores[code],
            base_positions[code],
            code,
        ),
    )
    return ranked, {
        "query_fault_codes": query_codes,
        "query_parameters": query_parameters,
        "query_components": query_components,
        "fault_code_matches": code_matches,
        "parameter_matches": {code: values for code, values in parameter_matches.items() if values},
        "component_matches": {code: values for code, values in component_matches.items() if values},
        "bonuses_by_code": bonuses_by_code,
        "enabled_signals": sorted(enabled),
    }


def _group_metrics(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        groups[str(item[key])].append(item)
    return {group: _average(values) for group, values in sorted(groups.items())}


def evaluate(gold: dict[str, Any], benchmark: dict[str, Any], model_name: str, cache_dir: str | None) -> dict[str, Any]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - exercised in an environment check
        raise RuntimeError("sentence-transformers is required; install the retrieval environment first") from exc

    records = _load_records(gold)
    queries = benchmark["queries"]
    codes = [str(record["fault_code"]) for record in records]
    descriptions = [str(record.get("description") or "") for record in records]
    causes = [_cause_text(record) for record in records]
    query_texts = [str(query["query"]) for query in queries]

    model = SentenceTransformer(model_name, cache_folder=cache_dir, device="cpu")
    description_vectors = model.encode(
        descriptions,
        batch_size=8,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    cause_vectors = model.encode(
        causes,
        batch_size=8,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    query_vectors = model.encode(
        query_texts,
        batch_size=8,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    description_scores = np.matmul(query_vectors, description_vectors.T)
    cause_scores = np.matmul(query_vectors, cause_vectors.T)
    description_rankings = [
        _rank_from_scores(description_scores[index], codes) for index in range(len(queries))
    ]
    cause_rankings = [
        _rank_from_scores(cause_scores[index], codes) for index in range(len(queries))
    ]
    c_rankings = [
        _rrf(description_rankings[index], cause_rankings[index])
        for index in range(len(queries))
    ]
    parameters_by_code = {
        str(record["fault_code"]): _record_parameters(record) for record in records
    }
    components_by_code = {
        str(record["fault_code"]): _record_component_text(record) for record in records
    }
    d_rankings: list[list[str]] = []
    d_signals: list[dict[str, Any]] = []
    for index, query in enumerate(queries):
        description_rank = description_rankings[index]
        cause_rank = cause_rankings[index]
        base_scores = _rrf_scores(description_rank, cause_rank)
        ranked, signals = _exact_hybrid_rank(
            c_rankings[index],
            base_scores,
            str(query["query"]),
            parameters_by_code,
            components_by_code,
        )
        d_rankings.append(ranked)
        d_signals.append(signals)

    methods = {
        "A_description_dense": description_rankings,
        "B_cause_dense": cause_rankings,
        "C_description_cause_rrf": c_rankings,
        "D_exact_hybrid": d_rankings,
    }

    results: dict[str, Any] = {}
    for method, rankings in methods.items():
        items = []
        for index, (query, ranked) in enumerate(zip(queries, rankings)):
            metric = _metrics(ranked, set(query["relevant_fault_codes"]))
            item: dict[str, Any] = {
                "query_id": query["query_id"],
                "query_type": query["query_type"],
                "difficulty": query["difficulty"],
                "ambiguity": query["ambiguity"],
                "relevant_fault_codes": query["relevant_fault_codes"],
                "top_10": ranked[:10],
                **metric,
            }
            if method == "D_exact_hybrid":
                item.update(d_signals[index])
            items.append(item)
        results[method] = {
            "metrics": _average(items),
            "metrics_by_query_type": _group_metrics(items, "query_type"),
            "metrics_by_ambiguity": _group_metrics(items, "ambiguity"),
            "queries": items,
        }

    rank_changes = []
    for index, query in enumerate(queries):
        relevant = set(query["relevant_fault_codes"])
        rank_changes.append({
            "query_id": query["query_id"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "A_rank": _metrics(description_rankings[index], relevant)["first_relevant_rank"],
            "B_rank": _metrics(cause_rankings[index], relevant)["first_relevant_rank"],
            "C_rank": _metrics(c_rankings[index], relevant)["first_relevant_rank"],
            "D_rank": _metrics(d_rankings[index], relevant)["first_relevant_rank"],
        })

    return {
        "evaluation_info": {
            "name": "siemens_s210_bge_dense_ablation",
            "version": "2026-09-21",
            "model": model_name,
            "mode": "dense_only",
            "dimension": int(description_vectors.shape[1]),
            "similarity": "normalized_inner_product_equivalent_to_cosine",
            "device": "cpu",
            "ranking_unit": "fault_code",
            "rrf_k": 60,
            "hybrid_signal_weights": {
                "fault_code_exact": _FAULT_CODE_BOOST,
                "parameter_exact_each": _PARAMETER_BOOST,
                "component_each": _COMPONENT_BOOST,
            },
            "sparse_enabled": False,
            "colbert_enabled": False,
            "reranker_enabled": False,
            "gold_source": "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json",
            "benchmark_source": "evaluation/quality_eval/datasets/siemens_s210_retrieval_evaluation_v1_2026-09-21.json",
            "python": sys.version,
            "platform": platform.platform(),
        },
        "results": results,
        "rank_changes": rank_changes,
    }


def render_markdown(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    lines = [
        "# Siemens S210 BGE-M3 dense 消融实验报告",
        "",
        f"模型：`{info['model']}`；模式：`dense_only`；维度：`{info['dimension']}`；设备：`{info['device']}`。",
        "未启用 sparse、ColBERT 或 reranker；D 在 C 的 RRF 基础上加入 exact/boost 信号，排名单位为 `fault_code`。",
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
        "## 实验解释",
        "",
        "- A 只验证 description 的跨语言语义能力。",
        "- B 只验证 causes 的跨语言语义能力。",
        "- C 使用 description/cause 两路独立排序后做 RRF，不是把两段文本拼成一个向量。",
        "- D 对 query 中的故障码做强优先级，对参数做精确加权，对组件做软加权，不做硬过滤。",
        "- Recall@10 用作后续 reranker 候选召回上限，不代表 reranker 已经启用。",
        "",
        "## A/B/C/D 首个正确结果排名变化",
        "",
        "`A_rank`/`B_rank`/`C_rank`/`D_rank` 表示各方案返回列表中第一个相关故障的排名；`—` 表示未进入完整排名。",
        "",
        "| Query | A_rank | B_rank | C_rank | D_rank | relevant_fault_codes |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for item in report["rank_changes"]:
        def display_rank(value: int | None) -> str:
            return str(value) if value is not None else "—"

        lines.append(
            f"| {item['query_id']} | {display_rank(item['A_rank'])} | {display_rank(item['B_rank'])} | "
            f"{display_rank(item['C_rank'])} | {display_rank(item['D_rank'])} | "
            f"{', '.join(item['relevant_fault_codes'])} |"
        )
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
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    report = evaluate(gold, benchmark, args.model, str(args.cache_dir) if args.cache_dir else None)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
