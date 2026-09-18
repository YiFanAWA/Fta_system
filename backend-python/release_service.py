"""Release gate between human review and downstream FTA tree building."""

from typing import Iterable

from release_contract import ReleaseBlock, ReleasedExtractionResult
from review_contract import ReviewStatus, ReviewableExtractionResult
from review_repository import ReviewRepository


class FaultRecordReleaseService:
    """Release only records whose current review state is explicitly allowed.

    The default policy is deliberately conservative: only a human
    ``approved`` decision is released. Automatic acceptance can be enabled
    later by passing ``ReviewStatus.NOT_REQUIRED`` explicitly.
    """

    def __init__(
        self,
        repository: ReviewRepository,
        allowed_statuses: Iterable[ReviewStatus] = (ReviewStatus.APPROVED,),
    ) -> None:
        self._repository = repository
        normalized_statuses: set[ReviewStatus] = set()
        for status in allowed_statuses:
            if isinstance(status, str):
                try:
                    status = ReviewStatus(status)
                except ValueError as exc:
                    raise ValueError(f"unsupported release status: {status}") from exc
            if not isinstance(status, ReviewStatus):
                raise TypeError("allowed_statuses must contain ReviewStatus values")
            normalized_statuses.add(status)
        if not normalized_statuses:
            raise ValueError("allowed_statuses cannot be empty")
        self._allowed_statuses = frozenset(normalized_statuses)

    def release(
        self,
        result: ReviewableExtractionResult,
    ) -> ReleasedExtractionResult:
        """Create a downstream-safe projection without mutating source data."""
        if not isinstance(result, ReviewableExtractionResult):
            raise TypeError("result must be a ReviewableExtractionResult")

        snapshot_reviews = {review.record_id: review for review in result.reviews}
        released_records = []
        released_decisions = []
        blocked = []

        for record in result.extraction.records:
            # A persisted human decision wins over the preparation snapshot.
            current = self._repository.get_current(record.record_id)
            review = current or snapshot_reviews.get(record.record_id)
            if review is None:
                blocked.append(
                    ReleaseBlock(
                        record_id=record.record_id,
                        status=None,
                        reason="missing_review",
                    )
                )
                continue

            if review.status not in self._allowed_statuses:
                blocked.append(
                    ReleaseBlock(
                        record_id=record.record_id,
                        status=review.status,
                        reason=f"review_status_not_allowed:{review.status.value}",
                    )
                )
                continue

            released_records.append(record)
            released_decisions.append(review)

        return ReleasedExtractionResult(
            source_result_id=result.extraction.result_id,
            records=tuple(released_records),
            review_decisions=tuple(released_decisions),
            blocked=tuple(blocked),
        )
