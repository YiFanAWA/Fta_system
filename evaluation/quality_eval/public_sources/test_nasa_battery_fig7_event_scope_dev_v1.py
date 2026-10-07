from __future__ import annotations

import unittest

from evaluation.quality_eval.fta_event_scope_packet_contract import (
    model_input_payload,
    validate_input_packet,
    validate_reference_gold,
)
from evaluation.quality_eval.public_sources.build_nasa_battery_fig7_event_scope_dev_v1 import build_artifacts


class TestNasaBatteryFigure7DevelopmentCase(unittest.TestCase):
    def setUp(self) -> None:
        artifacts = build_artifacts()
        self.by_name = {path.name: payload for path, payload in artifacts.items()}
        self.packet = self.by_name["fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"]
        self.gold = self.by_name["fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"]
        self.screen = self.by_name["fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29.json"]
        self.review = self.by_name["fta_event_scope_nasa_battery_fig7_ai_role_review_v1_2026-09-29.json"]

    def test_packet_and_separate_gold_satisfy_cross_artifact_contract(self) -> None:
        validate_input_packet(self.packet)
        validate_reference_gold(self.packet, self.gold)

    def test_model_projection_contains_only_source_event_scope(self) -> None:
        projected = model_input_payload(self.packet)
        self.assertEqual({"event_scope_id", "top_event", "source_segments"}, set(projected))
        self.assertNotIn("diagram_gates", str(projected))
        self.assertNotIn("text_authorized_gate", str(projected))
        self.assertNotIn("Module structural failure", projected["source_segments"][0]["text"])

    def test_diagram_reference_and_text_authorization_remain_distinct(self) -> None:
        self.assertEqual(7, len(self.gold["nodes"]))
        repeated = [node for node in self.gold["nodes"] if node["text"] == "Single cell explodes"]
        self.assertEqual(2, len(repeated))
        self.assertEqual(2, len({node["node_id"] for node in repeated}))
        self.assertEqual(3, len(self.gold["diagram_gates"]))
        self.assertEqual(
            ["OR", "AND", "AND"],
            [item["diagram_reference_gate"] for item in self.gold["diagram_gates"]],
        )
        self.assertEqual(
            ["OR", "AND", "unknown"],
            [item["text_authorized_gate"] for item in self.gold["text_gate_reviews"]],
        )
        self.assertEqual(
            {"ai_role_review"},
            {item["review_provenance"]["reviewer_role"] for item in self.gold["text_gate_reviews"]},
        )
        self.assertEqual({"reviewed"}, {item["review_provenance"]["review_status"] for item in self.gold["text_gate_reviews"]})
        self.assertFalse(self.review["reviewer"]["human_expert"])
        self.assertEqual(3, len(self.review["gate_operator_findings"]))
        self.assertTrue(all(item["text_operator_directly_supported"] for item in self.review["gate_operator_findings"]))
        self.assertEqual("scope_ambiguity", self.gold["text_gate_reviews"][2]["unknown_reason"])
        self.assertFalse(self.review["gate_operator_findings"][2]["exact_scope_authorized"])
        self.assertEqual("corrected", self.review["reference_graph_findings"][0]["status"])

    def test_case_is_development_only_and_not_an_accuracy_claim(self) -> None:
        suitability = self.screen["evaluation_suitability"]
        self.assertEqual("seen_development_only", suitability["status"])
        self.assertFalse(suitability["eligible_for_independent_final"])
        self.assertFalse(suitability["model_inference_run"])
        self.assertFalse(suitability["accuracy_claim_allowed"])
        self.assertFalse(suitability["production_or_formal_gold_use_allowed"])
        self.assertFalse(self.screen["source_cluster"]["semantic_overlap_audit_complete"])


if __name__ == "__main__":
    unittest.main()
