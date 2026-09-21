import unittest
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from evaluate_siemens_s210_retrieval_baselines import _metrics, evaluate  # noqa: E402


class RetrievalBaselineTests(unittest.TestCase):
    def test_multi_answer_metrics_use_any_relevant_result(self):
        metrics = _metrics(["A01009", "A30502", "F30002"], {"A30502", "F30002"})
        self.assertEqual(0.0, metrics["recall_at_1"])
        self.assertEqual(1.0, metrics["recall_at_3"])
        self.assertAlmostEqual(0.5, metrics["reciprocal_rank"])

    def test_baselines_return_all_metric_keys(self):
        gold = {
            "samples": [
                {"gold_records": [
                    {"fault_code": "F01033", "description": "Reference parameter value invalid", "causes": ["reference parameter is zero"], "parameters": ["p2000"]},
                    {"fault_code": "A01006", "description": "Firmware update required", "causes": ["firmware is not suitable"], "parameters": ["p7829"]},
                ]}
            ]
        }
        benchmark = {"queries": [{"query_id": "Q1", "query": "p2000 参数为零", "query_type": "parameter", "difficulty": "easy", "ambiguity": "none", "relevant_fault_codes": ["F01033"]}]}
        report = evaluate(gold, benchmark)
        for result in report["results"].values():
            self.assertEqual({"recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "mrr"}, set(result["metrics"]))


if __name__ == "__main__":
    unittest.main()
