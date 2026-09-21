"""Orchestrate text chunking, normalization, and literal evidence binding."""

import re
from typing import Callable, Iterable, Mapping

from contracts.extraction_contract import (
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    EvidenceField,
    EvidenceSpan,
    FaultRecord,
)
from extraction.fault_extractor import (
    RemoteLLMFaultExtractor,
    build_fault_record,
    normalize_cause_text,
)
from extraction.fault_record_grouping import group_related_fault_records
from core.model_client import ModelClient
from domains.component_registry import (
    COMPONENT_EVIDENCE_ALIASES,
    explicit_english_component_candidates,
    find_english_component_heading,
    normalize_component_label,
)


PromptBuilder = Callable[[str, int, int], str]
FallbackBuilder = Callable[[str], Iterable[Mapping[str, object]]]


_EXPLICIT_CAUSE_RE = re.compile(
    r"(?:(?<!原)因|由于|因为|避免|防止|以免|预防)\s*([^，。；;]{2,40}?)(?:导致|造成|引起)"
)
_PREVENTIVE_CAUSE_CONTEXT_RE = re.compile(r"(?:避免|防止|以免|预防)\s*$")
_DOWNSTREAM_FAULT_RE = re.compile(r"(?:二次|次生|后续)\s*故障|secondary\s+fault|downstream\s+fault", re.IGNORECASE)
_EXPLICIT_CAUSE_SECTION_RE = re.compile(
    r"(?ims)^\s*(?:cause|可能原因|候选原因)\s*[:：]\s*"
    r"(?P<body>.*?)(?=^\s*(?:note|fault\s+value|remedy|reaction|acknowledge|故障处理|处理建议)\s*[:：]|\Z)"
)
# ``\b`` does not work for codes adjacent to Chinese characters because both
# sides are Unicode word characters.  Use ASCII-only guards so that
# ``故障代码F01001。`` is still recognized as a code boundary.
_FAULT_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[AFN]\d{5}|E\d+|ERR_[A-Za-z0-9_]+)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_COMPONENT_ABSENT_RE = re.compile(r"(?:组件|驱动对象)\s*为\s*无")
_COMPONENT_DECLARATION_RE = re.compile(
    r"(?P<label>组件|驱动对象)\s*为\s*"
    r"(?P<primary>无|[^，,。；;\n（(]+?)"
    r"(?:\s*[（(]\s*关\s*联\s*(?P<related>[^）)]+)[）)])?"
)
_EXPLICIT_RELATION_ANYWHERE_RE = re.compile(
    r"(?:associated\s+with|related\s+to|connected\s+(?:to|with)|linked\s+to|"
    r"关联(?:组件)?|连接(?:到|至)?|相连|相关组件(?:为|：)?)",
    re.IGNORECASE,
)
_CAUSE_EVIDENCE_ALIASES = {
    "不存在电机抱闸且SBC使能": ("不存在电机抱闸", "SBC使能"),
    "电机抱闸控制，B且SBC使能": ("电机抱闸控制，B", "SBC使能"),
}
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

        normalized_text = text.strip()
        leading_offset = len(text) - len(text.lstrip())
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
        # A fallback is a recovery path for an empty model result, not a
        # second source of records to append to an already usable model result.
        # Appending both paths creates a model record plus a noisy duplicate,
        # which then leaks into review and tree construction.
        should_run_fallback = (
            self._fallback_builder is not None
            and not model_failed
            and not records
        )
        if should_run_fallback:
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
                    "skip_reason": (
                        "model_failed"
                        if model_failed
                        else "model_records_present"
                    ),
                }
            )

        records = self._deduplicate(records)
        records = self._recover_single_explicit_fault_code(records, normalized_text)
        records = list(group_related_fault_records(records))
        records = self._normalize_component_fields(records, normalized_text)
        records = self._normalize_description_fields(records, normalized_text)
        records = self._remove_description_embedded_causes(records)
        records = self._augment_explicit_causes(records, normalized_text)
        records = self._augment_explicit_cause_sections(records, normalized_text)
        evidence_spans = self._build_evidence_spans(
            records,
            normalized_text,
            leading_offset,
        )
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
                evidence_spans=evidence_spans,
                diagnostics=tuple(diagnostics),
            )
        return ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=tuple(records),
            evidence_spans=evidence_spans,
        )

    @classmethod
    def _recover_single_explicit_fault_code(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
    ) -> list[FaultRecord]:
        """Recover one omitted code only when the source has one clear header.

        Siemens manuals commonly put ``A01006``/``F01023`` directly at the
        beginning of a record instead of writing ``fault code A01006``.  The
        model may therefore leave ``fault_code`` empty under a conservative
        prompt.  This repair is intentionally narrow: it runs only for one
        extracted record and one header code, never infers a code from an
        inline message such as ``message F01700``.
        """
        normalized_records = list(records)
        if len(normalized_records) != 1 or normalized_records[0].fault_code:
            return normalized_records

        header_matches = [
            match
            for match in _FAULT_CODE_RE.finditer(source_text)
            if cls._is_fault_record_header(source_text, match)
        ]
        if len(header_matches) != 1:
            return normalized_records

        record = normalized_records[0]
        recovered_code = header_matches[0].group(0).upper()
        updated = FaultRecord(
            description=record.description,
            fault_code=recovered_code,
            component=record.component,
            related_components=record.related_components,
            causes=record.causes,
            parameters=record.parameters,
            confidence=record.confidence,
        )
        object.__setattr__(updated, "record_id", record.record_id)
        return [updated]

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

    @classmethod
    def _build_evidence_spans(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
        leading_offset: int,
    ) -> tuple[EvidenceSpan, ...]:
        """Attach only literal source spans; never invent evidence text.

        Model output commonly removes line breaks around Chinese punctuation.
        The normalized lookup accepts whitespace differences but stores the
        original quote and offsets, so ``EvidenceSpan.matches`` remains true
        against the caller's original source text.
        """
        spans: list[EvidenceSpan] = []
        for record in records:
            source_start, source_end = cls._record_source_bounds(
                record,
                source_text,
                list(_FAULT_CODE_RE.finditer(source_text)),
            )
            field_values = (
                (EvidenceField.FAULT_CODE, "fault_code", (record.fault_code,)),
                (
                    EvidenceField.PRIMARY_COMPONENT,
                    "primary_component",
                    (record.component,),
                ),
                (
                    EvidenceField.RELATED_COMPONENT,
                    "related_component",
                    record.related_components,
                ),
                (EvidenceField.DESCRIPTION, "description", (record.description,)),
                (EvidenceField.CAUSE, "cause", record.causes),
                (EvidenceField.PARAMETER, "parameter", record.parameters),
            )
            for field, _, values in field_values:
                for value_index, value in enumerate(values):
                    if not value:
                        continue
                    locations = cls._find_evidence_locations(
                        source_text[source_start:source_end],
                        value,
                        field,
                    )
                    for location in locations:
                        start, end = location
                        start += source_start
                        end += source_start
                        spans.append(
                            EvidenceSpan(
                                record_id=record.record_id,
                                field=field,
                                source_id="input_text",
                                quote=source_text[start:end],
                                start=leading_offset + start,
                                end=leading_offset + end,
                                value_index=(
                                    value_index
                                    if field
                                    in {
                                        EvidenceField.RELATED_COMPONENT,
                                        EvidenceField.CAUSE,
                                        EvidenceField.PARAMETER,
                                    }
                                    else None
                                ),
                            ),
                        )
            if record.component is None:
                declaration = cls._find_component_declaration(
                    source_text,
                    source_start,
                    source_end,
                )
                if declaration is not None:
                    declaration_field, start, end = declaration
                    spans.append(
                        EvidenceSpan(
                            record_id=record.record_id,
                            field=declaration_field,
                            source_id="input_text",
                            quote=source_text[start:end],
                            start=leading_offset + start,
                            end=leading_offset + end,
                        )
                    )
        return cls._deduplicate_evidence_spans(spans)

    @staticmethod
    def _deduplicate_evidence_spans(
        spans: Iterable[EvidenceSpan],
    ) -> tuple[EvidenceSpan, ...]:
        """Merge repeated source quotes shared by multiple normalized values."""
        merged: list[EvidenceSpan] = []
        by_location: dict[tuple[object, ...], int] = {}
        for span in spans:
            key = (
                span.record_id,
                span.field,
                span.source_id,
                span.start,
                span.end,
            )
            existing_index = by_location.get(key)
            if existing_index is None:
                by_location[key] = len(merged)
                merged.append(span)
                continue
            existing = merged[existing_index]
            if existing.value_index != span.value_index:
                merged[existing_index] = EvidenceSpan(
                    record_id=existing.record_id,
                    field=existing.field,
                    source_id=existing.source_id,
                    quote=existing.quote,
                    start=existing.start,
                    end=existing.end,
                    value_index=None,
                )
        return tuple(merged)

    @classmethod
    def _find_evidence_locations(
        cls,
        source_text: str,
        value: str,
        field: EvidenceField,
    ) -> tuple[tuple[int, int], ...]:
        location = cls._find_literal_span(source_text, value)
        if location is not None:
            return (location,)
        if field is EvidenceField.PRIMARY_COMPONENT:
            alias_locations: list[tuple[int, int]] = []
            for evidence_value in COMPONENT_EVIDENCE_ALIASES.get(value, ()):
                alias_location = cls._find_literal_span(source_text, evidence_value)
                if alias_location is not None and alias_location not in alias_locations:
                    alias_locations.append(alias_location)
            if alias_locations:
                return tuple(alias_locations)
        if field is not EvidenceField.CAUSE:
            return ()

        alias_locations: list[tuple[int, int]] = []
        for evidence_value in _CAUSE_EVIDENCE_ALIASES.get(value, ()):
            alias_location = cls._find_literal_span(source_text, evidence_value)
            if alias_location is not None and alias_location not in alias_locations:
                alias_locations.append(alias_location)
        if alias_locations:
            return tuple(alias_locations)

        # A model may compact a conditional scenario that is separated in the
        # source by parameter assignments, e.g. “不存在电机抱闸且SBC使能”
        # versus “不存在电机抱闸）且 p9602=1（SBC使能）”. Keep one cause value
        # but bind each meaningful literal part as evidence.
        parts = re.split(r"\s*(?:且|但|和|与)\s*", value)
        locations: list[tuple[int, int]] = []
        for part in parts:
            if len(part.strip()) < 2:
                continue
            part_location = cls._find_literal_span(source_text, part.strip())
            if part_location is not None and part_location not in locations:
                locations.append(part_location)
        return tuple(locations)

    @staticmethod
    def _find_literal_span(source_text: str, value: str) -> tuple[int, int] | None:
        direct_start = source_text.find(value)

        normalized_source: list[str] = []
        source_indexes: list[int] = []
        for index, character in enumerate(source_text):
            if character.isspace():
                continue
            normalized_source.append(character.casefold())
            source_indexes.append(index)

        normalized_value = "".join(
            character.casefold() for character in value if not character.isspace()
        )
        normalized_start = "".join(normalized_source).find(normalized_value)
        normalized_location = None
        if normalized_start >= 0 and normalized_value:
            source_start = source_indexes[normalized_start]
            source_end = source_indexes[normalized_start + len(normalized_value) - 1] + 1
            normalized_location = source_start, source_end

        direct_location = (
            (direct_start, direct_start + len(value))
            if direct_start >= 0
            else None
        )
        if normalized_location is None:
            return direct_location
        if direct_location is None:
            return normalized_location
        return min(normalized_location, direct_location, key=lambda location: location[0])

    @classmethod
    def _normalize_component_fields(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
    ) -> list[FaultRecord]:
        """Align component fields with explicit component declarations."""
        code_matches = list(_FAULT_CODE_RE.finditer(source_text))
        output: list[FaultRecord] = []
        for record in records:
            start, end = cls._record_source_bounds(record, source_text, code_matches)
            window = source_text[start:end]
            declaration = cls._find_component_declaration_detail(window)
            if declaration is None:
                heading_component = find_english_component_heading(window)
                recovered_related = cls._recover_explicit_english_related_components(
                    record.related_components,
                    window,
                    record.component or heading_component,
                )
                filtered_related = cls._filter_related_components(
                    recovered_related,
                    window,
                )
                component = heading_component or normalize_component_label(
                    record.component
                )
                component = component or record.component
                filtered_related = tuple(
                    value
                    for value in filtered_related
                    if cls._component_identity_key(value)
                    != cls._component_identity_key(component)
                )
                if (
                    component == record.component
                    and filtered_related == record.related_components
                ):
                    output.append(record)
                    continue
                updated = FaultRecord(
                    description=record.description,
                    fault_code=record.fault_code,
                    component=component,
                    related_components=filtered_related,
                    causes=record.causes,
                    parameters=record.parameters,
                    confidence=record.confidence,
                )
                object.__setattr__(updated, "record_id", record.record_id)
                output.append(updated)
                continue

            label, primary, related_text = declaration
            declared_related = cls._split_declared_components(related_text)
            component = record.component
            if primary == "无":
                component = None
            related = declared_related
            if component == record.component and related == record.related_components:
                output.append(record)
                continue
            updated = FaultRecord(
                description=record.description,
                fault_code=record.fault_code,
                component=component,
                related_components=related,
                causes=record.causes,
                parameters=record.parameters,
                confidence=record.confidence,
            )
            object.__setattr__(updated, "record_id", record.record_id)
            output.append(updated)
        return output

    @classmethod
    def _normalize_description_fields(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
    ) -> list[FaultRecord]:
        """Keep descriptions on the explicit phenomenon/title boundary.

        Manuals commonly put the phenomenon after ``故障现象为`` or put the
        English title on the first line before ``Reaction``/``Cause``.  A model
        may otherwise copy a component prefix, the fault-category header, or
        the following Cause paragraph into ``description``.  This is a
        structural boundary repair, not a vocabulary list.
        """
        code_matches = list(_FAULT_CODE_RE.finditer(source_text))
        output: list[FaultRecord] = []
        for record in records:
            description = str(record.description or "").strip()
            start, end = cls._record_source_bounds(record, source_text, code_matches)
            window = source_text[start:end]
            candidate = cls._explicit_description_candidate(window, record.fault_code)
            if candidate:
                description = candidate

            component = str(record.component or "").strip()
            if component:
                component_label = re.split(r"[（(]", component, maxsplit=1)[0].strip()
                prefix = re.match(
                    rf"^{re.escape(component_label)}\s*[：:]\s*",
                    description,
                    re.IGNORECASE,
                )
                if prefix:
                    description = description[prefix.end() :].strip()

            if description == record.description:
                output.append(record)
                continue
            updated = FaultRecord(
                description=description,
                fault_code=record.fault_code,
                component=record.component,
                related_components=record.related_components,
                causes=record.causes,
                parameters=record.parameters,
                confidence=record.confidence,
            )
            object.__setattr__(updated, "record_id", record.record_id)
            output.append(updated)
        return output

    @classmethod
    def _remove_description_embedded_causes(
        cls,
        records: Iterable[FaultRecord],
    ) -> list[FaultRecord]:
        """Do not duplicate a fault phenomenon as a candidate cause."""
        output: list[FaultRecord] = []
        for record in records:
            description_key = cls._normalize_repeated_text(record.description)
            causes = tuple(
                cause
                for cause in record.causes
                if not (
                    description_key
                    and len(cls._normalize_repeated_text(cause)) >= 4
                    and cls._normalize_repeated_text(cause) in description_key
                )
            )
            if causes == record.causes:
                output.append(record)
                continue
            updated = FaultRecord(
                description=record.description,
                fault_code=record.fault_code,
                component=record.component,
                related_components=record.related_components,
                causes=causes,
                parameters=record.parameters,
                confidence=record.confidence,
            )
            object.__setattr__(updated, "record_id", record.record_id)
            output.append(updated)
        return output

    @staticmethod
    def _contains_normalized_text(text: str, candidate: str) -> bool:
        compact = re.sub(r"\s+", "", str(text or "").casefold())
        target = re.sub(r"\s+", "", str(candidate or "").casefold())
        return bool(target) and target in compact

    @staticmethod
    def _explicit_description_candidate(window: str, fault_code: str | None) -> str:
        marker = re.search(
            r"(?:故障现象|报警信息|故障描述)\s*(?:为|是|[:：])\s*([^。！？!?]+)",
            window,
        )
        if marker:
            return marker.group(1).strip(" \t\r\n\"“”")

        first_line = next((line.strip() for line in window.splitlines() if line.strip()), "")
        code = str(fault_code or "").strip()
        if not first_line or not code:
            return ""
        header = re.match(rf"^{re.escape(code)}\s+(.+)$", first_line, re.IGNORECASE)
        if not header:
            return ""
        title = header.group(1).strip()
        if ":" in title:
            title = title.split(":", 1)[1].strip()
        return title

    @staticmethod
    def _filter_related_components(
        related_components: tuple[str, ...],
        source_window: str,
    ) -> tuple[str, ...]:
        """Keep related components only when a nearby relation is explicit."""
        if not related_components:
            return ()
        kept: list[str] = []
        for value in related_components:
            value = normalize_component_label(value)
            value_lower = value.casefold()
            clauses = re.split(r"[\n\r。！？!?；;]+", source_window)
            if any(
                value_lower in clause.casefold()
                and _EXPLICIT_RELATION_ANYWHERE_RE.search(clause)
                for clause in clauses
            ):
                kept.append(value)
        return tuple(kept)

    def _recover_explicit_english_related_components(
        related_components: tuple[str, ...],
        source_window: str,
        primary_component: str | None,
    ) -> tuple[str, ...]:
        """Recover only named components in an explicit English relation clause."""
        recovered = [
            normalize_component_label(value)
            for value in related_components
        ]
        primary_key = TextExtractionAdapter._component_identity_key(primary_component)
        clauses = re.split(r"[\n\r。！？!?；;]+", source_window)
        for clause in clauses:
            if not _EXPLICIT_RELATION_ANYWHERE_RE.search(clause):
                continue
            for pattern, canonical in explicit_english_component_candidates(clause):
                if not pattern.search(clause):
                    continue
                candidate_key = TextExtractionAdapter._component_identity_key(canonical)
                if candidate_key == primary_key:
                    continue
                if not any(
                    TextExtractionAdapter._component_identity_key(value) == candidate_key
                    for value in recovered
                ):
                    recovered.append(canonical)
        return tuple(recovered)

    @staticmethod
    def _component_identity_key(value: str | None) -> str:
        key = re.sub(r"[^a-z0-9]+", "", (value or "").casefold())
        if key.endswith("s") and not key.endswith("ss"):
            key = key[:-1]
        return key

    @staticmethod
    def _find_component_declaration_detail(
        source_window: str,
    ) -> tuple[str, str, str | None] | None:
        declarations = list(_COMPONENT_DECLARATION_RE.finditer(source_window))
        if not declarations:
            return None
        # An explicit component declaration is authoritative when both fields
        # appear. Otherwise, a driver-object declaration must not be promoted
        # into the component field.
        match = next(
            (item for item in declarations if item.group("label") == "组件"),
            declarations[0],
        )
        return (
            match.group("label"),
            match.group("primary").strip(),
            match.group("related"),
        )

    @staticmethod
    def _split_declared_components(value: str | None) -> tuple[str, ...]:
        if not value:
            return ()
        parts = re.split(r"\s*(?:及|和|与|、|,|，)\s*", value)
        cleaned: list[str] = []
        seen: set[str] = set()
        for part in parts:
            name = re.sub(r"\s+", "", part).strip()
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            cleaned.append(name)
        return tuple(cleaned)

    @staticmethod
    def _find_component_declaration(
        source_text: str,
        source_start: int,
        source_end: int,
    ) -> tuple[EvidenceField, int, int] | None:
        match = _COMPONENT_ABSENT_RE.search(source_text, source_start, source_end)
        if match is None:
            return None
        field = (
            EvidenceField.DRIVER_OBJECT_DECLARATION
            if match.group(0).startswith("驱动对象")
            else EvidenceField.COMPONENT_DECLARATION
        )
        return field, match.start(), match.end()

    @classmethod
    def _augment_explicit_causes(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
    ) -> list[FaultRecord]:
        """Add only explicit causal phrases that the model omitted.

        This is deliberately narrower than general cause inference.  It only
        recognizes Chinese causal markers followed by ``导致/造成/引起`` and
        limits each record to the source segment beginning at its fault code.
        The extracted phrase remains literal source text, so evidence binding
        can audit the augmentation just like a model field.
        """
        records = list(records)
        if not source_text or not records:
            return records

        code_matches = list(_FAULT_CODE_RE.finditer(source_text))
        output: list[FaultRecord] = []
        for record in records:
            window = cls._record_source_window(record, source_text, code_matches)
            additions: list[str] = []
            existing = {
                cls._normalize_repeated_text(cause) for cause in record.causes
            }
            for match in _EXPLICIT_CAUSE_RE.finditer(window):
                # A remedy/prevention sentence such as “避免因散热不良导致
                # 二次故障” describes a downstream risk, not the cause of the
                # current fault.  Keep explicit causal augmentation narrow and
                # leave the source available for normal evidence review.
                prefix = window[max(0, match.start() - 40) : match.start()]
                downstream = window[match.end() : match.end() + 20]
                marker = match.group(0).lstrip()
                preventive_marker = bool(
                    re.match(r"(?:避免|防止|以免|预防)", marker)
                    or _PREVENTIVE_CAUSE_CONTEXT_RE.search(prefix)
                )
                if preventive_marker and _DOWNSTREAM_FAULT_RE.search(downstream):
                    continue
                cause = match.group(1).strip(" ，,：:；;")
                cause = re.sub(r"^(?:因|由于|因为)\s*", "", cause)
                cause = normalize_cause_text(cause)
                key = cls._normalize_repeated_text(cause)
                if not cause or not key or key in existing:
                    continue
                existing.add(key)
                additions.append(cause)
            if not additions:
                output.append(record)
                continue
            updated = FaultRecord(
                description=record.description,
                fault_code=record.fault_code,
                component=record.component,
                related_components=record.related_components,
                causes=tuple(record.causes) + tuple(additions),
                parameters=record.parameters,
                confidence=record.confidence,
            )
            object.__setattr__(updated, "record_id", record.record_id)
            output.append(updated)
        return output

    @classmethod
    def _augment_explicit_cause_sections(
        cls,
        records: Iterable[FaultRecord],
        source_text: str,
    ) -> list[FaultRecord]:
        """Recover a literal Cause section only when the model returned none."""
        if not source_text:
            return list(records)
        code_matches = list(_FAULT_CODE_RE.finditer(source_text))
        output: list[FaultRecord] = []
        for record in records:
            if record.causes:
                output.append(record)
                continue
            start, end = cls._record_source_bounds(record, source_text, code_matches)
            window = source_text[start:end]
            match = _EXPLICIT_CAUSE_SECTION_RE.search(window)
            if match is None:
                output.append(record)
                continue
            cause = normalize_cause_text(match.group("body").strip(" \t\r\n-•"))
            if not cause:
                output.append(record)
                continue
            updated = FaultRecord(
                description=record.description,
                fault_code=record.fault_code,
                component=record.component,
                related_components=record.related_components,
                causes=(cause,),
                parameters=record.parameters,
                confidence=record.confidence,
            )
            object.__setattr__(updated, "record_id", record.record_id)
            output.append(updated)
        return output

    @staticmethod
    def _normalize_repeated_text(value: str) -> str:
        return re.sub(r"\s+", "", value).casefold()

    @staticmethod
    def _record_source_window(
        record: FaultRecord,
        source_text: str,
        code_matches: list[re.Match[str]],
    ) -> str:
        start, end = TextExtractionAdapter._record_source_bounds(
            record, source_text, code_matches
        )
        return source_text[start:end]

    @staticmethod
    def _record_source_bounds(
        record: FaultRecord,
        source_text: str,
        code_matches: list[re.Match[str]],
    ) -> tuple[int, int]:
        if not record.fault_code:
            return 0, len(source_text)
        code = record.fault_code.casefold()
        header_matches = [
            match
            for match in code_matches
            if TextExtractionAdapter._is_fault_record_header(source_text, match)
        ]
        candidate_matches = header_matches or code_matches
        start = next(
            (
                match.start()
                for match in candidate_matches
                if match.group(0).casefold() == code
            ),
            0,
        )
        end = len(source_text)
        for match in candidate_matches:
            if match.start() <= start:
                continue
            if match.group(0).casefold() != code:
                end = match.start()
                break
        return start, end

    @staticmethod
    def _is_fault_record_header(
        source_text: str,
        match: re.Match[str],
    ) -> bool:
        prefix = source_text[max(0, match.start() - 12) : match.start()]
        if re.search(r"(?:故障代码|故障码|fault\s+code|error\s+code)\s*$", prefix, re.IGNORECASE):
            return True
        return not prefix.strip() or prefix.endswith(("\n", "\r"))

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
