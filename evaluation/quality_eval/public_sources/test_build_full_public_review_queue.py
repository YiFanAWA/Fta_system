import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_full_public_review_queue import build_full_review_queue  # noqa: E402


class FullPublicReviewQueueTests(unittest.TestCase):
    def test_pending_candidates_are_not_gold_or_import_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            corpus_path = Path(directory) / "corpus.jsonl"
            corpus_path.write_text(
                "\n".join(
                    json.dumps({"sample_id": sample_id, "input_text": f"{sample_id} text"})
                    for sample_id in ("A1", "A2")
                ),
                encoding="utf-8",
            )
            corpus = {"path": str(corpus_path)}
            confirmed = {
                "samples": [
                    {
                        "sample_id": "A1",
                        "gold_records": [{"fault_code": "A1"}],
                        "evidence_spans": [{"field": "fault_code", "start": 0, "end": 2}],
                        "expert_review": {
                            "decision": "审核通过",
                            "correction_applied": False,
                        },
                    }
                ]
            }
            candidate = {
                "samples": [
                    {
                        "sample_id": "A2",
                        "model_prediction": {
                            "status": "success",
                            "records": [{"fault_code": "A2"}],
                            "evidence_spans": [{"field": "fault_code", "start": 0, "end": 2}],
                        },
                        "review_queue": {
                            "evidence_audit": {"status": "valid", "span_count": 1}
                        },
                    }
                ]
            }

            result = build_full_review_queue(
                corpus,
                confirmed,
                [("v2", candidate)],
                expected_confirmed_count=1,
            )
            self.assertEqual(2, result["dataset_info"]["source_records"])
            self.assertEqual(1, result["dataset_info"]["confirmed_expert_records"])
            self.assertEqual(1, result["dataset_info"]["pending_review_records"])
            pending = next(row for row in result["samples"] if row["sample_id"] == "A2")
            self.assertEqual("pending", pending["review_queue"]["status"])
            self.assertEqual([], pending["gold_records"])
            self.assertFalse(result["dataset_info"]["import_ready"])

    def test_evidence_insufficient_expert_result_is_not_confirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            corpus_path = Path(directory) / "corpus.jsonl"
            corpus_path.write_text(
                json.dumps({"sample_id": "A1", "input_text": "A1 text"}),
                encoding="utf-8",
            )
            result = build_full_review_queue(
                {"path": str(corpus_path)},
                {
                    "samples": [
                        {
                            "sample_id": "A1",
                            "gold_records": [{"fault_code": "A1"}],
                            "expert_review": {
                                "decision": "证据不足",
                                "opinion": "补充原文证据",
                            },
                        }
                    ]
                },
                [],
                expected_confirmed_count=1,
            )
            self.assertEqual("needs_resolution", result["samples"][0]["review_queue"]["status"])
            self.assertEqual(1, result["dataset_info"]["needs_resolution_records"])
            self.assertEqual(0, result["dataset_info"]["confirmed_expert_records"])


if __name__ == "__main__":
    unittest.main()
