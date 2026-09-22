import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "evaluation" / "quality_eval" / "public_sources"))

from validate_rag_boundary_expert_gold import score_policy, validate  # noqa: E402


def _review(status: str, action: str, *, allowed: bool, warning: bool, additional: bool) -> dict:
    return {
        "expert_status": "reviewed",
        "expected_knowledge_status": status,
        "answer_allowed": allowed,
        "warning_required": warning,
        "need_additional_info": additional,
        "missing_information": ["设备型号"] if additional else [],
        "expected_action": action,
        "expert_reason": "专家依据问题身份和当前知识库边界判断。",
        "reviewer": "刘武",
        "reviewed_at": "2026-09-22",
    }


class BoundaryGoldTests(unittest.TestCase):
    def test_pending_template_is_rejected(self) -> None:
        payload = {
            "dataset_info": {"status": "pending_expert_review", "gold_source": "engineering_draft"},
            "rows": [],
        }
        self.assertTrue(validate(payload))

    def test_valid_review_requires_consistent_policy_fields(self) -> None:
        payload = {
            "dataset_info": {"status": "expert_validated", "gold_source": "named_expert_review", "reviewer": "刘武"},
            "rows": [{"query_id": "Q1", "expert_review": _review("supported", "answer", allowed=True, warning=False, additional=False)}],
        }
        self.assertEqual([], validate(payload))

    def test_inconsistent_review_is_rejected(self) -> None:
        review = _review("insufficient_evidence", "ask_information", allowed=True, warning=False, additional=True)
        payload = {
            "dataset_info": {"status": "expert_validated", "gold_source": "named_expert_review", "reviewer": "刘武"},
            "rows": [{"query_id": "Q1", "expert_review": review}],
        }
        self.assertTrue(any("insufficient_evidence" in error for error in validate(payload)))

    def test_metrics_accepts_existing_boundary_report_shape(self) -> None:
        rows = [
            {"query_id": "Q1", "expert_review": _review("insufficient_evidence", "ask_information", allowed=False, warning=False, additional=True)},
            {"query_id": "Q2", "expert_review": _review("out_of_domain", "reject", allowed=False, warning=False, additional=False)},
            {"query_id": "Q3", "expert_review": _review("supported_with_warning", "answer_with_warning", allowed=True, warning=True, additional=True)},
        ]
        payload = {
            "dataset_info": {"status": "expert_validated", "gold_source": "named_expert_review", "reviewer": "刘武"},
            "rows": rows,
        }
        actual = [
            {"query_id": "Q1", "actual_knowledge_status": "insufficient_evidence", "decision": {"answer_allowed": False, "warning_required": False}},
            {"query_id": "Q2", "actual_knowledge_status": "out_of_domain", "decision": {"answer_allowed": False, "warning_required": False}},
            {"query_id": "Q3", "actual_knowledge_status": "supported_with_warning", "decision": {"answer_allowed": True, "warning_required": True}},
        ]
        metrics = score_policy(payload, actual)
        self.assertEqual(0.0, metrics["unsafe_answer_rate"])
        self.assertEqual(0.0, metrics["false_reject_rate"])
        self.assertEqual(1.0, metrics["warning_precision"])
        self.assertEqual(1.0, metrics["warning_recall"])
        self.assertEqual(1.0, metrics["out_of_domain_precision"])


if __name__ == "__main__":
    unittest.main()
