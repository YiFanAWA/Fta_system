#!/usr/bin/env python3
"""Extract a provenance-preserving, unlabeled Siemens S210 fault corpus from a PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pdfplumber


CODE_RE = re.compile(r"(?m)^(?P<code>[AFN]\d{5})\s+(?P<title>.+?)\s*$")
PARAM_RE = re.compile(r"\b[pr]\d{4,5}(?:\[[^\]]+\])?\b", re.IGNORECASE)
DROP_LINE_RE = re.compile(
    r"^(?:Faults and alarms|15\.2 List of faults and alarms|"
    r"Product: SINAMICS S210, Version: .*|Objects: S210|"
    r"SINAMICS S210 servo drive system|Operating Instructions, .*)$"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_block(raw: str) -> str:
    kept: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or DROP_LINE_RE.match(line):
            continue
        kept.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def _first_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(label)}:\s*(.+)$", text)
    return match.group(1).strip() if match else None


def _section(text: str, label: str) -> str | None:
    match = re.search(rf"(?ms)^{re.escape(label)}:\s*(.*?)(?=^[A-Z][^:\n]{{0,60}}:\s*|\Z)", text)
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip()
    return value or None


def _page_for_offset(offset: int, page_offsets: list[int]) -> int:
    page = 1
    for index, start in enumerate(page_offsets, start=1):
        if start > offset:
            break
        page = index
    return page


def extract_records(pdf_path: Path, *, start_page: int, end_page: int) -> list[dict[str, Any]]:
    page_texts: list[str] = []
    page_offsets: list[int] = []
    cursor = 0
    with pdfplumber.open(pdf_path) as pdf:
        if start_page < 1 or end_page > len(pdf.pages) or start_page > end_page:
            raise ValueError(f"invalid page range {start_page}-{end_page} for {len(pdf.pages)} pages")
        for page_number in range(1, end_page + 1):
            if page_number < start_page:
                continue
            text = pdf.pages[page_number - 1].extract_text() or ""
            page_offsets.append(cursor)
            page_texts.append(text)
            cursor += len(text) + 1

    full_text = "\n".join(page_texts)
    matches = list(CODE_RE.finditer(full_text))
    records: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        raw = full_text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else None]
        text = _clean_block(raw)
        code = match.group("code")
        title = match.group("title").strip()
        params = []
        for value in PARAM_RE.findall(text):
            normalized = value.lower()
            if normalized not in params:
                params.append(normalized)
        start = match.start()
        end = match.start() + len(raw)
        records.append(
            {
                "sample_id": f"SIEMENS_S210_2019_{code}",
                "split": "unlabeled",
                "source_type": "public_manual_fault_corpus",
                "input_text": text,
                "weak_record": {
                    "fault_code": code,
                    "description": title,
                    "component": _first_labeled_value(text, "Component"),
                    "related_components": [],
                    "causes_text": _section(text, "Cause"),
                    "parameters": params,
                    "gate_type": None,
                },
                "annotation": {
                    "human_expert_reviewed": False,
                    "engineering_verified": False,
                    "label_status": "unlabeled_public_corpus",
                    "logic_status": "unknown",
                    "use_policy": "candidate_evaluation_or_expert_review_only",
                },
                "provenance": {
                    "source_document": "SINAMICS S210 servo drive system with SIMOTICS S-1FK2 and S-1FT2",
                    "source_pdf": "S210_Manual_2019.pdf",
                    "source_url": "https://publikacje.siemens-info.com/pdf/681/S210%20Manual.pdf",
                    "official_reference_url": "https://support.industry.siemens.com/cs/attachments/109827474/S210_S-1FK2_S-1FT2_op_instr_0424_en-US.pdf",
                    "section": "15.2 List of faults and alarms",
                    "pdf_page_start": _page_for_offset(start, page_offsets) + start_page - 1,
                    "pdf_page_end": _page_for_offset(end, page_offsets) + start_page - 1,
                    "source_offset_start": start,
                    "source_offset_end": end,
                },
            }
        )
    return records


def build_corpus(
    pdf_path: Path,
    *,
    start_page: int = 423,
    end_page: int = 539,
    retrieved_date: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = extract_records(pdf_path, start_page=start_page, end_page=end_page)
    if not records:
        raise ValueError("no fault/alarm records were extracted")
    source_hash = _sha256(pdf_path)
    for record in records:
        record["provenance"]["source_sha256"] = source_hash
        record["provenance"]["retrieved_date"] = retrieved_date or date.today().isoformat()
    manifest = {
        "dataset": "siemens_s210_public_fault_corpus",
        "version": "0.1.0",
        "label_status": "unlabeled_public_corpus",
        "human_expert_reviewed": False,
        "records": len(records),
        "fault_records": sum(record["sample_id"].split("_")[-1].startswith("F") for record in records),
        "alarm_records": sum(record["sample_id"].split("_")[-1].startswith("A") for record in records),
        "internal_records": sum(record["sample_id"].split("_")[-1].startswith("N") for record in records),
        "source_sha256": source_hash,
        "source_pdf": "S210_Manual_2019.pdf",
        "source_url": "https://publikacje.siemens-info.com/pdf/681/S210%20Manual.pdf",
        "official_reference_url": "https://support.industry.siemens.com/cs/attachments/109827474/S210_S-1FK2_S-1FT2_op_instr_0424_en-US.pdf",
        "section": "15.2 List of faults and alarms",
        "page_range": {"start": start_page, "end": end_page},
        "license_note": (
            "The manual is publicly accessible but not marked as an open-data license in this corpus. "
            "Keep the PDF local, preserve provenance, and verify Siemens reuse terms before redistribution."
        ),
        "limitations": [
            "weak_record is a parser aid, not an expert gold annotation",
            "Cause text may contain parameter-value explanations and remedy context",
            "AND/OR logic is not annotated",
            "product/version differences require separate expert review",
        ],
    }
    return manifest, records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--start-page", type=int, default=423)
    parser.add_argument("--end-page", type=int, default=539)
    parser.add_argument("--retrieved-date", default=None)
    args = parser.parse_args()

    manifest, records = build_corpus(
        args.pdf,
        start_page=args.start_page,
        end_page=args.end_page,
        retrieved_date=args.retrieved_date,
    )
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    args.output_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output_jsonl} records={len(records)}")


if __name__ == "__main__":
    main()
