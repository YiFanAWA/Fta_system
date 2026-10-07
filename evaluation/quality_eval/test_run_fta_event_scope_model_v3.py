from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import build_prompt
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v3 import (
    MAX_TOKENS,
    RESPONSE_FORMAT,
    SDK_MAX_RETRIES,
    THINKING_MODE,
    InferenceRunError,
    assess_v3_output,
    preflight,
    response_diagnostics,
    run_once,
)
import evaluation.quality_eval.public_sources.run_fta_event_scope_model_v3 as runner_v3


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"


class TestFtaEventScopeOneShotRunnerV3(unittest.TestCase):
    def test_preflight_keeps_v2_payload_settings_and_disables_thinking(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        prompt = build_prompt(model_input)
        result = preflight(PACKET)
        self.assertEqual(8192, MAX_TOKENS)
        self.assertEqual({"type": "json_object"}, RESPONSE_FORMAT)
        self.assertEqual({"type": "disabled"}, THINKING_MODE)
        self.assertEqual(0, SDK_MAX_RETRIES)
        self.assertEqual(hashlib_sha256(prompt), result["prompt_sha256"])
        self.assertEqual("event-scope-text-only-tree-v2-compact-json", result["prompt_version"])
        self.assertIn("only thinking mode", result["comparison_lock"])
        self.assertNotIn("diagram_gates", str(model_input))

    def test_diagnostics_capture_reasoning_presence_and_counts_without_text(self) -> None:
        secret_reasoning = "private model reasoning that must not be persisted"
        response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content='{"nodes":[],"gates":[]}', reasoning_content=secret_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(
                prompt_tokens=12,
                completion_tokens=18,
                total_tokens=30,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=7),
            ),
            model="deepseek-flash",
            _request_id="request-test-id",
        )
        text, _message, diagnostics = response_diagnostics(response)
        serialized = json.dumps(diagnostics)
        self.assertEqual('{"nodes":[],"gates":[]}', text)
        self.assertTrue(diagnostics["reasoning_content_present"])
        self.assertEqual(len(secret_reasoning), diagnostics["reasoning_content_character_count"])
        self.assertEqual(7, diagnostics["reasoning_tokens"])
        self.assertFalse(diagnostics["reasoning_text_persisted"])
        self.assertNotIn(secret_reasoning, serialized)

    def test_diagnostics_tolerate_missing_reasoning_metadata(self) -> None:
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}"), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=2, total_tokens=4),
            model="deepseek-flash",
            _request_id=None,
        )
        _text, _message, diagnostics = response_diagnostics(response)
        self.assertFalse(diagnostics["reasoning_content_present"])
        self.assertEqual(0, diagnostics["reasoning_content_character_count"])
        self.assertIsNone(diagnostics["reasoning_tokens"])

    def test_empty_body_is_distinguished_from_truncation(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        result = {
            "request": {"finish_reason": "stop"},
            "model_output": {"raw_text": "", "parsed_json": None},
        }
        assessment = assess_v3_output(result, model_input)
        self.assertEqual("empty_content", assessment["assessment_status"])
        self.assertIn("no_usable_json_object", assessment["structural_errors"])
        self.assertEqual("not_performed", assessment["gold_comparison"])

    def test_malformed_json_shape_fails_closed_without_crashing(self) -> None:
        packet = json.loads(PACKET.read_text(encoding="utf-8"))
        result = {
            "request": {"finish_reason": "stop"},
            "model_output": {"raw_text": '{"nodes":[{"id":[]}],"gates":[]}', "parsed_json": {"nodes": [{"id": []}], "gates": []}},
        }
        assessment = assess_v3_output(result, model_input_payload(packet))
        self.assertEqual("structurally_invalid", assessment["assessment_status"])
        self.assertIn("malformed_model_output_shape", assessment["structural_errors"])
        self.assertEqual("not_performed", assessment["gold_comparison"])

    def test_live_request_requires_explicit_credential_rotation_confirmation(self) -> None:
        with self.assertRaisesRegex(InferenceRunError, "credential rotation must be confirmed"):
            run_once(confirm_credential_rotated=False)

    def test_artifact_paths_outside_repository_are_rejected_before_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            outside_run = Path(temp_dir) / "run.json"
            with self.assertRaisesRegex(InferenceRunError, "must stay inside the repository"):
                run_once(run_path=outside_run, confirm_credential_rotated=True)

    def test_mocked_request_sends_only_controlled_change_and_never_saves_reasoning(self) -> None:
        answer = '{"nodes":[{"id":"E1","text":"top","type":"top_event","parent_id":null,"evidence_quote":null}],"gates":[],"unresolved_questions":[]}'
        hidden_reasoning = "must not appear in saved artifacts"
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=answer, reasoning_content=hidden_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(
                prompt_tokens=20,
                completion_tokens=40,
                total_tokens=60,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
            ),
            model="deepseek-flash",
            _request_id="request-test-id",
        )
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=unittest.mock.Mock(return_value=fake_response))
            )
        )
        fake_openai = SimpleNamespace(OpenAI=unittest.mock.Mock(return_value=fake_client), __version__="test")
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            run_path = temp / "run.json"
            assessment_path = temp / "assessment.json"
            with (
                patch.object(runner_v3, "OPENAI_API_KEY", "test-only-not-a-real-key"),
                patch.object(runner_v3, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner_v3, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner_v3, "OPENAI_TIMEOUT_SECONDS", 30),
                patch.dict("sys.modules", {"openai": fake_openai}),
            ):
                result = run_once(
                    packet_path=PACKET,
                    run_path=run_path,
                    assessment_path=assessment_path,
                    confirm_credential_rotated=True,
                )
            call = fake_client.chat.completions.create.call_args.kwargs
            self.assertEqual({"type": "disabled"}, call["extra_body"]["thinking"])
            self.assertEqual(8192, call["max_tokens"])
            self.assertEqual({"type": "json_object"}, call["response_format"])
            self.assertEqual(1, result["request"]["request_count"])
            self.assertEqual(0, result["request"]["retry_count"])
            self.assertTrue(result["request"]["reasoning_content_present"])
            self.assertFalse(result["request"]["reasoning_text_persisted"])
            self.assertNotIn(hidden_reasoning, run_path.read_text(encoding="utf-8"))
            self.assertNotIn(hidden_reasoning, assessment_path.read_text(encoding="utf-8"))
            self.assertNotIn(hidden_reasoning, run_path.with_name("run.attempt.json").read_text(encoding="utf-8"))


def hashlib_sha256(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    unittest.main()
