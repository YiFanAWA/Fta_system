from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from fta_readiness_report_v1 import ReadinessReportValidationError, validate_readiness_report


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_scoped_readiness_assessment_v1_2026-09-28.json"


class ScopedFtaReadinessReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    def test_current_assessment_is_scoped_and_does_not_promote_global_readiness(self) -> None:
        result = validate_readiness_report(self.payload)
        self.assertEqual("blocked", result["structure_status"])
        self.assertEqual("blocked", result["quantitative_status"])
        self.assertFalse(result["fta_ready"])
        self.assertFalse(result["production_ready"])
        self.assertEqual(47, result["case_count"])
        self.assertEqual(18, result["source_cluster_count"])

    def test_scoped_ready_requires_all_criteria_and_evidence(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["structure_readiness"]["status"] = "ready_within_scope"
        payload["structure_readiness"]["blockers"] = []
        with self.assertRaisesRegex(ReadinessReportValidationError, "cannot be ready"):
            validate_readiness_report(payload)

    def test_quantitative_ready_requires_structure_ready_in_same_scope(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["quantitative_readiness"]["status"] = "ready_within_scope"
        payload["quantitative_readiness"]["blockers"] = []
        payload["quantitative_readiness"]["criteria"] = [
            {"criterion_id": "quantified", "result": "met", "evidence_refs": ["evidence.json#/rate"]}
        ]
        with self.assertRaisesRegex(ReadinessReportValidationError, "requires structure readiness"):
            validate_readiness_report(payload)

    def test_scoped_report_cannot_set_global_ready_flags(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["global_readiness"]["fta_ready"] = True
        with self.assertRaisesRegex(ReadinessReportValidationError, "must not change global"):
            validate_readiness_report(payload)

    def test_scope_counts_must_match_included_sets(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["scope"]["case_count"] += 1
        with self.assertRaisesRegex(ReadinessReportValidationError, "must equal included set counts"):
            validate_readiness_report(payload)

    def test_included_sets_and_source_hashes_must_match_pinned_manifest(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["scope"]["included_sets"][0]["dataset_artifacts"][0]["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReadinessReportValidationError, "dataset hash mismatch"):
            validate_readiness_report(payload)

    def test_source_cluster_allocation_must_match_pinned_manifest(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["scope"]["source_clusters"][0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReadinessReportValidationError, "differs from the pinned source provenance"):
            validate_readiness_report(payload)

    def test_baseline_hash_must_match_exact_manifest_bytes(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["baseline"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ReadinessReportValidationError, "does not match the pinned manifest"):
            validate_readiness_report(payload)

    def test_human_expert_claim_requires_expert_reviewer_role(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["assessment_provenance"]["human_expert_reviewed"] = True
        with self.assertRaisesRegex(ReadinessReportValidationError, "reviewer_role=domain_expert"):
            validate_readiness_report(payload)

    def test_scope_includes_all_declared_source_clusters_and_separates_final(self) -> None:
        result = validate_readiness_report(self.payload)
        self.assertEqual(18, len(self.payload["scope"]["source_clusters"]))
        self.assertEqual(3, result["excluded_set_count"])
        self.assertEqual("not_created", self.payload["scope"]["excluded_sets"][0]["status"])
        self.assertEqual("not_run", self.payload["evaluation_configuration"]["model_inference_status"])


if __name__ == "__main__":
    unittest.main()
