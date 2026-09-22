import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from normalize_rag_boundary_expert_gold import normalize  # noqa: E402


class NormalizeBoundaryGoldTests(unittest.TestCase):
    def test_normalizes_flat_review_rows(self) -> None:
        payload = normalize(
            {
                "reviewer": "刘武",
                "reviewed_at": "2026-09-22",
                "source": "expert.json",
                "rows": [
                    {
                        "query_id": "Q1",
                        "query": "S210 F01630 是什么故障？",
                        "expert_status": "reviewed",
                        "expected_knowledge_status": "supported",
                        "answer_allowed": True,
                        "warning_required": False,
                        "need_additional_info": False,
                        "missing_information": [],
                        "expected_action": "answer",
                        "expert_reason": "明确包含 S210 和故障码。",
                        "reviewer": "刘武",
                        "reviewed_at": "2026-09-22",
                    }
                ],
            }
        )
        self.assertEqual("expert_validated", payload["dataset_info"]["status"])
        self.assertEqual("Q1", payload["rows"][0]["query_id"])
        self.assertEqual("supported", payload["rows"][0]["expert_review"]["expected_knowledge_status"])


if __name__ == "__main__":
    unittest.main()
