import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from query_decision import QueryDecisionPolicy  # noqa: E402


class QueryDecisionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = QueryDecisionPolicy()

    def test_insufficient_clarifies(self):
        result = self.policy.decide(route_mode="cross_domain", sufficiency_level="insufficient")
        self.assertEqual("clarify", result.action)

    def test_partial_cross_domain_warns_without_blocking(self):
        result = self.policy.decide(route_mode="cross_domain", sufficiency_level="partially_sufficient")
        self.assertEqual("retrieve_with_warning", result.action)

    def test_sufficient_scoped_retrieves(self):
        result = self.policy.decide(route_mode="scoped", sufficiency_level="sufficient")
        self.assertEqual("retrieve", result.action)


if __name__ == "__main__":
    unittest.main()
