import sys
import unittest


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from finalize_public_review_decisions import finalize_queue  # noqa: E402


class FinalizePublicReviewDecisionTests(unittest.TestCase):
    def _queue(self):
        return {
            "dataset_info": {"name": "test", "import_ready": False},
            "samples": [
                {
                    "sample_id": "A1",
                    "review_queue": {"status": "pending"},
                    "model_prediction": {"records": [{"fault_code": "A1"}]},
                    "evidence_spans": [],
                    "review_history": [],
                }
            ],
        }

    def test_explicit_approval_creates_gold_and_history(self):
        result = finalize_queue(
            self._queue(),
            {
                "decisions": [
                    {
                        "sample_id": "A1",
                        "decision": "审核通过",
                        "reviewer_name": "专家A",
                        "review_date": "2026-09-20",
                        "opinion": "字段和证据一致",
                    }
                ]
            },
        )
        row = result["samples"][0]
        self.assertEqual("confirmed_expert", row["review_queue"]["status"])
        self.assertEqual("A1", row["gold_records"][0]["fault_code"])
        self.assertEqual(1, len(row["review_history"]))
        self.assertTrue(result["dataset_info"]["import_ready"])

    def test_pending_without_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            finalize_queue(self._queue(), {"decisions": []})

    def test_non_approval_keeps_import_blocked(self):
        result = finalize_queue(
            self._queue(),
            {
                "decisions": [
                    {
                        "sample_id": "A1",
                        "decision": "证据不足",
                        "reviewer_name": "专家A",
                        "opinion": "缺少候选原因证据",
                    }
                ]
            },
        )
        self.assertEqual("needs_resolution", result["samples"][0]["review_queue"]["status"])
        self.assertFalse(result["dataset_info"]["import_ready"])


if __name__ == "__main__":
    unittest.main()
