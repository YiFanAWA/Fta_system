#!/usr/bin/env python3
"""Build canonical soft-logic training JSONL from existing public gold sources.

The output is intentionally provider-neutral. It can later be converted to a
vendor-specific SFT format, while preserving provenance and hard-constraint
metadata in this canonical form.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "soft_logic_training.v1"
TASK = "fault_record_and_causal_candidate_extraction"
SOURCE_LOGBOOK = "Annotated Maintenance Logbook"
SOURCE_OMIN = "OMIn Dataset"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _preserve_input_text(value: Any) -> str:
    """Keep the exact source text because evidence offsets refer to it.

    Normalization is allowed for comparisons and labels, but the canonical
    input must remain byte-for-character stable with the source dataset's
    assembled text. Otherwise ``start_char``/``end_char`` evidence offsets
    silently point at the wrong characters.
    """
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _stable_split(sample_id: str, *, force_test: bool = False) -> str:
    if force_test:
        return "test"
    bucket = int(hashlib.sha256(sample_id.encode("utf-8")).hexdigest(), 16) % 100
    if bucket < 15:
        return "dev"
    if bucket < 35:
        return "test"
    return "train"


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _gate_candidate(text: str, causes: list[str]) -> dict[str, Any]:
    """Return a weak candidate only for explicit language cues.

    A causal annotation alone never becomes OR.  This is deliberately
    conservative because a cause edge and an FTA gate have different meanings.
    """
    lowered = text.casefold()
    if re.search(r"\b(?:or|either|alternatively)\b|或|任一|任选", lowered):
        gate = "OR"
        status = "explicit_source_candidate"
    elif re.search(
        r"\b(?:both|simultaneously|together|jointly)\b|同时|共同|必须.*(?:and|且|以及)",
        lowered,
    ):
        gate = "AND"
        status = "explicit_source_candidate"
    else:
        gate = None
        status = "source_relation_only" if causes else "unknown"
    return {
        "parent_path": "target.records[0]",
        "gate_candidate": gate,
        "confidence": 0.55 if gate else None,
        "status": status,
        "evidence_refs": [],
        "reason": "explicit lexical cue" if gate else "causal relation does not determine an FTA gate",
    }


def _make_sample(
    sample: dict[str, Any],
    *,
    dataset_override: str | None = None,
    force_test: bool = False,
) -> dict[str, Any]:
    sample_id = _clean(sample.get("sample_id"))
    if not sample_id:
        raise ValueError("source sample is missing sample_id")
    input_text = _preserve_input_text(sample.get("input_text"))
    if not input_text.strip():
        raise ValueError(f"{sample_id} is missing input_text")

    source = dict(sample.get("source") or {})
    annotation = dict(sample.get("annotation") or {})
    records = _safe_list(sample.get("gold_records"))
    relations = _safe_list(sample.get("gold_relations"))
    evidence_spans = _safe_list(sample.get("evidence_spans"))
    top_event = sample.get("gold_top_event")
    first_record = records[0] if records and isinstance(records[0], dict) else {}
    causes = [_clean(cause) for cause in _safe_list(first_record.get("causes")) if _clean(cause)]

    logic_candidate = _gate_candidate(input_text, causes)
    for span in evidence_spans:
        if not isinstance(span, dict):
            continue
        target_path = str(span.get("target_path") or "")
        if target_path.startswith("gold_records[0].causes"):
            logic_candidate["evidence_refs"].append(target_path)

    return {
        "schema_version": SCHEMA_VERSION,
        "sample_id": sample_id,
        "split": "test" if force_test else str(sample.get("split") or _stable_split(sample_id)),
        "task": TASK,
        "input_text": input_text,
        "target": {
            "top_event": top_event,
            "records": records,
            "relations": relations,
            "logic_candidates": [logic_candidate],
        },
        "evidence_spans": evidence_spans,
        "hard_constraints": {
            "allowed_gates": ["AND", "OR", None],
            "unknown_gate_policy": "keep_unknown",
            "require_evidence_for_records": True,
        },
        "provenance": {
            "dataset": dataset_override or source.get("dataset") or "unknown",
            "record_id": source.get("record_id"),
            "url": source.get("url"),
            "license": source.get("license"),
            "label_status": annotation.get(
                "label_status", sample.get("source_type", "source_annotated_provisional")
            ),
            "human_expert_reviewed": bool(annotation.get("human_expert_reviewed", False)),
        },
    }


def _load_json_sources(paths: Iterable[Path]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        samples = payload.get("samples") if isinstance(payload, dict) else None
        if not isinstance(samples, list):
            raise ValueError(f"{path} does not contain a samples list")
        dataset = ((payload.get("dataset_info") or {}).get("source") or {}).get("dataset")
        force_test = "project_handbook" in path.name
        for sample in samples:
            if isinstance(sample, dict):
                output.append(_make_sample(sample, dataset_override=dataset, force_test=force_test))
    return output


def _parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            parsed = []
    return [str(item).strip() for item in parsed] if isinstance(parsed, list) else []


def _find_text_column(fieldnames: list[str]) -> str:
    for candidate in ("c119", "text", "description", "narrative"):
        if candidate in fieldnames:
            return candidate
    raise ValueError("OMIn text CSV does not contain a supported narrative column")


def _build_span(text: str, value: str, target_path: str, source_column: str) -> dict[str, Any] | None:
    value = _clean(value)
    start = text.casefold().find(value.casefold()) if value else -1
    if start < 0:
        return None
    return {
        "target_type": "field",
        "target_path": target_path,
        "evidence_text": text[start : start + len(value)],
        "start_char": start,
        "end_char": start + len(value),
        "source_column": source_column,
        "evidence_status": "literal_match",
    }


def _load_omin(
    text_csv: Path,
    ner_csv: Path,
    re_csv: Path | None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    text_rows: dict[str, dict[str, str]] = {}
    with text_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        text_column = _find_text_column(fieldnames)
        id_column = "c5" if "c5" in fieldnames else fieldnames[1]
        for row in reader:
            record_id = _clean(row.get(id_column))
            text = _clean(row.get(text_column))
            if record_id and text:
                text_rows[record_id] = {"text": text, "source_row": row}

    entities: dict[str, list[dict[str, str]]] = {}
    with ner_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            record_id = _clean(row.get("c5_unique_id") or row.get("id"))
            if not record_id or record_id not in text_rows:
                continue
            values = _parse_json_list(row.get("GS", "[]"))
            types = _parse_json_list(row.get("GS TYPE", "[]"))
            for index, value in enumerate(values):
                entities.setdefault(record_id, []).append(
                    {"value": _clean(value), "type": types[index] if index < len(types) else "UNKNOWN"}
                )

    relations: dict[str, list[dict[str, str]]] = {}
    if re_csv is not None and re_csv.exists():
        with re_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                record_id = _clean(row.get("id"))
                if not record_id or record_id not in text_rows:
                    continue
                relations.setdefault(record_id, []).append(
                    {
                        "cause": _clean(row.get("subject")),
                        "relation": _clean(row.get("relation")),
                        "effect": _clean(row.get("object")),
                        "relation_type": _clean(row.get("relation_type")),
                    }
                )

    samples: list[dict[str, Any]] = []
    for record_id in sorted(text_rows):
        if limit is not None and len(samples) >= limit:
            break
        text = text_rows[record_id]["text"]
        entity_rows = entities.get(record_id, [])
        failures = [item["value"] for item in entity_rows if item["type"] in {"FAILURE", "SYMPTOM"}]
        components = [item["value"] for item in entity_rows if item["type"] in {"SYS", "COMPONENT"}]
        causes = [item["value"] for item in entity_rows if item["type"] == "CAUSE"]
        description = failures[0] if failures else text[:240]
        record = {
            "fault_code": None,
            "component": components[0] if components else None,
            "description": description,
            "causes": causes,
            "parameters": [],
        }
        spans: list[dict[str, Any]] = []
        for field_name, value, source_column in (
            ("description", description, "GS/FAILURE_OR_SYMPTOM"),
            ("component", components[0] if components else "", "GS/SYS"),
        ):
            span = _build_span(text, value, f"gold_records[0].{field_name}", source_column)
            if span:
                spans.append(span)
        for index, cause in enumerate(causes):
            span = _build_span(text, cause, f"gold_records[0].causes[{index}]", "GS/CAUSE")
            if span:
                spans.append(span)
        source = {
            "dataset": SOURCE_OMIN,
            "record_id": record_id,
            "url": "https://github.com/nd-crane/trusted_ke",
            "license": "Apache-2.0 repository; verify data terms before redistribution",
        }
        raw_sample = {
            "sample_id": f"OMIN-{record_id}",
            "split": _stable_split(record_id),
            "source_type": "public_annotated_maintenance",
            "input_text": text,
            "gold_top_event": description,
            "gold_records": [record],
            "gold_relations": relations.get(record_id, []),
            "evidence_spans": spans,
            "source": source,
            "annotation": {
                "label_status": "source_annotated_provisional",
                "human_expert_reviewed": False,
            },
        }
        samples.append(_make_sample(raw_sample, dataset_override=SOURCE_OMIN))
    return samples


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", action="append", default=[], help="Existing normalized dataset JSON")
    parser.add_argument("--omin-text-csv", type=Path)
    parser.add_argument("--omin-ner-csv", type=Path)
    parser.add_argument("--omin-re-csv", type=Path)
    parser.add_argument("--omin-limit", type=int, default=100)
    parser.add_argument("--mendeley-fault-events", type=Path, help="Reserved for the vehicle adapter")
    parser.add_argument("--mendeley-ner", type=Path, help="Reserved for the vehicle adapter")
    parser.add_argument("--mendeley-kg", type=Path, help="Reserved for the vehicle adapter")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.mendeley_fault_events or args.mendeley_ner or args.mendeley_kg:
        raise SystemExit(
            "Mendeley vehicle adapter is intentionally gated until all three files are supplied "
            "and their published column contract has been verified."
        )
    if not args.input_json and not (args.omin_text_csv and args.omin_ner_csv):
        raise SystemExit("provide --input-json or both --omin-text-csv and --omin-ner-csv")

    samples = _load_json_sources([Path(path) for path in args.input_json])
    if args.omin_text_csv and args.omin_ner_csv:
        samples.extend(
            _load_omin(
                args.omin_text_csv,
                args.omin_ner_csv,
                args.omin_re_csv,
                limit=args.omin_limit,
            )
        )

    seen: set[str] = set()
    deduplicated: list[dict[str, Any]] = []
    for sample in sorted(samples, key=lambda item: item["sample_id"]):
        if sample["sample_id"] in seen:
            continue
        seen.add(sample["sample_id"])
        deduplicated.append(sample)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for sample in deduplicated:
            handle.write(json.dumps(sample, ensure_ascii=False, separators=(",", ":")) + "\n")

    counts = {split: sum(item["split"] == split for item in deduplicated) for split in ("train", "dev", "test")}
    unknown_gates = sum(
        item["target"]["logic_candidates"][0]["gate_candidate"] is None
        for item in deduplicated
        if item["target"]["logic_candidates"]
    )
    print(f"[ok] wrote {args.output} samples={len(deduplicated)} split={counts} unknown_gate={unknown_gates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
