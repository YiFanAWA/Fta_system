from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v19 import V18_PATH, build_manifest


class TestFtaBaselineManifestV19(unittest.TestCase):
    def test_v19_registers_xvs_screen_without_creating_cases_or_readiness(self) -> None:
        prior_hash = hashlib.sha256(V18_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")

        self.assertEqual("candidate_fta_research_baseline_v19", payload["manifest_id"])
        self.assertEqual("seen_development_only_not_final", payload["event_scope_source_screening"]["status"])
        self.assertFalse(payload["event_scope_source_screening"]["eligible_for_independent_final"])
        self.assertFalse(payload["event_scope_source_screening"]["input_packet_created"])
        self.assertFalse(payload["event_scope_source_screening"]["reference_gold_created"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual(0, payload["independent_final_validation"]["sample_count"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(prior_hash, hashlib.sha256(V18_PATH.read_bytes()).hexdigest())

    def test_v19_registers_screen_report_and_historical_v18_snapshot(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn(payload["event_scope_source_screening"]["report_path"], paths)
        self.assertIn("evaluation/quality_eval/fta_baseline_manifest_v18.json", paths)
        self.assertIn("evaluation/quality_eval/test_fta_event_scope_xvs_source_screen.py", paths)


if __name__ == "__main__":
    unittest.main()
