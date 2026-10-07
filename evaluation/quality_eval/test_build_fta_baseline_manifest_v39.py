from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v39 import (
    ATTEMPT_PATH,
    ASSESSMENT_PATH,
    COMPARISON_PATH,
    RUN_PATH,
    V38_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV39(unittest.TestCase):
    def test_v39_records_two_non_gold_observations_without_readiness_promotion(self) -> None:
        v38_hash = hashlib.sha256(V38_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]

        self.assertEqual("candidate_fta_research_baseline_v39", manifest["manifest_id"])
        self.assertEqual("two_case_qualitative_matches_non_gold", active["event_scope_semantic_smoke_status"])
        self.assertEqual(2, active["event_scope_semantic_smoke_requests_performed"])
        self.assertEqual(["SMOKE-001", "SMOKE-002"], smoke["completed_case_ids"])
        self.assertEqual(["SMOKE-003", "SMOKE-004", "SMOKE-005"], smoke["not_run_case_ids"])
        self.assertEqual(["OR", "AND"], [item["observed_gate"] for item in smoke["case_results"]])
        self.assertTrue(all(item["policy_expectation_match"] for item in smoke["case_results"]))
        self.assertFalse(smoke["semantic_acceptance"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v38_hash, hashlib.sha256(V38_PATH.read_bytes()).hexdigest())

    def test_v39_registers_smoke_002_artifacts_and_current_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v38.json",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_PATH,
            "evaluation/quality_eval/build_fta_baseline_manifest_v39.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v39.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v38.json"]["lifecycle"])
        self.assertEqual("current_non_gold_observation", artifacts[RUN_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
