"""Siemens S210 adapter for the common fault schema."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Sequence

from contracts.common_fault_schema import (
    FaultEntity,
    FaultEvidence,
    build_fault_entity_id,
    normalize_fault_entity,
)
from contracts.domain_adapter_contract import ExactFieldMatches, RetrievalChunk, RetrievalFieldValues


_SECTION_RE = re.compile(
    r"(?im)^(?P<header>Reaction|Acknowledge|Cause|Alarm value|Fault value|Remedy|Note|See also)\b[^\n]*:"
)
_FAULT_CODE_RE = re.compile(r"(?<![A-Z0-9])[AFN]\d{5}(?![A-Z0-9])", re.IGNORECASE)
_PARAMETER_RE = re.compile(r"(?<![A-Z0-9])[PR]\d{4,5}(?:\[\d+\])?(?![A-Z0-9])", re.IGNORECASE)
_LEGACY_ALARM_VALUE_RE = re.compile(
    r"(?ims)^(?:Alarm value|Fault value)\b.*?(?=^Remedy:|\Z)"
)


def _section(text: str, labels: tuple[str, ...]) -> str:
    matches = list(_SECTION_RE.finditer(text or ""))
    wanted = {label.casefold() for label in labels}
    for index, match in enumerate(matches):
        if match.group("header").casefold() not in wanted:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[match.start():end].strip()
    return ""


def _section_until(text: str, labels: tuple[str, ...], end_labels: tuple[str, ...]) -> str:
    """Return a section whose boundary is a domain-declared end header.

    S210 alarm/fault values may contain ``Note:`` and parameter lines.  Those
    are part of the value explanation; the old validated pipeline bounded this
    section at ``Remedy:`` rather than at every manual heading.
    """

    matches = list(_SECTION_RE.finditer(text or ""))
    wanted = {label.casefold() for label in labels}
    endings = {label.casefold() for label in end_labels}
    for index, match in enumerate(matches):
        if match.group("header").casefold() not in wanted:
            continue
        end = len(text)
        for following in matches[index + 1 :]:
            if following.group("header").casefold() in endings:
                end = following.start()
                break
        return text[match.start() : end].strip()
    return ""


class SiemensS210Adapter:
    """Map the frozen S210 Gold shape without changing its source semantics."""

    domain = "industrial_drive"
    manufacturer = "Siemens"
    system = "S210"

    def parse_source(self, payload: dict[str, Any]) -> tuple[FaultEntity, ...]:
        if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
            raise ValueError("S210 Gold payload must contain a samples list")
        entities: list[FaultEntity] = []
        for sample in payload["samples"]:
            if not isinstance(sample, dict):
                continue
            raw_text = str(sample.get("input_text") or "")
            source_file = str(sample.get("source_file") or "")
            records = sample.get("gold_records", [])
            for record in records if isinstance(records, list) else []:
                if not isinstance(record, dict):
                    continue
                code = str(record.get("fault_code") or "").strip().upper()
                description = str(record.get("description") or "").strip()
                if not code or not description:
                    continue
                primary = str(record.get("component") or "").strip()
                related = self._strings(record.get("related_components"))
                components = self._unique((primary, *related))
                evidence = self._evidence(sample.get("evidence_spans"), code, source_file)
                entity = FaultEntity(
                    entity_id=build_fault_entity_id(
                        domain=self.domain,
                        manufacturer=self.manufacturer,
                        system=self.system,
                        fault_code=code,
                    ),
                    domain=self.domain,
                    manufacturer=self.manufacturer,
                    system=self.system,
                    fault_code=code,
                    description=description,
                    causes=self._strings(record.get("causes")),
                    components=components,
                    parameters=self._strings(record.get("parameters")),
                    remedies=(
                        remedy
                        if (remedy := _section(raw_text, ("Remedy",)))
                        else ()
                    ),
                    evidence=evidence,
                    raw_text=raw_text,
                    domain_specific={
                        "sample_id": sample.get("sample_id"),
                        "sequence": sample.get("sequence"),
                        "split": sample.get("split"),
                        "source_type": sample.get("source_type"),
                        "primary_component": primary,
                        "related_components": list(related),
                        "alarm_value": self._alarm_value(raw_text),
                        "gate_type": record.get("gate_type"),
                        "logic_status": sample.get("logic_status", "unknown"),
                        "gold_relations": sample.get("gold_relations", []),
                        "review_queue": sample.get("review_queue", {}),
                    },
                )
                entities.append(normalize_fault_entity(entity))
        return tuple(entities)

    def parse_file(self, path: str | Path) -> tuple[FaultEntity, ...]:
        import json

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.parse_source(payload)

    def normalize_entity(self, entity: FaultEntity) -> FaultEntity:
        return normalize_fault_entity(entity)

    def build_retrieval_chunks(self, entities: Sequence[FaultEntity]) -> tuple[RetrievalChunk, ...]:
        """Build generic child chunks while retaining one parent entity id."""

        chunks: list[RetrievalChunk] = []
        for entity in entities:
            fields = (
                ("description", entity.description),
                ("cause", " | ".join(entity.causes)),
                ("alarm", str(entity.domain_specific.get("alarm_value") or "")),
                ("full", "\n".join([entity.description, *entity.causes, *entity.remedies])),
            )
            for kind, text in fields:
                if str(text).strip():
                    chunks.append(
                        RetrievalChunk(
                            chunk_id=f"{entity.entity_id}:{kind}",
                            entity_id=entity.entity_id,
                            kind=kind,
                            text=str(text).strip(),
                            metadata={"fault_code": entity.fault_code},
                        )
                    )
        return tuple(chunks)

    def retrieval_field_values(self, entity: FaultEntity) -> RetrievalFieldValues:
        """Expose S210 values through generic retrieval roles only."""

        primary = str(entity.description or "").strip()
        causes = tuple(str(value).strip() for value in entity.causes if str(value).strip())
        parameters = tuple(str(value).strip() for value in entity.parameters if str(value).strip())
        alarm_value = str(entity.domain_specific.get("alarm_value") or "").strip()
        primary_component = str(entity.domain_specific.get("primary_component") or "").strip()
        related = tuple(str(value).strip() for value in entity.domain_specific.get("related_components", []) if str(value).strip())
        return RetrievalFieldValues(
            semantic_primary=primary,
            semantic_cause=" ".join(causes),
            semantic_auxiliary=alarm_value,
            exact_identifier=entity.fault_code,
            exact_parameters=parameters,
            metadata={
                "component": primary_component,
                "related_components": related,
            },
            reranker_fields=(
                ("Fault code", (entity.fault_code,)),
                ("Component", (primary_component,)),
                ("Related components", related),
                ("Description", (primary,)),
                ("Causes", causes),
                ("Parameters", parameters),
                ("Alarm value section", (alarm_value,)),
            ),
        )

    def extract_exact_fields(self, question: str) -> ExactFieldMatches:
        text = str(question or "")
        return ExactFieldMatches(
            fault_codes=tuple(sorted({value.upper() for value in _FAULT_CODE_RE.findall(text)})),
            parameters=tuple(sorted({self._normalize_parameter(value) for value in _PARAMETER_RE.findall(text)})),
        )

    @staticmethod
    def _normalize_parameter(value: str) -> str:
        return re.sub(r"\[\d+\]$", "", str(value).strip().upper())

    @staticmethod
    def _alarm_value(text: str) -> str:
        """Keep S210's validated alarm-value boundary, including inline prose."""

        match = _LEGACY_ALARM_VALUE_RE.search(str(text or ""))
        return match.group(0).strip() if match else ""

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return ()
        return tuple(str(item).strip() for item in value if str(item).strip())

    @staticmethod
    def _unique(values: Sequence[str]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            value = str(value).strip()
            if value and value not in result:
                result.append(value)
        return tuple(result)

    @staticmethod
    def _evidence(raw_spans: Any, code: str, source_file: str) -> tuple[FaultEvidence, ...]:
        if not isinstance(raw_spans, list):
            return ()
        result: list[FaultEvidence] = []
        seen: set[tuple[str, str, Any, Any]] = set()
        for raw in raw_spans:
            if not isinstance(raw, dict):
                continue
            field = str(raw.get("field") or "source").strip()
            quote = str(raw.get("quote") or "").strip()
            if not quote or (field, quote, raw.get("start"), raw.get("end")) in seen:
                continue
            seen.add((field, quote, raw.get("start"), raw.get("end")))
            result.append(
                FaultEvidence(
                    evidence_id=f"{code}:E{len(result) + 1}",
                    field=field,
                    quote=quote,
                    source_id=str(raw.get("source_id") or "input_text"),
                    source_file=source_file,
                    start=raw.get("start") if isinstance(raw.get("start"), int) else None,
                    end=raw.get("end") if isinstance(raw.get("end"), int) else None,
                    value_index=raw.get("value_index") if isinstance(raw.get("value_index"), int) else None,
                )
            )
        return tuple(result)
