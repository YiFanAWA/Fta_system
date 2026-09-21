"""Compare an oracle metadata-scoped index with the no-router mixed baseline.

The expected query domain is supplied by the frozen benchmark metadata.  This
is an upper-bound experiment for scoped retrieval, not a production router.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
PUBLIC_SOURCES = ROOT / "evaluation/quality_eval/public_sources"
for path in (BACKEND, PUBLIC_SOURCES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402
from generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402
from run_mixed_domain_baseline import _average, _load_queries, _metrics  # noqa: E402
from siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


def run(
    s210_gold_path: Path,
    aerospace_sample_path: Path,
    s210_eval_path: Path,
    aerospace_dev_path: Path,
    model_name: str,
    cache_dir: Path | None,
) -> dict[str, Any]:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers and numpy are required") from exc

    s210_adapter = SiemensS210Adapter()
    aerospace_adapter = FaaSdrAerospaceAdapter()
    s210_entities = s210_adapter.parse_file(s210_gold_path)
    aerospace_entities = aerospace_adapter.parse_file(aerospace_sample_path)
    s210_eval = json.loads(s210_eval_path.read_text(encoding="utf-8"))
    aerospace_dev = json.loads(aerospace_dev_path.read_text(encoding="utf-8"))
    queries = _load_queries(s210_eval, aerospace_dev)
    embedding = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")

    def encode(texts: Sequence[str]) -> Any:
        return np.asarray(
            embedding.encode(
                list(texts), batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
            )
        )

    s210_pipeline = GenericFaultRetrievalPipeline(s210_adapter, s210_entities, encode)
    aerospace_pipeline = GenericFaultRetrievalPipeline(aerospace_adapter, aerospace_entities, encode)
    rows: list[dict[str, Any]] = []
    for query in queries:
        pipeline = s210_pipeline if query["query_domain"] == "industrial_drive" else aerospace_pipeline
        output = pipeline.retrieve(query["query"])
        relevant = set(query["relevant_entity_ids"])
        rows.append(
            {
                "query_id": query["query_id"],
                "query_domain": query["query_domain"],
                "query_type": query["query_type"],
                "relevant_entity_ids": sorted(relevant),
                "metrics": _metrics(output.candidate_pool, relevant),
                "candidate_pool_size": len(output.candidate_pool),
                "wrong_domain_at_1": 0.0,
                "wrong_domain_at_3": 0.0,
                "wrong_domain_at_5": 0.0,
            }
        )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["query_domain"]].append(row["metrics"])
    return {
        "evaluation_info": {
            "name": "mixed_domain_metadata_scope_comparison_v1",
            "version": "2026-09-21",
            "router": "oracle_metadata_scope",
            "scope_source": "expected query domain from benchmark metadata; not a classifier",
            "entity_count": len(s210_entities) + len(aerospace_entities),
            "query_count": len(queries),
            "embedding_model": model_name,
            "production_claim": False,
        },
        "scoped_candidate_recall": {
            "metrics": _average([row["metrics"] for row in rows]),
            "metrics_by_domain": {key: _average(value) for key, value in sorted(grouped.items())},
            "contamination": {
                "wrong_domain_at_1": 0.0,
                "wrong_domain_at_3": 0.0,
                "wrong_domain_at_5": 0.0,
                "domain_purity_at_1": 1.0,
                "domain_purity_at_3": 1.0,
                "domain_purity_at_5": 1.0,
            },
        },
        "queries": rows,
        "interpretation": [
            "This is an oracle metadata-scope upper bound, not a domain router implementation.",
            "A zero contamination result is guaranteed by the scope boundary; internal domain recall remains meaningful.",
            "Use the result to separate cross-domain contamination from within-domain retrieval weakness.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["scoped_candidate_recall"]["metrics"]
    contamination = report["scoped_candidate_recall"]["contamination"]
    lines = [
        "# Mixed-Domain Metadata Scope Comparison v1",
        "",
        "这是使用评测集已知领域标签的 oracle scope 对照，不是生产 Domain Router。",
        "",
        "| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Oracle metadata scope | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | {metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | {metrics['recall_at_20']:.4f} | {metrics['mrr']:.4f} |",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| WrongDomain@1 | {contamination['wrong_domain_at_1']:.4f} |",
        f"| WrongDomain@3 | {contamination['wrong_domain_at_3']:.4f} |",
        f"| WrongDomain@5 | {contamination['wrong_domain_at_5']:.4f} |",
        "",
        "## 解释",
        "",
        "scope 将跨域污染强制降为 0，只能证明“领域边界有效”，不能证明领域识别器已经实现。还需要下一轮比较真实的 Query → Domain/System 分类器或 Router。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s210-gold", type=Path, required=True)
    parser.add_argument("--aerospace-sample", type=Path, required=True)
    parser.add_argument("--s210-eval", type=Path, required=True)
    parser.add_argument("--aerospace-dev", type=Path, required=True)
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.s210_gold, args.aerospace_sample, args.s210_eval, args.aerospace_dev, args.model, args.cache_dir)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
