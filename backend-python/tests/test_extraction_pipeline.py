import json
import sys
import unittest
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from contracts.extraction_contract import (  # noqa: E402
    EvidenceField,
    EvidenceSpan,
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from contracts.build_contract import BuildAttemptStatus  # noqa: E402
from extraction.extraction_application_service import ExtractionApplicationService  # noqa: E402
from extraction.extraction_repository import (  # noqa: E402
    InMemoryExtractionRepository,
    InMemoryExtractionWorkflowRepository,
)
from extraction.fault_extractor import RemoteLLMFaultExtractor  # noqa: E402
from extraction.fault_tree_build_service import FaultTreeBuildService  # noqa: E402
from fta.fta_generator import build_fault_tree  # noqa: E402
from core.model_client import (  # noqa: E402
    CallableModelClient,
    ModelClientError,
    RetryingModelClient,
)
from contracts.review_contract import (  # noqa: E402
    FaultRecordReview,
    ReviewStatus,
    ReviewableExtractionResult,
)
from extraction.review_decision_service import ReviewDecisionService  # noqa: E402
from extraction.review_preparation_service import ReviewPreparationService  # noqa: E402
from extraction.review_repository import InMemoryReviewRepository  # noqa: E402
from contracts.release_contract import ReleasedExtractionResult  # noqa: E402
from extraction.release_service import FaultRecordReleaseService  # noqa: E402
from extraction.sqlite_extraction_repository import SQLiteExtractionWorkflowRepository  # noqa: E402
from extraction.text_extraction_adapter import TextExtractionAdapter  # noqa: E402


class ExtractionContractTests(unittest.TestCase):
    def test_fault_record_allows_missing_code_and_empty_repeated_fields(self):
        record = FaultRecord(description="pump stopped")

        self.assertIsNone(record.fault_code)
        self.assertEqual(record.causes, ())
        self.assertEqual(record.parameters, ())
        with self.assertRaises((AttributeError, TypeError)):
            record.description = "changed"

    def test_failed_result_requires_diagnostics(self):
        with self.assertRaises(ValueError):
            ExtractionResult(status=ExtractionStatus.FAILED)

    def test_result_can_be_serialized_without_mutating_the_contract(self):
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(FaultRecord(description="pump stopped"),),
        )

        encoded = json.dumps(asdict(result))

        self.assertIn('"status": "success"', encoded)
        self.assertIn('"description": "pump stopped"', encoded)

    def test_evidence_span_matches_its_source_offsets(self):
        span = EvidenceSpan(
            record_id="record-1",
            field=EvidenceField.DESCRIPTION,
            source_id="manual-1",
            quote="pump stopped",
            start=0,
            end=12,
        )

        self.assertTrue(span.matches("pump stopped in bay A"))


