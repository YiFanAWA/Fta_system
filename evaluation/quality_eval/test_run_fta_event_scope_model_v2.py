from __future__ import annotations

import json
from pathlib import Path
import unittest

from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import (
    MAX_TOKENS,
    RESPONSE_FORMAT,
    SDK_MAX_RETRIES,
    assess_output,
    build_prompt,
    preflight,
)


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
GOLD = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"


class TestFtaEventScopeOneShotRunnerV2(unittest.TestCase):
    def test_compact_prompt_uses_only_validated_model_projection(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        prompt = build_prompt(model_input_payload(packet))
        self.assertIn('"gates"', prompt)
        self.assertIn("Section 5.0", prompt)
        self.assertNotIn("diagram_reference_gate", prompt)
        self.assertNotIn("text_authorized_gate", prompt)
        self.assertNotIn("Module structural failure", prompt)
        self.assertNotIn("19880001643", prompt)

    def test_preflight_locks_one_json_mode_request_with_larger_budget(self) -> None:
        result = preflight(PACKET)
        self.assertEqual(8192, MAX_TOKENS)
        self.assertEqual({"type": "json_object"}, RESPONSE_FORMAT)
        self.assertEqual(0, SDK_MAX_RETRIES)
        self.assertEqual(1, result["request_count"])
        self.assertEqual(0, result["sdk_max_retries"])
        self.assertTrue(result["credential_configured"])
        self.assertEqual("api.deepseek.com", result["provider_host"])
        self.assertEqual("deepseek-flash", result["model"])
        self.assertEqual({"type": "json_object"}, result["response_format"])

    def test_offline_assessment_checks_quotes_without_gold_comparison(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        output = {
            "request": {"finish_reason": "stop"},
            "model_output": {
                "parsed_json": {
                    "nodes": [
                        {"id": "E1", "evidence_quote": "the explosion or structural fragmentation of a battery module"},
                        {"id": "E2", "evidence_quote": "one or more cells in the battery pack"},
                    ],
                    "gates": [
                        {"output_node_id": "E1", "child_node_ids": ["E2", "E3"], "gate": "OR", "evidence_quote": "one or more cells"}
                    ],
                }
            },
        }
        assessment = assess_output(output, model_input)
        self.assertIn("gate_references_unknown_node", assessment["structural_errors"])
        self.assertEqual(0, assessment["invalid_quotes"])
        self.assertEqual("not_performed", assessment["gold_comparison"])
        self.assertFalse(assessment["accuracy_or_calibration_claim_allowed"])
        self.assertIn("diagram_gates", gold)

    def test_truncated_response_never_counts_as_usable(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        output = {
            "request": {"finish_reason": "length"},
            "model_output": {"parsed_json": {"nodes": [], "gates": []}},
        }
        assessment = assess_output(output, model_input_payload(packet))
        self.assertEqual("truncated", assessment["assessment_status"])

if __name__ == "__main__":
    unittest.main()
