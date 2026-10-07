from __future__ import annotations

import json
from pathlib import Path
import unittest

from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v1 import (
    SDK_MAX_RETRIES,
    build_prompt,
    preflight,
)


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
GOLD = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"


class TestFtaEventScopeOneShotRunner(unittest.TestCase):
    def test_prompt_is_built_from_only_validated_model_projection(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        prompt = build_prompt(model_input)

        self.assertIn("Section 5.0", prompt)
        self.assertIn("explosion or structural fragmentation of a battery module", prompt)
        self.assertNotIn("api.deepseek.com", prompt)
        self.assertNotIn("19880001643", prompt)
        self.assertNotIn("diagram_reference_gate", prompt)
        self.assertNotIn("text_authorized_gate", prompt)
        self.assertNotIn("Module structural failure", prompt)

    def test_runner_is_locked_to_one_attempt_without_sdk_retries(self) -> None:
        self.assertEqual(0, SDK_MAX_RETRIES)
        result = preflight(PACKET)
        self.assertEqual(1, result["request_count"])
        self.assertEqual(0, result["sdk_max_retries"])
        self.assertTrue(result["credential_configured"])
        self.assertEqual("api.deepseek.com", result["provider_host"])
        self.assertEqual("deepseek-flash", result["model"])
        self.assertEqual(
            ["event_scope_id", "source_segments", "top_event"],
            result["model_input_top_level_keys"],
        )

    def test_gold_is_not_loaded_as_part_of_model_projection(self) -> None:
        model_input = model_input_payload(json.loads(PACKET.read_text(encoding="utf-8")))
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        self.assertNotIn("diagram_gates", model_input)
        self.assertNotIn("text_gate_reviews", model_input)
        self.assertIn("diagram_gates", gold)
        self.assertNotIn("source_provenance", model_input)


if __name__ == "__main__":
    unittest.main()
