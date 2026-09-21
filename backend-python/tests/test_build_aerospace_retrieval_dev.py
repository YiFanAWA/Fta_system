import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
PUBLIC_SOURCES = ROOT / "evaluation/quality_eval/public_sources"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_aerospace_retrieval_dev import build  # noqa: E402


SAMPLE = ROOT / "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"


class AerospaceRetrievalDevTests(unittest.TestCase):
    def test_dev_set_is_sealed_as_non_final_and_has_multiple_query_roles(self):
        payload = build(SAMPLE)
        self.assertGreaterEqual(payload["dataset_info"]["query_count"], 30)
        self.assertLessEqual(payload["dataset_info"]["query_count"], 50)
        self.assertFalse(payload["dataset_info"]["eligible_for_final_generalization_claim"])
        self.assertGreaterEqual(len(payload["dataset_info"]["query_types"]), 4)
        self.assertTrue(all(item["relevant_entity_ids"] for item in payload["queries"]))

    def test_dev_labels_point_to_source_entities(self):
        payload = build(SAMPLE)
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        known = {
            f"aerospace:faa-sdr:service-difficulty-report:{row['OperatorControlNumber'].upper()}"
            for row in (item["raw_record"] for item in sample["samples"])
        }
        self.assertTrue(
            all(
                entity_id in known
                for query in payload["queries"]
                for entity_id in query["relevant_entity_ids"]
            )
        )


if __name__ == "__main__":
    unittest.main()
