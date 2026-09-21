import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_expert_gold_dataset import build_gold_dataset  # noqa: E402


class ExpertGoldDatasetTests(unittest.TestCase):
    def test_builds_all_reviewed_records_without_promoting_unknown_logic(self):
        bundle_path = (
            ROOT
            / "evaluation"
            / "quality_eval"
            / "runs"
            / "fta_project_handbook_expert_review_bundle_v8.json"
        )
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

        dataset = build_gold_dataset(
            bundle,
            source_bundle=str(bundle_path),
        )

        self.assertEqual("project_reviewed_provisional", dataset["dataset_info"]["label_status"])
        self.assertFalse(dataset["dataset_info"]["human_expert_reviewed"])
        self.assertEqual({"test": 27}, dataset["dataset_info"]["stats"]["split"])
        self.assertEqual(27, len(dataset["samples"]))
        self.assertEqual(27, dataset["dataset_info"]["review"]["decision_counts"]["审核通过"])
        self.assertTrue(all(item["logic_status"] == "unknown" for item in dataset["samples"]))
        self.assertTrue(all(item["expert_review"]["decision"] == "审核通过" for item in dataset["samples"]))

        record_10 = next(item for item in dataset["samples"] if item["sample_id"] == "PH-F01600")
        self.assertIn("交叉比较数据编号", record_10["gold_records"][0]["causes"])
        self.assertNotIn("交叉比较数据编号异常", record_10["gold_records"][0]["causes"])

        record_15 = next(item for item in dataset["samples"] if item["sample_id"] == "PH-A01631")
        self.assertEqual(
            ["不存在电机抱闸且SBC使能", "电机抱闸控制，B且SBC使能"],
            record_15["gold_records"][0]["causes"],
        )

        record_24 = next(item for item in dataset["samples"] if item["sample_id"] == "PH-A01006")
        self.assertIsNone(record_24["gold_records"][0]["component"])
        self.assertEqual(
            ["DRIVE-CLiQ组件", "编码器模块"],
            record_24["gold_records"][0]["related_components"],
        )


if __name__ == "__main__":
    unittest.main()
