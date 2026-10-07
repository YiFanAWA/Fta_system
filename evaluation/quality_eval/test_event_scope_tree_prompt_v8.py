from __future__ import annotations

import json
import unittest

from evaluation.quality_eval.event_scope_tree_prompt_v8 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH


CASES_PATH = PACKET_PATH.parent / "fta_event_scope_prompt_v8_regression_cases_v1.json"


class TestEventScopeTreePromptV8(unittest.TestCase):
    def setUp(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        self.model_input = model_input_payload(packet)
        self.prompt = build_prompt(self.model_input)
        self.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_prompt_allows_semantic_gate_interpretation_without_operator_tokens(self) -> None:
        self.assertIn("逻辑门按语义判断，不按关键词匹配", self.prompt)
        self.assertIn("原文不必出现字面", self.prompt)
        self.assertIn("不是封闭词表或关键词规则", self.prompt)
        self.assertIn("解释并绑定原文表达的逻辑含义", self.prompt)

    def test_implicit_or_and_examples_are_distinguished_from_ambiguity(self) -> None:
        cases = {case["case_id"]: case for case in self.cases["cases"]}
        self.assertEqual("OR", cases["SEMANTIC-OR-NO-OPERATOR"]["expected_candidate_gate"])
        self.assertEqual("AND", cases["SEMANTIC-AND-NO-OPERATOR"]["expected_candidate_gate"])
        self.assertNotIn(" or ", cases["SEMANTIC-OR-NO-OPERATOR"]["source_quote"].lower())
        self.assertNotIn(" and ", cases["SEMANTIC-AND-NO-OPERATOR"]["source_quote"].lower())
        self.assertEqual("unknown", cases["LEXICAL-OR-OUTSIDE-SCOPE"]["expected_candidate_gate"])
        self.assertEqual("unknown", cases["CAUSE-LIST-DOES-NOT-PROVE-OR"]["expected_candidate_gate"])
        self.assertEqual("unknown", cases["COOCCURRENCE-DOES-NOT-PROVE-AND"]["expected_candidate_gate"])

    def test_regression_fixture_is_non_gold_and_does_not_repair_observed_run(self) -> None:
        self.assertEqual("offline_semantic_policy_regressions_not_gold", self.cases["dataset_status"])
        self.assertFalse(self.cases["human_expert_gold"])
        self.assertFalse(self.cases["accuracy_claim_allowed"])
        self.assertFalse(self.cases["guardrails"]["model_request_performed"])
        observed = next(case for case in self.cases["cases"] if case["case_id"] == "FIG7-S1-EXPLICIT-OR-BINDING")
        source_packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        source = next(
            segment["text"]
            for segment in source_packet["model_input"]["source_segments"]
            if segment["segment_id"] == observed["source_segment_id"]
        )
        self.assertIn(observed["source_quote"], source)
        self.assertFalse(observed["auto_repair_allowed"])
        self.assertFalse(observed["final_gate_approved"])

    def test_label_free_input_and_v7_tree_contract_are_preserved(self) -> None:
        self.assertEqual(PROMPT_VERSION, "event-scope-text-only-tree-v8-semantic-gate-evidence")
        self.assertNotIn("diagram_gates", self.prompt)
        self.assertNotIn("text_gate_reviews", self.prompt)
        self.assertNotIn("expected_candidate_gate", self.prompt)
        self.assertIn("全部 child 之间的 AND/OR 关系", self.prompt)
        self.assertIn("指向该 scope 的 output_node_id", self.prompt)
        self.assertIn("unknown", self.prompt)


if __name__ == "__main__":
    unittest.main()
