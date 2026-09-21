"""Evaluate reproducible local retrieval baselines for the S210 benchmark.

This is a diagnostic baseline, not a production embedding or reranker.  It
uses character n-gram TF-IDF implemented with the Python standard library so
the result does not depend on an external vector package.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


CODE_RE = re.compile(r"\b[A-Za-z]\d{5}\b")
PARAM_RE = re.compile(r"\b[pr]\d{4}(?:\.\d+)?(?:\[\d+\])?\b", re.IGNORECASE)
COMPONENT_ALIASES = {
    "控制单元": "control unit",
    "电机模块": "motor module",
    "液压模块": "hydraulic module",
    "功率单元": "power module",
    "编码器": "encoder",
    "传感器": "sensor",
    "制动组件": "brake component",
    "DRIVE-CLiQ": "drive-cliq",
    "风扇": "fan",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _ngrams(text: str, min_n: int = 2, max_n: int = 5) -> Counter[str]:
    compact = re.sub(r"\s+", "", _normalize(text))
    result: Counter[str] = Counter()
    for n in range(min_n, max_n + 1):
        for index in range(0, max(0, len(compact) - n + 1)):
            result[compact[index : index + n]] += 1
    return result


def _record_text(record: dict[str, Any], mode: str) -> str:
    parts = [
        str(record.get("fault_code") or ""),
        str(record.get("component") or ""),
        " ".join(str(item) for item in record.get("related_components") or []),
        str(record.get("description") or ""),
        " ".join(str(item) for item in record.get("causes") or []),
        " ".join(str(item) for item in record.get("parameters") or []),
    ]
    if mode == "description_cause":
        parts = [parts[3], parts[4]]
    elif mode == "full":
        pass
    else:
        raise ValueError(f"unsupported mode: {mode}")
    text = " ".join(parts)
    for alias, canonical in COMPONENT_ALIASES.items():
        if alias.lower() in _normalize(text):
            text += f" {alias} {canonical}"
    return text


def _build_tfidf(documents: list[str]) -> tuple[list[dict[str, float]], dict[str, float]]:
    term_counts = [_ngrams(document) for document in documents]
    document_frequency: Counter[str] = Counter()
    for counts in term_counts:
        document_frequency.update(counts.keys())
    size = len(documents)
    idf = {
        term: math.log((size + 1) / (frequency + 1)) + 1.0
        for term, frequency in document_frequency.items()
    }
    vectors: list[dict[str, float]] = []
    for counts in term_counts:
        weighted = {term: count * idf[term] for term, count in counts.items()}
        norm = math.sqrt(sum(value * value for value in weighted.values())) or 1.0
        vectors.append({term: value / norm for term, value in weighted.items()})
    return vectors, idf


def _query_vector(query: str, idf: dict[str, float]) -> dict[str, float]:
    counts = _ngrams(query)
    weighted = {term: count * idf[term] for term, count in counts.items() if term in idf}
    norm = math.sqrt(sum(value * value for value in weighted.values())) or 1.0
    return {term: value / norm for term, value in weighted.items()}


def _cosine(query: dict[str, float], document: dict[str, float]) -> float:
    if len(query) > len(document):
        query, document = document, query
    return sum(value * document.get(term, 0.0) for term, value in query.items())


def _exact_boost(query: str, record: dict[str, Any]) -> float:
    query_normalized = _normalize(query)
    document = _record_text(record, "full")
    boost = 0.0
    for code in CODE_RE.findall(query):
        if code.lower() == str(record.get("fault_code") or "").lower():
            boost += 10.0
    for parameter in PARAM_RE.findall(query):
        if parameter.lower() in document.lower():
            boost += 1.5
    for alias, canonical in COMPONENT_ALIASES.items():
        if alias.lower() in query_normalized and canonical in document.lower():
            boost += 0.2
    return boost


def _rank(query: str, records: list[dict[str, Any]], mode: str, hybrid: bool) -> list[str]:
    documents = [_record_text(record, mode) for record in records]
    vectors, idf = _build_tfidf(documents)
    query_vector = _query_vector(query, idf)
    scored = []
    for index, record in enumerate(records):
        score = _cosine(query_vector, vectors[index])
        if hybrid:
            score += _exact_boost(query, record)
        scored.append((score, str(record["fault_code"])))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [code for _, code in scored]


def _metrics(ranked: list[str], relevant: set[str]) -> dict[str, float]:
    first_rank = next((index + 1 for index, code in enumerate(ranked) if code in relevant), None)
    return {
        "recall_at_1": float(any(code in relevant for code in ranked[:1])),
        "recall_at_3": float(any(code in relevant for code in ranked[:3])),
        "recall_at_5": float(any(code in relevant for code in ranked[:5])),
        "recall_at_10": float(any(code in relevant for code in ranked[:10])),
        "reciprocal_rank": 1.0 / first_rank if first_rank else 0.0,
        "first_relevant_rank": first_rank,
    }


def _average(items: Iterable[dict[str, Any]]) -> dict[str, float]:
    values = list(items)
    if not values:
        return {"recall_at_1": 0.0, "recall_at_3": 0.0, "recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0}
    return {
        "recall_at_1": sum(item["recall_at_1"] for item in values) / len(values),
        "recall_at_3": sum(item["recall_at_3"] for item in values) / len(values),
        "recall_at_5": sum(item["recall_at_5"] for item in values) / len(values),
        "recall_at_10": sum(item["recall_at_10"] for item in values) / len(values),
        "mrr": sum(item["reciprocal_rank"] for item in values) / len(values),
    }


def evaluate(gold: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    records = [record for sample in gold["samples"] for record in sample.get("gold_records", [])]
    if len({record.get("fault_code") for record in records}) != len(records):
        raise ValueError("retrieval ranking requires unique fault_code records")
    queries = benchmark["queries"]
    results: dict[str, Any] = {}
    for name, mode, hybrid in (
        ("baseline_a_full_record", "full", False),
        ("baseline_b_description_cause", "description_cause", False),
        ("baseline_c_hybrid", "description_cause", True),
    ):
        query_results = []
        for query in queries:
            ranked = _rank(query["query"], records, mode, hybrid)
            metric = _metrics(ranked, set(query["relevant_fault_codes"]))
            query_results.append({
                "query_id": query["query_id"],
                "query_type": query["query_type"],
                "difficulty": query["difficulty"],
                "ambiguity": query["ambiguity"],
                "relevant_fault_codes": query["relevant_fault_codes"],
                "top_5": ranked[:5],
                **metric,
            })
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_ambiguity: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in query_results:
            by_type[item["query_type"]].append(item)
            by_ambiguity[item["ambiguity"]].append(item)
        results[name] = {
            "metrics": _average(query_results),
            "metrics_by_query_type": {key: _average(value) for key, value in sorted(by_type.items())},
            "metrics_by_ambiguity": {key: _average(value) for key, value in sorted(by_ambiguity.items())},
            "queries": query_results,
        }
    return {
        "evaluation_info": {
            "name": "siemens_s210_retrieval_baseline_diagnostic",
            "version": "2026-09-21",
            "gold_source": "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json",
            "benchmark_source": "evaluation/quality_eval/datasets/siemens_s210_retrieval_evaluation_v1_2026-09-21.json",
            "ranking_unit": "fault_code",
            "vectorizer": "character_ngram_tfidf_2_to_5_standard_library",
            "not_production_embedding": True,
            "not_reranker": True,
        },
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Siemens S210 检索基线诊断报告",
        "",
        "本报告使用字符 n-gram TF-IDF，仅用于检索诊断，不代表生产 embedding、reranker 或最终 RAG 指标。",
        "排名单位为 `fault_code`，每个查询只要 Top-K 命中任一 `relevant_fault_codes` 即算命中。",
        "",
        "| 版本 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in report["results"].items():
        metrics = result["metrics"]
        lines.append(
            f"| {name} | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | "
            f"{metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | {metrics['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## 解读边界",
        "",
        "- 这是 42 条派生中文查询上的可复现实验，不是人工查询金标。",
        "- 不能根据该报告直接宣布生产检索效果，也不能据此修改 Gold。",
        "- 后续应接入真实多语言 embedding，并加入按 fault_code 聚合后的 reranker。",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    report = evaluate(gold, benchmark)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
