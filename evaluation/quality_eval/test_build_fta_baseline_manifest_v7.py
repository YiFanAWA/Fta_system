from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from evaluation.quality_eval.build_fta_baseline_manifest_v7 import (
    V6_PATH,
    build_manifest,
)


ROOT = Path(__file__).resolve().parents[2]


class TestFtaBaselineManifestV7(unittest.TestCase):
    def test_v7_inherits_frozen_sets_and_keeps_final_and_readiness_blocked(self) -> None:
        v6_before = hashlib.sha256(V6_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")

        self.assertEqual("candidate_fta_research_baseline_v7", payload["manifest_id"])
        self.assertEqual(["v6"], payload["superseded"][-1]["superseded_versions"])
        self.assertEqual("v7", payload["superseded"][-1]["current_version"])
        self.assertEqual(36, payload["behavior_regression_suite"]["sample_count"])
        self.assertEqual(15, payload["behavior_regression_suite"]["source_cluster_count"])
        self.assertEqual(11, payload["development_gate_suite"]["sample_count"])
        self.assertEqual(3, payload["development_gate_suite"]["source_cluster_count"])
        self.assertEqual("not_created", payload["independent_final_validation"]["status"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertFalse(payload["raw_text_preview_regressions"]["formal_gold"])
        self.assertFalse(payload["raw_text_preview_regressions"]["database_written"])
        self.assertFalse(payload["raw_text_preview_regressions"]["accuracy_claim_allowed"])
        self.assertEqual(v6_before, hashlib.sha256(V6_PATH.read_bytes()).hexdigest())

    def test_v7_fingerprints_current_prompt_runs_and_truth_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        artifacts = payload["artifacts"]
        paths = [item["path"] for item in artifacts]
        self.assertEqual(len(paths), len(set(paths)))
        required_paths = {
            "backend-python/fta/candidate_fta_extraction_service.py",
            "backend-python/tests/test_candidate_fta_extraction_service.py",
            "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py",
            "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py",
            "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.json",
            "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.json",
            "docs/current-state-audit.md",
            "docs/acceptance.md",
            "docs/candidate-fta-generation-v1.md",
            "docs/README.md",
        }
        self.assertTrue(required_paths.issubset(set(paths)))
        for artifact in artifacts:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(
                artifact["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["path"],
            )


if __name__ == "__main__":
    unittest.main()
