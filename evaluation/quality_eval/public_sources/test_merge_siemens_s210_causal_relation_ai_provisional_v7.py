import unittest
from pathlib import Path

from merge_siemens_s210_causal_relation_ai_provisional_v7 import (
    build_provisional,
    load_json,
)


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
RUNS = ROOT / "runs"


class AiProvisionalGoldV7Test(unittest.TestCase):
    def test_adds_two_relations_without_opening_formal_gate(self) -> None:
        result = build_provisional(
            load_json(DATASETS / "siemens_s210_causal_relation_gold_v6.json"),
            load_json(DATASETS / "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json"),
            load_json(RUNS / "siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.json"),
        )
        info = result["dataset_info"]
        self.assertEqual(info["status"], "ai_assisted_provisional")
        self.assertFalse(info["expert_validated"])
        self.assertEqual(info["formal_approved_causal_relation_count"], 163)
        self.assertEqual(info["provisional_relation_count"], 165)
        self.assertEqual(info["provisional_excluded_candidate_count"], 81)
        self.assertFalse(info["fta_ready"])
        rows = [row for row in result["relations"] if row["relation_id"].startswith("S210-CAUSAL-AI-V7-")]
        self.assertEqual({row["target_node"]["fault_code"] for row in rows}, {"A01691", "A01782"})
        self.assertTrue(all(row["expert_review"]["human_confirmation_required"] for row in rows))

    def test_provisional_review_is_not_official_approve(self) -> None:
        result = build_provisional(
            load_json(DATASETS / "siemens_s210_causal_relation_gold_v6.json"),
            load_json(DATASETS / "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json"),
            load_json(RUNS / "siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.json"),
        )
        rows = [row for row in result["relations"] if row["relation_id"].startswith("S210-CAUSAL-AI-V7-")]
        self.assertTrue(all(row["expert_review"]["overall_decision"] == "ai_provisional" for row in rows))


if __name__ == "__main__":
    unittest.main()
