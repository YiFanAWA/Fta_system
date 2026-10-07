from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v34 import V34_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v35 import (
    CASES_PATH,
    PROMPT_PATH,
    PROMPT_TEST_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV35(unittest.TestCase):
    def test_v35_registers_prompt_as_offline_only_and_preserves_readiness_guards(self) -> None:
        v34_hash = hashlib.sha256(V34_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        prompt = manifest["event_scope_prompt_v7_candidate"]

        self.assertEqual("candidate_fta_research_baseline_v35", manifest["manifest_id"])
        self.assertEqual("offline_candidate_not_run", active["event_scope_prompt_v7_candidate_status"])
        self.assertEqual(PROMPT_PATH, prompt["prompt_path"])
        self.assertEqual(PROMPT_TEST_PATH, prompt["test_path"])
        self.assertEqual(CASES_PATH, prompt["regression_cases_path"])
        self.assertFalse(prompt["runner_wired"])
        self.assertFalse(prompt["live_request_performed"])
        self.assertFalse(prompt["semantic_acceptance"])
        self.assertFalse(active["event_scope_model_v6_semantic_acceptance"])
        self.assertEqual("findings_preserved_not_cleared", active["event_scope_v6_semantic_regression_status"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v34_hash, hashlib.sha256(V34_PATH.read_bytes()).hexdigest())

    def test_v35_registers_current_prompt_tests_and_non_gold_fixture(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v34.json",
            PROMPT_PATH,
            PROMPT_TEST_PATH,
            CASES_PATH,
            "evaluation/quality_eval/build_fta_baseline_manifest_v35.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v35.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v34.json"]["lifecycle"])
        self.assertEqual("current_offline_only", artifacts[PROMPT_PATH]["lifecycle"])
        self.assertEqual("current_non_gold", artifacts[CASES_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
