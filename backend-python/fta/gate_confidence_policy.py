"""Explicit confidence thresholds for proposing an FTA gate."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class GateConfidencePolicy:
    """A review-only decision policy; thresholds are never implicit defaults.

    ``basis`` is ``provisional`` until a calibration report has been reviewed.
    Provisional policies can create review candidates, never approved trees.
    """

    policy_id: str
    minimum_probability: float
    minimum_margin: float
    basis: str = "provisional"

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise ValueError("policy_id must be a non-empty string")
        for value, name in (
            (self.minimum_probability, "minimum_probability"),
            (self.minimum_margin, "minimum_margin"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.basis != "provisional":
            raise ValueError("v1 only supports provisional thresholds, not calibrated policies")
        object.__setattr__(self, "policy_id", self.policy_id.strip())

    def decide(self, probabilities: dict[str, float]) -> tuple[str, str]:
        """Return a gate only when top confidence and margin meet this policy."""
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        top_gate, top_probability = ranked[0]
        if top_probability == ranked[1][1]:
            return "unknown", "gate_confidence_tie"
        margin = top_probability - ranked[1][1]

        if top_gate == "unknown":
            return "unknown", "model_prefers_unknown_gate"
        if top_probability < self.minimum_probability:
            return "unknown", "gate_confidence_below_threshold"
        if margin < self.minimum_margin:
            return "unknown", "gate_confidence_margin_below_threshold"
        return top_gate, "gate_confidence_policy_accepted"


__all__ = ["GateConfidencePolicy"]
