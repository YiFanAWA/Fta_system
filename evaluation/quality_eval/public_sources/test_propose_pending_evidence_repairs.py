import sys
import unittest


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from propose_pending_evidence_repairs import propose_repairs  # noqa: E402


class PendingEvidenceProposalTests(unittest.TestCase):
    def test_exact_cause_match_is_only_a_proposal(self):
        report = propose_repairs(
            {
                "dataset_info": {"name": "test"},
                "samples": [
                    {
                        "sample_id": "A1",
                        "input_text": "A1 Fault\nCause: cause one\nRemedy: fix",
                        "review_queue": {"status": "pending"},
                        "model_prediction": {
                            "records": [
                                {
                                    "fault_code": "A1",
                                    "description": "Fault",
                                    "causes": ["cause one"],
                                }
                            ]
                        },
                        "evidence_spans": [],
                    }
                ],
            }
        )
        self.assertEqual(1, report["proposal_count"])
        self.assertEqual("exact_source_match_needs_expert_acceptance", report["proposals"][0]["proposal_status"])
        self.assertIn("不改变审核结论", report["decision"])


if __name__ == "__main__":
    unittest.main()
