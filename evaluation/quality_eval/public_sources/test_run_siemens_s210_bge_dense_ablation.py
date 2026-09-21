import unittest
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from run_siemens_s210_bge_dense_ablation import (  # noqa: E402
    _exact_hybrid_rank,
    _extract_fault_codes,
    _extract_parameters,
    _metrics,
    _rrf,
)


class BgeDenseAblationTests(unittest.TestCase):
    def test_rrf_fuses_two_rankings_at_fault_code_level(self):
        ranking = _rrf(["F1", "F2", "F3"], ["F3", "F2", "F4"])
        self.assertEqual("F3", ranking[0])
        self.assertEqual(set(["F1", "F2", "F3", "F4"]), set(ranking))

    def test_recall_at_10_is_any_relevant_hit(self):
        ranking = [f"F{index}" for index in range(1, 21)]
        metric = _metrics(ranking, {"F20"})
        self.assertEqual(0.0, metric["recall_at_5"])
        self.assertEqual(0.0, metric["recall_at_10"])
        self.assertEqual(1.0, metric["recall_at_20"])

    def test_extracts_fault_code_and_parameter_signals(self):
        self.assertEqual({"F30002"}, _extract_fault_codes("查询 F30002"))
        self.assertEqual({"P7829", "R0037"}, _extract_parameters("p7829 和 r0037[0]"))

    def test_exact_hybrid_promotes_code_and_softly_boosts_metadata(self):
        ranked, signals = _exact_hybrid_rank(
            ["F00002", "F00001", "F00003"],
            {"F00002": 0.05, "F00001": 0.04, "F00003": 0.03},
            "F00001 控制单元 p7829",
            {"F00001": {"P7829"}, "F00002": set(), "F00003": set()},
            {"F00001": "CU", "F00002": "Motor", "F00003": "Power unit"},
        )
        self.assertEqual("F00001", ranked[0])
        self.assertEqual(["F00001"], signals["fault_code_matches"])
        self.assertEqual({"F00001": ["P7829"]}, signals["parameter_matches"])


if __name__ == "__main__":
    unittest.main()
