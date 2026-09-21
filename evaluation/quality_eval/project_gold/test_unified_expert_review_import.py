import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT_GOLD = ROOT / "evaluation" / "quality_eval" / "project_gold"
sys.path.insert(0, str(PROJECT_GOLD))

from import_unified_expert_review import import_review  # noqa: E402


class UnifiedExpertReviewImportTests(unittest.TestCase):
    SOURCE = ROOT / "evaluation/quality_eval/datasets/fta_unified_expert_review_57_2026-09-20.md"

    def test_imports_all_records_and_preserves_decisions(self):
        dataset = import_review(self.SOURCE)
        self.assertEqual(57, dataset["dataset_info"]["total"])
        self.assertEqual(27, dataset["dataset_info"]["project_records"])
        self.assertEqual(30, dataset["dataset_info"]["public_records"])
        self.assertEqual(
            {"审核通过": 42, "证据不足": 6, "语义需修改": 8, "无法判断": 1},
            dataset["dataset_info"]["decision_counts"],
        )
        self.assertTrue(dataset["gold_status"]["accepted_as_expert_by_user"])

    def test_corrections_do_not_overwrite_model_prediction(self):
        dataset = import_review(self.SOURCE)
        record = next(item for item in dataset["samples"] if item["sample_id"] == "PH-F01600")
        self.assertIn("交叉比较数据编号", record["model_prediction"]["record"]["causes"])
        self.assertNotIn("交叉比较数据编号", record["gold_records"][0]["causes"])
        self.assertEqual(
            ["另一个监控通道发出停止请求", "控制定时器届满", "PROFIsafe控制故障"],
            record["gold_records"][0]["causes"],
        )

    def test_evidence_insufficiency_remains_a_review_outcome(self):
        dataset = import_review(self.SOURCE)
        record = next(item for item in dataset["samples"] if item["sample_id"] == "SIEMENS_S210_2019_A01706")
        self.assertEqual("证据不足", record["expert_review"]["decision"])
        self.assertEqual("抽取证据-候选原因", record["expert_review"]["fields_to_modify"])
        self.assertEqual(record["model_prediction"]["record"], record["gold_records"][0])


if __name__ == "__main__":
    unittest.main()
