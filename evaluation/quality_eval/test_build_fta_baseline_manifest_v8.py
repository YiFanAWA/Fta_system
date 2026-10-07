from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v8 import (
    V7_PATH,
    build_manifest,
)


ROOT = V7_PATH.parents[2]


class TestFtaBaselineManifestV8(unittest.TestCase):
    def test_v8_preserves_v7_final_and_readiness_boundaries(self) -> None:
        v7_before = hashlib.sha256(V7_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")

        self.assertEqual("candidate_fta_research_baseline_v8", payload["manifest_id"])
        self.assertEqual(["v7"], payload["superseded"][-1]["superseded_versions"])
        self.assertEqual("v8", payload["superseded"][-1]["current_version"])
        self.assertEqual(36, payload["behavior_regression_suite"]["sample_count"])
        self.assertEqual(15, payload["behavior_regression_suite"]["source_cluster_count"])
        self.assertEqual(11, payload["development_gate_suite"]["sample_count"])
        self.assertEqual(3, payload["development_gate_suite"]["source_cluster_count"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual("fta-cause-disposition-v2", payload["active_baseline"]["cause_disposition_prompt"])
        self.assertFalse(payload["cause_disposition_v2_raw_text_regressions"]["formal_gold"])
        self.assertFalse(payload["cause_disposition_v2_raw_text_regressions"]["database_written"])
        self.assertFalse(payload["cause_disposition_v2_raw_text_regressions"]["accuracy_claim_allowed"])
        self.assertEqual(v7_before, hashlib.sha256(V7_PATH.read_bytes()).hexdigest())

    def test_v2_cases_preserve_expected_unknown_and_evidence_boundaries(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        cases = {
            case["fault_code"]: case
            for case in payload["cause_disposition_v2_raw_text_regressions"]["cases"]
        }
        self.assertEqual({"F01681", "F30027"}, set(cases))
        f01681 = cases["F01681"]
        self.assertEqual({"exclude_from_tree": 1, "fta_event_candidate": 15}, f01681["disposition_counts"])
        self.assertEqual(12, f01681["gate_scope_count"])
        self.assertEqual(10, f01681["complete_and_leaf_normalized_gate_count"])
        self.assertEqual("S210_Manual_2019.pdf", f01681["source_pdf"])
        self.assertEqual([455, 457], f01681["pdf_pages"])
        self.assertEqual(64, len(f01681["source_pdf_sha256"]))
        self.assertTrue(f01681["all_gates_unknown"])
        f30027 = cases["F30027"]
        self.assertEqual({"fta_event_candidate": 9}, f30027["disposition_counts"])
        self.assertEqual(2, f30027["gate_scope_count"])
        self.assertEqual(2, f30027["complete_and_leaf_normalized_gate_count"])
        self.assertTrue(f30027["all_gates_unknown"])
        for case in cases.values():
            self.assertEqual("candidate_ready_for_review", case["tree_status"])
            self.assertTrue(case["candidate_tree_evidence_exact_and_unique"])
            self.assertFalse(case["fta_ready"])
            self.assertFalse(case["production_ready"])

    def test_v8_fingerprints_all_active_sources_runs_and_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifacts = payload["artifacts"]
        paths = [item["path"] for item in artifacts]
        self.assertEqual(len(paths), len(set(paths)))
        required_paths = {
            "evaluation/quality_eval/build_fta_baseline_manifest_v8.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v8.py",
            "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_dev_regression_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_dev_regression_2026-09-28.json",
            "backend-python/fta/cause_disposition_service.py",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/README.md",
        }
        self.assertTrue(required_paths.issubset(set(paths)))
        for artifact in artifacts:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(
                artifact["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["path"],
            )


if __name__ == "__main__":
    unittest.main()
