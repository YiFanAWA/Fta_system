from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v48 import (
    CURRENT_ARTIFACTS,
    EXPECTED_V47_SHA256,
    EXPECTED_RUN_SHA256,
    V47_PATH,
    RUN_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV48(unittest.TestCase):
    def test_records_narrow_p1_pass_without_promoting_global_readiness(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]

        self.assertEqual(
            "P2_real_source_development_semantics",
            plan["current_stage"],
        )
        self.assertIn("one_synthetic_non_gold_case", plan["milestones"]["P1_observation_live_boundary"])
        self.assertTrue(plan["live_model_request_performed"])
        self.assertEqual(1, plan["observation_runner_actual_model_request_count"])
        self.assertTrue(plan["observation_runner_policy_boundary_match"])
        self.assertEqual(5, plan["observation_runner_unique_exact_evidence_reference_count"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_v47_and_live_run_are_hash_locked_and_registered(self) -> None:
        self.assertEqual(EXPECTED_V47_SHA256, hashlib.sha256(V47_PATH.read_bytes()).hexdigest())
        self.assertEqual(EXPECTED_RUN_SHA256, hashlib.sha256((V47_PATH.parents[2] / RUN_PATH).read_bytes()).hexdigest())
        manifest = build_manifest(captured_at="2026-10-07")
        entries = {item["path"]: item for item in manifest["artifacts"]}
        self.assertEqual(
            "historical",
            entries["evaluation/quality_eval/fta_baseline_manifest_v47.json"]["lifecycle"],
        )
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, entries)

    def test_run_artifact_is_non_gold_and_records_one_bounded_response(self) -> None:
        run = json.loads((V47_PATH.parents[2] / RUN_PATH).read_text(encoding="utf-8"))
        self.assertEqual("response_received", run["run_status"])
        self.assertEqual(1, run["request_attempt_count"])
        self.assertEqual(1, run["successful_response_count"])
        self.assertEqual("blocked", run["tree_status"])
        self.assertTrue(run["policy_assessment"]["policy_boundary_match"])
        self.assertFalse(run["formal_gold"])
        self.assertFalse(run["human_expert_gold"])
        self.assertFalse(run["database_written"])
        self.assertFalse(run["production_api_called"])

    def test_all_manifested_artifact_hashes_validate(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        result = validate_manifest(manifest, repo_root=V47_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
