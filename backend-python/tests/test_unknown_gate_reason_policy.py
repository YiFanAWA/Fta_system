import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.candidate_fta_contract import UnknownGateReasonCode
from fta.unknown_gate_reason_policy import (
    map_legacy_unknown_gate_reason,
    resolve_unknown_gate_reason,
)


class UnknownGateReasonPolicyTests(unittest.TestCase):
    def _resolve(self, **overrides):
        inputs = {
            "blockers": (),
            "confidence_reason": "gate_confidence_policy_accepted",
            "gate_quote_present": True,
            "gate_evidence_bound": True,
            "child_count": 2,
            "cause_set_complete": True,
            "cause_set_leaf_normalized": True,
        }
        inputs.update(overrides)
        return resolve_unknown_gate_reason(**inputs)

    def test_incomplete_child_set_has_primary_precedence(self):
        result = self._resolve(
            blockers=("cause_set_incomplete_or_not_leaf_normalized",),
            confidence_reason="gate_confidence_policy_unavailable",
            gate_quote_present=False,
            gate_evidence_bound=False,
            cause_set_complete=False,
        )
        self.assertEqual(UnknownGateReasonCode.INCOMPLETE_CHILD_SET, result)

    def test_scope_mismatch_precedes_evidence_and_confidence_reasons(self):
        result = self._resolve(
            blockers=(
                "gate_evidence_outside_scope",
                "gate_evidence_missing_or_ambiguous",
                "gate_confidence_policy_unavailable",
            ),
            confidence_reason="gate_confidence_policy_unavailable",
            gate_evidence_bound=False,
        )
        self.assertEqual(UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY, result)

    def test_missing_quote_is_not_confused_with_ambiguous_quote(self):
        result = self._resolve(
            blockers=("gate_evidence_missing_or_ambiguous",),
            gate_quote_present=False,
            gate_evidence_bound=False,
        )
        self.assertEqual(UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE, result)

        result = self._resolve(
            blockers=("gate_evidence_missing_or_ambiguous",),
            gate_quote_present=True,
            gate_evidence_bound=False,
        )
        self.assertEqual(UnknownGateReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS, result)

    def test_policy_reasons_are_mapped_without_reading_free_text(self):
        expected = {
            "gate_confidence_policy_unavailable": UnknownGateReasonCode.CONFIDENCE_POLICY_UNAVAILABLE,
            "model_prefers_unknown_gate": UnknownGateReasonCode.MODEL_PREFERS_UNKNOWN_GATE,
            "gate_confidence_tie": UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY,
            "gate_confidence_below_threshold": UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY,
            "gate_confidence_margin_below_threshold": UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY,
        }
        for policy_reason, expected_reason in expected.items():
            with self.subTest(policy_reason=policy_reason):
                self.assertEqual(
                    expected_reason,
                    self._resolve(confidence_reason=policy_reason),
                )

    def test_unmapped_current_reason_fails_closed_as_unresolved_structure(self):
        self.assertEqual(
            UnknownGateReasonCode.UNRESOLVED_STRUCTURE,
            self._resolve(confidence_reason="unexpected_policy_state"),
        )

    def test_legacy_mapping_uses_known_blocker_codes_and_never_guesses(self):
        cases = (
            (("gate_requires_multiple_children",), UnknownGateReasonCode.INCOMPLETE_CHILD_SET),
            (("cause_set_incomplete_or_not_leaf_normalized",), UnknownGateReasonCode.INCOMPLETE_CHILD_SET),
            (("gate_scope_does_not_contain_all_node_evidence:gate-2",), UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY),
            (("gate_scope_missing_or_ambiguous:gate-3",), UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY),
            (("gate_evidence_outside_scope:gate-4",), UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY),
            (("gate_children_outside_scope",), UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY),
            (("gate_evidence_missing_or_ambiguous",), UnknownGateReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS),
            (("no_direct_logic_evidence",), UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE),
            (("gate_confidence_policy_unavailable",), UnknownGateReasonCode.CONFIDENCE_POLICY_UNAVAILABLE),
            (("model_prefers_unknown_gate",), UnknownGateReasonCode.MODEL_PREFERS_UNKNOWN_GATE),
            (("gate_confidence_tie",), UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY),
            (("gate_confidence_below_threshold",), UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY),
            (("gate_confidence_margin_below_threshold",), UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY),
            (("unresolved_structure",), UnknownGateReasonCode.UNRESOLVED_STRUCTURE),
            (("unrecognized old blocker",), UnknownGateReasonCode.LEGACY_UNSPECIFIED),
            ((), UnknownGateReasonCode.LEGACY_UNSPECIFIED),
        )
        for blockers, expected_reason in cases:
            with self.subTest(blockers=blockers):
                self.assertEqual(
                    expected_reason,
                    map_legacy_unknown_gate_reason(gate="unknown", blockers=blockers),
                )

    def test_legacy_non_unknown_gate_does_not_receive_unknown_reason(self):
        for gate in ("AND", "OR", "not_applicable"):
            with self.subTest(gate=gate):
                self.assertIsNone(
                    map_legacy_unknown_gate_reason(gate=gate, blockers=())
                )


if __name__ == "__main__":
    unittest.main()
