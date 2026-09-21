import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from domains.dataset_registry import (
    assert_valid_registry,
    count_population,
    verify_database_import,
)


class DatasetRegistryTests(unittest.TestCase):
    def test_validates_unique_entries_and_population(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "dataset.json"
            artifact.write_text(json.dumps({"samples": [{"sample_id": "S1"}]}), encoding="utf-8")
            registry = {
                "registry_schema_version": 1,
                "datasets": [
                    {
                        "dataset_id": "sample",
                        "artifact_path": "dataset.json",
                        "role": "test",
                        "split": "test",
                        "population": {"kind": "samples", "count": 1},
                        "label_status": "test",
                        "expert_status": {},
                        "training_eligible": False,
                        "lifecycle_status": "sealed",
                        "database_import": {"status": "not_applicable"},
                    }
                ],
            }
            assert_valid_registry(registry, repo_root=root)
            self.assertEqual(1, count_population(json.loads(artifact.read_text()), "samples"))

    def test_database_import_verification_is_read_only_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "registry.sqlite3"
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE dataset_imports (import_id TEXT, dataset_name TEXT, "
                "dataset_version TEXT, record_count INTEGER, status TEXT)"
            )
            connection.execute(
                "INSERT INTO dataset_imports VALUES (?, ?, ?, ?, ?)",
                ("import-1", "dataset", "v1", 2, "completed"),
            )
            connection.commit()
            connection.close()

            state = verify_database_import(
                database,
                dataset_name="dataset",
                dataset_version="v1",
                expected_count=2,
            )
            self.assertEqual("completed", state["status"])
            self.assertEqual("import-1", state["import_id"])

            connection = sqlite3.connect(database)
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM dataset_imports").fetchone()[0])
            connection.close()

    def test_missing_database_is_not_reported_as_completed(self):
        state = verify_database_import(
            Path("missing.sqlite3"),
            dataset_name="dataset",
            dataset_version="v1",
            expected_count=1,
        )
        self.assertEqual("not_verified", state["status"])
        self.assertEqual("database_file_missing", state["reason"])


if __name__ == "__main__":
    unittest.main()
