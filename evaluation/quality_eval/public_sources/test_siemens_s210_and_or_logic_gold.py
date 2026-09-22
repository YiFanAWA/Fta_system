import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_siemens_s210_and_or_logic_gold import load, validate  # noqa: E402


class SiemensS210AndOrLogicGoldTests(unittest.TestCase):
    def test_imported_logic_gold_is_valid_and_not_fta_ready(self):
        path = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_and_or_logic_gold_v1.json"
        payload = load(path)
        self.assertEqual([], validate(payload))
        self.assertEqual(6, len(payload["events"]))
        self.assertEqual(5, payload["dataset_info"]["approved_event_count"])
        self.assertEqual(1, payload["dataset_info"]["unknown_gate_count"])
        self.assertFalse(payload["dataset_info"]["logic_gates_complete"])
        self.assertFalse(payload["dataset_info"]["fta_ready"])


if __name__ == "__main__":
    unittest.main()
