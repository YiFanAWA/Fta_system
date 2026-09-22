import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v4 import build_bundle  # noqa: E402
from validate_siemens_s210_causal_relation_candidates import validate  # noqa: E402


class SiemensS210CausalRelationReviewBundleV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / "evaluation" / "quality_eval" / "datasets"
        cls.source = json.loads(
            (base / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json").read_text(
                encoding="utf-8"
            )
        )
        cls.candidates = [
            json.loads((base / name).read_text(encoding="utf-8"))
            for name in (
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
            )
        ]

    def test_v4_excludes_v1_v2_v3_and_leaves_895(self):
        bundle = build_bundle(self.source, self.candidates, limit=50, reviewer="刘武")
        self.assertEqual([], validate(bundle))
        self.assertEqual(50, len(bundle["candidates"]))
        self.assertEqual(50, bundle["dataset_info"]["target_fault_count"])
        self.assertEqual(895, bundle["dataset_info"]["remaining_unreviewed_candidate_count"])
        reviewed_nodes = {
            candidate["source_node"]["node_id"]
            for source in self.candidates
            for candidate in source["candidates"]
        }
        self.assertTrue(
            all(candidate["source_node"]["node_id"] not in reviewed_nodes for candidate in bundle["candidates"])
        )
        self.assertTrue(all(candidate["candidate_id"].startswith("CR-CAND-V4-") for candidate in bundle["candidates"]))


if __name__ == "__main__":
    unittest.main()
