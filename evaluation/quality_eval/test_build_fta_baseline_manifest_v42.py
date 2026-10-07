from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v42 import (
    ATTEMPT_PATH,
    ASSESSMENT_PATH,
    COMPARISON_PATH,
    RUN_PATH,
    V41_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV42(unittest.TestCase):
    def test_v42_records_gate_policy_match_and_structural_block_separately(self) -> None:
        v41_hash = hashlib.sha256(V41_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]
        case = next(item for item in smoke["case_results"] if item["case_id"] == "SMOKE-005")

        self.assertEqual("candidate_fta_research_baseline_v42", manifest["manifest_id"])
        self.assertEqual("four_policy_matches_one_structure_blocked_non_gold", active["event_scope_semantic_smoke_status"])
        self.assertEqual(5, active["event_scope_semantic_smoke_requests_performed"])
        self.assertEqual(["SMOKE-001", "SMOKE-002", "SMOKE-003", "SMOKE-004", "SMOKE-005"], smoke["completed_case_ids"])
        self.assertEqual([], smoke["not_run_case_ids"])
        self.assertTrue(case["policy_expectation_match"])
        self.assertEqual("requires_review", case["overall_comparison_status"])
        self.assertFalse(case["structure_contract_valid"])
        self.assertEqual(["gate_scope_requires_at_least_two_children"], case["structure_blocker_codes"])
        self.assertFalse(case["qualitative_smoke_match"])
        self.assertEqual(22, smoke["evidence_locations_checked"])
        self.assertFalse(smoke["semantic_acceptance"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v41_hash, hashlib.sha256(V41_PATH.read_bytes()).hexdigest())

    def test_v42_registers_smoke_005_and_current_artifacts(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v41.json",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_PATH,
            "evaluation/quality_eval/build_fta_baseline_manifest_v42.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v42.py",
            "evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v41.json"]["lifecycle"])
        self.assertEqual("current_non_gold_observation", artifacts[COMPARISON_PATH]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
