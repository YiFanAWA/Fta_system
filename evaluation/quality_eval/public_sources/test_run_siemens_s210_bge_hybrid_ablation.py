import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from run_siemens_s210_bge_dense_ablation import _exact_hybrid_rank  # noqa: E402
from run_siemens_s210_bge_hybrid_ablation import (  # noqa: E402
    _alarm_value_section,
    _merge_candidate_pool,
    _promoted_over_relevant,
)


class BgeHybridAblationTests(unittest.TestCase):
    def test_parameter_and_component_levels_are_incremental(self):
        base_rank = ["F00002", "F00001", "F00003"]
        base_scores = {"F00002": 0.05, "F00001": 0.04, "F00003": 0.03}
        parameters = {"F00001": {"P7829"}, "F00002": set(), "F00003": set()}
        components = {"F00001": "Drive", "F00002": "Power unit", "F00003": "CU"}

        d1, _ = _exact_hybrid_rank(
            base_rank, base_scores, "p7829", parameters, components, enabled_signals={"fault_code"}
        )
        d2, _ = _exact_hybrid_rank(
            base_rank, base_scores, "p7829", parameters, components, enabled_signals={"fault_code", "parameter"}
        )
        d3, _ = _exact_hybrid_rank(
            base_rank,
            base_scores,
            "控制单元",
            parameters,
            components,
            enabled_signals={"fault_code", "parameter", "component"},
        )
        self.assertEqual("F00002", d1[0])
        self.assertEqual("F00001", d2[0])
        self.assertEqual("F00003", d3[0])

    def test_regression_log_identifies_non_relevant_promoted_fault(self):
        promoted = _promoted_over_relevant(
            ["F00001", "F00002"],
            ["F00002", "F00001"],
            {"F00001"},
            {
                "F00001": {"fault_code": 0.0, "parameter": 0.0, "component": 0.0, "total": 0.0},
                "F00002": {"fault_code": 0.0, "parameter": 0.25, "component": 0.0, "total": 0.25},
            },
        )
        self.assertEqual("F00002", promoted[0]["fault_code"])
        self.assertEqual(["F00001"], promoted[0]["passed_relevant_fault_codes"])

    def test_alarm_chunk_stops_before_remedy(self):
        text = "Fault value (r0949):\n1: cross-compared data\nRemedy: check wiring."
        self.assertEqual("Fault value (r0949):\n1: cross-compared data", _alarm_value_section(text))

    def test_candidate_pool_unions_and_deduplicates_by_fault_code(self):
        pool = _merge_candidate_pool(["F00001", "F00002"], ["F00002", "F00003"])
        self.assertEqual(["F00001", "F00002", "F00003"], pool)


if __name__ == "__main__":
    unittest.main()
