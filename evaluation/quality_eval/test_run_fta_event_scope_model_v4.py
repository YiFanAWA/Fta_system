from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluation.quality_eval.event_scope_tree_prompt_v4 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v4 import (
    InferenceRunError,
    _evidence_check,
    assess_output,
    preflight,
    run_once,
)
import evaluation.quality_eval.public_sources.run_fta_event_scope_model_v4 as runner_v4


ROOT = Path(__file__).resolve().parents[2]


def _valid_output() -> dict:
    return {
        "structure_status": "complete",
        "nodes": [
            {"id": "T", "text": "Top event", "type": "top_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5",
                "quote": "the explosion or structural fragmentation of a battery module",
            }},
            {"id": "A", "text": "Cell explosion", "type": "basic_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5", "quote": "A single cell explosion",
            }},
            {"id": "B", "text": "Vent failure", "type": "basic_event", "evidence": {
                "segment_id": "source-pdf-p3-p4-section-5", "quote": "the module container fails to operate as designed",
            }},
        ],
        "gates": [{
            "scope_id": "root",
            "output_node_id": "T",
            "child_node_ids": ["A", "B"],
            "gate": "AND",
            "scope_evidence": {
                "segment_id": "source-pdf-p3-p4-section-5",
                "quote": "A single cell explosion may lead to the Top Event if the module container fails to operate as designed",
            },
            "logic_evidence": {
                "segment_id": "source-pdf-p3-p4-section-5", "quote": "if the module container fails to operate as designed",
            },
            "unknown_reason": None,
        }],
        "unresolved_questions": [],
    }


class TestFtaEventScopeRunnerV4(unittest.TestCase):
    def test_preflight_uses_new_prompt_and_is_offline(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        prompt = build_prompt(model_input_payload(packet))
        result = preflight(PACKET_PATH)
        self.assertEqual("event-scope-text-only-tree-v4-located-evidence", PROMPT_VERSION)
        self.assertEqual(PROMPT_VERSION, result["prompt_version"])
        self.assertEqual(len(prompt), result["prompt_char_count"])
        self.assertFalse(result["gold_included_in_model_input"])
        self.assertFalse(result["live_request_performed"])
        self.assertIn('"scope_evidence"', prompt)
        self.assertIn('"evidence":{"segment_id"', prompt)
        self.assertNotIn('"parent_id"', prompt)

    def test_evidence_must_be_unique_in_referenced_input_segment(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        output = _valid_output()
        result = _evidence_check(output, model_input)
        self.assertEqual([], result["blockers"])
        self.assertEqual(result["checked"], result["valid"])

        output["nodes"][1]["evidence"]["quote"] = "battery"
        repeated = _evidence_check(output, model_input)
        self.assertIn("evidence_quote_not_unique_in_segment", {item["code"] for item in repeated["blockers"]})

    def test_unknown_gate_may_omit_logic_quote_but_needs_reason(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        output = _valid_output()
        output["gates"][0]["gate"] = "unknown"
        output["gates"][0]["logic_evidence"] = None
        output["gates"][0]["unknown_reason"] = "no_direct_logic_evidence"
        result = _evidence_check(output, model_input)
        self.assertEqual([], result["blockers"])

        output["gates"][0]["unknown_reason"] = None
        result = _evidence_check(output, model_input)
        self.assertIn("evidence_object_required", {item["code"] for item in result["blockers"]})

    def test_unknown_gate_cannot_claim_direct_logic_quote(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        output = _valid_output()
        output["gates"][0]["gate"] = "unknown"
        output["gates"][0]["unknown_reason"] = "no_direct_logic_evidence"
        result = _evidence_check(output, model_input)
        self.assertIn("unknown_gate_must_not_claim_logic_evidence", {item["code"] for item in result["blockers"]})

    def test_hierarchy_blocker_is_not_repaired_or_hidden_by_assessment(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        model_input = model_input_payload(packet)
        output = _valid_output()
        output["nodes"][1]["parent_id"] = "B"
        before = copy.deepcopy(output)
        result = assess_output({"request": {"finish_reason": "stop"}, "model_output": {"parsed_json": output}}, model_input)
        self.assertEqual("blocked", result["assessment_status"])
        self.assertIn("parent_id_conflicts_with_gate_scope", {item["code"] for item in result["combined_blockers"]})
        self.assertEqual(before, output)

    def test_live_request_requires_explicit_authorization(self) -> None:
        with self.assertRaisesRegex(InferenceRunError, "explicit authorization"):
            run_once(authorize_single_request=False)

    def test_mocked_request_is_one_shot_thinking_disabled_and_does_not_persist_reasoning(self) -> None:
        response_text = json.dumps(_valid_output(), ensure_ascii=False)
        hidden_reasoning = "must not persist hidden reasoning"
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=response_text, reasoning_content=hidden_reasoning),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=50, completion_tokens=80, total_tokens=130),
            model="deepseek-flash",
            _request_id="request-v4-test",
        )
        create = unittest.mock.Mock(return_value=fake_response)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        fake_openai = SimpleNamespace(OpenAI=unittest.mock.Mock(return_value=fake_client), __version__="test")
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp = Path(temp_dir)
            run_path = temp / "run.json"
            assessment_path = temp / "assessment.json"
            with (
                patch.object(runner_v4, "OPENAI_API_KEY", "test-only-key"),
                patch.object(runner_v4, "OPENAI_API_BASE", "https://api.deepseek.com"),
                patch.object(runner_v4, "OPENAI_MODEL", "deepseek-flash"),
                patch.object(runner_v4, "OPENAI_TIMEOUT_SECONDS", 30),
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
