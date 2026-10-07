"""Validate explicit occurrence reviews before binding repeated source evidence."""

from __future__ import annotations

from hashlib import sha256

from contracts.evidence_locator_review_contract import (
    EvidenceLocatorTargetField,
    EvidenceOccurrenceLocatorReview,
)
from contracts.extraction_contract import EvidenceField, EvidenceSpan, ExtractionResult


class EvidenceLocatorReviewValidationError(ValueError):
    """A supplied locator review does not match the current extraction/source."""


class EvidenceLocatorReviewResolver:
    """Resolve only review-selected spans; never choose an occurrence automatically."""

    def __init__(
        self,
        extraction: ExtractionResult,
        record_id: str,
        source_text: str,
        reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> None:
        if not isinstance(extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        if not isinstance(source_text, str) or not source_text:
            raise ValueError("source_text must be a non-empty string")
        if isinstance(reviews, (str, bytes)) or not isinstance(reviews, tuple):
            raise TypeError("reviews must be a tuple of EvidenceOccurrenceLocatorReview")

        if not any(record.record_id == record_id for record in extraction.records):
            raise ValueError("record_id is not present in the extraction result")
        source_digest = sha256(source_text.encode("utf-8")).hexdigest()
        indexed: dict[tuple[EvidenceLocatorTargetField, int | None], EvidenceSpan] = {}

        for review in reviews:
            if not isinstance(review, EvidenceOccurrenceLocatorReview):
                raise TypeError(
                    "reviews must contain EvidenceOccurrenceLocatorReview values"
                )
            if review.extraction_result_id != extraction.result_id:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} belongs to a different extraction"
                )
            if review.record_id != record_id:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} belongs to a different record"
                )
            if review.source_text_sha256 != source_digest:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} belongs to different source text"
                )
            if review.selected_occurrence.end > len(source_text) or review.scope.end > len(source_text):
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} has offsets outside the source"
                )
            if source_text[review.scope.start : review.scope.end] != review.scope.quote:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} scope quote does not match source offsets"
                )
            if (
                source_text[
                    review.selected_occurrence.start : review.selected_occurrence.end
                ]
                != review.selected_occurrence.quote
            ):
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} selected quote does not match source offsets"
                )
            occurrences = self._occurrences(
                source_text,
                review.selected_occurrence.quote,
                review.scope.start,
                review.scope.end,
            )
            if occurrences != [
                (review.selected_occurrence.start, review.selected_occurrence.end)
            ]:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} does not select a unique occurrence within its scope"
                )

            evidence_field = EvidenceField(review.target_field.value)
            evidence_spans = [
                span
                for span in extraction.evidence_spans
                if span.record_id == record_id
                and span.field is evidence_field
                and span.value_index == review.value_index
                and span.source_id == "input_text"
                and span.matches(source_text)
            ]
            selected_spans = [
                span
                for span in evidence_spans
                if span.start >= review.selected_occurrence.start
                and span.end <= review.selected_occurrence.end
            ]
            if len(selected_spans) != 1:
                raise EvidenceLocatorReviewValidationError(
                    f"locator review {review.review_id} must contain exactly one matching extraction evidence span"
                )

            key = (review.target_field, review.value_index)
            if key in indexed:
                raise EvidenceLocatorReviewValidationError(
                    f"multiple locator reviews target {review.target_field.value}:{review.value_index}"
                )
            indexed[key] = selected_spans[0]

        self._indexed = indexed
        self._source_text = source_text
        self._reviews = {
            (review.target_field, review.value_index): review for review in reviews
        }

    def review_for(
        self, field: EvidenceLocatorTargetField, value_index: int | None
    ) -> EvidenceOccurrenceLocatorReview | None:
        return self._reviews.get((field, value_index))

    def selected_span(
        self, field: EvidenceLocatorTargetField, value_index: int | None
    ) -> EvidenceSpan | None:
        return self._indexed.get((field, value_index))

    def bind_model_quote(
        self,
        quote: str,
        field: EvidenceLocatorTargetField,
        value_index: int | None,
    ) -> tuple[int, int] | None:
        """Bind a model quote only when it exactly equals the reviewed extraction span."""
        if not isinstance(quote, str) or not quote:
            return None
        selected = self.selected_span(field, value_index)
        if selected is None or quote != selected.quote:
            return None
        return selected.start, selected.end

    def prompt_payload(self) -> list[dict[str, object]]:
        payload: list[dict[str, object]] = []
        for key, review in self._reviews.items():
            selected = self._indexed[key]
            payload.append(
                {
                    "review_id": review.review_id,
                    "target_field": review.target_field.value,
                    "value_index": review.value_index,
                    "review_status": review.review_status,
                    "reviewer_provenance": review.reviewer_provenance,
                    "reviewer_is_human_expert": review.reviewer_is_human_expert,
                    "formal_gold": review.formal_gold,
                    "selected_occurrence": review.to_payload()["selected_occurrence"],
                    "scope": review.to_payload()["scope"],
                    "selected_extraction_evidence": {
                        "quote": selected.quote,
                        "start": selected.start,
                        "end": selected.end,
                    },
                    "rationale": review.rationale,
                }
            )
        return payload

    @staticmethod
    def _occurrences(
        source_text: str,
        quote: str,
        scope_start: int,
        scope_end: int,
    ) -> list[tuple[int, int]]:
        found: list[tuple[int, int]] = []
        start = source_text.find(quote, scope_start, scope_end)
        while start >= 0:
            found.append((start, start + len(quote)))
            start = source_text.find(quote, start + 1, scope_end)
        return found


__all__ = [
    "EvidenceLocatorReviewResolver",
    "EvidenceLocatorReviewValidationError",
]