class ExtractionRepositoryTests(unittest.TestCase):
    def test_save_and_get_preserve_the_complete_extraction_result(self):
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(FaultRecord(description="pump stopped"),),
        )
        repository = InMemoryExtractionRepository()

        saved = repository.save(result)

        self.assertIs(saved, result)
        self.assertIs(repository.get(result.result_id), result)

    def test_duplicate_result_id_cannot_overwrite_an_existing_result(self):
        result = ExtractionResult(
            status=ExtractionStatus.EMPTY,
        )
        repository = InMemoryExtractionRepository()
        repository.save(result)

        with self.assertRaises(ValueError):
            repository.save(result)

    def test_missing_result_returns_none(self):
        repository = InMemoryExtractionRepository()

        self.assertIsNone(repository.get("missing-result"))

    def test_workflow_repository_commits_result_and_initial_reviews_together(self):
        record = FaultRecord(description="pump stopped")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        review = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.PENDING,
        )
        repository = InMemoryExtractionWorkflowRepository()

        bundle = repository.save_extraction_with_reviews(result, (review,))

        self.assertIs(repository.get(result.result_id), result)
        self.assertIs(repository.get_current(record.record_id), review)
        self.assertIs(bundle.extraction, result)

    def test_workflow_repository_rejects_mismatched_reviews_before_writing(self):
        record = FaultRecord(description="pump stopped")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        orphan_review = FaultRecordReview(
            record_id="other-record",
            status=ReviewStatus.PENDING,
        )
        repository = InMemoryExtractionWorkflowRepository()

        with self.assertRaises(ValueError):
            repository.save_extraction_with_reviews(result, (orphan_review,))

        self.assertIsNone(repository.get(result.result_id))
        self.assertIsNone(repository.get_current(record.record_id))

    def test_workflow_repository_lists_pending_records_not_entire_tasks(self):
        repository = InMemoryExtractionWorkflowRepository()
        pending_record = FaultRecord(description="pump stopped")
        approved_record = FaultRecord(description="valve blocked")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(pending_record, approved_record),
        )
        pending = FaultRecordReview(
            record_id=pending_record.record_id,
            status=ReviewStatus.PENDING,
        )
        initially_pending = FaultRecordReview(
            record_id=approved_record.record_id,
            status=ReviewStatus.PENDING,
        )

        repository.save_extraction_with_reviews(result, (pending, initially_pending))
        approved = FaultRecordReview(
            record_id=approved_record.record_id,
            status=ReviewStatus.APPROVED,
            reviewer="reviewer-1",
        )
        repository.append(approved)

        listed = repository.list_pending_review_items()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].result_id, result.result_id)
        self.assertIs(listed[0].record, pending_record)
        self.assertIs(listed[0].review, pending)

    def test_workflow_repository_excludes_revision_from_pending_record_list(self):
        repository = InMemoryExtractionWorkflowRepository()
        record = FaultRecord(description="pump stopped")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        revision = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.REVISION,
            reviewer="reviewer-1",
            reason="add supporting evidence",
        )

        repository.save_extraction_with_reviews(result, (revision,))

        self.assertEqual(repository.list_pending_review_items(), ())


class SQLiteExtractionRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database_path = Path(self.temp_dir.name) / "workflow.sqlite3"
        self.repository = SQLiteExtractionWorkflowRepository(self.database_path)

    def test_reopened_repository_preserves_extraction_and_review_history(self):
        record = FaultRecord(
            description="pump stopped",
            component="pump",
            related_components=("pump", "motor"),
            causes=("motor overheated",),
            confidence=0.72,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="source-1",
                    quote="pump stopped",
                    start=0,
                    end=12,
                ),
            ),
        )
        pending = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.PENDING,
        )

        self.repository.save_extraction_with_reviews(result, (pending,))
        reopened = SQLiteExtractionWorkflowRepository(self.database_path)

        loaded = reopened.get(result.result_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.result_id, result.result_id)
        self.assertEqual(loaded.records[0].record_id, record.record_id)
        self.assertEqual(loaded.records[0].related_components, ("motor",))
        self.assertEqual(loaded.records[0].causes, ("motor overheated",))
        self.assertEqual(loaded.evidence_spans[0].quote, "pump stopped")
        self.assertEqual(reopened.get_current(record.record_id).status, ReviewStatus.PENDING)
        self.assertEqual(len(reopened.list_pending_review_items()), 1)

        approved = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.APPROVED,
            reviewer="reviewer-1",
        )
        reopened.append(approved)

        self.assertEqual(
            [review.status for review in reopened.history(record.record_id)],
            [ReviewStatus.PENDING, ReviewStatus.APPROVED],
        )
        self.assertEqual(reopened.list_pending_review_items(), ())

    def test_schema_version_and_backup_preserve_the_database_contract(self):
        record = FaultRecord(description="pump stopped")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        pending = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.PENDING,
        )
        self.repository.save_extraction_with_reviews(result, (pending,))

        self.assertEqual(self.repository.schema_version, 4)
        backup_path = Path(self.temp_dir.name) / "backup.sqlite3"
        self.repository.backup_to(backup_path)

        backup_repository = SQLiteExtractionWorkflowRepository(backup_path)
        self.assertEqual(backup_repository.schema_version, 4)
        self.assertIsNotNone(backup_repository.get(result.result_id))
        self.assertEqual(len(backup_repository.list_pending_review_items()), 1)

        with self.assertRaises(FileExistsError):
            self.repository.backup_to(backup_path)

    def test_mismatched_initial_reviews_roll_back_the_sqlite_transaction(self):
        record = FaultRecord(description="pump stopped")
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        orphan_review = FaultRecordReview(
            record_id="other-record",
            status=ReviewStatus.PENDING,
        )

        with self.assertRaises(ValueError):
            self.repository.save_extraction_with_reviews(result, (orphan_review,))

        self.assertIsNone(self.repository.get(result.result_id))
        self.assertIsNone(self.repository.get_current(record.record_id))

    def test_release_and_build_attempts_survive_repository_reopen(self):
        record = FaultRecord(
            description="pump stopped",
            causes=("motor overheated",),
            confidence=0.72,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        pending = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.PENDING,
        )
        self.repository.save_extraction_with_reviews(result, (pending,))
        approved = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.APPROVED,
            reviewer="reviewer-1",
        )
        self.repository.append(approved)

        prepared = ReviewableExtractionResult(
            extraction=result,
            reviews=(approved,),
        )
        release = FaultRecordReleaseService(self.repository).release(prepared)
        self.repository.save_release(release)
        attempt = FaultTreeBuildService(self.repository, build_fault_tree).build(
            release,
            "system failure",
        )

        reopened = SQLiteExtractionWorkflowRepository(self.database_path)
        loaded_release = reopened.get_release(release.release_id)
        self.assertIsNotNone(loaded_release)
        self.assertEqual(loaded_release.records[0].record_id, record.record_id)
        loaded_attempts = reopened.list_build_attempts(release.release_id)
        self.assertEqual(len(loaded_attempts), 1)
        self.assertEqual(loaded_attempts[0].attempt_id, attempt.attempt_id)
        self.assertEqual(loaded_attempts[0].status, BuildAttemptStatus.SUCCEEDED)


