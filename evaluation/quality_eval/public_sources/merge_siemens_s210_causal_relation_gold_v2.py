"""Merge the first causal Gold batch with the second same-fault batch."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def merge(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    relations = list(first.get("relations", [])) + list(second.get("relations", []))
    excluded = list(first.get("excluded_candidates", [])) + list(second.get("excluded_candidates", []))
    relation_ids = [relation["relation_id"] for relation in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("causal relation IDs overlap")
    counts = Counter(relation["target_node"]["fault_code"] for relation in relations)
    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_gold",
            "version": "v2",
            "status": "expert_validated",
            "gold_source": "named_expert_review",
            "reviewer": first["dataset_info"].get("reviewer"),
            "reviewed_at": None,
            "review_date_missing": True,
            "review_dates": {
                "batch_v1": first["dataset_info"].get("reviewed_at"),
                "batch_v2": second["dataset_info"].get("reviewed_at"),
            },
            "relation_scope": "causal_only",
            "candidate_scope": "pilot_batch_30_plus_remaining_same_faults_batch_66",
            "source_candidate_bundles": [
                first["dataset_info"].get("source_candidate_bundle"),
                second["dataset_info"].get("source_candidate_bundle"),
            ],
            "source_review_documents": [
                first["dataset_info"].get("source_review_document"),
                second["dataset_info"].get("source_review_document"),
            ],
            "source_record_count": first["dataset_info"].get("source_record_count"),
            "candidate_review_count": first["dataset_info"].get("candidate_review_count", 0)
            + second["dataset_info"].get("candidate_review_count", 0),
            "approved_causal_relation_count": len(relations),
            "excluded_candidate_count": len(excluded),
            "target_fault_count": len(counts),
            "multi_causal_target_fault_count": sum(1 for count in counts.values() if count >= 2),
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "runtime_registry_updated": False,
            "training_eligible": False,
            "summary_discrepancies": [
                first["dataset_info"].get("summary_discrepancy")
            ]
            if first["dataset_info"].get("summary_discrepancy")
            else [],
            "merge_note": (
                "The 39 relations cover only the 25 target faults represented by the two pilot batches; "
                "they are not a complete causal Gold for all 281 source records."
            ),
        },
        "relations": relations,
        "excluded_candidates": excluded,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", required=True)
    parser.add_argument("--second", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = merge(load(Path(args.first)), load(Path(args.second)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "relations": len(payload["relations"]), "excluded": len(payload["excluded_candidates"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
