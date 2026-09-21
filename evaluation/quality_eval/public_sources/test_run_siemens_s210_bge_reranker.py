import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from run_siemens_s210_bge_reranker import (  # noqa: E402
    _candidate_text,
    _guard_explicit_fault_codes,
    _rank_by_scores,
)


class BgeRerankerTests(unittest.TestCase):
    def test_rank_by_scores_is_descending_with_code_tie_break(self):
        self.assertEqual(
            ["F00002", "F00001", "F00003"],
            _rank_by_scores(["F00001", "F00002", "F00003"], [0.8, 0.9, 0.1]),
        )

    def test_explicit_fault_code_guard_pins_code(self):
        guarded, exact = _guard_explicit_fault_codes("请查询 F00001", ["F00002", "F00001", "F00003"])
        self.assertEqual(["F00001"], exact)
        self.assertEqual(["F00001", "F00002", "F00003"], guarded)

    def test_candidate_text_contains_structured_and_alarm_context(self):
        text = _candidate_text(
            {
                "fault_code": "F00001",
                "component": "CU",
                "related_components": [],
                "description": "Internal software error",
                "causes": ["An internal error occurred"],
                "parameters": ["r0949"],
            },
            "Fault value (r0949):\\nOnly for internal troubleshooting.",
        )
        self.assertIn("Fault code: F00001", text)
        self.assertIn("Causes: An internal error occurred", text)
        self.assertIn("Alarm value section:", text)


if __name__ == "__main__":
    unittest.main()