class ExtractionApplicationServiceTests(unittest.TestCase):
    class StubExtractor:
        def __init__(self, result: ExtractionResult) -> None:
            self.result = result
            self.received_text = None

        def extract(self, text: str) -> ExtractionResult:
            self.received_text = text
            return self.result

    def test_extract_persists_result_and_initial_pending_review(self):
        record = FaultRecord(description="pump stopped")
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
        )
        extractor = self.StubExtractor(extraction)
        repository = InMemoryExtractionWorkflowRepository()

        bundle = ExtractionApplicationService(extractor, repository).extract(
            "pump stopped in bay A"
        )

        self.assertEqual(extractor.received_text, "pump stopped in bay A")
        self.assertIs(bundle.extraction, extraction)
        self.assertEqual(bundle.reviews[0].status, ReviewStatus.PENDING)
        self.assertIs(repository.get(extraction.result_id), extraction)

    def test_failed_extraction_is_persisted_without_creating_review(self):
        extraction = ExtractionResult(
            status=ExtractionStatus.FAILED,
            diagnostics=(
                ExtractionDiagnostic(
                    code="provider_timeout",
                    message="provider did not respond",
                    stage="provider",
                    retryable=True,
                ),
            ),
        )
        repository = InMemoryExtractionWorkflowRepository()

        bundle = ExtractionApplicationService(
            self.StubExtractor(extraction),
            repository,
        ).extract("source text")

        self.assertEqual(bundle.extraction.status, ExtractionStatus.FAILED)
        self.assertEqual(bundle.reviews, ())
        self.assertIs(repository.get(extraction.result_id), extraction)

    def test_blank_text_is_rejected_before_extractor_call(self):
        extractor = self.StubExtractor(ExtractionResult(status=ExtractionStatus.EMPTY))
        repository = InMemoryExtractionWorkflowRepository()

        with self.assertRaises(ValueError):
            ExtractionApplicationService(extractor, repository).extract("   ")

        self.assertIsNone(extractor.received_text)


class FaultExtractorTests(unittest.TestCase):
    def _extractor(self, response: str) -> RemoteLLMFaultExtractor:
        return RemoteLLMFaultExtractor(
            CallableModelClient(lambda prompt: response),
            lambda text: f"extract: {text}",
        )

    def test_invalid_json_is_failed(self):
        result = self._extractor("not-json").extract("source")

        self.assertEqual(result.status, ExtractionStatus.FAILED)
        self.assertEqual(result.diagnostics[0].code, "invalid_json")

    def test_mixed_records_are_partial(self):
        response = (
            '{"items":[{"description":"pump stopped"},'
            '{"description":null}]}'
        )
        result = self._extractor(response).extract("source")

        self.assertEqual(result.status, ExtractionStatus.PARTIAL)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.diagnostics[0].code, "invalid_record")


