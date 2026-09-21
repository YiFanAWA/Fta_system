"""Application-layer orchestration for extraction and initial review setup."""

from contracts.extraction_contract import ExtractionResult
from extraction.extraction_repository import ExtractionWorkflowRepository
from extraction.fault_extractor import FaultExtractor
from contracts.review_contract import ReviewableExtractionResult
from extraction.review_preparation_service import ReviewPreparationService


class ExtractionApplicationService:
    """Coordinate extraction, review preparation, and atomic persistence."""

    def __init__(
        self,
        extractor: FaultExtractor,
        repository: ExtractionWorkflowRepository,
        review_preparation: ReviewPreparationService | None = None,
    ) -> None:
        self._extractor = extractor
        self._repository = repository
        self._review_preparation = review_preparation or ReviewPreparationService()

    def extract(self, text: str) -> ReviewableExtractionResult:
        """Run one extraction workflow and persist its initial review state."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not text.strip():
            raise ValueError("text must not be empty")

        extraction: ExtractionResult = self._extractor.extract(text)
        reviews = self._review_preparation.prepare(extraction)
        return self._repository.save_extraction_with_reviews(
            extraction,
            reviews,
        )
