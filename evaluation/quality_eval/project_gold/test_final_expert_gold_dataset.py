import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT_GOLD = ROOT / "evaluation" / "quality_eval" / "project_gold"
sys.path.insert(0, str(PROJECT_GOLD))

from build_final_expert_gold_dataset import finalize_dataset  # noqa: E402


class FinalExpertGoldDatasetTests(unittest.TestCase):
    def test_independent_expert_report_promotes_provisional_dataset(self):
        provisional = json.loads(
            (ROOT / "evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v1.json")
            .read_text(encoding="utf-8")
        )
        annotations = json.loads(
            (ROOT / "evaluation/quality_eval/datasets/fta_project_handbook_expert_annotations_v9.json")
            .read_text(encoding="utf-8")
        )
        final = finalize_dataset(provisional, annotations, source_annotation="report.json")
        info = final["dataset_info"]
        self.assertEqual("human_expert_reviewed", info["label_status"])
        self.assertTrue(info["human_expert_reviewed"])
        self.assertEqual(27, info["review"]["decision_counts"]["审核通过"])
        self.assertTrue(final["gold_status"]["f1_ready"])
        self.assertEqual("unknown", final["gold_status"]["logic_status"])
        self.assertEqual(27, len(final["samples"]))
        record_15 = next(item for item in final["samples"] if item["sample_id"] == "PH-A01631")
        self.assertEqual("审核通过", record_15["expert_review"]["decision"])
        self.assertFalse(record_15["expert_review"]["correction_applied"])
        self.assertTrue(record_15["review_history"][-1]["review_version"])


if __name__ == "__main__":
    unittest.main()
