"""Common fault entity contracts shared by domain adapters and retrieval."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


_ID_PART_RE = re.compile(r"[^a-z0-9]+")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _unique_strings(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _clean(value)
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return tuple(result)


def canonical_id_part(value: str) -> str:
    """Return a stable, readable identity component."""

    normalized = _ID_PART_RE.sub("-", _clean(value).casefold()).strip("-")
    return normalized or "unknown"


def build_fault_entity_id(
    *, domain: str, manufacturer: str, system: str, fault_code: str
) -> str:
    code = _clean(fault_code).upper()
    if not code:
        raise ValueError("fault_code is required for entity identity")
    return ":".join(
        [
            canonical_id_part(domain),
            canonical_id_part(manufacturer),
            canonical_id_part(system),
            code,
        ]
    )


@dataclass(frozen=True)
class FaultEvidence:
    evidence_id: str
    field: str
    quote: str
    source_id: str = ""
    source_file: str = ""
    start: int | None = None
    end: int | None = None
    value_index: int | None = None


@dataclass(frozen=True)
class FaultRelation:
    relation_type: str
    target_entity_id: str
    source: str = ""
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = None
    review_status: str = "unknown"


@dataclass(frozen=True)
class FaultEntity:
    """Domain-neutral fault record.

    Domain-specific fields must remain in ``domain_specific``.  The core
    identity deliberately includes domain, manufacturer, system and code so a
    code such as F30002 cannot collide across manuals or manufacturers.
    """

    entity_id: str
    domain: str
    manufacturer: str
    system: str
    fault_code: str
    description: str
    symptoms: tuple[str, ...] = ()
    causes: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()
    components: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    remedies: tuple[str, ...] = ()
    relations: tuple[FaultRelation, ...] = ()
    evidence: tuple[FaultEvidence, ...] = ()
    raw_text: str = ""
    domain_specific: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        required = {
            "entity_id": self.entity_id,
            "domain": self.domain,
            "manufacturer": self.manufacturer,
            "system": self.system,
            "fault_code": self.fault_code,
            "description": self.description,
        }
        missing = [name for name, value in required.items() if not _clean(value)]
        if missing:
            raise ValueError(f"fault entity missing required fields: {', '.join(missing)}")
        if self.entity_id != build_fault_entity_id(
            domain=self.domain,
            manufacturer=self.manufacturer,
            system=self.system,
            fault_code=self.fault_code,
        ):
            raise ValueError("entity_id does not match the common identity contract")
        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("fault evidence ids must be unique within an entity")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def normalize_fault_entity(entity: FaultEntity) -> FaultEntity:
    """Normalize collections without changing their semantic values."""

    normalized = FaultEntity(
        entity_id=build_fault_entity_id(
            domain=entity.domain,
            manufacturer=entity.manufacturer,
            system=entity.system,
            fault_code=entity.fault_code,
        ),
        domain=_clean(entity.domain),
        manufacturer=_clean(entity.manufacturer),
        system=_clean(entity.system),
        fault_code=_clean(entity.fault_code).upper(),
        description=_clean(entity.description),
        symptoms=_unique_strings(entity.symptoms),
        causes=_unique_strings(entity.causes),
        effects=_unique_strings(entity.effects),
        components=_unique_strings(entity.components),
        parameters=_unique_strings(entity.parameters),
        remedies=_unique_strings(entity.remedies),
        relations=tuple(entity.relations),
        evidence=tuple(entity.evidence),
        raw_text=_clean(entity.raw_text),
        domain_specific=dict(entity.domain_specific),
    )
    normalized.validate()
    return normalized
