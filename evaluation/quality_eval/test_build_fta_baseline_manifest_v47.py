from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v47 import (
    CURRENT_ARTIFACTS,
    EXPECTED_V46_SHA256,
    V46_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV47(unittest.TestCase):
    def test_records_single_request_gate_without_promoting_readiness(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]

        self.assertEqual(
            "offline_single_request_budget_gate_verified_live_run_pending_fresh_explicit_authorization",
            plan["milestones"]["P1_observation_live_boundary"],
        )
        self.assertEqual(3, plan["observation_runner_previous_max_model_calls"])
        self.assertEqual(1, plan["observation_runner_current_max_model_calls"])
        self.assertTrue(plan["observation_single_request_budget_gate_verified"])
        self.assertFalse(plan["observation_runner_live_validation_performed"])
        self.assertFalse(plan["live_model_request_performed"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_v46_is_immutable_and_registered_as_historical(self) -> None:
        self.assertEqual(EXPECTED_V46_SHA256, hashlib.sha256(V46_PATH.read_bytes()).hexdigest())
        manifest = build_manifest(captured_at="2026-10-07")
        entries = {item["path"]: item for item in manifest["artifacts"]}
        self.assertEqual(
            "historical",
            entries["evaluation/quality_eval/fta_baseline_manifest_v46.json"]["lifecycle"],
        )
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, entries)

    def test_all_manifested_artifact_hashes_validate(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        result = validate_manifest(manifest, repo_root=V46_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
