import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v5 import build_bundle  # noqa: E402
from prepare_siemens_s210_causal_relation_revision_v5 import build_revision_package  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v3 import load_json  # noqa: E402


DATASETS = ROOT / "evaluation" / "quality_eval" / "datasets"


class CausalRelationRevisionV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = load_json(DATASETS / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json")
        prior = [
            load_json(DATASETS / name)
            for name in (
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json",
            )
        ]
        cls.bundle = build_bundle(source, prior, 50, "刘武")
        cls.review = load_json(
            Path(r"C:\Users\爹\Downloads\Siemens_S210_Causal_Relation_Expert_Review_v5_LiuWu_FULL_50.json")
        )

    def test_revision_package_keeps_both_rows_pending(self):
        package = build_revision_package(self.bundle, self.review, "刘武")
        self.assertEqual(package["dataset_info"]["candidate_count"], 2)
        self.assertEqual(
            [item["candidate_id"] for item in package["revisions"]],
            ["CR-CAND-V5-007", "CR-CAND-V5-021"],
        )
        self.assertTrue(package["revisions"][1]["suggested_evidence"]["start"] > 0)
        self.assertTrue(
            all(item["expert_review"]["overall_decision"] == "pending" for item in package["revisions"])
        )


if __name__ == "__main__":
    unittest.main()
