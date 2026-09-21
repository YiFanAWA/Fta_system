import sys
import unittest


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from audit_pending_review_queue import audit_pending_dataset  # noqa: E402


class PendingReviewQueueAuditTests(unittest.TestCase):
    def test_missing_indexed_cause_evidence_is_reported_without_approval(self):
        dataset = {
            "dataset_info": {"name": "test"},
            "samples": [
                {
                    "sample_id": "A1",
                    "review_queue": {"status": "pending"},
                    "model_prediction": {
                        "records": [
                            {
                                "fault_code": "A1",
                                "component": "",
                                "related_components": [],
                                "description": "Fault",
                                "causes": ["cause one"],
                                "parameters": [],
                            }
                        ]
                    },
                    "evidence_spans": [
                        {"field": "fault_code", "quote": "A1", "value_index": None},
                        {"field": "description", "quote": "Fault", "value_index": None},
                    ],
                }
            ],
        }
        report = audit_pending_dataset(dataset)
        self.assertEqual(1, report["pending_records"])
        self.assertEqual(1, report["rows_with_findings"])
        self.assertIn("missing_cause_evidence", report["finding_counts"])
        self.assertEqual("结构审计不等于语义审核；不得据此自动批准", report["decision"])


if __name__ == "__main__":
    unittest.main()
