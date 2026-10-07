from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from evaluation.quality_eval.build_fta_baseline_manifest_v4 import build_manifest


ROOT = Path(__file__).resolve().parents[2]


class TestFtaBaselineManifestV4(unittest.TestCase):
    def test_v4_uses_current_v6_review_and_reports_limits(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")

        self.assertEqual("candidate_fta_research_baseline_v4", payload["manifest_id"])
        self.assertEqual("v4", payload["baseline_version"])
        self.assertEqual("v3", payload["supersedes_manifest"]["manifest_id"][-2:])

        overlap = payload["s120_s150_overlap_audit"]
        self.assertIn("overlap_audit_v4_2026-09-28.json", overlap["audit_artifact"])
        self.assertEqual(55, overlap["s210_gate_nodes"])
        self.assertEqual(53, overlap["gate_nodes_with_same_code_in_s120_s150"])
        self.assertEqual("34/55", overlap["overall_exact_scope_quote_overlap_ratio"])
        self.assertEqual("34/53", overlap["conditional_exact_scope_quote_overlap_ratio"])
        self.assertIn("near-transfer", overlap["classification"])
        self.assertIn("not independent", overlap["classification"])

        scope = payload["label_and_evaluation_scope"]
        gate_review = scope["gate_node_v6"]
        self.assertEqual({"AND": 12, "OR": 17, "unknown": 26}, gate_review["class_counts"])
        self.assertFalse(gate_review["reviewer_is_human_expert"])
        self.assertFalse(gate_review["formal_gold"])
        self.assertEqual(55, sum(gate_review["reviewer_provenance_counts"].values()))

        split = scope["gate_node_split_v6"]
        self.assertEqual(47, split["fault_source_groups"])
        self.assertEqual(0, split["cross_split_fault_code_count"])
        self.assertEqual(0, split["cross_split_source_cluster_count"])
        self.assertEqual(
            {"AND": 4, "OR": 3, "unknown": 5},
            split["split_class_support"]["validation"]["gate_counts"],
        )
        self.assertEqual("insufficient_evidence", split["calibration_status"])
        self.assertFalse(split["independent_source_validation"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])

    def test_all_v4_artifact_fingerprints_match_files(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        for artifact in payload["artifacts"]:
            path = ROOT / artifact["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, artifact["sha256"], artifact["path"])


if __name__ == "__main__":
    unittest.main()
