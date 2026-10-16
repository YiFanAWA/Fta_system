"""Packaging boundaries, not model quality or clean-machine acceptance."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_local_demo_package as package
from local_demo_runtime import DemoError


class PackageTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "source"
        source.mkdir()
        (source / "file.txt").write_bytes(b"frozen-public-fixture-not-a-secret")
        row = package.describe(source, "file.txt", "fixture")
        return source, (row,)

    def test_real_inventory_has_only_named_frozen_files(self):
        rows = package.source_inventory()
        self.assertEqual(146, len(rows))
        self.assertEqual(101, sum(row["role"] == "backend_source" for row in rows))
        self.assertEqual(33, sum(row["role"] == "frontend_build" for row in rows))
        self.assertEqual(3, sum(row["role"] == "frozen_input" for row in rows))
        self.assertFalse(any(".venv/" in row["path"] or ".env" in row["path"] for row in rows))

    def test_copy_manifest_and_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, rows = self.fixture(base)
            destination = base / "candidate"
            manifest = package.materialize(source, destination, rows)
            self.assertFalse(manifest["m4_complete"])
            self.assertFalse(manifest["public_distribution_authorized"])
            self.assertFalse(manifest["provider_enabled"])
            self.assertEqual(manifest, package.verify(destination, rows))
            self.assertEqual((source / "file.txt").read_bytes(), (destination / "file.txt").read_bytes())

    def test_existing_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            destination = root / "candidate"
            destination.mkdir()
            with self.assertRaisesRegex(DemoError, "package_destination_exists"):
                package.materialize(source, destination, rows)
            self.assertEqual([], list(destination.iterdir()))

    def test_source_drift_leaves_no_ready_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            (source / "file.txt").write_bytes(b"changed")
            destination = root / "candidate"
            with self.assertRaisesRegex(DemoError, "package_source_drift"):
                package.materialize(source, destination, rows)
            self.assertFalse((destination / package.MANIFEST).exists())

    def test_changed_member_and_extra_file_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            destination = root / "candidate"
            package.materialize(source, destination, rows)
            extra = destination / "injected.py"
            extra.write_bytes(b"not-allowed")
            with self.assertRaisesRegex(DemoError, "package_unexpected_member"):
                package.verify(destination, rows)
            extra.unlink()
            (destination / "file.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(DemoError, "package_member_drift"):
                package.verify(destination, rows)

    def test_manifest_cannot_grant_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            destination = root / "candidate"
            package.materialize(source, destination, rows)
            path = destination / package.MANIFEST
            data = json.loads(path.read_text(encoding="utf-8"))
            data["m4_complete"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(DemoError, "package_manifest_drift"):
                package.verify(destination, rows)

    def test_duplicate_case_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            for repeated in (rows + rows, rows + ({**rows[0], "path": "FILE.TXT"},)):
                with self.assertRaisesRegex(DemoError, "package_duplicate_path"):
                    package.materialize(source, root / "candidate", repeated)
            self.assertFalse((root / "candidate").exists())

    def test_relative_path_escape_rejected(self):
        for name in ("../outside", "/absolute", "C:/path", "a\\b", "a//b", "a/./b", "CON", "a."):
            with self.subTest(name=name), self.assertRaises(DemoError):
                package.relative_name(name)

    def test_hardlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            os.link(source / "file.txt", root / "link")
            with self.assertRaisesRegex(DemoError, "regular_single_link_file_required"):
                package.materialize(source, root / "candidate", rows)

    def test_hardlinked_candidate_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            destination = root / "candidate"
            package.materialize(source, destination, rows)
            os.link(destination / "file.txt", root / "link")
            with self.assertRaisesRegex(DemoError, "regular_single_link_file_required"):
                package.verify(destination, rows)

    def test_frozen_sha_is_not_replaced_by_fresh_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            (source / "file.txt").write_bytes(b"new-but-unapproved")
            with self.assertRaisesRegex(DemoError, "package_frozen_member_drift"):
                package.describe(source, "file.txt", "fixture", expected=rows[0]["sha256"])

    def test_missing_manifest_and_source_are_not_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            destination = root / "candidate"
            package.materialize(source, destination, rows)
            (destination / package.MANIFEST).unlink()
            with self.assertRaisesRegex(DemoError, "package_unexpected_member"):
                package.verify(destination, rows)
            self.assertFalse((destination / package.MANIFEST).exists())

    def test_inside_source_destination_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            for target in (source, source / "child", source.parent, Path(source.anchor)):
                with self.subTest(target=target), self.assertRaises(DemoError):
                    package.materialize(source, target, rows)

    def test_budget_does_not_accept_forged_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rows = self.fixture(root)
            bad = ({**rows[0], "size_bytes": package.MAX_TOTAL + 1},)
            with self.assertRaisesRegex(DemoError, "package_size_limit"):
                package.materialize(source, root / "candidate", bad)
            self.assertFalse((root / "candidate").exists())


if __name__ == "__main__":
    unittest.main()
