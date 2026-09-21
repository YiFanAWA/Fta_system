"""Audit pending candidate structure before semantic expert review.

This is a read-only gate.  It never changes review decisions and never turns a
candidate into a gold record.  It identifies missing or ambiguous field-level
evidence so the expert can focus on semantic questions rather than formatting.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _field_spans(row: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for span in row.get("evidence_spans") or []:
        result.setdefault(str(span.get("field") or ""), []).append(span)
    return result


def _has_indexed_span(spans: list[dict[str, Any]], index: int) -> bool:
    return any(span.get("value_index") == index for span in spans)


def audit_pending_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    pending_rows = [
        row for row in dataset.get("samples", []) if (row.get("review_queue") or {}).get("status") == "pending"
    ]

    for row in pending_rows:
        sample_id = str(row.get("sample_id") or "")
        prediction = row.get("model_prediction") or {}
        records = prediction.get("records") or []
        spans_by_field = _field_spans(row)
        row_codes: list[str] = []
        if len(records) != 1:
            row_codes.append("record_count_not_one")
        record = records[0] if len(records) == 1 else {}

        required_scalar_fields = {
            "fault_code": "fault_code",
            "description": "description",
        }
        for record_field, evidence_field in required_scalar_fields.items():
            if str(record.get(record_field) or "").strip() and not spans_by_field.get(evidence_field):
                row_codes.append(f"missing_{evidence_field}_evidence")

        component = str(record.get("component") or "").strip()
        if component and not (
            spans_by_field.get("primary_component") or spans_by_field.get("component")
        ):
            row_codes.append("missing_primary_component_evidence")
        if not component and not (
            spans_by_field.get("component_declaration")
            or spans_by_field.get("driver_object_declaration")
        ):
            row_codes.append("empty_component_without_explicit_declaration")

        related = list(record.get("related_components") or [])
        related_spans = spans_by_field.get("related_component") or []
        for index, value in enumerate(related):
            if not _has_indexed_span(related_spans, index):
                row_codes.append(f"missing_related_component_evidence:{index}")

        causes = list(record.get("causes") or [])
        cause_spans = spans_by_field.get("cause") or []
        for index, value in enumerate(causes):
            if not _has_indexed_span(cause_spans, index):
                row_codes.append(f"missing_cause_evidence:{index}")
            elif str(value).strip() and not any(
                str(span.get("quote") or "").strip() and str(value).strip() in str(span.get("quote") or "")
                for span in cause_spans
                if span.get("value_index") == index
            ):
                row_codes.append(f"cause_needs_semantic_review:{index}")

        parameters = list(record.get("parameters") or [])
        parameter_spans = spans_by_field.get("parameter") or []
        for index, value in enumerate(parameters):
            if not _has_indexed_span(parameter_spans, index):
                row_codes.append(f"missing_parameter_evidence:{index}")

        for code in row_codes:
            counters[code.split(":", 1)[0]] += 1
        findings.append({"sample_id": sample_id, "codes": row_codes})

    return {
        "dataset": dataset.get("dataset_info", {}).get("name"),
        "pending_records": len(pending_rows),
        "rows_with_findings": sum(bool(item["codes"]) for item in findings),
        "rows_clean_structurally": sum(not item["codes"] for item in findings),
        "finding_counts": dict(sorted(counters.items())),
        "findings": findings,
        "decision": "结构审计不等于语义审核；不得据此自动批准",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    report = audit_pending_dataset(_load(args.queue_json))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("pending_records", "rows_with_findings", "rows_clean_structurally", "finding_counts")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
