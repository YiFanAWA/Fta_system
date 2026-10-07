from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v27 import V27_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v28 import build_manifest


class TestFtaBaselineManifestV28(unittest.TestCase):
    def test_v28_records_one_blocked_seen_dev_request_and_keeps_readiness_false(self) -> None:
        v27_hash = hashlib.sha256(V27_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        self.assertEqual("candidate_fta_research_baseline_v28", manifest["manifest_id"])
        self.assertEqual(1, manifest["event_scope_model_v4"]["authorized_request_count"])
        self.assertEqual(0, manifest["event_scope_model_v4"]["observed_retry_count"])
        self.assertEqual("blocked", manifest["event_scope_model_v4"]["structure_status"])
        self.assertEqual({"valid": 9, "checked": 9, "semantic_entailment_assessed": False}, manifest["event_scope_model_v4"]["evidence_location"])
        self.assertFalse(manifest["event_scope_model_v4"]["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])
        self.assertEqual(v27_hash, hashlib.sha256(V27_PATH.read_bytes()).hexdigest())

    def test_v28_registers_observation_reports_and_governing_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json",
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json",
            "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v28.py",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
