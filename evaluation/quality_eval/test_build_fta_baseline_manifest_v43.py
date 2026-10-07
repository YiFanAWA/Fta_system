from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_baseline_manifest_v43 import CURRENT_ARTIFACTS, V42_PATH, build_manifest


class TestFtaBaselineManifestV43(unittest.TestCase):
    def test_v43_records_policy_without_promoting_readiness_or_accuracy(self) -> None:
        v42_hash = hashlib.sha256(V42_PATH.read_bytes()).hexdigest()
        manifest = build_manifest(captured_at="2026-09-29")
        active = manifest["active_baseline"]
        policy = manifest["candidate_fta_semantic_policy_v1"]

        self.assertEqual("candidate_fta_research_baseline_v43", manifest["manifest_id"])
        self.assertEqual("v43", manifest["baseline_version"])
        self.assertEqual("retain_disconnected_observation_nodes_and_block_whole_tree_without_causal_evidence_v1", active["candidate_fta_observation_link_policy"])
        self.assertEqual("infer_from_complete_propositions_not_operator_keywords_v1", active["candidate_fta_gate_semantics_policy"])
        self.assertFalse(policy["model_request_performed"])
        self.assertFalse(policy["human_expert_gold"])
        self.assertFalse(policy["accuracy_or_calibration_claim_allowed"])
        self.assertFalse(active["fta_ready"])
        self.assertFalse(active["production_ready"])
        self.assertEqual(v42_hash, hashlib.sha256(V42_PATH.read_bytes()).hexdigest())

    def test_v43_registers_all_current_policy_sources(self) -> None:
        manifest = build_manifest(captured_at="2026-09-29")
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        for path in CURRENT_ARTIFACTS:
            self.assertIn(path, artifacts)
        self.assertEqual("historical", artifacts["evaluation/quality_eval/fta_baseline_manifest_v42.json"]["lifecycle"])
        self.assertEqual("current", artifacts["backend-python/fta/candidate_fta_extraction_service.py"]["lifecycle"])


if __name__ == "__main__":
    unittest.main()
