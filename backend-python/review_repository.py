"""Repository port and in-memory implementation for review history."""

from typing import Protocol

from review_contract import FaultRecordReview, ReviewStatus


class ReviewRepository(Protocol):
    """Persistence boundary for immutable fault-record review decisions."""

    def append(self, review: FaultRecordReview) -> FaultRecordReview:
        """Persist one new review decision without modifying old decisions."""
        ...

    def get_current(self, record_id: str) -> FaultRecordReview | None:
        """Return the latest review decision for one record."""
        ...

    def history(self, record_id: str) -> tuple[FaultRecordReview, ...]:
        """Return all review decisions for one record in insertion order."""
        ...

    def list_pending(self) -> tuple[FaultRecordReview, ...]:
        """Return current records whose ordinary review state is pending."""
        ...


class InMemoryReviewRepository:
    """Small deterministic repository used before a real database adapter."""

    def __init__(self) -> None:
        self._history_by_record: dict[str, list[tuple[int, FaultRecordReview]]] = {}
        self._review_ids: set[str] = set()
        self._next_sequence = 0

    def append(self, review: FaultRecordReview) -> FaultRecordReview:
        if not isinstance(review, FaultRecordReview):
            raise TypeError("review must be a FaultRecordReview")
        if review.review_id in self._review_ids:
            raise ValueError("review_id has already been stored")

        self._next_sequence += 1
        self._review_ids.add(review.review_id)
        self._history_by_record.setdefault(review.record_id, []).append(
            (self._next_sequence, review)
        )
        return review

    def get_current(self, record_id: str) -> FaultRecordReview | None:
        self._validate_record_id(record_id)
        entries = self._history_by_record.get(record_id, [])
        if not entries:
            return None
        return max(entries, key=lambda entry: (entry[1].created_at, entry[0]))[1]

    def history(self, record_id: str) -> tuple[FaultRecordReview, ...]:
        self._validate_record_id(record_id)
        entries = self._history_by_record.get(record_id, [])
        return tuple(review for _, review in entries)

    def list_pending(self) -> tuple[FaultRecordReview, ...]:
        pending: list[tuple[int, FaultRecordReview]] = []
        for entries in self._history_by_record.values():
            if not entries:
                continue
            sequence, review = max(
                entries,
                key=lambda entry: (entry[1].created_at, entry[0]),
            )
            if review.status is ReviewStatus.PENDING:
                pending.append((sequence, review))

        pending.sort(key=lambda entry: entry[0])
        return tuple(review for _, review in pending)

    @staticmethod
    def _validate_record_id(record_id: str) -> None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")
