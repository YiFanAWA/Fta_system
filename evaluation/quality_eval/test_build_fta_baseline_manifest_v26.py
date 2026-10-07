from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v25 import V25_PATH
from evaluation.quality_eval.build_fta_baseline_manifest_v26 import build_manifest


class TestFtaBaselineManifestV26(unittest.TestCase):
    def test_v26_registers_fail_closed_hierarchy_without_promoting_readiness(self) -> None:
        v25_hash = hashlib.sha256(V25_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-29")
        self.assertEqual("candidate_fta_research_baseline_v26", payload["manifest_id"])
        self.assertEqual("v26", payload["baseline_version"])
        self.assertEqual("gate_scopes", payload["active_baseline"]["event_scope_hierarchy_owner"])
        self.assertEqual(
            "validate_projection_only_block_conflict_preserve_output",
            payload["active_baseline"]["event_scope_parent_id_policy"],
        )
        self.assertEqual("not_run", payload["active_baseline"]["event_scope_prepared_prompt_status"])
        comparison = payload["event_scope_model_post_run_comparison"]
        self.assertEqual(6, comparison["hierarchy_contract_blocker_count"])
        self.assertFalse(comparison["raw_model_output_modified"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v25_hash, hashlib.sha256(V25_PATH.read_bytes()).hexdigest())

    def test_v26_registers_contract_prompt_tests_and_current_docs(self) -> None:
        payload = build_manifest(captured_at="2026-09-29")
        paths = {item["path"] for item in payload["artifacts"]}
        for path in (
            "evaluation/quality_eval/event_scope_tree_contract.py",
            "evaluation/quality_eval/event_scope_tree_prompt_v3.py",
            "evaluation/quality_eval/test_event_scope_tree_contract.py",
            "evaluation/quality_eval/test_build_fta_baseline_manifest_v26.py",
            "docs/README.md",
            "docs/acceptance.md",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
