import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import api_server  # noqa: E402
from extraction_contract import ExtractionResult, ExtractionStatus, FaultRecord  # noqa: E402
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

    def test_release_endpoint_returns_404_for_unknown_result(self):
        with self.assertRaises(api_server.HTTPException) as context:
            api_server.release_extraction(
                api_server.ReleaseExtractionRequest(result_id="missing-result")
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
