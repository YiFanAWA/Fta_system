from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from evaluation.quality_eval.public_sources.run_fta_event_scope_semantic_smoke_v1 import (
    INPUT_DATASET_PATH,
    SmokeRunError,
    load_case,
    preflight,
    run_once,
)
from evaluation.quality_eval.event_scope_tree_prompt_v8 import build_prompt
import evaluation.quality_eval.public_sources.run_fta_event_scope_semantic_smoke_v1 as runner


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json"


class TestFtaEventScopeSemanticSmokeRunnerV1(unittest.TestCase):
    def test_input_and_reference_are_separate_and_non_gold(self) -> None:
        input_data = json.loads(INPUT_DATASET_PATH.read_text(encoding="utf-8"))
        reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        input_ids = {case["case_id"] for case in input_data["cases"]}
        reference_ids = {case["case_id"] for case in reference["cases"]}

        self.assertEqual(input_ids, reference_ids)
        self.assertEqual(5, len(input_ids))
        self.assertFalse(input_data["human_expert_gold"])
        self.assertFalse(input_data["accuracy_claim_allowed"])
        self.assertFalse(reference["human_expert_gold"])
        self.assertFalse(reference["accuracy_claim_allowed"])
        self.assertFalse(input_data["guardrails"]["reference_labels_included"])
        self.assertNotIn("expected_candidate_gate", INPUT_DATASET_PATH.read_text(encoding="utf-8"))
        runner_source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("REFERENCE_PATH", runner_source)
        for case in input_data["cases"]:
            prompt = build_prompt(case["model_input"])
            self.assertNotIn("expected_candidate_gate", prompt)
            self.assertNotIn("authored_policy_reference_not_expert_reviewed", prompt)

    def test_implicit_or_and_cases_have_no_literal_operator_tokens(self) -> None:
        or_case, _ = load_case("SMOKE-001")
        and_case, _ = load_case("SMOKE-002")
        or_source = " ".join(segment["text"] for segment in or_case["model_input"]["source_segments"])
        and_source = " ".join(segment["text"] for segment in and_case["model_input"]["source_segments"])
        self.assertIsNone(re.search(r"\b(?:or|and)\b", or_source, re.IGNORECASE))
        self.assertIsNone(re.search(r"\b(?:or|and)\b", and_source, re.IGNORECASE))

    def test_preflight_is_offline_one_case_and_never_loads_reference_labels(self) -> None:
        input_data = json.loads(INPUT_DATASET_PATH.read_text(encoding="utf-8"))
        for case in input_data["cases"]:
            result = preflight(case["case_id"])
            self.assertEqual("event-scope-text-only-tree-v8-semantic-gate-evidence", result["prompt_version"])
            self.assertEqual(1, result["request_count"])
            self.assertEqual(0, result["sdk_max_retries"])
            self.assertEqual("disabled", result["thinking_mode"]["type"])
            self.assertFalse(result["reference_labels_loaded"])
            self.assertFalse(result["gold_included_in_model_input"])
            self.assertFalse(result["live_request_performed"])

    def test_invalid_input_with_answer_label_is_rejected_before_any_request(self) -> None:
        payload = json.loads(INPUT_DATASET_PATH.read_text(encoding="utf-8"))
        payload["cases"][0]["model_input"]["expected_gate"] = "OR"
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            bad_path = Path(temp_dir) / "bad_input.json"
            bad_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(SmokeRunError, "model_input has an invalid top-level shape"):
                load_case("SMOKE-001", bad_path)

    def test_live_request_requires_explicit_single_request_authorization(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            paths = (temp / "run.json", temp / "assessment.json", temp / "attempt.json")
            with patch.object(runner, "_artifact_paths", return_value=paths):
                with self.assertRaisesRegex(SmokeRunError, "explicit authorization"):
                    run_once(case_id="SMOKE-001", authorize_single_request=False)
            self.assertFalse(any(path.exists() for path in paths))

    def test_malformed_response_is_preserved_blocked_and_not_retried_or_repaired(self) -> None:
        response_text = "not strict json"
        hidden_reasoning = "private reasoning that must not be stored"
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=response_text, reasoning_content=hidden_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=20, completion_tokens=10, total_tokens=30),
            model="deepseek-flash",
            _request_id="smoke-test-request",
        )
        create = Mock(return_value=fake_response)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        fake_openai = SimpleNamespace(OpenAI=Mock(return_value=fake_client), __version__="test")

        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            paths = (temp / "run.json", temp / "assessment.json", temp / "attempt.json")
            with (
                patch.object(runner, "_artifact_paths", return_value=paths),
                patch.object(runner, "OPENAI_API_KEY", "test-only-key"),
                patch.object(runner, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner, "OPENAI_TIMEOUT_SECONDS", 30),
                patch.object(runner.importlib.util, "find_spec", return_value=object()),
                patch.dict("sys.modules", {"openai": fake_openai}),
            ):
                result = run_once(case_id="SMOKE-001", authorize_single_request=True)

            saved = json.loads(paths[0].read_text(encoding="utf-8"))
            assessment = json.loads(paths[1].read_text(encoding="utf-8"))
            receipt = json.loads(paths[2].read_text(encoding="utf-8"))
            self.assertEqual(1, create.call_count)
            self.assertEqual(1, result["request"]["request_count"])
            self.assertEqual(0, result["request"]["retry_count"])
            self.assertEqual(response_text, saved["model_output"]["raw_text"])
            self.assertEqual("response_is_not_strict_json", saved["model_output"]["parse_error"])
            self.assertEqual("no_usable_json", assessment["output_assessment"]["assessment_status"])
            self.assertFalse(assessment["automatic_repair_performed"])
            self.assertFalse(assessment["automatic_retry_performed"])
            self.assertFalse(assessment["reference_comparison_performed"])
            self.assertFalse(receipt["reference_labels_loaded"])
            self.assertNotIn(hidden_reasoning, paths[0].read_text(encoding="utf-8"))
            self.assertNotIn(hidden_reasoning, paths[1].read_text(encoding="utf-8"))

    def test_existing_attempt_artifact_prevents_duplicate_request(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            paths = (temp / "run.json", temp / "assessment.json", temp / "attempt.json")
            paths[2].write_text("{}", encoding="utf-8")
            with patch.object(runner, "_artifact_paths", return_value=paths):
                with self.assertRaisesRegex(SmokeRunError, "refusing a duplicate"):
                    run_once(case_id="SMOKE-001", authorize_single_request=True)


if __name__ == "__main__":
    unittest.main()
