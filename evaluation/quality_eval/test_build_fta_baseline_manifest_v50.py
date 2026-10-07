from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v50 import (
    ARTIFACTS,
    EXPECTED_V49_SHA256,
    V49_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV50(unittest.TestCase):
    def test_parent_snapshot_and_blocked_run_are_locked(self) -> None:
        self.assertEqual(EXPECTED_V49_SHA256, hashlib.sha256(V49_PATH.read_bytes()).hexdigest())
        manifest = build_manifest(captured_at="2026-10-07")
        plan = manifest["next_stage_plan_v1"]
        self.assertEqual("candidate_fta_research_baseline_v50", manifest["manifest_id"])
        self.assertEqual("blocked", plan["p2_current_run_status"])
        self.assertEqual(4, plan["p2_model_requests_performed_this_run"])
        self.assertEqual(4, plan["p2_model_request_limit_this_run"])
        self.assertEqual(0, plan["p2_model_retries_performed"])
        self.assertEqual(0, plan["p2_semantic_defects_closed"])
        self.assertEqual(
            "passed_fail_closed_with_both_exact_offsets_and_context_spans",
            plan["p2_occurrence_scope_regression_status"],
        )
        self.assertEqual(2, plan["p2_occurrence_scope_regression_test_count"])
        self.assertEqual(86, plan["p2_backend_targeted_test_count"])
        self.assertFalse(plan["p2_shared_evidence_contract_changed"])
        self.assertEqual({"fta_event_candidate": 3, "relation_only": 1, "unresolved": 1}, plan["p2_host_effective_dispositions"])
        self.assertFalse(manifest["active_baseline"]["fta_ready"])
        self.assertFalse(manifest["active_baseline"]["production_ready"])

    def test_current_artifact_set_is_registered(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        registered = {item["path"]: item for item in manifest["artifacts"]}
        for path in ARTIFACTS:
            self.assertIn(path, registered)
        self.assertEqual("historical", registered["evaluation/quality_eval/fta_baseline_manifest_v49.json"]["lifecycle"])
        self.assertEqual("historical", registered["evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v1_2026-10-07.json"]["lifecycle"])

    def test_registered_artifact_hashes_validate(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        result = validate_manifest(manifest, repo_root=V49_PATH.parents[2])
        self.assertEqual(result["artifact_count"], result["verified_count"])

    def test_raw_run_provenance_is_not_human_gold(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        run_path = V49_PATH.parents[2] / "evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.json"
        audit = json.loads(run_path.read_text(encoding="utf-8"))
        self.assertFalse(audit["formal_gold"])
        self.assertFalse(audit["blind_final"])
        self.assertIn("not_human_expert_review", audit["reviewer_provenance"])
        self.assertEqual("blocked", manifest["next_stage_plan_v1"]["p2_current_run_status"])


if __name__ == "__main__":
    unittest.main()
