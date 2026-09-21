import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from response_policy import ResponsePolicyLayer  # noqa: E402


class ResponsePolicyTests(unittest.TestCase):
    def setUp(self):
        self.layer = ResponsePolicyLayer()

    def test_partial_allows_retrieval_and_warns(self):
        result = self.layer.decide(sufficiency_level="partially_sufficient")
        self.assertEqual("allow", result.retrieval_policy)
        self.assertEqual("warning", result.response_policy)

    def test_insufficient_does_not_produce_definitive_answer(self):
        result = self.layer.decide(sufficiency_level="insufficient")
        self.assertEqual("allow", result.retrieval_policy)
        self.assertEqual("clarify", result.response_policy)

    def test_sufficient_is_normal(self):
        result = self.layer.decide(sufficiency_level="sufficient")
        self.assertEqual("allow", result.retrieval_policy)
        self.assertEqual("normal", result.response_policy)

    def test_cannot_determine_warns_without_blocking(self):
        result = self.layer.decide(sufficiency_level="cannot_determine")
        self.assertEqual("allow", result.retrieval_policy)
        self.assertEqual("warning", result.response_policy)

    def test_v2_direct_answer_contract(self):
        result = self.layer.decide_v2(sufficiency_level="sufficient")
        self.assertEqual("P0_DIRECT_ANSWER", result.policy)
        self.assertTrue(result.answer_allowed)
        self.assertEqual("high", result.confidence_level)
        self.assertFalse(result.warning_required)

    def test_v2_warning_contract(self):
        result = self.layer.decide_v2(sufficiency_level="partially_sufficient")
        self.assertEqual("P1_ANSWER_WITH_WARNING", result.policy)
        self.assertTrue(result.answer_allowed)
        self.assertEqual("medium", result.confidence_level)
        self.assertTrue(result.warning_required)

    def test_v2_clarification_contract_does_not_block_retrieval(self):
        result = self.layer.decide_v2(sufficiency_level="insufficient")
        self.assertEqual("P2_ASK_BEFORE_DEFINITIVE_ANSWER", result.policy)
        self.assertFalse(result.answer_allowed)
        self.assertTrue(result.need_additional_info)
        self.assertEqual("allow", result.retrieval_policy)

    def test_boundary_rejects_explicit_external_topic(self):
        result = self.layer.assess_boundary(
            question="今天天气怎么样？",
            contexts=[object()],
        )
        self.assertEqual("out_of_domain", result.knowledge_status)
        self.assertFalse(result.answer_allowed)
        self.assertIn("天气", result.matched_external_signals)

    def test_boundary_warns_for_technical_query_without_identity(self):
        result = self.layer.assess_boundary(
            question="温度异常怎么办？",
            contexts=[object()],
        )
        self.assertEqual("supported_with_warning", result.knowledge_status)
        self.assertTrue(result.answer_allowed)
        self.assertTrue(result.warning_required)

    def test_boundary_clarifies_low_information_query(self):
        result = self.layer.assess_boundary(
            question="设备坏了。",
            contexts=[object()],
        )
        self.assertEqual("insufficient_evidence", result.knowledge_status)
        self.assertFalse(result.answer_allowed)
        self.assertTrue(result.need_additional_info)

    def test_boundary_accepts_explicit_s210_identifier(self):
        result = self.layer.assess_boundary(
            question="S210 F01630 是什么故障？",
            contexts=[object()],
        )
        self.assertEqual("supported", result.knowledge_status)
        self.assertTrue(result.answer_allowed)
        self.assertEqual("high", result.confidence_level)

    def test_boundary_does_not_treat_data_as_aircraft_ata_signal(self):
        result = self.layer.assess_boundary(
            question='CU-EEPROM incorrect read-write data',
            contexts=[object()],
        )
        self.assertNotEqual("out_of_domain", result.knowledge_status)


if __name__ == "__main__":
    unittest.main()
