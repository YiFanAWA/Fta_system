from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_semantic_review_cases_v1.json"
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json"
PACKET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"


def _by_case_id(payload: dict) -> dict[str, dict]:
    return {case["case_id"]: case for case in payload["cases"]}


class TestEventScopeSemanticReviewRegressionV1(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_policy_examples_are_not_gold_or_accuracy_samples(self) -> None:
        self.assertEqual("development_policy_cases_not_gold", self.cases["dataset_status"])
        self.assertFalse(self.cases["human_expert_gold"])
        self.assertFalse(self.cases["accuracy_claim_allowed"])
        self.assertFalse(self.cases["guardrails"]["gold_written"])

    def test_explicit_or_and_cooccurrence_have_distinct_review_dispositions(self) -> None:
        cases = _by_case_id(self.cases)
        self.assertEqual("OR", cases["POLICY-OR-001"]["expected_candidate_gate"])
        self.assertTrue(cases["POLICY-OR-001"]["logic_evidence_required"])
        self.assertFalse(cases["POLICY-OR-001"]["final_gate_approved"])
        self.assertEqual("AND", cases["POLICY-AND-001"]["expected_candidate_gate"])
        self.assertTrue(cases["POLICY-AND-001"]["logic_evidence_required"])
        self.assertFalse(cases["POLICY-AND-001"]["final_gate_approved"])
        self.assertEqual("unknown", cases["POLICY-COOCCURRENCE-001"]["expected_candidate_gate"])
        self.assertFalse(cases["POLICY-COOCCURRENCE-001"]["logic_evidence_required"])

    def test_v6_explicit_alternative_miss_remains_a_semantic_blocker(self) -> None:
        run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        gates = run["model_output"]["parsed_json"]["gates"]
        s1 = next(gate for gate in gates if gate["scope_id"] == "S1")
        source_text = next(
            segment["text"]
            for segment in packet["model_input"]["source_segments"]
            if segment["segment_id"] == s1["scope_evidence"]["segment_id"]
        )
        self.assertIn(s1["scope_evidence"]["quote"], source_text)
        self.assertIn("or", s1["scope_evidence"]["quote"].lower())
        self.assertEqual("unknown", s1["gate"])
        self.assertIsNone(s1["logic_evidence"])

        case = _by_case_id(self.cases)["FIG7-V6-S1-OR-NOT-BOUND"]
        self.assertEqual(
            "semantic_review_blocker_explicit_alternative_not_bound",
            case["expected_review_disposition"],
        )
        self.assertFalse(case["automatic_repair"])
        self.assertFalse(case["semantic_acceptance"])

    def test_event_identity_and_composite_granularity_stay_manual(self) -> None:
        run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in run["model_output"]["parsed_json"]["nodes"]}
        cases = _by_case_id(self.cases)

        self.assertIn("cell explosion", nodes["E2"]["text"].lower())
        self.assertIn("cell explosion", nodes["E4"]["text"].lower())
        self.assertEqual(
            "manual_review_event_identity_no_auto_merge_or_split",
            cases["FIG7-V6-SHARED-CELL-EVENT"]["expected_review_disposition"],
        )
        self.assertFalse(cases["FIG7-V6-SHARED-CELL-EVENT"]["automatic_repair"])

        self.assertGreater(len(nodes["E5"]["text"]), 120)
        self.assertIn("sympathetic secondary explosion", nodes["E7"]["text"].lower())
        self.assertEqual(
            "manual_review_event_granularity_no_invented_decomposition",
            cases["FIG7-V6-COMPOSITE-EVENT-BOUNDARY"]["expected_review_disposition"],
        )
        self.assertFalse(cases["FIG7-V6-COMPOSITE-EVENT-BOUNDARY"]["automatic_repair"])


if __name__ == "__main__":
    unittest.main()
