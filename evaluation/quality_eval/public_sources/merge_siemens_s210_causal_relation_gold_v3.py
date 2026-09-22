"""Merge the completed v3 expert review into the causal Relation Gold."""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalise_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _clean(value))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean(value).casefold() == "true"


def _review_key(row: Mapping[str, Any]) -> str:
    return _clean(row.get("candidate_id"))


def _validate_review_alignment(
    candidates: Mapping[str, Any], reviews: list[Mapping[str, Any]]
) -> None:
    candidate_rows = candidates.get("candidates")
    if not isinstance(candidate_rows, list):
        raise ValueError("candidate bundle must contain candidates")
    candidate_map = {_clean(row.get("candidate_id")): row for row in candidate_rows}
    review_map = {_review_key(row): row for row in reviews}
    if "" in candidate_map or "" in review_map:
        raise ValueError("candidate_id must be non-empty")
    expected_ids = set(candidate_map)
    actual_ids = set(review_map)
    if expected_ids != actual_ids:
        raise ValueError(
            "review IDs do not match candidates; "
            f"missing={sorted(expected_ids - actual_ids)}, "
            f"extra={sorted(actual_ids - expected_ids)}"
        )

    allowed_status = {"causal", "associated_only", "unsupported", "cannot_determine"}
    allowed_directions = {"source_to_target", "target_to_source", "undirected", "unknown"}
    allowed_relations = {"causes", "caused_by", "associated_with", "no_relation"}
    allowed_decisions = {"approve", "revise", "reject", "cannot_determine"}
    for candidate_id, review in review_map.items():
        candidate = candidate_map[candidate_id]
        evidence = (candidate.get("evidence") or [{}])[0]
        checks = {
            "fault_code": (review.get("fault_code"), candidate.get("target_node", {}).get("fault_code")),
            "fault_description": (
                review.get("fault_description"),
                candidate.get("target_node", {}).get("description"),
            ),
            "candidate_cause": (review.get("candidate_cause"), candidate.get("source_node", {}).get("text")),
            "evidence_ref": (review.get("evidence_ref"), evidence.get("evidence_id")),
            "evidence_text": (review.get("evidence_text"), evidence.get("quote")),
        }
        for field, (actual, expected) in checks.items():
            if _normalise_text(actual) != _normalise_text(expected):
                raise ValueError(
                    f"{candidate_id}.{field} does not match the candidate bundle"
                )
        if _clean(review.get("causal_status")) not in allowed_status:
            raise ValueError(f"{candidate_id}.causal_status is invalid")
        if _clean(review.get("direction")) not in allowed_directions:
            raise ValueError(f"{candidate_id}.direction is invalid")
        if _clean(review.get("relation_type")) not in allowed_relations:
            raise ValueError(f"{candidate_id}.relation_type is invalid")
        if _clean(review.get("overall_decision")) not in allowed_decisions:
            raise ValueError(f"{candidate_id}.overall_decision is invalid")


