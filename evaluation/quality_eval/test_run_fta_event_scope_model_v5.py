from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluation.quality_eval.event_scope_tree_prompt_v5 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v5 import (
    InferenceRunError,
    preflight,
    run_once,
)
import evaluation.quality_eval.public_sources.run_fta_event_scope_model_v5 as runner_v5


ROOT = Path(__file__).resolve().parents[2]


def _valid_output() -> dict:
    return {
        "structure_status": "unresolved",
        "nodes": [
            {"id": "T", "text": "Top event", "type": "top_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5",
                "quote": "the explosion or structural fragmentation of a battery module",
            }},
            {"id": "A", "text": "Cell explosion", "type": "basic_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5", "quote": "A single cell explosion",
            }},
            {"id": "B", "text": "Container fails to relieve overpressure", "type": "basic_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5", "quote": "the module container fails to operate as designed",
            }},
        ],
        "gates": [{
            "scope_id": "root",
            "output_node_id": "T",
            "child_node_ids": ["A", "B"],
            "gate": "unknown",
            "scope_evidence": {
                "segment_id": "source-pdf-p3-p4-section-5",
                "quote": "A single cell explosion may lead to the Top Event if the module container fails to operate as designed",
            },
            "logic_evidence": None,
            "unknown_reason": "no_direct_logic_evidence",
        }],
        "unresolved_questions": [],
    }


class TestFtaEventScopeRunnerV5(unittest.TestCase):
    def test_preflight_is_offline_and_uses_v5_prompt(self) -> None:
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

    def test_mocked_request_is_single_no_retry_and_persists_only_public_response(self) -> None:
        response_text = json.dumps(_valid_output(), ensure_ascii=False)
        hidden_reasoning = "must not persist hidden reasoning"
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=response_text, reasoning_content=hidden_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=50, completion_tokens=80, total_tokens=130),
            model="deepseek-flash",
            _request_id="request-v5-test",
        )
        create = unittest.mock.Mock(return_value=fake_response)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        fake_openai = SimpleNamespace(OpenAI=unittest.mock.Mock(return_value=fake_client), __version__="test")
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            run_path = temp / "run.json"
            assessment_path = temp / "assessment.json"
            with (
                patch.object(runner_v5, "OPENAI_API_KEY", "test-only-key"),
                patch.object(runner_v5, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner_v5, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner_v5, "OPENAI_TIMEOUT_SECONDS", 30),
                patch.object(runner_v5.importlib.util, "find_spec", return_value=object()),
                patch.dict("sys.modules", {"openai": fake_openai}),
            ):
                result = run_once(
                    packet_path=PACKET_PATH,
                    run_path=run_path,
                    assessment_path=assessment_path,
                    authorize_single_request=True,
                )
            kwargs = create.call_args.kwargs
            self.assertEqual({"type": "disabled"}, kwargs["extra_body"]["thinking"])
            self.assertEqual(1, fake_client.chat.completions.create.call_count)
            self.assertEqual(1, result["request"]["request_count"])
            self.assertEqual(0, result["request"]["retry_count"])
            self.assertEqual(PROMPT_VERSION, result["request"]["prompt_version"])
            self.assertFalse(result["request"]["gold_included_in_model_input"])
            self.assertNotIn(hidden_reasoning, run_path.read_text(encoding="utf-8"))
            self.assertNotIn(hidden_reasoning, assessment_path.read_text(encoding="utf-8"))
            self.assertTrue(run_path.with_name("run.attempt.json").exists())


if __name__ == "__main__":
    unittest.main()
