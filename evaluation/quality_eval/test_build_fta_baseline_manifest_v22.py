from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v22 import V21_PATH, build_manifest


class TestFtaBaselineManifestV22(unittest.TestCase):
    def test_v22_records_two_unusable_one_shot_calls_without_readiness_promotion(self) -> None:
        v21_hash = hashlib.sha256(V21_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")
        inference = payload["event_scope_model_inference"]
        self.assertEqual("candidate_fta_research_baseline_v22", payload["manifest_id"])
        self.assertEqual("v22", payload["baseline_version"])
        self.assertEqual(2, inference["request_count"])
        self.assertEqual(0, inference["retry_count"])
        self.assertEqual(2, len(inference["attempts"]))
        self.assertFalse(inference["usable_json"])
        self.assertEqual("undetermined", inference["root_cause"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v21_hash, hashlib.sha256(V21_PATH.read_bytes()).hexdigest())

    def test_v22_registers_second_run_and_assessment_artifacts(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn(
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json",
            paths,
        )
        self.assertIn(
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.md",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
