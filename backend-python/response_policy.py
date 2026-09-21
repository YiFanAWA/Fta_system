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


@dataclass(frozen=True)
class ResponsePolicyV2Decision:
    """Structured answer contract for the v2 policy Gold."""

    policy: str
    answer_allowed: bool
    confidence_level: str
    need_additional_info: bool
    warning_required: bool
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

    def decide_v2(self, *, sufficiency_level: str) -> ResponsePolicyV2Decision:
        """Return an explicit answer-allowed/confidence contract.

        Retrieval remains allowed for every policy.  The v2 fields only control
        whether and how a definitive answer may be presented.
        """

        if sufficiency_level not in {"sufficient", "partially_sufficient", "insufficient", "cannot_determine"}:
            raise ValueError(f"unsupported sufficiency_level: {sufficiency_level}")
        if sufficiency_level == "insufficient":
            return ResponsePolicyV2Decision(
                policy="P2_ASK_BEFORE_DEFINITIVE_ANSWER",
                answer_allowed=False,
                confidence_level="low",
                need_additional_info=True,
                warning_required=False,
                retrieval_policy="allow",
                reason="retrieve candidates if useful, then ask for missing context before a definitive answer",
                sufficiency_level=sufficiency_level,
            )
        if sufficiency_level in {"partially_sufficient", "cannot_determine"}:
            return ResponsePolicyV2Decision(
                policy="P1_ANSWER_WITH_WARNING",
                answer_allowed=True,
                confidence_level="medium",
                need_additional_info=True,
                warning_required=True,
                retrieval_policy="allow",
                reason="answer from evidence with reduced certainty and request missing context",
                sufficiency_level=sufficiency_level,
            )
        return ResponsePolicyV2Decision(
            policy="P0_DIRECT_ANSWER",
            answer_allowed=True,
            confidence_level="high",
            need_additional_info=False,
            warning_required=False,
            retrieval_policy="allow",
            reason="query context is sufficient for a direct evidence-grounded answer",
            sufficiency_level=sufficiency_level,
        )
