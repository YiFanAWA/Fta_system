import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_prediction_review_candidate import build_candidate_dataset  # noqa: E402


class PredictionReviewCandidateTests(unittest.TestCase):
    def test_prediction_and_literal_evidence_remain_pending(self):
        sample = {
            "dataset_info": {"name": "sample"},
            "samples": [{"sample_id": "A1", "input_text": "A1 fault text"}],
        }
        prediction = {
            "predictions": [
                {
                    "sample_id": "A1",
                    "status": "success",
                    "latency_ms": 10,
                    "prediction": {
                        "extracted_faults": {
                            "records": [{"fault_code": "A1", "description": "fault text"}],
                            "evidence_spans": [
                                {
                                    "field": "fault_code",
                                    "quote": "A1",
                                    "start": 0,
                                    "end": 2,
                                }
                            ],
                        }
                    },
                }
            ]
        }

        result = build_candidate_dataset(
            sample,
            prediction,
            prediction_run_name="test-run",
        )

        item = result["samples"][0]
        self.assertEqual("model_prediction_pending_expert_review", result["dataset_info"]["label_status"])
        self.assertEqual("pending", item["review_queue"]["status"])
        self.assertEqual("valid", item["review_queue"]["evidence_audit"]["status"])
        self.assertIsNone(item["review_queue"]["decision"])
        self.assertEqual("test-run", result["dataset_info"]["prediction_run"])


if __name__ == "__main__":
    unittest.main()
