from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v24 import V24_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v25 import build_manifest


class TestFtaBaselineManifestV25(unittest.TestCase):
    def test_v25_records_qualitative_mismatch_without_score_or_readiness_promotion(self) -> None:
        v24_hash = hashlib.sha256(V24_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")
        self.assertEqual("candidate_fta_research_baseline_v25", payload["manifest_id"])
        self.assertEqual("v25", payload["baseline_version"])
        comparison = payload["event_scope_model_post_run_comparison"]
        self.assertEqual("qualitative_dev_comparison_complete_tree_not_accepted", comparison["status"])
        self.assertFalse(comparison["scoring_performed"])
        self.assertFalse(comparison["semantic_tree_accepted"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v24_hash, hashlib.sha256(V24_PATH.read_bytes()).hexdigest())

    def test_v25_registers_comparison_report_and_current_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        self.assertIn("evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json", paths)
        self.assertIn("evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md", paths)
        self.assertIn("evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py", paths)
        self.assertIn("docs/README.md", paths)
        self.assertIn("docs/acceptance.md", paths)


if __name__ == "__main__":
    unittest.main()
