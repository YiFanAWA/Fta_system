"""Propose source-backed evidence spans for pending causes.

Only exact normalized text matches inside the source Cause section are
proposed.  The output is advisory and does not mutate the queue or approve a
record.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise_with_positions(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    positions: list[int] = []
    pending_space = False
    for index, char in enumerate(text):
        if char.isspace():
            if chars:
                pending_space = True
            continue
        if pending_space:
            chars.append(" ")
            positions.append(index - 1)
            pending_space = False
        chars.append(char)
        positions.append(index)
    return "".join(chars), positions


def _find_exact_in_cause_section(text: str, value: str) -> dict[str, Any] | None:
    cause_start = text.find("Cause:")
    if cause_start < 0:
        return None
    remedy_start = text.find("Remedy:", cause_start)
    section_end = remedy_start if remedy_start >= 0 else len(text)
    section = text[cause_start:section_end]
    normalised, positions = _normalise_with_positions(section)
    target = re.sub(r"\s+", " ", value).strip()
    start = normalised.find(target)
    if start < 0:
        return None
    end = start + len(target)
    local_start = positions[start]
    local_end = positions[end - 1] + 1
    original_start = cause_start + local_start
    original_end = cause_start + local_end
    return {
        "field": "cause",
        "source_id": "input_text",
        "quote": text[original_start:original_end],
        "start": original_start,
        "end": original_end,
    }


def propose_repairs(dataset: dict[str, Any]) -> dict[str, Any]:
    proposals: list[dict[str, Any]] = []
    for row in dataset.get("samples", []):
        if (row.get("review_queue") or {}).get("status") != "pending":
            continue
        prediction = row.get("model_prediction") or {}
        records = prediction.get("records") or []
        if len(records) != 1:
            continue
        record = records[0]
        spans = row.get("evidence_spans") or []
        existing_indexes = {
            span.get("value_index")
            for span in spans
            if span.get("field") == "cause"
        }
        for index, cause in enumerate(record.get("causes") or []):
            if index in existing_indexes:
                continue
            span = _find_exact_in_cause_section(row.get("input_text", ""), str(cause))
            if span is None:
                continue
            span["value_index"] = index
            proposals.append(
                {
                    "sample_id": row["sample_id"],
                    "value_index": index,
                    "value": cause,
                    "proposed_evidence": span,
                    "proposal_status": "exact_source_match_needs_expert_acceptance",
                }
            )
    return {
        "dataset": dataset.get("dataset_info", {}).get("name"),
        "proposal_count": len(proposals),
        "proposals": proposals,
        "decision": "仅为证据补齐建议，不改变审核结论，不自动批准",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    report = propose_repairs(_load(args.queue_json))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"proposal_count": report["proposal_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
