import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v6 import build_bundle  # noqa: E402
from validate_siemens_s210_causal_relation_candidates import validate  # noqa: E402


DATASETS = ROOT / "evaluation" / "quality_eval" / "datasets"


class SiemensS210CausalRelationReviewBundleV6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(
            (DATASETS / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json")
            .read_text(encoding="utf-8")
        )
        cls.bundles = [
            json.loads((DATASETS / name).read_text(encoding="utf-8"))
            for name in (
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json",
            )
        ]

    def test_v6_excludes_v1_to_v5_and_validates(self):
        bundle = build_bundle(self.source, self.bundles, limit=50, reviewer="刘武")
        self.assertEqual(bundle["dataset_info"]["version"], "v6")
        self.assertEqual(bundle["dataset_info"]["reviewed_candidate_count"], 246)
        self.assertEqual(bundle["dataset_info"]["remaining_unreviewed_candidate_count"], 795)
        self.assertEqual(bundle["dataset_info"]["candidate_count"], 50)
        self.assertEqual(bundle["dataset_info"]["target_fault_count"], 50)
        self.assertTrue(all(item["candidate_id"].startswith("CR-CAND-V6-") for item in bundle["candidates"]))
        self.assertTrue(validate(bundle) == [])

    def test_v6_does_not_repeat_reviewed_source_nodes(self):
        bundle = build_bundle(self.source, self.bundles, limit=50, reviewer="刘武")
        reviewed = {
            candidate["source_node"]["node_id"]
            for source_bundle in self.bundles
            for candidate in source_bundle["candidates"]
        }
        self.assertTrue(
            all(candidate["source_node"]["node_id"] not in reviewed for candidate in bundle["candidates"])
        )


if __name__ == "__main__":
    unittest.main()
