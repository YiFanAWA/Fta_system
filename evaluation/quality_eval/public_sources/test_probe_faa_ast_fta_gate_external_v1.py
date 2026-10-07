from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from probe_faa_ast_fta_gate_external_v1 import (  # noqa: E402
    DATASET,
    build_prompt,
    load_fixture,
    parse_probabilities,
    run_probe,
    summarize,
)


class FaaExternalGateProbeTests(unittest.TestCase):
    def test_fixture_has_thirteen_explicit_nodes_with_expected_distribution(self) -> None:
        fixture, _ = load_fixture(DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]
        self.assertEqual(len(labels), 13)
        self.assertEqual(labels.count("AND"), 3)
        self.assertEqual(labels.count("OR"), 10)

    def test_inference_prompt_contains_only_parent_and_children_not_gold_or_source_cues(self) -> None:
        fixture, _ = load_fixture(DATASET)
        row = fixture["gate_nodes"][0]
        prompt = build_prompt(row)
        case_json = json.loads(prompt[prompt.rfind("{") : prompt.rfind("}") + 1])
        self.assertEqual(set(case_json), {"parent_event", "direct_child_events"})
        self.assertNotIn(row["expected_gate"], case_json.values())
        self.assertNotIn(row["figure_id"], prompt)
        self.assertNotIn(row["gate_node_id"], prompt)

    def test_probability_response_contract(self) -> None:
        probabilities, reason = parse_probabilities(
            '{"gate_probabilities":{"AND":0.7,"OR":0.2,"unknown":0.1},"reason":"all inputs"}'
        )
        self.assertEqual(probabilities["AND"], 0.7)
        self.assertEqual(reason, "all inputs")
        with self.assertRaises(ValueError):
            parse_probabilities('{"gate_probabilities":{"AND":0.7,"OR":0.2,"unknown":0.2}}')

    def test_summary_reports_imbalance_baseline_and_abstentions(self) -> None:
        rows = [
            {"expected_gate": "AND", "predicted_gate": "AND", "gate_probabilities": {"AND": 0.8, "OR": 0.1, "unknown": 0.1}},
            {"expected_gate": "OR", "predicted_gate": "unknown", "gate_probabilities": {"AND": 0.2, "OR": 0.3, "unknown": 0.5}},
            {"expected_gate": "OR", "predicted_gate": "OR", "gate_probabilities": {"AND": 0.1, "OR": 0.8, "unknown": 0.1}},
        ]
        summary = summarize(rows)
        self.assertAlmostEqual(summary["always_OR_baseline_accuracy"], 2 / 3)
        self.assertEqual(summary["unknown_count"], 1)
        self.assertAlmostEqual(summary["decisive_coverage"], 2 / 3)
        self.assertAlmostEqual(summary["exact_accuracy"], 2 / 3)

    def test_run_probe_prediction_schema_matches_summary_schema(self) -> None:
        class AlwaysOrModel:
            def complete(self, _prompt: str) -> str:
                return '{"gate_probabilities":{"AND":0.1,"OR":0.8,"unknown":0.1},"reason":"OR combination"}'

        fixture, _ = load_fixture(DATASET)
        artifact = run_probe(fixture, AlwaysOrModel(), model_id="test-model", provider_host=None)

        self.assertEqual(artifact["status"], "completed")
        self.assertEqual(len(artifact["predictions"]), 13)
        self.assertEqual(artifact["summary"]["sample_count"], 13)
        self.assertTrue(all("expected_gate" in row for row in artifact["predictions"]))


if __name__ == "__main__":
    unittest.main()
