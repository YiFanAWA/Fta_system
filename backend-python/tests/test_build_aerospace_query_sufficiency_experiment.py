import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation/quality_eval/public_sources"))

from build_aerospace_query_sufficiency_experiment import build  # noqa: E402


SAMPLE = ROOT / "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"
DEV = ROOT / "evaluation/quality_eval/datasets/aerospace_retrieval_dev_v1_2026-09-21.json"


class AerospaceSufficiencyExperimentTests(unittest.TestCase):
    def test_builds_paired_base_and_enriched_queries(self):
        payload = build(SAMPLE, DEV)
        self.assertEqual(32, payload["dataset_info"]["query_count"])
        self.assertEqual({"base", "enriched"}, {query["variant"] for query in payload["queries"]})
        self.assertEqual(
            len([query for query in payload["queries"] if query["variant"] == "base"]),
            len([query for query in payload["queries"] if query["variant"] == "enriched"]),
        )
        enriched = [query for query in payload["queries"] if query["variant"] == "enriched"]
        self.assertTrue(all(query["query_sufficiency"] == "sufficient" for query in enriched))


if __name__ == "__main__":
    unittest.main()