class TextExtractionAdapterTests(unittest.TestCase):
    def test_model_failure_is_not_masked_by_fallback(self):
        def failing(prompt: str) -> str:
            raise ModelClientError(
                "provider_auth_failed",
                "invalid credentials",
                retryable=False,
            )

        adapter = TextExtractionAdapter(
            CallableModelClient(failing),
            lambda text, index, total: text,
            fallback_builder=lambda text: [
                {"description": "fallback record"},
            ],
        )
        result = adapter.extract("source text")

        self.assertEqual(result.status, ExtractionStatus.FAILED)
        self.assertEqual(result.diagnostics[0].code, "provider_auth_failed")
        self.assertEqual(len(result.records), 0)

    def test_fallback_records_are_partial(self):
        adapter = TextExtractionAdapter(
            CallableModelClient(lambda prompt: '{"items":[]}'),
            lambda text, index, total: text,
            fallback_builder=lambda text: [
                {"description": "fallback record"},
            ],
        )

        result = adapter.extract("source text")

        self.assertEqual(result.status, ExtractionStatus.PARTIAL)
        self.assertEqual(result.diagnostics[0].code, "fallback_used")
        self.assertEqual(len(result.records), 1)

    def test_model_records_skip_fallback_instead_of_appending_duplicates(self):
        fallback_calls = []

        def fallback(text):
            fallback_calls.append(text)
            return [{"description": "fallback duplicate"}]

        adapter = TextExtractionAdapter(
            CallableModelClient(
                lambda prompt: '{"items":[{"fault_code":"F01003",'
                '"description":"access delay","causes":[],"parameters":[]}]}'
            ),
            lambda text, index, total: text,
            fallback_builder=fallback,
        )

        result = adapter.extract("fault text")

        self.assertEqual(result.status, ExtractionStatus.SUCCESS)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(fallback_calls, [])
        fallback_report = adapter.last_chunk_reports[-1]
        self.assertEqual(fallback_report["source"], "fallback")
        self.assertEqual(fallback_report["status"], "skipped")
        self.assertEqual(fallback_report["skip_reason"], "model_records_present")

    def test_successful_model_record_is_normalized(self):
        response = (
            '{"items":[{"fault_code":null,"description":"pump stopped",'
            '"causes":[],"parameters":[],"confidence":0.8}]}'
        )
        adapter = TextExtractionAdapter(
            CallableModelClient(lambda prompt: response),
            lambda text, index, total: text,
        )
        result = adapter.extract("source text")

        self.assertEqual(result.status, ExtractionStatus.SUCCESS)
        self.assertIsNone(result.records[0].fault_code)
        self.assertEqual(result.records[0].causes, ())

    def test_chunk_overlap_only_removes_exact_duplicates(self):
        response = '{"items":[{"description":"same fault"}]}'
        adapter = TextExtractionAdapter(
            CallableModelClient(lambda prompt: response),
            lambda text, index, total: text,
            chunk_size_chars=5,
            overlap_chars=1,
        )

        result = adapter.extract("abcdefghij")

        self.assertEqual(result.status, ExtractionStatus.SUCCESS)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(len(adapter.last_chunk_reports), 3)


class RetryingModelClientTests(unittest.TestCase):
    def test_retryable_error_has_bounded_retries(self):
        calls = []

        def failing(prompt: str) -> str:
            calls.append(prompt)
            raise ModelClientError("timeout", "temporary timeout", retryable=True)

        client = RetryingModelClient(
            CallableModelClient(failing),
            max_retries=2,
            delay_seconds=0,
            sleep_fn=lambda seconds: None,
        )

        with self.assertRaises(ModelClientError):
            client.complete("prompt")
        self.assertEqual(len(calls), 3)


