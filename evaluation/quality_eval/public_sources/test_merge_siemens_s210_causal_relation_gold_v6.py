import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v5 import build_bundle  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v3 import load_json  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v6 import merge_gold  # noqa: E402


DATASETS = ROOT / "evaluation" / "quality_eval" / "datasets"


class MergeCausalRelationGoldV6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = load_json(DATASETS / "siemens_s210_causal_relation_gold_v5.json")
        cls.source = load_json(DATASETS / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json")
        cls.bundles = [
            load_json(DATASETS / name)
            for name in (
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json",
            )
        ]
        cls.candidates = build_bundle(cls.source, cls.bundles, limit=50, reviewer="刘武")

    def test_v5_review_merges_only_approved_rows(self):
        rows = []
        for index, candidate in enumerate(self.candidates["candidates"]):
            approved = index < 45
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "fault_code": candidate["target_node"]["fault_code"],
                    "fault_description": candidate["target_node"]["description"],
                    "cause_node": candidate["source_node"]["text"],
                    "evidence_reference": candidate["evidence"][0]["evidence_id"],
                    "evidence_text": candidate["evidence"][0]["quote"],
                    "causal_status": "causal" if approved else "associated_only",
                    "direction": "source_to_target" if approved else "undirected",
                    "relation_type": "causes" if approved else "associated_with",
                    "fta_eligible": approved,
                    "overall_decision": "approve" if approved else "reject",
                    "review_comment": "fixture",
                }
            )
        review = {"reviewer": "刘武", "review_date": "2026-09-22", "records": rows}
        gold = merge_gold(self.previous, self.candidates, review, ["review-v5.json"])

        self.assertEqual(gold["dataset_info"]["version"], "v6")
        self.assertEqual(gold["dataset_info"]["reviewed_candidate_count"], 246)
        self.assertEqual(gold["dataset_info"]["unreviewed_candidate_count"], 795)
        self.assertEqual(gold["dataset_info"]["approved_causal_relation_count"], 163)
        self.assertEqual(gold["dataset_info"]["excluded_candidate_count"], 83)
        self.assertEqual(gold["dataset_info"]["review_summary_v5"]["approve"], 45)
        self.assertFalse(gold["dataset_info"]["fta_ready"])


if __name__ == "__main__":
    unittest.main()
