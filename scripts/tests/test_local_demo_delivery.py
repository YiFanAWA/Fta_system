"""Closed file-set checks, not field/causal correctness or public licensing."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_demo_runtime import DemoError
import verify_local_demo_delivery as delivery


class DeliveryTests(unittest.TestCase):
    def fixture(self, root):
        (root / "data.txt").write_bytes(b"operator-owned-fixture")
        row = {"path": "data.txt", "role": "fixture", "size_bytes": 22,
               "sha256": sha256(b"operator-owned-fixture").hexdigest()}
        manifest = {"kind": "local_research_demo_delivery_v1", "public_distribution_authorized": False,
                    "files": [row], "file_count_excluding_manifest": 1, "total_bytes_excluding_manifest": 22}
        path = root / delivery.MANIFEST
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest, sha256(path.read_bytes()).hexdigest()

    def test_fresh_inventory_and_external_manifest_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, identity = self.fixture(root)
            self.assertEqual(manifest, delivery.verify(root, expected_manifest_sha=identity))
            with self.assertRaises(DemoError):
                delivery.verify(root, expected_manifest_sha="0" * 64)

    def test_extra_runtime_product_is_not_clean_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / "database.sqlite3").write_bytes(b"never-package")
            with self.assertRaisesRegex(DemoError, "delivery_unexpected_or_missing_files"):
                delivery.verify(root)

    def test_payload_change_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / "data.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(DemoError, "delivery_member_drift"):
                delivery.verify(root)

    def test_public_scope_not_inferred(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = self.fixture(root)
            manifest["public_distribution_authorized"] = True
            (root / delivery.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(DemoError, "delivery_scope_mismatch"):
                delivery.verify(root)

    def test_duplicate_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, _ = self.fixture(Path(directory))
            row = manifest["files"][0]
            for rows in ([row, row], [{**row, "path": "../data.txt"}], [{**row, "path": "a//data.txt"}],
                         [{**row, "path": "data.txt:stream"}]):
                with self.subTest(rows=rows), self.assertRaises(DemoError):
                    delivery.validate_rows(rows)


if __name__ == "__main__":
    unittest.main()
