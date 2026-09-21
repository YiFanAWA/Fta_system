import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_domain_router_error_taxonomy import build  # noqa: E402


class DomainRouterTaxonomyTests(unittest.TestCase):
    def test_classifies_cross_domain_rows_without_mutating_router(self):
        report = {
            "queries": [
                {
                    "query_id": "Q-A",
                    "query": "STO status mismatch",
                    "query_domain": "industrial_drive",
                    "router": {"mode": "cross_domain", "selected_scope_ids": ["siemens", "aero"]},
                },
                {
                    "query_id": "Q-B",
                    "query": "temperature failure",
                    "query_domain": "aerospace",
                    "router": {"mode": "cross_domain", "selected_scope_ids": ["siemens", "aero"]},
                },
                {
                    "query_id": "Q-S",
                    "query": "JASC 2100",
                    "query_domain": "aerospace",
                    "router": {"mode": "scoped", "selected_scope_ids": ["faa_sdr"]},
                },
            ]
        }
        result = build(report)
        self.assertEqual(2, result["taxonomy_info"]["cross_domain_queries"])
        self.assertEqual(1, result["summary"]["missing_router_signal"])
        self.assertEqual(1, result["summary"]["domain_ambiguous"])
        self.assertEqual(0, result["summary"]["false_scoped"])
        self.assertTrue(all(row["requires_human_review"] for row in result["cross_domain_rows"]))


if __name__ == "__main__":
    unittest.main()
