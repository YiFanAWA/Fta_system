"""Conservative semantic grouping for model-produced fault records."""

from __future__ import annotations

import re
from typing import Iterable

from contracts.extraction_contract import FaultRecord


_WHITESPACE_RE = re.compile(r"\s+")


def _normalized_key(value: str) -> str:
    return _WHITESPACE_RE.sub("", value).casefold()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = _normalized_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return tuple(result)


def _components(record: FaultRecord) -> tuple[str, ...]:
    return _unique(record.related_components or ((record.component or ""),))


def _merge_components(records: Iterable[FaultRecord]) -> tuple[str, ...]:
    values: list[str] = []
    for record in records:
        values.extend(_components(record))
    return _unique(values)


def _merge_records(records: Iterable[FaultRecord]) -> FaultRecord:
    grouped = tuple(records)
    first = grouped[0]
    components = _merge_components(grouped)
    primary_components = _unique(
        record.component for record in grouped if record.component
    )
    causes = _unique(cause for record in grouped for cause in record.causes)
    parameters = _unique(parameter for record in grouped for parameter in record.parameters)
    confidence_values = [record.confidence for record in grouped if record.confidence is not None]
    confidence = max(confidence_values) if confidence_values else None
    # Multiple model items for one fault may only provide associated
    # components.  Keep the primary field empty unless all items agree on one
    # explicit primary component; the complete component context remains in
    # ``related_components``.
    component = primary_components[0] if len(primary_components) == 1 else None

    merged = FaultRecord(
        description=first.description,
        fault_code=first.fault_code,
        component=component,
        related_components=components,
        causes=causes,
        parameters=parameters,
        confidence=confidence,
    )
    # Evidence is attached after grouping, so preserve the first record identity
    # for callers that already hold the model record object.
    object.__setattr__(merged, "record_id", first.record_id)
    return merged


def group_related_fault_records(records: Iterable[FaultRecord]) -> tuple[FaultRecord, ...]:
    """Merge only same-code/same-description records split by components.

    A missing fault code is deliberately never grouped: without a stable code,
    merging two records could silently change the source meaning. Different
    descriptions are also kept separate, even when their codes match.
    """

    records = tuple(records)
    groups: dict[tuple[str, str], list[FaultRecord]] = {}

    for record in records:
        if not record.fault_code:
            continue

        key = (
            _normalized_key(record.fault_code),
            _normalized_key(record.description),
        )
        group = groups.setdefault(key, [])
        group.append(record)

    grouped_records: list[FaultRecord] = []
    for key, group in groups.items():
        if len(group) == 1:
            grouped_records.append(group[0])
        else:
            grouped_records.append(_merge_records(group))

    # Preserve the first-seen ordering across ungrouped and grouped records.
    # Model output order is part of the review experience, so do not sort by code.
    grouped_by_key = {
        (
            _normalized_key(record.fault_code or ""),
            _normalized_key(record.description),
        ): record
        for record in grouped_records
        if record.fault_code
    }
    output: list[FaultRecord] = []
    emitted_groups: set[tuple[str, str]] = set()
    for record in records:
        if not record.fault_code:
            output.append(record)
            continue
        key = (
            _normalized_key(record.fault_code),
            _normalized_key(record.description),
        )
        if key in emitted_groups:
            continue
        emitted_groups.add(key)
        output.append(grouped_by_key[key])

    return tuple(output)
