from __future__ import annotations

import json
import unittest

from evaluation.quality_eval.event_scope_tree_prompt_v5 import PROMPT_VERSION, build_prompt
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH


class TestEventScopeTreePromptV5(unittest.TestCase):
    def test_conditional_condition_is_not_misattached_as_antecedent_child(self) -> None:
        prompt = build_prompt({"top_event": {"text": "T"}, "source_segments": []})
        self.assertIn("B 不是导致 A 发生的子事件", prompt)
        self.assertIn("不得建立 output=A、child=B 的 scope", prompt)
        self.assertIn("A 与 B 是共同参与通向 T 的条件", prompt)

    def test_alternative_paths_are_kept_as_complete_scoped_combinations(self) -> None:
        prompt = build_prompt({"top_event": {"text": "T"}, "source_segments": []})
        self.assertIn("(A AND B) OR (C AND D)", prompt)
        self.assertIn("不要把第一条路径塞进第二条路径的子项", prompt)
        self.assertIn("不得把一个节点挂到多个父 scope", prompt)

    def test_prompt_contains_only_the_validated_model_input_projection(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        projected = model_input_payload(packet)
        prompt = build_prompt(projected)
        payload = json.loads(prompt.split("输入 JSON：\n", 1)[1])
        self.assertEqual(projected, payload)
        self.assertNotIn("diagram_gates", prompt)
        self.assertNotIn("text_gate_reviews", prompt)
        self.assertEqual("event-scope-text-only-tree-v5-causal-path-scope", PROMPT_VERSION)


if __name__ == "__main__":
    unittest.main()
