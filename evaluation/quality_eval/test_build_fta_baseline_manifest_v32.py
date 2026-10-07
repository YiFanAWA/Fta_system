from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v31 import V31_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v32 import RUNNER_PATH, RUNNER_TEST_PATH, build_manifest


class TestFtaBaselineManifestV32(unittest.TestCase):
    def test_v32_records_wired_runner_without_model_run_or_readiness_promotion(self) -> None:
        v31_hash = hashlib.sha256(V31_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        prompt = manifest["event_scope_prompt_v6"]
        active = manifest["active_baseline"]

        self.assertEqual("candidate_fta_research_baseline_v32", manifest["manifest_id"])
        self.assertEqual("completed_seen_development_only_blocked", manifest["event_scope_prompt_v5"]["status"])
        self.assertEqual("runner_wired_not_run", prompt["status"])
        self.assertTrue(prompt["runner_wired"])
        self.assertTrue(prompt["runner_offline_verified"])
        self.assertEqual(RUNNER_PATH, prompt["runner_path"])
        self.assertEqual(0, prompt["live_request_count"])
        self.assertFalse(prompt["model_output_observed"])
        self.assertTrue(prompt["requires_fresh_explicit_authorization_for_any_model_request"])
        self.assertTrue(prompt["raw_model_output_preserved_on_block"])
        self.assertFalse(prompt["automatic_repair_performed"])
        self.assertFalse(prompt["automatic_retry_performed"])
        self.assertFalse(prompt["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v31_hash, hashlib.sha256(V31_PATH.read_bytes()).hexdigest())

    def test_v32_registers_runner_and_current_truth_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v31.json",
            "evaluation/quality_eval/event_scope_tree_prompt_v6.py",
            "evaluation/quality_eval/test_event_scope_tree_prompt_v6.py",
            RUNNER_PATH,
            RUNNER_TEST_PATH,
            "evaluation/quality_eval/build_fta_baseline_manifest_v32.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v32.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
