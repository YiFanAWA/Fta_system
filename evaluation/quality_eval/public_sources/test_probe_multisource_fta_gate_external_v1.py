from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from fta_gate_external_probe_core import build_prompt  # noqa: E402
from probe_multisource_fta_gate_external_v1 import DATASET, load_fixture, run_probe, source_pdf_map  # noqa: E402


class MultisourceExternalGateProbeTests(unittest.TestCase):
    def test_fixture_has_balanced_known_gate_labels_and_distinct_document_clusters(self) -> None:
        fixture, _ = load_fixture(DATASET)
        self.assertEqual(fixture["source_document_count"], 3)
        self.assertEqual(fixture["source_cluster_count"], 3)
        self.assertEqual(len(fixture["gate_nodes"]), 5)
        self.assertEqual([row["expected_gate"] for row in fixture["gate_nodes"]].count("AND"), 2)
        self.assertEqual([row["expected_gate"] for row in fixture["gate_nodes"]].count("OR"), 3)
        self.assertTrue(all(row["label_evidence"] for row in fixture["gate_nodes"]))

    def test_prompt_withholds_gate_and_source_metadata(self) -> None:
        fixture, _ = load_fixture(DATASET)
        row = fixture["gate_nodes"][0]
        prompt = build_prompt(row)
        payload = json.loads(prompt[prompt.rfind("{") : prompt.rfind("}") + 1])
        self.assertEqual(set(payload), {"parent_event", "direct_child_events"})
        self.assertNotIn(row["gate_node_id"], prompt)
        self.assertNotIn(row["source_id"], prompt)
        self.assertNotIn(row["figure_id"], prompt)
        self.assertNotIn(row["label_evidence"]["quote"], prompt)

    def test_source_pdf_mapping_requires_exact_source_set(self) -> None:
        fixture, _ = load_fixture(DATASET)
        source_ids = [source["source_id"] for source in fixture["sources"]]
        mapped = source_pdf_map([f"{source_id}=example.pdf" for source_id in source_ids], fixture["sources"])
        self.assertEqual(set(mapped), set(source_ids))
        with self.assertRaises(ValueError):
            source_pdf_map([f"{source_ids[0]}=example.pdf"], fixture["sources"])

    def test_probe_aggregates_by_document_source_without_treating_source_as_prompt(self) -> None:
        fixture, _ = load_fixture(DATASET)
        labels = [row["expected_gate"] for row in fixture["gate_nodes"]]

        class LabelSequenceModel:
            def __init__(self) -> None:
                self.index = 0

            def complete(self, _prompt: str) -> str:
                label = labels[self.index]
                self.index += 1
                other = "OR" if label == "AND" else "AND"
                scores = {label: 0.8, other: 0.1, "unknown": 0.1}
                return json.dumps({"gate_probabilities": scores, "reason": "test double"})

        artifact = run_probe(fixture, LabelSequenceModel(), model_id="test-only", provider_host=None)
        self.assertEqual(artifact["status"], "completed")
        self.assertEqual(artifact["summary"]["sample_count"], 5)
        self.assertEqual(set(artifact["per_source_summary"]), {source["source_id"] for source in fixture["sources"]})
        self.assertTrue(all(artifact["summary"]["confusion_matrix_gold_rows_predicted_columns"][gate][gate] == count for gate, count in (("AND", 2), ("OR", 3))))
        self.assertFalse(artifact["formal_gold"])
        self.assertFalse(artifact["fta_ready"])


if __name__ == "__main__":
    unittest.main()
