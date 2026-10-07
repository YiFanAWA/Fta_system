from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v36 import V36_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v37 import (
    INPUTS_PATH,
    REFERENCE_PATH,
    RUNNER_PATH,
    build_manifest,
)


ROOT = V36_PATH.resolve().parents[2]


class TestFtaBaselineManifestV37(unittest.TestCase):
    def test_v37_records_preflight_only_and_preserves_readiness(self) -> None:
        v36_hash = hashlib.sha256(V36_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        smoke = manifest["event_scope_semantic_smoke_v1"]

        self.assertEqual("candidate_fta_research_baseline_v37", manifest["manifest_id"])
        self.assertEqual("v37", manifest["baseline_version"])
        self.assertEqual("preflight_ready_not_run", smoke["status"])
        self.assertEqual(5, smoke["case_count"])
        self.assertFalse(smoke["runner_reads_reference"])
        self.assertFalse(smoke["live_request_performed"])
        self.assertFalse(smoke["human_expert_gold"])
        self.assertFalse(smoke["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertFalse(active["event_scope_prompt_v8_semantic_acceptance"])
        self.assertEqual(v36_hash, hashlib.sha256(V36_PATH.read_bytes()).hexdigest())

    def test_v37_registers_inputs_references_runner_tests_and_current_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        required = (
            "evaluation/quality_eval/fta_baseline_manifest_v36.json",
            INPUTS_PATH,
            REFERENCE_PATH,
            RUNNER_PATH,
            "evaluation/quality_eval/test_run_fta_event_scope_semantic_smoke_v1.py",
            "evaluation/quality_eval/build_fta_baseline_manifest_v37.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v37.py",
            "evaluation/quality_eval/validate_fta_baseline_manifest.py",
            "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
            "docs/README.md",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/fta-validation-reliability-plan-v1.md",
        )
        for path in required:
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v36.json"]["lifecycle"])
        self.assertEqual("current_non_gold", artifacts[INPUTS_PATH]["lifecycle"])
        self.assertEqual("current_non_gold_separate", artifacts[REFERENCE_PATH]["lifecycle"])
        self.assertEqual("current_preflight_only", artifacts[RUNNER_PATH]["lifecycle"])

    def test_smoke_labels_remain_separate_and_implicit_gate_cases_literal_free(self) -> None:
        inputs = json.loads((ROOT / INPUTS_PATH).read_text(encoding="utf-8"))
        references = json.loads((ROOT / REFERENCE_PATH).read_text(encoding="utf-8"))
        self.assertEqual(
            {case["case_id"] for case in inputs["cases"]},
            {case["case_id"] for case in references["cases"]},
        )
        self.assertFalse(inputs["guardrails"]["reference_labels_included"])
        self.assertEqual("authored_policy_reference_not_expert_reviewed", references["reference_status"])
        for case in inputs["cases"]:
            model_input = case["model_input"]
            self.assertNotIn("expected_candidate_gate", model_input)
            self.assertNotIn("reference_labels", model_input)
        for case_id in ("SMOKE-001", "SMOKE-002"):
            case = next(item for item in inputs["cases"] if item["case_id"] == case_id)
            text = " ".join(segment["text"] for segment in case["model_input"]["source_segments"])
            self.assertNotRegex(text, r"(?i)\b(?:and|or)\b")


if __name__ == "__main__":
    unittest.main()