class ReviewContractTests(unittest.TestCase):
    def test_pending_review_has_no_reviewer_and_is_immutable(self):
        review = FaultRecordReview(
            record_id="record-1",
            status=ReviewStatus.PENDING,
            reason="fallback was used",
        )

        self.assertEqual(review.status, ReviewStatus.PENDING)
        self.assertIsNone(review.reviewer)
        self.assertEqual(review.created_at.tzinfo, timezone.utc)
        with self.assertRaises((AttributeError, TypeError)):
            review.status = ReviewStatus.APPROVED

    def test_approved_review_requires_reviewer(self):
        with self.assertRaises(ValueError):
            FaultRecordReview(
                record_id="record-1",
                status=ReviewStatus.APPROVED,
                created_at=datetime.now(timezone.utc),
            )

    def test_rejected_review_keeps_reason_and_reviewer(self):
        review = FaultRecordReview(
            record_id="record-1",
            status=ReviewStatus.REJECTED,
            reason="description is not supported by source text",
            reviewer="reviewer-1",
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(review.reviewer, "reviewer-1")
        self.assertIn("not supported", review.reason)


class ReviewPreparationServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ReviewPreparationService()

    def test_success_creates_pending_review_for_each_record(self):
        records = (
            FaultRecord(description="first fault"),
            FaultRecord(description="second fault"),
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=records,
        )

        reviews = self.service.prepare(result)

        self.assertEqual(len(reviews), 2)
        self.assertEqual(
            {review.record_id for review in reviews},
            {record.record_id for record in records},
        )
        self.assertTrue(all(review.status is ReviewStatus.PENDING for review in reviews))

    def test_partial_review_reason_contains_diagnostic_codes(self):
        result = ExtractionResult(
            status=ExtractionStatus.PARTIAL,
            records=(FaultRecord(description="fault"),),
            diagnostics=(
                ExtractionDiagnostic(
                    code="fallback_used",
                    message="manual review required",
                    stage="fallback",
                ),
            ),
        )

        reviews = self.service.prepare(result)

        self.assertEqual(len(reviews), 1)
        self.assertIn("fallback_used", reviews[0].reason)

    def test_high_confidence_record_with_evidence_is_not_required(self):
        record = FaultRecord(
            description="pump stopped",
            confidence=0.95,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="manual-1",
                    quote="pump stopped",
                    start=0,
                    end=12,
                ),
            ),
        )

        reviews = ReviewPreparationService(confidence_threshold=0.8).prepare(result)

        self.assertEqual(reviews[0].status, ReviewStatus.NOT_REQUIRED)
        self.assertEqual(reviews[0].reason, "automatic_review_not_required")

    def test_populated_field_without_evidence_remains_pending(self):
        record = FaultRecord(
            description="pump stopped",
            causes=("overheat",),
            confidence=0.95,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="manual-1",
                    quote="pump stopped",
                    start=0,
                    end=12,
                ),
            ),
        )

        review = self.service.prepare(result)[0]

        self.assertEqual(review.status, ReviewStatus.PENDING)
        self.assertIn("missing_reason_evidence", review.reason)

    def test_empty_primary_component_with_related_components_needs_declaration(self):
        record = FaultRecord(
            description="pump stopped",
            related_components=("motor",),
            confidence=0.95,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="manual-1",
                    quote="pump stopped",
                    start=0,
                    end=12,
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.RELATED_COMPONENT,
                    source_id="manual-1",
                    quote="motor",
                    start=20,
                    end=25,
                    value_index=0,
                ),
            ),
        )

        review = self.service.prepare(result)[0]

        self.assertEqual(review.status, ReviewStatus.PENDING)
        self.assertIn("missing_evidence:component_declaration", review.reason)

    def test_component_absence_is_supported_by_declaration_evidence(self):
        record = FaultRecord(
            description="pump stopped",
            related_components=("motor",),
            confidence=0.95,
        )
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="manual-1",
                    quote="pump stopped",
                    start=0,
                    end=12,
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.RELATED_COMPONENT,
                    source_id="manual-1",
                    quote="motor",
                    start=20,
                    end=25,
                    value_index=0,
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.COMPONENT_DECLARATION,
                    source_id="manual-1",
                    quote="component none",
                    start=13,
                    end=27,
                ),
            ),
        )

        review = self.service.prepare(result)[0]

        self.assertEqual(review.status, ReviewStatus.NOT_REQUIRED)

    def test_empty_or_failed_result_creates_no_reviews(self):
        empty_result = ExtractionResult(status=ExtractionStatus.EMPTY)
        failed_result = ExtractionResult(
            status=ExtractionStatus.FAILED,
            diagnostics=(
                ExtractionDiagnostic(
                    code="provider_failed",
                    message="provider unavailable",
                    stage="provider",
                ),
            ),
        )

        self.assertEqual(self.service.prepare(empty_result), ())
        self.assertEqual(self.service.prepare(failed_result), ())

    def test_prepare_result_keeps_extraction_and_current_reviews_together(self):
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(FaultRecord(description="fault"),),
        )

        bundle = self.service.prepare_result(result)

        self.assertIsInstance(bundle, ReviewableExtractionResult)
        self.assertIs(bundle.extraction, result)
        self.assertEqual(len(bundle.reviews), 1)
        self.assertEqual(bundle.reviews[0].record_id, result.records[0].record_id)

    def test_reviewable_result_rejects_orphan_review(self):
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(FaultRecord(description="fault"),),
        )
        orphan = FaultRecordReview(
            record_id="not-in-result",
            status=ReviewStatus.PENDING,
        )

        with self.assertRaises(ValueError):
            ReviewableExtractionResult(extraction=result, reviews=(orphan,))


