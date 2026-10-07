from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v23 import V22_PATH, build_manifest


class TestFtaBaselineManifestV23(unittest.TestCase):
    def test_v23_records_prepared_but_unrun_request_without_readiness_promotion(self) -> None:
        v22_hash = hashlib.sha256(V22_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")
        inference = payload["event_scope_model_inference"]
        next_attempt = inference["next_controlled_attempt"]
        self.assertEqual("candidate_fta_research_baseline_v23", payload["manifest_id"])
        self.assertEqual("v23", payload["baseline_version"])
        self.assertEqual(2, inference["request_count"])
        self.assertEqual("prepared_blocked_credential_rotation", next_attempt["status"])
        self.assertEqual(0, next_attempt["request_count"])
        self.assertTrue(next_attempt["credential_rotation_confirmation_required"])
        self.assertFalse(inference["usable_json"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v22_hash, hashlib.sha256(V22_PATH.read_bytes()).hexdigest())

    def test_v23_registers_runner_tests_and_current_documents(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn("evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py", paths)
        self.assertIn("evaluation/quality_eval/test_run_fta_event_scope_model_v3.py", paths)
        self.assertIn("docs/current-state-audit.md", paths)
        self.assertIn("docs/acceptance.md", paths)


if __name__ == "__main__":
    unittest.main()
