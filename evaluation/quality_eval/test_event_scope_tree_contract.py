from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from evaluation.quality_eval.event_scope_tree_contract import validate_event_scope_tree
from evaluation.quality_eval.event_scope_tree_prompt_v3 import PROMPT_VERSION, build_prompt


ROOT = Path(__file__).resolve().parents[2]
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json"
PACKET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"


def _valid_nested_tree() -> dict:
    return {
        "structure_status": "complete",
        "nodes": [
            {"id": "T", "text": "Top", "type": "top_event"},
            {"id": "B1", "text": "Branch one", "type": "intermediate_event"},
            {"id": "A", "text": "A", "type": "basic_event"},
            {"id": "B", "text": "B", "type": "basic_event"},
            {"id": "B2", "text": "Branch two", "type": "intermediate_event"},
            {"id": "C", "text": "C", "type": "basic_event"},
            {"id": "D", "text": "D", "type": "basic_event"},
        ],
        "gates": [
            {"scope_id": "root", "output_node_id": "T", "child_node_ids": ["B1", "B2"], "gate": "OR"},
            {"scope_id": "branch-1", "output_node_id": "B1", "child_node_ids": ["A", "B"], "gate": "AND"},
            {"scope_id": "branch-2", "output_node_id": "B2", "child_node_ids": ["C", "D"], "gate": "AND"},
        ],
    }


class TestEventScopeTreeContract(unittest.TestCase):
    def test_nested_or_of_and_tree_passes_with_gate_scopes_as_only_hierarchy(self) -> None:
        result = validate_event_scope_tree(_valid_nested_tree())
        self.assertTrue(result["valid"], result["blockers"])
        self.assertEqual("gate_scopes", result["hierarchy_owner"])
        self.assertIsNone(result["derived_parent_ids"]["T"])
        self.assertEqual("T", result["derived_parent_ids"]["B1"])

    def test_v3_run_is_blocked_for_conflicting_parent_and_gate_scope_and_single_child_scopes(self) -> None:
        run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
        output = run["model_output"]["parsed_json"]
        result = validate_event_scope_tree(output)
        codes = {item["code"] for item in result["blockers"]}
        self.assertFalse(result["valid"])
        self.assertIn("node_has_multiple_parent_scopes", codes)
        self.assertIn("parent_id_conflicts_with_gate_scope", codes)
        self.assertIn("gate_scope_requires_at_least_two_children", codes)
        self.assertFalse(result["output_mutated"])

    def test_conflicting_parent_id_is_not_repaired(self) -> None:
        output = _valid_nested_tree()
        output["nodes"][2]["parent_id"] = "B2"
        before = copy.deepcopy(output)
        result = validate_event_scope_tree(output)
        self.assertFalse(result["valid"])
        self.assertIn("parent_id_conflicts_with_gate_scope", {item["code"] for item in result["blockers"]})
        self.assertEqual("B2", output["nodes"][2]["parent_id"])
        self.assertEqual(before, output)

    def test_unhashable_child_identifier_is_rejected_without_exception(self) -> None:
        output = _valid_nested_tree()
        output["gates"][0]["child_node_ids"][0] = {"id": "B1"}
        result = validate_event_scope_tree(output)
        self.assertFalse(result["valid"])
        self.assertIn("gate_child_node_id_must_be_string", {item["code"] for item in result["blockers"]})

    def test_unhashable_gate_output_identifier_is_rejected_without_exception(self) -> None:
        output = _valid_nested_tree()
        output["gates"][0]["output_node_id"] = ["T"]
        result = validate_event_scope_tree(output)
        self.assertFalse(result["valid"])
        self.assertIn("gate_output_node_id_required", {item["code"] for item in result["blockers"]})

    def test_node_cannot_be_output_of_multiple_gate_scopes(self) -> None:
        output = _valid_nested_tree()
        output["gates"].append({
            "scope_id": "duplicate-output",
            "output_node_id": "B1",
            "child_node_ids": ["C", "D"],
            "gate": "OR",
        })
        result = validate_event_scope_tree(output)
        self.assertFalse(result["valid"])
        self.assertIn("node_has_multiple_output_scopes", {item["code"] for item in result["blockers"]})

    def test_cycle_in_gate_scope_hierarchy_is_rejected(self) -> None:
        output = _valid_nested_tree()
        output["gates"][1]["child_node_ids"] = ["T", "B"]
        result = validate_event_scope_tree(output)
        self.assertFalse(result["valid"])
        self.assertIn("gate_scope_hierarchy_contains_cycle", {item["code"] for item in result["blockers"]})

    def test_complete_status_cannot_claim_a_blocked_structure(self) -> None:
        output = _valid_nested_tree()
        output["gates"][0]["child_node_ids"] = ["B1"]
        result = validate_event_scope_tree(output)
        self.assertIn("complete_structure_status_has_blockers", {item["code"] for item in result["blockers"]})

    def test_reference_input_is_real_packet_and_prompt_excludes_parent_id(self) -> None:
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        prompt = build_prompt(packet["model_input"])
        self.assertEqual("event-scope-text-only-tree-v3-gate-scopes-canonical", PROMPT_VERSION)
        self.assertIn("gate scopes 是父子层级的唯一事实来源", prompt)
        self.assertIn("每个门 scope 必须有至少两个不同的直接 child", prompt)
        self.assertIn('"nodes":[{"id":"E1"', prompt)
        self.assertNotIn('"parent_id"', prompt)
        self.assertNotIn("text_authorized_gate", prompt)


if __name__ == "__main__":
    unittest.main()
