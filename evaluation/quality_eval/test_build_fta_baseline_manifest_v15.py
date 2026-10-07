from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v15 import V14_PATH, build_manifest


class TestFtaBaselineManifestV15(unittest.TestCase):
    def test_v15_narrows_regression_claim_without_rewriting_v14_or_readiness(self) -> None:
        v14_before = hashlib.sha256(V14_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        suite = payload["seen_case_regression_suite"]

        self.assertEqual("candidate_fta_research_baseline_v15", payload["manifest_id"])
        self.assertNotIn("behavior_regression_suite", payload)
        self.assertEqual("fta_gate_behavior_regression_v1", suite["legacy_suite_id"])
        self.assertEqual("fta_gate_contract_boundary_regression_v1", suite["suite_id"])
        self.assertEqual("fixture_contract_and_boundary_regression", suite["verification_scope"]["classification"])
        self.assertFalse(suite["verification_scope"]["offline_tests_call_current_model"])
        self.assertFalse(suite["verification_scope"]["accuracy_claim_allowed"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v14_before, hashlib.sha256(V14_PATH.read_bytes()).hexdigest())

    def test_v15_preserves_frozen_case_counts_and_fixture_hashes(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        suite = payload["seen_case_regression_suite"]
        self.assertEqual(36, suite["sample_count"])
        self.assertEqual(36, len(suite["cases"]))
        self.assertEqual(15, suite["source_cluster_count"])
        self.assertEqual({"AND": 9, "OR": 15, "unknown": 12}, suite["label_counts"])
        self.assertEqual(3, payload["development_gate_suite"]["source_cluster_count"])
        self.assertFalse(payload["development_gate_suite"]["overlap_with_seen_case_regression"])
        self.assertEqual(36, sum(item["sample_count"] for item in suite["dataset_suites"]))

        for item in suite["dataset_suites"]:
            relative = item["dataset_path"]
            artifact = next(row for row in payload["artifacts"] if row["path"] == relative)
            self.assertEqual(item["dataset_sha256"], artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
