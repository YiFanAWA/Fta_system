"""Build an AI-assisted provisional causal relation view from Gold v6."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_map(bundle: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = bundle.get("candidates")
    if not isinstance(rows, list):
        raise ValueError("candidate bundle must contain candidates")
    return {row["candidate_id"]: row for row in rows}


def _build_relation(
    candidate: Mapping[str, Any], review: Mapping[str, Any]
) -> dict[str, Any]:
    candidate_id = review["candidate_id"]
    source = candidate["source_node"]
    target = candidate["target_node"]
    evidence = {
        "citation_id": f"{candidate_id}:ai_provisional",
        "source_id": "input_text",
        "field": "cause",
        "quote": review["evidence_text"],
        "start": review["evidence_start"],
        "end": review["evidence_end"],
        "alignment_status": "ai_simulated_pending_human_confirmation",
    }
    return {
        "relation_id": f"S210-CAUSAL-AI-V7-{candidate_id.rsplit('-', 1)[-1]}",
        "candidate_id": candidate_id,
        "source_node": {
            "node_id": source["node_id"],
            "node_type": source["node_type"],
            "text": review["suggested_final_cause_text"],
        },
        "target_node": copy.deepcopy(target),
        "relation_type": review["suggested_relation_type"],
        "direction": review["suggested_direction"],
        "relation_note": review["reason"],
        "evidence": [evidence],
        "expert_review": {
            "review_status": "simulation_only",
            "causal_status": review["suggested_causal_status"],
            "fta_eligible": review["suggested_fta_eligible"],
            "overall_decision": "ai_provisional",
            "reviewer": "Codex simulated Siemens S210 expert",
            "reviewed_at": "2026-09-23",
            "human_confirmation_required": True,
        },
    }


def build_provisional(
    previous: Mapping[str, Any],
    candidates: Mapping[str, Any],
    ai_review: Mapping[str, Any],
) -> dict[str, Any]:
    info = copy.deepcopy(dict(previous["dataset_info"]))
    candidate_map = _candidate_map(candidates)
    records = ai_review.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ValueError("AI pre-review must contain exactly two records")
    candidate_ids = [row["candidate_id"] for row in records]
    if set(candidate_ids) != {"CR-CAND-V5-007", "CR-CAND-V5-021"}:
        raise ValueError("AI pre-review candidate scope is not A01691/A01782")

    relations = copy.deepcopy(list(previous.get("relations", [])))
    excluded = copy.deepcopy(list(previous.get("excluded_candidates", [])))
    for record in records:
        candidate_id = record["candidate_id"]
        candidate = candidate_map.get(candidate_id)
        if candidate is None:
            raise ValueError(f"missing candidate {candidate_id}")
        if record.get("simulated_decision") != "revise":
            raise ValueError(f"{candidate_id} must remain revise in AI provisional view")
        if sum(row.get("candidate_id") == candidate_id for row in excluded) != 1:
            raise ValueError(f"expected one excluded pending row for {candidate_id}")
        excluded = [row for row in excluded if row.get("candidate_id") != candidate_id]
        relations.append(_build_relation(candidate, record))

    relation_ids = [row.get("relation_id") for row in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("relation IDs overlap in AI provisional view")
    counts = Counter(row["target_node"]["fault_code"] for row in relations)
    previous_count = int(info.get("reviewed_candidate_count", 0))
    info.update(
        {
            "version": "v7-ai-provisional",
            "status": "ai_assisted_provisional",
            "expert_validated": False,
            "gold_source": "named_expert_review_plus_ai_simulated_revision",
            "reviewer": "Codex simulated Siemens S210 expert",
            "reviewed_at": "2026-09-23",
            "reviewed_candidate_count": previous_count,
            "unreviewed_candidate_count": int(info["source_candidate_count"]) - previous_count,
            "formal_approved_causal_relation_count": len(previous.get("relations", [])),
            "provisional_ai_relation_count": 2,
            "provisional_relation_count": len(relations),
            "formal_excluded_candidate_count": len(previous.get("excluded_candidates", [])),
            "provisional_excluded_candidate_count": len(excluded),
            "target_fault_count": len(counts),
            "multi_causal_target_fault_count": sum(1 for count in counts.values() if count >= 2),
            "source_ai_review_documents": [
                "siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.json",
                "siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.md",
            ],
            "expert_validation_scope": "formal_named_expert_reviewed_candidates_only",
            "provisional_validation_scope": "two_ai_simulated_revision_candidates_only",
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "runtime_registry_updated": False,
            "merge_note": (
                "This is an AI-assisted provisional view only. The two added relations require "
                "formal named-expert confirmation before they can enter official Gold."
            ),
        }
    )
    return {"dataset_info": info, "relations": relations, "excluded_candidates": excluded}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--ai-review", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build_provisional(
        load_json(Path(args.previous)),
        load_json(Path(args.candidates)),
        load_json(Path(args.ai_review)),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "status": result["dataset_info"]["status"],
                "provisional_relation_count": result["dataset_info"]["provisional_relation_count"],
                "formal_approved_causal_relation_count": result["dataset_info"]["formal_approved_causal_relation_count"],
                "provisional_excluded_candidate_count": result["dataset_info"]["provisional_excluded_candidate_count"],
                "fta_ready": result["dataset_info"]["fta_ready"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
