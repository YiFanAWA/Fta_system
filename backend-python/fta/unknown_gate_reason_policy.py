"""Deterministic primary-reason policy for unknown FTA gate assessments."""

from __future__ import annotations

from collections.abc import Iterable

from contracts.candidate_fta_contract import UnknownGateReasonCode


_INCOMPLETE_CHILD_BLOCKERS = frozenset(
    {
        "gate_requires_multiple_children",
        "cause_set_incomplete_or_not_leaf_normalized",
    }
)
_SCOPE_BLOCKERS = frozenset(
    {
        "gate_scope_does_not_contain_all_node_evidence",
        "gate_scope_missing_or_ambiguous",
        "gate_evidence_outside_scope",
        "gate_children_outside_scope",
    }
)
_EVIDENCE_BLOCKERS = frozenset({"gate_evidence_missing_or_ambiguous"})
_CONFIDENCE_BLOCKERS = frozenset(
    {
        "gate_confidence_tie",
        "gate_confidence_below_threshold",
        "gate_confidence_margin_below_threshold",
    }
)
_KNOWN_BLOCKERS = (
    _INCOMPLETE_CHILD_BLOCKERS
    | _SCOPE_BLOCKERS
    | _EVIDENCE_BLOCKERS
    | _CONFIDENCE_BLOCKERS
    | frozenset(
        {
            "gate_confidence_policy_unavailable",
            "model_prefers_unknown_gate",
            "no_direct_logic_evidence",
            "unresolved_structure",
        }
    )
)


def _blocker_codes(blockers: Iterable[str]) -> frozenset[str]:
    codes: set[str] = set()
    for blocker in blockers:
        if not isinstance(blocker, str):
            continue
        # Some tree blockers append a node/scope identity after a colon. Only
        # exact, registered code prefixes are recognized; prose is never parsed.
        code = blocker.split(":", 1)[0]
        if blocker in _KNOWN_BLOCKERS or code in _KNOWN_BLOCKERS:
            codes.add(code)
    return frozenset(codes)


def resolve_unknown_gate_reason(
    *,
    blockers: Iterable[str],
    confidence_reason: str,
    gate_quote_present: bool,
    gate_evidence_bound: bool,
    child_count: int,
    cause_set_complete: bool,
    cause_set_leaf_normalized: bool,
) -> UnknownGateReasonCode:
    """Choose one primary reason using a stable, fail-closed precedence.

    Precedence is: incomplete child set, scope mismatch, missing direct logic
    evidence, ambiguous/unbound evidence, unavailable policy, model uncertainty,
    then unresolved structure. Other blockers remain independently available on
    the assessment as secondary details.
    """

    if isinstance(child_count, bool) or not isinstance(child_count, int) or child_count < 1:
        raise ValueError("child_count must be a positive integer")
    if not isinstance(gate_quote_present, bool) or not isinstance(gate_evidence_bound, bool):
        raise TypeError("gate evidence state must be boolean")
    if not isinstance(cause_set_complete, bool) or not isinstance(
        cause_set_leaf_normalized, bool
    ):
        raise TypeError("cause-set state must be boolean")

    codes = _blocker_codes(blockers)
    if (
        child_count < 2
        or not cause_set_complete
        or not cause_set_leaf_normalized
        or codes & _INCOMPLETE_CHILD_BLOCKERS
    ):
        return UnknownGateReasonCode.INCOMPLETE_CHILD_SET
    if codes & _SCOPE_BLOCKERS:
        return UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY
    if not gate_quote_present:
        return UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE
    if codes & _EVIDENCE_BLOCKERS or not gate_evidence_bound:
        return UnknownGateReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS
    if confidence_reason == "gate_confidence_policy_unavailable":
        return UnknownGateReasonCode.CONFIDENCE_POLICY_UNAVAILABLE
    if confidence_reason == "model_prefers_unknown_gate":
        return UnknownGateReasonCode.MODEL_PREFERS_UNKNOWN_GATE
    if confidence_reason in _CONFIDENCE_BLOCKERS:
        return UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY
    return UnknownGateReasonCode.UNRESOLVED_STRUCTURE


def map_legacy_unknown_gate_reason(
    *, gate: str, blockers: Iterable[str]
) -> UnknownGateReasonCode | None:
    """Map historical structured blockers without guessing from free-text reasons.

    An unmapped historical ``unknown`` remains explicitly ``legacy_unspecified``.
    This helper does not rewrite historical artifacts.
    """

    if gate != "unknown":
        return None
    codes = _blocker_codes(blockers)
    if codes & _INCOMPLETE_CHILD_BLOCKERS:
        return UnknownGateReasonCode.INCOMPLETE_CHILD_SET
    if codes & _SCOPE_BLOCKERS:
        return UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY
    if codes & _EVIDENCE_BLOCKERS:
        return UnknownGateReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS
    if "no_direct_logic_evidence" in codes:
        return UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE
    if "gate_confidence_policy_unavailable" in codes:
        return UnknownGateReasonCode.CONFIDENCE_POLICY_UNAVAILABLE
    if "model_prefers_unknown_gate" in codes:
        return UnknownGateReasonCode.MODEL_PREFERS_UNKNOWN_GATE
    if codes & _CONFIDENCE_BLOCKERS:
        return UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY
    if "unresolved_structure" in codes:
        return UnknownGateReasonCode.UNRESOLVED_STRUCTURE
    return UnknownGateReasonCode.LEGACY_UNSPECIFIED


__all__ = [
    "map_legacy_unknown_gate_reason",
    "resolve_unknown_gate_reason",
]
