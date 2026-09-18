"""Persistence port for complete extraction results."""

from typing import Protocol

from extraction_contract import ExtractionResult
from review_contract import FaultRecordReview, ReviewableExtractionResult
from review_repository import InMemoryReviewRepository, ReviewRepository


class ExtractionRepository(Protocol):
    """Storage boundary for immutable extraction results."""

    def save(self, result: ExtractionResult) -> ExtractionResult:
        """Persist one extraction result without overwriting an existing result."""
        ...

    def get(self, result_id: str) -> ExtractionResult | None:
        """Return one persisted extraction result by its generated ID."""
        ...


class ExtractionWorkflowRepository(ExtractionRepository, ReviewRepository, Protocol):
    """Atomic persistence boundary for extraction plus initial reviews."""

    def save_extraction_with_reviews(
        self,
        result: ExtractionResult,
        reviews: tuple[FaultRecordReview, ...],
    ) -> ReviewableExtractionResult:
        """Persist both parts or expose neither as a completed workflow."""
        ...


class InMemoryExtractionRepository:
    """Process-local repository used to learn the persistence contract first."""

    def __init__(self) -> None:
        self._results: dict[str, ExtractionResult] = {}

    def save(self, result: ExtractionResult) -> ExtractionResult:
        if not isinstance(result, ExtractionResult):
            raise TypeError("result must be an ExtractionResult")
        if result.result_id in self._results:
            raise ValueError("result_id has already been stored")
        self._results[result.result_id] = result
        return result

    def get(self, result_id: str) -> ExtractionResult | None:
        if not isinstance(result_id, str) or not result_id.strip():
            raise ValueError("result_id must be a non-empty string")
        return self._results.get(result_id.strip())


class InMemoryExtractionWorkflowRepository(
    InMemoryExtractionRepository,
    InMemoryReviewRepository,
):
    """In-memory implementation of the combined workflow boundary."""

    def __init__(self) -> None:
        InMemoryExtractionRepository.__init__(self)
        InMemoryReviewRepository.__init__(self)

    def save_extraction_with_reviews(
        self,
        result: ExtractionResult,
        reviews: tuple[FaultRecordReview, ...],
    ) -> ReviewableExtractionResult:
        if not isinstance(result, ExtractionResult):
            raise TypeError("result must be an ExtractionResult")
        reviews = tuple(reviews)
        if not all(isinstance(review, FaultRecordReview) for review in reviews):
            raise TypeError("reviews must contain only FaultRecordReview values")
        if result.result_id in self._results:
            raise ValueError("result_id has already been stored")

        record_ids = {record.record_id for record in result.records}
        review_record_ids = [review.record_id for review in reviews]
        if len(review_record_ids) != len(set(review_record_ids)):
            raise ValueError("reviews must have unique record_id values")
        if set(review_record_ids) != record_ids:
            raise ValueError(
                "reviews must contain one current state for every extraction record"
            )
        if any(review.review_id in self._review_ids for review in reviews):
            raise ValueError("review_id has already been stored")
        if any(record_id in self._history_by_record for record_id in record_ids):
            raise ValueError("record_id already has review history")

        bundle = ReviewableExtractionResult(extraction=result, reviews=reviews)

        # All validation happens before these assignments. The in-memory
        # implementation therefore commits the two collections as one unit.
        self._results[result.result_id] = result
        for review in reviews:
            self._next_sequence += 1
            self._review_ids.add(review.review_id)
            self._history_by_record.setdefault(review.record_id, []).append(
                (self._next_sequence, review)
            )
        return bundle
