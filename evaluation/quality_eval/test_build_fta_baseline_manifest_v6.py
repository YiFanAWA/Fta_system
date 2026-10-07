from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from evaluation.quality_eval.build_fta_baseline_manifest_v6 import V5_PATH, build_manifest


ROOT = Path(__file__).resolve().parents[2]


class TestFtaBaselineManifestV6(unittest.TestCase):
    def test_new_development_set_is_disjoint_and_final_remains_uncreated(self) -> None:
        v5_before = hashlib.sha256(V5_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        suite = payload["development_gate_suite"]

        self.assertEqual("candidate_fta_research_baseline_v6", payload["manifest_id"])
        self.assertEqual("allocated_development_not_formal_gold", suite["status"])
        self.assertEqual(11, suite["sample_count"])
        self.assertEqual(3, suite["source_document_count"])
        self.assertEqual(3, suite["source_cluster_count"])
        self.assertEqual({"AND": 5, "OR": 6}, suite["label_counts"])
        self.assertFalse(suite["formal_gold"])
        self.assertFalse(suite["accuracy_claim_allowed"])
        self.assertFalse(suite["overlap_with_seen_behavior_regression"])
        self.assertFalse(suite["final_test_eligible"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual([], payload["source_cluster_allocation"]["independent_final_validation"]["source_clusters"])
        self.assertEqual(v5_before, hashlib.sha256(V5_PATH.read_bytes()).hexdigest())

    def test_v6_artifact_hashes_cover_dataset_sources_and_current_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifacts = payload["artifacts"]
        paths = [item["path"] for item in artifacts]
        self.assertEqual(len(paths), len(set(paths)))
        required_paths = {
            "evaluation/quality_eval/datasets/fta_gate_diagram_development_v1.json",
            "evaluation/quality_eval/public_sources/source_pdfs/DOE-HDBK-1100-2004-ReaffOct2022.pdf",
            "evaluation/quality_eval/public_sources/source_pdfs/FAA-SRM-Guidance-2024.pdf",
            "evaluation/quality_eval/public_sources/source_pdfs/NASA-FDIR-Report-1994.pdf",
            "evaluation/quality_eval/public_sources/test_fta_gate_diagram_development_v1.py",
        }
        self.assertTrue(required_paths.issubset(set(paths)))
        for artifact in artifacts:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(artifact["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), artifact["path"])


if __name__ == "__main__":
    unittest.main()
