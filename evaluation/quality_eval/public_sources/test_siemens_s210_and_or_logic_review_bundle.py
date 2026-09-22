import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_and_or_logic_review_bundle import build, load  # noqa: E402


class SiemensS210AndOrLogicReviewBundleTests(unittest.TestCase):
    def test_six_multi_cause_events_are_ready_for_expert_gate_review(self):
        gold = load(
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_causal_relation_gold_v2.json"
        )
        bundle = build(gold, "刘武")
        self.assertEqual(6, len(bundle["events"]))
        self.assertTrue(all(event["expert_review"]["logic_gate"] == "pending" for event in bundle["events"]))


if __name__ == "__main__":
    unittest.main()
