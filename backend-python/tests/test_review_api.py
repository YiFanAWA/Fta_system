import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import api_server  # noqa: E402
from extraction_contract import (  # noqa: E402
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from extraction_repository import InMemoryExtractionWorkflowRepository  # noqa: E402
from review_contract import FaultRecordReview, ReviewStatus  # noqa: E402


class ReviewApiTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryExtractionWorkflowRepository()
        api_server.app.state.extraction_workflow_repository = self.repository
        self.record = FaultRecord(description="pump stopped")
        self.extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
        )
        self.repository.save_extraction_with_reviews(
            self.extraction,
            (
                FaultRecordReview(
                    record_id=self.record.record_id,
                    status=ReviewStatus.PENDING,
                ),
            ),
        )

    def test_approve_endpoint_persists_an_immutable_approval(self):
        response = api_server.approve_fault_record(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="source evidence is sufficient",
            )
        )

        self.assertEqual(response["status"], "approved")
        self.assertEqual(response["record_id"], self.record.record_id)
        self.assertEqual(
            self.repository.get_current(self.record.record_id).status,
            ReviewStatus.APPROVED,
        )
        self.assertEqual(len(self.repository.history(self.record.record_id)), 2)

    def test_reject_endpoint_requires_and_persists_a_reason(self):
        response = api_server.reject_fault_record(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="the source does not support this fault",
            )
        )

        self.assertEqual(response["status"], "rejected")
        self.assertEqual(response["reason"], "the source does not support this fault")

    def test_revision_endpoint_persists_a_revision_request(self):
        response = api_server.request_fault_record_revision(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="add supporting evidence",
            )
        )

        self.assertEqual(response["status"], "revision")
        self.assertEqual(response["reviewer"], "reviewer-1")
        pending = api_server.list_pending_review_tasks()
        self.assertEqual(pending["count"], 0)

    def test_pending_query_returns_one_fault_record_review_item(self):
        response = api_server.list_pending_review_tasks()

        self.assertEqual(response["count"], 1)
        item = response["items"][0]
        self.assertEqual(item["result_id"], self.extraction.result_id)
        self.assertEqual(item["extraction_status"], "success")
        self.assertEqual(item["record"]["record_id"], self.record.record_id)
        self.assertEqual(item["review"]["status"], "pending")

    def test_approved_extraction_leaves_pending_query(self):
        api_server.approve_fault_record(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="source evidence is sufficient",
            )
        )

        response = api_server.list_pending_review_tasks()

        self.assertEqual(response, {"items": [], "count": 0})

    def test_failed_extraction_is_not_listed_as_pending_review(self):
        failed = ExtractionResult(
            status=ExtractionStatus.FAILED,
            diagnostics=(
                ExtractionDiagnostic(
                    code="provider_timeout",
                    message="model provider timed out",
                    stage="model_call",
                    retryable=True,
                ),
            ),
        )
        self.repository.save_extraction_with_reviews(failed, ())

        response = api_server.list_pending_review_tasks()

        self.assertEqual(response["count"], 1)
        self.assertEqual(response["items"][0]["result_id"], self.extraction.result_id)

    def test_reject_without_reason_returns_422_and_keeps_pending_state(self):
        with self.assertRaises(api_server.HTTPException) as context:
            api_server.reject_fault_record(
                api_server.ReviewDecisionRequest(
                    record_id=self.record.record_id,
                    reviewer="reviewer-1",
                )
            )

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(
            self.repository.get_current(self.record.record_id).status,
            ReviewStatus.PENDING,
        )

    def test_release_endpoint_blocks_pending_records(self):
        response = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(
                result_id=self.extraction.result_id,
            )
        )

        self.assertEqual(response["records"], [])
        self.assertEqual(response["blocked"][0]["record_id"], self.record.record_id)
        self.assertEqual(response["blocked"][0]["status"], "pending")

    def test_release_endpoint_returns_approved_records(self):
        api_server.approve_fault_record(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="source evidence is sufficient",
            )
        )

        response = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(
                result_id=self.extraction.result_id,
            )
        )

        self.assertEqual(response["records"][0]["record_id"], self.record.record_id)
        self.assertEqual(response["review_decisions"][0]["status"], "approved")
        self.assertEqual(response["blocked"], [])
        self.assertIsNotNone(self.repository.get_release(response["release_id"]))

    def test_not_required_release_requires_explicit_api_policy(self):
        self.repository.append(
            FaultRecordReview(
                record_id=self.record.record_id,
                status=ReviewStatus.NOT_REQUIRED,
            )
        )

        blocked = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(result_id=self.extraction.result_id)
        )
        self.assertEqual(blocked["records"], [])
        self.assertEqual(blocked["blocked"][0]["status"], "not_required")

        original_policy = api_server.ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE
        self.addCleanup(
            setattr,
            api_server,
            "ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE",
            original_policy,
        )
        api_server.ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE = True
        released = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(result_id=self.extraction.result_id)
        )

        self.assertEqual(released["records"][0]["record_id"], self.record.record_id)

    def test_build_endpoint_returns_tree_and_appends_each_retry(self):
        api_server.approve_fault_record(
            api_server.ReviewDecisionRequest(
                record_id=self.record.record_id,
                reviewer="reviewer-1",
                reason="source evidence is sufficient",
            )
        )
        release = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(result_id=self.extraction.result_id)
        )
        request = api_server.BuildReleasedExtractionRequest(
            release_id=release["release_id"],
            top_event="system failure",
        )

        first = api_server.build_released_extraction(request)
        second = api_server.build_released_extraction(request)

        self.assertEqual(first["status"], "succeeded")
        self.assertEqual(first["tree"]["top"], "system failure")
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])
        attempts = api_server.list_build_attempts(release["release_id"])
        self.assertEqual(attempts["count"], 2)

    def test_rejected_build_keeps_release_and_records_attempt(self):
        release = api_server.release_extraction(
            api_server.ReleaseExtractionRequest(result_id=self.extraction.result_id)
        )

        attempt = api_server.build_released_extraction(
            api_server.BuildReleasedExtractionRequest(
                release_id=release["release_id"],
                top_event="system failure",
            )
        )

        self.assertEqual(attempt["status"], "rejected")
        self.assertIn("没有可用于构建故障树的事件", attempt["reason"])
        self.assertIsNotNone(self.repository.get_release(release["release_id"]))
        self.assertEqual(
            api_server.list_build_attempts(release["release_id"])["count"],
            1,
        )

    def test_release_endpoint_returns_404_for_unknown_result(self):
        with self.assertRaises(api_server.HTTPException) as context:
            api_server.release_extraction(
                api_server.ReleaseExtractionRequest(result_id="missing-result")
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
