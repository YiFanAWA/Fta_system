import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_causal_relation_review_bundle import build_bundle, _load  # noqa: E402
from validate_siemens_s210_causal_relation_candidates import validate  # noqa: E402


class SiemensS210CausalRelationCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _load(
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
        )

    def test_builder_creates_pending_evidence_backed_candidates(self):
        bundle = build_bundle(self.source, limit=3, reviewer="刘武")
        self.assertEqual([], validate(bundle))
        self.assertEqual(3, len(bundle["candidates"]))
        self.assertFalse(bundle["dataset_info"]["fta_ready"])
        self.assertTrue(all(c["expert_review"]["overall_decision"] == "pending" for c in bundle["candidates"]))

    def test_validator_rejects_promoting_pending_candidate(self):
        bundle = build_bundle(self.source, limit=1, reviewer="刘武")
        invalid = copy.deepcopy(bundle)
        invalid["candidates"][0]["expert_review"]["overall_decision"] = "approve"
        errors = validate(invalid)
        self.assertTrue(any("overall_decision" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
