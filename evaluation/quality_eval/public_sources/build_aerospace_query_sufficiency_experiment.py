"""Build paired base/enriched queries for aerospace information sufficiency."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "backend-python") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend-python"))

from domains.aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402


def build(sample_path: Path, dev_path: Path) -> dict[str, Any]:
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    dev = json.loads(dev_path.read_text(encoding="utf-8"))
    entities = FaaSdrAerospaceAdapter()
    by_id = {entity.entity_id: entity for entity in entities.parse_source(sample)}
    base_queries = [
        query
        for query in dev["queries"]
        if query["query_type"] in {"component", "condition"}
        and len(query["relevant_entity_ids"]) == 1
    ]
    queries: list[dict[str, Any]] = []
    for index, query in enumerate(base_queries, start=1):
        entity = by_id[query["relevant_entity_ids"][0]]
        context = [
            str(entity.domain_specific.get("aircraft_model") or "").strip(),
            f"JASC {entity.domain_specific.get('jasc_code', '')}",
            " ".join(entity.components),
            " ".join(entity.parameters),
        ]
        context = [item for item in context if item.strip()]
        for variant, query_text, sufficiency in (
            ("base", query["query"], query["query_sufficiency"]),
            ("enriched", f"{query['query']}，上下文：{' '.join(context)}", "sufficient"),
        ):
            queries.append(
                {
                    **query,
                    "query_id": f"AERO-SUFF-{index:03d}-{variant}",
                    "query": query_text,
                    "variant": variant,
                    "query_sufficiency": sufficiency,
                    "sufficiency_reason": "paired context enrichment experiment" if variant == "enriched" else query["sufficiency_reason"],
                    "gold_source": "derived_from_aerospace_retrieval_dev_v1_paired_query",
                }
            )
    return {
        "dataset_info": {
            "name": "aerospace_query_sufficiency_experiment_v1",
            "version": "2026-09-21",
            "source_dev": str(dev_path),
            "query_count": len(queries),
            "evaluation_role": "paired_development_experiment",
            "lifecycle_status": "development_only",
            "eligible_for_final_generalization_claim": False,
            "paired_variants": ["base", "enriched"],
            "annotation_authority": "derived public-row paired query; not expert annotation",
            "notes": [
                "Enriched queries append target-row aircraft/JASC/component/part context only to measure information sufficiency.",
                "The enriched context is experimental metadata, not a production query rewrite rule.",
            ],
        },
        "queries": queries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build(args.sample, args.dev)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "query_count": payload["dataset_info"]["query_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
