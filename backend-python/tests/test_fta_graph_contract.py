import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.fta_graph_contract import validate_fta_preview  # noqa: E402


class FtaGraphContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_fta_preview_v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_expert_bound_preview_is_valid(self):
        self.assertEqual([], validate_fta_preview(self.preview))

    def test_preview_cannot_be_marked_production_ready(self):
        payload = json.loads(json.dumps(self.preview))
        payload["dataset_info"]["production_ready"] = True
        errors = validate_fta_preview(payload)
        self.assertIn("dataset_info.production_ready must be false", errors)

    def test_preview_requires_evidence_for_each_child(self):
        payload = json.loads(json.dumps(self.preview))
        payload["trees"][0]["children"][0]["evidence"] = []
        errors = validate_fta_preview(payload)
        self.assertTrue(any("evidence must be non-empty" in error for error in errors))

    def test_unknown_event_is_not_in_preview(self):
        faults = {
            tree["top_event"]["fault_code"] for tree in self.preview["trees"]
        }
        self.assertNotIn("F01611", faults)
        self.assertEqual(1, len(self.preview["excluded_events"]))


if __name__ == "__main__":
    unittest.main()
