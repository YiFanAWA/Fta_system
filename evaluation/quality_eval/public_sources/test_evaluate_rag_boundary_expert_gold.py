import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from evaluate_rag_boundary_expert_gold import main  # noqa: E402


class EvaluateBoundaryExpertGoldTests(unittest.TestCase):
    def test_module_imports(self) -> None:
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
