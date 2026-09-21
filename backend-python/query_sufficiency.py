"""Explainable query-information sufficiency assessment.

This layer does not rank faults and does not choose a retrieval scope. It
only reports whether the query contains enough identity/context to retrieve
without an avoidable clarification request.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Sequence


_FAULT_CODE_RE = re.compile(r"\b[AFN]\d{5}\b", re.IGNORECASE)
_PARAMETER_RE = re.compile(r"\b[pr]\d{4,5}(?:\[\d+\])?\b", re.IGNORECASE)
_JASC_RE = re.compile(r"\bjasc\s*\d{4}\b", re.IGNORECASE)
_PART_NUMBER_RE = re.compile(r"\b(?:p/n|pn|part\s+number)\s*[:#-]?\s*[a-z0-9][a-z0-9./-]{2,}\b", re.IGNORECASE)

_DOMAIN_TERMS = (
    "siemens",
    "sinamics",
    "s210",
    "drive-cliq",
    "faa",
    "sdr",
    "jasc",
    "航空",
    "航空器",
    "飞机",
    "aerospace",
    "industrial drive",
)
_TECHNICAL_TERMS = (
    "fault",
    "failure",
    "alarm",
    "error",
    "故障",
    "报警",
    "异常",
    "temperature",
    "overheat",
    "voltage",
    "communication",
    "status",
    "同步",
    "温度",
    "通信",
    "过热",
)
_COMPONENT_TERMS = (
    "component",
    "module",
    "sensor",
    "encoder",
    "motor",
    "pump",
    "drive",
    "lru",
    "组件",
    "模块",
    "传感器",
    "编码器",
    "电机",
    "控制单元",
)


@dataclass(frozen=True)
class QuerySufficiencyDecision:
    query: str
    sufficiency_score: float
    level: str
    recommended_action: str
    requires_clarification: bool
    domain_confidence: float
    route_mode: str
    matched_identifiers: tuple[str, ...]
    matched_domain_terms: tuple[str, ...]
    matched_technical_terms: tuple[str, ...]
    matched_component_terms: tuple[str, ...]
    missing_information: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QuerySufficiencyEvaluator:
    """Return a conservative, auditable sufficiency decision."""

    def assess(
        self,
        query: str,
        *,
        domain_confidence: float = 0.0,
        route_mode: str = "cross_domain",
    ) -> QuerySufficiencyDecision:
        text = str(query or "").strip()
        if not text:
            raise ValueError("query cannot be empty")
        normalized = text.casefold()
        identifiers = tuple(
            dict.fromkeys(
                [
                    *(_FAULT_CODE_RE.findall(text)),
                    *(_PARAMETER_RE.findall(text)),
                    *(_JASC_RE.findall(text)),
                    *(_PART_NUMBER_RE.findall(text)),
                ]
            )
        )
        domain_terms = tuple(term for term in _DOMAIN_TERMS if term.casefold() in normalized)
        technical_terms = tuple(term for term in _TECHNICAL_TERMS if term.casefold() in normalized)
        component_terms = tuple(term for term in _COMPONENT_TERMS if term.casefold() in normalized)
        has_fault_code = bool(_FAULT_CODE_RE.search(text))
        has_identifier = bool(identifiers)
        has_context = bool(technical_terms or component_terms)

        if has_fault_code and (domain_terms or route_mode == "scoped"):
            score = 0.99
            level = "sufficient"
            reason = "explicit fault code plus domain/system evidence"
        elif has_fault_code:
            score = 0.90
            level = "sufficient"
            reason = "explicit fault code is a strong retrieval identifier"
        elif has_identifier and domain_terms and has_context:
            score = 0.95
            level = "sufficient"
            reason = "explicit identifier, domain/system evidence, and technical context"
        elif has_identifier:
            score = 0.82
            level = "partially_sufficient"
            reason = "an identifier is present but query context is limited"
        elif domain_terms and has_context:
            score = 0.72
            level = "partially_sufficient"
            reason = "domain/system and technical context are present without an exact identifier"
        elif len(technical_terms) + len(component_terms) >= 2:
            score = 0.52
            level = "partially_sufficient"
            reason = "technical context is present but identity/domain remains ambiguous"
        else:
            score = 0.10 if not has_context else 0.28
            level = "insufficient"
            reason = "query does not contain enough identity and context for reliable scoping"

        missing: list[str] = []
        if not domain_terms and route_mode != "scoped":
            missing.append("device/system/manufacturer")
        if not has_identifier:
            missing.append("fault_code_or_parameter")
        if not has_context:
            missing.append("symptom/component/condition")
        requires_clarification = level == "insufficient"
        return QuerySufficiencyDecision(
            query=text,
            sufficiency_score=score,
            level=level,
            recommended_action="clarify_before_retrieval" if requires_clarification else (
                "retrieve_with_caution" if level == "partially_sufficient" else "retrieve"
            ),
            requires_clarification=requires_clarification,
            domain_confidence=max(0.0, min(1.0, float(domain_confidence))),
            route_mode=route_mode,
            matched_identifiers=identifiers,
            matched_domain_terms=domain_terms,
            matched_technical_terms=technical_terms,
            matched_component_terms=component_terms,
            missing_information=tuple(dict.fromkeys(missing)),
            reason=reason,
        )
