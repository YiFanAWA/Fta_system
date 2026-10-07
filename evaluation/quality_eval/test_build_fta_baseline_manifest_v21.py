from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v21 import V20_PATH, build_manifest


class TestFtaBaselineManifestV21(unittest.TestCase):
    def test_v21_records_one_incomplete_call_without_promoting_readiness(self) -> None:
        v20_hash = hashlib.sha256(V20_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")

        self.assertEqual("candidate_fta_research_baseline_v21", payload["manifest_id"])
        self.assertEqual("v21", payload["baseline_version"])
        self.assertEqual(1, payload["event_scope_model_inference"]["request_count"])
        self.assertEqual(0, payload["event_scope_model_inference"]["retry_count"])
        self.assertEqual("length", payload["event_scope_model_inference"]["finish_reason"])
        self.assertFalse(payload["event_scope_model_inference"]["usable_json"])
        self.assertEqual("not_performed", payload["event_scope_model_inference"]["gold_comparison"])
        self.assertEqual(1, payload["event_scope_dev_case"]["event_scope_count"])
        self.assertFalse(payload["event_scope_dev_case"]["eligible_for_independent_final"])
        self.assertFalse(payload["event_scope_dev_case"]["formal_gold"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v20_hash, hashlib.sha256(V20_PATH.read_bytes()).hexdigest())

    def test_v21_registers_attempt_run_assessment_and_runner(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v20.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.attempt.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.json",
            "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v1.py",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