def _evidence(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in candidate.get("evidence", []):
        result.append(
            {
                "citation_id": item["evidence_id"],
                "source_id": item["source_id"],
                "field": item["field"],
                "quote": item["quote"],
                "start": item.get("start"),
                "end": item.get("end"),
            }
        )
    return result


def _relation_from_review(
    candidate: Mapping[str, Any], review: Mapping[str, Any], reviewer: str, reviewed_at: str | None
) -> dict[str, Any]:
    source = candidate["source_node"]
    target = candidate["target_node"]
    suffix = _clean(review["candidate_id"]).replace("CR-CAND-V3-", "")
    return {
        "relation_id": f"S210-CAUSAL-V3-{suffix}",
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
    candidate: Mapping[str, Any], review: Mapping[str, Any], reviewer: str, reviewed_at: str | None
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
    review: Mapping[str, Any],
    source_review_documents: list[str],
) -> dict[str, Any]:
    reviews = review.get("rows")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("expert review JSON must contain non-empty rows")
    _validate_review_alignment(candidates, reviews)
    candidate_map = {row["candidate_id"]: row for row in candidates["candidates"]}

    review_info = review.get("dataset_info") or {}
    reviewer = _clean(review_info.get("reviewer"))
    reviewed_at = _clean(review_info.get("reviewed_at")) or None
    if not reviewer or not reviewed_at:
        raise ValueError("v3 expert review must provide reviewer and reviewed_at")

    new_relations: list[dict[str, Any]] = []
    new_excluded: list[dict[str, Any]] = []
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

    previous_relations = copy.deepcopy(list(previous.get("relations", [])))
    previous_excluded = copy.deepcopy(list(previous.get("excluded_candidates", [])))
    relations = previous_relations + new_relations
    excluded = previous_excluded + new_excluded
    relation_ids = [row.get("relation_id") for row in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("causal relation IDs overlap after v3 merge")

    counts = Counter(row["target_node"]["fault_code"] for row in relations)
    previous_info = dict(previous.get("dataset_info") or {})
    prior_dates = dict(previous_info.get("review_dates") or {})
    prior_dates["batch_v3"] = reviewed_at
    review_date_missing = any(
        not _clean(row.get("expert_review", {}).get("reviewed_at")) for row in relations
    )
    missing_date_batches = list(previous_info.get("review_date_missing_batches") or [])
    if review_date_missing and "batch_v2" not in missing_date_batches:
        missing_date_batches.append("batch_v2")
    prior_bundles = list(previous_info.get("source_candidate_bundles") or [])
    v3_bundle = candidates.get("dataset_info", {}).get("name", "")
    if v3_bundle and v3_bundle not in prior_bundles:
        prior_bundles.append(f"{v3_bundle}_v3_remaining_unreviewed.json")
    previous_docs = list(previous_info.get("source_review_documents") or [])
    for document in source_review_documents:
        if document not in previous_docs:
            previous_docs.append(document)

    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_gold",
            "version": "v3",
            "status": "expert_validated",
            "gold_source": "named_expert_review",
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "review_date_missing": review_date_missing,
            "review_date_missing_batches": missing_date_batches,
            "review_dates": prior_dates,
            "relation_scope": "causal_only",
            "candidate_scope": (
                "pilot_batch_30_plus_remaining_same_faults_batch_66_plus_diverse_unreviewed_batch_50"
            ),
            "source_candidate_bundles": prior_bundles,
            "source_review_documents": previous_docs,
            "source_record_count": previous_info.get("source_record_count"),
            "candidate_review_count": previous_info.get("candidate_review_count", 0) + len(reviews),
            "approved_causal_relation_count": len(relations),
            "excluded_candidate_count": len(excluded),
            "target_fault_count": len(counts),
            "multi_causal_target_fault_count": sum(1 for count in counts.values() if count >= 2),
            "review_summary_v3": {
                "causal": sum(1 for row in reviews if row["causal_status"] == "causal"),
                "associated_only": sum(1 for row in reviews if row["causal_status"] == "associated_only"),
                "unsupported": sum(1 for row in reviews if row["causal_status"] == "unsupported"),
                "cannot_determine": sum(1 for row in reviews if row["causal_status"] == "cannot_determine"),
                "fta_eligible_true": sum(1 for row in reviews if _bool(row["fta_eligible"])),
            },
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "runtime_registry_updated": False,
            "training_eligible": False,
            "summary_discrepancies": list(previous_info.get("summary_discrepancies") or []),
            "merge_note": (
                "The 72 relations cover only the target faults represented by the three reviewed batches; "
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
    parser.add_argument("--review-docx")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_documents = [Path(args.review_json).name]
    for optional in (args.review_markdown, args.review_docx):
        if optional:
            source_documents.append(Path(optional).name)
    gold = merge_gold(
        load_json(Path(args.previous)),
        load_json(Path(args.candidates)),
        load_json(Path(args.review_json)),
        source_documents,
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
