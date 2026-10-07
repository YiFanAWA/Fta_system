from __future__ import annotations

import unittest

from evaluation.quality_eval.compare_fta_event_scope_model_run_v3_dev import build_report


class TestFigure7V3QualitativeComparison(unittest.TestCase):
    def test_comparison_is_qualitative_and_does_not_promote_readiness(self) -> None:
        report = build_report()
        self.assertEqual("seen_development_only", report["case"]["exposure_status"])
        self.assertEqual("not_accepted_for_fta_preview", report["summary"]["semantic_tree_status"])
        self.assertIsNone(report["summary"]["quantitative_score"])
        self.assertFalse(report["summary"]["accuracy_or_generalization_claim_allowed"])
        self.assertFalse(report["summary"]["fta_ready"])
        self.assertFalse(report["summary"]["production_ready"])
        self.assertEqual("blocked", report["summary"]["tree_hierarchy_contract"]["status"])
        self.assertFalse(report["summary"]["tree_hierarchy_contract"]["output_mutated"])

    def test_comparison_uses_text_authorized_labels_not_diagram_gate_as_gold(self) -> None:
        report = build_report()
        self.assertFalse(report["reference_provenance"]["diagram_gate_labels_used_as_text_gold"])
        by_id = {item["finding_id"]: item for item in report["findings"]}
        self.assertEqual("not_aligned", by_id["secondary_explosion_scope"]["status"])
        self.assertEqual("scope_mismatch_unresolved", by_id["structural_branch_scope"]["status"])
        self.assertEqual("not_aligned", by_id["top_level_branch_topology"]["status"])

    def test_quotes_are_counted_as_literal_matching_only(self) -> None:
        report = build_report()
        by_id = {item["finding_id"]: item for item in report["findings"]}
        quote_result = by_id["source_quote_matching"]
        self.assertEqual("passed_literal_matching_only", quote_result["status"])
        self.assertEqual(8, quote_result["prediction"]["literal_matches"])

    def test_hierarchy_contract_blocks_conflict_and_keeps_original_prediction(self) -> None:
        report = build_report()
        finding = next(item for item in report["findings"] if item["finding_id"] == "tree_hierarchy_contract")
        self.assertEqual("blocked", finding["status"])
        self.assertFalse(finding["prediction"]["valid"])
        self.assertFalse(finding["prediction"]["output_mutated"])
        blocker_codes = {item["code"] for item in finding["prediction"]["blockers"]}
        self.assertIn("parent_id_conflicts_with_gate_scope", blocker_codes)
        self.assertIn("node_has_multiple_parent_scopes", blocker_codes)


if __name__ == "__main__":
    unittest.main()
