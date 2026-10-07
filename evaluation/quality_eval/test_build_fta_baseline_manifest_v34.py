from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v33 import V33_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v34 import (
    CASES_PATH,
    POLICY_PATH,
    REGRESSION_TEST_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV34(unittest.TestCase):
    def test_v34_records_policy_without_gold_or_readiness_promotion(self) -> None:
        v33_hash = hashlib.sha256(V33_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]

        self.assertEqual("candidate_fta_research_baseline_v34", manifest["manifest_id"])
        self.assertEqual(POLICY_PATH, active["event_scope_semantic_review_policy_path"])
        self.assertEqual(CASES_PATH, active["event_scope_semantic_review_cases_path"])
        self.assertEqual(REGRESSION_TEST_PATH, active["event_scope_semantic_review_test_path"])
        self.assertEqual("findings_preserved_not_cleared", active["event_scope_v6_semantic_regression_status"])
        self.assertFalse(active["event_scope_model_v6_semantic_acceptance"])
        self.assertFalse(active["event_scope_model_v6_accuracy_claim_allowed"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v33_hash, hashlib.sha256(V33_PATH.read_bytes()).hexdigest())

    def test_v34_registers_non_gold_policy_and_regression_artifacts(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v33.json",
            "evaluation/quality_eval/build_fta_baseline_manifest_v34.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v34.py",
            POLICY_PATH,
            CASES_PATH,
            REGRESSION_TEST_PATH,
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v33.json"]["lifecycle"])
        self.assertEqual("current_non_gold", artifacts[CASES_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
