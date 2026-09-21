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


if __name__ == "__main__":
    unittest.main()
