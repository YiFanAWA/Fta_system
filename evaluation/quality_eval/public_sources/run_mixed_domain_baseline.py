"""Run a no-router Siemens + Aerospace mixed-index baseline.

The composition adapter lives in this evaluation harness, not in the generic
retrieval core.  This keeps the experiment from adding a production domain
router or domain-specific branches before contamination is measured.
"""

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

from domains.aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402
from contracts.domain_adapter_contract import ExactFieldMatches, RetrievalChunk, RetrievalFieldValues  # noqa: E402
from rag.generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402
from domains.siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


class MixedDomainEvaluationAdapter:
    """Compose two existing adapters without changing the shared contract."""

    def __init__(self, siemens: SiemensS210Adapter, aerospace: FaaSdrAerospaceAdapter) -> None:
        self._siemens = siemens
        self._aerospace = aerospace

    def parse_source(self, payload: dict[str, Any]):  # pragma: no cover - harness only
        raise NotImplementedError("mixed evaluation loads each source through its own adapter")

    def normalize_entity(self, entity):
        return self._delegate(entity).normalize_entity(entity)

    def build_retrieval_chunks(self, entities: Sequence[Any]) -> tuple[RetrievalChunk, ...]:
        result: list[RetrievalChunk] = []
        for entity in entities:
            result.extend(self._delegate(entity).build_retrieval_chunks([entity]))
        return tuple(result)

    def extract_exact_fields(self, question: str) -> ExactFieldMatches:
        left = self._siemens.extract_exact_fields(question)
        right = self._aerospace.extract_exact_fields(question)
        return ExactFieldMatches(
            fault_codes=tuple(dict.fromkeys((*left.fault_codes, *right.fault_codes))),
            parameters=tuple(dict.fromkeys((*left.parameters, *right.parameters))),
            components=tuple(dict.fromkeys((*left.components, *right.components))),
        )

    def retrieval_field_values(self, entity) -> RetrievalFieldValues:
        return self._delegate(entity).retrieval_field_values(entity)

    def _delegate(self, entity):
        if entity.domain == self._siemens.domain:
            return self._siemens
        if entity.domain == self._aerospace.domain:
            return self._aerospace
        raise ValueError(f"unsupported mixed-domain entity: {entity.domain}")


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


