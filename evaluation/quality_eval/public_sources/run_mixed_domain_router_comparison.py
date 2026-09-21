"""Compare no-router, explainable rule-router, and oracle scope retrieval."""

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
from domain_router import DomainScopeProfile, RuleBasedDomainRouter  # noqa: E402
from generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402
from run_mixed_domain_baseline import (  # noqa: E402
    MixedDomainEvaluationAdapter,
    _average,
    _domain_metrics,
    _domain_quality,
    _load_queries,
    _metrics,
)
from siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


def _profiles() -> tuple[DomainScopeProfile, ...]:
    return (
        DomainScopeProfile(
            scope_id="siemens_s210",
            domain="industrial_drive",
            manufacturer="Siemens",
            system="S210",
            strong_terms=("siemens", "sinamics", "s210", "drive-cliq", "profinet", "profisafe"),
            identifier_patterns=(r"\b[AFN]\d{5}\b", r"\b[pr]\d{4,5}\b"),
        ),
        DomainScopeProfile(
            scope_id="faa_sdr",
            domain="aerospace",
            manufacturer="FAA",
            system="SDR",
            strong_terms=("航空器", "航空", "faa", "jasc", "sdr", "飞机"),
            identifier_patterns=(r"\bjasc\s*\d{4}\b",),
        ),
    )


def _stage(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    metrics = _average([row[stage]["metrics"] for row in rows])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["query_domain"]].append({**row[stage]["metrics"], "query_domain": row["query_domain"]})
    contamination = {
        f"wrong_domain_at_{k}": sum(row[stage]["contamination"][f"at_{k}"]["wrong_domain_presence"] for row in rows) / len(rows)
        for k in (1, 3, 5)
    }
    purity = {
        f"domain_purity_at_{k}": sum(row[stage]["contamination"][f"at_{k}"]["domain_purity"] for row in rows) / len(rows)
        for k in (1, 3, 5)
    }
    return {
        "metrics": metrics,
        "metrics_by_domain": _domain_metrics([item for values in grouped.values() for item in values], "query_domain"),
        "contamination": {**contamination, **purity},
    }


