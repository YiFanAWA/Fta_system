import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT_GOLD = ROOT / "evaluation" / "quality_eval" / "project_gold"
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(PROJECT_GOLD))
sys.path.insert(0, str(BACKEND))

from import_reviewed_dataset_to_sqlite import import_dataset  # noqa: E402
from extraction.sqlite_extraction_repository import SQLiteExtractionWorkflowRepository  # noqa: E402


class ReviewedDatasetImportTests(unittest.TestCase):
    def _dataset(self):
        source = "F00001 Drive: pump stopped. Cause: motor overheated. Parameter p0001."
        return {
            "dataset_info": {
                "name": "test_reviewed_dataset",
                "version": "v1",
                "source": "test-source",
                "eligible_for_training": False,
            },
            "samples": [
                {
                    "sample_id": "S1",
                    "input_text": source,
                    "gold_records": [
                        {
                            "fault_code": "F00001",
                            "component": "Drive",
                            "related_components": [],
                            "description": "pump stopped",
                            "causes": ["motor overheated"],
                            "parameters": ["p0001"],
                        }
                    ],
                    "evidence_spans": [
                        {"field": "fault_code", "quote": "F00001", "start": 0, "end": 6},
                        {"field": "primary_component", "quote": "Drive", "start": 7, "end": 12},
                        {"field": "description", "quote": "pump stopped", "start": 14, "end": 26},
                        {"field": "cause", "quote": "motor overheated", "start": 35, "end": 51, "value_index": 0},
                        {"field": "parameter", "quote": "p0001", "start": 63, "end": 68, "value_index": 0},
                    ],
                    "expert_review": {
                        "decision": "审核通过",
                        "reviewer_name": "reviewer-1",
                        "review_date": "2026-09-20",
                    },
                    "provenance": {"source_file": "test.txt", "source_sha256": "hash"},
                }
            ],
        }

    def test_import_is_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "reviewed.sqlite3"
            first = import_dataset(self._dataset(), database, expected_records=1)
            second = import_dataset(self._dataset(), database, expected_records=1)

            self.assertEqual("imported", first["status"])
            self.assertEqual("already_imported", second["status"])
            repository = SQLiteExtractionWorkflowRepository(database)
            self.assertEqual(4, repository.schema_version)
            self.assertEqual((), repository.list_pending())
            connection = sqlite3.connect(database)
            try:
                self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM dataset_imports").fetchone()[0])
                self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM dataset_import_records").fetchone()[0])
                self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM fault_records").fetchone()[0])
            finally:
                connection.close()

    def test_invalid_evidence_does_not_create_import_rows(self):
        dataset = self._dataset()
        dataset["samples"][0]["evidence_spans"][2]["quote"] = "not in source"
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "reviewed.sqlite3"
            with self.assertRaises(ValueError):
                import_dataset(dataset, database, expected_records=1)
            self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
