"""Merge the first full AI review with the third targeted review.

This creates a new review-decision artifact only.  It does not modify the
source queue, produce the final dataset, or write SQLite.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


APPROVED = "审核通过"
REVISED = "语义需修改"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def merge(first: dict[str, Any], third: dict[str, Any]) -> dict[str, Any]:
    decisions = first.get("decisions")
    targeted = third.get("per_sample_decisions")
    if not isinstance(decisions, list) or not isinstance(targeted, list):
        raise ValueError("first.decisions and third.per_sample_decisions must be lists")

    merged = deepcopy(first)
    by_id = {str(item.get("sample_id")): item for item in decisions}
    if len(by_id) != len(decisions):
        raise ValueError("first review contains duplicate sample_id")

    targeted_ids: set[str] = set()
    revised_count = 0
    approved_count = 0
    for review in targeted:
        sample_id = str(review.get("sample_id") or "").strip()
        if not sample_id or sample_id in targeted_ids:
            raise ValueError(f"third review sample_id missing or duplicated: {sample_id!r}")
        if sample_id not in by_id:
            raise ValueError(f"third review contains unknown sample_id: {sample_id}")
        targeted_ids.add(sample_id)

        current = by_id[sample_id]
        final_decision = str(review.get("final_decision") or "").strip()
        if final_decision not in {APPROVED, REVISED}:
            raise ValueError(f"{sample_id} has unsupported final decision: {final_decision!r}")

        current["third_review"] = deepcopy(review)
        current["review_round"] = 3
        current["reviewer_name"] = third.get("reviewer_name") or "AI辅助定向复核专家（第三子agent）"
        current["review_date"] = third.get("review_date") or "2026-09-20"
        current["accepted_as_expert_by_user"] = True
        current["decision"] = final_decision
        current["fields_to_modify"] = deepcopy(review.get("fields_to_modify") or [])
        current["opinion"] = (
            review.get("retained_fields")
            or review.get("removed_or_added_fields")
            or "第三轮定向复核结论"
        )

        override = deepcopy(review.get("correction_override") or {})
        if final_decision == REVISED:
            gold_records = override.get("gold_records") or override.get("records")
            if not isinstance(gold_records, list) or not gold_records:
                raise ValueError(f"{sample_id} revised decision lacks correction gold_records")
            override["gold_records"] = deepcopy(gold_records)
            current["correction_applied"] = True
            current["correction_override"] = override
            current["evidence_spans"] = deepcopy(review.get("evidence_spans") or [])
            revised_count += 1
        else:
            current["correction_applied"] = False
            current["correction_override"] = {}
            current.pop("gold_records", None)
            current.pop("evidence_spans", None)
            approved_count += 1

    if len(targeted_ids) != 23:
        raise ValueError(f"expected 23 targeted decisions, got {len(targeted_ids)}")

    merged["review_mode"] = "ai_assisted_expert_review_authorized_by_user"
    merged["review_rounds"] = [
        "ai_expert_review_round_1",
        "ai_expert_review_round_2",
        "ai_targeted_review_round_3",
    ]
    merged["merge_summary"] = {
        "source_first_decision_count": len(decisions),
        "targeted_third_decision_count": len(targeted_ids),
        "third_round_approved_count": approved_count,
        "third_round_revised_count": revised_count,
        "database_written": False,
    }
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-json", required=True, type=Path)
    parser.add_argument("--third-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    result = merge(_load(args.first_json), _load(args.third_json))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["merge_summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
