"""Build a deterministic FAA SDR retrieval development set.

The labels are derived from the selected public rows and are explicitly not
expert query annotations or a final generalization benchmark.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402


DEFAULT_SAMPLE = ROOT / "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"
DEFAULT_OUTPUT = ROOT / "evaluation/quality_eval/datasets/aerospace_retrieval_dev_v1_2026-09-21.json"


def _first_words(text: str, limit: int = 12) -> str:
    return " ".join(str(text or "").split()[:limit]).strip(" .")


def _query(
    query_id: str,
    text: str,
    query_type: str,
    entity_ids: list[str],
    *,
    difficulty: str = "medium",
    ambiguity: str = "none",
    sufficiency: str = "partially_sufficient",
    sufficiency_reason: str = "",
) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "query": text,
        "query_type": query_type,
        "difficulty": difficulty,
        "relevant_entity_ids": entity_ids,
        "relevance_policy": "any_relevant_entity_in_top_k",
        "ambiguity": ambiguity,
        "query_sufficiency": sufficiency,
        "sufficiency_reason": sufficiency_reason,
        "gold_source": "derived_from_faa_sdr_public_sample_v1",
        "annotation_authority": "template_derived_public_record_link; not expert_query_annotation",
    }


def build(sample_path: Path) -> dict[str, Any]:
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    adapter = FaaSdrAerospaceAdapter()
    entities = adapter.parse_source(payload)
    by_jasc: dict[str, list[str]] = defaultdict(list)
    with_parameters = []
    with_components = []
    with_remedies = []
    with_conditions = []
    component_counts: dict[str, int] = defaultdict(int)
    condition_counts: dict[str, int] = defaultdict(int)
    parameter_counts: dict[str, int] = defaultdict(int)
    for entity in entities:
        by_jasc[str(entity.domain_specific["jasc_code"])].append(entity.entity_id)
        if entity.parameters:
            with_parameters.append(entity)
        if entity.components:
            with_components.append(entity)
        if entity.remedies:
            with_remedies.append(entity)
        if entity.symptoms:
            with_conditions.append(entity)
        for value in entity.components:
            component_counts[value.casefold()] += 1
        for value in entity.symptoms:
            condition_counts[value.casefold()] += 1
        for value in entity.parameters:
            parameter_counts[value.casefold()] += 1

    queries: list[dict[str, Any]] = []
    # JASC classification queries deliberately allow multiple matching reports.
    for index, (jasc, entity_ids) in enumerate(sorted(by_jasc.items())[:8], start=1):
        queries.append(
            _query(
                f"AERO-Q{index:03d}",
                f"JASC {jasc} 对应哪些航空故障报告？",
                "identifier",
                entity_ids,
                difficulty="easy",
                ambiguity="multi_answer" if len(entity_ids) > 1 else "none",
                sufficiency="sufficient",
                sufficiency_reason="explicit JASC identifier; repeated JASC values intentionally allow multi-answer relevance",
            )
        )

    cursor = 0
    for entity in with_parameters[:8]:
        queries.append(
            _query(
                f"AERO-Q{len(queries) + 1:03d}",
                f"航空维修记录中涉及部件号 {entity.parameters[0]} 的是哪条记录？",
                "part_number",
                [entity.entity_id],
                difficulty="easy",
                sufficiency="sufficient" if parameter_counts[entity.parameters[0].casefold()] == 1 else "partially_sufficient",
                sufficiency_reason="explicit part number" if parameter_counts[entity.parameters[0].casefold()] == 1 else "part number is shared by multiple sampled reports",
            )
        )
        cursor += 1

    for entity in with_components[:8]:
        component = entity.components[0]
        queries.append(
            _query(
                f"AERO-Q{len(queries) + 1:03d}",
                f"哪条航空故障记录涉及 {component}？",
                "component",
                [entity.entity_id],
                difficulty="medium",
                sufficiency="partially_sufficient" if component_counts[component.casefold()] == 1 else "insufficient",
                sufficiency_reason="component-only query lacks aircraft/JASC context" if component_counts[component.casefold()] == 1 else "component label is shared by multiple sampled reports",
            )
        )

    for entity in with_conditions[:8]:
        condition = entity.symptoms[0]
        queries.append(
            _query(
                f"AERO-Q{len(queries) + 1:03d}",
                f"航空部件状态为 {condition} 的故障记录是哪条？",
                "condition",
                [entity.entity_id],
                difficulty="medium",
                sufficiency="insufficient" if condition_counts[condition.casefold()] > 1 else "partially_sufficient",
                sufficiency_reason="low-information condition label is repeated" if condition_counts[condition.casefold()] > 1 else "condition query lacks aircraft/JASC/part context",
            )
        )

    for entity in with_remedies[:8]:
        remedy = _first_words(entity.remedies[0])
        queries.append(
            _query(
                f"AERO-Q{len(queries) + 1:03d}",
                f"哪条航空维修报告包含处置记录：{remedy}？",
                "maintenance_action",
                [entity.entity_id],
                difficulty="hard",
                sufficiency="sufficient",
                sufficiency_reason="explicit C/A maintenance narrative",
            )
        )

    # Keep the first release in the planned 30-50 range, without inventing
    # labels when a source field is absent in the selected sample.
    queries = queries[:50]
    if len(queries) < 30:
        raise RuntimeError(f"development set is too small: {len(queries)}")
    try:
        source_sample = str(sample_path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        source_sample = str(sample_path)
    return {
        "dataset_info": {
            "name": "aerospace_retrieval_dev_v1",
            "version": "2026-09-21",
            "source_sample": source_sample,
            "query_count": len(queries),
            "evaluation_role": "Aerospace Retrieval Development v1",
            "lifecycle_status": "sealed_development_only",
            "eligible_for_final_generalization_claim": False,
            "ranking_unit": "entity_id",
            "multi_answer_policy": "any relevant entity in top_k",
            "annotation_authority": "derived public-record links and deterministic templates; not human expert query annotation",
            "query_types": {
                query_type: sum(item["query_type"] == query_type for item in queries)
                for query_type in sorted({item["query_type"] for item in queries})
            },
            "query_sufficiency_counts": {
                sufficiency: sum(item["query_sufficiency"] == sufficiency for item in queries)
                for sufficiency in sorted({item["query_sufficiency"] for item in queries})
            },
            "stages": [
                "adapter_parse",
                "exact_identifier_and_part_number_retrieval",
                "description_dense_retrieval",
                "candidate_fusion",
                "entity_id_aggregation",
                "reranking",
            ],
            "notes": [
                "This is a development set generated from public source rows, not expert relevance annotation.",
                "Do not modify Common Fault Gold or Generic Pipeline from this set alone.",
                "Classify misses as adapter_mapping, schema_gap, retrieval_role, chunk, or generic_contract before changing shared code.",
            ],
        },
        "queries": queries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build(args.sample)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "query_count": payload["dataset_info"]["query_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
