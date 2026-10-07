from __future__ import annotations

import hashlib
import json
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v12 import (
    V11_PATH,
    build_manifest,
)


ROOT = V11_PATH.parents[2]


class TestFtaBaselineManifestV12(unittest.TestCase):
    def test_v12_preserves_v11_and_keeps_readiness_closed(self) -> None:
        v11_before = hashlib.sha256(V11_PATH.read_bytes()).hexdigest()
        payload = build_manifest(captured_at="2026-09-28")
        policy = payload["cause_disposition_v4_policy_regression"]

        self.assertEqual("candidate_fta_research_baseline_v12", payload["manifest_id"])
        self.assertEqual("v12", payload["superseded"][-1]["current_version"])
        self.assertEqual("fta-cause-disposition-v4", payload["active_baseline"]["cause_disposition_prompt"])
        self.assertIsNone(payload["active_baseline"]["f01681_v4_online_model_replay"])
        self.assertIn("historical_f01681_v3_development_run", payload["active_baseline"])
        self.assertEqual("v3", payload["cause_disposition_v3_online_model_replay"]["prompt_version"].rsplit("-", 1)[-1])
        self.assertEqual("offline_prompt_and_contract_regression_passed", policy["status"])
        self.assertFalse(policy["online_model_rerun"])
        self.assertFalse(policy["formal_gold"])
        self.assertFalse(policy["database_written"])
        self.assertFalse(policy["accuracy_claim_allowed"])
        self.assertFalse(payload["active_baseline"]["fta_ready"])
        self.assertFalse(payload["active_baseline"]["production_ready"])
        self.assertEqual(v11_before, hashlib.sha256(V11_PATH.read_bytes()).hexdigest())

    def test_v12_indexes_current_files_and_hashes_actual_contents(self) -> None:
        payload = build_manifest(captured_at="2026-09-28")
        paths = [item["path"] for item in payload["artifacts"]]
        artifact_ids = [item["artifact_id"] for item in payload["artifacts"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(artifact_ids), len(set(artifact_ids)))

        service_relative = "backend-python/fta/cause_disposition_service.py"
        service_path = ROOT / service_relative
        registered = next(item for item in payload["artifacts"] if item["path"] == service_relative)
        self.assertEqual(
            hashlib.sha256(service_path.read_bytes()).hexdigest(), registered["sha256"]
        )
        replay = payload["cause_disposition_v3_online_model_replay"]
        self.assertEqual("fta-cause-disposition-v3", replay["prompt_version"])
        self.assertTrue(payload["cause_disposition_v4_policy_regression"]["v3_online_replay_preserved_unchanged"])


if __name__ == "__main__":
    unittest.main()
