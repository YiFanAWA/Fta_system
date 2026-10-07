from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluation.quality_eval.event_scope_tree_prompt_v6 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v6 import (
    InferenceRunError,
    preflight,
    run_once,
)
import evaluation.quality_eval.public_sources.run_fta_event_scope_model_v6 as runner_v6


ROOT = Path(__file__).resolve().parents[2]


def _blocked_output() -> dict:
    return {
        "structure_status": "unresolved",
        "nodes": [
            {
                "id": "T",
                "text": "Top event",
                "type": "top_event",
                "evidence": {
                    "segment_id": "source-pdf-p3-p4-section-5",
                    "quote": "the explosion or structural fragmentation of a battery module",
                },
            },
            {
                "id": "T",
                "text": "Duplicated node id",
                "type": "basic_event",
                "evidence": {
                    "segment_id": "source-pdf-p3-p4-section-5",
                    "quote": "A single cell explosion",
                },
            }
        ],
        "gates": [],
        "unresolved_questions": ["No gate scope was supplied."],
    }


class TestFtaEventScopeRunnerV6(unittest.TestCase):
    def test_preflight_is_offline_and_uses_v6_prompt(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        prompt = build_prompt(model_input_payload(packet))
        result = preflight(PACKET_PATH)
        self.assertEqual(PROMPT_VERSION, result["prompt_version"])
        self.assertEqual(len(prompt), result["prompt_char_count"])
        self.assertFalse(result["gold_included_in_model_input"])
        self.assertFalse(result["live_request_performed"])
        self.assertEqual(1, result["request_count"])
        self.assertEqual(0, result["sdk_max_retries"])

    def test_live_request_requires_explicit_authorization(self) -> None:
        with self.assertRaisesRegex(InferenceRunError, "explicit authorization"):
            run_once(authorize_single_request=False)

    def test_invalid_output_is_preserved_and_blocked_without_repair_or_retry(self) -> None:
        response_text = json.dumps(_blocked_output(), ensure_ascii=False)
        hidden_reasoning = "must not persist hidden reasoning"
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=response_text, reasoning_content=hidden_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=50, completion_tokens=80, total_tokens=130),
            model="deepseek-flash",
            _request_id="request-v6-test",
        )
        create = unittest.mock.Mock(return_value=fake_response)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        fake_openai = SimpleNamespace(OpenAI=unittest.mock.Mock(return_value=fake_client), __version__="test")
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            run_path = temp / "run.json"
            assessment_path = temp / "assessment.json"
            with (
                patch.object(runner_v6, "OPENAI_API_KEY", "test-only-key"),
                patch.object(runner_v6, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner_v6, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner_v6, "OPENAI_TIMEOUT_SECONDS", 30),
                patch.object(runner_v6.importlib.util, "find_spec", return_value=object()),
                patch.dict("sys.modules", {"openai": fake_openai}),
            ):
                result = run_once(
                    packet_path=PACKET_PATH,
                    run_path=run_path,
                    assessment_path=assessment_path,
                    authorize_single_request=True,
                )

            raw_run = json.loads(run_path.read_text(encoding="utf-8"))
            assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
            kwargs = create.call_args.kwargs
            self.assertEqual(1, fake_client.chat.completions.create.call_count)
            self.assertEqual(0, result["request"]["retry_count"])
            self.assertEqual(PROMPT_VERSION, result["request"]["prompt_version"])
            self.assertEqual({"type": "disabled"}, kwargs["extra_body"]["thinking"])
            self.assertEqual(response_text, raw_run["model_output"]["raw_text"])
            self.assertEqual("blocked", assessment["output_assessment"]["assessment_status"])
            self.assertTrue(assessment["raw_model_output_preserved"])
            self.assertFalse(assessment["automatic_repair_performed"])
            self.assertFalse(assessment["automatic_retry_performed"])
            self.assertNotIn(hidden_reasoning, run_path.read_text(encoding="utf-8"))
            self.assertNotIn(hidden_reasoning, assessment_path.read_text(encoding="utf-8"))
            self.assertTrue(run_path.with_name("run.attempt.json").exists())

    def test_existing_artifacts_prevent_a_second_request(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            run_path = temp / "run.json"
            run_path.write_text("{}", encoding="utf-8")
            with (
                patch.object(runner_v6, "OPENAI_API_KEY", "test-only-key"),
                patch.object(runner_v6, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner_v6, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner_v6.importlib.util, "find_spec", return_value=object()),
            ):
                with self.assertRaisesRegex(InferenceRunError, "refusing a duplicate"):
                    run_once(
                        packet_path=PACKET_PATH,
                        run_path=run_path,
                        assessment_path=temp / "assessment.json",
                        authorize_single_request=True,
                    )


if __name__ == "__main__":
    unittest.main()
