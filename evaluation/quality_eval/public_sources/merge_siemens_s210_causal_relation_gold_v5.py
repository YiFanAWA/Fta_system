"""Merge the approved A01730 revision into Causal Relation Gold v5."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from merge_siemens_s210_causal_relation_gold_v3 import _bool, _clean, load_json


REVISION_CANDIDATE_ID = "CR-CAND-V4-029"


def _find_candidate(bundle: Mapping[str, Any], candidate_id: str) -> Mapping[str, Any]:
    matches = [
        candidate
        for candidate in bundle.get("candidates", [])
        if _clean(candidate.get("candidate_id")) == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one candidate for {candidate_id}, got {len(matches)}")
    return matches[0]


def _validate_approval(review: Mapping[str, Any], candidate: Mapping[str, Any]) -> None:
    expected = {
        "candidate_id": REVISION_CANDIDATE_ID,
        "previous_status": "pending_expert_revision",
    }
    for field, value in expected.items():
        if review.get(field) != value:
            raise ValueError(f"revision.{field} must be {value}")
    body = review.get("review")
    gate = review.get("gate_check")
    if not isinstance(body, Mapping) or not isinstance(gate, Mapping):
        raise ValueError("revision approval must contain review and gate_check objects")
    required_review = {
        "causal_status": "causal",
        "direction": "source_to_target",
        "relation_type": "causes",
        "fta_eligible": True,
        "overall_decision": "approve",
    }
    for field, value in required_review.items():
        if body.get(field) != value:
            raise ValueError(f"review.{field} must be {value}")
    for field in (
        "overall_decision_approve",
        "causal_status_causal",
        "direction_source_to_target",
        "relation_type_causes",
        "fta_eligible_true",
        "final_cause_text_matches_evidence",
        "eligible_for_next_gold",
    ):
        if gate.get(field) is not True:
            raise ValueError(f"gate_check.{field} must be true")
    if _clean(review.get("reviewer")) != _clean(body.get("reviewer")):
        raise ValueError("reviewer mismatch between top-level and review")
    if _clean(review.get("fault_code")) != _clean(candidate["target_node"]["fault_code"]):
        raise ValueError("fault_code does not match candidate target")
    if _clean(body.get("final_cause_text")) == "":
        raise ValueError("review.final_cause_text is required")


def _revised_evidence(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_text = _clean(candidate.get("source_context", {}).get("input_text"))
    cause_marker = source_text.find("Cause:")
    if cause_marker < 0:
        raise ValueError("candidate source_context.input_text has no Cause section")
    line_end = source_text.find("\n", cause_marker)
    if line_end < 0:
        line_end = len(source_text)
    quote = source_text[cause_marker + len("Cause:") : line_end].strip()
    if quote.endswith("."):
        quote = quote[:-1]
    start = source_text.find(quote, cause_marker + len("Cause:"))
    if start < 0:
        raise ValueError("Cause section text is not locatable in source_context.input_text")
    end = start + len(quote)
    return [
        {
            "citation_id": f"{candidate['candidate_id']}:cause:revision_v4",
            "source_id": "input_text",
            "field": "cause",
            "quote": quote,
            "start": start,
            "end": end,
        }
    ]


def _build_relation(
    candidate: Mapping[str, Any], review: Mapping[str, Any]
) -> dict[str, Any]:
    body = review["review"]
    final_cause_text = _clean(body["final_cause_text"])
    return {
        "relation_id": "S210-CAUSAL-V4-029",
        "candidate_id": candidate["candidate_id"],
        "source_node": {
            "node_id": candidate["source_node"]["node_id"],
            "node_type": candidate["source_node"]["node_type"],
            "text": final_cause_text,
        },
        "target_node": copy.deepcopy(candidate["target_node"]),
        "relation_type": body["relation_type"],
        "direction": body["direction"],
        "relation_note": body.get("expert_reason", ""),
        "evidence": _revised_evidence(candidate),
        "expert_review": {
            "causal_status": body["causal_status"],
            "fta_eligible": _bool(body["fta_eligible"]),
            "overall_decision": body["overall_decision"],
            "final_cause_text": final_cause_text,
            "expert_comment": body.get("expert_reason", ""),
            "reviewer": body["reviewer"],
            "reviewed_at": body["reviewed_at"],
            "revision_of": "S210-CAUSAL-V4-029 pending exclusion",
        },
    }


def merge_gold(
    previous: Mapping[str, Any],
    candidate_bundle: Mapping[str, Any],
    revision_review: Mapping[str, Any],
    source_review_documents: list[str],
) -> dict[str, Any]:
    candidate = _find_candidate(candidate_bundle, REVISION_CANDIDATE_ID)
    _validate_approval(revision_review, candidate)

    previous_info = dict(previous.get("dataset_info") or {})
    relations = copy.deepcopy(list(previous.get("relations", [])))
    if any(row.get("candidate_id") == REVISION_CANDIDATE_ID for row in relations):
        raise ValueError("A01730 revision already exists in relations")
    excluded = copy.deepcopy(list(previous.get("excluded_candidates", [])))
    removed = [
        row for row in excluded if row.get("candidate_id") == REVISION_CANDIDATE_ID
    ]
    if len(removed) != 1:
        raise ValueError("expected exactly one pending A01730 exclusion in Gold v4")
    excluded = [
        row for row in excluded if row.get("candidate_id") != REVISION_CANDIDATE_ID
    ]
    relations.append(_build_relation(candidate, revision_review))

    relation_ids = [row.get("relation_id") for row in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("relation IDs overlap after A01730 revision merge")
    counts = Counter(row["target_node"]["fault_code"] for row in relations)
    documents = list(previous_info.get("source_review_documents") or [])
    for document in source_review_documents:
        if document not in documents:
            documents.append(document)
    review_dates = dict(previous_info.get("review_dates") or {})
    reviewed_at = _clean(revision_review["review"]["reviewed_at"])
    review_dates["revision_v4_a01730"] = reviewed_at

    info = {
        **previous_info,
        "version": "v5",
        "reviewer": revision_review["reviewer"],
        "reviewed_at": reviewed_at,
        "review_dates": review_dates,
        "source_review_documents": documents,
        "candidate_scope": (
            f"{previous_info.get('candidate_scope', '')}_plus_revision_v4_a01730"
        ),
        "approved_causal_relation_count": len(relations),
        "excluded_candidate_count": len(excluded),
        "target_fault_count": len(counts),
        "multi_causal_target_fault_count": sum(1 for count in counts.values() if count >= 2),
        "review_summary_v5": {
            "revision_candidate_id": REVISION_CANDIDATE_ID,
            "revision_approved": True,
            "revision_count": 1,
            "previous_exclusion_removed": True,
        },
        "causal_relations_complete": False,
        "logic_gates_complete": False,
        "fta_ready": False,
        "runtime_registry_updated": False,
        "merge_note": (
            "The 118 relations cover only the four reviewed batches plus one approved revision; "
            "they are not a complete causal Gold for all 281 source records."
        ),
    }
    return {"dataset_info": info, "relations": relations, "excluded_candidates": excluded}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True)
    parser.add_argument("--candidate-bundle", required=True)
    parser.add_argument("--revision-json", required=True)
    parser.add_argument("--review-markdown")
    parser.add_argument("--review-docx")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    gold = merge_gold(
        load_json(Path(args.previous)),
        load_json(Path(args.candidate_bundle)),
        load_json(Path(args.revision_json)),
        [
            name
            for name in (
                Path(args.revision_json).name,
                Path(args.review_markdown).name if args.review_markdown else None,
                Path(args.review_docx).name if args.review_docx else None,
            )
            if name
        ],
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
