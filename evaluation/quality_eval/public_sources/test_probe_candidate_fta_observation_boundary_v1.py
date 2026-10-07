from __future__ import annotations

import json
from hashlib import sha256
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend-python"))
sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.public_sources.probe_candidate_fta_observation_boundary_v1 import (  # noqa: E402
    CASE_ID,
    MAX_MODEL_CALLS,
    OBSERVATIONS,
    SOURCE_TEXT,
    CountingRecordingClient,
    ModelRequestBudgetExceeded,
    build_attempt_artifact,
    build_fixture,
    budget_failure_payload,
    assess_policy,
    preflight,
    render_existing_artifact,
)
from fta.candidate_fta_extraction_service import CandidateFtaExtractionService  # noqa: E402
from evaluation.quality_eval.public_sources import probe_candidate_fta_observation_boundary_v1 as probe_module  # noqa: E402


PRESERVED_RUN_PATH = (
    ROOT
    / "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.json"
)


class TestCandidateFtaObservationBoundaryProbe(unittest.TestCase):
    def test_synthetic_fixture_has_exact_distinct_observation_evidence(self) -> None:
        extraction, record = build_fixture()
        self.assertEqual(2, len(record.causes))
        self.assertEqual(OBSERVATIONS, record.causes)
        self.assertEqual(3, len(extraction.evidence_spans))
        for span in extraction.evidence_spans:
            self.assertEqual(span.quote, SOURCE_TEXT[span.start:span.end])
        self.assertNotIn("expected_gate", SOURCE_TEXT)
        self.assertEqual("OBSERVATION-COOCCURRENCE-001", CASE_ID)

    def test_preflight_never_requests_model_or_loads_reference_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = preflight(Path(temp_dir) / "run.json")
        self.assertEqual("preflight_only", result["status"])
        self.assertFalse(result["model_request_performed"])
        self.assertFalse(result["reference_labels_loaded"])
        self.assertFalse(result["gold_included_in_model_input"])
        self.assertEqual(0, result["sdk_max_retries"])
        self.assertEqual(0, result["outer_retries"])
        self.assertEqual(1, result["planned_max_model_calls"])
        self.assertTrue(result["output_paths_available"])

    def test_second_pipeline_stage_is_blocked_and_first_raw_response_is_preserved(self) -> None:
        extraction, record = build_fixture()
        raw_response = json.dumps(
            {
                "cause_dispositions": [
                    {
                        "source_cause_index": index,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": cause,
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "测试预算门禁；不作为语义结论。",
                    }
                    for index, cause in enumerate(record.causes)
                ]
            },
            ensure_ascii=False,
        )

        class RecordingDelegate:
            call_count = 0

            def complete(self, _prompt):
                self.call_count += 1
                return raw_response

        delegate = RecordingDelegate()
        client = CountingRecordingClient(delegate)
        with self.assertRaises(ModelRequestBudgetExceeded) as raised:
            CandidateFtaExtractionService(client).propose(
                extraction, record.record_id, SOURCE_TEXT
            )

        failure = budget_failure_payload(raised.exception)
        artifact = build_attempt_artifact(
            client,
            extraction=extraction,
            record=record,
            started_at="2026-09-29T00:00:00+00:00",
            run_status="blocked",
            failure=failure,
        )
        serialized = json.loads(json.dumps(artifact, ensure_ascii=False))

        self.assertEqual(1, MAX_MODEL_CALLS)
        self.assertEqual(1, delegate.call_count)
        self.assertEqual(1, serialized["request_attempt_count"])
        self.assertEqual(1, serialized["successful_response_count"])
        self.assertEqual(raw_response, serialized["model_stage_responses"][0]["response"])
        self.assertEqual("cause_disposition", serialized["model_stage_responses"][0]["stage"])
        self.assertEqual("blocked", serialized["run_status"])
        self.assertEqual("structure_decomposition", serialized["failure"]["stage"])
        self.assertEqual("model_request_budget_exceeded", serialized["failure"]["error_code"])
        self.assertTrue(serialized["failure"]["blocked_before_provider_call"])
        self.assertEqual(2, serialized["failure"]["attempted_request_index"])
        self.assertIsNone(serialized["tree"])

    def test_run_once_persists_blocked_budget_failure_without_network_retry(self) -> None:
        extraction, record = build_fixture()
        raw_response = json.dumps(
            {
                "cause_dispositions": [
                    {
                        "source_cause_index": index,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": cause,
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "离线测试响应；不作为语义结论。",
                    }
                    for index, cause in enumerate(record.causes)
                ]
            },
            ensure_ascii=False,
        )

        class RecordingDelegate:
            call_count = 0

            def complete(self, _prompt):
                self.call_count += 1
                return raw_response

        delegate = RecordingDelegate()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "blocked.json"
            with (
                patch.object(probe_module, "OPENAI_API_KEY", "offline-test-key"),
                patch.object(probe_module, "OpenAICompatibleModelClient", return_value=delegate),
            ):
                result = probe_module.run_once(output)

            persisted = json.loads(output.read_text(encoding="utf-8"))
            report = output.with_suffix(".md").read_text(encoding="utf-8")

        self.assertEqual(1, delegate.call_count)
        self.assertEqual("blocked", result["run_status"])
        self.assertEqual("model_request_budget_exceeded", result["failure"]["error_code"])
        self.assertEqual(raw_response, persisted["model_stage_responses"][0]["response"])
        self.assertEqual("blocked", persisted["run_status"])
        self.assertIn("model_request_budget_exceeded", report)
        self.assertEqual(1, persisted["model"]["max_model_calls"])

    def test_attempt_artifact_is_json_safe_and_preserves_fixture_identity(self) -> None:
        extraction, record = build_fixture()
        artifact = build_attempt_artifact(
            CountingRecordingClient(object()),
            extraction=extraction,
            record=record,
            started_at="2026-09-29T00:00:00+00:00",
            run_status="blocked",
        )
        encoded = json.dumps(artifact, ensure_ascii=False)
        decoded = json.loads(encoded)
        synthetic = decoded["synthetic_input"]
        self.assertEqual(record.record_id, synthetic["record"]["record_id"])
        self.assertTrue(all(
            span["record_id"] == record.record_id
            for span in synthetic["evidence_spans"]
        ))
        self.assertEqual("cause", synthetic["evidence_spans"][1]["field"])
        self.assertFalse(synthetic["gold_included_in_model_input"])

    def test_existing_run_report_can_be_rendered_without_model_access(self) -> None:
        extraction, record = build_fixture()
        artifact = build_attempt_artifact(
            CountingRecordingClient(object()),
            extraction=extraction,
            record=record,
            started_at="2026-09-29T00:00:00+00:00",
            run_status="response_received",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "run.json"
            output.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
            result = render_existing_artifact(output)
            report = output.with_suffix(".md").read_text(encoding="utf-8")
        self.assertEqual("report_rendered_from_preserved_response", result["status"])
        self.assertFalse(result["model_request_performed"])
        self.assertIn("SDK 自动重试：0", report)

    def test_preserved_model_response_replays_to_detached_observations_offline(self) -> None:
        artifact = json.loads(PRESERVED_RUN_PATH.read_text(encoding="utf-8"))
        response_entry = next(
            item
            for item in artifact["model_stage_responses"]
            if item["stage"] == "cause_disposition"
        )
        raw_response = response_entry["response"]
        self.assertEqual(
            response_entry["response_sha256"],
            sha256(raw_response.encode("utf-8")).hexdigest(),
        )
        extraction, record = build_fixture()

        class PreservedResponseClient:
            call_count = 0

            def complete(self, _prompt):
                self.call_count += 1
                return raw_response

        client = PreservedResponseClient()
        tree = CandidateFtaExtractionService(client).propose(
            extraction, record.record_id, SOURCE_TEXT
        )
        policy = assess_policy(tree)

        self.assertEqual(1, client.call_count)
        self.assertTrue(policy["policy_boundary_match"], policy)
        self.assertEqual(
            {"alarm A was logged", "alarm B was logged"},
            {
                node.text
                for node in tree.nodes
                if node.node_type == "observation_candidate"
            },
        )
        self.assertEqual((), tree.gate_assessments)
        self.assertEqual((), tree.relations)


if __name__ == "__main__":
    unittest.main()
