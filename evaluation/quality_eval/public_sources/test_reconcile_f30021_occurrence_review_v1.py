from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from evaluation.quality_eval.public_sources.reconcile_f30021_occurrence_review_v1 import (
    CAUSE_INDEX,
    CORPUS_PATH,
    LOCATOR_REVIEW_PATH,
    RAW_RUN_PATH,
    ReconciliationError,
    SAMPLE_ID,
    build_reconciliation,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[3]


def load_inputs() -> tuple[dict, dict, dict]:
    source = next(
        json.loads(line)
        for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("sample_id") == SAMPLE_ID
    )
    raw_run = json.loads(RAW_RUN_PATH.read_text(encoding="utf-8"))
    locator_review = json.loads(LOCATOR_REVIEW_PATH.read_text(encoding="utf-8"))
    return source, raw_run, locator_review


class TestF30021OccurrenceReviewReconciliation(unittest.TestCase):
    def setUp(self) -> None:
        self.source, self.raw_run, self.locator_review = load_inputs()

    def test_saved_locator_matches_unique_scoped_occurrence_but_is_not_applied(self) -> None:
        report = build_reconciliation(self.source, self.raw_run, self.locator_review)
        self.assertTrue(report["reconciliation_result"]["scope_and_offsets_consistent"])
        self.assertTrue(report["reconciliation_result"]["prior_locator_selection_valid_within_reviewed_scope"])
        self.assertFalse(report["reconciliation_result"]["prior_locator_decision_applied_to_latest_run"])
        self.assertEqual("unresolved", report["latest_raw_run"]["current_disposition"])
        self.assertEqual("blocked", report["latest_raw_run"]["tree_status"])
        self.assertEqual("unknown", report["latest_raw_run"]["gate"])
        self.assertEqual(0, report["reconciliation_result"]["semantic_defects_closed"])

    def test_report_distinguishes_ai_review_from_human_gold(self) -> None:
        report = build_reconciliation(self.source, self.raw_run, self.locator_review)
        self.assertFalse(report["locator_review"]["reviewer_is_human_expert"])
        self.assertFalse(report["locator_review"]["formal_gold"])
        self.assertIn("ai_locator_review", report["reviewer_provenance"])
        self.assertIn("不推 OR/AND", render_markdown(report))

    def test_changed_source_hash_is_rejected(self) -> None:
        review = copy.deepcopy(self.locator_review)
        review["source"]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReconciliationError, "locator review source hash"):
            build_reconciliation(self.source, self.raw_run, review)

    def test_changed_occurrence_offset_is_rejected(self) -> None:
        review = copy.deepcopy(self.locator_review)
        review["selected_evidence"]["start"] += 1
        with self.assertRaisesRegex(ReconciliationError, "saved locator selection"):
            build_reconciliation(self.source, self.raw_run, review)

    def test_review_cannot_be_promoted_to_human_or_gold(self) -> None:
        review = copy.deepcopy(self.locator_review)
        review["reviewer_is_human_expert"] = True
        with self.assertRaisesRegex(ReconciliationError, "explicitly non-human"):
            build_reconciliation(self.source, self.raw_run, review)
        review = copy.deepcopy(self.locator_review)
        review["formal_gold"] = True
        with self.assertRaisesRegex(ReconciliationError, "formal Gold"):
            build_reconciliation(self.source, self.raw_run, review)

    def test_current_run_must_keep_unresolved_evidence_empty_and_tree_blocked(self) -> None:
        run = copy.deepcopy(self.raw_run)
        tree = run["result"]["outcomes"][0]["tree"]
        item = next(x for x in tree["cause_dispositions"] if x["source_cause_index"] == CAUSE_INDEX)
        item["evidence"] = [{"start": 332, "end": 372, "quote": "- short-circuit at the braking resistor."}]
        with self.assertRaisesRegex(ReconciliationError, "unresolved without confirmed evidence"):
            build_reconciliation(self.source, run, self.locator_review)

    def test_child_set_or_gate_cannot_be_silently_promoted(self) -> None:
        run = copy.deepcopy(self.raw_run)
        tree = run["result"]["outcomes"][0]["tree"]
        tree["gate_assessments"][0]["gate"] = "OR"
        with self.assertRaisesRegex(ReconciliationError, "unknown gate"):
            build_reconciliation(self.source, run, self.locator_review)


if __name__ == "__main__":
    unittest.main()
