import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert_siemens_s210_causal_relation_expert_review import build_gold  # noqa: E402
from validate_siemens_s210_causal_relation_gold import load, validate  # noqa: E402


class SiemensS210CausalRelationGoldTests(unittest.TestCase):
    def test_converted_pilot_gold_has_25_causal_relations_and_five_exclusions(self):
        gold = load(
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_causal_relation_gold_v1.json"
        )
        self.assertEqual([], validate(gold))
        self.assertEqual(25, len(gold["relations"]))
        self.assertEqual(5, len(gold["excluded_candidates"]))
        self.assertTrue(gold["dataset_info"]["summary_discrepancy"])

    def test_source_review_table_is_authoritative_for_counts(self):
        gold = load(
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_causal_relation_gold_v1.json"
        )
        summary = gold["dataset_info"]["summary_discrepancy"]
        self.assertEqual(26, summary["claimed_in_document"]["causal"])
        self.assertEqual(25, summary["reconciled_from_review_table"]["causal"])


if __name__ == "__main__":
    unittest.main()
