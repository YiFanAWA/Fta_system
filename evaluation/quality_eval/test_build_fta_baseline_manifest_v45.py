from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v45 import (
    CURRENT_ARTIFACTS,
    EXPECTED_V44_SHA256,
    V44_PATH,
    build_manifest,
)
from evaluation.quality_eval.validate_fta_baseline_manifest import validate_manifest


class TestFtaBaselineManifestV45(unittest.TestCase):
    def test_reconciles_distinct_review_scopes_without_combining_them(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        tracks = manifest["review_scope_reconciliation_v1"]["tracks"]

        causal = tracks["named_expert_causal_gold_v7"]
        self.assertEqual(296, causal["decision_count"])
        self.assertEqual(205, causal["approved_relation_count"])
        self.assertEqual(91, causal["excluded_or_pending_count"])
        self.assertEqual(745, causal["unreviewed_candidate_count"])
        self.assertEqual(1041, causal["decision_count"] + causal["unreviewed_candidate_count"])
        self.assertTrue(causal["counts_partition_source_candidates"])

        ai = tracks["ai_authorized_batches_02_99"]
        self.assertEqual(281, ai["unique_event_count"])
        self.assertEqual(1041, ai["unique_candidate_count"])
        self.assertFalse(ai["reviewer_is_human_expert"])
        self.assertFalse(ai["formal_gold"])

        event_scope = tracks["event_scope_primary_review_v8"]
        self.assertEqual(39, event_scope["scope_count"])
        self.assertEqual({"AND": 0, "OR": 1, "unknown": 36}, event_scope["gate_counts_reviewed_only"])

        gate_nodes = tracks["gate_node_review_v6"]
        self.assertEqual({"AND": 12, "OR": 17, "unknown": 26}, gate_nodes["gate_counts"])
        self.assertEqual(55, gate_nodes["gate_node_count"])

        provisional = tracks["causal_gold_v7_ai_provisional_view"]
        self.assertTrue(provisional["overlaps_formal_gold"])
        self.assertFalse(provisional["additive_to_other_tracks"])

    def test_preserves_false_readiness_and_pending_live_validation(self) -> None:
        manifest = build_manifest(captured_at="2026-10-07")
        active = manifest["active_baseline"]
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(
            "pending_explicit_request_authorization",
            active["detached_observation_live_validation"],
        )

    def test_v44_is_immutable_and_registered_as_historical(self) -> None:
        self.assertEqual(EXPECTED_V44_SHA256, hashlib.sha256(V44_PATH.read_bytes()).hexdigest())
        manifest = build_manifest(captured_at="2026-10-07")
        entries = {item["path"]: item for item in manifest["artifacts"]}
        self.assertEqual(
            "historical",
            entries["evaluation/quality_eval/fta_baseline_manifest_v44.json"]["lifecycle"],
        )
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, entries)

    def test_all_manifested_artifact_hashes_validate(self) -> None:
        root = V44_PATH.parents[2]
        manifest = build_manifest(captured_at="2026-10-07")
        result = validate_manifest(manifest, repo_root=root)
        self.assertEqual(result["artifact_count"], result["verified_count"])


if __name__ == "__main__":
    unittest.main()
