"""Orchestrate raw-text extraction and retryable candidate FTA proposals."""

from __future__ import annotations

from hashlib import sha256

from contracts.candidate_fta_contract import (
    CandidateFtaGenerationResult,
    CandidateFtaOutcomeDiagnostic,
    CandidateFtaOutcomeStatus,
    CandidateFtaRecordOutcome,
    CandidateFtaStatus,
)
from contracts.extraction_contract import ExtractionResult
from contracts.evidence_locator_review_contract import EvidenceOccurrenceLocatorReview
from core.model_client import ModelClientError
from extraction.fault_extractor import FaultExtractor
from fta.candidate_fta_extraction_service import (
    CandidateFtaExtractionService,
    CandidateFtaValidationError,
)


class CandidateFtaApplicationService:
    """Run extraction once, then independently propose/retry per-record trees.

    The complete extraction result is always returned with the outcomes. A
    failed model proposal therefore does not discard the extracted records or
    their evidence, and callers can retry selected record IDs without calling
    the upstream extractor again.
    """

    def __init__(
        self,
        extractor: FaultExtractor,
        candidate_service: CandidateFtaExtractionService,
    ) -> None:
        if not hasattr(extractor, "extract"):
            raise TypeError("extractor must implement extract(text)")
        if not hasattr(candidate_service, "propose"):
            raise TypeError(
                "candidate_service must implement propose(extraction, record_id, source_text, locator_reviews=...)"
            )
        self._extractor = extractor
        self._candidate_service = candidate_service

    def generate(self, source_text: str) -> CandidateFtaGenerationResult:
        """Extract facts from original text and propose a candidate per record."""
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must be a non-empty string")
        extraction = self._extractor.extract(source_text)
        if not isinstance(extraction, ExtractionResult):
            raise TypeError("extractor must return an ExtractionResult")
        return self.propose_from_extraction(extraction, source_text)

    def retry_records(
        self,
        previous_result: CandidateFtaGenerationResult,
        source_text: str,
        record_ids: tuple[str, ...] | list[str],
        locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> CandidateFtaGenerationResult:
        """Retry only selected candidate proposals using retained extraction."""
        if not isinstance(previous_result, CandidateFtaGenerationResult):
            raise TypeError("previous_result must be a CandidateFtaGenerationResult")
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must be a non-empty string")
        if sha256(source_text.encode("utf-8")).hexdigest() != previous_result.source_text_sha256:
            raise ValueError("source_text does not match the retained extraction source")
        if isinstance(record_ids, str) or not isinstance(record_ids, (tuple, list)):
            raise TypeError("record_ids must be a list or tuple of strings")
        if not record_ids or not all(isinstance(item, str) and item.strip() for item in record_ids):
            raise ValueError("record_ids must contain non-empty strings")
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("record_ids must not contain duplicates")
        extraction = previous_result.extraction
        known_ids = {record.record_id for record in extraction.records}
        unknown_ids = set(record_ids) - known_ids
        if unknown_ids:
            raise ValueError("record_ids include records absent from the retained extraction")
        previous_outcome_ids = {outcome.record_id for outcome in previous_result.outcomes}
        if previous_outcome_ids != known_ids:
            raise ValueError("previous_result must contain one outcome for each extracted record")
        return self._propose(
            extraction,
            source_text,
            tuple(record_ids),
            previous_outcomes=previous_result.outcomes,
            locator_reviews=locator_reviews,
        )

    def propose_from_extraction(
        self,
        extraction: ExtractionResult,
        source_text: str,
        locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> CandidateFtaGenerationResult:
        """Skip extraction and propose from a retained result, useful for retries."""
        if not isinstance(extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must be a non-empty string")
        return self._propose(
            extraction,
            source_text,
            tuple(record.record_id for record in extraction.records),
            locator_reviews=locator_reviews,
        )

    def _propose(
        self,
        extraction: ExtractionResult,
        source_text: str,
        record_ids: tuple[str, ...],
        *,
        previous_outcomes: tuple[CandidateFtaRecordOutcome, ...] = (),
        locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> CandidateFtaGenerationResult:
        if isinstance(locator_reviews, (str, bytes)) or not isinstance(
            locator_reviews, tuple
        ):
            raise TypeError("locator_reviews must be a tuple")
        records = {record.record_id: record for record in extraction.records}
        outcomes = {item.record_id: item for item in previous_outcomes}
        selected_record_ids = set(record_ids)
        for review in locator_reviews:
            if not isinstance(review, EvidenceOccurrenceLocatorReview):
                raise TypeError(
                    "locator_reviews must contain EvidenceOccurrenceLocatorReview values"
                )
            if review.record_id not in records:
                raise ValueError("locator review references a record absent from extraction")
            if review.record_id not in selected_record_ids:
                raise ValueError("locator review references a record not selected for this proposal")
        for record_id in record_ids:
            record = records[record_id]
            try:
                tree = self._candidate_service.propose(
                    extraction,
                    record_id,
                    source_text,
                    locator_reviews=tuple(
                        review
                        for review in locator_reviews
                        if review.record_id == record_id
                    ),
                )
            except ModelClientError as exc:
                outcomes[record_id] = CandidateFtaRecordOutcome(
                    record_id=record_id,
                    fault_code=record.fault_code,
                    status=CandidateFtaOutcomeStatus.FAILED,
                    diagnostics=(
                        CandidateFtaOutcomeDiagnostic(
                            code=exc.code,
                            message=exc.message,
                            stage="gate_proposal_provider",
                            retryable=exc.retryable,
                        ),
                    ),
                )
                continue
            except CandidateFtaValidationError as exc:
                outcomes[record_id] = CandidateFtaRecordOutcome(
                    record_id=record_id,
                    fault_code=record.fault_code,
                    status=CandidateFtaOutcomeStatus.FAILED,
                    diagnostics=(
                        CandidateFtaOutcomeDiagnostic(
                            code="invalid_gate_proposal",
                            message=str(exc),
                            stage="gate_proposal_validation",
                            retryable=True,
                        ),
                    ),
                )
                continue
            except ValueError as exc:
                outcomes[record_id] = CandidateFtaRecordOutcome(
                    record_id=record_id,
                    fault_code=record.fault_code,
                    status=CandidateFtaOutcomeStatus.FAILED,
                    diagnostics=(
                        CandidateFtaOutcomeDiagnostic(
                            code="candidate_fta_contract_invalid",
                            message=str(exc),
                            stage="candidate_fta_contract_validation",
                            retryable=True,
                        ),
                    ),
                )
                continue
            if tree.status is CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW:
                status = CandidateFtaOutcomeStatus.PROPOSED
            else:
                status = CandidateFtaOutcomeStatus.BLOCKED
            outcomes[record_id] = CandidateFtaRecordOutcome(
                record_id=record_id,
                fault_code=record.fault_code,
                status=status,
                tree=tree,
            )

        return CandidateFtaGenerationResult.for_source(
            extraction,
            source_text,
            tuple(
                outcomes[record.record_id]
                for record in extraction.records
                if record.record_id in outcomes
            ),
        )


__all__ = ["CandidateFtaApplicationService"]
