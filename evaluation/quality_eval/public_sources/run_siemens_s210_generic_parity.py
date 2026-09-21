"""Run the generic retrieval pipeline against the frozen S210 parity baseline.

The legacy S210 candidate and reranker reports are references only.  The new
pipeline loads the same frozen Gold through ``SiemensS210Adapter`` and runs the
domain-neutral parent loader, role channels, candidate union, and reranker.
No production API is switched by this script.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402
from siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


def _codes(entity_ids: Sequence[str]) -> list[str]:
    return [str(entity_id).rsplit(":", 1)[-1] for entity_id in entity_ids]


def _metrics(ranked: Sequence[str], relevant: set[str]) -> dict[str, Any]:
    first = next((index + 1 for index, code in enumerate(ranked) if code in relevant), None)
    return {
        "recall_at_1": float(bool(first is not None and first <= 1)),
        "recall_at_3": float(bool(first is not None and first <= 3)),
        "recall_at_5": float(bool(first is not None and first <= 5)),
        "recall_at_10": float(bool(first is not None and first <= 10)),
        "recall_at_20": float(bool(first is not None and first <= 20)),
        "reciprocal_rank": 1.0 / first if first else 0.0,
        "first_relevant_rank": first,
    }


def _average(items: Sequence[dict[str, Any]]) -> dict[str, float]:
    keys = (
        "recall_at_1",
        "recall_at_3",
        "recall_at_5",
        "recall_at_10",
        "recall_at_20",
        "reciprocal_rank",
    )
    if not items:
        return {key: 0.0 for key in keys}
    return {key: sum(float(item[key]) for item in items) / len(items) for key in keys}


def _group_metrics(items: Sequence[dict[str, Any]], field: str) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(str(item[field]), []).append(item)
    return {key: _average(values) for key, values in groups.items()}


def _method_result(queries: Sequence[dict[str, Any]], rankings: Sequence[Sequence[str]]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for query, ranking in zip(queries, rankings):
        item = {
            "query_id": query["query_id"],
            "query_type": query["query_type"],
            "difficulty": query["difficulty"],
            "ambiguity": query["ambiguity"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "top_5": list(ranking[:5]),
            "top_10": list(ranking[:10]),
        }
        item.update(_metrics(ranking, set(query["relevant_fault_codes"])))
        items.append(item)
    return {
        "metrics": _average(items),
        "metrics_by_query_type": _group_metrics(items, "query_type"),
        "metrics_by_ambiguity": _group_metrics(items, "ambiguity"),
        "queries": items,
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_difference(left: Sequence[str], right: Sequence[str]) -> dict[str, Any] | None:
    """Return the first positional difference between two stage rankings."""

    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return {
                "rank": index + 1,
                "left": left[index],
                "right": right[index],
            }
    if len(left) != len(right):
        return {
            "rank": limit + 1,
            "left": left[limit] if len(left) > limit else None,
            "right": right[limit] if len(right) > limit else None,
        }
    return None


def _legacy_stage_reference(
    query_id: str,
    legacy_candidate: dict[str, Any],
    legacy_ablation: dict[str, Any] | None,
) -> dict[str, Any]:
    """Expose only stages that were persisted by the validated legacy runs."""

    reference: dict[str, Any] = {
        "d2_top_20": list(legacy_candidate.get("candidate_pool", []))[:20],
        "alarm_top_10": list(legacy_candidate.get("alarm_top_10", []))[:10],
        "description_top_10": None,
        "cause_top_10": None,
        "rrf_top_10": None,
        "reference_status": "candidate_union_and_alarm_persisted",
    }
    if not legacy_ablation:
        reference["unavailable_stages"] = [
            "description_dense",
            "cause_dense",
            "rrf",
        ]
        return reference

    query_by_stage: dict[str, dict[str, Any]] = {}
    for stage in ("A_description_dense", "B_cause_dense", "C_description_cause_rrf"):
        rows = legacy_ablation.get("results", {}).get(stage, {}).get("queries", [])
        query_by_stage[stage] = next(
            (row for row in rows if row.get("query_id") == query_id),
            {},
        )
    reference["description_top_10"] = (
        list(query_by_stage["A_description_dense"].get("top_10", []))[:10]
        if query_by_stage["A_description_dense"] else None
    )
    reference["cause_top_10"] = (
        list(query_by_stage["B_cause_dense"].get("top_10", []))[:10]
        if query_by_stage["B_cause_dense"] else None
    )
    reference["rrf_top_10"] = (
        list(query_by_stage["C_description_cause_rrf"].get("top_10", []))[:10]
        if query_by_stage["C_description_cause_rrf"] else None
    )
    reference["reference_status"] = "top_10_for_dense_rrf_d2_and_alarm_persisted"
    reference["unavailable_stages"] = [
        "description_dense_ranks_11_plus",
        "cause_dense_ranks_11_plus",
        "rrf_ranks_11_plus",
    ]
    return reference


def evaluate(
    gold: dict[str, Any],
    benchmark: dict[str, Any],
    legacy_candidate_report: dict[str, Any],
    legacy_reranker_report: dict[str, Any],
    *,
    legacy_ablation_report: dict[str, Any] | None = None,
    embedding_model: str,
    reranker_model: str,
    cache_dir: str | None,
) -> dict[str, Any]:
    try:
        import numpy as np
        from sentence_transformers import CrossEncoder, SentenceTransformer
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("sentence-transformers and numpy are required") from exc

    adapter = SiemensS210Adapter()
    entities = adapter.parse_source(gold)
    model = SentenceTransformer(embedding_model, cache_folder=cache_dir, device="cpu")

    def encode(texts: Sequence[str]):
        return model.encode(
            list(texts),
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    reranker = CrossEncoder(
        reranker_model,
        max_length=512,
        device="cpu",
        cache_folder=cache_dir,
    )

    def rerank(pairs: Sequence[Sequence[str]]) -> Sequence[float]:
        return reranker.predict(list(pairs), batch_size=8, show_progress_bar=False)

    pipeline = GenericFaultRetrievalPipeline(adapter, entities, encode, rerank)
    queries = benchmark["queries"]
    legacy_candidates = {
        item["query_id"]: item
        for item in legacy_candidate_report["hybrid_signal_logs"]
    }
    legacy_reranked = {
        item["query_id"]: item
        for item in legacy_reranker_report["results"]["E_reranker_guarded"]["queries"]
    }

    generic_rankings: list[list[str]] = []
    generic_raw_rankings: list[list[str]] = []
    candidate_rows: list[dict[str, Any]] = []
    signal_logs: list[dict[str, Any]] = []
    candidate_set_matches = 0
    candidate_order_matches = 0
    top_matches = {1: 0, 3: 0, 5: 0, 10: 0}
    candidate_recall_hits = 0
    top1_relevant_preserved = 0
    outputs = pipeline.retrieve_many([str(query["query"]) for query in queries])
    stage_diagnostics: list[dict[str, Any]] = []
    for index, (query, output) in enumerate(zip(queries, outputs), start=1):
        generic_pool = _codes(output.candidate_pool)
        generic_guarded = _codes(output.guarded_rank)
        generic_raw = _codes(output.raw_reranker_rank)
        generic_rankings.append(generic_guarded)
        generic_raw_rankings.append(generic_raw)

        old_candidate = legacy_candidates[query["query_id"]]
        old_reranked = legacy_reranked[query["query_id"]]
        old_pool = list(old_candidate["candidate_pool"])
        old_top = list(old_reranked["top_10"])
        candidate_set_equal = set(generic_pool) == set(old_pool)
        candidate_order_equal = generic_pool == old_pool
        candidate_set_matches += int(candidate_set_equal)
        candidate_order_matches += int(candidate_order_equal)
        for top_k in top_matches:
            top_matches[top_k] += int(generic_guarded[:top_k] == old_top[:top_k])

        relevant = set(query["relevant_fault_codes"])
        candidate_recall_hits += int(bool(relevant & set(generic_pool)))
        top1_relevant_preserved += int(
            bool(generic_guarded[:1] and generic_guarded[0] in relevant)
            == bool(old_top[:1] and old_top[0] in relevant)
        )
        candidate_rows.append({
            "query_id": query["query_id"],
            "relevant_fault_codes": query["relevant_fault_codes"],
            "legacy_candidate_pool": old_pool,
            "generic_candidate_pool": generic_pool,
            "candidate_set_equal": candidate_set_equal,
            "candidate_order_equal": candidate_order_equal,
            "legacy_guarded_top_10": old_top,
            "generic_guarded_top_10": generic_guarded[:10],
            "top_k_sequence_equal": {
                str(top_k): generic_guarded[:top_k] == old_top[:top_k]
                for top_k in top_matches
            },
            "legacy_first_relevant_rank": old_reranked.get("first_relevant_rank"),
            "generic_first_relevant_rank": _metrics(generic_guarded, relevant)["first_relevant_rank"],
            "candidate_pool_added": sorted(set(generic_pool) - set(old_pool)),
            "candidate_pool_removed": sorted(set(old_pool) - set(generic_pool)),
        })
        signal_logs.append({
            "query_id": query["query_id"],
            "matched_fault_codes": list(output.exact_fields.fault_codes),
            "matched_parameters": sorted({
                parameter
                for values in output.matched_parameters_by_entity.values()
                for parameter in values
            }),
            "matched_components": list(output.exact_fields.components),
            "matched_entities_by_parameter": {
                entity_id: list(values)
                for entity_id, values in output.matched_parameters_by_entity.items()
            },
            "exact_identifier_entities": _codes(output.exact_identifier_entities),
            "parameter_bonus_by_entity": {
                _codes((entity_id,))[0]: len(values) * pipeline.config.parameter_boost
                for entity_id, values in output.matched_parameters_by_entity.items()
            },
            "stages": {
                "description_dense_top_20": _codes(output.primary_rank)[:20],
                "cause_dense_top_20": _codes(output.cause_rank)[:20],
                "rrf_top_20": _codes(output.rrf_rank)[:20],
                "d2_top_20": _codes(output.main_rank)[:20],
                "alarm_top_10": _codes(output.auxiliary_rank)[:10],
            },
            "main_rank": _codes(output.main_rank),
            "auxiliary_rank": _codes(output.auxiliary_rank),
            "candidate_pool": generic_pool,
            "candidate_pool_size": len(generic_pool),
            "raw_reranker_rank": generic_raw,
            "guarded_rank": generic_guarded,
            "reranker_scores": {
                code: output.reranker_scores[entity_id]
                for entity_id, code in zip(output.reranker_scores, _codes(output.reranker_scores.keys()))
            },
        })
        if not candidate_set_equal:
            legacy_stage = _legacy_stage_reference(
                query["query_id"],
                old_candidate,
                legacy_ablation_report,
            )
            generic_stage = {
                "description_top_10": _codes(output.primary_rank)[:10],
                "cause_top_10": _codes(output.cause_rank)[:10],
                "rrf_top_10": _codes(output.rrf_rank)[:10],
                "d2_top_20": _codes(output.main_rank)[:20],
                "alarm_top_10": _codes(output.auxiliary_rank)[:10],
            }
            stage_comparisons = {
                stage: {
                    "first_difference": (
                        _first_difference(legacy_stage[stage], generic_stage[stage])
                        if legacy_stage.get(stage) is not None else None
                    ),
                    "legacy_available": legacy_stage.get(stage) is not None,
                    "compared_depth": len(legacy_stage.get(stage) or []),
                }
                for stage in ("description_top_10", "cause_top_10", "rrf_top_10", "d2_top_20", "alarm_top_10")
            }
            first_stage = next(
                (
                    stage
                    for stage in ("description_top_10", "cause_top_10", "rrf_top_10", "d2_top_20", "alarm_top_10")
                    if stage_comparisons[stage]["legacy_available"]
                    and stage_comparisons[stage]["first_difference"] is not None
                ),
                "candidate_union",
            )
            stage_diagnostics.append({
                "query_id": query["query_id"],
                "legacy_only": sorted(set(old_pool) - set(generic_pool)),
                "generic_only": sorted(set(generic_pool) - set(old_pool)),
                "legacy": legacy_stage,
                "generic": generic_stage,
                "stage_comparisons": stage_comparisons,
                "first_stage_difference": first_stage,
                "interpretation": (
                    "legacy reference contains an empty alarm channel item;"
                    " this is an informational historical boundary difference"
                    if "N30800" in (set(old_pool) ^ set(generic_pool))
                    else "candidate boundary difference requires review"
                ),
            })
        if index % 10 == 0 or index == len(queries):
            print(f"processed {index}/{len(queries)} queries", flush=True)

    generic_result = _method_result(queries, generic_rankings)
    generic_raw_result = _method_result(queries, generic_raw_rankings)
    count = len(queries)
    old_metrics = legacy_reranker_report["results"]["E_reranker_guarded"]["metrics"]
    return {
        "evaluation_info": {
            "name": "siemens_s210_generic_retrieval_parity",
            "version": "2026-09-21",
            "pipeline": "generic parent loader + role channels + D2 Top20 union auxiliary Top10 + generic reranker",
            "adapter": "SiemensS210Adapter",
            "embedding_model": embedding_model,
            "reranker_model": reranker_model,
            "device": "cpu",
            "entity_count": len(entities),
            "benchmark_query_count": len(queries),
            "gold_source": str(ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"),
            "benchmark_source": str(ROOT / "evaluation/quality_eval/datasets/siemens_s210_retrieval_final_test_v1_2026-09-21.json"),
            "legacy_candidate_report": str(ROOT / "evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_final_test_v1_2026-09-21.json"),
            "legacy_reranker_report": str(ROOT / "evaluation/quality_eval/runs/siemens_s210_bge_reranker_final_test_v1_2026-09-21.json"),
            "legacy_ablation_report": (
                str(ROOT / "evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_ablation_d1_d3_2026-09-21.json")
                if legacy_ablation_report else None
            ),
            "python": sys.version,
            "platform": platform.platform(),
        },
        "parity": {
            "candidate_set_exact_match_rate": candidate_set_matches / count if count else 0.0,
            "candidate_order_exact_match_rate": candidate_order_matches / count if count else 0.0,
            "guarded_top_k_sequence_match_rate": {
                str(top_k): top_matches[top_k] / count if count else 0.0
                for top_k in top_matches
            },
            "candidate_set_exact_match_count": candidate_set_matches,
            "candidate_order_exact_match_count": candidate_order_matches,
            "candidate_recall": candidate_recall_hits / count if count else 0.0,
            "candidate_recall_hit_count": candidate_recall_hits,
            "top1_relevant_preserved_count": top1_relevant_preserved,
            "top1_relevant_preserved_rate": top1_relevant_preserved / count if count else 0.0,
            "stage_diagnostics_count": len(stage_diagnostics),
            "query_count": count,
        },
        "metrics": {
            "legacy_E_reranker_guarded": old_metrics,
            "generic_E_reranker_raw": generic_raw_result["metrics"],
            "generic_E_reranker_guarded": generic_result["metrics"],
        },
        "generic_results": {
            "E_reranker_raw": generic_raw_result,
            "E_reranker_guarded": generic_result,
        },
        "candidate_rows": candidate_rows,
        "signal_logs": signal_logs,
        "stage_diagnostics": stage_diagnostics,
    }


def render_markdown(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    parity = report["parity"]
    metrics = report["metrics"]
    lines = [
        "# Siemens S210 通用检索管线一致性回归报告",
        "",
        "本报告只验证通用父实体/检索/重排管线与已验证 S210 旧管线的一致性，不切换生产 API。",
        "",
        f"- Gold 实体数：{info['entity_count']}；独立测试查询：{info['benchmark_query_count']}。",
        f"- 候选集合完全一致：{parity['candidate_set_exact_match_count']}/{parity['query_count']} "
        f"（{parity['candidate_set_exact_match_rate']:.4f}）。",
        f"- 候选顺序完全一致：{parity['candidate_order_exact_match_count']}/{parity['query_count']} "
        f"（{parity['candidate_order_exact_match_rate']:.4f}）。",
        f"- 通用候选召回：{parity['candidate_recall_hit_count']}/{parity['query_count']} "
        f"（{parity['candidate_recall']:.4f}）。",
        f"- Top-1 相关性保持：{parity['top1_relevant_preserved_count']}/{parity['query_count']} "
        f"（{parity['top1_relevant_preserved_rate']:.4f}）。",
        "",
        "## 指标对比",
        "",
        "| 管线 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, values in metrics.items():
        reciprocal_rank = values.get("reciprocal_rank", values.get("mrr", 0.0))
        lines.append(
            f"| {name} | {values['recall_at_1']:.4f} | {values['recall_at_3']:.4f} | "
            f"{values['recall_at_5']:.4f} | {values['recall_at_10']:.4f} | "
            f"{values['recall_at_20']:.4f} | {reciprocal_rank:.4f} |"
        )
    lines.extend([
        "",
        "## 重排 Top-K 序列一致率",
        "",
        "| K | 完全一致率 |",
        "|---:|---:|",
    ])
    for key, value in parity["guarded_top_k_sequence_match_rate"].items():
        lines.append(f"| {key} | {value:.4f} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 候选集合一致说明通用管线没有改变召回边界；候选顺序一致说明 D2/Alarm 并集行为保持不变。",
        "- Top-K 序列一致率用于检测重排文档构造是否改变排序；即使排序存在差异，也要先看候选集合是否保持。",
        "- 只有在本报告的候选集合和指标达到既定 parity 门槛后，才允许考虑替换 S210 生产实现。",
        "- `candidate_set_exact` 与 Top-K 序列是诊断信息；旧版空告警通道或近边界顺序差异不单独阻断，只要候选召回和核心语义指标保持。",
        f"- 本次阶段差异诊断条数：{parity['stage_diagnostics_count']}；详见 JSON 的 `stage_diagnostics`。",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--legacy-candidate-report", type=Path, required=True)
    parser.add_argument("--legacy-reranker-report", type=Path, required=True)
    parser.add_argument("--legacy-ablation-report", type=Path)
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--reranker-model", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(
        _load_json(args.gold),
        _load_json(args.benchmark),
        _load_json(args.legacy_candidate_report),
        _load_json(args.legacy_reranker_report),
        legacy_ablation_report=(
            _load_json(args.legacy_ablation_report)
            if args.legacy_ablation_report else None
        ),
        embedding_model=args.embedding_model,
        reranker_model=args.reranker_model,
        cache_dir=str(args.cache_dir) if args.cache_dir else None,
    )
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
