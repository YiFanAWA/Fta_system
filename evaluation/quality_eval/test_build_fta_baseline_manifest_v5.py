from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from evaluation.quality_eval.build_fta_baseline_manifest_v5 import build_manifest


ROOT = Path(__file__).resolve().parents[2]


class TestFtaBaselineManifestV5(unittest.TestCase):
    def test_seen_gate_probes_are_frozen_as_regressions_not_final_test(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        suite = payload["behavior_regression_suite"]

        self.assertEqual("frozen_seen_behavior_regression", suite["status"])
        self.assertEqual(36, suite["sample_count"])
        self.assertEqual(36, suite["unique_case_count"])
        self.assertEqual(15, suite["source_cluster_count"])
        self.assertEqual({"AND": 9, "OR": 15, "unknown": 12}, suite["label_counts"])
        self.assertFalse(suite["formal_gold"])
        self.assertFalse(suite["training_set"])
        self.assertFalse(suite["accuracy_claim_allowed"])
        self.assertTrue(all(not item["final_test_eligible"] for item in suite["dataset_suites"]))
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertEqual(0, payload["independent_final_validation"]["sample_count"])
        self.assertEqual(0, payload["independent_final_validation"]["source_cluster_count"])

    def test_evidence_modes_and_case_invariants_preserve_abstention_boundaries(self) -> None:
        suite = build_manifest(captured_at="2026-09-28")["behavior_regression_suite"]
        by_id = {case["gate_node_id"]: case for case in suite["cases"]}
        self.assertEqual(36, len(by_id))

        unknown = [case for case in by_id.values() if case["expected_gate"] == "unknown"]
        decisive = [case for case in by_id.values() if case["expected_gate"] in {"AND", "OR"}]
        self.assertEqual(12, len(unknown))
        self.assertEqual(24, len(decisive))
        self.assertTrue(all("do_not_force_and_or_without_direct_gate_evidence" in case["expected_invariants"] for case in unknown))
        self.assertTrue(all(case["source_reference"]["source_sha256"] for case in by_id.values()))
        self.assertTrue(all(case["source_reference"]["dataset_path"] for case in by_id.values()))
        self.assertTrue(all(case["source_reference"]["reference_type"] != "no_decisive_gate_quote_in_model_visible_scope" for case in decisive))

        ablation = [case for case in unknown if case["evidence_mode"] == "decisive_text_evidence_withheld_control"]
        self.assertEqual(6, len(ablation))
        self.assertTrue(all("withheld_decisive_evidence_must_remain_unknown" in case["expected_invariants"] for case in ablation))

        diagram = [case for case in by_id.values() if case["source_reference"]["reference_type"] == "explicit_diagram_gate_symbol"]
        self.assertEqual(13, len(diagram))

    def test_every_listed_artifact_hash_matches_the_current_file(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifact_paths = [artifact["path"] for artifact in payload["artifacts"]]
        self.assertEqual(len(artifact_paths), len(set(artifact_paths)))
        for artifact in payload["artifacts"]:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, artifact["sha256"], artifact["path"])


if __name__ == "__main__":
    unittest.main()
