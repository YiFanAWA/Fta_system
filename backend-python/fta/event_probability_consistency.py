"""Post-structure FTA probability consistency checks; never infer a gate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence


class ProbabilityConsistencyStatus(str, Enum):
    NOT_EVALUATED = "not_evaluated"
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"


@dataclass(frozen=True)
class EventOccurrenceProbability:
    event_id: str
    probability: float
    source_id: str
    observation_window: str
    observation_count: int

    def __post_init__(self) -> None:
        for value, name in (
            (self.event_id, "event_id"),
            (self.source_id, "source_id"),
            (self.observation_window, "observation_window"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.probability, bool) or not isinstance(self.probability, (int, float)):
            raise TypeError("probability must be numeric")
        if not math.isfinite(float(self.probability)) or not 0.0 <= float(self.probability) <= 1.0:
            raise ValueError("probability must be finite and in [0, 1]")
        if (
            isinstance(self.observation_count, bool)
            or not isinstance(self.observation_count, int)
            or self.observation_count <= 0
        ):
            raise ValueError("observation_count must be a positive integer")
        object.__setattr__(self, "probability", float(self.probability))


@dataclass(frozen=True)
class ProbabilityConsistencyResult:
    status: ProbabilityConsistencyStatus
    reason: str
    gate: str
    gate_structure_id: str | None
    independence_evidence_id: str | None = None
    calculated_parent_probability: float | None = None
    observed_parent_probability: float | None = None
    absolute_difference: float | None = None
    tolerance: float | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "gate": self.gate,
            "gate_structure_id": self.gate_structure_id,
            "independence_evidence_id": self.independence_evidence_id,
            "calculated_parent_probability": self.calculated_parent_probability,
            "observed_parent_probability": self.observed_parent_probability,
            "absolute_difference": self.absolute_difference,
            "tolerance": self.tolerance,
            "may_change_gate": False,
        }


def check_event_probability_consistency(
    *,
    gate: str,
    gate_structure_confirmed: bool,
    gate_structure_id: str | None,
    child_probabilities: Sequence[EventOccurrenceProbability],
    observed_parent_probability: EventOccurrenceProbability | None,
    events_independent: bool | None,
    independence_evidence_id: str | None,
    tolerance: float,
) -> ProbabilityConsistencyResult:
    """Compare gate-implied probability to observations after structure review.

    The independence formulas are applied only when independence is explicitly
    supported and every event uses the same observation window. A mismatch is
    a consistency warning, not evidence for switching AND/OR.
    """
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise TypeError("tolerance must be numeric")
    if not math.isfinite(float(tolerance)) or not 0.0 <= float(tolerance) <= 1.0:
        raise ValueError("tolerance must be finite and in [0, 1]")
    if gate not in {"AND", "OR", "unknown"}:
        raise ValueError("gate must be AND, OR, or unknown")
    if not isinstance(gate_structure_confirmed, bool):
        raise TypeError("gate_structure_confirmed must be a boolean")
    if events_independent is not None and not isinstance(events_independent, bool):
        raise TypeError("events_independent must be a boolean or None")
    if independence_evidence_id is not None and (
        not isinstance(independence_evidence_id, str)
        or not independence_evidence_id.strip()
    ):
        raise ValueError("independence_evidence_id must be a non-empty string when provided")

    if not gate_structure_confirmed or not gate_structure_id:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "gate_structure_not_confirmed",
            independence_evidence_id=independence_evidence_id,
        )
    if gate == "unknown":
        return _not_evaluated(
            gate,
            gate_structure_id,
            "unknown_gate_has_no_probability_formula",
            independence_evidence_id=independence_evidence_id,
        )
    if events_independent is not True:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "event_independence_not_established",
            independence_evidence_id=independence_evidence_id,
        )
    if independence_evidence_id is None:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "independence_evidence_reference_missing",
            independence_evidence_id=independence_evidence_id,
        )
    if not isinstance(child_probabilities, Sequence) or isinstance(child_probabilities, (str, bytes)):
        raise TypeError("child_probabilities must be a sequence")
    if len(child_probabilities) < 2:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "fewer_than_two_child_probabilities",
            independence_evidence_id=independence_evidence_id,
        )
    if observed_parent_probability is None:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "observed_parent_probability_missing",
            independence_evidence_id=independence_evidence_id,
        )
    all_events = (*child_probabilities, observed_parent_probability)
    if not all(isinstance(item, EventOccurrenceProbability) for item in all_events):
        raise TypeError("event probabilities must be EventOccurrenceProbability values")
    if len({item.event_id for item in child_probabilities}) != len(child_probabilities):
        raise ValueError("child event IDs must be unique")
    if observed_parent_probability.event_id in {item.event_id for item in child_probabilities}:
        raise ValueError("parent event ID must differ from every child event ID")
    if len({item.source_id for item in all_events}) != 1:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "probability_sources_do_not_match",
            independence_evidence_id=independence_evidence_id,
        )
    windows = {item.observation_window for item in all_events}
    if len(windows) != 1:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "observation_windows_do_not_match",
            independence_evidence_id=independence_evidence_id,
        )
    if len({item.observation_count for item in all_events}) != 1:
        return _not_evaluated(
            gate,
            gate_structure_id,
            "observation_counts_do_not_match",
            independence_evidence_id=independence_evidence_id,
        )

    probabilities = [item.probability for item in child_probabilities]
    if gate == "AND":
        calculated = math.prod(probabilities)
    else:
        calculated = 1.0 - math.prod(1.0 - probability for probability in probabilities)
    difference = abs(calculated - observed_parent_probability.probability)
    status = (
        ProbabilityConsistencyStatus.CONSISTENT
        if difference <= float(tolerance)
        else ProbabilityConsistencyStatus.INCONSISTENT
    )
    return ProbabilityConsistencyResult(
        status=status,
        reason="independence_formula_within_tolerance" if status is ProbabilityConsistencyStatus.CONSISTENT else "observed_rate_differs_from_gate_formula",
        gate=gate,
        gate_structure_id=gate_structure_id,
        independence_evidence_id=independence_evidence_id,
        calculated_parent_probability=calculated,
        observed_parent_probability=observed_parent_probability.probability,
        absolute_difference=difference,
        tolerance=float(tolerance),
    )


def _not_evaluated(
    gate: str,
    gate_structure_id: str | None,
    reason: str,
    *,
    independence_evidence_id: str | None = None,
) -> ProbabilityConsistencyResult:
    return ProbabilityConsistencyResult(
        status=ProbabilityConsistencyStatus.NOT_EVALUATED,
        reason=reason,
        gate=gate,
        gate_structure_id=gate_structure_id,
        independence_evidence_id=independence_evidence_id,
    )


__all__ = [
    "EventOccurrenceProbability",
    "ProbabilityConsistencyResult",
    "ProbabilityConsistencyStatus",
    "check_event_probability_consistency",
]
