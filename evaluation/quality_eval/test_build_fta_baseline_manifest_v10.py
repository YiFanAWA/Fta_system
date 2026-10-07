from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v10 import (
    V9_PATH,
    build_manifest,
)


ROOT = V9_PATH.parents[2]


class TestFtaBaselineManifestV10(unittest.TestCase):
    def test_v10_preserves_v9_and_keeps_readiness_closed(self) -> None:
        v9_before = hashlib.sha256(V9_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")

        self.assertEqual("candidate_fta_research_baseline_v10", payload["manifest_id"])
        self.assertEqual("fta-cause-disposition-v3", payload["active_baseline"]["cause_disposition_prompt"])
        self.assertEqual("v10", payload["superseded"][-1]["current_version"])
        self.assertEqual(["v9"], payload["superseded"][-1]["superseded_versions"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertFalse(payload["cause_disposition_v3_policy_regression"]["formal_gold"])
        self.assertFalse(payload["cause_disposition_v3_policy_regression"]["database_written"])
        self.assertFalse(payload["cause_disposition_v3_policy_regression"]["online_model_rerun"])
        self.assertFalse(payload["cause_disposition_v3_policy_regression"]["accuracy_claim_allowed"])
        self.assertIn(
            "diagnostic_mappings_do_not_auto_connect",
            payload["cause_disposition_v3_policy_regression"]["user_decision"],
        )
        self.assertEqual(v9_before, hashlib.sha256(V9_PATH.read_bytes()).hexdigest())

    def test_v10_indexes_current_policy_tests_and_documents(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifacts = payload["artifacts"]
        paths = [item["path"] for item in artifacts]
        ids = [item["artifact_id"] for item in artifacts]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(ids), len(set(ids)))
        required = {
            "evaluation/quality_eval/fta_baseline_manifest_v9.json",
            "evaluation/quality_eval/build_fta_baseline_manifest_v10.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v10.py",
            "backend-python/fta/cause_disposition_service.py",
            "backend-python/fta/candidate_fta_extraction_service.py",
            "backend-python/tests/test_fta_cause_disposition.py",
            "backend-python/tests/test_candidate_fta_extraction_service.py",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        }
        self.assertTrue(required.issubset(set(paths)))
        for artifact in artifacts:
            target = ROOT / artifact["path"]
            self.assertTrue(target.is_file(), artifact["path"])
            self.assertEqual(
                artifact["sha256"],
                hashlib.sha256(target.read_bytes()).hexdigest(),
                artifact["path"],
            )


if __name__ == "__main__":
    unittest.main()
