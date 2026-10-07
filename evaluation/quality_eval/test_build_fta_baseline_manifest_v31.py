from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v30 import V30_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v31 import build_manifest


class TestFtaBaselineManifestV31(unittest.TestCase):
    def test_v31_records_offline_prompt_without_promoting_run_or_readiness(self) -> None:
        v30_hash = hashlib.sha256(V30_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        prompt = manifest["event_scope_prompt_v6"]
        active = manifest["active_baseline"]

        self.assertEqual("candidate_fta_research_baseline_v31", manifest["manifest_id"])
        self.assertEqual("completed_seen_development_only_blocked", manifest["event_scope_prompt_v5"]["status"])
        self.assertEqual("prepared_offline_not_run", prompt["status"])
        self.assertEqual(0, prompt["live_request_count"])
        self.assertFalse(prompt["runner_wired"])
        self.assertFalse(prompt["model_output_observed"])
        self.assertTrue(prompt["requires_fresh_explicit_authorization_for_any_model_request"])
        self.assertFalse(prompt["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v30_hash, hashlib.sha256(V30_PATH.read_bytes()).hexdigest())

    def test_v31_registers_prompt_tests_validator_and_current_documents(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v30.json",
            "evaluation/quality_eval/event_scope_tree_prompt_v6.py",
            "evaluation/quality_eval/test_event_scope_tree_prompt_v6.py",
            "evaluation/quality_eval/build_fta_baseline_manifest_v31.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v31.py",
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
