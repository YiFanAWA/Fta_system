"""Prepare immutable human-review records after extraction."""

from extraction_contract import ExtractionResult, ExtractionStatus
from review_contract import (
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
        return not any(span.record_id == record_id for span in result.evidence_spans)

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
            if not any(span.record_id == record_id for span in result.evidence_spans):
                reasons.append("missing_evidence")

        if reasons:
            return "manual_confirmation_required:" + ",".join(reasons)
        return "automatic_review_not_required"
