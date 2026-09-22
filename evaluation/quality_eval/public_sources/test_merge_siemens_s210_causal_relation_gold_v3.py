import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from merge_siemens_s210_causal_relation_gold_v3 import load_json, merge_gold  # noqa: E402


REPO = Path(__file__).resolve().parents[3]
DATASETS = REPO / "evaluation" / "quality_eval" / "datasets"


class MergeCausalRelationGoldV3Tests(unittest.TestCase):
    def test_merge_v3_review_into_gold(self) -> None:
        previous = load_json(DATASETS / "siemens_s210_causal_relation_gold_v2.json")
        candidates = load_json(DATASETS / "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json")
        rows = []
        for index, candidate in enumerate(candidates["candidates"]):
            evidence = candidate["evidence"][0]
            is_causal = index < 33
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "fault_code": candidate["target_node"]["fault_code"],
                    "fault_description": candidate["target_node"]["description"],
                    "candidate_cause": candidate["source_node"]["text"],
                    "evidence_ref": evidence["evidence_id"],
                    "evidence_text": evidence["quote"],
                    "causal_status": "causal" if is_causal else "associated_only",
                    "direction": "source_to_target" if is_causal else "undirected",
                    "relation_type": "causes" if is_causal else "associated_with",
                    "fta_eligible": is_causal,
                    "overall_decision": "approve" if is_causal else "revise",
                    "expert_comment": "fixture",
                }
            )
        review = {
            "dataset_info": {
                "reviewer": "刘武",
                "reviewed_at": "2026-09-22",
            },
            "rows": rows,
        }

        gold = merge_gold(
            previous,
            candidates,
            review,
            [
                "Siemens_S210_Causal_Relation_Expert_Review_v3_LiuWu_FULL_50.json",
                "Siemens_S210_Causal_Relation_Expert_Review_v3_LiuWu_FULL_50.md",
                "Siemens_S210_Causal_Relation_Expert_Review_v3_LiuWu_FULL_50.docx",
            ],
        )

        self.assertEqual(gold["dataset_info"]["version"], "v3")
        self.assertEqual(gold["dataset_info"]["candidate_review_count"], 146)
        self.assertEqual(gold["dataset_info"]["approved_causal_relation_count"], 72)
        self.assertEqual(gold["dataset_info"]["excluded_candidate_count"], 74)
        self.assertTrue(gold["dataset_info"]["review_date_missing"])
        self.assertEqual(gold["dataset_info"]["review_date_missing_batches"], ["batch_v2"])
        self.assertEqual(gold["dataset_info"]["review_summary_v3"]["causal"], 33)
        self.assertEqual(gold["dataset_info"]["review_summary_v3"]["associated_only"], 17)
        self.assertFalse(gold["dataset_info"]["causal_relations_complete"])
        self.assertFalse(gold["dataset_info"]["fta_ready"])
        self.assertEqual(len({row["relation_id"] for row in gold["relations"]}), 72)
        self.assertTrue(all(row["relation_id"].startswith("S210-CAUSAL-") for row in gold["relations"]))
        self.assertTrue(all(row["expert_review"]["reviewer"] == "刘武" for row in gold["relations"][-33:]))


if __name__ == "__main__":
    unittest.main()
