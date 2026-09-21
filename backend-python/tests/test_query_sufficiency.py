import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from rag.query_sufficiency import QuerySufficiencyEvaluator  # noqa: E402


class QuerySufficiencyTests(unittest.TestCase):
    def setUp(self):
        self.evaluator = QuerySufficiencyEvaluator()

    def test_explicit_system_and_fault_code_is_sufficient(self):
        decision = self.evaluator.assess("S210 F01630", domain_confidence=0.99, route_mode="scoped")
        self.assertEqual("sufficient", decision.level)
        self.assertFalse(decision.requires_clarification)
        self.assertEqual(("F01630",), decision.matched_identifiers)

    def test_fault_only_requires_clarification(self):
        decision = self.evaluator.assess("fault")
        self.assertEqual("insufficient", decision.level)
        self.assertTrue(decision.requires_clarification)
        self.assertIn("device/system/manufacturer", decision.missing_information)

    def test_technical_phrase_without_identity_is_partial(self):
        decision = self.evaluator.assess("temperature fault")
        self.assertEqual("partially_sufficient", decision.level)
        self.assertFalse(decision.requires_clarification)
        self.assertIn("device/system/manufacturer", decision.missing_information)


if __name__ == "__main__":
    unittest.main()
