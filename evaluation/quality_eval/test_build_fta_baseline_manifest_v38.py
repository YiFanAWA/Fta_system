from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v37 import V37_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v38 import (
    ATTEMPT_PATH,
    ASSESSMENT_PATH,
    COMPARISON_PATH,
    RUN_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV38(unittest.TestCase):
    def test_v38_records_single_non_gold_observation_without_readiness_promotion(self) -> None:
        v37_hash = hashlib.sha256(V37_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]

        self.assertEqual("candidate_fta_research_baseline_v38", manifest["manifest_id"])
        self.assertEqual("one_case_qualitative_match_non_gold", active["event_scope_semantic_smoke_status"])
        self.assertEqual(1, active["event_scope_semantic_smoke_requests_performed"])
        self.assertEqual(["SMOKE-001"], smoke["completed_case_ids"])
        self.assertEqual(["SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"], smoke["not_run_case_ids"])
        self.assertTrue(smoke["policy_expectation_match"])
        self.assertFalse(smoke["semantic_acceptance"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v37_hash, hashlib.sha256(V37_PATH.read_bytes()).hexdigest())

    def test_v38_registers_run_assessment_receipt_comparison_tools_and_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v37.json",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_PATH,
            "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py",
            "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v1.py",
            "evaluation/quality_eval/build_fta_baseline_manifest_v38.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v38.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v37.json"]["lifecycle"])
        self.assertEqual("current_non_gold_observation", artifacts[RUN_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
