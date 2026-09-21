"""Prepare immutable human-review records after extraction."""

from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from contracts.review_contract import (
    FaultRecordReview,
    ReviewStatus,
    ReviewableExtractionResult,
)


class ReviewPreparationService:
    """Translate extraction quality into per-record review states."""

    def __init__(self, confidence_threshold: float = 0.8) -> None:
        if isinstance(confidence_threshold, bool) or not isinstance(
            confidence_threshold,
            (int, float),
        ):
            raise TypeError("confidence_threshold must be a number")
        if not 0.0 <= float(confidence_threshold) <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        self._confidence_threshold = float(confidence_threshold)

    def prepare(
        self,
        result: ExtractionResult,
    ) -> tuple[FaultRecordReview, ...]:
        if not isinstance(result, ExtractionResult):
            raise TypeError("result must be an ExtractionResult")

        if result.status in {
            ExtractionStatus.EMPTY,
            ExtractionStatus.FAILED,
        }:
            return ()

        return tuple(
            FaultRecordReview(
                record_id=record.record_id,
                status=(
                    ReviewStatus.PENDING
                    if self._needs_review(result, record.record_id, record.confidence)
                    else ReviewStatus.NOT_REQUIRED
                ),
                reason=self._review_reason(
                    result,
                    record.record_id,
                    record.confidence,
                ),
            )
            for record in result.records
        )

    def prepare_result(
        self,
        result: ExtractionResult,
    ) -> ReviewableExtractionResult:
        """Return the extraction result together with its current review state."""
        return ReviewableExtractionResult(
            extraction=result,
            reviews=self.prepare(result),
        )

    def _needs_review(
        self,
        result: ExtractionResult,
        record_id: str,
        confidence: float | None,
    ) -> bool:
        if result.status is ExtractionStatus.PARTIAL:
            return True
        if confidence is None or confidence < self._confidence_threshold:
            return True
        return bool(self._missing_evidence_fields(result, record_id))

    def _review_reason(
        self,
        result: ExtractionResult,
        record_id: str,
        confidence: float | None,
    ) -> str:
        reasons: list[str] = []
        if result.status is ExtractionStatus.PARTIAL:
            reasons.append("extraction_partial")
            reasons.extend(
                sorted({diagnostic.code for diagnostic in result.diagnostics})
            )
        else:
            if confidence is None:
                reasons.append("missing_confidence")
            elif confidence < self._confidence_threshold:
                reasons.append("low_confidence")
            missing_fields = self._missing_evidence_fields(result, record_id)
            if missing_fields:
                generic_fields = tuple(
                    field for field in missing_fields if field != "causes"
                )
                if generic_fields:
                    reasons.append("missing_evidence:" + ",".join(generic_fields))
                if "causes" in missing_fields:
                    reasons.append("missing_reason_evidence")

        if reasons:
            return "manual_confirmation_required:" + ",".join(reasons)
        return "automatic_review_not_required"

    @classmethod
    def _missing_evidence_fields(
        cls,
        result: ExtractionResult,
        record_id: str,
    ) -> tuple[str, ...]:
        """Return populated record fields that have no supporting source span.

        Empty optional fields do not require evidence.  An empty primary
        component does require a declaration span when related components are
        present, because that absence is itself a source-backed conclusion.
        """
        record = next(
            (item for item in result.records if item.record_id == record_id),
            None,
        )
        if record is None:
            return ("record",)

        spans = tuple(
            span for span in result.evidence_spans if span.record_id == record_id
        )
        missing: list[str] = []

        if not cls._has_scalar_evidence(spans, EvidenceField.DESCRIPTION):
            missing.append("description")
        if record.fault_code and not cls._has_scalar_evidence(
            spans,
            EvidenceField.FAULT_CODE,
        ):
            missing.append("fault_code")
        if record.component and not cls._has_scalar_evidence(
            spans,
            EvidenceField.PRIMARY_COMPONENT,
            EvidenceField.COMPONENT,
        ):
            missing.append("component")
        if record.related_components and not cls._has_indexed_evidence(
            spans,
            EvidenceField.RELATED_COMPONENT,
            len(record.related_components),
        ):
            missing.append("related_components")
        if record.causes and not cls._has_indexed_evidence(
            spans,
            EvidenceField.CAUSE,
            len(record.causes),
        ):
            missing.append("causes")
        if record.parameters and not cls._has_indexed_evidence(
            spans,
            EvidenceField.PARAMETER,
            len(record.parameters),
        ):
            missing.append("parameters")

        if (
            record.component is None
            and record.related_components
            and not cls._has_scalar_evidence(
                spans,
                EvidenceField.COMPONENT_DECLARATION,
                EvidenceField.DRIVER_OBJECT_DECLARATION,
            )
        ):
            missing.append("component_declaration")

        return tuple(missing)

    @staticmethod
    def _has_scalar_evidence(
        spans: tuple[EvidenceSpan, ...],
        *fields: EvidenceField,
    ) -> bool:
        return any(span.field in fields for span in spans)

    @staticmethod
    def _has_indexed_evidence(
        spans: tuple[EvidenceSpan, ...],
        field: EvidenceField,
        value_count: int,
    ) -> bool:
        indexed = {
            span.value_index
            for span in spans
            if span.field is field and span.value_index is not None
        }
        return all(index in indexed for index in range(value_count))
