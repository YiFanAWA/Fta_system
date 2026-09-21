"""Post-retrieval response-risk policy.

This layer does not decide retrieval scope or ranking. It controls how a
retrieved, evidence-grounded answer may be presented to the user.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ResponsePolicyDecision:
    response_policy: str
    retrieval_policy: str
    reason: str
    sufficiency_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResponsePolicyLayer:
    """Map query-analysis risk to answer behavior after retrieval."""

    def decide(self, *, sufficiency_level: str) -> ResponsePolicyDecision:
        if sufficiency_level not in {"sufficient", "partially_sufficient", "insufficient", "cannot_determine"}:
            raise ValueError(f"unsupported sufficiency_level: {sufficiency_level}")
        if sufficiency_level == "insufficient":
            return ResponsePolicyDecision(
                response_policy="clarify",
                retrieval_policy="allow",
                reason="retrieval may inform the clarification, but no definitive answer should be produced",
                sufficiency_level=sufficiency_level,
            )
        if sufficiency_level in {"partially_sufficient", "cannot_determine"}:
            return ResponsePolicyDecision(
                response_policy="warning",
                retrieval_policy="allow",
                reason="answer should state uncertainty and request missing context or domain context",
                sufficiency_level=sufficiency_level,
            )
        return ResponsePolicyDecision(
            response_policy="normal",
            retrieval_policy="allow",
            reason="query context is sufficient for a normal evidence-grounded answer",
            sufficiency_level=sufficiency_level,
        )
