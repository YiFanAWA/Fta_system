"""Port definition for fault extraction implementations."""

import json
from typing import Callable, Protocol

from extraction_contract import (
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from model_client import ModelClient, ModelClientError


class FaultExtractor(Protocol):
    """The application-facing contract for every extraction adapter."""

    def extract(self, text: str) -> ExtractionResult:
        """Extract normalized fault facts from source text."""
        ...


def build_fault_record(raw_item: object) -> FaultRecord:
    """Convert one validated model item into the shared FaultRecord contract."""
    if not isinstance(raw_item, dict):
        raise TypeError("record must be an object")

    return FaultRecord(
        description=raw_item.get("description"),
        fault_code=raw_item.get("fault_code"),
        component=raw_item.get("component"),
        causes=(
            ()
            if "causes" not in raw_item or raw_item["causes"] is None
            else raw_item["causes"]
        ),
        parameters=(
            ()
            if "parameters" not in raw_item or raw_item["parameters"] is None
            else raw_item["parameters"]
        ),
        confidence=raw_item.get("confidence"),
    )


class RemoteLLMFaultExtractor:
    """Adapt a text-generation client to the FaultExtractor contract."""

    def __init__(
        self,
        model_client: ModelClient,
        prompt_builder: Callable[[str], str],
    ) -> None:
        self._model_client = model_client
        self._prompt_builder = prompt_builder

    def extract(self, text: str) -> ExtractionResult:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        prompt = self._prompt_builder(text)

        try:
            raw_response = self._model_client.complete(prompt)
        except ModelClientError as exc:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                diagnostics=(
                    ExtractionDiagnostic(
                        code=exc.code,
                        message=exc.message,
                        stage="provider",
                        retryable=exc.retryable,
                    ),
                ),
            )

        if not isinstance(raw_response, str):
            return self._failed(
                code="invalid_model_response",
                message="model client returned a non-text response",
                stage="provider",
            )

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            return self._failed(
                code="invalid_json",
                message=f"model response is not valid JSON: {exc.msg}",
                stage="json_parsing",
            )

        if not isinstance(payload, dict) or "items" not in payload:
            return self._failed(
                code="invalid_payload_schema",
                message="model JSON must be an object containing an items array",
                stage="payload_validation",
            )

        raw_items = payload["items"]
        if not isinstance(raw_items, list):
            return self._failed(
                code="invalid_items_schema",
                message="model JSON items must be an array",
                stage="payload_validation",
            )

        if not raw_items:
            return ExtractionResult(status=ExtractionStatus.EMPTY)

        records: list[FaultRecord] = []
        diagnostics: list[ExtractionDiagnostic] = []

        for index, raw_item in enumerate(raw_items):
            try:
                records.append(build_fault_record(raw_item))
            except (TypeError, ValueError) as exc:
                diagnostics.append(
                    ExtractionDiagnostic(
                        code="invalid_record",
                        message=f"item at index {index} is invalid: {exc}",
                        stage="record_validation",
                    )
                )

        if not records:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                diagnostics=tuple(diagnostics),
            )
        if diagnostics:
            return ExtractionResult(
                status=ExtractionStatus.PARTIAL,
                records=tuple(records),
                diagnostics=tuple(diagnostics),
            )
        return ExtractionResult(status=ExtractionStatus.SUCCESS, records=tuple(records))

    @staticmethod
    def _failed(*, code: str, message: str, stage: str) -> ExtractionResult:
        return ExtractionResult(
            status=ExtractionStatus.FAILED,
            diagnostics=(
                ExtractionDiagnostic(code=code, message=message, stage=stage),
            ),
        )
