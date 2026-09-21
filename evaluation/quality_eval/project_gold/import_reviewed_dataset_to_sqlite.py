#!/usr/bin/env python3
"""Import a fully resolved reviewed dataset into SQLite atomically and idempotently."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from extraction_contract import EvidenceField, EvidenceSpan, ExtractionResult, ExtractionStatus, FaultRecord  # noqa: E402
from review_contract import FaultRecordReview, ReviewStatus  # noqa: E402
from sqlite_extraction_repository import SQLiteExtractionWorkflowRepository  # noqa: E402


_APPROVED_DECISIONS = {"审核通过", "approved", "approve"}
_REVISED_DECISIONS = {"语义需修改", "revision", "revised"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("samples"), list):
        raise ValueError("reviewed dataset must contain a samples list")
    return value


def _review_datetime(review: dict[str, Any]) -> datetime:
    value = review.get("review_date") or review.get("created_at")
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _reviewer(review: dict[str, Any]) -> str:
    value = review.get("reviewer") or review.get("reviewer_name")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("resolved records require reviewer/reviewer_name")
    return value.strip()


def _decision(review: dict[str, Any]) -> str:
    value = review.get("decision") or review.get("status")
    return str(value or "").strip().casefold()


def _record_id(dataset_name: str, version: str, sample_id: str, position: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"fta-record:{dataset_name}:{version}:{sample_id}:{position}"))


def _result_id(dataset_name: str, version: str, sample_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"fta-result:{dataset_name}:{version}:{sample_id}"))


def _build_records(
    dataset_name: str,
    version: str,
    sample: dict[str, Any],
) -> tuple[tuple[FaultRecord, ...], dict[str, str]]:
    sample_id = str(sample.get("sample_id", "")).strip()
    gold_records = sample.get("gold_records")
    if not sample_id or not isinstance(gold_records, list) or not gold_records:
        raise ValueError(f"{sample_id or '<missing sample_id>'} has no resolved gold_records")

    records: list[FaultRecord] = []
    old_to_new: dict[str, str] = {}
    for position, payload in enumerate(gold_records):
        if not isinstance(payload, dict):
            raise ValueError(f"{sample_id} gold record {position} is not an object")
        record = FaultRecord(
            fault_code=payload.get("fault_code"),
            component=payload.get("component"),
            related_components=tuple(payload.get("related_components") or ()),
            description=str(payload.get("description") or "").strip(),
            causes=tuple(payload.get("causes") or ()),
            parameters=tuple(payload.get("parameters") or ()),
        )
        new_id = _record_id(dataset_name, version, sample_id, position)
        object.__setattr__(record, "record_id", new_id)
        records.append(record)
        old_id = payload.get("record_id")
        if old_id:
            old_to_new[str(old_id)] = new_id
    return tuple(records), old_to_new


def _build_evidence(
    sample: dict[str, Any],
    records: tuple[FaultRecord, ...],
    old_to_new: dict[str, str],
) -> tuple[EvidenceSpan, ...]:
    source = str(sample.get("input_text") or "")
    raw_spans = sample.get("evidence_spans")
    if not isinstance(raw_spans, list):
        raise ValueError(f"{sample.get('sample_id')} has no evidence_spans")
    spans: list[EvidenceSpan] = []
    for raw in raw_spans:
        if not isinstance(raw, dict):
            raise ValueError("evidence span is not an object")
        old_record_id = str(raw.get("record_id") or "")
        if old_record_id in old_to_new:
            record_id = old_to_new[old_record_id]
        elif len(records) == 1:
            record_id = records[0].record_id
        else:
            raise ValueError(f"{sample.get('sample_id')} evidence cannot identify its record")
        field = raw.get("field")
        quote = raw.get("quote")
        start = raw.get("start")
        end = raw.get("end")
        if not isinstance(quote, str) or not isinstance(start, int) or not isinstance(end, int):
            raise ValueError(f"{sample.get('sample_id')} has incomplete evidence offsets")
        if start < 0 or end <= start or source[start:end] != quote:
            raise ValueError(f"{sample.get('sample_id')} has evidence that does not match input_text")
        spans.append(
            EvidenceSpan(
                record_id=record_id,
                field=EvidenceField(field),
                source_id=str(raw.get("source_id") or "input_text"),
                quote=quote,
                start=start,
                end=end,
                value_index=raw.get("value_index"),
            )
        )
    return tuple(spans)


def _validate_field_evidence(
    sample_id: str,
    records: tuple[FaultRecord, ...],
    spans: tuple[EvidenceSpan, ...],
    *,
    allow_unstated_empty_component: bool = False,
) -> None:
    by_record: dict[str, set[EvidenceField]] = {}
    for span in spans:
        by_record.setdefault(span.record_id, set()).add(span.field)
    for record in records:
        fields = by_record.get(record.record_id, set())
        if record.fault_code and EvidenceField.FAULT_CODE not in fields:
            raise ValueError(f"{sample_id} missing fault_code evidence")
        if EvidenceField.DESCRIPTION not in fields:
            raise ValueError(f"{sample_id} missing description evidence")
        if record.component:
            if not ({EvidenceField.PRIMARY_COMPONENT, EvidenceField.COMPONENT} & fields):
                raise ValueError(f"{sample_id} missing primary component evidence")
        elif (
            not allow_unstated_empty_component
            and not ({EvidenceField.COMPONENT_DECLARATION, EvidenceField.DRIVER_OBJECT_DECLARATION} & fields)
        ):
            raise ValueError(f"{sample_id} missing explicit empty-component evidence")
        if record.related_components and EvidenceField.RELATED_COMPONENT not in fields:
            raise ValueError(f"{sample_id} missing related component evidence")
        if record.causes and EvidenceField.CAUSE not in fields:
            raise ValueError(f"{sample_id} missing cause evidence")
        if record.parameters and EvidenceField.PARAMETER not in fields:
            raise ValueError(f"{sample_id} missing parameter evidence")


def _review_chain(sample: dict[str, Any], records: tuple[FaultRecord, ...]) -> tuple[FaultRecordReview, ...]:
    review = sample.get("expert_review") or sample.get("review")
    if not isinstance(review, dict):
        raise ValueError(f"{sample.get('sample_id')} has no expert review")
    decision = _decision(review)
    reviewer = _reviewer(review)
    created_at = _review_datetime(review)
    reason = str(review.get("opinion") or review.get("reason") or "final reviewed dataset import")
    if decision in _APPROVED_DECISIONS:
        return tuple(
            FaultRecordReview(
                record_id=record.record_id,
                status=ReviewStatus.APPROVED,
                reviewer=reviewer,
                reason=reason,
                created_at=created_at,
            )
            for record in records
        )
    if decision in _REVISED_DECISIONS and bool(review.get("correction_applied")):
        return tuple(
            item
            for record in records
            for item in (
                FaultRecordReview(
                    record_id=record.record_id,
                    status=ReviewStatus.REVISION,
                    reviewer=reviewer,
                    reason=reason,
                    created_at=created_at,
                ),
                FaultRecordReview(
                    record_id=record.record_id,
                    status=ReviewStatus.APPROVED,
                    reviewer=reviewer,
                    reason="resolved after correction",
                    created_at=created_at,
                ),
            )
        )
    raise ValueError(
        f"{sample.get('sample_id')} is not resolved; decision={review.get('decision')!r}"
    )


def import_dataset(
    dataset: dict[str, Any],
    database_path: str | Path,
    *,
    expected_records: int = 281,
) -> dict[str, Any]:
    info = dataset.get("dataset_info") or {}
    dataset_name = str(info.get("name") or "").strip()
    version = str(info.get("version") or "").strip()
    samples = dataset["samples"]
    if not dataset_name or not version:
        raise ValueError("dataset_info.name and dataset_info.version are required")
    if len(samples) != expected_records:
        raise ValueError(f"expected {expected_records} samples, got {len(samples)}")
    if info.get("eligible_for_training") is True:
        raise ValueError("evaluation dataset must not be training eligible")

    prepared: list[tuple[str, ExtractionResult, tuple[FaultRecordReview, ...], dict[str, Any]]] = []
    seen: set[str] = set()
    for sample in samples:
        sample_id = str(sample.get("sample_id") or "").strip()
        if not sample_id or sample_id in seen:
            raise ValueError(f"duplicate or missing sample_id: {sample_id!r}")
        seen.add(sample_id)
        records, old_to_new = _build_records(dataset_name, version, sample)
        spans = _build_evidence(sample, records, old_to_new)
        allow_unstated_empty_component = (
            info.get("component_evidence_policy")
            == "allow_unstated_empty_component_for_public_manual"
            and str(sample.get("source_type") or "")
            in {"public_manual_fault_corpus", "public_s210_manual"}
        )
        _validate_field_evidence(
            sample_id,
            records,
            spans,
            allow_unstated_empty_component=allow_unstated_empty_component,
        )
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=records,
            evidence_spans=spans,
        )
        object.__setattr__(extraction, "result_id", _result_id(dataset_name, version, sample_id))
        reviews = _review_chain(sample, records)
        prepared.append((sample_id, extraction, reviews, sample))

    repository = SQLiteExtractionWorkflowRepository(database_path)
    import_id = str(uuid5(NAMESPACE_URL, f"fta-dataset-import:{dataset_name}:{version}"))
    source_corpus = str(info.get("source") or info.get("source_corpus") or "reviewed_dataset")
    with repository._connect() as connection:  # the adapter owns the transaction boundary
        existing = connection.execute(
            "SELECT status, record_count FROM dataset_imports WHERE dataset_name = ? AND dataset_version = ?",
            (dataset_name, version),
        ).fetchone()
        if existing is not None:
            if existing["status"] == "completed" and int(existing["record_count"]) == expected_records:
                return {"status": "already_imported", "import_id": import_id, "records": expected_records}
            raise ValueError("dataset import exists but is incomplete or inconsistent")
        try:
            connection.execute(
                "INSERT INTO dataset_imports(import_id, dataset_name, dataset_version, source_corpus, record_count, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (import_id, dataset_name, version, source_corpus, expected_records, "running", datetime.now(timezone.utc).isoformat()),
            )
            for sample_id, extraction, reviews, sample in prepared:
                repository._insert_result(connection, extraction)
                for review in reviews:
                    repository._insert_review(connection, review)
                provenance = sample.get("provenance") or {}
                primary_record_id = extraction.records[0].record_id
                connection.execute(
                    "INSERT INTO dataset_import_records(import_id, sample_id, result_id, record_id, source_file, source_url, source_sha256, source_page_start, source_page_end, source_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        import_id,
                        sample_id,
                        extraction.result_id,
                        primary_record_id,
                        provenance.get("source_file") or provenance.get("source_pdf"),
                        provenance.get("source_url") or provenance.get("official_reference_url"),
                        provenance.get("source_sha256"),
                        provenance.get("pdf_page_start"),
                        provenance.get("pdf_page_end"),
                        str(sample.get("input_text") or ""),
                    ),
                )
            connection.execute(
                "UPDATE dataset_imports SET status = ? WHERE import_id = ?",
                ("completed", import_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return {"status": "imported", "import_id": import_id, "records": expected_records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--expected-records", type=int, default=281)
    args = parser.parse_args()
    print(json.dumps(import_dataset(_load(args.dataset), args.database, expected_records=args.expected_records), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
