"""Apply explicit review decisions to the 281-record review queue.

This command is the boundary between a review work package and a final gold
snapshot.  It never invents expert decisions: every pending sample must have
an explicit decision and reviewer.  Non-approved decisions remain blocked or
explicitly excluded and therefore keep ``import_ready=false``.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


DECISIONS = {"审核通过", "语义需修改", "证据不足", "无法判断"}
APPROVED = "审核通过"
REVISED = "语义需修改"
BLOCKED = {"证据不足", "无法判断"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _prediction_records(row: dict[str, Any]) -> list[dict[str, Any]]:
    prediction = row.get("model_prediction") or {}
    records = prediction.get("records")
    if not isinstance(records, list):
        record = prediction.get("record")
        records = [record] if isinstance(record, dict) else []
    return deepcopy(records)


def _review_entry(decision: dict[str, Any], previous: str | None) -> dict[str, Any]:
    reviewer = str(decision.get("reviewer_name") or decision.get("reviewer") or "").strip()
    if not reviewer:
        raise ValueError(f"{decision.get('sample_id')} 缺少 reviewer_name")
    review_date = str(decision.get("review_date") or date.today().isoformat()).strip()
    result = {
        "decision": decision.get("decision"),
        "fields_to_modify": decision.get("fields_to_modify"),
        "modified_content": decision.get("modified_content"),
        "opinion": decision.get("opinion") or decision.get("review_note"),
        "reviewer_name": reviewer,
        "review_date": review_date,
        "correction_applied": bool(decision.get("correction_applied")),
        "accepted_as_expert_by_user": bool(decision.get("accepted_as_expert_by_user", False)),
    }
    if previous:
        result["previous_decision"] = previous
    return result


def finalize_queue(queue: dict[str, Any], decisions_payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(queue)
    rows = result.get("samples")
    decisions = decisions_payload.get("decisions")
    if not isinstance(rows, list) or not isinstance(decisions, list):
        raise ValueError("queue.samples and decisions_payload.decisions are required lists")
    by_id = {str(item.get("sample_id")): item for item in rows}
    if len(by_id) != len(rows):
        raise ValueError("审核队列存在重复 sample_id")
    decision_by_id: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError("审核结论必须是对象")
        sample_id = str(decision.get("sample_id") or "").strip()
        if not sample_id or sample_id in decision_by_id:
            raise ValueError(f"审核结论 sample_id 缺失或重复: {sample_id!r}")
        if sample_id not in by_id:
            raise ValueError(f"审核结论包含未知 sample_id: {sample_id}")
        value = str(decision.get("decision") or "").strip()
        if value not in DECISIONS:
            raise ValueError(f"{sample_id} 使用了未知审核结论: {value!r}")
        decision_by_id[sample_id] = decision

    pending_ids = {
        sample_id
        for sample_id, row in by_id.items()
        if (row.get("review_queue") or {}).get("status") == "pending"
    }
    missing = sorted(pending_ids - set(decision_by_id))
    if missing:
        raise ValueError(f"仍有 pending 记录没有明确审核结论: {missing[:10]}")

    for sample_id in sorted(pending_ids):
        row = by_id[sample_id]
        decision = decision_by_id[sample_id]
        value = str(decision["decision"])
        previous = (row.get("expert_review") or {}).get("decision")
        if value == APPROVED:
            gold_records = deepcopy(decision.get("gold_records") or _prediction_records(row))
            if not gold_records:
                raise ValueError(f"{sample_id} 审核通过但没有 gold_records")
            row["gold_records"] = gold_records
            row["gold_relations"] = deepcopy(decision.get("gold_relations") or [])
            row["review_queue"] = {
                "status": "confirmed_expert",
                "reason": "explicit_expert_approval",
                "decision": value,
            }
        elif value == REVISED:
            if not bool(decision.get("correction_applied")):
                raise ValueError(f"{sample_id} 语义需修改必须标记 correction_applied=true")
            gold_records = deepcopy(
                decision.get("gold_records")
                or (decision.get("correction_override") or {}).get("gold_records")
            )
            if not gold_records:
                raise ValueError(f"{sample_id} 语义需修改但没有修正后的 gold_records")
            row["gold_records"] = gold_records
            if decision.get("evidence_spans") is not None:
                row["evidence_spans"] = deepcopy(decision["evidence_spans"])
            row["gold_relations"] = deepcopy(decision.get("gold_relations") or [])
            row["review_queue"] = {
                "status": "confirmed_expert",
                "reason": "explicit_expert_correction_applied",
                "decision": value,
            }
        else:
            if bool(decision.get("excluded")):
                row["gold_records"] = []
                row["review_queue"] = {
                    "status": "excluded",
                    "reason": decision.get("opinion") or "explicit_expert_exclusion",
                    "decision": value,
                }
            else:
                row["review_queue"] = {
                    "status": "needs_resolution",
                    "reason": "explicit_expert_non_approval",
                    "decision": value,
                }

        review = _review_entry(decision, previous)
        row["expert_review"] = review
        row.setdefault("review_history", []).append(
            {
                "stage": "final_expert_review",
                **review,
            }
        )

    counts = {status: sum((row.get("review_queue") or {}).get("status") == status for row in rows) for status in ("confirmed_expert", "pending", "needs_resolution", "excluded")}
    info = result.setdefault("dataset_info", {})
    info["expert_review_decided_records"] = len(rows) - counts["pending"]
    info["confirmed_expert_records"] = counts["confirmed_expert"]
    info["pending_review_records"] = counts["pending"]
    info["needs_resolution_records"] = counts["needs_resolution"]
    info["excluded_records"] = counts["excluded"]
    info["label_status"] = "human_expert_reviewed" if counts["pending"] == 0 else "partial_expert_review_queue"
    info["import_ready"] = counts["pending"] == 0 and counts["needs_resolution"] == 0 and counts["excluded"] == 0
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-json", required=True, type=Path)
    parser.add_argument("--decisions-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    result = finalize_queue(_load(args.queue_json), _load(args.decisions_json))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["dataset_info"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
