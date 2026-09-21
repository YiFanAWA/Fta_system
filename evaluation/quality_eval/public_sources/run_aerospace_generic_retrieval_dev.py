"""Run the frozen Generic Retrieval Pipeline on the FAA SDR dev set."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402
from generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402


def _average(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"recall_at_1": 0.0, "recall_at_3": 0.0, "recall_at_5": 0.0, "recall_at_10": 0.0, "recall_at_20": 0.0, "mrr": 0.0}
    return {
        key: sum(float(row[key]) for row in rows) / len(rows)
        for key in ("recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "recall_at_20", "mrr")
    }


def _metrics(ranked: Sequence[str], relevant: set[str]) -> dict[str, Any]:
    first = next((index + 1 for index, entity_id in enumerate(ranked) if entity_id in relevant), None)
    return {
        "recall_at_1": float(first is not None and first <= 1),
        "recall_at_3": float(first is not None and first <= 3),
        "recall_at_5": float(first is not None and first <= 5),
        "recall_at_10": float(first is not None and first <= 10),
        "recall_at_20": float(first is not None and first <= 20),
        "mrr": 1.0 / first if first else 0.0,
        "first_relevant_rank": first,
    }


def _by_type(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["query_type"])].append(row)
    return {key: _average(value) for key, value in sorted(grouped.items())}


def _record_id(entity_id: str) -> str:
    return str(entity_id).rsplit(":", 1)[-1]


def _diagnostic_hint(
    relevant: set[str],
    output: Any,
) -> str:
    if relevant & set(output.candidate_pool):
        if relevant & set(output.guarded_rank[:1]):
            return "none"
        return "candidate_recalled_but_ranking_needs_review"
    channel_positions = {
        "description": {entity_id: index + 1 for index, entity_id in enumerate(output.primary_rank)},
        "cause": {entity_id: index + 1 for index, entity_id in enumerate(output.cause_rank)},
        "auxiliary": {entity_id: index + 1 for index, entity_id in enumerate(output.auxiliary_rank)},
    }
    best = {
        channel: min((positions.get(entity_id, 9999) for entity_id in relevant), default=9999)
        for channel, positions in channel_positions.items()
    }
    if min(best.values(), default=9999) < 9999:
        return "candidate_union_or_top_k_boundary_needs_review"
    return "retrieval_miss_taxonomy_unreviewed"


def run(
    sample_path: Path,
    dev_path: Path,
    model_name: str,
    reranker_name: str,
    cache_dir: Path | None,
) -> dict[str, Any]:
    try:
        import numpy as np
        from sentence_transformers import CrossEncoder, SentenceTransformer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers and numpy are required") from exc

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    benchmark = json.loads(dev_path.read_text(encoding="utf-8"))
    adapter = FaaSdrAerospaceAdapter()
    entities = adapter.parse_source(sample)
    queries = benchmark["queries"]
    embedding = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")
    reranker = CrossEncoder(reranker_name, max_length=512, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")

    def encode(texts: Sequence[str]) -> Any:
        return np.asarray(
            embedding.encode(
                list(texts),
                batch_size=8,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        )

    def rerank(pairs: Sequence[Sequence[str]]) -> Sequence[float]:
        return reranker.predict(list(pairs), batch_size=8, show_progress_bar=False)

    pipeline = GenericFaultRetrievalPipeline(adapter, entities, encode, rerank=rerank)
    outputs = pipeline.retrieve_many([str(query["query"]) for query in queries])
    entity_by_id = {entity.entity_id: entity for entity in entities}
    rows: list[dict[str, Any]] = []
    for query, output in zip(queries, outputs):
        relevant = set(query["relevant_entity_ids"])
        candidate_metrics = _metrics(output.candidate_pool, relevant)
        rank_metrics = _metrics(output.guarded_rank, relevant)
        rows.append(
            {
                "query_id": query["query_id"],
                "query": query["query"],
                "query_type": query["query_type"],
                "variant": query.get("variant", "base"),
                "difficulty": query["difficulty"],
                "ambiguity": query["ambiguity"],
                "query_sufficiency": query["query_sufficiency"],
                "sufficiency_reason": query["sufficiency_reason"],
                "relevant_entity_ids": sorted(relevant),
                "relevant_source_record_ids": sorted(_record_id(value) for value in relevant),
                "candidate_pool_size": len(output.candidate_pool),
                "candidate_metrics": candidate_metrics,
                "reranked_metrics": rank_metrics,
                "top_5_source_record_ids": [_record_id(value) for value in output.guarded_rank[:5]],
                "candidate_pool_source_record_ids": [_record_id(value) for value in output.candidate_pool],
                "exact_fields": {
                    "fault_codes": list(output.exact_fields.fault_codes),
                    "parameters": list(output.exact_fields.parameters),
                    "components": list(output.exact_fields.components),
                },
                "matched_parameters_by_entity": {
                    _record_id(entity_id): list(values)
                    for entity_id, values in output.matched_parameters_by_entity.items()
                },
                "exact_identifier_source_record_ids": [_record_id(value) for value in output.exact_identifier_entities],
                "diagnostic_hint": _diagnostic_hint(relevant, output),
                "taxonomy_status": "unreviewed",
                "stage_top_entity_ids": {
                    "description_top_5": list(output.primary_rank[:5]),
                    "cause_top_5": list(output.cause_rank[:5]),
                    "auxiliary_top_5": list(output.auxiliary_rank[:5]),
                    "d2_top_5": list(output.main_rank[:5]),
                },
            }
        )

    try:
        sample_source = str(sample_path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        sample_source = str(sample_path)
    try:
        benchmark_source = str(dev_path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        benchmark_source = str(dev_path)
    return {
        "evaluation_info": {
            "name": "aerospace_generic_retrieval_dev_v1",
            "version": "2026-09-21",
            "sample_source": sample_source,
            "benchmark_source": benchmark_source,
            "embedding_model": model_name,
            "reranker_model": reranker_name,
            "device": "cpu",
            "pipeline": "Generic Retrieval Pipeline v1; D2 Top20 union auxiliary Top10; entity_id aggregation",
            "production_claim": False,
            "query_annotation_authority": benchmark["dataset_info"]["annotation_authority"],
            "taxonomy_status": "unreviewed; diagnostics only",
            "python": sys.version,
            "platform": platform.platform(),
        },
        "candidate_recall": {
            "metrics": _average([row["candidate_metrics"] for row in rows]),
            "metrics_by_query_type": _by_type([
                {**row["candidate_metrics"], "query_type": row["query_type"]} for row in rows
            ]),
            "metrics_by_sufficiency": _by_type([
                {**row["candidate_metrics"], "query_type": row["query_sufficiency"]} for row in rows
            ]),
            "metrics_by_variant": _by_type([
                {**row["candidate_metrics"], "query_type": row["variant"]} for row in rows
            ]),
        },
        "reranked": {
            "metrics": _average([row["reranked_metrics"] for row in rows]),
            "metrics_by_query_type": _by_type([
                {**row["reranked_metrics"], "query_type": row["query_type"]} for row in rows
            ]),
            "metrics_by_sufficiency": _by_type([
                {**row["reranked_metrics"], "query_type": row["query_sufficiency"]} for row in rows
            ]),
            "metrics_by_variant": _by_type([
                {**row["reranked_metrics"], "query_type": row["variant"]} for row in rows
            ]),
        },
        "error_taxonomy": {
            "status": "unreviewed",
            "allowed_categories": ["adapter_mapping", "schema_gap", "retrieval_role", "chunk", "generic_contract"],
            "rows_requiring_review": [row["query_id"] for row in rows if row["diagnostic_hint"] != "none"],
        },
        "queries": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    candidate = report["candidate_recall"]["metrics"]
    reranked = report["reranked"]["metrics"]
    lines = [
        "# Aerospace Generic Retrieval Dev v1",
        "",
        "本报告运行冻结的 Generic Retrieval Pipeline v1，不代表航空专家金标或最终泛化成绩。查询标签由公开样本确定性派生，错误分类状态保持 `unreviewed`。",
        "",
        "## 总体指标",
        "",
        "| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Candidate Union | {candidate['recall_at_1']:.4f} | {candidate['recall_at_3']:.4f} | {candidate['recall_at_5']:.4f} | {candidate['recall_at_10']:.4f} | {candidate['recall_at_20']:.4f} | {candidate['mrr']:.4f} |",
        f"| Reranked | {reranked['recall_at_1']:.4f} | {reranked['recall_at_3']:.4f} | {reranked['recall_at_5']:.4f} | {reranked['recall_at_10']:.4f} | {reranked['recall_at_20']:.4f} | {reranked['mrr']:.4f} |",
        "",
        "## 按查询类型",
        "",
        "| 类型 | Candidate R@20 | Reranked R@1 | Reranked MRR |",
        "|---|---:|---:|---:|",
    ]
    candidate_by_type = report["candidate_recall"]["metrics_by_query_type"]
    reranked_by_type = report["reranked"]["metrics_by_query_type"]
    for query_type in sorted(candidate_by_type):
        lines.append(
            f"| {query_type} | {candidate_by_type[query_type]['recall_at_20']:.4f} | "
            f"{reranked_by_type[query_type]['recall_at_1']:.4f} | {reranked_by_type[query_type]['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## 按查询充分性",
        "",
        "| 充分性 | Candidate R@20 | Reranked R@1 | Reranked MRR |",
        "|---|---:|---:|---:|",
    ])
    candidate_by_sufficiency = report["candidate_recall"]["metrics_by_sufficiency"]
    reranked_by_sufficiency = report["reranked"]["metrics_by_sufficiency"]
    for sufficiency in sorted(candidate_by_sufficiency):
        lines.append(
            f"| {sufficiency} | {candidate_by_sufficiency[sufficiency]['recall_at_20']:.4f} | "
            f"{reranked_by_sufficiency[sufficiency]['recall_at_1']:.4f} | {reranked_by_sufficiency[sufficiency]['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## 按查询版本",
        "",
        "| 版本 | Candidate R@20 | Reranked R@1 | Reranked MRR |",
        "|---|---:|---:|---:|",
    ])
    candidate_by_variant = report["candidate_recall"]["metrics_by_variant"]
    reranked_by_variant = report["reranked"]["metrics_by_variant"]
    for variant in sorted(candidate_by_variant):
        lines.append(
            f"| {variant} | {candidate_by_variant[variant]['recall_at_20']:.4f} | "
            f"{reranked_by_variant[variant]['recall_at_1']:.4f} | {reranked_by_variant[variant]['mrr']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- `candidate_recall` 只说明正确实体是否进入候选池；不能说明查询标签是专家确认的。",
            "- `diagnostic_hint` 只是定位线索，所有错误分类仍需人工/工程复核；本轮不自动把失败归因到 Generic Pipeline。",
            "- 如需改变公共 Schema、Adapter Contract 或 Generic Pipeline，必须先完成错误分类并新增相应回归门禁。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--reranker", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.sample, args.dev, args.model, args.reranker, args.cache_dir)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
