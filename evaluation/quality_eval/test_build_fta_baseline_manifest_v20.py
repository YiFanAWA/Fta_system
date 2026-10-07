from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v20 import V19_PATH, build_manifest


class TestFtaBaselineManifestV20(unittest.TestCase):
    def test_v20_records_one_dev_case_without_claiming_inference_or_readiness(self) -> None:
        prior_hash = hashlib.sha256(V19_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")

        self.assertEqual("candidate_fta_research_baseline_v20", payload["manifest_id"])
        self.assertEqual("v20", payload["baseline_version"])
        self.assertEqual("populated_seen_development_only", payload["event_scope_packet_contract"]["status"])
        self.assertEqual(1, payload["event_scope_packet_contract"]["input_packet_count"])
        self.assertEqual(1, payload["event_scope_packet_contract"]["reference_gold_count"])
        self.assertFalse(payload["event_scope_packet_contract"]["model_inference_run"])
        self.assertEqual(1, payload["event_scope_dev_case"]["event_scope_count"])
        self.assertEqual(7, payload["event_scope_dev_case"]["diagram_node_count"])
        self.assertEqual(3, payload["event_scope_dev_case"]["diagram_gate_count"])
        self.assertEqual({"AND": 1, "OR": 1, "unknown": 1}, payload["event_scope_packet_contract"]["text_authorized_gate_counts"])
        self.assertFalse(payload["event_scope_dev_case"]["eligible_for_independent_final"])
        self.assertFalse(payload["event_scope_dev_case"]["formal_gold"])
        self.assertIn(payload["event_scope_dev_case"]["source_cluster_id"], payload["source_cluster_allocation"]["development_clusters"])
        self.assertNotIn(payload["event_scope_dev_case"]["source_cluster_id"], payload["source_cluster_allocation"]["independent_final_validation"]["source_clusters"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual(0, payload["independent_final_validation"]["sample_count"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(prior_hash, hashlib.sha256(V19_PATH.read_bytes()).hexdigest())

    def test_v20_registers_packet_gold_source_screen_and_historical_v19(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn(payload["event_scope_packet_contract"]["dev_packet_path"], paths)
        self.assertIn(payload["event_scope_packet_contract"]["reference_gold_path"], paths)
        self.assertIn(payload["event_scope_packet_contract"]["source_screen_path"], paths)
        self.assertIn(payload["event_scope_packet_contract"]["ai_role_review_path"], paths)
        self.assertIn("evaluation/quality_eval/fta_baseline_manifest_v19.json", paths)


if __name__ == "__main__":
    unittest.main()
