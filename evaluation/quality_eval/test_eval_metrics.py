from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


metrics = _load_module(
    "run_eval_benchmark_under_test",
    ROOT / "evaluation" / "quality_eval" / "run_eval_benchmark.py",
)
logic = _load_module(
    "event_logic_eval_under_test",
    ROOT / "evaluation" / "quality_eval" / "event_logic_eval.py",
)


class EvaluationMetricTests(unittest.TestCase):
    def test_f1_formula_uses_micro_counts(self):
        precision, recall, f1 = logic._f1(54, 41, 17)
        self.assertEqual(round(precision, 6), 0.568421)
        self.assertEqual(round(recall, 6), 0.760563)
        self.assertEqual(round(f1, 6), 0.650602)


    def test_unknown_null_fields_are_not_hallucinated(self):
        sample = {"input_text": "Problem: motor stopped\nAction: replaced fuse"}
        prediction = {
            "extracted_faults": {
                "records": [
                    {
                        "fault_code": None,
                        "component": None,
                        "description": "motor stopped",
                        "causes": [],
                        "parameters": [],
                    }
                ]
            }
        }
        self.assertEqual(
            metrics._hallucination_counts(sample, prediction),
            {"total": 1, "hallucinated": 0},
        )


    def test_tree_top_event_is_not_counted_as_basic_event(self):
        prediction = {
            "extracted_faults": {"records": [{"causes": ["fuse open"]}]},
            "tree": {"top": "motor stopped", "gate": "OR", "children": []},
        }
        self.assertEqual(logic._extract_pred_basic_events(prediction), {"fuseopen"})


if __name__ == "__main__":
    unittest.main()
