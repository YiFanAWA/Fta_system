import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_siemens_s210_fta_preview import build_preview  # noqa: E402
from validate_siemens_s210_fta_preview import load, validate  # noqa: E402


class SiemensS210FtaPreviewTests(unittest.TestCase):
    def test_preview_contains_only_five_approved_or_events(self):
        path = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_and_or_logic_gold_v1.json"
        preview = build_preview(load(path))
        self.assertEqual([], validate(preview))
        self.assertEqual(5, len(preview["trees"]))
        self.assertEqual(1, len(preview["excluded_events"]))
        self.assertFalse(preview["dataset_info"]["production_ready"])
        self.assertFalse(preview["dataset_info"]["fta_ready"])
        self.assertEqual("F01611", preview["excluded_events"][0]["fault_code"])


if __name__ == "__main__":
    unittest.main()
