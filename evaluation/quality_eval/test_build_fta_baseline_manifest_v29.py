from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v28 import V28_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v29 import build_manifest


class TestFtaBaselineManifestV29(unittest.TestCase):
    def test_v29_records_offline_candidate_without_model_request_or_readiness_promotion(self) -> None:
        v28_hash = hashlib.sha256(V28_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        self.assertEqual("candidate_fta_research_baseline_v29", manifest["manifest_id"])
        self.assertEqual("prepared_offline_not_run", manifest["event_scope_prompt_v5"]["status"])
        self.assertEqual(0, manifest["event_scope_prompt_v5"]["live_request_count"])
        self.assertEqual(
            "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json",
            manifest["event_scope_prompt_v5"]["latest_actual_model_run"],
        )
        self.assertFalse(manifest["event_scope_prompt_v5"]["model_accuracy_or_improvement_claim_allowed"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])
        self.assertEqual(v28_hash, hashlib.sha256(V28_PATH.read_bytes()).hexdigest())

    def test_v29_registers_v5_candidate_and_current_documents(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/event_scope_tree_prompt_v5.py",
            "evaluation/quality_eval/test_event_scope_tree_prompt_v5.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v29.py",
            "evaluation/quality_eval/fta_baseline_manifest_v28.json",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
