"""Immutable, source-pinned review decisions for repeated evidence occurrences."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from contracts.extraction_contract import EvidenceField


class EvidenceLocatorTargetField(str, Enum):
    DESCRIPTION = EvidenceField.DESCRIPTION.value
    CAUSE = EvidenceField.CAUSE.value


@dataclass(frozen=True)
class EvidenceLocatorSpan:
    """An exact quoted source interval used by a locator review."""

    quote: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not isinstance(self.quote, str) or not self.quote.strip():
            raise ValueError("quote must be a non-empty string")
        if isinstance(self.start, bool) or not isinstance(self.start, int):
            raise TypeError("start must be an integer")
        if isinstance(self.end, bool) or not isinstance(self.end, int):
            raise TypeError("end must be an integer")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("span offsets must satisfy 0 <= start < end")
        if self.end - self.start != len(self.quote):
            raise ValueError("span offsets must have the same length as quote")


@dataclass(frozen=True)
class EvidenceOccurrenceLocatorReview:
    """A review of evidence location only; it does not approve semantics or Gold."""

    review_id: str
    extraction_result_id: str
    record_id: str
    source_text_sha256: str
    target_field: EvidenceLocatorTargetField
    value_index: int | None
    selected_occurrence: EvidenceLocatorSpan
    scope: EvidenceLocatorSpan
    reviewer_provenance: str
    reviewer_is_human_expert: bool
    rationale: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.review_id, "review_id"),
            (self.extraction_result_id, "extraction_result_id"),
            (self.record_id, "record_id"),
            (self.reviewer_provenance, "reviewer_provenance"),
            (self.rationale, "rationale"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if (
            not isinstance(self.source_text_sha256, str)
            or len(self.source_text_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.source_text_sha256)
        ):
            raise ValueError("source_text_sha256 must be a lowercase SHA-256 digest")

        if isinstance(self.target_field, str):
            try:
                object.__setattr__(
                    self,
                    "target_field",
                    EvidenceLocatorTargetField(self.target_field),
                )
            except ValueError as exc:
                raise ValueError(
                    f"unsupported locator target field: {self.target_field}"
                ) from exc
        elif not isinstance(self.target_field, EvidenceLocatorTargetField):
            raise TypeError("target_field must be an EvidenceLocatorTargetField")

        if self.target_field is EvidenceLocatorTargetField.CAUSE:
            if isinstance(self.value_index, bool) or not isinstance(self.value_index, int):
                raise TypeError("cause locator value_index must be an integer")
            if self.value_index < 0:
                raise ValueError("cause locator value_index must be non-negative")
        elif self.value_index is not None:
            raise ValueError("description locator value_index must be None")

        if not isinstance(self.selected_occurrence, EvidenceLocatorSpan):
            raise TypeError("selected_occurrence must be an EvidenceLocatorSpan")
        if not isinstance(self.scope, EvidenceLocatorSpan):
            raise TypeError("scope must be an EvidenceLocatorSpan")
        if (
            self.selected_occurrence.start < self.scope.start
            or self.selected_occurrence.end > self.scope.end
        ):
            raise ValueError("selected occurrence must be fully contained in scope")
        if not isinstance(self.reviewer_is_human_expert, bool):
            raise TypeError("reviewer_is_human_expert must be a boolean")

        for name in (
            "review_id",
            "extraction_result_id",
            "record_id",
            "reviewer_provenance",
            "rationale",
        ):
            object.__setattr__(self, name, getattr(self, name).strip())

    @property
    def review_status(self) -> str:
        return "locator_confirmed"

    @property
    def formal_gold(self) -> bool:
        return False

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_type": "evidence_occurrence_locator_review",
            "artifact_version": "v1",
            "review_id": self.review_id,
            "extraction_result_id": self.extraction_result_id,
            "record_id": self.record_id,
            "source_text_sha256": self.source_text_sha256,
            "target_field": self.target_field.value,
            "value_index": self.value_index,
            "selected_occurrence": {
                "quote": self.selected_occurrence.quote,
                "start": self.selected_occurrence.start,
                "end": self.selected_occurrence.end,
            },
            "scope": {
                "quote": self.scope.quote,
                "start": self.scope.start,
                "end": self.scope.end,
            },
            "review_status": self.review_status,
            "reviewer_provenance": self.reviewer_provenance,
            "reviewer_is_human_expert": self.reviewer_is_human_expert,
            "formal_gold": self.formal_gold,
            "rationale": self.rationale,
        }


__all__ = [
    "EvidenceLocatorSpan",
    "EvidenceLocatorTargetField",
    "EvidenceOccurrenceLocatorReview",
]
