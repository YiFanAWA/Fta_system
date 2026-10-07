from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v49 import (
    AUDIT_JSON_PATH,
    CURRENT_ARTIFACTS,
    EXPECTED_V48_SHA256,
    V48_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV49(unittest.TestCase):
    def test_records_p2_audit_without_claiming_current_semantic_validation(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]

        self.assertEqual("P2_real_source_development_semantics", plan["current_stage"])
        self.assertTrue(plan["p2_contract_audit_complete"])
        self.assertTrue(plan["p2_historical_case_audit_complete"])
        self.assertEqual(6, plan["p2_historical_case_count"])
        self.assertEqual("fta-cause-disposition-v5", plan["p2_current_cause_disposition_prompt_version"])
        self.assertFalse(plan["p2_current_model_run_performed"])
        self.assertEqual(0, plan["p2_model_requests_performed_this_audit"])
        self.assertEqual(0, plan["p2_semantic_defects_closed"])
        self.assertTrue(plan["p2_next_action_requires_fresh_explicit_authorization"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_parent_and_audit_scope_are_locked(self) -> None:
        self.assertEqual(EXPECTED_V48_SHA256, hashlib.sha256(V48_PATH.read_bytes()).hexdigest())
        audit = json.loads((V48_PATH.parents[2] / AUDIT_JSON_PATH).read_text(encoding="utf-8"))
        self.assertEqual(0, audit["safety_scope"]["model_requests_performed"])
        self.assertEqual(6, len(audit["cases"]))
        self.assertEqual("agent_engineering_audit_not_human_expert_review", audit["reviewer_provenance"])
        manifest = build_manifest(captured_at="2026-10-07")
        entries = {item["path"]: item for item in manifest["artifacts"]}
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, entries)
        self.assertEqual("historical", entries["evaluation/quality_eval/fta_baseline_manifest_v48.json"]["lifecycle"])

    def test_all_manifested_artifact_hashes_validate(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        result = validate_manifest(manifest, repo_root=V48_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
