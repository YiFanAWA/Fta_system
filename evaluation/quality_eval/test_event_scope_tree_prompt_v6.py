from __future__ import annotations

import json
import unittest

from evaluation.quality_eval.event_scope_tree_contract import validate_event_scope_tree
from evaluation.quality_eval.event_scope_tree_prompt_v6 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH


def _nested_alternative_tree() -> dict:
    return {
        "structure_status": "complete",
        "nodes": [
            {"id": "T", "text": "T", "type": "top_event"},
            {"id": "P1", "text": "Path one", "type": "intermediate_event"},
            {"id": "A", "text": "A", "type": "basic_event"},
            {"id": "B", "text": "B", "type": "basic_event"},
            {"id": "P2", "text": "Path two", "type": "intermediate_event"},
            {"id": "C", "text": "C", "type": "basic_event"},
            {"id": "D", "text": "D", "type": "basic_event"},
        ],
        "gates": [
            {"scope_id": "root", "output_node_id": "T", "child_node_ids": ["P1", "P2"], "gate": "OR"},
            {"scope_id": "p1", "output_node_id": "P1", "child_node_ids": ["A", "B"], "gate": "unknown"},
            {"scope_id": "p2", "output_node_id": "P2", "child_node_ids": ["C", "D"], "gate": "unknown"},
        ],
    }


class TestEventScopeTreePromptV6(unittest.TestCase):
    def test_condition_direction_keeps_b_as_condition_for_t(self) -> None:
        prompt = build_prompt({"top_event": {"text": "T"}, "source_segments": []})
        self.assertIn("B 不是导致 A 的子事件", prompt)
        self.assertIn("不得建立 output=A、child=B 的 scope", prompt)
        self.assertIn("A 与 B 都是通向 T 的相关条件", prompt)

    def test_single_hierarchy_and_intermediate_path_scopes_are_explicit(self) -> None:
        prompt = build_prompt({"top_event": {"text": "T"}, "source_segments": []})
        self.assertIn("一个 output_node_id 在全份输出中只能出现于一个 gate scope", prompt)
        self.assertIn("顶事件必须只有一个根 scope", prompt)
        self.assertIn("根 T 只建立一个 scope，直接 child 为 P1、P2", prompt)
        self.assertIn("不得为每个句子各自重复创建顶事件 scope", prompt)

    def test_known_gate_requires_explicit_null_unknown_reason(self) -> None:
        prompt = build_prompt({"top_event": {"text": "T"}, "source_segments": []})
        self.assertIn("unknown_reason 必须显式为 JSON null", prompt)
        self.assertIn("不得省略任何字段", prompt)

    def test_nested_alternative_fixture_passes_single_hierarchy_contract(self) -> None:
        result = validate_event_scope_tree(_nested_alternative_tree())
        self.assertTrue(result["valid"], result["blockers"])
        self.assertEqual("P1", result["derived_parent_ids"]["A"])
        self.assertEqual("T", result["derived_parent_ids"]["P1"])

    def test_prompt_contains_only_validated_label_free_projection(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        projected = model_input_payload(packet)
        prompt = build_prompt(projected)
        payload = json.loads(prompt.split("输入 JSON：\n", 1)[1])
        self.assertEqual(projected, payload)
        self.assertNotIn("diagram_gates", prompt)
        self.assertNotIn("text_gate_reviews", prompt)
        self.assertEqual("event-scope-text-only-tree-v6-single-hierarchy", PROMPT_VERSION)


if __name__ == "__main__":
    unittest.main()
