from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v13 import (
    REVIEW_PATH,
    RUN_PATH,
    V12_PATH,
    build_manifest,
)


ROOT = V12_PATH.parents[2]


class TestFtaBaselineManifestV13(unittest.TestCase):
    def test_v13_preserves_v12_and_keeps_gold_database_and_readiness_closed(self) -> None:
        v12_before = hashlib.sha256(V12_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        replay = payload["cause_disposition_v4_online_model_replay"]

        self.assertEqual("candidate_fta_research_baseline_v13", payload["manifest_id"])
        self.assertEqual("v13", payload["superseded"][-1]["current_version"])
        self.assertEqual("fta-cause-disposition-v4", payload["active_baseline"]["cause_disposition_prompt"])
        self.assertEqual({"total": 16, "causal_summary_relation_only": 1, "diagnostic_mapping_relation_only": 15}, replay["cause_disposition_counts"])
        self.assertEqual(["fault_extraction", "cause_disposition"], replay["stages"])
        self.assertEqual(["structure_decomposition", "gate_assessment"], replay["stages_skipped"])
        self.assertEqual("blocked", replay["candidate_tree_status"])
        self.assertEqual("PASS", replay["independent_ai_review"]["conclusion"])
        self.assertFalse(replay["formal_gold"])
        self.assertFalse(replay["database_written"])
        self.assertFalse(replay["accuracy_claim_allowed"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v12_before, hashlib.sha256(V12_PATH.read_bytes()).hexdigest())

    def test_v13_verifies_replay_and_review_file_hashes(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        paths = [item["path"] for item in payload["artifacts"]]
        ids = [item["artifact_id"] for item in payload["artifacts"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(ids), len(set(ids)))
        for file_path in (RUN_PATH, REVIEW_PATH):
            relative = file_path.relative_to(ROOT).as_posix()
            artifact = next(item for item in payload["artifacts"] if item["path"] == relative)
            self.assertEqual(hashlib.sha256(file_path.read_bytes()).hexdigest(), artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
