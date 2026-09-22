import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_siemens_s210_fault_relation_gold import compare_registry, load, validate  # noqa: E402


class SiemensS210FaultRelationGoldTests(unittest.TestCase):
    def test_expert_gold_is_valid_and_matches_runtime_registry(self):
        gold_path = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_fault_relation_gold_v1.json"
        registry_path = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_fault_relation_registry_v1.json"
        gold = load(gold_path)
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual([], validate(gold))
        self.assertEqual([], compare_registry(gold, registry))
        self.assertEqual(5, len(gold["relations"]))

    def test_causal_or_logic_claims_are_rejected_in_association_gold(self):
        gold = load(ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_fault_relation_gold_v1.json")
        gold["dataset_info"]["causal_relations_complete"] = True
        errors = validate(gold)
        self.assertTrue(any("causal_relations_complete" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
