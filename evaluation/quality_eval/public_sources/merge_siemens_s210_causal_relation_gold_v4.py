"""Merge the completed v4 expert review into causal Relation Gold v4."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from merge_siemens_s210_causal_relation_gold_v3 import (
    _bool,
    _clean,
    _evidence,
    _validate_review_alignment,
    load_json,
)


def _normalise_review(review: Mapping[str, Any]) -> dict[str, Any]:
    records = review.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("v4 expert review JSON must contain non-empty records")
    rows = []
    for record in records:
        rows.append(
            {
                "candidate_id": record.get("candidate_id"),
                "fault_code": record.get("fault_code"),
                "fault_description": record.get("fault_description"),
                "candidate_cause": record.get("cause_node"),
                "evidence_ref": record.get("evidence_reference"),
                "evidence_text": record.get("evidence_text"),
                "causal_status": record.get("causal_status"),
                "direction": record.get("direction"),
                "relation_type": record.get("relation_type"),
                "fta_eligible": record.get("fta_eligible"),
                "overall_decision": record.get("overall_decision"),
                "expert_comment": record.get("review_comment", ""),
            }
        )
    return {
        "dataset_info": {
            "reviewer": review.get("reviewer"),
            "reviewed_at": review.get("review_date"),
        },
        "rows": rows,
    }


def _relation_from_review(
    candidate: Mapping[str, Any], review: Mapping[str, Any], reviewer: str, reviewed_at: str
) -> dict[str, Any]:
    source = candidate["source_node"]
    target = candidate["target_node"]
    suffix = _clean(review["candidate_id"]).replace("CR-CAND-V4-", "")
    return {
        "relation_id": f"S210-CAUSAL-V4-{suffix}",
        "candidate_id": review["candidate_id"],
        "source_node": {
            "node_id": source["node_id"],
            "node_type": source["node_type"],
            "text": source["text"],
        },
        "target_node": {
            "node_id": target["node_id"],
            "node_type": target["node_type"],
            "fault_code": target["fault_code"],
            "description": target["description"],
        },
        "relation_type": review["relation_type"],
        "direction": review["direction"],
        "relation_note": review.get("expert_comment", ""),
        "evidence": _evidence(candidate),
        "expert_review": {
            "causal_status": review["causal_status"],
            "fta_eligible": _bool(review["fta_eligible"]),
            "overall_decision": review["overall_decision"],
            "expert_comment": review.get("expert_comment", ""),
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
        },
    }


def _excluded_from_review(
    candidate: Mapping[str, Any], review: Mapping[str, Any], reviewer: str, reviewed_at: str
) -> dict[str, Any]:
    return {
        "candidate_id": review["candidate_id"],
        "fault_code": candidate["source_record"]["fault_code"],
        "causal_status": review["causal_status"],
        "direction": review["direction"],
        "relation_type": review["relation_type"],
        "fta_eligible": _bool(review["fta_eligible"]),
        "decision": review["overall_decision"],
        "expert_comment": review.get("expert_comment", ""),
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
    }


def merge_gold(
    previous: Mapping[str, Any],
    candidates: Mapping[str, Any],
    review_file: Mapping[str, Any],
    source_review_documents: list[str],
) -> dict[str, Any]:
    review = _normalise_review(review_file)
    reviews = review["rows"]
    _validate_review_alignment(candidates, reviews)
    candidate_map = {row["candidate_id"]: row for row in candidates["candidates"]}
    reviewer = _clean(review["dataset_info"].get("reviewer"))
    reviewed_at = _clean(review["dataset_info"].get("reviewed_at"))
    if not reviewer or not reviewed_at:
        raise ValueError("v4 expert review must provide reviewer and review_date")

    new_relations = []
    new_excluded = []
    for row in reviews:
        candidate = candidate_map[row["candidate_id"]]
        approved = (
            row["causal_status"] == "causal"
            and row["direction"] == "source_to_target"
            and row["relation_type"] == "causes"
            and _bool(row["fta_eligible"])
            and row["overall_decision"] == "approve"
        )
        if approved:
            new_relations.append(_relation_from_review(candidate, row, reviewer, reviewed_at))
        else:
            new_excluded.append(_excluded_from_review(candidate, row, reviewer, reviewed_at))

    previous_info = dict(previous.get("dataset_info") or {})
    relations = copy.deepcopy(list(previous.get("relations", []))) + new_relations
    excluded = copy.deepcopy(list(previous.get("excluded_candidates", []))) + new_excluded
    relation_ids = [row.get("relation_id") for row in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("causal relation IDs overlap after v4 merge")
    counts = Counter(row["target_node"]["fault_code"] for row in relations)
    source_candidate_count = previous_info.get("source_candidate_count")
    if not isinstance(source_candidate_count, int) or source_candidate_count <= 0:
        raise ValueError("previous Gold must expose a positive source_candidate_count")
    reviewed_count = previous_info.get("reviewed_candidate_count", 0) + len(reviews)
    review_dates = dict(previous_info.get("review_dates") or {})
    review_dates["batch_v4"] = reviewed_at
    source_documents = list(previous_info.get("source_review_documents") or [])
    for document in source_review_documents:
        if document not in source_documents:
            source_documents.append(document)

    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_gold",
            "version": "v4",
            "status": "expert_validated",
            "expert_validated": True,
            "gold_source": "named_expert_review",
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "review_date_missing": bool(previous_info.get("review_date_missing")),
            "review_date_missing_batches": list(previous_info.get("review_date_missing_batches") or []),
            "review_dates": review_dates,
            "relation_scope": "causal_only",
            "candidate_scope": (
                "pilot_batch_30_plus_remaining_same_faults_batch_66_plus_diverse_unreviewed_batch_50_plus_batch_50"
            ),
            "source_candidate_bundles": list(previous_info.get("source_candidate_bundles") or [])
            + ["siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json"],
            "source_review_documents": source_documents,
            "source_record_count": previous_info.get("source_record_count"),
            "source_candidate_count": source_candidate_count,
            "candidate_review_count": reviewed_count,
            "expert_validation_scope": "reviewed_candidates_only",
            "reviewed_candidate_count": reviewed_count,
            "unreviewed_candidate_count": source_candidate_count - reviewed_count,
            "approved_causal_relation_count": len(relations),
            "excluded_candidate_count": len(excluded),
            "target_fault_count": len(counts),
            "multi_causal_target_fault_count": sum(1 for count in counts.values() if count >= 2),
            "review_summary_v4": {
                "total": len(reviews),
                "causal": sum(1 for row in reviews if row["causal_status"] == "causal"),
                "associated_only": sum(1 for row in reviews if row["causal_status"] == "associated_only"),
                "unsupported": sum(1 for row in reviews if row["causal_status"] == "unsupported"),
                "cannot_determine": sum(1 for row in reviews if row["causal_status"] == "cannot_determine"),
                "fta_eligible_true": sum(1 for row in reviews if _bool(row["fta_eligible"])),
                "approve": sum(1 for row in reviews if row["overall_decision"] == "approve"),
                "revise": sum(1 for row in reviews if row["overall_decision"] == "revise"),
                "reject": sum(1 for row in reviews if row["overall_decision"] == "reject"),
            },
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "runtime_registry_updated": False,
            "training_eligible": False,
            "summary_discrepancies": list(previous_info.get("summary_discrepancies") or []),
            "merge_note": (
                "The 117 relations cover only the target faults represented by the four reviewed batches; "
                "they are not a complete causal Gold for all 281 source records."
            ),
        },
        "relations": relations,
        "excluded_candidates": excluded,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--review-json", required=True)
    parser.add_argument("--review-markdown")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    documents = [Path(args.review_json).name]
    if args.review_markdown:
        documents.append(Path(args.review_markdown).name)
    gold = merge_gold(
        load_json(Path(args.previous)),
        load_json(Path(args.candidates)),
        load_json(Path(args.review_json)),
        documents,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "relations": len(gold["relations"]),
                "excluded_candidates": len(gold["excluded_candidates"]),
                "target_fault_count": gold["dataset_info"]["target_fault_count"],
                "fta_ready": gold["dataset_info"]["fta_ready"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
