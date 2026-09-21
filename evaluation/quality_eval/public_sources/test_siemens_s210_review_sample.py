import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_siemens_s210_review_sample import build_review_dataset  # noqa: E402


class SiemensS210ReviewSampleTests(unittest.TestCase):
    def test_sample_has_deterministic_message_type_quotas(self):
        jsonl = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl"
        records = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        dataset = build_review_dataset(records)
        samples = dataset["samples"]
        self.assertEqual(30, len(samples))
        self.assertEqual({"F": 20, "A": 8, "N": 2}, dataset["dataset_info"]["selection"]["quotas"])
        counts = {}
        for sample in samples:
            kind = sample["weak_record"]["fault_code"][0]
            counts[kind] = counts.get(kind, 0) + 1
            self.assertFalse(sample["annotation"]["human_expert_reviewed"])
            self.assertIsNone(sample["annotation"]["decision"])
        self.assertEqual({"F": 20, "A": 8, "N": 2}, counts)

    def test_next_batch_excludes_previous_sample_ids(self):
        jsonl = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl"
        records = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        first = build_review_dataset(records)
        excluded = {sample["sample_id"] for sample in first["samples"]}
        second = build_review_dataset(records, excluded_ids=excluded, batch_name="v2")
        first_ids = excluded
        second_ids = {sample["sample_id"] for sample in second["samples"]}
        self.assertEqual(30, len(second_ids))
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertEqual("v2", second["dataset_info"]["version"])
        self.assertEqual(30, second["dataset_info"]["selection"]["excluded_count"])

    def test_custom_batch_quotas_are_preserved(self):
        jsonl = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl"
        records = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        dataset = build_review_dataset(records, quotas={"F": 1, "A": 2, "N": 0}, batch_name="tail")
        self.assertEqual(3, len(dataset["samples"]))
        self.assertEqual({"F": 1, "A": 2, "N": 0}, dataset["dataset_info"]["selection"]["quotas"])


if __name__ == "__main__":
    unittest.main()
