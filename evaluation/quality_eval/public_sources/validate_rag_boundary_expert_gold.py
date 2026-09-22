"""Validate and score an expert-reviewed S210 RAG boundary dataset.

The validator refuses to score pending or partially reviewed data. This keeps
engineering expectations separate from named-expert Gold conclusions.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


STATUSES = {"supported", "supported_with_warning", "insufficient_evidence", "out_of_domain"}
ACTIONS = {"answer", "answer_with_warning", "ask_information", "reject"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
        raise ValueError("expert Gold must be an object with rows")
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info", {})
    if info.get("status") != "expert_validated":
        errors.append("dataset_info.status must be expert_validated")
    if info.get("gold_source") != "named_expert_review":
        errors.append("dataset_info.gold_source must be named_expert_review")
    if not info.get("reviewer"):
        errors.append("dataset_info.reviewer is required")
    seen: set[str] = set()
    for index, row in enumerate(payload["rows"], start=1):
        prefix = f"rows[{index}]"
        query_id = row.get("query_id")
        if not query_id or query_id in seen:
            errors.append(f"{prefix}.query_id must be unique and non-empty")
        seen.add(query_id)
        review = row.get("expert_review") or {}
        if review.get("expert_status") != "reviewed":
            errors.append(f"{prefix}.expert_review.expert_status must be reviewed")
        status = review.get("expected_knowledge_status")
        action = review.get("expected_action")
        if status not in STATUSES:
            errors.append(f"{prefix}: invalid expected_knowledge_status")
        if action not in ACTIONS:
            errors.append(f"{prefix}: invalid expected_action")
        for field in ("answer_allowed", "warning_required", "need_additional_info"):
            if not isinstance(review.get(field), bool):
                errors.append(f"{prefix}.expert_review.{field} must be boolean")
        if not isinstance(review.get("missing_information"), list):
            errors.append(f"{prefix}.expert_review.missing_information must be an array")
        if not str(review.get("expert_reason") or "").strip():
            errors.append(f"{prefix}.expert_review.expert_reason is required")
        if status == "supported" and (not review.get("answer_allowed") or review.get("warning_required")):
            errors.append(f"{prefix}: supported requires answer_allowed=true and warning_required=false")
        if status == "supported" and (action != "answer" or review.get("need_additional_info")):
            errors.append(f"{prefix}: supported requires action=answer and need_additional_info=false")
        if status == "supported_with_warning" and (not review.get("answer_allowed") or not review.get("warning_required")):
            errors.append(f"{prefix}: supported_with_warning requires answer_allowed=true and warning_required=true")
        if status == "supported_with_warning" and (action != "answer_with_warning" or not review.get("need_additional_info")):
            errors.append(f"{prefix}: supported_with_warning requires action=answer_with_warning and need_additional_info=true")
        if status == "supported_with_warning" and not review.get("missing_information"):
            errors.append(f"{prefix}: supported_with_warning requires missing_information")
        if status == "insufficient_evidence" and review.get("answer_allowed"):
            errors.append(f"{prefix}: insufficient_evidence requires answer_allowed=false")
        if status == "insufficient_evidence" and (action != "ask_information" or not review.get("need_additional_info")):
            errors.append(f"{prefix}: insufficient_evidence requires action=ask_information and need_additional_info=true")
        if status == "insufficient_evidence" and not review.get("missing_information"):
            errors.append(f"{prefix}: insufficient_evidence requires missing_information")
        if status == "out_of_domain" and review.get("answer_allowed"):
            errors.append(f"{prefix}: out_of_domain requires answer_allowed=false")
        if status == "out_of_domain" and (action != "reject" or review.get("warning_required") or review.get("need_additional_info")):
            errors.append(f"{prefix}: out_of_domain requires action=reject and no warning/additional info")
    return errors


def score_policy(payload: dict[str, Any], actual_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold_by_id = {row["query_id"]: row["expert_review"] for row in payload["rows"]}
    joined = []
    for actual in actual_rows:
        gold = gold_by_id.get(actual.get("query_id"))
        if gold is None:
            continue
        joined.append((gold, actual))
    if len(joined) != len(gold_by_id):
        missing = sorted(set(gold_by_id) - {row.get("query_id") for row in actual_rows})
        raise ValueError(f"actual policy rows missing query ids: {missing}")

    def actual_value(row: dict[str, Any], key: str) -> Any:
        """Read either normalized policy rows or evaluator result rows."""

        if key in row:
            return row[key]
        decision = row.get("decision")
        if isinstance(decision, dict):
            return decision.get(key)
        return None

    def actual_bool(row: dict[str, Any], key: str) -> bool:
        return bool(actual_value(row, key))

    def actual_status(row: dict[str, Any]) -> str:
        return str(actual_value(row, "knowledge_status") or row.get("actual_knowledge_status") or "")

    unsafe = [gold for gold, actual in joined if gold["expected_knowledge_status"] == "insufficient_evidence" and actual_bool(actual, "answer_allowed")]
    answer_permitted = [gold for gold, _ in joined if gold["answer_allowed"]]
    false_rejects = [gold for gold, actual in joined if gold["answer_allowed"] and not actual_bool(actual, "answer_allowed")]
    gold_warning = [gold for gold, _ in joined if gold["warning_required"]]
    actual_warning = [actual for _, actual in joined if actual_bool(actual, "warning_required")]
    warning_tp = sum(1 for gold, actual in joined if gold["warning_required"] and actual_bool(actual, "warning_required"))
    out_domain = [gold for gold, _ in joined if gold["expected_knowledge_status"] == "out_of_domain"]
    predicted_out_domain = [actual for _, actual in joined if actual_status(actual) == "out_of_domain"]
    out_domain_true_positive = sum(
        1
        for gold, actual in joined
        if actual_status(actual) == "out_of_domain"
        and gold["expected_knowledge_status"] == "out_of_domain"
    )
    return {
        "query_count": len(joined),
        "unsafe_answer_rate": len(unsafe) / sum(1 for gold, _ in joined if gold["expected_knowledge_status"] == "insufficient_evidence") if any(g["expected_knowledge_status"] == "insufficient_evidence" for g, _ in joined) else 0.0,
        "false_reject_rate": len(false_rejects) / len(answer_permitted) if answer_permitted else 0.0,
        "warning_precision": warning_tp / len(actual_warning) if actual_warning else 0.0,
        "warning_recall": warning_tp / len(gold_warning) if gold_warning else 0.0,
        "out_of_domain_precision": out_domain_true_positive / len(predicted_out_domain) if predicted_out_domain else 0.0,
        "out_of_domain_recall": out_domain_true_positive / len(out_domain) if out_domain else 0.0,
        "gold_status_counts": dict(Counter(g["expected_knowledge_status"] for g, _ in joined)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--actual-policy", help="JSON array or object with a results array")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = load(Path(args.gold))
    errors = validate(payload)
    if errors:
        report = {"status": "not_ready", "errors": errors}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    report: dict[str, Any] = {
        "status": "expert_gold_validated",
        "expert_validated": True,
        "query_count": len(payload["rows"]),
    }
    if args.actual_policy:
        actual_payload = json.loads(Path(args.actual_policy).read_text(encoding="utf-8"))
        actual_rows = actual_payload.get("results", actual_payload) if isinstance(actual_payload, dict) else actual_payload
        report["boundary_metrics"] = score_policy(payload, actual_rows)
    if args.output:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
