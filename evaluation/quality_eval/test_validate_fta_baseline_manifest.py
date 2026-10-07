from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.quality_eval.validate_fta_baseline_manifest import ManifestValidationError, validate_manifest


class TestFtaBaselineManifest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.artifact = self.root / "evidence.txt"
        self.artifact.write_text("fixed evidence\n", encoding="utf-8")
        digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.payload = {
            "manifest_schema": "fta_baseline_manifest_v1",
            "artifacts": [
                {"artifact_id": "evidence", "path": "evidence.txt", "sha256": digest}
            ],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_manifest_verifies_exact_file_hash(self) -> None:
        self.assertEqual(
            validate_manifest(self.payload, repo_root=self.root),
            {"artifact_count": 1, "verified_count": 1},
        )

    def test_changed_artifact_is_rejected(self) -> None:
        self.artifact.write_text("changed evidence\n", encoding="utf-8")
        with self.assertRaisesRegex(ManifestValidationError, "hash mismatch"):
            validate_manifest(self.payload, repo_root=self.root)

    def test_parent_path_is_rejected(self) -> None:
        self.payload["artifacts"][0]["path"] = "../outside.txt"
        with self.assertRaisesRegex(ManifestValidationError, "repo-relative"):
            validate_manifest(self.payload, repo_root=self.root)

    def test_duplicate_artifact_ids_are_rejected(self) -> None:
        self.payload["artifacts"].append(dict(self.payload["artifacts"][0]))
        with self.assertRaisesRegex(ManifestValidationError, "duplicate artifact_id"):
            validate_manifest(self.payload, repo_root=self.root)

    def test_missing_artifact_is_rejected(self) -> None:
        self.payload["artifacts"][0]["path"] = "missing.txt"
        with self.assertRaisesRegex(ManifestValidationError, "file is missing"):
            validate_manifest(self.payload, repo_root=self.root)

    def test_repository_active_baseline_manifest_v52_is_current(self) -> None:
        root = Path(__file__).resolve().parents[2]
        manifest_path = root / "evaluation" / "quality_eval" / "fta_baseline_manifest_v52.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("candidate_fta_research_baseline_v52", payload["manifest_id"])
        result = validate_manifest(payload, repo_root=root)
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
