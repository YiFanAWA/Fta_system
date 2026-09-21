"""Port definition for fault extraction implementations."""

import json
from typing import Callable, Protocol

from extraction_contract import (
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)

import re
from model_client import ModelClient, ModelClientError


class FaultExtractor(Protocol):
    """The application-facing contract for every extraction adapter."""

    def extract(self, text: str) -> ExtractionResult:
        """Extract normalized fault facts from source text."""
        ...


_CAUSE_VALUE_PREFIX_RE = re.compile(
    r"^(?:若\s*)?(?:故障值|参数值|状态值)?\s*"
    r"(?:[A-Za-z_]+\s*=\s*)?[0-9A-Za-z]+"
    r"(?:\s*[~～至-]\s*[0-9A-Za-z]+)?"
    r"(?:\s*[、,]\s*[0-9A-Za-z]+)*\s*"
    r"(?:表示|对应)\s*(?P<meaning>.+)$"
)
_CAUSE_VALUE_PAREN_RE = re.compile(
    r"^(?:若\s*)?(?:故障值|参数值|状态值)?\s*"
    r"(?:为\s*)?"
    r"(?:[A-Za-z_]+\s*=\s*)?[0-9A-Za-z]+"
    r"(?:\s*[~～至-]\s*[0-9A-Za-z]+)?"
    r"(?:\s*[、,]\s*[0-9A-Za-z]+)*\s*"
    r"[（(](?P<meaning>.*)[）)]$"
)

# A diagnostic index by itself is not a fault scenario.  Keep this rewrite
# conservative: it adds only the abnormality implied by the enclosing fault
# record and does not invent a concrete failure mode.
_CAUSE_SEMANTIC_REWRITES = {
    # Keep legacy phrasing normalized before applying the generic diagnostic
    # index guard below.  The guard then prevents the index from becoming a
    # candidate cause by itself.
    "交叉比较数据编号异常": "交叉比较数据编号",
    "不存在电机抱闸但SBC使能": "不存在电机抱闸且SBC使能",
    "电机抱闸控制B但SBC使能": "电机抱闸控制，B且SBC使能",
}


def is_diagnostic_index_only(value: str) -> bool:
    """Return True when a cause is only a diagnostic locator, not a scenario."""
    normalized = re.sub(r"\s+", "", value.casefold())
    index_terms = ("编号", "索引", "序号", "index", "identifier")
    diagnostic_terms = ("交叉比较", "crosscomparison", "diagnostic")
    fault_terms = (
        "异常", "不一致", "错误", "失败", "故障", "超时", "无效",
        "mismatch", "error", "fault", "fail", "timeout", "invalid",
    )
    return (
        any(term in normalized for term in index_terms)
        and any(term in normalized for term in diagnostic_terms)
        and not any(term in normalized for term in fault_terms)
    )


def normalize_cause_text(value: str) -> str:
    """Keep the fault scenario, not its parameter-value wrapper."""
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", value)
    match = _CAUSE_VALUE_PREFIX_RE.match(value)
    if match:
        value = match.group("meaning").strip(" ，,；;：:")
    else:
        match = _CAUSE_VALUE_PAREN_RE.match(value)
        if match:
            value = match.group("meaning").strip(" ，,；;：:")
    return _CAUSE_SEMANTIC_REWRITES.get(value, value)


def build_fault_record(raw_item: object) -> FaultRecord:
    """Convert one validated model item into the shared FaultRecord contract."""
    if not isinstance(raw_item, dict):
        raise TypeError("record must be an object")

    related_components = raw_item.get("related_components", raw_item.get("components", ()))
    if related_components is None:
        related_components = ()
    if isinstance(related_components, str):
        related_components = (related_components,)
    if not isinstance(related_components, (list, tuple)):
        raise TypeError("related_components must be a list or tuple of strings")

    causes = (
        ()
        if "causes" not in raw_item or raw_item["causes"] is None
        else tuple(
            normalized
            for cause in raw_item["causes"]
            if isinstance(cause, str)
            and cause.strip()
            for normalized in (normalize_cause_text(cause),)
            if normalized and not is_diagnostic_index_only(normalized)
        )
    )

    return FaultRecord(
        description=raw_item.get("description"),
        fault_code=raw_item.get("fault_code"),
        component=raw_item.get("component"),
        related_components=related_components,
        causes=causes,
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
