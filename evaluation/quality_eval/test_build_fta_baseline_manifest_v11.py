from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v11 import (
    F01681_V3_PATH,
    V10_PATH,
    build_manifest,
)


ROOT = V10_PATH.parents[2]


class TestFtaBaselineManifestV11(unittest.TestCase):
    def test_v11_preserves_v10_and_keeps_readiness_closed(self) -> None:
        v10_before = hashlib.sha256(V10_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        replay = payload["cause_disposition_v3_online_model_replay"]

        self.assertEqual("candidate_fta_research_baseline_v11", payload["manifest_id"])
        self.assertEqual("v11", payload["superseded"][-1]["current_version"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(4, replay["request_attempt_count"])
        self.assertEqual(4, replay["successful_response_count"])
        self.assertEqual(0, replay["configured_max_retries"])
        self.assertEqual({"fta_event_candidate": 1, "relation_only": 15}, replay["cause_disposition_counts"])
        self.assertFalse(replay["formal_gold"])
        self.assertFalse(replay["database_written"])
        self.assertFalse(replay["accuracy_claim_allowed"])
        self.assertFalse(replay["remedy_xxxx_9507_scope_reconciled"])
        self.assertEqual(v10_before, hashlib.sha256(V10_PATH.read_bytes()).hexdigest())

    def test_v11_indexes_run_and_hashes_actual_files(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        paths = [item["path"] for item in payload["artifacts"]]
        artifact_ids = [item["artifact_id"] for item in payload["artifacts"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(artifact_ids), len(set(artifact_ids)))
        replay = json.loads(F01681_V3_PATH.read_text(encoding="utf-8"))
        self.assertEqual("fta-cause-disposition-v3", replay["prompt_versions"]["cause_disposition"])
        self.assertEqual(
            hashlib.sha256(F01681_V3_PATH.read_bytes()).hexdigest(),
            next(item["sha256"] for item in payload["artifacts"] if item["path"] == F01681_V3_PATH.relative_to(ROOT).as_posix()),
        )


if __name__ == "__main__":
    unittest.main()
