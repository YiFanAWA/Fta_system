"""Evidence-backed fault relation expansion after retrieval and reranking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from rag_contract import FaultContext, FaultRelation, FaultRelationEvidence


class FaultRelationError(ValueError):
    """Raised when a relation registry cannot be safely loaded or resolved."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in (_clean(item) for item in value) if item)


@dataclass(frozen=True)
class FaultRelationSpec:
    relation_id: str
    fault_codes: tuple[str, ...]
    relation_type: str
    query_triggers: tuple[str, ...]
    relation_note: str
    evidence: tuple[Mapping[str, str], ...]
    review_status: str


class FaultRelationRegistry:
    """Load a small, reviewed relation registry without changing retrieval."""

    def __init__(self, specs: Sequence[FaultRelationSpec] = ()) -> None:
        self._specs = tuple(specs)

    @classmethod
    def from_path(cls, path: str | Path) -> "FaultRelationRegistry":
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except OSError as exc:
            raise FaultRelationError(f"无法读取故障关系注册表：{path}") from exc
        except json.JSONDecodeError as exc:
            raise FaultRelationError(f"故障关系注册表 JSON 无法解析：{path}") from exc
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "FaultRelationRegistry":
        raw_relations = payload.get("relations")
        if not isinstance(raw_relations, list):
            raise FaultRelationError("故障关系注册表缺少 relations 列表")
        specs: list[FaultRelationSpec] = []
        seen_ids: set[str] = set()
        for raw in raw_relations:
            if not isinstance(raw, Mapping):
                raise FaultRelationError("故障关系条目必须是对象")
            relation_id = _clean(raw.get("relation_id"))
            fault_codes = tuple(code.upper() for code in _as_strings(raw.get("fault_codes")))
            relation_type = _clean(raw.get("relation_type"))
            if not relation_id or relation_id in seen_ids:
                raise FaultRelationError(f"关系 ID 缺失或重复：{relation_id}")
            if len(fault_codes) != 2 or not relation_type:
                raise FaultRelationError(f"关系条目不完整：{relation_id}")
            raw_evidence = raw.get("evidence")
            if not isinstance(raw_evidence, list) or not raw_evidence:
                raise FaultRelationError(f"关系缺少证据：{relation_id}")
            evidence: list[Mapping[str, str]] = []
            for item in raw_evidence:
                if not isinstance(item, Mapping):
                    raise FaultRelationError(f"关系证据格式错误：{relation_id}")
                evidence.append(
                    {
                        "fault_code": _clean(item.get("fault_code")).upper(),
                        "citation_id": _clean(item.get("citation_id")),
                        "field": _clean(item.get("field")),
                    }
                )
            specs.append(
                FaultRelationSpec(
                    relation_id=relation_id,
                    fault_codes=fault_codes,
                    relation_type=relation_type,
                    query_triggers=_as_strings(raw.get("query_triggers")),
                    relation_note=_clean(raw.get("relation_note")),
                    evidence=tuple(evidence),
                    review_status=_clean(raw.get("review_status")),
                )
            )
            seen_ids.add(relation_id)
        return cls(specs)

    @property
    def specs(self) -> tuple[FaultRelationSpec, ...]:
        return self._specs

    def triggered_related_codes(self, question: str, primary_fault_code: str) -> tuple[str, ...]:
        """Return registry targets before context loading, preserving registry order."""

        primary = primary_fault_code.strip().upper()
        result: list[str] = []
        seen: set[str] = set()
        for spec in self._specs:
            if primary not in spec.fault_codes:
                continue
            if not self._trigger_matches(question, spec.query_triggers):
                continue
            related = next(code for code in spec.fault_codes if code != primary)
            if related not in seen:
                result.append(related)
                seen.add(related)
        return tuple(result)

    @staticmethod
    def _trigger_matches(question: str, triggers: Iterable[str]) -> bool:
        normalized_question = " ".join(question.casefold().split())
        return any(
            trigger.casefold() in normalized_question
            for trigger in triggers
            if trigger.strip()
        )

    def expand(
        self,
        question: str,
        primary_fault_code: str,
        contexts: Sequence[FaultContext],
    ) -> tuple[FaultRelation, ...]:
        """Resolve only explicitly triggered relations with verified evidence."""

        primary = primary_fault_code.strip().upper()
        contexts_by_code = {context.fault_code.upper(): context for context in contexts}
        result: list[FaultRelation] = []
        for spec in self._specs:
            if primary not in spec.fault_codes:
                continue
            if not self._trigger_matches(question, spec.query_triggers):
                continue
            related = next(code for code in spec.fault_codes if code != primary)
            if related not in contexts_by_code:
                continue
            resolved_evidence: list[FaultRelationEvidence] = []
            for ref in spec.evidence:
                code = ref["fault_code"].upper()
                context = contexts_by_code.get(code)
                if context is None:
                    continue
                citation = next(
                    (
                        evidence
                        for evidence in context.evidence
                        if evidence.citation_id == ref["citation_id"]
                    ),
                    None,
                )
                if citation is None:
                    continue
                resolved_evidence.append(
                    FaultRelationEvidence(
                        fault_code=code,
                        citation_id=citation.citation_id,
                        field=ref["field"],
                        quote=citation.quote,
                    )
                )
            if not resolved_evidence:
                continue
            result.append(
                FaultRelation(
                    relation_id=spec.relation_id,
                    primary_fault_code=primary,
                    related_fault_code=related,
                    relation_type=spec.relation_type,
                    relation_note=spec.relation_note,
                    review_status=spec.review_status,
                    evidence=tuple(resolved_evidence),
                )
            )
        return tuple(result)
