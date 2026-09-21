import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from domain_evidence_registry import build_domain_scope_profiles  # noqa: E402


class DomainEvidenceRegistryTests(unittest.TestCase):
    def test_pending_signals_are_not_router_signals_by_default(self):
        profiles = {profile.scope_id: profile for profile in build_domain_scope_profiles()}
        siemens = profiles["siemens_s210"]
        self.assertIn("s210", siemens.strong_terms)
        self.assertNotIn("sto", {term.casefold() for term in siemens.strong_terms})
        self.assertNotIn("si motion", {term.casefold() for term in siemens.strong_terms})

    def test_offline_review_can_include_pending_signals_explicitly(self):
        profiles = {profile.scope_id: profile for profile in build_domain_scope_profiles(include_pending=True)}
        siemens = profiles["siemens_s210"]
        terms = {term.casefold() for term in siemens.strong_terms}
        self.assertIn("sto", terms)
        self.assertIn("si motion", terms)


if __name__ == "__main__":
    unittest.main()