class ReviewRepositoryTests(unittest.TestCase):
    def test_latest_review_is_current_but_history_is_preserved(self):
        repository = InMemoryReviewRepository()
        created_at = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
        pending = FaultRecordReview(
            record_id="record-1",
            status=ReviewStatus.PENDING,
            created_at=created_at,
        )
        approved = FaultRecordReview(
            record_id="record-1",
            status=ReviewStatus.APPROVED,
            reviewer="reviewer-1",
            created_at=created_at,
        )

        repository.append(pending)
        repository.append(approved)

        self.assertIs(repository.get_current("record-1"), approved)
        self.assertEqual(repository.history("record-1"), (pending, approved))
        self.assertEqual(repository.list_pending(), ())

    def test_revision_is_kept_out_of_pending_work(self):
        repository = InMemoryReviewRepository()
        revision = FaultRecordReview(
            record_id="record-2",
            status=ReviewStatus.REVISION,
            reason="add supporting evidence",
            reviewer="reviewer-1",
        )

        repository.append(revision)

        self.assertEqual(repository.list_pending(), ())

    def test_same_review_cannot_be_appended_twice(self):
        repository = InMemoryReviewRepository()
        review = FaultRecordReview(
            record_id="record-1",
            status=ReviewStatus.PENDING,
        )
        repository.append(review)

        with self.assertRaises(ValueError):
            repository.append(review)


class ReviewDecisionServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryReviewRepository()
        self.repository.append(
            FaultRecordReview(
                record_id="record-1",
                status=ReviewStatus.PENDING,
            )
        )
        self.service = ReviewDecisionService(self.repository)

    def test_approve_appends_new_decision(self):
        decision = self.service.approve(
            record_id="record-1",
            reviewer="reviewer-1",
            reason="source evidence is sufficient",
        )

        self.assertEqual(decision.status, ReviewStatus.APPROVED)
        self.assertIs(self.repository.get_current("record-1"), decision)
        self.assertEqual(len(self.repository.history("record-1")), 2)

    def test_reject_requires_a_reason(self):
        with self.assertRaises(ValueError):
            self.service.reject("record-1", "reviewer-1", "")

        self.assertEqual(self.repository.history("record-1")[0].status, ReviewStatus.PENDING)

    def test_decision_requires_existing_review_history(self):
        with self.assertRaises(ValueError):
            self.service.approve("missing-record", "reviewer-1")


