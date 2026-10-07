from __future__ import annotations

import unittest

from evaluation.quality_eval.compare_fta_event_scope_semantic_smoke_run_v2 import (
    ALLOWED_UNKNOWN_REASONS,
    _gate_logic_check,
    compare_saved_run_v2,
)


class TestFtaSemanticSmokeOfflineComparisonV2(unittest.TestCase):
    def test_known_gate_requires_exact_logic_quote_against_authored_expectation(self) -> None:
        result = compare_saved_run_v2("SMOKE-002")
        comparison = result["comparison"]
        self.assertEqual("matched_authored_policy_expectation_not_expert_validation", result["status"])
        self.assertEqual("AND", comparison["expected_gate"])
        self.assertTrue(comparison["known_gate_logic_evidence_matches_decisive_quote"])
        self.assertIsNone(comparison["unknown_gate_contract_valid"])
        self.assertTrue(comparison["qualitative_smoke_match"])
        self.assertFalse(result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"])

    def test_unknown_gate_uses_null_evidence_and_allowed_reason_not_quote_binding(self) -> None:
        result = compare_saved_run_v2("SMOKE-003")
        comparison = result["comparison"]
        self.assertEqual("matched_authored_policy_expectation_not_expert_validation", result["status"])
        self.assertEqual("unknown", comparison["expected_gate"])
        self.assertTrue(comparison["gate_matches_policy_expectation"])
        self.assertIsNone(comparison["known_gate_logic_evidence_matches_decisive_quote"])
        self.assertTrue(comparison["unknown_gate_contract_valid"])
        self.assertEqual("no_direct_logic_evidence", comparison["unknown_reason"])
        self.assertTrue(comparison["decisive_source_quote_present_in_input"])
        self.assertTrue(comparison["qualitative_smoke_match"])
        self.assertFalse(result["claim_boundaries"]["human_expert_gold"])
        self.assertFalse(result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"])

    def test_unknown_gate_with_logic_quote_or_missing_reason_is_invalid(self) -> None:
        invalid_quote = _gate_logic_check("unknown", {
            "gate": "unknown",
            "logic_evidence": {"quote": "some text"},
            "unknown_reason": "no_direct_logic_evidence",
        })
        missing_reason = _gate_logic_check("unknown", {
            "gate": "unknown",
            "logic_evidence": None,
            "unknown_reason": None,
        })
        self.assertFalse(invalid_quote["unknown_gate_contract_valid"])
        self.assertFalse(missing_reason["unknown_gate_contract_valid"])
        self.assertEqual({
            "no_direct_logic_evidence", "incomplete_child_set", "scope_ambiguity", "input_context_unavailable"
        }, ALLOWED_UNKNOWN_REASONS)

    def test_saved_smoke_004_cooccurrence_stays_unknown(self) -> None:
        result = compare_saved_run_v2("SMOKE-004")
        comparison = result["comparison"]
        self.assertEqual("matched_authored_policy_expectation_not_expert_validation", result["status"])
        self.assertEqual("unknown", comparison["observed_gate"])
        self.assertTrue(comparison["unknown_gate_contract_valid"])
        self.assertEqual("no_direct_logic_evidence", comparison["unknown_reason"])
        self.assertEqual(4, comparison["evidence_locations_checked"])
        self.assertEqual(4, comparison["evidence_locations_valid"])

    def test_saved_smoke_005_matches_unknown_gate_but_is_blocked_by_single_child_scope(self) -> None:
        result = compare_saved_run_v2("SMOKE-005")
        comparison = result["comparison"]
        self.assertEqual("requires_review", result["status"])
        self.assertEqual("unknown", comparison["expected_gate"])
        self.assertEqual("unknown", comparison["observed_gate"])
        self.assertTrue(comparison["gate_matches_policy_expectation"])
        self.assertTrue(comparison["unknown_gate_contract_valid"])
        self.assertFalse(comparison["structure_contract_valid"])
        self.assertEqual(3, comparison["evidence_locations_checked"])
        self.assertEqual(3, comparison["evidence_locations_valid"])
        self.assertFalse(comparison["qualitative_smoke_match"])
        self.assertFalse(result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"])

    def test_smoke_001_remains_valid_under_v2_policy(self) -> None:
        result = compare_saved_run_v2("SMOKE-001")
        self.assertEqual("OR", result["comparison"]["observed_gate"])
        self.assertTrue(result["comparison"]["known_gate_logic_evidence_matches_decisive_quote"])
        self.assertTrue(result["comparison"]["qualitative_smoke_match"])


if __name__ == "__main__":
    unittest.main()
