"""Resolve explicit evidence-only findings in the accepted public expert batch.

The six target rows were not semantic disagreements: the accepted expert report
explicitly said the candidate reasons were correct and named the missing Cause
evidence.  This script adds only those source-backed spans, preserves the
original ``证据不足`` decision in history, and records a new approved state.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


TARGETS: dict[str, list[tuple[int, str]]] = {
    "SIEMENS_S210_2019_A01706": [
        (
            0,
            "Motion monitoring functions with SAM (p9506 = 0):\n- after initiating SS1 or SS2, the speed exceeded the set tolerance.",
        ),
        (
            1,
            "Motion monitoring functions with SBR (p9506 = 2):\n- after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance.",
        ),
    ],
    "SIEMENS_S210_2019_F01650": [
        (0, 'The "Safety Integrated" function on monitoring channel 1 requires an acceptance test.'),
    ],
    "SIEMENS_S210_2019_F01800": [
        (
            1,
            "Communication via DRIVE-CLiQ socket X100 ... X107 has not been switched to cyclic operation. The cause may be an incorrect structure or a configuration that results in an impossible bus timing.",
        ),
        (
            2,
            "Loss of the DRIVE-CLiQ connection. The cause may be, for example, that the DRIVE-CLiQ cable was withdrawn from the Control Unit or as a result of a short-circuit for motors with DRIVE-CLiQ.",
        ),
        (
            4,
            "A connection was detected but the node ID exchange mechanism does not function. The reason is probably that the component is defective.",
        ),
    ],
    "SIEMENS_S210_2019_F07093": [
        (2, "The parameterized distance (p5308) was exceeded."),
        (4, "Offset (p5297) is too high for the parameterized distance (p5308)."),
    ],
    "SIEMENS_S210_2019_F30027": [
        (4, "4) Line supply voltage incorrectly set (p0210)."),
        (
            7,
            '7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit, power is taken from the DC link.',
        ),
    ],
    "SIEMENS_S210_2019_F30685": [
        (
            0,
            'The limit value for the function "Safely-Limited Speed" (SLS) is greater than the speed that corresponds to an encoder limit frequency of 500 kHz.',
        ),
    ],
}


def _normalise_with_positions(text: str) -> tuple[str, list[int]]:
    normalised: list[str] = []
    positions: list[int] = []
    pending_space = False
    for index, char in enumerate(text):
        if char.isspace():
            if normalised:
                pending_space = True
            continue
        if pending_space:
            normalised.append(" ")
            positions.append(index - 1)
            pending_space = False
        normalised.append(char)
        positions.append(index)
    return "".join(normalised), positions


def _find_span(text: str, target: str) -> dict[str, Any]:
    normalised_text, positions = _normalise_with_positions(text)
    normalised_target = re.sub(r"\s+", " ", target).strip()
    start = normalised_text.find(normalised_target)
    if start < 0:
        raise ValueError(f"无法在原文中定位证据: {target}")
    end = start + len(normalised_target)
    original_start = positions[start]
    original_end = positions[end - 1] + 1
    return {
        "field": "cause",
        "source_id": "input_text",
        "quote": text[original_start:original_end],
        "start": original_start,
        "end": original_end,
    }


def resolve_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(dataset)
    rows = {row["sample_id"]: row for row in result.get("samples", [])}
    if set(TARGETS) - set(rows):
        raise ValueError(f"输入数据缺少目标记录: {sorted(set(TARGETS) - set(rows))}")

    for sample_id, targets in TARGETS.items():
        row = rows[sample_id]
        review = row.get("expert_review") or {}
        if review.get("decision") != "证据不足":
            raise ValueError(f"{sample_id} 当前不是预期的“证据不足”: {review.get('decision')}")
        existing = row.get("evidence_spans") or []
        added: list[dict[str, Any]] = []
        for value_index, target in targets:
            span = _find_span(row["input_text"], target)
            span["value_index"] = value_index
            if not any(
                item.get("field") == "cause"
                and item.get("start") == span["start"]
                and item.get("end") == span["end"]
                for item in existing
            ):
                existing.append(span)
                added.append(span)
        existing.sort(key=lambda item: (item.get("start", 0), item.get("end", 0)))
        row["evidence_spans"] = existing

        original_decision = review.get("decision")
        review["decision"] = "审核通过"
        review["correction_applied"] = True
        review["modified_content"] = "已按专家意见补充候选原因的原文证据；原始证据不足结论保留在审核历史。"
        review["correction_override"] = {
            "evidence_spans_added": [
                {"start": span["start"], "end": span["end"], "value_index": span["value_index"]}
                for span in added
            ]
        }
        review["resolution_source"] = "accepted_expert_review_evidence_repair"
        row["expert_review"] = review
        history = row.setdefault("review_history", [])
        history.append(
            {
                "stage": "expert_evidence_resolution",
                "previous_decision": original_decision,
                "decision": "审核通过",
                "reviewer_name": review.get("reviewer_name"),
                "review_date": "2026-09-20",
                "fields_to_modify": "抽取证据-候选原因",
                "modified_content": review["modified_content"],
                "added_evidence_count": len(added),
            }
        )

    result.setdefault("dataset_info", {})["evidence_resolution"] = {
        "status": "resolved",
        "resolved_records": len(TARGETS),
        "method": "expert_explicit_missing_cause_evidence_repair",
        "import_ready_for_these_rows": True,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    dataset = json.loads(args.input_json.read_text(encoding="utf-8"))
    result = resolve_dataset(dataset)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["dataset_info"]["evidence_resolution"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
