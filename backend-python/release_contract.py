"""Contracts for releasing reviewed fault records to downstream FTA work."""

from dataclasses import dataclass, field
from uuid import uuid4

from extraction_contract import FaultRecord
from review_contract import FaultRecordReview, ReviewStatus


@dataclass(frozen=True)
class ReleaseBlock:
    """Explain why one extracted record was not released downstream."""

    record_id: str
    status: ReviewStatus | None
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        object.__setattr__(self, "record_id", self.record_id.strip())

        if self.status is not None:
            if isinstance(self.status, str):
                try:
                    object.__setattr__(self, "status", ReviewStatus(self.status))
                except ValueError as exc:
                    raise ValueError(f"unsupported review status: {self.status}") from exc
            elif not isinstance(self.status, ReviewStatus):
                raise TypeError("status must be a ReviewStatus or None")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        object.__setattr__(self, "reason", self.reason.strip())


@dataclass(frozen=True)
class ReleasedExtractionResult:
    """The safe projection that downstream FTA tree building may consume.

    Records that fail the release policy are represented only by ``blocked``
    metadata. Their ``FaultRecord`` payloads are intentionally absent here.
    """

    source_result_id: str
    records: tuple[FaultRecord, ...] = ()
    review_decisions: tuple[FaultRecordReview, ...] = ()
    blocked: tuple[ReleaseBlock, ...] = ()
    release_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.source_result_id, str) or not self.source_result_id.strip():
            raise ValueError("source_result_id must be a non-empty string")
        object.__setattr__(self, "source_result_id", self.source_result_id.strip())

        records = tuple(self.records)
        decisions = tuple(self.review_decisions)
        blocked = tuple(self.blocked)
        if not all(isinstance(record, FaultRecord) for record in records):
            raise TypeError("records must contain only FaultRecord values")
        if not all(
            isinstance(decision, FaultRecordReview) for decision in decisions
        ):
            raise TypeError(
                "review_decisions must contain only FaultRecordReview values"
            )
        if not all(isinstance(item, ReleaseBlock) for item in blocked):
            raise TypeError("blocked must contain only ReleaseBlock values")

        record_ids = [record.record_id for record in records]
        decision_ids = [decision.record_id for decision in decisions]
        blocked_ids = [item.record_id for item in blocked]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("released records must have unique record_id values")
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("review_decisions must have unique record_id values")
        if len(blocked_ids) != len(set(blocked_ids)):
            raise ValueError("blocked records must have unique record_id values")
        if set(decision_ids) != set(record_ids):
            raise ValueError(
                "review_decisions must describe every released record exactly once"
            )
        if set(record_ids) & set(blocked_ids):
            raise ValueError("a record cannot be both released and blocked")

        object.__setattr__(self, "records", records)
        object.__setattr__(self, "review_decisions", decisions)
        object.__setattr__(self, "blocked", blocked)
