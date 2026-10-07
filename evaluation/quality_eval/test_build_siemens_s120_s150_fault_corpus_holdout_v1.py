from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.public_sources.build_siemens_s120_s150_fault_corpus_holdout_v1 import (
    extract_records_from_pages,
)


class TestSiemensS120S150HoldoutCorpusExtraction(unittest.TestCase):
    def test_extracts_repeated_fault_codes_without_colliding_sample_ids(self) -> None:
        pages = [
            (
                "4.2 List of faults and alarms\n"
                "F01000 First internal fault\n"
                "Cause: First exact cause.\n"
                "Remedy: do not treat as cause\n"
                "F01000 Repeated internal fault\n"
                "Cause: Second exact cause.\n"
                "Remedy: do not treat as cause\n"
            ),
            "4.2 List of faults and alarms\nA01001 Alarm text\nCause: A separate cause.\nRemedy: action\n",
        ]
        pdf_digest = "a" * 64

        full_text, records = extract_records_from_pages(
            pages,
            start_page=100,
            source_pdf_sha256=pdf_digest,
            retrieved_date="2026-09-27",
        )

        self.assertEqual(len(records), 3)
        self.assertNotEqual(records[0]["sample_id"], records[1]["sample_id"])
        self.assertEqual(records[0]["weak_record"]["fault_code"], "F01000")
        self.assertEqual(records[1]["weak_record"]["fault_code"], "F01000")
        self.assertEqual(records[2]["weak_record"]["fault_code"], "A01001")
        self.assertEqual(records[0]["provenance"]["pdf_page_start"], 100)
        self.assertEqual(records[2]["provenance"]["pdf_page_start"], 101)
        self.assertEqual(
            records[0]["provenance"]["source_cluster_id"], f"external_source:{pdf_digest}"
        )
        self.assertEqual(records[0]["split"], "external_source_holdout")
        self.assertEqual(records[0]["annotation"]["logic_status"], "unknown")

        first_cause = records[0]["weak_record"]["cause_sections"][0]
        self.assertEqual(
            records[0]["input_text"][first_cause["start"] : first_cause["end"]],
            first_cause["quote"],
        )
        self.assertEqual(first_cause["quote"], "First exact cause.")
        self.assertNotIn("do not treat as cause", first_cause["quote"])
        self.assertTrue(hashlib.sha256(full_text.encode("utf-8")).hexdigest())

    def test_fault_value_subsection_inside_cause_is_not_cut_off(self) -> None:
        pages = [
            "F02001 Fault with diagnostic value\n"
            "Cause: Fault value (r0949, interpret bitwise):\n"
            "Bit 1: Feedback signal missing.\n"
            "Remedy: check the signal\n"
        ]

        _, records = extract_records_from_pages(
            pages,
            start_page=1,
            source_pdf_sha256="c" * 64,
            retrieved_date="2026-09-27",
        )

        cause = records[0]["weak_record"]["cause_sections"][0]
        self.assertIn("Fault value (r0949, interpret bitwise)", cause["quote"])
        self.assertIn("Bit 1: Feedback signal missing.", cause["quote"])
        self.assertNotIn("Remedy:", cause["quote"])

    def test_cause_quotes_are_exact_and_page_separator_is_preserved(self) -> None:
        pages = ["F02000 First\nCause: first page text", "continued cause text\nRemedy: action"]

        _, records = extract_records_from_pages(
            pages,
            start_page=1,
            source_pdf_sha256="b" * 64,
            retrieved_date="2026-09-27",
        )

        cause = records[0]["weak_record"]["cause_sections"][0]
        self.assertIn("\f", records[0]["input_text"])
        self.assertEqual(
            records[0]["input_text"][cause["start"] : cause["end"]],
            cause["quote"],
        )
        self.assertEqual(cause["quote"], "first page text\n\f\ncontinued cause text")
