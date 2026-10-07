from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v26 import V26_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v27 import build_manifest


class TestFtaBaselineManifestV27(unittest.TestCase):
    def test_v27_keeps_request_unrun_and_readiness_false(self) -> None:
        v26_hash = hashlib.sha256(V26_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        self.assertEqual("candidate_fta_research_baseline_v27", manifest["manifest_id"])
        self.assertEqual("not_run", manifest["active_baseline"]["event_scope_prepared_prompt_status"])
        self.assertEqual(0, manifest["event_scope_model_v4"]["authorized_request_count"])
        self.assertFalse(manifest["event_scope_model_v4"]["model_input_includes_gold"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])
        self.assertEqual(v26_hash, hashlib.sha256(V26_PATH.read_bytes()).hexdigest())

    def test_v27_registers_v4_runner_prompt_tests_and_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/event_scope_tree_prompt_v4.py",
            "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py",
            "evaluation/quality_eval/test_run_fta_event_scope_model_v4.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v27.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
