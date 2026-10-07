from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v24 import V23_PATH, build_manifest


class TestFtaBaselineManifestV24(unittest.TestCase):
    def test_v24_records_only_the_completed_controlled_request_without_readiness_promotion(self) -> None:
        v23_hash = hashlib.sha256(V23_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")
        inference = payload["event_scope_model_inference"]
        attempt = inference["controlled_attempt_v3"]
        self.assertEqual("candidate_fta_research_baseline_v24", payload["manifest_id"])
        self.assertEqual("v24", payload["baseline_version"])
        self.assertEqual(3, inference["request_count"])
        self.assertEqual("stop", attempt["finish_reason"])
        self.assertTrue(attempt["strict_json_parsed"])
        self.assertEqual(8, attempt["quote_checks"])
        self.assertEqual(0, attempt["invalid_quotes"])
        self.assertEqual("not_performed", attempt["gold_comparison"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v23_hash, hashlib.sha256(V23_PATH.read_bytes()).hexdigest())

    def test_v24_registers_run_receipt_assessment_and_current_documents(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn("evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json", paths)
        self.assertIn("evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.attempt.json", paths)
        self.assertIn("evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v3_2026-09-29.json", paths)
        self.assertIn("docs/current-state-audit.md", paths)
        self.assertIn("docs/acceptance.md", paths)


if __name__ == "__main__":
    unittest.main()
