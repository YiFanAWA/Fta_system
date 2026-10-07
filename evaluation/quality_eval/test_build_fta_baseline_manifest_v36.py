from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v35 import V35_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v36 import (
    CASES_PATH,
    PROMPT_PATH,
    PROMPT_TEST_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV36(unittest.TestCase):
    def test_v36_registers_semantic_prompt_policy_and_preserves_readiness_guards(self) -> None:
        v35_hash = hashlib.sha256(V35_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        prompt = manifest["event_scope_prompt_v8_candidate"]

        self.assertEqual("candidate_fta_research_baseline_v36", manifest["manifest_id"])
        self.assertEqual("offline_candidate_not_run", active["event_scope_prompt_v8_candidate_status"])
        self.assertEqual(PROMPT_PATH, prompt["prompt_path"])
        self.assertEqual(PROMPT_TEST_PATH, prompt["test_path"])
        self.assertEqual(CASES_PATH, prompt["regression_cases_path"])
        self.assertFalse(prompt["runner_wired"])
        self.assertFalse(prompt["live_request_performed"])
        self.assertFalse(prompt["semantic_acceptance"])
        self.assertFalse(prompt["policy"]["literal_and_or_tokens_required"])
        self.assertTrue(prompt["policy"]["semantic_interpretation_allowed"])
        self.assertTrue(prompt["policy"]["logic_evidence_must_directly_support_children_relation_and_same_output"])
        self.assertFalse(prompt["policy"]["mere_list_or_cooccurrence_is_sufficient"])
        self.assertFalse(active["event_scope_model_v6_semantic_acceptance"])
        self.assertEqual("findings_preserved_not_cleared", active["event_scope_v6_semantic_regression_status"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v35_hash, hashlib.sha256(V35_PATH.read_bytes()).hexdigest())

    def test_v36_registers_current_prompt_tests_fixture_docs_and_validator(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v35.json",
            PROMPT_PATH,
            PROMPT_TEST_PATH,
            CASES_PATH,
            "evaluation/quality_eval/build_fta_baseline_manifest_v36.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v36.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v35.json"]["lifecycle"])
        self.assertEqual("current_offline_only", artifacts[PROMPT_PATH]["lifecycle"])
        self.assertEqual("current_non_gold", artifacts[CASES_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
