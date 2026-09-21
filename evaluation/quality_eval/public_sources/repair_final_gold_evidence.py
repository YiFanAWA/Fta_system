"""Repair exact evidence projection for the finalized public gold snapshot.

This script never changes gold field values.  It only makes evidence quotes
match the stored input text exactly and adds a cause span when a reviewed
cause has an unambiguous token-level match in the source text.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)*")


# A small, reviewable fallback table for causes whose reviewed wording is a
# normalized paraphrase of a source sentence or whose source contains a
# numbered/value prefix.  The table stores source text, never replacement
# gold values; spans are still projected from the actual input_text.
FALLBACK_CAUSE_SOURCE = {
    ("SIEMENS_S210_2019_A01711", 7):
        "Scaling factor for acceleration for SBR different.",
    ("SIEMENS_S210_2019_A01711", 8):
        "Scaling factor for the inverse value of the acceleration for SBR different.",
    ("SIEMENS_S210_2019_A01784", 16):
        "If the brake closing time of the motor holding brake (p1217) has been set too low, then at the start of the brake test, the brake\nis closed too late.",
    ("SIEMENS_S210_2019_F01033", 0):
        "When changing over the units to the referred representation type, it is not permissible for any of the required reference\nparameters to be equal to 0.0",
    ("SIEMENS_S210_2019_F01663", 0):
        "The copy function for Safety Integrated parameters is initiated using the commissioning tool.\nThis is the reason that when booting, an attempt is made to copy Safety Integrated parameters from monitoring channel 1\nto monitoring channel 2. However, no safety-relevant function has been selected in monitoring channel 1 (p9501 = 0, p9601\n= 0). Copying was rejected for safety reasons.",
    ("SIEMENS_S210_2019_F07412", 11):
        "1: The change in the speed signal from the motor encoder has changed by > p0492 within a current controller clock cycle.",
}


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


def _find_source_span(source: str, value: str) -> tuple[int, int] | None:
    exact = source.find(value)
    if exact >= 0:
        return exact, exact + len(value)

    value_tokens = _tokens(value)
    source_tokens = _tokens(source)
    if not value_tokens:
        return None

    candidates: list[tuple[int, int, int]] = []
    first = value_tokens[0][0]
    last = value_tokens[-1][0]
    for start_index, (token, start, _) in enumerate(source_tokens):
        if token != first:
            continue
        cursor = start_index
        matched = 1
        last_end = source_tokens[start_index][2]
        for expected in value_tokens[1:]:
            found = None
            for index in range(cursor + 1, min(len(source_tokens), cursor + 13)):
                if source_tokens[index][0] == expected[0]:
                    found = index
                    break
            if found is None:
                break
            cursor = found
            last_end = source_tokens[found][2]
            matched += 1
        if matched == len(value_tokens) and source_tokens[cursor][0] == last:
            candidates.append((matched, start, last_end))

    if not candidates:
        return None
    _, start, end = min(candidates, key=lambda item: (item[2] - item[1], item[1]))
    return start, end


def _repair_spans(sample: dict[str, Any]) -> tuple[int, int]:
    source = str(sample.get("input_text") or "")
    spans = sample.get("evidence_spans")
    if not isinstance(spans, list):
        spans = []
        sample["evidence_spans"] = spans

    exact_repairs = 0
    added_cause_spans = 0

    for span in spans:
        start = span.get("start")
        end = span.get("end")
        if isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(source):
            actual = source[start:end]
            if span.get("quote") != actual:
                span["quote"] = actual
                exact_repairs += 1

    existing_causes = {
        int(span.get("value_index"))
        for span in spans
        if span.get("field") == "cause" and isinstance(span.get("value_index"), int)
    }
    records = sample.get("gold_records") or []
    sample_id = str(sample.get("sample_id") or "")
    for record in records:
        for value_index, cause in enumerate(record.get("causes") or []):
            if value_index in existing_causes:
                continue
            match = _find_source_span(source, str(cause))
            if match is None:
                fallback = FALLBACK_CAUSE_SOURCE.get((sample_id, value_index))
                if fallback:
                    match = _find_source_span(source, fallback)
            if match is None:
                continue
            start, end = match
            item: dict[str, Any] = {
                "field": "cause",
                "source_id": "input_text",
                "quote": source[start:end],
                "start": start,
                "end": end,
                "value_index": value_index,
            }
            record_id = record.get("record_id")
            if record_id:
                item["record_id"] = record_id
            spans.append(item)
            existing_causes.add(value_index)
            added_cause_spans += 1

    return exact_repairs, added_cause_spans


def repair(dataset: dict[str, Any]) -> dict[str, Any]:
    result = dataset
    exact_repairs = 0
    added_cause_spans = 0
    unresolved_causes: list[str] = []
    for sample in result.get("samples") or []:
        repaired, added = _repair_spans(sample)
        exact_repairs += repaired
        added_cause_spans += added
        source = str(sample.get("input_text") or "")
        existing = {
            int(span.get("value_index"))
            for span in sample.get("evidence_spans") or []
            if span.get("field") == "cause" and isinstance(span.get("value_index"), int)
        }
        for record in sample.get("gold_records") or []:
            for index, _ in enumerate(record.get("causes") or []):
                if index not in existing:
                    unresolved_causes.append(f"{sample.get('sample_id')} cause[{index}]")

    info = result.setdefault("dataset_info", {})
    info["component_evidence_policy"] = "allow_unstated_empty_component_for_public_manual"
    info["evidence_repair"] = {
        "exact_quote_repairs": exact_repairs,
        "added_cause_spans": added_cause_spans,
        "unresolved_cause_evidence": unresolved_causes,
        "gold_field_values_changed": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-json", required=True, type=Path)
    args = parser.parse_args()
    dataset = json.loads(args.dataset_json.read_text(encoding="utf-8"))
    result = repair(dataset)
    args.dataset_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["dataset_info"]["evidence_repair"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
