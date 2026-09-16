"""Shared data contracts for natural-language fault extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from uuid import uuid4


def _clean_optional_text(value: str | None, *, field_name: str) -> str | None:
    """Normalize an optional text field and reject non-text values."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    value = value.strip()
    return value or None


def _clean_text_tuple(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    """Convert repeated text values to an immutable, validated tuple."""
    if isinstance(values, str):
        raise TypeError(f"{field_name} must be an iterable of strings, not a string")

    cleaned: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"every {field_name} must be a string")
        value = value.strip()
        if value:
            cleaned.append(value)
    return tuple(cleaned)


@dataclass(frozen=True)
class FaultRecord:
    """One normalized fault fact extracted from a source text."""

    description: str
    fault_code: str | None = None
    component: str | None = None
    causes: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    confidence: float | None = None
    record_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        object.__setattr__(self, "description", self.description.strip())

        object.__setattr__(
            self,
            "fault_code",
            _clean_optional_text(self.fault_code, field_name="fault_code"),
        )
        object.__setattr__(
            self,
            "component",
            _clean_optional_text(self.component, field_name="component"),
        )
        object.__setattr__(
            self,
            "causes",
            _clean_text_tuple(self.causes, field_name="causes"),
        )
        object.__setattr__(
            self,
            "parameters",
            _clean_text_tuple(self.parameters, field_name="parameters"),
        )

        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
                raise TypeError("confidence must be a number or None")
            if not 0.0 <= float(self.confidence) <= 1.0:
                raise ValueError("confidence must be between 0.0 and 1.0")
            object.__setattr__(self, "confidence", float(self.confidence))


class EvidenceField(str, Enum):
    """FaultRecord fields that may be grounded in source text."""

    FAULT_CODE = "fault_code"
    COMPONENT = "component"
    DESCRIPTION = "description"
    CAUSE = "cause"
    PARAMETER = "parameter"


@dataclass(frozen=True)
class EvidenceSpan:
    """A quoted source fragment supporting one FaultRecord field."""

    record_id: str
    field: EvidenceField
    source_id: str
    quote: str
    start: int
    end: int
    value_index: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id must be a non-empty string")

        if isinstance(self.field, str):
            try:
                normalized_field = EvidenceField(self.field)
            except ValueError as exc:
                raise ValueError(f"unsupported evidence field: {self.field}") from exc
            object.__setattr__(self, "field", normalized_field)
        elif not isinstance(self.field, EvidenceField):
            raise TypeError("field must be an EvidenceField")

        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.quote, str) or not self.quote:
            raise ValueError("quote must be a non-empty string")
        if isinstance(self.start, bool) or not isinstance(self.start, int):
            raise TypeError("start must be an integer")
        if isinstance(self.end, bool) or not isinstance(self.end, int):
            raise TypeError("end must be an integer")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("evidence offsets must satisfy 0 <= start < end")
        if self.value_index is not None:
            if isinstance(self.value_index, bool) or not isinstance(self.value_index, int):
                raise TypeError("value_index must be an integer or None")
            if self.value_index < 0:
                raise ValueError("value_index must be non-negative")

        object.__setattr__(self, "record_id", self.record_id.strip())
        object.__setattr__(self, "source_id", self.source_id.strip())

    def matches(self, source_text: str) -> bool:
        """Return whether the quote matches the declared source offsets."""
        if not isinstance(source_text, str):
            raise TypeError("source_text must be a string")
        return source_text[self.start : self.end] == self.quote


class ExtractionStatus(str, Enum):
    """The outcome of one extraction task."""

    SUCCESS = "success"
    EMPTY = "empty"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class ExtractionDiagnostic:
    """A structured problem or warning produced during extraction."""

    code: str
    message: str
    stage: str
    retryable: bool = False

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.code, "code"),
            (self.message, "message"),
            (self.stage, "stage"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a boolean")

        object.__setattr__(self, "code", self.code.strip())
        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(self, "stage", self.stage.strip())


@dataclass(frozen=True)
class ExtractionResult:
    """The complete, normalized outcome of one extraction task."""

    status: ExtractionStatus
    records: tuple[FaultRecord, ...] = ()
    evidence_spans: tuple[EvidenceSpan, ...] = ()
    diagnostics: tuple[ExtractionDiagnostic, ...] = ()
    result_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            try:
                normalized_status = ExtractionStatus(self.status)
            except ValueError as exc:
                raise ValueError(f"unsupported extraction status: {self.status}") from exc
            object.__setattr__(self, "status", normalized_status)
        elif not isinstance(self.status, ExtractionStatus):
            raise TypeError("status must be an ExtractionStatus")

        records = tuple(self.records)
        evidence_spans = tuple(self.evidence_spans)
        diagnostics = tuple(self.diagnostics)

        if not all(isinstance(record, FaultRecord) for record in records):
            raise TypeError("records must contain only FaultRecord values")
        if not all(isinstance(span, EvidenceSpan) for span in evidence_spans):
            raise TypeError("evidence_spans must contain only EvidenceSpan values")
        if not all(isinstance(item, ExtractionDiagnostic) for item in diagnostics):
            raise TypeError(
                "diagnostics must contain only ExtractionDiagnostic values"
            )

        record_ids = {record.record_id for record in records}
        if any(span.record_id not in record_ids for span in evidence_spans):
            raise ValueError("every evidence span must reference a record in this result")

        if self.status is ExtractionStatus.SUCCESS and not records:
            raise ValueError("success requires at least one fault record")
        if self.status is ExtractionStatus.EMPTY and records:
            raise ValueError("empty result cannot contain fault records")
        if self.status is ExtractionStatus.FAILED and records:
            raise ValueError("failed result cannot contain usable fault records")
        if self.status is ExtractionStatus.FAILED and not diagnostics:
            raise ValueError("failed result requires diagnostics")
        if self.status is ExtractionStatus.PARTIAL and not records:
            raise ValueError("partial result requires at least one fault record")
        if self.status is ExtractionStatus.PARTIAL and not diagnostics:
            raise ValueError("partial result requires diagnostics")

        object.__setattr__(self, "records", records)
        object.__setattr__(self, "evidence_spans", evidence_spans)
        object.__setattr__(self, "diagnostics", diagnostics)
