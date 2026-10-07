from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from probe_fta_gate_text_evidence_abstention_v1 import (  # noqa: E402
    DATASET,
    build_prompt,
    load_fixture,
    parse_model_output,
    run_probe,
)

EXTENSION_DATASET = DATASET.with_name("fta_gate_text_evidence_abstention_extension_v1.json")
EXTENSION_V2_DATASET = DATASET.with_name("fta_gate_text_evidence_abstention_extension_v2.json")
EVIDENCE_ABLATION_DATASET = DATASET.with_name("fta_gate_text_evidence_ablation_v1.json")


class TextEvidenceAbstentionProbeTests(unittest.TestCase):
    def test_fixture_covers_three_unknown_sources_and_one_explicit_or_control(self) -> None:
        fixture, _ = load_fixture(DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]
        self.assertEqual(fixture["source_document_count"], 4)
        self.assertEqual(fixture["source_cluster_count"], 4)
        self.assertEqual(labels.count("unknown"), 3)
        self.assertEqual(labels.count("OR"), 1)
        self.assertFalse(fixture["formal_gold"])

    def test_prompt_withholds_label_provenance_and_source_identity(self) -> None:
        fixture, _ = load_fixture(DATASET)
        row = fixture["gate_nodes"][0]
        prompt = build_prompt(row)
        payload = json.loads(prompt[prompt.index("{") :])
        self.assertEqual(set(payload), {"parent_event", "direct_child_events", "source_scope_evidence"})
        self.assertNotIn(row["expected_gate"], payload.values())
        self.assertNotIn(row["source_id"], prompt)
        self.assertNotIn(row["gate_node_id"], prompt)
        self.assertIn("possible causes", prompt)
        self.assertIn("gate_evidence_quote 必须为 null", prompt)

    def test_label_gate_evidence_must_be_in_the_candidate_cause_scope(self) -> None:
        fixture, _ = load_fixture(DATASET)
        row = fixture["gate_nodes"][-1]
        self.assertIn(row["expected_gate_evidence"], row["candidate_set_evidence"])
        self.assertNotIn("Cabin temperature too high or too low", row["expected_gate_evidence"])

    def test_extension_adds_explicit_and_and_an_independent_unknown_case(self) -> None:
        fixture, _ = load_fixture(EXTENSION_DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]
        self.assertEqual(fixture["source_document_count"], 2)
        self.assertEqual(fixture["source_cluster_count"], 2)
        self.assertEqual(len(fixture["gate_nodes"]), 2)
        self.assertEqual(labels.count("AND"), 1)
        self.assertEqual(labels.count("unknown"), 1)
        self.assertFalse(fixture["formal_gold"])

        and_row, unknown_row = fixture["gate_nodes"]
        self.assertIn("both", and_row["expected_gate_evidence"])
        self.assertIn("must occur", and_row["expected_gate_evidence"])
        self.assertIn(and_row["expected_gate_evidence"], and_row["candidate_set_evidence"])
        self.assertIn("possible causes", unknown_row["candidate_set_evidence"])
        self.assertIn(" and ", unknown_row["candidate_set_evidence"])
        self.assertIsNone(unknown_row["expected_gate_evidence"])

    def test_extension_v2_covers_paraphrased_gates_and_conjunction_near_misses(self) -> None:
        fixture, _ = load_fixture(EXTENSION_V2_DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]
        self.assertEqual(fixture["source_document_count"], 5)
        self.assertEqual(fixture["source_cluster_count"], 5)
        self.assertEqual(len(fixture["gate_nodes"]), 6)
        self.assertEqual(labels.count("AND"), 3)
        self.assertEqual(labels.count("OR"), 1)
        self.assertEqual(labels.count("unknown"), 2)
        self.assertFalse(fixture["formal_gold"])

        nodes = {row["gate_node_id"]: row for row in fixture["gate_nodes"]}
        resistor_and = nodes["NASA-VESELY-RESISTOR-CRITICAL-PATH-AND-001"]
        self.assertIn("must fail in Mode A", resistor_and["expected_gate_evidence"])
        self.assertEqual(len(resistor_and["children"]), 2)

        all_inputs = nodes["NASA-TM86404-CAREIII-ALL-EVENTS-AND-001"]
        self.assertIn("all events", all_inputs["expected_gate_evidence"])
        self.assertEqual(len(all_inputs["children"]), 14)

        any_input = nodes["NASA-TM86404-CAREIII-ANY-INPUT-OR-001"]
        self.assertIn("if any of the events", any_input["candidate_set_evidence"])
        self.assertIn("event k occurs", any_input["candidate_set_evidence"])
        self.assertEqual(len(any_input["children"]), 14)

        possible_causes = nodes["NASA-TM111876-CONDENSATE-POSSIBLE-CAUSE-LIST-UNKNOWN-001"]
        self.assertIn("Possible causes include", possible_causes["candidate_set_evidence"])
        self.assertIsNone(possible_causes["expected_gate_evidence"])
        abstract_source = next(
            source for source in fixture["sources"] if source["source_id"] == "NASA_TM_111876_CONDENSATE"
        )
        self.assertIsNone(abstract_source["source_pdf_sha256"])
        self.assertEqual(len(abstract_source["source_text_sha256"]), 64)

        co_occurring_states = nodes["NASA-APOLLO13-PRESSURE-TEMPERATURE-RUPTURE-UNKNOWN-001"]
        self.assertIn("pressure and a temperature", co_occurring_states["candidate_set_evidence"])
        self.assertIsNone(co_occurring_states["expected_gate_evidence"])

    def test_evidence_ablation_pairs_with_known_gates_without_leaking_decisive_text(self) -> None:
        ablation, _ = load_fixture(EVIDENCE_ABLATION_DATASET)
        original_fixtures = [DATASET, EXTENSION_DATASET, EXTENSION_V2_DATASET]
        originals = {}
        for path in original_fixtures:
            fixture, _ = load_fixture(path)
            originals.update({row["gate_node_id"]: row for row in fixture["gate_nodes"]})

        self.assertEqual(ablation["source_document_count"], 5)
        self.assertEqual(ablation["source_cluster_count"], 5)
        self.assertEqual(len(ablation["gate_nodes"]), 6)
        self.assertTrue(all(row["expected_gate"] == "unknown" for row in ablation["gate_nodes"]))

        for row in ablation["gate_nodes"]:
            paired = originals[row["paired_original_node_id"]]
            self.assertIn(paired["expected_gate"], {"AND", "OR"})
            self.assertEqual(row["parent_event"], paired["parent_event"])
            self.assertEqual(row["children"], paired["children"])
            self.assertFalse(row.get("candidate_set_heading"))
            self.assertFalse(row["candidate_set_evidence"])
            prompt = build_prompt(row)
            self.assertNotIn(paired["expected_gate_evidence"], prompt)
            self.assertNotIn(row["paired_original_node_id"], prompt)
            self.assertNotIn(row["source_id"], prompt)

    def test_model_output_contract_requires_finite_normalized_distribution(self) -> None:
        probabilities, quote, reason = parse_model_output(
            '{"gate_probabilities":{"AND":0.02,"OR":0.03,"unknown":0.95},"gate_evidence_quote":null,"reason":"no relation stated"}'
        )
        self.assertEqual(probabilities["unknown"], 0.95)
        self.assertIsNone(quote)
        self.assertEqual(reason, "no relation stated")
        with self.assertRaises(ValueError):
            parse_model_output('{"gate_probabilities":{"AND":0.2,"OR":0.2,"unknown":0.2},"gate_evidence_quote":null}')

    def test_summary_distinguishes_unknown_false_accept_from_or_positive_control(self) -> None:
        fixture, _ = load_fixture(DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]

        class ExpectedLabelsTestDouble:
            def __init__(self) -> None:
                self.index = 0

            def complete(self, _prompt: str) -> str:
                label = labels[self.index]
                self.index += 1
                probs = {"AND": 0.02, "OR": 0.03, "unknown": 0.95}
                quote = None
                if label == "OR":
                    probs = {"AND": 0.02, "OR": 0.96, "unknown": 0.02}
                    quote = fixture["gate_nodes"][self.index - 1]["expected_gate_evidence"]
                return json.dumps({"gate_probabilities": probs, "gate_evidence_quote": quote, "reason": "test double"})

        artifact = run_probe(fixture, ExpectedLabelsTestDouble(), model_id="test-only", provider_host=None)
        self.assertEqual(artifact["status"], "completed")
        self.assertEqual(artifact["summary"]["top1_accuracy"], 1.0)
        self.assertEqual(artifact["summary"]["unknown_recall"], 1.0)
        self.assertEqual(artifact["summary"]["unknown_unsafe_accept_count"], 0)
        self.assertEqual(artifact["summary"]["known_gate_correct_count"], 1)
        self.assertEqual(artifact["summary"]["decisive_quote_substring_match_count"], 1)
        self.assertFalse(artifact["fta_ready"])


if __name__ == "__main__":
    unittest.main()