def _average(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"recall_at_1": 0.0, "recall_at_3": 0.0, "recall_at_5": 0.0, "recall_at_10": 0.0, "recall_at_20": 0.0, "mrr": 0.0}
    return {
        key: sum(float(row[key]) for row in rows) / len(rows)
        for key in ("recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "recall_at_20", "mrr")
    }


def _domain_metrics(rows: Sequence[dict[str, Any]], field: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return {key: _average(values) for key, values in sorted(grouped.items())}


def _domain_quality(ranking: Sequence[str], expected_domain: str, domain_by_entity: dict[str, str], top_k: int) -> dict[str, float]:
    top = list(ranking[:top_k])
    if not top:
        return {"wrong_domain_presence": 0.0, "domain_purity": 0.0}
    wrong = [entity_id for entity_id in top if domain_by_entity[entity_id] != expected_domain]
    return {
        "wrong_domain_presence": float(bool(wrong)),
        "domain_purity": sum(domain_by_entity[entity_id] == expected_domain for entity_id in top) / len(top),
    }


def _load_queries(siemens_eval: dict[str, Any], aerospace_dev: dict[str, Any]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    for query in siemens_eval["queries"]:
        queries.append({
            "query_id": f"S210-{query['query_id']}",
            "query": query["query"],
            "query_type": query["query_type"],
            "query_domain": "industrial_drive",
            "relevant_entity_ids": [f"industrial-drive:siemens:s210:{code.upper()}" for code in query["relevant_fault_codes"]],
            "source_benchmark": "siemens_s210_retrieval_final_test_v1",
        })
    for query in aerospace_dev["queries"]:
        queries.append({
            "query_id": query["query_id"],
            "query": query["query"],
            "query_type": query["query_type"],
            "query_domain": "aerospace",
            "relevant_entity_ids": list(query["relevant_entity_ids"]),
            "source_benchmark": "aerospace_retrieval_dev_v1",
        })
    return queries


def run(
    s210_gold_path: Path,
    aerospace_sample_path: Path,
    s210_eval_path: Path,
    aerospace_dev_path: Path,
    model_name: str,
    cache_dir: Path | None,
    with_reranker: bool,
    reranker_name: str,
) -> dict[str, Any]:
    try:
        import numpy as np
        from sentence_transformers import CrossEncoder, SentenceTransformer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers and numpy are required") from exc

    s210_adapter = SiemensS210Adapter()
    aerospace_adapter = FaaSdrAerospaceAdapter()
    s210_entities = s210_adapter.parse_file(s210_gold_path)
    aerospace_entities = aerospace_adapter.parse_file(aerospace_sample_path)
    entities = (*s210_entities, *aerospace_entities)
    adapter = MixedDomainEvaluationAdapter(s210_adapter, aerospace_adapter)
    s210_eval = json.loads(s210_eval_path.read_text(encoding="utf-8"))
    aerospace_dev = json.loads(aerospace_dev_path.read_text(encoding="utf-8"))
    queries = _load_queries(s210_eval, aerospace_dev)

    embedding = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")

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

    rerank = None
    if with_reranker:
        model = CrossEncoder(reranker_name, max_length=512, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")

        def rerank(pairs: Sequence[Sequence[str]]) -> Sequence[float]:
            return model.predict(list(pairs), batch_size=8, show_progress_bar=False)

    pipeline = GenericFaultRetrievalPipeline(adapter, entities, encode, rerank=rerank)
    outputs = pipeline.retrieve_many([query["query"] for query in queries])
    domain_by_entity = {entity.entity_id: entity.domain for entity in entities}
    rows: list[dict[str, Any]] = []
    for query, output in zip(queries, outputs):
        relevant = set(query["relevant_entity_ids"])
        ranking = output.guarded_rank
        rows.append({
            "query_id": query["query_id"],
            "query": query["query"],
            "query_type": query["query_type"],
            "query_domain": query["query_domain"],
            "relevant_entity_ids": sorted(relevant),
            "candidate_pool_size": len(output.candidate_pool),
            "candidate_metrics": _metrics(output.candidate_pool, relevant),
            "ranked_metrics": _metrics(ranking, relevant),
            "candidate_wrong_domain": {
                f"at_{k}": _domain_quality(output.candidate_pool, query["query_domain"], domain_by_entity, k)
                for k in (1, 3, 5)
            },
            "ranked_wrong_domain": {
                f"at_{k}": _domain_quality(ranking, query["query_domain"], domain_by_entity, k)
                for k in (1, 3, 5)
            },
            "top_5": [
                {"entity_id": entity_id, "domain": domain_by_entity[entity_id]}
                for entity_id in ranking[:5]
            ],
            "taxonomy_status": "unreviewed",
        })

    def contamination(stage: str) -> dict[str, float]:
        values: dict[str, float] = {}
        for k in (1, 3, 5):
            key = f"at_{k}"
            values[f"wrong_domain_at_{k}"] = sum(row[stage][key]["wrong_domain_presence"] for row in rows) / len(rows)
            values[f"domain_purity_at_{k}"] = sum(row[stage][key]["domain_purity"] for row in rows) / len(rows)
        return values

    return {
        "evaluation_info": {
            "name": "mixed_domain_retrieval_baseline_v1",
            "version": "2026-09-21",
            "domains": ["industrial_drive/Siemens/S210", "aerospace/FAA_SDR"],
            "entity_count": len(entities),
            "query_count": len(queries),
            "embedding_model": model_name,
            "reranker_model": reranker_name if with_reranker else None,
            "router": "none",
            "candidate_pool": "D2 Top20 union auxiliary Top10, entity_id deduplicated",
            "production_claim": False,
            "query_annotation_authority": "S210 frozen derived benchmark + aerospace public-row derived dev labels",
            "taxonomy_status": "unreviewed",
            "python": sys.version,
            "platform": platform.platform(),
        },
        "candidate_recall": {
            "metrics": _average([row["candidate_metrics"] for row in rows]),
            "metrics_by_domain": _domain_metrics([
                {**row["candidate_metrics"], "query_domain": row["query_domain"]} for row in rows
            ], "query_domain"),
            "contamination": contamination("candidate_wrong_domain"),
        },
        "ranked": {
            "metrics": _average([row["ranked_metrics"] for row in rows]),
            "metrics_by_domain": _domain_metrics([
                {**row["ranked_metrics"], "query_domain": row["query_domain"]} for row in rows
            ], "query_domain"),
            "contamination": contamination("ranked_wrong_domain"),
        },
        "queries": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    info = report["evaluation_info"]
    lines = [
        "# Siemens S210 + Aerospace Mixed-Domain Baseline v1",
        "",
        f"实体数：{info['entity_count']}；查询数：{info['query_count']}；Router：`{info['router']}`。本报告是无 Router 诊断，不是生产结论。",
        "",
        "## 检索指标",
        "",
        "| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("candidate_recall", "ranked"):
        metrics = report[name]["metrics"]
        lines.append(
            f"| {name} | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | {metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | {metrics['recall_at_20']:.4f} | {metrics['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## 跨域污染",
        "",
        "WrongDomain@K 表示 Top-K 中是否出现至少一个错误领域实体的查询比例；DomainPurity@K 表示 Top-K 中属于期望领域的实体比例。",
        "",
        "| 阶段 | WrongDomain@1 | WrongDomain@3 | WrongDomain@5 | Purity@1 | Purity@3 | Purity@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for name in ("candidate_recall", "ranked"):
        c = report[name]["contamination"]
        lines.append(
            f"| {name} | {c['wrong_domain_at_1']:.4f} | {c['wrong_domain_at_3']:.4f} | {c['wrong_domain_at_5']:.4f} | {c['domain_purity_at_1']:.4f} | {c['domain_purity_at_3']:.4f} | {c['domain_purity_at_5']:.4f} |"
        )
    lines.extend([
        "",
        "## 解释边界",
        "",
        "- 当前没有 Router，混合 Adapter 只存在于评测脚本中；Generic Pipeline 未添加领域分支。",
        "- S210 查询来自冻结 Final Test v1；航空查询来自非专家模板派生 Dev v1，不能把两者合并分数当作对称领域质量。",
        "- 若发现污染，先定位 query 信息量、Adapter 字段角色和候选池，再决定是否设计 Router；本报告不会自动触发 Router 实现。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s210-gold", type=Path, required=True)
    parser.add_argument("--aerospace-sample", type=Path, required=True)
    parser.add_argument("--s210-eval", type=Path, required=True)
    parser.add_argument("--aerospace-dev", type=Path, required=True)
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--reranker", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--with-reranker", action="store_true")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = run(
        args.s210_gold,
        args.aerospace_sample,
        args.s210_eval,
        args.aerospace_dev,
        args.model,
        args.cache_dir,
        args.with_reranker,
        args.reranker,
    )
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
