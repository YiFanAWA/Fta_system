"""Wheel-cache verification, not an installer or a model-quality score."""
from hashlib import sha224, sha256
from pathlib import Path
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collect_local_demo_wheels as wheels
from local_demo_runtime import DemoError


class WheelCacheTests(unittest.TestCase):
    def row(self):
        return {"filename": "example-1.0-py3-none-any.whl", "packagetype": "bdist_wheel", "yanked": False,
                "url": "https://files.pythonhosted.org/packages/example-1.0-py3-none-any.whl",
                "size": 3, "digests": {"sha256": sha256(b"abc").hexdigest()}}

    def body(self, root, row):
        key = sha224(row["url"].encode()).hexdigest()
        path = root / Path(*key[:5]) / (key + ".body")
        path.parent.mkdir(parents=True)
        path.write_bytes(b"abc")
        return path

    def test_compatible_wheel_not_sdist_or_yanked(self):
        row = self.row()
        self.assertEqual(row, wheels.select_wheel([{**row, "packagetype": "sdist"}, {**row, "yanked": True}, row]))
        with self.assertRaisesRegex(DemoError, "compatible_pinned_wheel_missing"):
            wheels.select_wheel([{**row, "yanked": True}])

    def test_exact_cached_body_passes_official_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root, row = Path(directory), self.row()
            path = self.body(root, row)
            self.assertEqual(b"abc", wheels.verified_cached_body(row, root))
            self.assertEqual(b"abc", path.read_bytes())

    def test_missing_or_wrong_body_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root, row = Path(directory), self.row()
            self.assertIsNone(wheels.verified_cached_body(row, root))
            self.body(root, row).write_bytes(b"bad")
            self.assertIsNone(wheels.verified_cached_body(row, root))

    def test_unapproved_host_size_or_identity_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            for change in ({"url": "https://other.example/a.whl"}, {"url": "http://files.pythonhosted.org/a.whl"},
                           {"size": wheels.MAX_WHEEL + 1}, {"digests": {"sha256": "invalid"}}):
                with self.subTest(change=change), self.assertRaises(DemoError):
                    wheels.verified_cached_body({**self.row(), **change}, Path(directory))

    def test_hardlinked_cache_body_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root, row = Path(directory), self.row()
            path = self.body(root, row)
            os.link(path, root / "link")
            with self.assertRaisesRegex(DemoError, "regular_single_link_file_required"):
                wheels.verified_cached_body(row, root)


if __name__ == "__main__":
    unittest.main()