class FaultRecordReleaseServiceTests(unittest.TestCase):
    def _result_with_records(self, *records: FaultRecord) -> ExtractionResult:
        return ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=records,
        )

    def test_only_approved_records_are_released(self):
        first = FaultRecord(description="first fault")
        second = FaultRecord(description="second fault")
        extraction = self._result_with_records(first, second)
        prepared = ReviewPreparationService().prepare_result(extraction)
        repository = InMemoryReviewRepository()
        repository.append(
            FaultRecordReview(
                record_id=first.record_id,
                status=ReviewStatus.APPROVED,
                reviewer="reviewer-1",
            )
        )
        repository.append(
            FaultRecordReview(
                record_id=second.record_id,
                status=ReviewStatus.PENDING,
            )
        )

        released = FaultRecordReleaseService(repository).release(prepared)

        self.assertEqual(released.records, (first,))
        self.assertEqual(released.review_decisions[0].status, ReviewStatus.APPROVED)
        self.assertEqual(len(released.blocked), 1)
        self.assertEqual(released.blocked[0].record_id, second.record_id)

    def test_latest_persisted_decision_overrides_preparation_snapshot(self):
        record = FaultRecord(description="pump stopped")
        extraction = self._result_with_records(record)
        prepared = ReviewPreparationService().prepare_result(extraction)
        repository = InMemoryReviewRepository()
        repository.append(prepared.reviews[0])
        approved = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.APPROVED,
            reviewer="reviewer-1",
        )
        repository.append(approved)

        released = FaultRecordReleaseService(repository).release(prepared)

        self.assertEqual(released.records, (record,))
        self.assertEqual(released.review_decisions, (approved,))
        self.assertEqual(released.blocked, ())

    def test_pending_revision_and_rejected_records_are_blocked(self):
        statuses = (
            (ReviewStatus.PENDING, None),
            (ReviewStatus.REVISION, "add evidence"),
            (ReviewStatus.REJECTED, "unsupported"),
        )
        records = tuple(
            FaultRecord(description=f"fault-{index}")
            for index, _ in enumerate(statuses)
        )
        extraction = self._result_with_records(*records)
        reviews = tuple(
            FaultRecordReview(
                record_id=record.record_id,
                status=status,
                reason=reason,
                reviewer=(None if status is ReviewStatus.PENDING else "reviewer-1"),
            )
            for record, (status, reason) in zip(records, statuses)
        )
        prepared = ReviewableExtractionResult(extraction=extraction, reviews=reviews)
        repository = InMemoryReviewRepository()
        for review in reviews:
            repository.append(review)

        released = FaultRecordReleaseService(repository).release(prepared)

        self.assertEqual(released.records, ())
        self.assertEqual(
            {item.status for item in released.blocked},
            {ReviewStatus.PENDING, ReviewStatus.REVISION, ReviewStatus.REJECTED},
        )

    def test_not_required_needs_an_explicit_release_policy(self):
        record = FaultRecord(description="verified fault")
        extraction = self._result_with_records(record)
        review = FaultRecordReview(
            record_id=record.record_id,
            status=ReviewStatus.NOT_REQUIRED,
        )
        prepared = ReviewableExtractionResult(
            extraction=extraction,
            reviews=(review,),
        )
        repository = InMemoryReviewRepository()
        repository.append(review)

        blocked = FaultRecordReleaseService(repository).release(prepared)
        released = FaultRecordReleaseService(
            repository,
            allowed_statuses=(ReviewStatus.APPROVED, ReviewStatus.NOT_REQUIRED),
        ).release(prepared)

        self.assertEqual(blocked.records, ())
        self.assertEqual(released.records, (record,))


