from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v9 import (
    V8_PATH,
    build_manifest,
)


ROOT = V8_PATH.parents[2]


class TestFtaBaselineManifestV9(unittest.TestCase):
    def test_v9_preserves_v8_final_and_readiness_boundaries(self) -> None:
        v8_before = hashlib.sha256(V8_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")

        self.assertEqual("candidate_fta_research_baseline_v9", payload["manifest_id"])
        self.assertEqual({"v8"}, set(payload["superseded"][-1]["superseded_versions"]))
        self.assertEqual("v9", payload["superseded"][-1]["current_version"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertFalse(payload["cause_disposition_v2_extended_raw_text_regressions"]["formal_gold"])
        self.assertFalse(payload["cause_disposition_v2_extended_raw_text_regressions"]["database_written"])
        self.assertFalse(payload["cause_disposition_v2_extended_raw_text_regressions"]["accuracy_claim_allowed"])
        self.assertFalse(payload["f01681_independent_ai_semantic_review"]["human_reviewed"])
        self.assertFalse(payload["f01681_independent_ai_semantic_review"]["formal_gold"])
        self.assertIn("extraction_cause_index_1_missing_evidence_span", payload["f01681_independent_ai_semantic_review"]["finding_codes"])
        self.assertIn(
            "offline_replay_of_the_saved_f01681_extraction_response_maps_all_16_causes",
            payload["f01681_independent_ai_semantic_review"]["finding_resolution"][
                "extraction_cause_index_1_missing_evidence_span"
            ],
        )
        self.assertIn(
            "does_not_prove_causal_semantics",
            payload["f01681_independent_ai_semantic_review"]["finding_resolution"][
                "extraction_cause_index_1_missing_evidence_span"
            ],
        )
        self.assertEqual(v8_before, hashlib.sha256(V8_PATH.read_bytes()).hexdigest())

    def test_raw_v2_cases_keep_expected_evidence_and_unknown_gates(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        cases = {item["fault_code"]: item for item in payload["cause_disposition_v2_extended_raw_text_regressions"]["cases"]}
        self.assertEqual({"F30021", "F35400", "F06000"}, set(cases))
        self.assertEqual("blocked", cases["F30021"]["tree_status"])
        self.assertFalse(cases["F30021"]["candidate_tree_evidence_unique"])
        self.assertEqual("candidate_ready_for_review", cases["F35400"]["tree_status"])
        self.assertTrue(cases["F35400"]["candidate_tree_evidence_unique"])
        self.assertEqual("candidate_ready_for_review", cases["F06000"]["tree_status"])
        self.assertIn("not_applicable", cases["F06000"]["gate_values"])
        self.assertTrue(all(case["fta_ready"] is False and case["production_ready"] is False for case in cases.values()))
        guard = payload["top_event_evidence_ambiguity_guard"]
        self.assertTrue(guard["does_not_auto_select_offsets"])
        self.assertTrue(guard["example_run_predates_guard"])

    def test_v9_fingerprints_all_new_runs_code_tests_and_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifacts = payload["artifacts"]
        paths = [item["path"] for item in artifacts]
        self.assertEqual(len(paths), len(set(paths)))
        required = {
            "evaluation/quality_eval/build_fta_baseline_manifest_v9.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v9.py",
            "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md",
            "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
            "backend-python/fta/candidate_fta_extraction_service.py",
            "backend-python/tests/test_candidate_fta_extraction_service.py",
            "backend-python/extraction/text_extraction_adapter.py",
            "backend-python/tests/test_evidence_mapping.py",
            "backend-python/fta/cause_disposition_service.py",
            "backend-python/tests/test_fta_cause_disposition.py",
            "backend-python/tests/test_recursive_candidate_fta_extraction_service.py",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/README.md",
        }
        self.assertTrue(required.issubset(set(paths)))
        for item in artifacts:
            path = ROOT / item["path"]
            self.assertTrue(path.is_file(), item["path"])
            self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), item["path"])


if __name__ == "__main__":
    unittest.main()
