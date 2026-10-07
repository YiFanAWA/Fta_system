from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v16 import V15_PATH, build_manifest


class TestFtaBaselineManifestV16(unittest.TestCase):
    def test_v16_registers_scoped_readiness_without_promoting_global_flags(self) -> None:
        v15_before = hashlib.sha256(V15_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        assessment = payload["scoped_readiness_assessment"]

        self.assertEqual("candidate_fta_research_baseline_v16", payload["manifest_id"])
        self.assertEqual("blocked", assessment["structure_status"])
        self.assertEqual("blocked", assessment["quantitative_status"])
        self.assertEqual(47, assessment["case_count"])
        self.assertEqual(18, assessment["source_cluster_count"])
        self.assertFalse(assessment["human_expert_reviewed"])
        self.assertFalse(assessment["scope_can_promote_global_readiness"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v15_before, hashlib.sha256(V15_PATH.read_bytes()).hexdigest())

    def test_v16_artifact_registry_pins_report_and_builder_inputs(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        paths = {artifact["path"] for artifact in payload["artifacts"]}
        self.assertIn(payload["scoped_readiness_assessment"]["report_path"], paths)
        self.assertIn("evaluation/quality_eval/fta_baseline_manifest_v15.json", paths)
        self.assertIn("evaluation/quality_eval/build_fta_scoped_readiness_report_v1.py", paths)
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])


if __name__ == "__main__":
    unittest.main()