class FaultTreeBuildServiceTests(unittest.TestCase):
    def _release(self, *records: FaultRecord) -> ReleasedExtractionResult:
        decisions = tuple(
            FaultRecordReview(
                record_id=record.record_id,
                status=ReviewStatus.APPROVED,
                reviewer="reviewer-1",
            )
            for record in records
        )
        return ReleasedExtractionResult(
            source_result_id="result-1",
            records=tuple(records),
            review_decisions=decisions,
        )

    def test_successful_build_appends_a_succeeded_attempt(self):
        repository = InMemoryExtractionWorkflowRepository()
        record = FaultRecord(
            description="pump stopped",
            causes=("motor overheated",),
        )
        release = self._release(record)
        repository.save_release(release)

        attempt = FaultTreeBuildService(repository, build_fault_tree).build(
            release,
            "system failure",
        )

        self.assertEqual(attempt.status, BuildAttemptStatus.SUCCEEDED)
        self.assertEqual(attempt.tree["top"], "system failure")
        self.assertEqual(
            attempt.tree["children"][0]["source_record_ids"],
            [record.record_id],
        )
        self.assertEqual(
            attempt.tree["children"][0]["children"][0]["name"],
            "motor overheated",
        )
        self.assertEqual(repository.list_build_attempts(release.release_id), (attempt,))

    def test_duplicate_fault_descriptions_keep_all_source_record_ids(self):
        repository = InMemoryExtractionWorkflowRepository()
        first = FaultRecord(description="pump stopped")
        second = FaultRecord(description="pump stopped")
        release = self._release(first, second)
        repository.save_release(release)

        attempt = FaultTreeBuildService(repository, build_fault_tree).build(
            release,
            "system failure",
        )

        self.assertEqual(attempt.status, BuildAttemptStatus.SUCCEEDED)
        self.assertEqual(len(attempt.tree["children"]), 1)
        self.assertEqual(
            set(attempt.tree["children"][0]["source_record_ids"]),
            {first.record_id, second.record_id},
        )

    def test_builder_and_record_mapper_are_independently_injectable(self):
        repository = InMemoryExtractionWorkflowRepository()
        record = FaultRecord(description="pump stopped")
        release = self._release(record)
        repository.save_release(release)
        mapped_record_ids = []

        def mapper(value):
            mapped_record_ids.append(value.record_id)
            return {
                "name": "mapped pump event",
                "source_record_ids": [value.record_id],
                "causes": [],
            }

        def builder(top_event, failures):
            return build_fault_tree(top_event, failures)

        attempt = FaultTreeBuildService(
            repository,
            builder=builder,
            mapper=mapper,
        ).build(release, "system failure")

        self.assertEqual(attempt.status, BuildAttemptStatus.SUCCEEDED)
        self.assertEqual(mapped_record_ids, [record.record_id])
        self.assertEqual(
            attempt.tree["children"][0]["name"],
            "mapped pump event",
        )

    def test_failed_build_preserves_release_and_appends_each_retry(self):
        repository = InMemoryExtractionWorkflowRepository()
        empty_release = self._release()
        repository.save_release(empty_release)

        first = FaultTreeBuildService(repository, build_fault_tree).build(
            empty_release,
            "system failure",
        )
        second = FaultTreeBuildService(repository, build_fault_tree).build(
            empty_release,
            "system failure",
        )

        self.assertEqual(first.status, BuildAttemptStatus.REJECTED)
        self.assertIn("没有可用于构建故障树的事件", first.reason)
        self.assertEqual(second.status, BuildAttemptStatus.REJECTED)
        self.assertNotEqual(first.attempt_id, second.attempt_id)
        self.assertIs(repository.get_release(empty_release.release_id), empty_release)
        self.assertEqual(
            repository.list_build_attempts(empty_release.release_id),
            (first, second),
        )

    def test_unexpected_builder_failure_is_also_recorded_as_retryable(self):
        repository = InMemoryExtractionWorkflowRepository()
        release = self._release(FaultRecord(description="pump stopped"))
        repository.save_release(release)

        def fail_unexpectedly(top_event, failures):
            raise RuntimeError("builder unavailable")

        attempt = FaultTreeBuildService(repository, builder=fail_unexpectedly).build(
            release,
            "system failure",
        )

        self.assertEqual(attempt.status, BuildAttemptStatus.REJECTED)
        self.assertEqual(attempt.reason, "builder unavailable")
        self.assertTrue(attempt.retryable)
        self.assertEqual(repository.list_build_attempts(release.release_id), (attempt,))

    def test_invalid_builder_output_is_rejected_and_recorded(self):
        repository = InMemoryExtractionWorkflowRepository()
        release = self._release(FaultRecord(description="pump stopped"))
        repository.save_release(release)

        def return_invalid_tree(top_event, failures):
            return {"top": top_event, "children": []}

        attempt = FaultTreeBuildService(
            repository,
            builder=return_invalid_tree,
        ).build(release, "system failure")

        self.assertEqual(attempt.status, BuildAttemptStatus.REJECTED)
        self.assertEqual(attempt.reason, "tree.children必须是非空列表")
        self.assertFalse(attempt.retryable)
        self.assertEqual(repository.list_build_attempts(release.release_id), (attempt,))


if __name__ == "__main__":
    unittest.main()
