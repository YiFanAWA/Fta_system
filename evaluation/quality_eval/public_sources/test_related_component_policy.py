import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from project_related_component_policy import project  # noqa: E402


class RelatedComponentPolicyTests(unittest.TestCase):
    def test_keeps_only_explicit_relation_and_preserves_original_value(self):
        payload = {
            "dataset_info": {"version": "v1"},
            "samples": [
                {
                    "sample_id": "F01357",
                    "input_text": (
                        "Two Control Units are connected with one another through DRIVE-CLiQ."
                    ),
                    "gold_records": [
                        {
                            "fault_code": "F01357",
                            "related_components": ["Control Unit"],
                        }
                    ],
                },
                {
                    "sample_id": "F30075",
                    "input_text": (
                        "A communication error occurred while configuring the power unit "
                        "using the Control Unit."
                    ),
                    "gold_records": [
                        {
                            "fault_code": "F30075",
                            "related_components": ["Control Unit"],
                        }
                    ],
                },
                {
                    "sample_id": "F30027",
                    "input_text": (
                        "There is no line supply voltage connected. "
                        "The power unit DC link was not precharged."
                    ),
                    "gold_records": [
                        {
                            "fault_code": "F30027",
                            "related_components": ["DC link"],
                        }
                    ],
                },
            ],
        }

        result = project(payload)

        self.assertEqual(
            ["Control Unit"],
            result["samples"][0]["gold_records"][0]["related_components"],
        )
        self.assertEqual(
            [],
            result["samples"][1]["gold_records"][0]["related_components"],
        )
        self.assertEqual(
            ["Control Unit"],
            result["samples"][1]["gold_records"][0]["related_components_original_v1"],
        )
        self.assertEqual(
            [],
            result["samples"][2]["gold_records"][0]["related_components"],
        )


if __name__ == "__main__":
    unittest.main()
