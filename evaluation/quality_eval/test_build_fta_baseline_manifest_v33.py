from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v32 import V32_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v33 import (
    ASSESSMENT_PATH,
    ATTEMPT_PATH,
    COMPARISON_PATH,
    RUN_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV33(unittest.TestCase):
    def test_v33_records_single_run_without_semantic_or_readiness_promotion(self) -> None:
        v32_hash = hashlib.sha256(V32_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        prompt = manifest["event_scope_prompt_v6"]
        active = manifest["active_baseline"]

        self.assertEqual("candidate_fta_research_baseline_v33", manifest["manifest_id"])
        self.assertEqual("completed_seen_development_only_semantics_unassessed", prompt["status"])
        self.assertEqual(1, prompt["live_request_count"])
        self.assertTrue(prompt["model_output_observed"])
        self.assertTrue(prompt["structure_contract_valid"])
        self.assertEqual(10, prompt["evidence_location_valid"])
        self.assertEqual(10, prompt["evidence_location_checked"])
        self.assertEqual({"AND": 0, "OR": 0, "unknown": 3}, prompt["gate_labels"])
        self.assertFalse(prompt["semantic_acceptance"])
        self.assertFalse(prompt["accuracy_or_calibration_claim_allowed"])
        self.assertEqual(RUN_PATH, active["event_scope_latest_actual_model_run"])
        self.assertEqual(ASSESSMENT_PATH, active["event_scope_model_run_assessment"])
        self.assertEqual(COMPARISON_PATH, active["event_scope_model_comparison"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v32_hash, hashlib.sha256(V32_PATH.read_bytes()).hexdigest())
        self.assertIn(ATTEMPT_PATH, {item["path"] for item in manifest["artifacts"]})

    def test_v33_registers_run_evaluation_and_current_truth(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in (
            "evaluation/quality_eval/fta_baseline_manifest_v32.json",
            "evaluation/quality_eval/build_fta_baseline_manifest_v33.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v33.py",
            "evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py",
            RUN_PATH,
            ASSESSMENT_PATH,
            ATTEMPT_PATH,
            COMPARISON_PATH,
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        ):
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v32.json"]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
