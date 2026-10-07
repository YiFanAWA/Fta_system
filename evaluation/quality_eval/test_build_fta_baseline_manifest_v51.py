from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v51 import (
    ARTIFACTS,
    EXPECTED_V50_SHA256,
    V50_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV51(unittest.TestCase):
    def test_parent_snapshot_and_fail_closed_state_are_locked(self) -> None:
        self.assertEqual(EXPECTED_V50_SHA256, hashlib.sha256(V50_PATH.read_bytes()).hexdigest())
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]
        self.assertEqual("candidate_fta_research_baseline_v51", manifest["manifest_id"])
        self.assertEqual("blocked", plan["p2_current_run_status"])
        self.assertEqual(0, plan["p2_semantic_defects_closed"])
        self.assertFalse(plan["p2_shared_evidence_contract_changed"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_reconciliation_artifacts_are_registered_and_hashed(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        registered = {item["path"]: item for item in manifest["artifacts"]}
        for path in ARTIFACTS:
            self.assertIn(path, registered)
        result = validate_manifest(manifest, repo_root=V50_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])

    def test_ai_locator_review_does_not_become_human_gold_or_applied_decision(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        reconciliation = manifest["next_stage_plan_v1"]
        self.assertEqual(
            "passed_offline_scope_hash_and_offset_checks_not_applied_to_latest_raw_run",
            reconciliation["p2_occurrence_review_reconciliation_status"],
        )
        self.assertFalse(manifest["active_baseline"]["latest_real_source_semantic_acceptance"])


if __name__ == "__main__":
    unittest.main()
