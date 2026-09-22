"""Validate the resolved AND/OR logic Gold contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


ALLOWED_GATES = {"AND", "OR", "unknown", "not_applicable"}
ALLOWED_DECISIONS = {"approve", "revise", "reject", "cannot_determine"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info", {})
    events = payload.get("events", [])
    if info.get("status") != "expert_validated":
        errors.append("dataset_info.status must be expert_validated")
    if not events:
        errors.append("events must not be empty")
    if info.get("event_count") != len(events):
        errors.append("event_count does not match events length")
    ids = [event.get("logic_candidate_id") for event in events]
    if len(ids) != len(set(ids)):
        errors.append("logic_candidate_id values must be unique")
    for event in events:
        event_id = event.get("logic_candidate_id", "<missing>")
        review = event.get("expert_review", {})
        gate = event.get("logic_gate")
        decision = review.get("overall_decision")
        if gate not in ALLOWED_GATES:
            errors.append(f"{event_id}: invalid logic_gate={gate}")
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{event_id}: invalid overall_decision={decision}")
        if review.get("status") != "expert_reviewed":
            errors.append(f"{event_id}: status is not expert_reviewed")
        if decision == "approve" and not (
            review.get("child_set_complete") == "complete"
            and gate in {"AND", "OR"}
            and review.get("evidence_support") == "supported"
        ):
            errors.append(f"{event_id}: approved event is not fully supported")
    expected_unknown = sum(1 for event in events if event.get("logic_gate") == "unknown")
    if info.get("unknown_gate_count") != expected_unknown:
        errors.append("unknown_gate_count does not match events")
    if info.get("logic_gates_complete") and expected_unknown:
        errors.append("logic_gates_complete cannot be true while unknown gates remain")
    if info.get("fta_ready"):
        errors.append("FTA must remain blocked until causal and logic Gold are complete")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = load(Path(args.input))
    errors = validate(payload)
    report = {
        "status": "and_or_logic_gold_validated" if not errors else "validation_failed",
        "expert_validated": not bool(errors),
        "event_count": len(payload.get("events", [])),
        "approved_event_count": payload.get("dataset_info", {}).get("approved_event_count"),
        "unknown_gate_count": payload.get("dataset_info", {}).get("unknown_gate_count"),
        "logic_gates_complete": payload.get("dataset_info", {}).get("logic_gates_complete"),
        "fta_ready": payload.get("dataset_info", {}).get("fta_ready"),
        "errors": errors,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
