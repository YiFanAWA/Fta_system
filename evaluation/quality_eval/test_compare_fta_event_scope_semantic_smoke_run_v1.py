from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from evaluation.quality_eval.compare_fta_event_scope_semantic_smoke_run_v1 import (
    ComparisonError,
    compare_saved_run,
)


ROOT = Path(__file__).resolve().parents[2]
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29.json"
ASSESSMENT_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29_assessment.json"
RUN_002_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29.json"
ASSESSMENT_002_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29_assessment.json"
REFERENCE_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json"


class TestFtaSemanticSmokeOfflineComparisonV1(unittest.TestCase):
    def test_saved_smoke_001_matches_only_the_non_gold_policy_expectation(self) -> None:
        result = compare_saved_run("SMOKE-001")
        self.assertEqual("matched_authored_policy_expectation_not_expert_validation", result["status"])
        self.assertTrue(result["comparison"]["gate_matches_policy_expectation"])
        self.assertEqual("OR", result["comparison"]["observed_gate"])
        self.assertTrue(result["comparison"]["logic_evidence_exactly_matches_decisive_quote"])
        self.assertTrue(result["comparison"]["structure_contract_valid"])
        self.assertEqual(5, result["comparison"]["evidence_locations_checked"])
        self.assertEqual(5, result["comparison"]["evidence_locations_valid"])
        self.assertFalse(result["claim_boundaries"]["human_expert_gold"])
        self.assertFalse(result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(result["claim_boundaries"]["fta_ready"])

    def test_saved_smoke_002_matches_only_the_non_gold_policy_expectation(self) -> None:
        result = compare_saved_run("SMOKE-002", run_path=RUN_002_PATH, assessment_path=ASSESSMENT_002_PATH)
        self.assertEqual("matched_authored_policy_expectation_not_expert_validation", result["status"])
        self.assertTrue(result["comparison"]["gate_matches_policy_expectation"])
        self.assertEqual("AND", result["comparison"]["observed_gate"])
        self.assertTrue(result["comparison"]["logic_evidence_exactly_matches_decisive_quote"])
        self.assertTrue(result["comparison"]["structure_contract_valid"])
        self.assertEqual(5, result["comparison"]["evidence_locations_checked"])
        self.assertEqual(5, result["comparison"]["evidence_locations_valid"])
        self.assertFalse(result["claim_boundaries"]["human_expert_gold"])
        self.assertFalse(result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(result["claim_boundaries"]["fta_ready"])

    def test_failed_or_malformed_model_run_cannot_be_scored(self) -> None:
        run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
        assessment = json.loads(ASSESSMENT_PATH.read_text(encoding="utf-8"))
        run["status"] = "failed_no_retry"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            failed_path = temp / "failed.json"
            assessment_path = temp / "assessment.json"
            failed_path.write_text(json.dumps(run), encoding="utf-8")
            assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
            with self.assertRaisesRegex(ComparisonError, "successful response_received"):
                compare_saved_run("SMOKE-001", run_path=failed_path, assessment_path=assessment_path)

    def test_expert_gold_reference_is_rejected(self) -> None:
        reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        reference["human_expert_gold"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            reference_path = Path(temp_dir) / "gold.json"
            reference_path.write_text(json.dumps(reference), encoding="utf-8")
            with self.assertRaisesRegex(ComparisonError, "cannot be used as expert Gold"):
                compare_saved_run("SMOKE-001", reference_path=reference_path)


if __name__ == "__main__":
    unittest.main()
