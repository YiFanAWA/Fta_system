"""Domain-neutral query action policy after routing and sufficiency analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QueryDecision:
    action: str
    reason: str
    route_mode: str
    sufficiency_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QueryDecisionPolicy:
    """Map analysis signals to behavior without changing retrieval ranking."""

    def decide(self, *, route_mode: str, sufficiency_level: str) -> QueryDecision:
        if route_mode not in {"scoped", "cross_domain"}:
            raise ValueError(f"unsupported route_mode: {route_mode}")
        if sufficiency_level not in {"sufficient", "partially_sufficient", "insufficient", "cannot_determine"}:
            raise ValueError(f"unsupported sufficiency_level: {sufficiency_level}")
        if sufficiency_level == "insufficient":
            return QueryDecision(
                action="clarify",
                reason="query lacks enough identity/context for a reliable retrieval decision",
                route_mode=route_mode,
                sufficiency_level=sufficiency_level,
            )
        if sufficiency_level == "sufficient" and route_mode == "scoped":
            return QueryDecision(
                action="retrieve",
                reason="query has sufficient information and an explicit retrieval scope",
                route_mode=route_mode,
                sufficiency_level=sufficiency_level,
            )
        return QueryDecision(
            action="retrieve_with_warning",
            reason="retrieval is allowed, but identity/scope or context remains incomplete",
            route_mode=route_mode,
            sufficiency_level=sufficiency_level,
        )
