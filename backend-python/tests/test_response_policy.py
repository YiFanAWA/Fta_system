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


if __name__ == "__main__":
    unittest.main()
