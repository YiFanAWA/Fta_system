import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from merge_siemens_s210_causal_relation_gold_v5 import merge_gold  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v3 import load_json  # noqa: E402


DATASETS = ROOT / "evaluation" / "quality_eval" / "datasets"


class MergeCausalRelationGoldV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = load_json(DATASETS / "siemens_s210_causal_relation_gold_v4.json")
        cls.candidates = load_json(
            DATASETS / "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json"
        )

    def test_approved_revision_replaces_pending_exclusion(self):
        review = {
            "reviewer": "刘武",
            "fault_code": "A01730",
            "candidate_id": "CR-CAND-V4-029",
            "previous_status": "pending_expert_revision",
            "review": {
                "causal_status": "causal",
                "direction": "source_to_target",
                "relation_type": "causes",
                "fta_eligible": True,
                "overall_decision": "approve",
                "final_cause_text": "PROFIsafe transferred reference block is negative",
                "expert_reason": "approved fixture",
                "reviewer": "刘武",
                "reviewed_at": "2026-09-22T22:48:40+08:00",
            },
            "gate_check": {
                "overall_decision_approve": True,
                "causal_status_causal": True,
                "direction_source_to_target": True,
                "relation_type_causes": True,
                "fta_eligible_true": True,
                "final_cause_text_matches_evidence": True,
                "eligible_for_next_gold": True,
            },
        }
        gold = merge_gold(self.previous, self.candidates, review, ["approval.json"])

        self.assertEqual(gold["dataset_info"]["version"], "v5")
        self.assertEqual(gold["dataset_info"]["reviewed_candidate_count"], 196)
        self.assertEqual(gold["dataset_info"]["unreviewed_candidate_count"], 845)
        self.assertEqual(gold["dataset_info"]["approved_causal_relation_count"], 118)
        self.assertEqual(gold["dataset_info"]["excluded_candidate_count"], 78)
        self.assertFalse(
            any(row.get("candidate_id") == "CR-CAND-V4-029" for row in gold["excluded_candidates"])
        )
        relation = next(
            row for row in gold["relations"] if row.get("candidate_id") == "CR-CAND-V4-029"
        )
        self.assertEqual(
            relation["source_node"]["text"],
            "PROFIsafe transferred reference block is negative",
        )
        self.assertEqual(
            relation["evidence"][0]["quote"],
            "The reference block transferred via PROFIsafe is negative",
        )
        self.assertEqual(relation["evidence"][0]["start"], 118)
        self.assertEqual(relation["evidence"][0]["end"], 175)
        self.assertFalse(gold["dataset_info"]["fta_ready"])


if __name__ == "__main__":
    unittest.main()
