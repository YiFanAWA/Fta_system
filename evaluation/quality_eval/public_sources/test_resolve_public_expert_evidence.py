import sys
import unittest


ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from resolve_public_expert_evidence import _find_span  # noqa: E402


class PublicExpertEvidenceResolutionTests(unittest.TestCase):
    def test_find_span_accepts_manual_line_wraps(self):
        text = "Cause: first line\nsecond line."
        span = _find_span(text, "first line second line.")
        self.assertEqual("first line\nsecond line.", span["quote"])
        self.assertEqual(7, span["start"])
        self.assertEqual(len(text), span["end"])


if __name__ == "__main__":
    unittest.main()
