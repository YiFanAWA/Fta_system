from __future__ import annotations

import unittest

from evaluation.quality_eval.compare_fta_event_scope_model_run_v4_dev import build_report


class TestFigure7V4QualitativeComparison(unittest.TestCase):
    def test_v4_run_is_blocked_without_making_accuracy_claims(self) -> None:
        report = build_report()
        self.assertEqual("not_accepted_for_fta_preview", report["summary"]["semantic_tree_status"])
        self.assertEqual("blocked", report["summary"]["structure_contract_status"])
        self.assertEqual(1, report["summary"]["structure_blocker_count"])
        self.assertEqual("9/9", report["summary"]["literal_evidence_location"])
        self.assertTrue(report["summary"]["all_predicted_gate_labels_unknown"])
        self.assertIsNone(report["summary"]["quantitative_score"])
        self.assertFalse(report["summary"]["accuracy_or_calibration_claim_allowed"])

    def test_comparison_keeps_ai_text_review_and_diagram_labels_separate(self) -> None:
        report = build_report()
        self.assertEqual("ai_role_review", report["reference_provenance"]["reviewer_role"])
        self.assertFalse(report["reference_provenance"]["formal_human_expert_gold"])
        self.assertFalse(report["reference_provenance"]["diagram_gate_labels_used_as_text_gold"])
        root = next(item for item in report["findings"] if item["finding_id"] == "root_gate_vs_ai_text_review")
        self.assertEqual("unknown", root["model"]["gate"])
        self.assertEqual("OR", root["reference"]["text_authorized_gate"])


if __name__ == "__main__":
    unittest.main()
