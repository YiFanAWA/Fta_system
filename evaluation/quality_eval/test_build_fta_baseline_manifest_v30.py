from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v29 import V29_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v30 import build_manifest


class TestFtaBaselineManifestV30(unittest.TestCase):
    def test_v30_records_one_blocked_v5_run_without_promoting_readiness(self) -> None:
        v29_hash = hashlib.sha256(V29_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        run = manifest["event_scope_prompt_v5"]
        self.assertEqual("candidate_fta_research_baseline_v30", manifest["manifest_id"])
        self.assertEqual("completed_seen_development_only_blocked", run["status"])
        self.assertEqual(1, run["authorized_request_count"])
        self.assertEqual(0, run["observed_retry_count"])
        self.assertEqual("blocked", run["structure_status"])
        self.assertEqual({"valid": 15, "checked": 15, "semantic_entailment_assessed": False}, run["evidence_location"])
        self.assertFalse(run["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])
        self.assertEqual(v29_hash, hashlib.sha256(V29_PATH.read_bytes()).hexdigest())

    def test_v30_registers_run_bundle_and_current_runner(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v5.py",
            "evaluation/quality_eval/test_run_fta_event_scope_model_v5.py",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v5_2026-09-29.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.attempt.json",
            "evaluation/quality_eval/runs/fta_event_scope_model_run_v5_dev_comparison_2026-09-29.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
