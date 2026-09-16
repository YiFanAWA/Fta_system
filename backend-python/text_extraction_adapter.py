"""Orchestrate text chunking and model-output normalization."""

from typing import Callable, Iterable, Mapping

from extraction_contract import (
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from fault_extractor import (
    RemoteLLMFaultExtractor,
    build_fault_record,
)
from model_client import ModelClient


PromptBuilder = Callable[[str, int, int], str]
FallbackBuilder = Callable[[str], Iterable[Mapping[str, object]]]


class TextExtractionAdapter:
    """Adapt a model client into one complete text-extraction operation.

    The adapter owns chunking, per-chunk extraction, conservative deduplication,
    and aggregation of diagnostics. It does not own provider-specific code or
    FTA tree construction.
    """

    def __init__(
        self,
        model_client: ModelClient,
        prompt_builder: PromptBuilder,
        *,
        chunk_size_chars: int = 6000,
        overlap_chars: int = 300,
        fallback_builder: FallbackBuilder | None = None,
    ) -> None:
        if not isinstance(chunk_size_chars, int) or isinstance(chunk_size_chars, bool):
            raise ValueError("chunk_size_chars must be an integer")
        if chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars must be positive")
        if not isinstance(overlap_chars, int) or isinstance(overlap_chars, bool):
            raise ValueError("overlap_chars must be an integer")
        if overlap_chars < 0 or overlap_chars >= chunk_size_chars:
            raise ValueError("overlap_chars must satisfy 0 <= overlap < chunk_size")

        self._model_client = model_client
        self._prompt_builder = prompt_builder
        self._chunk_size_chars = chunk_size_chars
        self._overlap_chars = overlap_chars
        self._fallback_builder = fallback_builder
        self.last_chunk_reports: tuple[dict[str, object], ...] = ()

    def extract(self, text: str) -> ExtractionResult:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        chunks = self._split_chunks(text)
        reports: list[dict[str, object]] = []
        records: list[FaultRecord] = []
        diagnostics: list[ExtractionDiagnostic] = []

        total_chunks = len(chunks)
        for chunk_index, chunk in enumerate(chunks):
            try:
                extractor = RemoteLLMFaultExtractor(
                    self._model_client,
                    lambda chunk_text, index=chunk_index: self._prompt_builder(
                        chunk_text,
                        index,
                        total_chunks,
                    ),
                )
                chunk_result = extractor.extract(chunk)
            except Exception as exc:
                chunk_result = ExtractionResult(
                    status=ExtractionStatus.FAILED,
                    diagnostics=(
                        ExtractionDiagnostic(
                            code="adapter_extraction_error",
                            message=f"chunk extraction failed: {exc}",
                            stage="adapter",
                        ),
                    ),
                )
            records.extend(chunk_result.records)
            diagnostics.extend(
                self._with_chunk_context(chunk_result.diagnostics, chunk_index)
            )
            reports.append(
                {
                    "source": "model",
                    "chunk_index": chunk_index + 1,
                    "status": chunk_result.status.value,
                    "accepted_count": len(chunk_result.records),
                    "diagnostic_codes": tuple(
                        diagnostic.code for diagnostic in chunk_result.diagnostics
                    ),
                }
            )

        model_failed = any(
            report.get("source") == "model" and report.get("status") == "failed"
            for report in reports
        )

        fallback_used = False
        if self._fallback_builder is not None and not model_failed:
            try:
                fallback_diagnostic_start = len(diagnostics)
                fallback_items = self._fallback_builder(text)
                fallback_records: list[FaultRecord] = []
                for item_index, item in enumerate(fallback_items):
                    try:
                        fallback_records.append(build_fault_record(dict(item)))
                    except (TypeError, ValueError) as exc:
                        diagnostics.append(
                            ExtractionDiagnostic(
                                code="invalid_fallback_record",
                                message=(
                                    f"fallback item at index {item_index} is invalid: {exc}"
                                ),
                                stage="fallback_validation",
                            )
                        )
                records.extend(fallback_records)
                if fallback_records:
                    fallback_used = True
                    diagnostics.append(
                        ExtractionDiagnostic(
                            code="fallback_used",
                            message=(
                                "rule fallback produced records; manual review is required"
                            ),
                            stage="fallback",
                        )
                    )
                reports.append(
                    {
                        "source": "fallback",
                        "status": "success" if fallback_records else "empty",
                        "accepted_count": len(fallback_records),
                        "diagnostic_codes": tuple(
                            diagnostic.code
                            for diagnostic in diagnostics[fallback_diagnostic_start:]
                        ),
                    }
                )
            except Exception as exc:
                diagnostics.append(
                    ExtractionDiagnostic(
                        code="fallback_failed",
                        message=f"fallback extraction failed: {exc}",
                        stage="fallback",
                    )
                )
                reports.append(
                    {
                        "source": "fallback",
                        "status": "failed",
                        "accepted_count": 0,
                        "diagnostic_codes": ("fallback_failed",),
                    }
                )
        elif self._fallback_builder is not None:
            reports.append(
                {
                    "source": "fallback",
                    "status": "skipped",
                    "accepted_count": 0,
                    "diagnostic_codes": (),
                }
            )

        records = self._deduplicate(records)
        self.last_chunk_reports = tuple(reports)

        if not records:
            if diagnostics:
                return ExtractionResult(
                    status=ExtractionStatus.FAILED,
                    diagnostics=tuple(diagnostics),
                )
            return ExtractionResult(status=ExtractionStatus.EMPTY)

        if diagnostics or fallback_used:
            return ExtractionResult(
                status=ExtractionStatus.PARTIAL,
                records=tuple(records),
                diagnostics=tuple(diagnostics),
            )
        return ExtractionResult(status=ExtractionStatus.SUCCESS, records=tuple(records))

    def _split_chunks(self, text: str) -> list[str]:
        cleaned = text.strip()
        chunks: list[str] = []
        start = 0

        while start < len(cleaned):
            end = min(start + self._chunk_size_chars, len(cleaned))
            chunks.append(cleaned[start:end])
            if end == len(cleaned):
                break
            start = end - self._overlap_chars

        return chunks

    @staticmethod
    def _with_chunk_context(
        diagnostics: Iterable[ExtractionDiagnostic],
        chunk_index: int,
    ) -> list[ExtractionDiagnostic]:
        display_index = chunk_index + 1
        return [
            ExtractionDiagnostic(
                code=diagnostic.code,
                message=f"chunk {display_index}: {diagnostic.message}",
                stage=f"chunk_{display_index}.{diagnostic.stage}",
                retryable=diagnostic.retryable,
            )
            for diagnostic in diagnostics
        ]

    @staticmethod
    def _deduplicate(records: Iterable[FaultRecord]) -> list[FaultRecord]:
        """Remove only exact semantic duplicates created by chunk overlap.

        This is deliberately narrower than business-level deduplication. A
        later stage may decide that two differently worded records are the same
        fault; this adapter must not silently make that decision.
        """
        result: list[FaultRecord] = []
        seen: set[tuple[object, ...]] = set()
        for record in records:
            key = (
                record.fault_code,
                record.component,
                record.description,
                record.causes,
                record.parameters,
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(record)
        return result
