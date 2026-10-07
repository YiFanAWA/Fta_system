from __future__ import annotations

import hashlib
import unittest

from evaluation.quality_eval.build_fta_generation_eval_lock_v1 import (
    PINNED_SOURCES,
    ROOT,
    build_lock,
)


class TestBuildFtaGenerationEvalLockV1(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = {
            "model_id": "deepseek-flash",
            "base_url": "https://api.deepseek.com/v1?token=must-not-be-recorded",
            "timeout_seconds": 120,
            "max_retries": 2,
            "credential_configured": True,
        }

    def test_lock_pins_runner_sources_and_marks_evaluation_not_run(self) -> None:
        lock = build_lock(runtime=self.runtime, captured_at="2026-09-28")

        self.assertEqual("pinned_candidate_eval_configuration", lock["configuration_status"])
        self.assertEqual("not_run", lock["model_inference_status"])
        self.assertEqual("not_created", lock["independent_final_validation"]["status"])
        self.assertEqual(len(PINNED_SOURCES), len(lock["prompt_parser_and_contract_sources"]))
        self.assertEqual(
            "deepseek-flash",
            lock["model"]["model_id"],
        )
        self.assertEqual("api.deepseek.com", lock["model"]["endpoint"]["host"])
        self.assertIsNone(lock["model"]["endpoint"].get("query"))
        self.assertFalse(lock["model"]["credential_value_recorded"])
        self.assertNotIn("must-not-be-recorded", str(lock))

        expected_path, expected_role = PINNED_SOURCES[0]
        source_entry = lock["prompt_parser_and_contract_sources"][0]
        expected_hash = hashlib.sha256((ROOT / expected_path).read_bytes()).hexdigest()
        self.assertEqual({"path": expected_path, "role": expected_role, "sha256": expected_hash}, source_entry)

    def test_lock_rejects_invalid_runtime_values(self) -> None:
        for field, value in (("model_id", ""), ("timeout_seconds", 0), ("max_retries", -1)):
            runtime = dict(self.runtime)
            runtime[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_lock(runtime=runtime, captured_at="2026-09-28")


if __name__ == "__main__":
    unittest.main()
