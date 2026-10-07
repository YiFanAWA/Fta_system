from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v44 import (
    CURRENT_ARTIFACTS,
    V43_PATH,
    build_manifest,
)


class TestFtaBaselineManifestV44(unittest.TestCase):
    def test_v44_records_pre_fix_mismatch_without_promoting_readiness(self) -> None:
        v43_hash = hashlib.sha256(V43_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        boundary = manifest["candidate_fta_observation_boundary_v2"]

        self.assertEqual("candidate_fta_research_baseline_v44", manifest["manifest_id"])
        self.assertEqual("v44", manifest["baseline_version"])
        self.assertEqual(
            "preserve_detached_observation_candidates_without_graph_links_v2",
            active["candidate_fta_observation_link_policy"],
        )
        self.assertFalse(boundary["pre_fix_live_run"]["policy_boundary_match"])
        self.assertFalse(boundary["corrected_behavior_live_validation_performed"])
        self.assertEqual(
            "preserved_response_offline_replay_passed_live_validation_pending",
            boundary["status"],
        )
        replay = boundary["preserved_response_offline_replay"]
        self.assertEqual(0, replay["provider_requests"])
        self.assertFalse(replay["raw_response_modified"])
        self.assertEqual(2, replay["distinct_observation_nodes"])
        self.assertTrue(replay["policy_boundary_match"])
        self.assertEqual(1, boundary["pre_fix_live_run"]["model_request_count"])
        self.assertEqual(0, boundary["pre_fix_live_run"]["sdk_retries"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v43_hash, hashlib.sha256(V43_PATH.read_bytes()).hexdigest())

    def test_v44_registers_runtime_probe_outputs_and_current_docs(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, artifacts)
        self.assertEqual(
            "historical",
            artifacts["evaluation/quality_eval/fta_baseline_manifest_v43.json"]["lifecycle"],
        )
        self.assertEqual(
            "current",
            artifacts["backend-python/contracts/candidate_fta_contract.py"]["lifecycle"],
        )
        self.assertIn(
            "observation_candidate",
            manifest["candidate_fta_observation_boundary_v2"][
                "corrected_behavior_offline_contract"
            ]["node_type"],
        )


if __name__ == "__main__":
    unittest.main()
