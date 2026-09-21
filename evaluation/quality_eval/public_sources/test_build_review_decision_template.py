import sys
import unittest


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_review_decision_template import build_template  # noqa: E402


class ReviewDecisionTemplateTests(unittest.TestCase):
    def test_only_pending_rows_are_included(self):
        result = build_template(
            {
                "dataset_info": {"name": "test"},
                "samples": [
                    {"sample_id": "A1", "review_queue": {"status": "confirmed_expert"}},
                    {"sample_id": "A2", "review_queue": {"status": "pending"}},
                ],
            }
        )
        self.assertEqual(["A2"], [item["sample_id"] for item in result["decisions"]])
        self.assertIsNone(result["decisions"][0]["decision"])


if __name__ == "__main__":
    unittest.main()
