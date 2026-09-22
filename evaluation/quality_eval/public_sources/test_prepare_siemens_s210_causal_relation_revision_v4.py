import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_siemens_s210_causal_relation_revision_v4 import (  # noqa: E402
    build_checklist,
    build_revision_package,
)


class CausalRelationRevisionV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = (
            ROOT
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json"
        )
        cls.bundle = json.loads(path.read_text(encoding="utf-8"))

    def test_revision_package_keeps_candidate_pending(self):
        package = build_revision_package(self.bundle, "CR-CAND-V4-029", "刘武")
        revision = package["revisions"][0]
        candidate = revision["original_candidate"]

        self.assertEqual(package["dataset_info"]["status"], "pending_expert_revision")
        self.assertFalse(package["dataset_info"]["expert_validated"])
        self.assertEqual(candidate["source_node"]["text"], "requested, invalid reference block")
        self.assertEqual(
            package["revision_request"]["suggested_normalized_cause"],
            "PROFIsafe transferred reference block is negative",
        )
        self.assertTrue(revision["evidence_check"]["source_text_contains_original_quote"])
        self.assertEqual(revision["expert_review"]["overall_decision"], "pending")

    def test_checklist_contains_source_and_gate(self):
        package = build_revision_package(self.bundle, "CR-CAND-V4-029", "刘武")
        checklist = build_checklist(package)
        self.assertIn("A01730", checklist)
        self.assertIn("PROFIsafe transferred reference block is negative", checklist)
        self.assertIn("不得将该候选写入正式因果 Gold", checklist)


if __name__ == "__main__":
    unittest.main()
