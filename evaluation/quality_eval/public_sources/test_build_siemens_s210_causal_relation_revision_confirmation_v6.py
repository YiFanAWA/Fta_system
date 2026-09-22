import json
import unittest
from pathlib import Path

from build_siemens_s210_causal_relation_revision_confirmation_v6 import (
    build_confirmation,
    load_json,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets" / "siemens_s210_causal_relation_revision_v5.json"


class RevisionConfirmationV6Test(unittest.TestCase):
    def test_builds_two_pending_records_without_gold_approval(self) -> None:
        package = build_confirmation(load_json(SOURCE))
        self.assertEqual(package["dataset_info"]["status"], "pending_expert_revision")
        self.assertFalse(package["dataset_info"]["expert_validated"])
        self.assertEqual(
            [row["fault_code"] for row in package["revisions"]], ["A01691", "A01782"]
        )
        for row in package["revisions"]:
            self.assertEqual(row["expert_review"]["status"], "pending_expert_revision")
            self.assertEqual(row["expert_review"]["overall_decision"], "")
            self.assertFalse(row["expert_review"]["final_cause_text"])

    def test_a01782_suggested_evidence_is_not_current_evidence(self) -> None:
        package = build_confirmation(load_json(SOURCE))
        row = next(item for item in package["revisions"] if item["fault_code"] == "A01782")
        self.assertEqual(row["original_evidence"][0]["start"], 307)
        self.assertEqual(row["suggested_revision"]["suggested_evidence"]["start"], 461)
        self.assertNotEqual(
            row["original_evidence"][0]["quote"],
            row["suggested_revision"]["suggested_evidence"]["quote"],
        )


if __name__ == "__main__":
    unittest.main()
