"""FAA Service Difficulty Report adapter for the common fault contracts.

This adapter is intentionally an adapter-only Phase G implementation.  It
does not add aerospace branches to the generic retriever and it does not
claim that a public SDR row is an expert-verified fault label.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from contracts.common_fault_schema import (
    FaultEntity,
    FaultEvidence,
    build_fault_entity_id,
    normalize_fault_entity,
)
from contracts.domain_adapter_contract import ExactFieldMatches, RetrievalChunk, RetrievalFieldValues


_CA_RE = re.compile(r"(?is)\bC/A\s*:\s*(?P<text>.+)$")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _non_placeholder(value: Any) -> str:
    value = _text(value)
    return "" if value.casefold() in {"unknown", "n/a", "na", "none", "null", "-"} else value


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = _text(value)
        if value and value.casefold() not in seen:
            result.append(value)
            seen.add(value.casefold())
    return tuple(result)


class FaaSdrAerospaceAdapter:
    """Map public FAA SDR rows into ``FaultEntity`` without expert claims.

    FAA SDR has no native fault-code column.  The source's
    ``OperatorControlNumber`` is therefore used in the required common
    ``fault_code`` identity slot and explicitly marked as a record identifier
    in ``domain_specific``.  ``JASCCode`` is exposed as the adapter's exact
    aerospace identifier for retrieval and is never silently promoted to a
    unique fault entity.
    """

    domain = "aerospace"
    manufacturer = "FAA_SDR"
    system = "service_difficulty_report"

    def __init__(self) -> None:
        self._known_record_ids: set[str] = set()
        self._known_jasc_codes: set[str] = set()
        self._known_part_numbers: set[str] = set()
        self._known_components: set[str] = set()

    def parse_source(self, payload: dict[str, Any]) -> tuple[FaultEntity, ...]:
        if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
            raise ValueError("FAA SDR payload must contain a samples list")

        entities: list[FaultEntity] = []
        for sample in payload["samples"]:
            if not isinstance(sample, dict):
                continue
            row = sample.get("raw_record")
            if not isinstance(row, dict):
                continue
            record_id = _text(row.get("OperatorControlNumber"))
            jasc = _text(row.get("JASCCode"))
            discrepancy = _text(row.get("Discrepancy"))
            if not record_id or not jasc or not discrepancy:
                continue
            entity = self._entity_from_sample(sample, row, record_id, jasc, discrepancy)
            entities.append(entity)
            self._known_record_ids.add(record_id.upper())
            self._known_jasc_codes.add(jasc.upper())
            for value in entity.parameters:
                self._known_part_numbers.add(value.upper())
            self._known_components.update(value.upper() for value in entity.components)

        if not entities:
            raise ValueError("FAA SDR payload produced no valid entities")
        return tuple(entities)

    def parse_file(self, path: str | Path) -> tuple[FaultEntity, ...]:
        import json

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.parse_source(payload)

    def normalize_entity(self, entity: FaultEntity) -> FaultEntity:
        return normalize_fault_entity(entity)

    def build_retrieval_chunks(
        self, entities: Sequence[FaultEntity]
    ) -> tuple[RetrievalChunk, ...]:
        chunks: list[RetrievalChunk] = []
        for entity in entities:
            values = self.retrieval_field_values(entity)
            fields = (
                ("description", values.semantic_primary),
                ("condition", " | ".join(entity.symptoms)),
                ("remedy", values.semantic_auxiliary),
                (
                    "full",
                    "\n".join(
                        value
                        for value in (
                            values.semantic_primary,
                            values.semantic_cause,
                            values.semantic_auxiliary,
                            " | ".join(entity.components),
                            " | ".join(entity.parameters),
                        )
                        if value.strip()
                    ),
                ),
            )
            for kind, text in fields:
                if not text.strip():
                    continue
                chunks.append(
                    RetrievalChunk(
                        chunk_id=f"{entity.entity_id}:{kind}",
                        entity_id=entity.entity_id,
                        kind=kind,
                        text=text.strip(),
                        metadata={
                            "fault_code": entity.fault_code,
                            "jasc_code": entity.domain_specific.get("jasc_code", ""),
                            "domain": entity.domain,
                        },
                    )
                )
        return tuple(chunks)

    def extract_exact_fields(self, question: str) -> ExactFieldMatches:
        text = _text(question).upper()

        def present(value: str) -> bool:
            if not value:
                return False
            if re.fullmatch(r"[A-Z0-9]+", value):
                return re.search(rf"(?<![A-Z0-9]){re.escape(value)}(?![A-Z0-9])", text) is not None
            return value in text

        fault_codes = tuple(
            sorted(
                {
                    value
                    for value in (*self._known_jasc_codes, *self._known_record_ids)
                    if present(value)
                }
            )
        )
        parameters = tuple(sorted(value for value in self._known_part_numbers if present(value)))
        components = tuple(sorted(value for value in self._known_components if present(value)))
        return ExactFieldMatches(
            fault_codes=fault_codes,
            parameters=parameters,
            components=components,
        )

    def retrieval_field_values(self, entity: FaultEntity) -> RetrievalFieldValues:
        jasc = _text(entity.domain_specific.get("jasc_code"))
        return RetrievalFieldValues(
            semantic_primary=entity.description,
            semantic_cause=" ".join(entity.causes),
            semantic_auxiliary=" ".join(entity.remedies),
            exact_identifier=jasc,
            exact_parameters=entity.parameters,
            metadata={
                "component": entity.domain_specific.get("component", ""),
                "aircraft_make": entity.domain_specific.get("aircraft_make", ""),
                "aircraft_model": entity.domain_specific.get("aircraft_model", ""),
                "jasc_code": jasc,
                "source_record_id": entity.fault_code,
            },
            reranker_fields=(
                ("Source record", (entity.fault_code,)),
                ("JASC code", (jasc,)),
                ("Aircraft", (_text(entity.domain_specific.get("aircraft_model")),)),
                ("Component", entity.components),
                ("Part numbers", entity.parameters),
                ("Description", (entity.description,)),
                ("Condition", entity.symptoms),
                ("Remedy", entity.remedies),
            ),
        )

    def _entity_from_sample(
        self,
        sample: Mapping[str, Any],
        row: Mapping[str, Any],
        record_id: str,
        jasc: str,
        discrepancy: str,
    ) -> FaultEntity:
        part_name = _non_placeholder(row.get("PartName"))
        component_name = _non_placeholder(row.get("ComponentName"))
        components = _unique((component_name, part_name))
        part_numbers = _unique(
            (
                _non_placeholder(row.get("PartNumber")),
                _non_placeholder(row.get("ComponentPartNumber")),
            )
        )
        condition = _non_placeholder(row.get("PartCondition"))
        remedies = self._remedies(discrepancy)
        source_text = _text(sample.get("input_text")) or self._source_text(row)
        evidence = self._evidence(row, source_text, record_id, discrepancy, components, part_numbers, remedies)
        entity = FaultEntity(
            entity_id=build_fault_entity_id(
                domain=self.domain,
                manufacturer=self.manufacturer,
                system=self.system,
                fault_code=record_id,
            ),
            domain=self.domain,
            manufacturer=self.manufacturer,
            system=self.system,
            fault_code=record_id,
            description=discrepancy,
            symptoms=(condition,) if condition else (),
            components=components,
            parameters=part_numbers,
            remedies=remedies,
            evidence=evidence,
            raw_text=source_text,
            domain_specific={
                "source_id": "faa_sdr_2024",
                "source_record_id": record_id,
                "identifier_kind": "operator_control_number",
                "native_fault_code_present": False,
                "jasc_code": jasc,
                "component": component_name,
                "aircraft_make": _text(row.get("AircraftMake")),
                "aircraft_model": _text(row.get("AircraftModel")),
                "stage_of_operation_code": _text(row.get("StageOfOperationCode")),
                "how_discovered_code": _text(row.get("HowDiscoveredCode")),
                "nature_of_condition_codes": [
                    value
                    for value in (_text(row.get("NatureOfConditionA")), _text(row.get("NatureOfConditionB")), _text(row.get("NatureOfConditionC")))
                    if value
                ],
                "precautionary_procedure_codes": [
                    value
                    for value in (
                        _text(row.get("PrecautionaryProcedureA")),
                        _text(row.get("PrecautionaryProcedureB")),
                        _text(row.get("PrecautionaryProcedureC")),
                        _text(row.get("PrecautionaryProcedureD")),
                    )
                    if value
                ],
                "part_name": part_name,
                "part_condition": condition,
                "part_location": _text(row.get("PartLocation")),
                "raw_record": dict(row),
                "source_sample_id": _text(sample.get("sample_id")),
            },
        )
        return normalize_fault_entity(entity)

    @staticmethod
    def _remedies(discrepancy: str) -> tuple[str, ...]:
        match = _CA_RE.search(discrepancy)
        if not match:
            return ()
        value = re.split(r"\s*\((?:LP|FC|TSN|CSN)\s*:", match.group("text"), maxsplit=1)[0].strip(" .")
        return (value,) if value else ()

    @staticmethod
    def _source_text(row: Mapping[str, Any]) -> str:
        names = (
            "OperatorControlNumber",
            "JASCCode",
            "AircraftMake",
            "AircraftModel",
            "PartName",
            "PartNumber",
            "PartCondition",
            "ComponentName",
            "ComponentPartNumber",
            "Discrepancy",
        )
        return "\n".join(f"{name}: {_text(row.get(name))}" for name in names if _text(row.get(name)))

    @staticmethod
    def _evidence(
        row: Mapping[str, Any],
        source_text: str,
        record_id: str,
        discrepancy: str,
        components: Sequence[str],
        parameters: Sequence[str],
        remedies: Sequence[str],
    ) -> tuple[FaultEvidence, ...]:
        requested = [
            ("identifier", record_id),
            ("jasc_code", _text(row.get("JASCCode"))),
            ("description", discrepancy),
        ]
        requested.extend(("component", value) for value in components)
        requested.extend(("parameter", value) for value in parameters)
        requested.extend(("remedy", value) for value in remedies)
        result: list[FaultEvidence] = []
        cursor = 0
        for field, quote in requested:
            quote = _text(quote)
            if not quote:
                continue
            start = source_text.find(quote, cursor)
            if start < 0:
                start = source_text.find(quote)
            if start < 0:
                continue
            end = start + len(quote)
            result.append(
                FaultEvidence(
                    evidence_id=f"{record_id}:E{len(result) + 1}",
                    field=field,
                    quote=quote,
                    source_id="faa_sdr_2024",
                    source_file="SDR-2024.csv",
                    start=start,
                    end=end,
                )
            )
            cursor = end
        return tuple(result)


__all__ = ["FaaSdrAerospaceAdapter"]
