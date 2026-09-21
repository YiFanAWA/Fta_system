"""Explainable domain/system routing for multi-domain retrieval.

The router is deliberately independent from the Generic Retrieval Pipeline.
It only decides whether a query has enough explicit evidence to scope the
retrieval space. No match means cross-domain retrieval, not a guessed domain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DomainScopeProfile:
    """Signals that identify one retrieval scope."""

    scope_id: str
    domain: str
    manufacturer: str = ""
    system: str = ""
    strong_terms: tuple[str, ...] = ()
    weak_terms: tuple[str, ...] = ()
    identifier_patterns: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.scope_id.strip():
            raise ValueError("scope_id must not be empty")
        if not self.domain.strip():
            raise ValueError("domain must not be empty")
        for pattern in self.identifier_patterns:
            re.compile(pattern)


@dataclass(frozen=True)
class DomainRouteDecision:
    """Inspectable result of a routing decision."""

    query: str
    selected_scope_ids: tuple[str, ...]
    mode: str
    confidence: float
    signals: tuple[str, ...]
    scores: tuple[tuple[str, float], ...]


class RuleBasedDomainRouter:
    """Route only when explicit, explainable evidence separates one scope."""

    def __init__(
        self,
        profiles: Sequence[DomainScopeProfile],
        *,
        strong_weight: float = 3.0,
        weak_weight: float = 1.0,
        minimum_score: float = 3.0,
        minimum_margin: float = 1.0,
    ) -> None:
        if not profiles:
            raise ValueError("at least one domain scope profile is required")
        self._profiles = tuple(profiles)
        seen: set[str] = set()
        for profile in self._profiles:
            profile.validate()
            if profile.scope_id in seen:
                raise ValueError(f"duplicate scope_id: {profile.scope_id}")
            seen.add(profile.scope_id)
        if strong_weight <= 0 or weak_weight <= 0:
            raise ValueError("signal weights must be positive")
        if minimum_score <= 0 or minimum_margin < 0:
            raise ValueError("routing thresholds are invalid")
        self._strong_weight = float(strong_weight)
        self._weak_weight = float(weak_weight)
        self._minimum_score = float(minimum_score)
        self._minimum_margin = float(minimum_margin)

    @property
    def profiles(self) -> tuple[DomainScopeProfile, ...]:
        return self._profiles

    def route(self, query: str) -> DomainRouteDecision:
        text = str(query or "").strip()
        if not text:
            raise ValueError("query cannot be empty")
        normalized = text.casefold()
        scored: list[tuple[str, float]] = []
        matched: dict[str, list[str]] = {}
        for profile in self._profiles:
            score = 0.0
            signals: list[str] = []
            for term in profile.strong_terms:
                cue = str(term).strip().casefold()
                if cue and cue in normalized:
                    score += self._strong_weight
                    signals.append(f"strong_term:{term}")
            for term in profile.weak_terms:
                cue = str(term).strip().casefold()
                if cue and cue in normalized:
                    score += self._weak_weight
                    signals.append(f"weak_term:{term}")
            for pattern in profile.identifier_patterns:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    score += self._strong_weight
                    signals.append(f"identifier_pattern:{pattern}")
            scored.append((profile.scope_id, score))
            if signals:
                matched[profile.scope_id] = signals

        ordered = tuple(sorted(scored, key=lambda item: (-item[1], item[0])))
        top_scope, top_score = ordered[0]
        second_score = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = top_score - second_score
        if top_score < self._minimum_score or margin < self._minimum_margin:
            return DomainRouteDecision(
                query=text,
                selected_scope_ids=tuple(profile.scope_id for profile in self._profiles),
                mode="cross_domain",
                confidence=0.0,
                signals=(),
                scores=ordered,
            )
        return DomainRouteDecision(
            query=text,
            selected_scope_ids=(top_scope,),
            mode="scoped",
            confidence=min(1.0, top_score / (top_score + second_score + 1.0)),
            signals=tuple(matched.get(top_scope, ())),
            scores=ordered,
        )
