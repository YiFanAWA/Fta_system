import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle import _load  # noqa: E402
from build_siemens_s210_causal_relation_review_bundle_v2 import build_remaining_bundle  # noqa: E402
from validate_siemens_s210_causal_relation_candidates import validate  # noqa: E402


class SiemensS210CausalRelationReviewBundleV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _load(
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
        )
        cls.gold = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_causal_relation_gold_v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_remaining_batch_is_pending_and_has_66_candidates(self):
        bundle = build_remaining_bundle(self.source, self.gold, "刘武")
        self.assertEqual(66, len(bundle["candidates"]))
        self.assertEqual([], validate(bundle))
        self.assertFalse(bundle["dataset_info"]["logic_gates_complete"])
        self.assertEqual(66, bundle["dataset_info"]["candidate_count"])


if __name__ == "__main__":
    unittest.main()
