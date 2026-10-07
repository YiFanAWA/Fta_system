import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend-python"))
sys.path.insert(0, str(ROOT / "evaluation" / "quality_eval" / "public_sources"))

from build_siemens_s210_recursive_fta_preview_v2 import (  # noqa: E402
    DEFAULT_OVERLAY,
    DEFAULT_SOURCE,
    build_preview,
)
from contracts.fta_graph_contract import validate_fta_preview  # noqa: E402


class SiemensS210RecursiveFtaPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = DEFAULT_SOURCE.read_bytes()
        cls.source_sha256 = hashlib.sha256(cls.source_bytes).hexdigest()
        cls.source = json.loads(cls.source_bytes.decode("utf-8"))
        cls.overlay = json.loads(DEFAULT_OVERLAY.read_text(encoding="utf-8"))

    def test_recursive_preview_builds_only_three_scoped_trees(self):
        preview = build_preview(self.source, self.overlay, self.source_sha256)
        self.assertEqual([], validate_fta_preview(preview))
        self.assertEqual("v2", preview["artifact_version"])
        self.assertEqual(3, preview["dataset_info"]["tree_count"])
        self.assertEqual(1, preview["dataset_info"]["excluded_event_count"])
        self.assertEqual(
            {"F01911", "F07900", "F07901"},
            {tree["top_event"]["fault_code"] for tree in preview["trees"]},
        )
        self.assertEqual("F30655", preview["excluded_events"][0]["fault_code"])
        self.assertEqual(18, preview["dataset_info"]["verified_source_span_count"])
        self.assertEqual(17, preview["dataset_info"]["verified_tree_span_count"])
        self.assertEqual(1, preview["dataset_info"]["verified_exclusion_span_count"])
        self.assertFalse(preview["dataset_info"]["human_expert_signature"])
        self.assertFalse(preview["dataset_info"]["formal_gold_mutated"])
        self.assertFalse(preview["dataset_info"]["database_written"])
        self.assertFalse(preview["dataset_info"]["fta_ready"])
        self.assertFalse(preview["dataset_info"]["production_ready"])

    def test_f07900_preserves_nested_or_of_and_and_duration_caveat(self):
        preview = build_preview(self.source, self.overlay, self.source_sha256)
        tree = next(item for item in preview["trees"] if item["top_event"]["fault_code"] == "F07900")
        self.assertEqual("OR", tree["gate"])
        self.assertEqual(2, len(tree["children"]))
        self.assertEqual({"AND"}, {edge["node"]["gate"] for edge in tree["children"]})
        first_path = tree["children"][0]["node"]
        self.assertIn("不作额外推断", first_path["text"])
        self.assertEqual(2, len(first_path["children"]))
        self.assertTrue(all(edge["node"]["node_type"] == "trigger_condition" for edge in first_path["children"]))

    def test_modified_source_span_fails_closed(self):
        overlay = copy.deepcopy(self.overlay)
        first_evidence = overlay["gate_decisions"][0]["reviewed_tree"]["gate_evidence"][0]
        first_evidence["start"] += 1
        with self.assertRaisesRegex(ValueError, "quote does not exactly match source offsets"):
            build_preview(self.source, overlay, self.source_sha256)

    def test_overlay_cannot_claim_human_signature(self):
        overlay = copy.deepcopy(self.overlay)
        overlay["human_expert_signature"] = True
        with self.assertRaisesRegex(ValueError, "must not claim a human expert signature"):
            build_preview(self.source, overlay, self.source_sha256)


if __name__ == "__main__":
    unittest.main()
