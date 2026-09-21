"""Application service for human review decisions."""

from contracts.review_contract import FaultRecordReview, ReviewStatus
from extraction.review_repository import ReviewRepository


class ReviewDecisionService:
    """Create immutable decisions and persist them through a repository."""

    def __init__(self, repository: ReviewRepository) -> None:
        self._repository = repository

    def approve(
        self,
        record_id: str,
        reviewer: str,
        reason: str | None = None,
    ) -> FaultRecordReview:
        return self._decide(
            record_id=record_id,
            status=ReviewStatus.APPROVED,
            reviewer=reviewer,
            reason=reason,
        )

    def reject(
        self,
        record_id: str,
        reviewer: str,
        reason: str,
    ) -> FaultRecordReview:
        return self._decide(
            record_id=record_id,
            status=ReviewStatus.REJECTED,
            reviewer=reviewer,
            reason=reason,
        )

    def request_revision(
        self,
        record_id: str,
        reviewer: str,
        reason: str,
    ) -> FaultRecordReview:
        return self._decide(
            record_id=record_id,
            status=ReviewStatus.REVISION,
            reviewer=reviewer,
            reason=reason,
        )

    def _decide(
        self,
        *,
        record_id: str,
        status: ReviewStatus,
        reviewer: str,
        reason: str | None,
    ) -> FaultRecordReview:
        current = self._repository.get_current(record_id)
        if current is None:
            raise ValueError(f"no review history exists for record_id: {record_id}")

        decision = FaultRecordReview(
            record_id=record_id,
            status=status,
            reason=reason,
            reviewer=reviewer,
        )
        return self._repository.append(decision)
