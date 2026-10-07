from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v14 import (
    REVIEW_PATH,
    V13_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV14(unittest.TestCase):
    def test_v14_records_remedy_only_and_keeps_scope_and_readiness_unresolved(self) -> None:
        v13_before = hashlib.sha256(V13_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        review = payload["f01681_remedy_9507_scope_reconciliation"]

        self.assertEqual("candidate_fta_research_baseline_v14", payload["manifest_id"])
        self.assertEqual("v14", payload["superseded"][-1]["current_version"])
        self.assertEqual("reviewed_remedy_only_scope_completeness_unresolved", review["status"])
        self.assertFalse(review["candidate_event_added"])
        self.assertFalse(review["causal_edge_supported"])
        self.assertEqual("unresolved", review["cause_set_completeness"])
        self.assertEqual("ai_subagent_read_only_role_review_not_human_expert", review["review_provenance"])
        self.assertFalse(review["formal_gold"])
        self.assertFalse(review["database_written"])
        self.assertFalse(review["fta_ready"])
        self.assertFalse(review["production_ready"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v13_before, hashlib.sha256(V13_PATH.read_bytes()).hexdigest())

    def test_v14_registers_review_artifact_hash(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        relative = REVIEW_PATH.relative_to(V13_PATH.parents[2]).as_posix()
        artifact = next(item for item in payload["artifacts"] if item["path"] == relative)
        self.assertEqual(hashlib.sha256(REVIEW_PATH.read_bytes()).hexdigest(), artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
