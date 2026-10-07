from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v17 import V16_PATH, build_manifest


class TestFtaBaselineManifestV17(unittest.TestCase):
    def test_v17_records_seen_sources_as_development_only_and_keeps_final_uncreated(self) -> None:
        before = hashlib.sha256(V16_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        screen = payload["source_screen"]

        self.assertEqual("candidate_fta_research_baseline_v17", payload["manifest_id"])
        self.assertEqual(4, screen["screened_document_count"])
        self.assertEqual(2, screen["seen_development_only_source_count"])
        self.assertEqual(0, screen["blind_final_eligible_source_count"])
        self.assertTrue(screen["evaluation_adapter_required"])
        self.assertFalse(screen["model_inference_run"])
        self.assertFalse(screen["final_dataset_created"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual(0, payload["independent_final_validation"]["sample_count"])
        self.assertEqual([], payload["source_cluster_allocation"]["independent_final_validation"]["source_clusters"])
        self.assertEqual(0, payload["source_cluster_allocation"]["screened_blind_final_eligible_count"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(before, hashlib.sha256(V16_PATH.read_bytes()).hexdigest())

    def test_v17_registers_screen_report_and_preserves_non_human_provenance(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn(payload["source_screen"]["report_path"], paths)
        self.assertIn("evaluation/quality_eval/fta_baseline_manifest_v16.json", paths)
        self.assertFalse(payload["scoped_readiness_assessment"]["human_expert_reviewed"])
        self.assertFalse(payload["independent_final_validation"].get("model_inference_run", False))


if __name__ == "__main__":
    unittest.main()
