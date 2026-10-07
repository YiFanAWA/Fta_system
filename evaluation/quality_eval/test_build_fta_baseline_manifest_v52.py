from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v52 import (
    ARTIFACTS,
    EXPECTED_V51_SHA256,
    V51_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV52(unittest.TestCase):
    def test_parent_snapshot_and_false_readiness_are_locked(self) -> None:
        self.assertEqual(
            EXPECTED_V51_SHA256,
            hashlib.sha256(V51_PATH.read_bytes()).hexdigest(),
        )
        manifest = build_manifest(captured_at="2026-10-07")
        self.assertEqual("candidate_fta_research_baseline_v52", manifest["manifest_id"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_locator_overlay_is_internal_non_gold_and_does_not_rewrite_run(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]
        self.assertEqual(
            "implemented_offline_verified_internal_only",
            plan["p2e_locator_overlay_contract_status"],
        )
        self.assertFalse(plan["p2e_review_is_formal_gold"])
        self.assertEqual(0, plan["p2e_model_requests_performed"])
        self.assertFalse(plan["p2e_public_api_changed"])
        self.assertFalse(plan["p2e_database_changed"])
        self.assertFalse(plan["p2e_gold_changed"])
        self.assertFalse(plan["p2e_historical_run_rewritten"])
        self.assertEqual(0, plan["p2e_semantic_defects_closed"])

    def test_current_artifacts_are_registered_and_hash_valid(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        registered = {item["path"]: item for item in manifest["artifacts"]}
        for path in ARTIFACTS:
            self.assertIn(path, registered)
        result = validate_manifest(manifest, repo_root=V51_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
