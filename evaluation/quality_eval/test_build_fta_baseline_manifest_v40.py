from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v40 import (
    ATTEMPT_PATH,
    ASSESSMENT_PATH,
    COMPARISON_V1_PATH,
    COMPARISON_V2_PATH,
    RUN_PATH,
    V39_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV40(unittest.TestCase):
    def test_v40_records_unknown_case_and_keeps_all_readiness_false(self) -> None:
        v39_hash = hashlib.sha256(V39_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]

        self.assertEqual("candidate_fta_research_baseline_v40", manifest["manifest_id"])
        self.assertEqual("three_case_qualitative_matches_non_gold", active["event_scope_semantic_smoke_status"])
        self.assertEqual(3, active["event_scope_semantic_smoke_requests_performed"])
        self.assertEqual(["SMOKE-001", "SMOKE-002", "SMOKE-003"], smoke["completed_case_ids"])
        self.assertEqual(["SMOKE-004", "SMOKE-005"], smoke["not_run_case_ids"])
        self.assertEqual("v2", smoke["case_results"][2]["comparison_version"])
        self.assertTrue(smoke["case_results"][2]["unknown_gate_contract_valid"])
        self.assertFalse(smoke["semantic_acceptance"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v39_hash, hashlib.sha256(V39_PATH.read_bytes()).hexdigest())

    def test_v40_registers_both_comparison_records_and_current_policy_artifacts(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v39.json",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_V1_PATH,
            COMPARISON_V2_PATH,
            "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py",
            "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py",
            "evaluation/quality_eval/build_fta_baseline_manifest_v40.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v40.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical_diagnostic", artifacts[COMPARISON_V1_PATH]["lifecycle"])
        self.assertEqual("current_non_gold_observation", artifacts[COMPARISON_V2_PATH]["lifecycle"])
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v39.json"]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
