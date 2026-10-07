#!/usr/bin/env python3
"""Build a blind, unlabeled gate-review pilot from unseen-code S120/S150 records."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from evaluation.quality_eval.public_sources.audit_siemens_s120_s150_holdout_overlap_v1 import (
    read_jsonl,
)


DEFAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS = DEFAULT_ROOT / "evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.jsonl"
DEFAULT_OVERLAP_AUDIT = DEFAULT_ROOT / "evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v3_2026-09-27.json"
PILOT_SAMPLE_IDS = (
    "SIEMENS_S120_S150_2023_F35400_P3271_N001",
    "SIEMENS_S120_S150_2023_F06000_P2792_N001",
    "SIEMENS_S120_S150_2023_A30079_P3008_N001",
    "SIEMENS_S120_S150_2023_F08702_P2967_N001",
)
REQUIRED_STRATUM = "unseen_fault_code_no_exact_full_cause_text_overlap"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_bundle(
    corpus_rows: Sequence[dict[str, Any]],
    overlap_audit: dict[str, Any],
    *,
    corpus_path: Path,
    overlap_audit_path: Path,
    bundle_date: str | None = None,
) -> dict[str, Any]:
    rows_by_id = {row.get("sample_id"): row for row in corpus_rows}
    if len(rows_by_id) != len(corpus_rows):
        raise ValueError("corpus sample_id values must be unique")
    audit_by_id = {
        row.get("sample_id"): row for row in overlap_audit.get("s120_records", [])
    }
    if len(audit_by_id) != len(overlap_audit.get("s120_records", [])):
        raise ValueError("overlap audit sample_id values must be unique")

    corpus_hash = sha256_file(corpus_path)
    expected_hash = overlap_audit.get("sources", {}).get("s120_s150_holdout_v2", {}).get("sha256")
    if corpus_hash != expected_hash:
        raise ValueError("overlap audit does not refer to the current S120/S150 corpus bytes")

    cases: list[dict[str, Any]] = []
    for ordinal, sample_id in enumerate(PILOT_SAMPLE_IDS, start=1):
        source_row = rows_by_id.get(sample_id)
        audit_row = audit_by_id.get(sample_id)
        if source_row is None or audit_row is None:
            raise ValueError(f"pilot sample is missing from corpus or overlap audit: {sample_id}")
        if audit_row.get("overlap_stratum") != REQUIRED_STRATUM:
            raise ValueError(f"pilot sample is not in the strict unseen-code stratum: {sample_id}")
        if audit_row.get("same_fault_code_in_s210") or audit_row.get("exact_cause_text_match_any_s210_code"):
            raise ValueError(f"pilot sample has a detected code/text overlap: {sample_id}")
        if audit_row.get("partial_cause_text_containment_match_any_s210_code_min_chars"):
            raise ValueError(f"pilot sample has a screened partial cause-text overlap: {sample_id}")

        weak = source_row.get("weak_record", {})
        provenance = source_row.get("provenance", {})
        cases.append(
            {
                "candidate_id": f"S120-PILOT-{ordinal:03d}",
                "review_status": "pending",
                "sample_id": sample_id,
                "fault_code": weak.get("fault_code"),
                "description": weak.get("description"),
                "input_text": source_row.get("input_text"),
                "parser_cause_sections": weak.get("cause_sections", []),
                "provenance": {
                    "source_document": provenance.get("source_document"),
                    "edition": provenance.get("edition"),
                    "source_cluster_id": provenance.get("source_cluster_id"),
                    "source_pdf_sha256": provenance.get("source_pdf_sha256"),
                    "pdf_page_start": provenance.get("pdf_page_start"),
                    "pdf_page_end": provenance.get("pdf_page_end"),
                    "source_offset_start": provenance.get("source_offset_start"),
                    "source_offset_end": provenance.get("source_offset_end"),
                    "record_text_sha256": provenance.get("record_text_sha256"),
                },
                "overlap_audit_stratum": audit_row["overlap_stratum"],
                "review_template": {
                    "scope_type": None,
                    "scope_anchor": None,
                    "children": [],
                    "child_set_complete": None,
                    "gate_label": None,
                    "gate_evidence": [],
                    "review_reason": "",
                },
            }
        )

    return {
        "artifact_type": "unlabeled_fta_gate_review_candidate_bundle",
        "artifact_version": "1.0.0",
        "created_date": bundle_date or date.today().isoformat(),
        "status": "candidate_bundle_pending_ai_role_review",
        "reviewer_provenance": None,
        "reviewer_is_human_expert": False,
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "candidate_selection_policy": (
            "A four-record pilot was selected from the S120/S150 overlap audit's unseen-fault-code, "
            "no exact/partial full causes_text overlap stratum. Selection is for scope review only and does not "
            "imply that any case has an AND/OR gate."
        ),
        "review_policy": [
            "Review the exact local scope and the complete same-level child set before assigning a gate.",
            "AND/OR requires direct evidence within that scope; a list, parameter code, fault-value key, or ordinary conjunction is not enough.",
            "Distinguish cause conditions from diagnostic modes, signal logic, effects, and remedies.",
            "If evidence, scope, child identity, or completeness is uncertain, use unknown or not_applicable and explain why.",
            "AI-role review is not a human expert signature, calibrated probability, or formal Gold label.",
        ],
        "summary": {
            "candidate_count": len(cases),
            "unique_fault_code_count": len({case["fault_code"] for case in cases}),
            "source_cluster_count": len(
                {case["provenance"]["source_cluster_id"] for case in cases}
            ),
            "reviewed_count": 0,
            "pending_count": len(cases),
        },
        "input_artifacts": {
            "s120_s150_corpus_path": str(corpus_path),
            "s120_s150_corpus_sha256": corpus_hash,
            "overlap_audit_path": str(overlap_audit_path),
            "overlap_audit_sha256": sha256_file(overlap_audit_path),
        },
        "cases": cases,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--overlap-audit", type=Path, default=DEFAULT_OVERLAP_AUDIT)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output_json.exists():
        raise FileExistsError("refusing to overwrite an existing review candidate bundle")
    with args.overlap_audit.open("r", encoding="utf-8") as stream:
        overlap = json.load(stream)
    bundle = build_bundle(
        read_jsonl(args.corpus),
        overlap,
        corpus_path=args.corpus,
        overlap_audit_path=args.overlap_audit,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(bundle, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(bundle["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
