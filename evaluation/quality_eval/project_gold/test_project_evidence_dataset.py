import json
import re
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from build_project_evidence_dataset import build_dataset  # noqa: E402


class ProjectEvidenceDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_path = ROOT / "backend-python" / "examples" / "manual_handbook_sample.txt"
        cls.payload = build_dataset(cls.input_path)

    def test_expected_first_batch_and_provenance(self):
        samples = self.payload["samples"]
        self.assertEqual(27, len(samples))
        self.assertEqual({"test"}, {sample["split"] for sample in samples})
        for sample in samples:
            source = sample["source"]
            self.assertEqual(64, len(source["source_sha256"]))
            self.assertFalse(sample["annotation"]["human_expert_reviewed"])
            self.assertEqual("unknown", sample["annotation"]["causal_logic_status"])

    def test_every_evidence_span_matches_input(self):
        for sample in self.payload["samples"]:
            input_text = sample["input_text"]
            record = sample["gold_records"][0]
            for span in sample["evidence_spans"]:
                actual = input_text[span["start_char"] : span["end_char"]]
                self.assertEqual(span["evidence_text"], actual, sample["sample_id"])
                normalized = re.sub(r"\s+", "", actual)
                path = span["target_path"]
                if path.endswith("fault_code"):
                    expected = record["fault_code"]
                elif path.endswith("description"):
                    expected = record["description"]
                elif path.endswith("component"):
                    expected = record["component"]
                elif ".parameters[" in path:
                    index = int(path.rsplit("[", 1)[1].split("]", 1)[0])
                    expected = record["parameters"][index]
                elif ".causes[" in path:
                    index = int(path.rsplit("[", 1)[1].split("]", 1)[0])
                    expected = record["causes"][index]
                else:
                    self.fail(f"unexpected evidence target: {path}")
                self.assertEqual(expected, normalized if span["evidence_status"].endswith("whitespace") else actual)

    def test_unknown_component_is_not_promoted(self):
        f01630 = next(sample for sample in self.payload["samples"] if sample["sample_id"] == "PH-F01630")
        record = f01630["gold_records"][0]
        self.assertIsNone(record["component"])
        self.assertFalse(any(span["target_path"].endswith("component") for span in f01630["evidence_spans"]))
        self.assertEqual("unknown", f01630["annotation"]["causal_logic_status"])

    def test_fault_block_does_not_include_following_section(self):
        a01032 = next(sample for sample in self.payload["samples"] if sample["sample_id"] == "PH-A01032")
        f01651 = next(sample for sample in self.payload["samples"] if sample["sample_id"] == "PH-F01651")
        self.assertNotIn("2.2 功率单元及电机模块", a01032["input_text"])
        self.assertNotIn("故障代码F01034", f01651["input_text"])
        self.assertEqual(["r2124", "p0977"], a01032["gold_records"][0]["parameters"])

    def test_component_label_can_cross_a_source_line_break(self):
        for sample_id in ("PH-A01032", "PH-F01009"):
            sample = next(item for item in self.payload["samples"] if item["sample_id"] == sample_id)
            self.assertIsNotNone(sample["gold_records"][0]["component"])


if __name__ == "__main__":
    unittest.main()
