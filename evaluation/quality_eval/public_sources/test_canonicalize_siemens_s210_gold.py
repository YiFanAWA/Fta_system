import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from canonicalize_siemens_s210_gold import canonicalize_dataset  # noqa: E402


class SiemensS210GoldCanonicalizationTests(unittest.TestCase):
    def test_canonicalizes_observed_values_and_preserves_audit_values(self):
        source = {
            "dataset_info": {"version": "v2"},
            "gold_status": {"f1_ready": False},
            "samples": [{"gold_records": [{
                "component": "功率单元（Power unit）",
                "related_components": ["Control Unit（控制单元）"],
            }]}],
        }
        result = canonicalize_dataset(source)
        record = result["samples"][0]["gold_records"][0]
        self.assertEqual("Power unit", record["component"])
        self.assertEqual("功率单元（Power unit）", record["component_original_v2"])
        self.assertEqual(["Control Unit"], record["related_components"])
        self.assertEqual(["Control Unit（控制单元）"], record["related_components_original_v2"])
        self.assertTrue(result["gold_status"]["f1_ready"])
        self.assertEqual("v3-official-f1", result["dataset_info"]["version"])

    def test_rejects_unmapped_component_instead_of_guessing(self):
        source = {
            "dataset_info": {},
            "gold_status": {},
            "samples": [{"gold_records": [{"component": "unreviewed component"}]}],
        }
        with self.assertRaises(ValueError):
            canonicalize_dataset(source)


if __name__ == "__main__":
    unittest.main()