def _evaluate_output(output: Any, query: dict[str, Any], domain_by_entity: dict[str, str]) -> dict[str, Any]:
    relevant = set(query["relevant_entity_ids"])
    expected_domain = query["query_domain"]
    return {
        "metrics": _metrics(output.candidate_pool, relevant),
        "contamination": {
            f"at_{k}": _domain_quality(output.candidate_pool, expected_domain, domain_by_entity, k)
            for k in (1, 3, 5)
        },
        "candidate_pool_size": len(output.candidate_pool),
    }


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
    entities = (*s210_entities, *aerospace_entities)
    adapter = MixedDomainEvaluationAdapter(s210_adapter, aerospace_adapter)
    s210_eval = json.loads(s210_eval_path.read_text(encoding="utf-8"))
    aerospace_dev = json.loads(aerospace_dev_path.read_text(encoding="utf-8"))
    queries = _load_queries(s210_eval, aerospace_dev)
    embedding = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")

    def encode(texts: Sequence[str]) -> Any:
        return np.asarray(
            embedding.encode(list(texts), batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        )

    all_pipeline = GenericFaultRetrievalPipeline(adapter, entities, encode)
    scoped_pipelines = {
        "siemens_s210": GenericFaultRetrievalPipeline(s210_adapter, s210_entities, encode),
        "faa_sdr": GenericFaultRetrievalPipeline(aerospace_adapter, aerospace_entities, encode),
    }
    router = RuleBasedDomainRouter(_profiles())
    domain_by_entity = {entity.entity_id: entity.domain for entity in entities}
    rows: list[dict[str, Any]] = []
    for query in queries:
        no_router = all_pipeline.retrieve(query["query"])
        decision = router.route(query["query"])
        if decision.mode == "scoped" and decision.selected_scope_ids[0] in scoped_pipelines:
            routed_output = scoped_pipelines[decision.selected_scope_ids[0]].retrieve(query["query"])
        else:
            routed_output = no_router
        oracle_scope = scoped_pipelines[
            "siemens_s210" if query["query_domain"] == "industrial_drive" else "faa_sdr"
        ].retrieve(query["query"])
        rows.append(
            {
                "query_id": query["query_id"],
                "query": query["query"],
                "query_type": query["query_type"],
                "query_domain": query["query_domain"],
                "relevant_entity_ids": sorted(query["relevant_entity_ids"]),
                "router": {
                    "mode": decision.mode,
                    "selected_scope_ids": decision.selected_scope_ids,
                    "confidence": decision.confidence,
                    "signals": decision.signals,
                    "scores": decision.scores,
                },
                "no_router": _evaluate_output(no_router, query, domain_by_entity),
                "rule_router": _evaluate_output(routed_output, query, domain_by_entity),
                "oracle_scope": _evaluate_output(oracle_scope, query, domain_by_entity),
            }
        )

    return {
        "evaluation_info": {
            "name": "mixed_domain_router_comparison_v1",
            "version": "2026-09-21",
            "router": "explainable_rule_router",
            "router_contract": "scope only when explicit signal reaches threshold; otherwise cross_domain",
            "oracle_scope": "expected query domain from benchmark metadata; comparison only",
            "entity_count": len(entities),
            "query_count": len(queries),
            "embedding_model": model_name,
            "production_claim": False,
        },
        "no_router": _stage(rows, "no_router"),
        "rule_router": _stage(rows, "rule_router"),
        "oracle_scope": _stage(rows, "oracle_scope"),
        "router_decision_counts": {
            mode: sum(row["router"]["mode"] == mode for row in rows)
            for mode in ("scoped", "cross_domain")
        },
        "queries": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Siemens S210 + Aerospace Domain Router Comparison v1",
        "",
        "本报告在同一 321 个实体、79 条查询和 BGE-M3 下，对比 no-router 与可解释规则 Router；不代表生产上线。",
        "",
        "## 路由决策",
        "",
        f"scoped：{report['router_decision_counts']['scoped']}；cross_domain：{report['router_decision_counts']['cross_domain']}。",
        "",
        "## 检索指标",
        "",
        "| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, label in (("no_router", "No Router"), ("rule_router", "Rule Router"), ("oracle_scope", "Oracle Scope")):
        metrics = report[name]["metrics"]
        lines.append(
            f"| {label} | {metrics['recall_at_1']:.4f} | {metrics['recall_at_3']:.4f} | {metrics['recall_at_5']:.4f} | {metrics['recall_at_10']:.4f} | {metrics['recall_at_20']:.4f} | {metrics['mrr']:.4f} |"
        )
    lines.extend([
        "",
        "## 跨域污染",
        "",
        "| 方案 | WrongDomain@1 | WrongDomain@3 | WrongDomain@5 | Purity@1 | Purity@3 | Purity@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for name, label in (("no_router", "No Router"), ("rule_router", "Rule Router"), ("oracle_scope", "Oracle Scope")):
        contamination = report[name]["contamination"]
        lines.append(
            f"| {label} | {contamination['wrong_domain_at_1']:.4f} | {contamination['wrong_domain_at_3']:.4f} | {contamination['wrong_domain_at_5']:.4f} | {contamination['domain_purity_at_1']:.4f} | {contamination['domain_purity_at_3']:.4f} | {contamination['domain_purity_at_5']:.4f} |"
        )
    lines.extend([
        "",
        "## 边界",
        "",
        "- Rule Router 只在显式信号达到阈值时缩小 scope；低信息查询保持 cross_domain。",
        "- Oracle scope 仍不是分类器，只用于测量 metadata scope 的上限。",
        "- 本轮不修改 Generic Retrieval Pipeline，不切生产 API，不把规则写入前端。",
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
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
