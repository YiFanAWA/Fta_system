#!/usr/bin/env python3
"""Build a provisional, source-annotated evidence dataset from a public CSV.

The input is the CC BY 4.0 Annotated Maintenance Logbook dataset.  This
builder deliberately keeps source annotations separate from expert FTA
judgement: it copies only the source columns, attaches literal spans when a
value occurs in the assembled input text, and marks the remaining FTA fields
as unknown.

Example:
  python evaluation/quality_eval/public_evidence/build_public_evidence_dataset.py \
    --input "ANNOTATED LOGBOOK. Refinement according to expert feedback.csv" \
    --output evaluation/quality_eval/datasets/fta_public_logbook_evidence.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = (
    ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_public_logbook_evidence.json"
)

SOURCE_DATASET = "Annotated Maintenance Logbook"
SOURCE_DOI = "10.5281/zenodo.20779601"
SOURCE_URL = "https://zenodo.org/records/20779601"
SOURCE_LICENSE = "CC BY 4.0"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").casefold())


def _split_for_key(value: str) -> str:
    digest = int(hashlib.sha256(_normalize(value).encode("utf-8")).hexdigest(), 16)
    bucket = digest % 100
    if bucket < 15:
        return "dev"
    if bucket < 35:
        return "test"
    return "train"


def _append_source_line(
    lines: List[str],
    spans: Dict[str, Tuple[int, int]],
    label: str,
    source_column: str,
    value: str,
) -> None:
    if not value:
        return
    prefix = f"{label}: "
    start = sum(len(line) + 1 for line in lines) + len(prefix)
    lines.append(prefix + value)
    spans[source_column] = (start, start + len(value))


def _find_literal(text: str, value: str) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    direct = text.find(value)
    if direct >= 0:
        return direct, direct + len(value)

    lowered_text = text.casefold()
    lowered_value = value.casefold()
    direct = lowered_text.find(lowered_value)
    if direct >= 0:
        return direct, direct + len(value)
    return None


def _evidence(
    input_text: str,
    value: str,
    target_path: str,
    source_column: str,
) -> Optional[Dict[str, Any]]:
    location = _find_literal(input_text, value)
    if location is None:
        return None
    start, end = location
    return {
        "target_type": "field",
        "target_path": target_path,
        "evidence_text": input_text[start:end],
        "start_char": start,
        "end_char": end,
        "source_column": source_column,
        "evidence_status": "literal_match",
    }


def _evidence_at_source_span(
    input_text: str,
    source_spans: Dict[str, Tuple[int, int]],
    source_column: str,
    target_path: str,
) -> Optional[Dict[str, Any]]:
    location = source_spans.get(source_column)
    if location is None:
        return None
    start, end = location
    return {
        "target_type": "field",
        "target_path": target_path,
        "evidence_text": input_text[start:end],
        "start_char": start,
        "end_char": end,
        "source_column": source_column,
        "evidence_status": "literal_match",
    }


def _evidence_in_source_field(
    input_text: str,
    source_spans: Dict[str, Tuple[int, int]],
    value: str,
    target_path: str,
) -> Optional[Dict[str, Any]]:
    for source_column, (field_start, field_end) in source_spans.items():
        field_text = input_text[field_start:field_end]
        location = _find_literal(field_text, value)
        if location is None:
            continue
        relative_start, relative_end = location
        start = field_start + relative_start
        end = field_start + relative_end
        return {
            "target_type": "field",
            "target_path": target_path,
            "evidence_text": input_text[start:end],
            "start_char": start,
            "end_char": end,
            "source_column": source_column,
            "evidence_status": "literal_match",
        }
    return None


def _build_input(row: Dict[str, str]) -> Tuple[str, Dict[str, Tuple[int, int]]]:
    lines: List[str] = []
    spans: Dict[str, Tuple[int, int]] = {}
    _append_source_line(lines, spans, "Problem", "PROBLEM", _clean(row.get("PROBLEM")))
    _append_source_line(lines, spans, "Location", "LOCATION", _clean(row.get("LOCATION")))
    _append_source_line(
        lines,
        spans,
        "Problem part",
        "PROBLEM_PART",
        _clean(row.get("PROBLEM_PART")),
    )
    _append_source_line(lines, spans, "Effect", "EFFECT", _clean(row.get("EFFECT")))
    _append_source_line(lines, spans, "Action", "ACTION", _clean(row.get("ACTION")))
    _append_source_line(
        lines,
        spans,
        "Action part",
        "ACTION_PART",
        _clean(row.get("ACTION_PART")),
    )
    return "\n".join(lines), spans


def _build_sample(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    source_id = _clean(row.get("IDENT"))
    problem = _clean(row.get("PROBLEM"))
    cause = _clean(row.get("CAUSE"))
    if not source_id or not problem or not cause:
        return None

    location = _clean(row.get("LOCATION"))
    problem_part = _clean(row.get("PROBLEM_PART"))
    component = problem_part or location
    input_text, source_spans = _build_input(row)

    record: Dict[str, Any] = {
        "fault_code": None,
        "component": component or None,
        "description": problem,
        "causes": [cause],
        "parameters": [],
    }

    evidence_spans: List[Dict[str, Any]] = []
    description_evidence = _evidence_at_source_span(
        input_text,
        source_spans,
        "PROBLEM",
        "gold_records[0].description",
    )
    if description_evidence:
        evidence_spans.append(description_evidence)

    if component:
        component_column = "PROBLEM_PART" if problem_part else "LOCATION"
        component_evidence = _evidence_at_source_span(
            input_text,
            source_spans,
            component_column,
            "gold_records[0].component",
        )
        if component_evidence:
            evidence_spans.append(component_evidence)

    cause_evidence = _evidence_in_source_field(
        input_text,
        source_spans,
        cause,
        "gold_records[0].causes[0]",
    )
    if cause_evidence:
        evidence_spans.append(cause_evidence)

    relation: Dict[str, Any] = {
        "cause": cause,
        "effect": problem,
        "relation": "CAUSES",
        "relation_status": "source_annotated_provisional",
    }

    return {
        "sample_id": f"PL-{source_id}",
        "split": _split_for_key(input_text),
        "source_type": "public_annotated_logbook",
        "difficulty_tag": "easy" if len(input_text) < 280 else "medium",
        "input_text": input_text,
        "gold_top_event": problem,
        "gold_records": [record],
        "gold_relations": [relation],
        "evidence_spans": evidence_spans,
        "expected_metrics_tags": {
            "count_for_legality": True,
            "count_for_hallucination": True,
            "count_for_fta_productivity": False,
            "count_for_evidence": True,
            "count_for_causal_logic": False,
        },
        "source": {
            "dataset": SOURCE_DATASET,
            "record_id": source_id,
            "url": SOURCE_URL,
            "doi": SOURCE_DOI,
            "license": SOURCE_LICENSE,
            "source_columns": {
                "description": "PROBLEM",
                "component": "PROBLEM_PART or LOCATION",
                "cause": "CAUSE",
                "relation": "CAUSE -> PROBLEM source annotation",
            },
        },
        "annotation": {
            "label_status": "source_annotated_provisional",
            "human_expert_reviewed": False,
            "evidence_policy": "only literal spans in assembled input are evidence",
            "unknown_fields": ["fault_code", "parameters", "gate"],
            "causal_logic_status": "unknown",
        },
        "notes": (
            "The source row provides a provisional problem/cause annotation. "
            "It is not an expert-approved FTA tree and must not be used to "
            "auto-approve production reviews."
        ),
    }


def _read_rows(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def build_dataset(input_path: Path) -> Dict[str, Any]:
    samples = [sample for row in _read_rows(input_path) if (sample := _build_sample(row))]
    samples.sort(key=lambda item: item["sample_id"])

    split_counts = {split: sum(item["split"] == split for item in samples) for split in ("train", "dev", "test")}
    evidence_counts = {
        "samples": len(samples),
        "with_literal_evidence": sum(bool(item["evidence_spans"]) for item in samples),
        "with_cause_evidence": sum(
            any(span["target_path"] == "gold_records[0].causes[0]" for span in item["evidence_spans"])
            for item in samples
        ),
    }

    return {
        "dataset_info": {
            "name": "fta_public_logbook_evidence",
            "version": "1.0.0",
            "language": "en",
            "task": "evidence_grounded_fault_record_extraction",
            "description": "Provisional evidence set generated from a public annotated maintenance logbook.",
            "created_at": date.today().isoformat(),
            "owner": "project_evaluation",
            "label_status": "source_annotated_provisional",
            "warning": (
                "This is not an expert-approved FTA gold set. Source annotations are "
                "preserved with provenance; gate logic, fault codes, and parameters "
                "remain unknown unless separately verified."
            ),
            "source": {
                "dataset": SOURCE_DATASET,
                "url": SOURCE_URL,
                "doi": SOURCE_DOI,
                "license": SOURCE_LICENSE,
            },
            "stats": {
                "total": len(samples),
                "split": split_counts,
                "evidence": evidence_counts,
            },
        },
        "label_schema": {
            "record_fields": ["fault_code", "component", "description", "causes", "parameters"],
            "evidence_span_fields": ["description", "component", "causes[0]"],
            "unknown_policy": "Do not infer unobserved fault_code, parameters, or gate logic.",
        },
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the downloaded public CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    payload = build_dataset(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = payload["dataset_info"]["stats"]
    print(
        f"[ok] wrote {output} samples={stats['total']} "
        f"split={stats['split']} evidence={stats['evidence']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
