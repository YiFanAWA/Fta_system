from __future__ import annotations

import json
import unittest

from evaluation.quality_eval.event_scope_tree_prompt_v7 import PROMPT_VERSION, build_prompt, prompt_sha256
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH


CASES_PATH = PACKET_PATH.parent / "fta_event_scope_prompt_v7_regression_cases_v1.json"


class TestEventScopeTreePromptV7(unittest.TestCase):
    def setUp(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        self.model_input = model_input_payload(packet)
        self.prompt = build_prompt(self.model_input)
        self.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_prompt_requires_logic_and_output_binding_for_known_gates(self) -> None:
        self.assertIn("全部 child 之间的 AND/OR 关系", self.prompt)
        self.assertIn("指向该 scope 的 output_node_id", self.prompt)
        self.assertIn("scope_evidence 只能证明", self.prompt)
        self.assertIn("不能代替 logic_evidence", self.prompt)
        self.assertIn("不得只引用孤立的 and/or", self.prompt)

    def test_prompt_keeps_direct_joint_logic_and_alternative_examples(self) -> None:
        self.assertIn("either pathway A or pathway B can lead to T", self.prompt)
        self.assertIn("T occurs only when A and B are both present", self.prompt)
        self.assertIn("A and B were both observed before T", self.prompt)

    def test_regressions_distinguish_evidence_bound_or_and_and_unknown(self) -> None:
        self.assertEqual("offline_policy_regressions_not_gold", self.cases["dataset_status"])
        self.assertFalse(self.cases["human_expert_gold"])
        self.assertFalse(self.cases["accuracy_claim_allowed"])
        cases = {case["case_id"]: case for case in self.cases["cases"]}
        fig7 = cases["FIG7-S1-OR-EVIDENCE-BINDING"]
        self.assertEqual(["E6", "E7"], fig7["child_node_ids"])
        self.assertIn("same Top Event", fig7["required_logic_evidence"])
        self.assertEqual("OR", fig7["expected_candidate_gate"])
        self.assertFalse(fig7["final_gate_approved"])
        self.assertEqual("AND", cases["EXPLICIT-JOINT-CONDITION-AND"]["expected_candidate_gate"])
        self.assertEqual("unknown", cases["COOCCURRENCE-IS-NOT-AND"]["expected_candidate_gate"])
        self.assertEqual("unknown", cases["UNSCOPED-ALTERNATIVE-IS-NOT-OR"]["expected_candidate_gate"])
        self.assertFalse(self.cases["guardrails"]["model_request_performed"])

    def test_fig7_evidence_is_exactly_available_in_label_free_model_input(self) -> None:
        fig7 = next(case for case in self.cases["cases"] if case["case_id"] == "FIG7-S1-OR-EVIDENCE-BINDING")
        source = next(
            segment["text"]
            for segment in self.model_input["source_segments"]
            if segment["segment_id"] == fig7["source_segment_id"]
        )
        self.assertIn(fig7["source_quote"], source)
        self.assertEqual(PROMPT_VERSION, "event-scope-text-only-tree-v7-bound-logic-evidence")
        self.assertEqual(64, len(prompt_sha256(self.model_input)))
        self.assertNotIn("diagram_gates", self.prompt)
        self.assertNotIn("text_gate_reviews", self.prompt)
        self.assertNotIn("expected_candidate_gate", self.prompt)

    def test_v7_preserves_v6_single_hierarchy_and_unknown_field_contract(self) -> None:
        self.assertIn("一个 output_node_id 在全份输出中只能出现于一个 gate scope", self.prompt)
        self.assertIn("unknown_reason 必须显式为 JSON null", self.prompt)
        self.assertIn("必须是允许的原因代码", self.prompt)


if __name__ == "__main__":
    unittest.main()
