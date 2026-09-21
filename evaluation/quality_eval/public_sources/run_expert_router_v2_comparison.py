"""Compare No Router, Rule Router v1, and expert-derived Router v2.

Router v2 is an experiment-only profile loaded from a review-derived registry.
This script evaluates retrieval and clarification behavior separately and
never modifies the production Router configuration.
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
PUBLIC_SOURCES = ROOT / "evaluation/quality_eval/public_sources"
for path in (BACKEND, PUBLIC_SOURCES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402
from domain_evidence_registry import build_domain_scope_profiles  # noqa: E402
from domain_router import RuleBasedDomainRouter  # noqa: E402
from generic_retrieval_pipeline import GenericFaultRetrievalPipeline  # noqa: E402
from query_sufficiency import QuerySufficiencyEvaluator  # noqa: E402
from run_mixed_domain_baseline import (  # noqa: E402
    MixedDomainEvaluationAdapter,
    _average,
    _domain_quality,
    _load_queries,
    _metrics,
)
from siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _scope_profiles(path: Path | None) -> tuple[Any, ...]:
    return build_domain_scope_profiles(path)


def _load_gold(path: Path) -> dict[str, dict[str, Any]]:
    payload = _read(path)
    return {str(row["query_id"]): row for row in payload.get("queries", [])}


def _evaluate_output(output: Any, query: dict[str, Any], domain_by_entity: dict[str, str]) -> dict[str, Any]:
    relevant = set(query["relevant_entity_ids"])
    expected_domain = query["query_domain"]
    return {
        "candidate_metrics": _metrics(output.candidate_pool, relevant),
        "ranked_metrics": _metrics(output.guarded_rank, relevant),
        "candidate_contamination": {
            f"at_{k}": _domain_quality(output.candidate_pool, expected_domain, domain_by_entity, k)
            for k in (1, 3, 5, 10, 20)
        },
        "ranked_contamination": {
            f"at_{k}": _domain_quality(output.guarded_rank, expected_domain, domain_by_entity, k)
            for k in (1, 3, 5, 10, 20)
        },
        "candidate_pool_size": len(output.candidate_pool),
        "route_rank": list(output.guarded_rank),
        "candidate_pool": list(output.candidate_pool),
    }


def _stage(rows: Sequence[dict[str, Any]], stage: str) -> dict[str, Any]:
    candidate = _average([row[stage]["candidate_metrics"] for row in rows])
    ranked = _average([row[stage]["ranked_metrics"] for row in rows])
    contamination: dict[str, float] = {}
    for source, key in (("candidate_contamination", "candidate"), ("ranked_contamination", "ranked")):
        for k in (1, 3, 5, 10, 20):
            contamination[f"{key}_wrong_domain_at_{k}"] = sum(
                row[stage][source][f"at_{k}"]["wrong_domain_presence"] for row in rows
            ) / len(rows)
            contamination[f"{key}_domain_purity_at_{k}"] = sum(
                row[stage][source][f"at_{k}"]["domain_purity"] for row in rows
            ) / len(rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["query_domain"]].append(row)
    return {
        "candidate_recall": candidate,
        "ranked_metrics": ranked,
        "contamination": contamination,
        "metrics_by_domain": {
            domain: {
                "candidate_recall": _average([item[stage]["candidate_metrics"] for item in values]),
                "ranked_metrics": _average([item[stage]["ranked_metrics"] for item in values]),
            }
            for domain, values in sorted(grouped.items())
        },
    }


def _clarification_metrics(
    rows: Sequence[dict[str, Any]],
    stage: str,
    gold: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    all_rows = [row[stage]["clarification"] for row in rows]
    reviewed = [item for item in all_rows if item["query_id"] in gold]
    tp = sum(item["predicted_clarification"] and gold[item["query_id"]]["gold_action"] == "clarify_first" for item in reviewed)
    fp = sum(item["predicted_clarification"] and gold[item["query_id"]]["gold_action"] != "clarify_first" for item in reviewed)
    fn = sum((not item["predicted_clarification"]) and gold[item["query_id"]]["gold_action"] == "clarify_first" for item in reviewed)
    tn = sum((not item["predicted_clarification"]) and gold[item["query_id"]]["gold_action"] != "clarify_first" for item in reviewed)
    predicted_positive = tp + fp
    return {
        "reviewed_gold_count": len(reviewed),
        "reviewed_gold_positive_count": sum(gold[item["query_id"]]["gold_action"] == "clarify_first" for item in reviewed),
        "predicted_clarification_count_all_queries": sum(item["predicted_clarification"] for item in all_rows),
        "clarification_rate_all_queries": sum(item["predicted_clarification"] for item in all_rows) / len(all_rows),
        "clarification_precision_on_reviewed_gold": tp / predicted_positive if predicted_positive else None,
        "clarification_recall_on_reviewed_gold": tp / (tp + fn) if (tp + fn) else None,
        "clarification_accuracy_on_reviewed_gold": (tp + tn) / len(reviewed) if reviewed else None,
        "confusion_matrix_on_reviewed_gold": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "unreviewed_query_count": len(all_rows) - len(reviewed),
        "metric_note": "Precision/recall are computed only on the 22 manually reviewed query rows; all-query rate is behavior, not Gold accuracy.",
    }


def run(
    s210_gold_path: Path,
    aerospace_sample_path: Path,
    s210_eval_path: Path,
    aerospace_dev_path: Path,
    v2_registry_path: Path,
    sufficiency_gold_path: Path,
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
    s210_eval = _read(s210_eval_path)
    aerospace_dev = _read(aerospace_dev_path)
    queries = _load_queries(s210_eval, aerospace_dev)
    gold = _load_gold(sufficiency_gold_path)
    embedding = SentenceTransformer(model_name, cache_folder=str(cache_dir) if cache_dir else None, device="cpu")
    vector_cache: dict[str, Any] = {}

    def encode(texts: Sequence[str]) -> Any:
        values = [str(text) for text in texts]
        missing = list(dict.fromkeys(value for value in values if value not in vector_cache))
        if missing:
            encoded = np.asarray(
                embedding.encode(
                    missing,
                    batch_size=8,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
            )
            vector_cache.update(zip(missing, encoded))
        return np.asarray([vector_cache[value] for value in values])

    all_pipeline = GenericFaultRetrievalPipeline(adapter, entities, encode)
    scoped_pipelines = {
        "siemens_s210": GenericFaultRetrievalPipeline(s210_adapter, s210_entities, encode),
        "faa_sdr": GenericFaultRetrievalPipeline(aerospace_adapter, aerospace_entities, encode),
    }
    v1_router = RuleBasedDomainRouter(_scope_profiles(None))
    v2_router = RuleBasedDomainRouter(_scope_profiles(v2_registry_path))
    sufficiency = QuerySufficiencyEvaluator()
    domain_by_entity = {entity.entity_id: entity.domain for entity in entities}
    rows: list[dict[str, Any]] = []

    for query in queries:
        no_output = all_pipeline.retrieve(query["query"])
        v1_decision = v1_router.route(query["query"])
        v2_decision = v2_router.route(query["query"])

        def routed_output(decision: Any) -> Any:
            if decision.mode == "scoped" and decision.selected_scope_ids[0] in scoped_pipelines:
                return scoped_pipelines[decision.selected_scope_ids[0]].retrieve(query["query"])
            return no_output

        v1_output = routed_output(v1_decision)
        v2_output = routed_output(v2_decision)
        stages = {
            "no_router": (no_output, None),
            "rule_router_v1": (v1_output, v1_decision),
            "expert_router_v2": (v2_output, v2_decision),
        }
        row: dict[str, Any] = {
            "query_id": query["query_id"],
            "query": query["query"],
            "query_type": query["query_type"],
            "query_domain": query["query_domain"],
            "relevant_entity_ids": sorted(query["relevant_entity_ids"]),
            "expert_gold": gold.get(query["query_id"]),
            "router_decisions": {},
        }
        for stage, (output, decision) in stages.items():
            evaluated = _evaluate_output(output, query, domain_by_entity)
            if decision is None:
                decision_json = {
                    "mode": "cross_domain",
                    "selected_scope_ids": ["siemens_s210", "faa_sdr"],
                    "confidence": 0.0,
                    "signals": [],
                    "scores": [],
                }
            else:
                decision_json = {
                    "mode": decision.mode,
                    "selected_scope_ids": list(decision.selected_scope_ids),
                    "confidence": decision.confidence,
                    "signals": list(decision.signals),
                    "scores": [list(item) for item in decision.scores],
                }
            sufficiency_decision = sufficiency.assess(
                query["query"],
                domain_confidence=float(decision_json["confidence"]),
                route_mode=str(decision_json["mode"]),
            )
            predicted_clarification = stage != "no_router" and sufficiency_decision.requires_clarification
            evaluated["clarification"] = {
                "query_id": query["query_id"],
                "predicted_clarification": predicted_clarification,
                "sufficiency_decision": sufficiency_decision.to_dict(),
            }
            row[stage] = evaluated
            row["router_decisions"][stage] = decision_json
        rows.append(row)

    return {
        "evaluation_info": {
            "name": "expert_router_v2_comparison_v1",
            "version": "2026-09-21",
            "domains": ["industrial_drive/Siemens/S210", "aerospace/FAA_SDR"],
            "entity_count": len(entities),
            "query_count": len(queries),
            "expert_query_gold_count": len(gold),
            "embedding_model": model_name,
            "v1_registry": "backend-python/config/domain_evidence_registry_v1.json",
            "v2_registry": str(v2_registry_path),
            "sufficiency_gold": str(sufficiency_gold_path),
            "production_claim": False,
            "generic_pipeline_changed": False,
            "query_sufficiency_metric_scope": "22 manually reviewed query rows only for precision/recall; 79 rows for behavior rate",
            "python": sys.version,
            "platform": platform.platform(),
        },
        "no_router": _stage(rows, "no_router"),
        "rule_router_v1": _stage(rows, "rule_router_v1"),
        "expert_router_v2": _stage(rows, "expert_router_v2"),
        "clarification": {
            "no_router": _clarification_metrics(rows, "no_router", gold),
            "rule_router_v1": _clarification_metrics(rows, "rule_router_v1", gold),
            "expert_router_v2": _clarification_metrics(rows, "expert_router_v2", gold),
        },
        "queries": rows,
    }


def _fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# No Router / Rule Router v1 / Expert Router v2 对比",
        "",
        "本报告只验证审核派生的 Router v2，不代表生产切换。Generic Retrieval Pipeline 未修改。",
        "",
        "## 检索指标",
        "",
        "| 方案 | Candidate Recall@20 | Ranked R@1 | Ranked R@3 | Ranked R@5 | Ranked R@10 | MRR | WrongDomain@1（候选） |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("no_router", "No Router"), ("rule_router_v1", "Rule Router v1"), ("expert_router_v2", "Expert Router v2")):
        stage = report[key]
        lines.append(
            f"| {label} | {stage['candidate_recall']['recall_at_20']:.4f} | {stage['ranked_metrics']['recall_at_1']:.4f} | {stage['ranked_metrics']['recall_at_3']:.4f} | {stage['ranked_metrics']['recall_at_5']:.4f} | {stage['ranked_metrics']['recall_at_10']:.4f} | {stage['ranked_metrics']['mrr']:.4f} | {stage['contamination']['candidate_wrong_domain_at_1']:.4f} |"
        )
    lines.extend([
        "",
        "## 澄清行为",
        "",
        "| 方案 | 专家 Gold 数 | Gold 中应澄清 | Clarification Precision | Clarification Recall | 全量澄清比例 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for key, label in (("no_router", "No Router"), ("rule_router_v1", "Rule Router v1"), ("expert_router_v2", "Expert Router v2")):
        item = report["clarification"][key]
        lines.append(
            f"| {label} | {item['reviewed_gold_count']} | {item['reviewed_gold_positive_count']} | {_fmt(item['clarification_precision_on_reviewed_gold'])} | {_fmt(item['clarification_recall_on_reviewed_gold'])} | {item['clarification_rate_all_queries']:.4f} |"
        )
    lines.extend([
        "",
        "## 口径与限制",
        "",
        "- Candidate Recall@20 看正确实体是否进入候选池；Ranked 指标看最终排序。",
        "- Clarification Precision/Recall 只在刘武明确审核的 22 条查询上计算；57 条未审核查询不参与 Gold 准确率。",
        "- 全量 79 条的澄清比例是系统行为统计，不能解释成“需要补充信息的真实比例”。",
        "- Expert Router v2 registry 为实验文件，未写入 `backend-python/config`，未接生产 API/前端。",
        "",
        "## 逐条结果",
        "",
        "结果明细见同名 JSON 的 `queries` 字段，包括每个方案的路由、sufficiency、候选池、排名和跨域污染。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s210-gold", type=Path, required=True)
    parser.add_argument("--aerospace-sample", type=Path, required=True)
    parser.add_argument("--s210-eval", type=Path, required=True)
    parser.add_argument("--aerospace-dev", type=Path, required=True)
    parser.add_argument("--v2-registry", type=Path, required=True)
    parser.add_argument("--sufficiency-gold", type=Path, required=True)
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
        args.v2_registry,
        args.sufficiency_gold,
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
