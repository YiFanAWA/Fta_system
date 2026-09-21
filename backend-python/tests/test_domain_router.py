import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from domain_router import DomainScopeProfile, RuleBasedDomainRouter  # noqa: E402


class DomainRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = RuleBasedDomainRouter(
            (
                DomainScopeProfile(
                    scope_id="siemens",
                    domain="industrial_drive",
                    strong_terms=("siemens", "sinamics", "s210", "drive-cliq"),
                    identifier_patterns=(r"\b[AFN]\d{5}\b", r"\b[pr]\d{4,5}\b"),
                ),
                DomainScopeProfile(
                    scope_id="aerospace",
                    domain="aerospace",
                    strong_terms=("航空器", "航空", "faa", "jasc", "sdr"),
                    identifier_patterns=(r"\bjasc\s*\d{4}\b",),
                ),
            )
        )

    def test_explicit_identifier_scopes_to_siemens(self):
        decision = self.router.route("F30002 的故障原因是什么？")
        self.assertEqual(("siemens",), decision.selected_scope_ids)
        self.assertEqual("scoped", decision.mode)
        self.assertTrue(any(signal.startswith("identifier_pattern:") for signal in decision.signals))

    def test_explicit_aerospace_term_scopes_to_aerospace(self):
        decision = self.router.route("JASC 2100 对应哪些航空故障记录？")
        self.assertEqual(("aerospace",), decision.selected_scope_ids)
        self.assertEqual("scoped", decision.mode)

    def test_low_information_query_keeps_cross_domain_scope(self):
        decision = self.router.route("通信失败")
        self.assertEqual("cross_domain", decision.mode)
        self.assertEqual(("siemens", "aerospace"), decision.selected_scope_ids)
        self.assertEqual(0.0, decision.confidence)

    def test_tied_signals_do_not_force_a_scope(self):
        router = RuleBasedDomainRouter(
            (
                DomainScopeProfile(scope_id="left", domain="left", strong_terms=("shared",)),
                DomainScopeProfile(scope_id="right", domain="right", strong_terms=("shared",)),
            )
        )
        decision = router.route("shared failure")
        self.assertEqual("cross_domain", decision.mode)


if __name__ == "__main__":
    unittest.main()
