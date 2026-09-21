import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from s210_retrieval_adapter import (  # noqa: E402
    _d2_rank,
    _extract_fault_codes,
    _extract_parameters,
    _merge_candidate_pool,
    _rrf_rank,
)


class S210RetrievalAdapterTests(unittest.TestCase):
    def test_extracts_identifiers_without_matching_substrings(self):
        self.assertEqual({"F01600"}, _extract_fault_codes("查询 F01600"))
        self.assertEqual({"P9602", "R0949"}, _extract_parameters("p9602 与 r0949"))
        self.assertEqual(set(), _extract_fault_codes("AF01600"))

    def test_d2_pins_fault_code_and_boosts_parameter(self):
        base = _rrf_rank(
            ["F00001", "F00002", "F00003"],
            ["F00002", "F00001", "F00003"],
        )
        scores = {"F00001": 0.04, "F00002": 0.05, "F00003": 0.03}
        ranked, signals = _d2_rank(
            base,
            scores,
            "F00001 p7829",
            {"F00001": {"P7829"}, "F00002": set(), "F00003": set()},
        )
        self.assertEqual("F00001", ranked[0])
        self.assertEqual(["F00001"], signals["exact_fault_codes"])
        self.assertEqual(["P7829"], signals["parameter_matches_by_fault"]["F00001"])

    def test_candidate_pool_is_d2_then_alarm_and_deduplicated(self):
        self.assertEqual(
            ["F00001", "F00002", "F00003", "F00004"],
            _merge_candidate_pool(
                ["F00001", "F00002", "F00003"],
                ["F00002", "F00004"],
                d2_top_k=3,
                alarm_top_k=2,
            ),
        )


if __name__ == "__main__":
    unittest.main()
