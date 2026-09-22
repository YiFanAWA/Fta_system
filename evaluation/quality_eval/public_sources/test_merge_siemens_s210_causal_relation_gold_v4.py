import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle_v4 import build_bundle  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v4 import merge_gold  # noqa: E402
from merge_siemens_s210_causal_relation_gold_v3 import load_json  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
DATASETS = ROOT / "evaluation" / "quality_eval" / "datasets"


class MergeCausalRelationGoldV4Tests(unittest.TestCase):
    def test_merge_v4_fixture_keeps_revise_out_of_gold(self) -> None:
        previous = load_json(DATASETS / "siemens_s210_causal_relation_gold_v3.json")
        source = load_json(DATASETS / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json")
        bundles = [
            load_json(DATASETS / name)
            for name in (
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
            )
        ]
        candidates = build_bundle(source, bundles, limit=50, reviewer="刘武")
        rows = []
        for index, candidate in enumerate(candidates["candidates"]):
            evidence = candidate["evidence"][0]
            approved = index < 45
            revised = index == 45
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "fault_code": candidate["target_node"]["fault_code"],
                    "fault_description": candidate["target_node"]["description"],
                    "cause_node": candidate["source_node"]["text"],
                    "evidence_reference": evidence["evidence_id"],
                    "evidence_text": evidence["quote"],
                    "causal_status": "causal" if approved or revised else "associated_only",
                    "direction": "source_to_target" if approved or revised else "undirected",
                    "relation_type": "causes" if approved or revised else "associated_with",
                    "fta_eligible": approved or revised,
                    "overall_decision": "approve" if approved else ("revise" if revised else "reject"),
                    "review_comment": "fixture",
                }
            )
        review = {
            "reviewer": "刘武",
            "review_date": "2026-09-22",
            "records": rows,
        }
        gold = merge_gold(previous, candidates, review, ["review-v4.json"])

        self.assertEqual(gold["dataset_info"]["version"], "v4")
        self.assertEqual(gold["dataset_info"]["reviewed_candidate_count"], 196)
        self.assertEqual(gold["dataset_info"]["unreviewed_candidate_count"], 845)
        self.assertEqual(gold["dataset_info"]["approved_causal_relation_count"], 117)
        self.assertEqual(gold["dataset_info"]["excluded_candidate_count"], 79)
        self.assertEqual(gold["dataset_info"]["review_summary_v4"]["revise"], 1)
        self.assertEqual(len([r for r in gold["relations"] if r["relation_id"].startswith("S210-CAUSAL-V4-")]), 45)
        self.assertFalse(gold["dataset_info"]["fta_ready"])


if __name__ == "__main__":
    unittest.main()
