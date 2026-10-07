#!/usr/bin/env python3
"""Extract an unlabeled, whole-document holdout corpus from the Siemens S120/S150 List Manual."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Sequence

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - exercised by CLI environments without pypdf
    raise RuntimeError("This evaluation utility requires pypdf to read the local source PDF") from exc


DOCUMENT = "SINAMICS S120/S150 List Manual"
EDITION = "11/2023"
OFFICIAL_SOURCE_URL = (
    "https://cache.industry.siemens.com/dl/files/046/109827046/att_1164654/"
    "v1/S120_S150_list_man_1123_en-US.pdf?download=true"
)
OFFICIAL_SUPPORT_REFERENCE = "https://support.industry.siemens.com/cs/ww/en/view/109827046"
DEFAULT_START_PAGE = 2579
DEFAULT_END_PAGE = 3352
PAGE_SEPARATOR = "\n\f\n"

CODE_RE = re.compile(r"(?m)^(?P<code>[AFN]\d{5})[ \t]+(?P<title>[^\r\n]+)[ \t]*$")
CAUSE_RE = re.compile(r"(?im)^Cause\s*:\s*")
FIELD_RE = re.compile(
    r"(?im)^(?:Cause|Remedy|Response|Acknowledgment|"
    r"Acknowl\. upon|Note|See also|Message value|Message class|Drive object|"
    r"Component|Propagation|Product|Objects)\s*:"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _page_for_offset(offset: int, page_offsets: Sequence[int], start_page: int) -> int:
    page_index = 0
    for index, page_start in enumerate(page_offsets):
        if page_start > offset:
            break
        page_index = index
    return start_page + page_index


def _cause_sections(record_text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for index, match in enumerate(CAUSE_RE.finditer(record_text), start=1):
        value_start = match.end()
        next_field = FIELD_RE.search(record_text, value_start)
        value_end = next_field.start() if next_field else len(record_text)
        while value_end > value_start and record_text[value_end - 1].isspace():
            value_end -= 1
        if value_end <= value_start:
            continue
        sections.append(
            {
                "cause_section_id": f"cause-{index:02d}",
                "quote": record_text[value_start:value_end],
                "start": value_start,
                "end": value_end,
            }
        )
    return sections


def extract_records_from_pages(
    page_texts: Sequence[str],
    *,
    start_page: int,
    source_pdf_sha256: str,
    retrieved_date: str,
) -> tuple[str, list[dict[str, Any]]]:
    if not page_texts or any(not isinstance(text, str) for text in page_texts):
        raise ValueError("page_texts must contain at least one string")
    if start_page < 1:
        raise ValueError("start_page must be a positive PDF page number")

    page_offsets: list[int] = []
    cursor = 0
    for index, text in enumerate(page_texts):
        page_offsets.append(cursor)
        cursor += len(text)
        if index < len(page_texts) - 1:
            cursor += len(PAGE_SEPARATOR)
    full_text = PAGE_SEPARATOR.join(page_texts)
    matches = list(CODE_RE.finditer(full_text))
    if not matches:
        raise ValueError("no fault/alarm code headings found in the requested PDF pages")

    occurrence_by_code: dict[str, int] = {}
    records: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
        input_text = full_text[start:end]
        code = match.group("code")
        occurrence_by_code[code] = occurrence_by_code.get(code, 0) + 1
        pdf_page_start = _page_for_offset(start, page_offsets, start_page)
        pdf_page_end = _page_for_offset(max(start, end - 1), page_offsets, start_page)
        sample_id = (
            f"SIEMENS_S120_S150_2023_{code}_P{pdf_page_start:04d}_"
            f"N{occurrence_by_code[code]:03d}"
        )
        causes = _cause_sections(input_text)
        records.append(
            {
                "sample_id": sample_id,
                "split": "external_source_holdout",
                "source_type": "public_manual_fault_corpus",
                "input_text": input_text,
                "weak_record": {
                    "fault_code": code,
                    "description": match.group("title").strip(),
                    "causes_text": "\n".join(item["quote"] for item in causes) or None,
                    "cause_sections": causes,
                    "gate_type": None,
                },
                "annotation": {
                    "human_expert_reviewed": False,
                    "engineering_verified": False,
                    "label_status": "unlabeled_external_source_holdout",
                    "logic_status": "unknown",
                    "use_policy": "external_source_validation_or_expert_review_only",
                },
                "provenance": {
                    "source_document": DOCUMENT,
                    "edition": EDITION,
                    "source_pdf": "SINAMICS_S120_S150_List_Manual_11-2023_EN.pdf",
                    "source_pdf_sha256": source_pdf_sha256,
                    "source_cluster_id": f"external_source:{source_pdf_sha256}",
                    "source_url": OFFICIAL_SOURCE_URL,
                    "official_reference_url": OFFICIAL_SUPPORT_REFERENCE,
                    "section": "4.2 List of faults and alarms",
                    "pdf_page_start": pdf_page_start,
                    "pdf_page_end": pdf_page_end,
                    "source_offset_start": start,
                    "source_offset_end": end,
                    "record_text_sha256": sha256_bytes(input_text.encode("utf-8")),
                    "retrieved_date": retrieved_date,
                },
            }
        )
    return full_text, records


def build_corpus(
    pdf_path: Path,
    *,
    start_page: int = DEFAULT_START_PAGE,
    end_page: int = DEFAULT_END_PAGE,
    retrieved_date: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not pdf_path.is_file():
        raise FileNotFoundError(f"source PDF does not exist: {pdf_path}")
    if start_page < 1 or end_page < start_page:
        raise ValueError("PDF page range must be positive and ordered")

    source_pdf_sha256 = sha256_file(pdf_path)
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        raise ValueError("encrypted source PDFs are not supported")
    if end_page > len(reader.pages):
        raise ValueError(f"end_page {end_page} exceeds PDF page count {len(reader.pages)}")
    metadata = reader.metadata or {}
    title = str(metadata.get("/Title") or "")
    subject = str(metadata.get("/Subject") or "")
    if "S120/S150" not in title and "S120/S150" not in subject:
        raise ValueError("PDF metadata does not identify the expected SINAMICS S120/S150 manual")

    page_texts = [
        reader.pages[page_number - 1].extract_text() or ""
        for page_number in range(start_page, end_page + 1)
    ]
    if not any("4.2 List of faults and alarms" in text for text in page_texts[:3]):
        raise ValueError("the requested page range does not begin at section 4.2")
    if not any("4.2 List of faults and alarms" in text for text in page_texts[-3:]):
        raise ValueError("the requested page range does not end within section 4.2")

    extracted_text, records = extract_records_from_pages(
        page_texts,
        start_page=start_page,
        source_pdf_sha256=source_pdf_sha256,
        retrieved_date=retrieved_date or date.today().isoformat(),
    )
    sample_ids = [row["sample_id"] for row in records]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("extracted sample identifiers are not unique")

    corpus_bytes = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in records
    ).encode("utf-8")
    counts = {
        prefix: sum(row["weak_record"]["fault_code"].startswith(prefix) for row in records)
        for prefix in ("F", "A", "N")
    }
    manifest = {
        "dataset": "siemens_s120_s150_2023_public_fault_corpus_external_holdout",
        "version": "2.0.0",
        "supersedes_artifact": "siemens_s120_s150_2023_public_fault_corpus_holdout_v1",
        "supersession_reason": (
            "The cause-section boundary parser now keeps Fault/Alarm value subheadings that occur inside a Cause field. "
            "Raw extracted input_text and its offsets are unchanged."
        ),
        "artifact_type": "unlabeled_external_source_holdout_corpus_manifest",
        "label_status": "unlabeled_public_corpus",
        "human_expert_reviewed": False,
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "source_document": DOCUMENT,
        "edition": EDITION,
        "source_pdf": pdf_path.name,
        "source_pdf_sha256": source_pdf_sha256,
        "source_url": OFFICIAL_SOURCE_URL,
        "official_reference_url": OFFICIAL_SUPPORT_REFERENCE,
        "section": "4.2 List of faults and alarms",
        "page_range": {"start": start_page, "end": end_page},
        "record_count": len(records),
        "unique_fault_code_count": len({row["weak_record"]["fault_code"] for row in records}),
        "record_type_counts": {
            "fault": counts["F"],
            "alarm": counts["A"],
            "internal_message": counts["N"],
        },
        "extracted_section_sha256": sha256_bytes(extracted_text.encode("utf-8")),
        "corpus_jsonl_sha256": sha256_bytes(corpus_bytes),
        "extraction": {
            "tool": "pypdf",
            "page_separator": PAGE_SEPARATOR,
            "sample_identity": "fault code + first PDF page + occurrence ordinal for repeated codes",
            "source_offsets": "Python Unicode character offsets within the assembled extracted section text",
        },
        "holdout_policy": (
            "The entire S120/S150 List Manual document is an external source holdout. "
            "Do not use these records to fit thresholds, select a model, or tune prompts. "
            "This is a different manual/version, not a cross-industry test."
        ),
        "license_note": (
            "The manual is publicly accessible but is not marked as an open-data license here. "
            "Keep the PDF and derived corpus local; preserve source provenance and verify Siemens reuse terms before redistribution."
        ),
        "limitations": [
            "weak_record and cause_sections are parser outputs, not expert labels",
            "a cause list, multiple bullets, or the mere presence of 'and'/'or' does not establish an FTA gate",
            "gate labels and direct evidence require separate review; absent direct gate evidence remains unknown",
            "this single manual is one independent source cluster, regardless of record count",
        ],
        "retrieved_date": retrieved_date or date.today().isoformat(),
    }
    return manifest, records


def _write_new(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--start-page", type=int, default=DEFAULT_START_PAGE)
    parser.add_argument("--end-page", type=int, default=DEFAULT_END_PAGE)
    parser.add_argument("--retrieved-date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    if args.output_jsonl.resolve() == args.manifest_output.resolve():
        raise ValueError("corpus and manifest must use different paths")
    if args.output_jsonl.exists() or args.manifest_output.exists():
        raise FileExistsError("refusing to overwrite an existing corpus or manifest")

    manifest, records = build_corpus(
        args.pdf,
        start_page=args.start_page,
        end_page=args.end_page,
        retrieved_date=args.retrieved_date,
    )
    corpus_text = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in records
    )
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    corpus_written = False
    try:
        _write_new(args.output_jsonl, corpus_text)
        corpus_written = True
        _write_new(args.manifest_output, manifest_text)
    except Exception:
        if corpus_written:
            args.output_jsonl.unlink(missing_ok=True)
        raise
    print(
        json.dumps(
            {
                "corpus": str(args.output_jsonl),
                "manifest": str(args.manifest_output),
                "record_count": manifest["record_count"],
                "unique_fault_code_count": manifest["unique_fault_code_count"],
                "source_pdf_sha256": manifest["source_pdf_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
