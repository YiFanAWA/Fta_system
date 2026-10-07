from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from probe_candidate_fta_raw_source_v1 import (
    CountingClient,
    RequestBudgetClient,
    build_artifact,
    check_text_references,
    classify_response_stage,
    evidence_integrity,
    load_sample,
    revalidate_existing_artifact,
)
from core.model_client import ModelClientError, RetryingModelClient


class ProbeCandidateFtaRawSourceTests(unittest.TestCase):
    def test_request_budget_blocks_before_exceeding_authorized_limit(self) -> None:
        class Delegate:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, prompt: str) -> str:
                self.calls += 1
                return f"response-{self.calls}"

        delegate = Delegate()
        counted = CountingClient(delegate)
        budgeted = RequestBudgetClient(counted, max_model_calls=2)
        client = RetryingModelClient(budgeted, max_retries=0)

        self.assertEqual("response-1", client.complete("first"))
        self.assertEqual("response-2", client.complete("second"))
        with self.assertRaises(ModelClientError) as raised:
            client.complete("must not reach provider")

        self.assertEqual("evaluation_model_call_budget_exhausted", raised.exception.code)
        self.assertTrue(budgeted.budget_exhausted)
        self.assertEqual(2, budgeted.calls_started)
        self.assertEqual(2, counted.complete_calls)
        self.assertEqual(2, delegate.calls)

    def test_provider_failure_is_not_retried_by_the_evaluation_wrapper(self) -> None:
        class FailingDelegate:
            def __init__(self) -> None:
                self.calls = 0

            def complete(self, prompt: str) -> str:
                self.calls += 1
                raise ModelClientError("transient", "provider unavailable", retryable=True)

        delegate = FailingDelegate()
        counted = CountingClient(delegate)
        client = RetryingModelClient(
            RequestBudgetClient(counted, max_model_calls=4), max_retries=0
        )
        with self.assertRaises(ModelClientError):
            client.complete("one attempt")
        self.assertEqual(1, delegate.calls)
        self.assertEqual(1, counted.complete_calls)

    def test_classifies_current_model_response_contracts(self) -> None:
        cases = (
            ('{"items":[]}', "fault_extraction"),
            ('{"cause_dispositions":[]}', "cause_disposition"),
            ('{"structure_status":"complete","nodes":[],"gate_scopes":[]}', "structure_decomposition"),
            ('{"gate_assessments":[]}', "gate_assessment"),
        )
        for response, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(expected, classify_response_stage(response))

    def test_unrecognized_response_is_not_positionally_guessed(self) -> None:
        self.assertEqual("unclassified_model_response", classify_response_stage('{"unexpected":true}'))
        self.assertEqual("unclassified_model_response", classify_response_stage("not json"))

    def test_load_sample_selects_exact_public_record_id(self) -> None:
        rows = [
            {"sample_id": "A", "input_text": "first"},
            {"sample_id": "B", "input_text": "second"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            self.assertEqual("second", load_sample(path, "B")["input_text"])
            with self.assertRaises(ValueError):
                load_sample(path, "missing")

    def test_text_reference_check_detects_wrong_offsets_and_duplicate_quotes(self) -> None:
        result = check_text_references(
            [
                {"citation_id": "ok", "quote": "fault", "start": 0, "end": 5},
                {"citation_id": "bad-offset", "quote": "fault", "start": 1, "end": 6},
            ],
            "fault fault",
        )
        self.assertFalse(result["all_offsets_exact"])
        self.assertFalse(result["all_quotes_unique"])
        self.assertEqual(3, len(result["failures"]))

    def test_evidence_integrity_reports_extraction_even_without_tree(self) -> None:
        result = evidence_integrity(
            {
                "extraction": {"evidence_spans": [{"citation_id": "e1", "quote": "Fault", "start": 0, "end": 5}]},
                "outcomes": [{"status": "failed", "tree": None}],
            },
            "Fault text",
        )
        self.assertTrue(result["extraction"]["all_offsets_exact"])
        self.assertIsNone(result["extraction"]["all_quotes_unique"])
        self.assertFalse(result["candidate_tree_available"])
        self.assertFalse(result["cause_dispositions_available"])

    def test_evidence_integrity_checks_cause_disposition_ledger_separately(self) -> None:
        result = evidence_integrity(
            {
                "extraction": {"evidence_spans": []},
                "outcomes": [{"tree": {
                    "nodes": [],
                    "gate_assessments": [],
                    "relations": [],
                    "cause_dispositions": [
                        {"disposition": "fta_event_candidate", "evidence": [
                            {"citation_id": "unique", "quote": "Cause", "start": 0, "end": 5}
                        ]},
                        {"disposition": "unresolved", "evidence": []},
                    ],
                }}],
            },
            "Cause text",
        )
        self.assertEqual(2, result["cause_dispositions"]["disposition_count"])
        self.assertEqual(1, result["cause_dispositions"]["reference_count"])
        self.assertTrue(result["cause_dispositions"]["all_offsets_exact"])
        self.assertTrue(result["cause_dispositions"]["all_quotes_unique"])
        self.assertEqual(1, result["cause_dispositions"]["unresolved_without_evidence_count"])

    def test_repeated_extraction_quotes_are_offset_checked_not_rejected(self) -> None:
        result = evidence_integrity(
            {
                "extraction": {
                    "evidence_spans": [
                        {"quote": "fault", "start": 0, "end": 5},
                        {"quote": "fault", "start": 6, "end": 11},
                    ]
                },
                "outcomes": [{"status": "failed", "tree": None}],
            },
            "fault fault",
        )
        self.assertTrue(result["extraction"]["all_offsets_exact"])
        self.assertFalse(result["extraction"]["quote_uniqueness_required"])
        self.assertEqual(2, result["extraction"]["non_unique_source_quote_count"])

    def test_artifact_stage_trace_comes_from_response_contract(self) -> None:
        artifact = build_artifact(
            {"sample_id": "SAMPLE", "input_text": "Fault", "provenance": {}},
            {
                "extraction": {"status": "success", "records": [], "evidence_spans": []},
                "outcomes": [{"status": "failed", "tree": None, "diagnostics": []}],
            },
            [
                '{"items":[]}',
                '{"cause_dispositions":[]}',
                '{"structure_status":"unresolved","nodes":[],"gate_scopes":[]}',
            ],
            3,
        )
        self.assertEqual(
            ["fault_extraction", "cause_disposition", "structure_decomposition"],
            [item["stage"] for item in artifact["model_stage_responses"]],
        )
        self.assertFalse(artifact["fta_ready"])
        self.assertFalse(artifact["production_ready"])
        self.assertEqual("fta-cause-disposition-v5", artifact["prompt_versions"]["cause_disposition"])
        self.assertEqual(4, artifact["request_budget"]["max_model_calls"])
        self.assertEqual(0, artifact["model"]["outer_max_retries"])
        self.assertEqual(0, artifact["model"]["sdk_max_retries"])

    def test_artifact_separates_raw_proposal_from_host_normalized_dispositions(self) -> None:
        response = json.dumps({
            "cause_dispositions": [
                {"fta_disposition": "fta_event_candidate"},
                {"fta_disposition": "fta_event_candidate"},
                {"fta_disposition": "relation_only"},
            ]
        })
        payload = {
            "extraction": {"status": "success", "records": [], "evidence_spans": []},
            "outcomes": [{
                "status": "blocked",
                "tree": {"nodes": [], "gate_assessments": [], "relations": [], "cause_dispositions": [
                    {"disposition": "fta_event_candidate"},
                    {"disposition": "unresolved"},
                    {"disposition": "relation_only"},
                ]},
                "diagnostics": [],
            }],
        }
        artifact = build_artifact(
            {"sample_id": "SAMPLE", "input_text": "Fault", "provenance": {}},
            payload,
            [response],
            1,
        )
        self.assertEqual(
            {"fta_event_candidate": 1, "relation_only": 1, "unresolved": 1},
            artifact["cause_disposition_counts"],
        )
        self.assertEqual(
            {"fta_event_candidate": 2, "relation_only": 1},
            artifact["model_proposed_cause_disposition_counts"],
        )

    def test_artifact_records_the_actual_input_corpus(self) -> None:
        artifact = build_artifact(
            {"sample_id": "SAMPLE", "input_text": "Fault", "provenance": {}},
            {
                "extraction": {"status": "success", "records": [], "evidence_spans": []},
                "outcomes": [{"status": "failed", "tree": None, "diagnostics": []}],
            },
            [],
            0,
            dataset_id="siemens_s210_public_fault_corpus_v1",
        )
        self.assertEqual("siemens_s210_public_fault_corpus_v1", artifact["source"]["dataset"])

    def test_artifact_preserves_pdf_provenance_using_corpus_field_names(self) -> None:
        artifact = build_artifact(
            {
                "sample_id": "SAMPLE",
                "input_text": "Fault",
                "provenance": {
                    "source_pdf": "manual.pdf",
                    "source_sha256": "a" * 64,
                    "section": "Faults",
                    "source_offset_start": 10,
                    "source_offset_end": 15,
                },
            },
            {
                "extraction": {"status": "success", "records": [], "evidence_spans": []},
                "outcomes": [{"status": "failed", "tree": None, "diagnostics": []}],
            },
            [],
            0,
            dataset_id="corpus",
        )
        self.assertEqual("manual.pdf", artifact["source"]["source_pdf"])
        self.assertEqual("a" * 64, artifact["source"]["source_document_sha256"])
        self.assertEqual("Faults", artifact["source"]["source_section"])
        self.assertEqual(10, artifact["source"]["source_offset_start"])
        self.assertEqual(15, artifact["source"]["source_offset_end"])

    def test_offline_revalidation_checks_source_hash_and_relabels_stages(self) -> None:
        sample = {"sample_id": "SAMPLE", "input_text": "Fault text", "provenance": {}}
        payload = {
            "extraction": {
                "status": "success",
                "records": [],
                "evidence_spans": [
                    {"quote": "Fault", "start": 0, "end": 5},
                    {"quote": "Fault", "start": 0, "end": 5},
                ],
            },
            "outcomes": [{"status": "failed", "tree": None, "diagnostics": []}],
        }
        artifact = build_artifact(sample, payload, ['{"items":[]}'], 1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus_path = root / "corpus.jsonl"
            corpus_path.write_text(json.dumps(sample), encoding="utf-8")
            input_path = root / "input.json"
            input_path.write_text(json.dumps(artifact), encoding="utf-8")
            result = revalidate_existing_artifact(input_path, corpus_path, root / "checked.json")
            self.assertEqual("v1.1", result["artifact_version"])
            self.assertEqual("fault_extraction", result["model_stage_responses"][0]["stage"])
            self.assertTrue(result["evidence_integrity"]["extraction"]["all_offsets_exact"])
            self.assertIsNone(result["evidence_integrity"]["extraction"]["all_quotes_unique"])
            self.assertEqual("corpus", result["source"]["dataset"])

    def test_offline_revalidation_recomputes_effective_disposition_counts(self) -> None:
        sample = {"sample_id": "SAMPLE", "input_text": "Fault text", "provenance": {}}
        response = json.dumps({"cause_dispositions": [
            {"fta_disposition": "fta_event_candidate"},
            {"fta_disposition": "fta_event_candidate"},
            {"fta_disposition": "relation_only"},
        ]})
        payload = {
            "extraction": {"status": "success", "records": [], "evidence_spans": []},
            "outcomes": [{"status": "blocked", "tree": {
                "nodes": [], "gate_assessments": [], "relations": [],
                "cause_dispositions": [
                    {"disposition": "fta_event_candidate"},
                    {"disposition": "unresolved"},
                    {"disposition": "relation_only"},
                ],
            }, "diagnostics": []}],
        }
        artifact = build_artifact(sample, payload, [response], 1)
        artifact["cause_disposition_counts"] = {"fta_event_candidate": 2, "relation_only": 1}
        artifact.pop("model_proposed_cause_disposition_counts")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus_path = root / "corpus.jsonl"
            corpus_path.write_text(json.dumps(sample), encoding="utf-8")
            input_path = root / "input.json"
            input_path.write_text(json.dumps(artifact), encoding="utf-8")
            result = revalidate_existing_artifact(input_path, corpus_path, root / "checked.json")
        self.assertEqual(
            {"fta_event_candidate": 1, "relation_only": 1, "unresolved": 1},
            result["cause_disposition_counts"],
        )
        self.assertEqual(
            {"fta_event_candidate": 2, "relation_only": 1},
            result["model_proposed_cause_disposition_counts"],
        )


if __name__ == "__main__":
    unittest.main()
