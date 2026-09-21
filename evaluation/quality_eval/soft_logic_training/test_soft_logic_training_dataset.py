import json
import tempfile
import unittest
from pathlib import Path

from build_soft_logic_training_dataset import _gate_candidate, _make_sample
from convert_soft_logic_training import _record_sample, convert


class SoftLogicTrainingDatasetTests(unittest.TestCase):
    def test_causal_relation_does_not_become_or(self):
        candidate = _gate_candidate("A caused B.", ["A"])
        self.assertIsNone(candidate["gate_candidate"])
        self.assertEqual(candidate["status"], "source_relation_only")

    def test_explicit_or_is_only_a_weak_candidate(self):
        candidate = _gate_candidate("B may be caused by A or C.", ["A", "C"])
        self.assertEqual(candidate["gate_candidate"], "OR")
        self.assertEqual(candidate["status"], "explicit_source_candidate")
        self.assertEqual(candidate["confidence"], 0.55)

    def test_project_handbook_samples_are_forced_to_test(self):
        sample = _make_sample(
            {
                "sample_id": "PH-1",
                "input_text": "故障可能由 A 或 B 引起",
                "gold_top_event": "系统故障",
                "gold_records": [{"description": "系统故障", "causes": ["A", "B"]}],
                "gold_relations": [],
                "evidence_spans": [],
                "source": {"dataset": "Project Handbook"},
                "annotation": {"label_status": "source_annotated_provisional"},
            },
            force_test=True,
        )
        self.assertEqual(sample["split"], "test")
        self.assertEqual(sample["target"]["logic_candidates"][0]["gate_candidate"], "OR")
        self.assertEqual(sample["hard_constraints"]["unknown_gate_policy"], "keep_unknown")

    def test_output_is_jsonl_and_has_required_contract_fields(self):
        root = Path(__file__).resolve().parents[3]
        output = root / "evaluation" / "quality_eval" / "datasets" / "fta_soft_logic_training.jsonl"
        if not output.exists():
            self.skipTest("generated dataset has not been built yet")
        lines = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(lines)
        for sample in lines:
            self.assertEqual(sample["schema_version"], "soft_logic_training.v1")
            self.assertIn(sample["split"], {"train", "dev", "test"})
            self.assertIn("evidence_spans", sample)
            self.assertIn("logic_candidates", sample["target"])
            self.assertEqual(sample["hard_constraints"]["unknown_gate_policy"], "keep_unknown")

    def test_generated_evidence_offsets_match_canonical_text(self):
        root = Path(__file__).resolve().parents[3]
        output = root / "evaluation" / "quality_eval" / "datasets" / "fta_soft_logic_training.jsonl"
        if not output.exists():
            self.skipTest("generated dataset has not been built yet")
        rows = [
            json.loads(line)
            for line in output.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        mismatches = []
        for sample in rows:
            text = sample["input_text"]
            for span in sample["evidence_spans"]:
                start = span["start_char"]
                end = span["end_char"]
                if text[start:end] != span["evidence_text"]:
                    mismatches.append((sample["sample_id"], span["target_path"]))
        self.assertEqual(mismatches, [])

    def test_canonical_input_text_is_preserved_for_offsets(self):
        sample = _make_sample(
            {
                "sample_id": "OFFSET-1",
                "input_text": "A\n故障 B",
                "gold_top_event": "故障 B",
                "gold_records": [{"description": "故障 B", "causes": []}],
                "gold_relations": [],
                "evidence_spans": [
                    {
                        "target_path": "gold_records[0].description",
                        "evidence_text": "故障 B",
                        "start_char": 2,
                        "end_char": 6,
                    }
                ],
                "source": {"dataset": "test"},
                "annotation": {"label_status": "source_annotated_provisional"},
            }
        )
        self.assertEqual(sample["input_text"], "A\n故障 B")
        span = sample["evidence_spans"][0]
        self.assertEqual(sample["input_text"][span["start_char"] : span["end_char"]], span["evidence_text"])

    def test_sft_converter_keeps_partial_labels_explicit(self):
        converted = _record_sample(
            {
                "sample_id": "CONVERT-1",
                "split": "train",
                "input_text": "Problem: pump failed",
                "target": {
                    "top_event": "pump failed",
                    "records": [{"description": "pump failed", "fault_code": None}],
                    "relations": [],
                },
                "evidence_spans": [
                    {"target_path": "gold_records[0].description", "evidence_text": "pump failed"}
                ],
                "provenance": {
                    "dataset": "test",
                    "label_status": "source_annotated_provisional",
                    "human_expert_reviewed": False,
                },
            }
        )
        self.assertIsNotNone(converted)
        assistant = json.loads(converted["messages"][2]["content"])
        self.assertEqual(assistant["records"], [{"description": "pump failed"}])
        self.assertEqual(converted["metadata"]["label_scope"], ["description"])

    def test_conversion_writes_task_specific_files(self):
        root = Path(__file__).resolve().parents[3]
        input_path = root / "evaluation" / "quality_eval" / "datasets" / "fta_soft_logic_training.jsonl"
        if not input_path.exists():
            self.skipTest("generated dataset has not been built yet")
        with tempfile.TemporaryDirectory() as directory:
            manifest = convert(input_path, Path(directory))
            self.assertEqual(manifest["sample_count"], 203)
            self.assertTrue((Path(directory) / "fault_record_evidence_sft_train.jsonl").exists())
            self.assertTrue((Path(directory) / "causal_relation_sft_train.jsonl").exists())
            self.assertTrue((Path(directory) / "gate_candidate_review.jsonl").exists())
            self.assertTrue(manifest["policy"]["gate_candidates_are_not_sft_targets"])


if __name__ == "__main__":
    unittest.main()
