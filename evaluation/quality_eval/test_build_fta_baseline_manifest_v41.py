from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v41 import (
    ATTEMPT_PATH,
    ASSESSMENT_PATH,
    COMPARISON_PATH,
    RUN_PATH,
    V40_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV41(unittest.TestCase):
    def test_v41_records_cooccurrence_unknown_case_without_readiness_promotion(self) -> None:
        v40_hash = hashlib.sha256(V40_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]

        self.assertEqual("candidate_fta_research_baseline_v41", manifest["manifest_id"])
        self.assertEqual("four_case_qualitative_matches_non_gold", active["event_scope_semantic_smoke_status"])
        self.assertEqual(4, active["event_scope_semantic_smoke_requests_performed"])
        self.assertEqual(["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004"], smoke["completed_case_ids"])
        self.assertEqual(["SMOKE-005"], smoke["not_run_case_ids"])
        self.assertTrue(smoke["case_results"][3]["unknown_gate_contract_valid"])
        self.assertEqual("no_direct_logic_evidence", smoke["case_results"][3]["unknown_reason"])
        self.assertFalse(smoke["semantic_acceptance"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v40_hash, hashlib.sha256(V40_PATH.read_bytes()).hexdigest())

    def test_v41_registers_smoke_004_and_current_policy_artifacts(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v40.json",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_PATH,
            "evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py",
            "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py",
            "evaluation/quality_eval/build_fta_baseline_manifest_v41.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v41.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v40.json"]["lifecycle"])
        self.assertEqual("current_non_gold_observation", artifacts[COMPARISON_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
