import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from evaluate_siemens_s210_gold import evaluate  # noqa: E402


class SiemensS210GoldEvaluationTests(unittest.TestCase):
    def test_scores_saved_prediction_fields_without_treating_empty_gold_as_fn(self):
        gold = {
            "samples": [
                {
                    "sample_id": "S1",
                    "gold_records": [
                        {
                            "fault_code": "F01000",
                            "description": "Motor stopped",
                            "component": None,
                            "related_components": [],
                            "causes": ["Overcurrent"],
                            "parameters": ["r0949"],
                        }
                    ],
                }
            ]
        }
        report = evaluate(
            gold,
            {
                "S1": {
                    "records": [
                        {
                            "fault_code": "F01000",
                            "description": "Motor stopped",
                            "component": None,
                            "related_components": [],
                            "causes": ["Overcurrent"],
                            "parameters": ["r0949"],
                        }
                    ]
                }
            },
        )
        self.assertEqual(1.0, report["field_metrics"]["fault_code"]["metrics"]["f1"])
        self.assertEqual("unknown_gold_excluded", report["field_metrics"]["component"]["counts"]["status"] if "status" in report["field_metrics"]["component"]["counts"] else "unknown_gold_excluded")
        self.assertEqual(1.0, report["field_metrics"]["causes"]["metrics"]["f1"])

    def test_reads_api_response_with_nested_extracted_faults(self):
        gold = {
            "gold_status": {"f1_ready": False},
            "samples": [
                {
                    "sample_id": "S1",
                    "gold_records": [{"fault_code": "A01006", "description": "Firmware update"}],
                }
            ],
        }
        report = evaluate(
            gold,
            {
                "S1": {
                    "success": True,
                    "extracted_faults": {
                        "records": [{"fault_code": "A01006", "description": "Firmware update"}]
                    },
                }
            },
        )
        self.assertEqual("diagnostic_completed", report["status"])
        self.assertEqual("diagnostic_only", report["evaluation_scope"])
        self.assertEqual(1.0, report["field_metrics"]["fault_code"]["metrics"]["f1"])

    def test_normalized_metrics_match_bilingual_components_and_split_causes(self):
        gold = {
            "gold_status": {"f1_ready": False},
            "samples": [
                {
                    "sample_id": "S1",
                    "gold_records": [
                        {
                            "component": "功率单元（Power unit）",
                            "causes": ["Possible causes: line supply failure; line phase interrupted (p0210 = 1)"],
                        }
                    ],
                }
            ],
        }
        report = evaluate(
            gold,
            {
                "S1": {
                    "records": [
                        {
                            "component": "Power unit",
                            "causes": ["line supply failure", "line phase interrupted"],
                        }
                    ]
                }
            },
        )
        self.assertEqual(0.0, report["field_metrics"]["component"]["metrics"]["f1"])
        self.assertEqual(1.0, report["normalized_field_metrics"]["component"]["metrics"]["f1"])
        self.assertEqual(1.0, report["normalized_field_metrics"]["causes"]["metrics"]["f1"])

    def test_normalized_causes_ignore_parameter_parentheses_and_split_sentences(self):
        gold = {
            "gold_status": {"f1_ready": False},
            "samples": [
                {
                    "sample_id": "S1",
                    "gold_records": [
                        {
                            "causes": [
                                "SAM (p9506 = 0): speed exceeded the tolerance."
                                " SBR (p9506 = 2): speed exceeded the tolerance."
                            ]
                        }
                    ],
                }
            ],
        }
        report = evaluate(
            gold,
            {
                "S1": {
                    "records": [
                        {
                            "causes": [
                                "SAM: speed exceeded the tolerance.",
                                "SBR: speed exceeded the tolerance.",
                            ]
                        }
                    ]
                }
            },
        )
        self.assertEqual(1.0, report["normalized_field_metrics"]["causes"]["metrics"]["f1"])

    def test_official_policy_scores_description_synonym_and_split_causes(self):
        gold = {
            "gold_status": {"f1_ready": True},
            "samples": [
                {
                    "sample_id": "S1",
                    "gold_records": [
                        {
                            "fault_code": "F01000",
                            "component": "Motor",
                            "description": "Motor overheating",
                            "causes": [
                                "Possible causes: The motor is overheating (p1083[0] = 1); encoder failure"
                            ],
                            "related_components": [],
                            "parameters": [],
                        }
                    ],
                }
            ],
        }
        report = evaluate(
            gold,
            {
                "S1": {
                    "records": [
                        {
                            "fault_code": "F01000",
                            "component": "Motor",
                            "description": "Motor temperature too high",
                            "causes": ["motor overheat", "encoder fail"],
                            "related_components": [],
                            "parameters": [],
                        }
                    ]
                }
            },
        )
        self.assertEqual("official", report["evaluation_scope"])
        self.assertEqual(1.0, report["official_field_metrics"]["description"]["metrics"]["f1"])
        self.assertEqual(1.0, report["official_field_metrics"]["causes"]["metrics"]["f1"])


if __name__ == "__main__":
    unittest.main()
