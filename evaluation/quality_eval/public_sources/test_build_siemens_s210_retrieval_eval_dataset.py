import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_siemens_s210_retrieval_eval_dataset import build  # noqa: E402


class RetrievalEvaluationDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
        cls.dataset = build(json.loads(path.read_text(encoding="utf-8")))

    def test_has_stratified_queries_and_multiple_answer_cases(self):
        info = self.dataset["dataset_info"]
        self.assertEqual(42, info["query_count"])
        self.assertGreaterEqual(len(info["query_types"]), 7)
        self.assertTrue(any(len(item["relevant_fault_codes"]) > 1 for item in self.dataset["queries"]))

    def test_labels_exist_in_frozen_gold(self):
        codes = {
            record["fault_code"]
            for sample in json.loads(
                (ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json").read_text(encoding="utf-8")
            )["samples"]
            for record in sample["gold_records"]
        }
        for query in self.dataset["queries"]:
            self.assertTrue(set(query["relevant_fault_codes"]).issubset(codes), query["query_id"])

    def test_ambiguity_policy_is_explicit(self):
        for query in self.dataset["queries"]:
            self.assertEqual("any_relevant_in_top_k", query["relevance_policy"])
            self.assertIn(query["ambiguity"], {"none", "ambiguous_description", "insufficient_query_context"})


if __name__ == "__main__":
    unittest.main()
