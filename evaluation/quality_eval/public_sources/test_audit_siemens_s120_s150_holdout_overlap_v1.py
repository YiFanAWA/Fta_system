from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluation.quality_eval.public_sources.audit_siemens_s120_s150_holdout_overlap_v1 import (
    build_overlap_audit,
    normalize_text,
)


def corpus_row(sample_id: str, code: str, cause: str, text: str = "") -> dict:
    return {
        "sample_id": sample_id,
        "input_text": text,
        "weak_record": {"fault_code": code, "causes_text": cause},
        "provenance": {"pdf_page_start": 1},
    }


class TestS120S150OverlapAudit(unittest.TestCase):
    def test_normalization_preserves_punctuation_and_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_text("  A\nB  "), "a b")
        self.assertNotEqual(normalize_text("A-B"), normalize_text("A B"))

    def test_stratifies_exact_partial_code_only_and_unseen_cases(self) -> None:
        s210 = [
            corpus_row("old-exact", "F01000", "An internal software error has occurred."),
            corpus_row("old-partial", "F02000", "The motor temperature exceeded the allowed threshold."),
            corpus_row("old-other", "F03000", "A communication error occurred."),
        ]
        s120 = [
            corpus_row("new-exact", "F01000", "An internal software error has occurred."),
            corpus_row(
                "new-partial",
                "F02000",
                "The motor temperature exceeded the allowed threshold. Additional context follows.",
            ),
            corpus_row("new-code-only", "F03000", "A different cause is documented."),
            corpus_row("new-unseen", "F04000", "A source-new cause without an old code."),
        ]
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for name in ("s120.jsonl", "s210.jsonl", "review.json"):
                (base / name).write_text("fixture", encoding="utf-8")
            report = build_overlap_audit(
                s120,
                s210,
                {"gate_nodes": []},
                s120_path=base / "s120.jsonl",
                s210_path=base / "s210.jsonl",
                gate_review_path=base / "review.json",
                audit_date="2026-09-27",
            )

        strata = {row["sample_id"]: row["overlap_stratum"] for row in report["s120_records"]}
        self.assertEqual(strata["new-exact"], "same_code_exact_cause_text")
        self.assertEqual(strata["new-partial"], "same_code_partial_cause_text")
        self.assertEqual(strata["new-code-only"], "same_fault_code_other_cause_text")
        self.assertEqual(
            strata["new-unseen"], "unseen_fault_code_no_exact_full_cause_text_overlap"
        )
        rows_by_id = {row["sample_id"]: row for row in report["s120_records"]}
        self.assertFalse(rows_by_id["new-unseen"]["partial_cause_text_containment_match_any_s210_code_min_chars"])

    def test_scope_anchor_reuse_requires_same_fault_code(self) -> None:
        s120 = [corpus_row("new-a", "F01000", "cause", "The direct OR anchor is here.")]
        s210 = [corpus_row("old-a", "F01000", "cause")]
        gate_review = {
            "reviewer_is_human_expert": False,
            "gate_nodes": [
                {
                    "gate_node_id": "gate-1",
                    "fault_code": "F01000",
                    "review_status": "reviewed",
                    "scope_anchor": {"quote": "The direct OR anchor is here."},
                },
                {
                    "gate_node_id": "gate-2",
                    "fault_code": "F02000",
                    "review_status": "reviewed",
                    "scope_anchor": {"quote": "The direct OR anchor is here."},
                },
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for name in ("s120.jsonl", "s210.jsonl", "review.json"):
                (base / name).write_text("fixture", encoding="utf-8")
            report = build_overlap_audit(
                s120,
                s210,
                gate_review,
                s120_path=base / "s120.jsonl",
                s210_path=base / "s210.jsonl",
                gate_review_path=base / "review.json",
                audit_date="2026-09-27",
            )
        matched = [
            row["gate_node_id"]
            for row in report["s210_reviewed_gate_node_overlap"]
            if row["scope_anchor_exact_text_reused_in_s120"]
        ]
        self.assertEqual(matched, ["gate-1"])

    def test_gate_review_source_metadata_uses_the_supplied_review_set(self) -> None:
        s120 = [corpus_row("new-a", "F01000", "cause", "The direct OR anchor is here.")]
        s210 = [corpus_row("old-a", "F01000", "cause")]
        gate_review = {
            "artifact_version": "v6",
            "reviewer_is_human_expert": False,
            "reviewer_provenance": "user_authorized_ai_role_review",
            "gate_nodes": [
                {
                    "gate_node_id": "gate-1",
                    "fault_code": "F01000",
                    "review_status": "reviewed",
                    "reviewer_provenance": "user_authorized_ai_role_review",
                    "scope_anchor": {"quote": "The direct OR anchor is here."},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for name in ("s120.jsonl", "s210.jsonl", "review-v6.json"):
                (base / name).write_text("fixture", encoding="utf-8")
            report = build_overlap_audit(
                s120,
                s210,
                gate_review,
                s120_path=base / "s120.jsonl",
                s210_path=base / "s210.jsonl",
                gate_review_path=base / "review-v6.json",
                audit_date="2026-09-28",
            )

        review_source = report["sources"]["s210_gate_node_review"]
        self.assertEqual(review_source["artifact_version"], "v6")
        self.assertEqual(review_source["artifact_name"], "review-v6.json")
        self.assertEqual(review_source["reviewer_provenance"], "user_authorized_ai_role_review")
        self.assertEqual(review_source["reviewer_provenance_counts"], {"user_authorized_ai_role_review": 1})
        self.assertFalse(review_source["reviewer_is_human_expert"])
        self.assertNotIn("s210_gate_node_review_v5", report["sources"])

    def test_partial_cause_overlap_is_detected_across_different_fault_codes(self) -> None:
        old_cause = "The motor temperature exceeded the allowed threshold."
        new_cause = old_cause + " Additional newly worded detail follows."
        s210 = [corpus_row("old-a", "F01000", old_cause)]
        s120 = [corpus_row("new-a", "F99000", new_cause)]
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for name in ("s120.jsonl", "s210.jsonl", "review.json"):
                (base / name).write_text("fixture", encoding="utf-8")
            report = build_overlap_audit(
                s120,
                s210,
                {"gate_nodes": []},
                s120_path=base / "s120.jsonl",
                s210_path=base / "s210.jsonl",
                gate_review_path=base / "review.json",
                audit_date="2026-09-27",
            )
        self.assertTrue(
            report["s120_records"][0][
                "partial_cause_text_containment_match_any_s210_code_min_chars"
            ]
        )


if __name__ == "__main__":
    unittest.main()
