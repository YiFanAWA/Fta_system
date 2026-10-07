import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fta.event_probability_consistency import (
    EventOccurrenceProbability,
    ProbabilityConsistencyStatus,
    check_event_probability_consistency,
)


class EventProbabilityConsistencyTests(unittest.TestCase):
    @staticmethod
    def _event(event_id, probability, *, window="2026-Q1", source="maintenance-rate-report-v1"):
        return EventOccurrenceProbability(
            event_id=event_id,
            probability=probability,
            source_id=source,
            observation_window=window,
            observation_count=1000,
        )

    def _check(self, gate, children, parent, **overrides):
        values = {
            "gate": gate,
            "gate_structure_confirmed": True,
            "gate_structure_id": "reviewed-tree-1",
            "child_probabilities": children,
            "observed_parent_probability": parent,
            "events_independent": True,
            "independence_evidence_id": "reviewed-independence-assessment-1",
            "tolerance": 0.02,
        }
        values.update(overrides)
        return check_event_probability_consistency(**values)

    def test_probability_is_not_consulted_before_gate_structure_is_confirmed(self):
        result = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.28),
            gate_structure_confirmed=False,
            gate_structure_id=None,
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, result.status)
        self.assertEqual("gate_structure_not_confirmed", result.reason)
        self.assertFalse(result.to_payload()["may_change_gate"])

    def test_or_gate_probability_uses_independent_event_formula(self):
        result = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.29),
        )
        self.assertEqual(ProbabilityConsistencyStatus.CONSISTENT, result.status)
        self.assertAlmostEqual(0.28, result.calculated_parent_probability)
        self.assertAlmostEqual(0.01, result.absolute_difference)

    def test_and_gate_probability_uses_independent_event_formula(self):
        result = self._check(
            "AND",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.02),
        )
        self.assertEqual(ProbabilityConsistencyStatus.CONSISTENT, result.status)
        self.assertAlmostEqual(0.02, result.calculated_parent_probability)

    def test_mismatch_is_reported_without_rewriting_gate(self):
        result = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.6),
            tolerance=0.05,
        )
        self.assertEqual(ProbabilityConsistencyStatus.INCONSISTENT, result.status)
        self.assertEqual("OR", result.gate)
        self.assertFalse(result.to_payload()["may_change_gate"])

    def test_dependent_events_are_not_evaluated_with_independence_formula(self):
        result = self._check(
            "AND",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.02),
            events_independent=None,
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, result.status)
        self.assertEqual("event_independence_not_established", result.reason)

    def test_independence_claim_requires_a_reviewable_evidence_reference(self):
        result = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.28),
            independence_evidence_id=None,
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, result.status)
        self.assertEqual("independence_evidence_reference_missing", result.reason)

    def test_probabilities_from_different_sources_are_not_compared(self):
        result = self._check(
            "OR",
            (
                self._event("C1", 0.1),
                self._event("C2", 0.2, source="different-report-v1"),
            ),
            self._event("TOP", 0.28),
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, result.status)
        self.assertEqual("probability_sources_do_not_match", result.reason)

    def test_unknown_gate_and_mismatched_observation_window_are_not_evaluated(self):
        unknown = self._check(
            "unknown",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            self._event("TOP", 0.2),
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, unknown.status)
        mismatched = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2, window="2025-Q4")),
            self._event("TOP", 0.28),
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, mismatched.status)
        self.assertEqual("observation_windows_do_not_match", mismatched.reason)

    def test_different_observation_counts_are_not_compared(self):
        result = self._check(
            "OR",
            (self._event("C1", 0.1), self._event("C2", 0.2)),
            EventOccurrenceProbability(
                event_id="TOP",
                probability=0.28,
                source_id="maintenance-rate-report-v1",
                observation_window="2026-Q1",
                observation_count=500,
            ),
        )
        self.assertEqual(ProbabilityConsistencyStatus.NOT_EVALUATED, result.status)
        self.assertEqual("observation_counts_do_not_match", result.reason)

    def test_invalid_probability_is_rejected(self):
        with self.assertRaises(ValueError):
            self._event("C1", float("nan"))


if __name__ == "__main__":
    unittest.main()
