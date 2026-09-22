import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v3 import build_bundle  # noqa: E402
from validate_siemens_s210_causal_relation_candidates import validate  # noqa: E402


class SiemensS210CausalRelationReviewBundleV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
            ).read_text(encoding="utf-8")
        )
        cls.candidate_v1 = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_causal_relation_candidates_v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.candidate_v2 = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json"
            ).read_text(encoding="utf-8")
        )

    def test_v3_excludes_v1_v2_and_spreads_across_faults(self):
        bundle = build_bundle(
            self.source,
            [self.candidate_v1, self.candidate_v2],
            limit=50,
            reviewer="刘武",
        )
        self.assertEqual([], validate(bundle))
        self.assertEqual(50, len(bundle["candidates"]))
        self.assertEqual(50, bundle["dataset_info"]["target_fault_count"])
        self.assertEqual(945, bundle["dataset_info"]["remaining_unreviewed_candidate_count"])
        reviewed_nodes = {
            candidate["source_node"]["node_id"]
            for candidate in self.candidate_v1["candidates"] + self.candidate_v2["candidates"]
        }
        self.assertTrue(
            all(candidate["source_node"]["node_id"] not in reviewed_nodes for candidate in bundle["candidates"])
        )
        self.assertTrue(all(candidate["candidate_id"].startswith("CR-CAND-V3-") for candidate in bundle["candidates"]))


if __name__ == "__main__":
    unittest.main()
