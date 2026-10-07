from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v18 import V17_PATH, build_manifest


class TestFtaBaselineManifestV18(unittest.TestCase):
    def test_v18_registers_contract_but_keeps_population_and_readiness_closed(self) -> None:
        previous_hash = hashlib.sha256(V17_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")

        self.assertEqual("candidate_fta_research_baseline_v18", payload["manifest_id"])
        self.assertEqual("contract_defined_not_populated", payload["event_scope_packet_contract"]["status"])
        self.assertEqual(0, payload["event_scope_packet_contract"]["input_packet_count"])
        self.assertEqual(0, payload["event_scope_packet_contract"]["reference_gold_count"])
        self.assertTrue(payload["event_scope_packet_contract"]["diagram_reference_gate_and_text_authorized_gate_are_separate"])
        self.assertFalse(payload["event_scope_packet_contract"]["model_inference_run"])
        self.assertEqual(1, payload["metadata_only_source_leads"]["lead_count"])
        self.assertEqual(0, payload["metadata_only_source_leads"]["final_eligible_count"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual(0, payload["independent_final_validation"]["sample_count"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(previous_hash, hashlib.sha256(V17_PATH.read_bytes()).hexdigest())

    def test_v18_registers_contract_schema_source_lead_and_ai_provenance(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn(payload["event_scope_packet_contract"]["input_schema_path"], paths)
        self.assertIn(payload["event_scope_packet_contract"]["reference_gold_schema_path"], paths)
        self.assertIn(payload["metadata_only_source_leads"]["report_path"], paths)
        self.assertIn("evaluation/quality_eval/fta_baseline_manifest_v17.json", paths)
        self.assertFalse(payload["scoped_readiness_assessment"]["human_expert_reviewed"])


if __name__ == "__main__":
    unittest.main()
