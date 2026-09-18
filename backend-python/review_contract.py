"""Immutable contracts for human review of extracted fault records."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from extraction_contract import (
    EvidenceSpan,
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)


class ReviewStatus(str, Enum):
    """The review state of one extracted fault record."""

    PENDING = "pending"
    NOT_REQUIRED = "not_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION = "revision"


@dataclass(frozen=True)
class FaultRecordReview:
    """One immutable review decision associated with a FaultRecord.

    A new instance is created for every review action. The latest decision is
    a separate read-model concern; older decisions remain available for audit.
    """

    record_id: str
    status: ReviewStatus
    reason: str | None = None
    reviewer: str | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    review_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        object.__setattr__(self, "record_id", self.record_id.strip())

        if isinstance(self.status, str):
            try:
                normalized_status = ReviewStatus(self.status)
            except ValueError as exc:
                raise ValueError(f"unsupported review status: {self.status}") from exc
            object.__setattr__(self, "status", normalized_status)
        elif not isinstance(self.status, ReviewStatus):
            raise TypeError("status must be a ReviewStatus")

        for value, field_name in (
            (self.reason, "reason"),
            (self.reviewer, "reviewer"),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string or None")
            if isinstance(value, str):
                object.__setattr__(self, field_name, value.strip() or None)

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(timezone.utc),
        )

        if self.status in {ReviewStatus.PENDING, ReviewStatus.NOT_REQUIRED}:
            if self.reviewer is not None:
                raise ValueError("automated review state cannot have a reviewer")
            return

        if self.reviewer is None:
            raise ValueError("completed review must have a reviewer")
        if self.status in {ReviewStatus.REJECTED, ReviewStatus.REVISION}:
            if self.reason is None:
                raise ValueError("rejected or revision review must have a reason")


@dataclass(frozen=True)
class ReviewableExtractionResult:
    """An extraction result paired with one current review state per record."""

    extraction: ExtractionResult
    reviews: tuple[FaultRecordReview, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")

        reviews = tuple(self.reviews)
        if not all(isinstance(review, FaultRecordReview) for review in reviews):
            raise TypeError("reviews must contain only FaultRecordReview values")

        record_ids = {record.record_id for record in self.extraction.records}
        review_record_ids = [review.record_id for review in reviews]
        if len(review_record_ids) != len(set(review_record_ids)):
            raise ValueError("reviews must contain at most one current state per record")
        if set(review_record_ids) != record_ids:
            raise ValueError(
                "reviews must contain one current state for every extraction record"
            )

        object.__setattr__(self, "reviews", reviews)


@dataclass(frozen=True)
class PendingReviewItem:
    """One fault record currently waiting for human review."""

    result_id: str
    extraction_status: ExtractionStatus
    diagnostics: tuple[ExtractionDiagnostic, ...]
    record: FaultRecord
    evidence_spans: tuple[EvidenceSpan, ...]
    review: FaultRecordReview

    def __post_init__(self) -> None:
        if not isinstance(self.result_id, str) or not self.result_id.strip():
            raise ValueError("result_id must be a non-empty string")
        object.__setattr__(self, "result_id", self.result_id.strip())

        if isinstance(self.extraction_status, str):
            try:
                normalized_status = ExtractionStatus(self.extraction_status)
            except ValueError as exc:
                raise ValueError(
                    f"unsupported extraction status: {self.extraction_status}"
                ) from exc
            object.__setattr__(self, "extraction_status", normalized_status)
        elif not isinstance(self.extraction_status, ExtractionStatus):
            raise TypeError("extraction_status must be an ExtractionStatus")

        diagnostics = tuple(self.diagnostics)
        if not all(
            isinstance(diagnostic, ExtractionDiagnostic)
            for diagnostic in diagnostics
        ):
            raise TypeError(
                "diagnostics must contain only ExtractionDiagnostic values"
            )
        object.__setattr__(self, "diagnostics", diagnostics)

        if not isinstance(self.record, FaultRecord):
            raise TypeError("record must be a FaultRecord")

        evidence_spans = tuple(self.evidence_spans)
        if not all(isinstance(span, EvidenceSpan) for span in evidence_spans):
            raise TypeError("evidence_spans must contain only EvidenceSpan values")
        if any(span.record_id != self.record.record_id for span in evidence_spans):
            raise ValueError("evidence spans must reference the pending record")
        object.__setattr__(self, "evidence_spans", evidence_spans)

        if not isinstance(self.review, FaultRecordReview):
            raise TypeError("review must be a FaultRecordReview")
        if self.review.record_id != self.record.record_id:
            raise ValueError("review must reference the pending record")
        if self.review.status is not ReviewStatus.PENDING:
            raise ValueError("pending review item must have a pending review")
