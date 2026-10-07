import json
from hashlib import sha256
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.candidate_fta_contract import (
    CandidateFtaNode,
    CandidateFtaOutcomeStatus,
    CandidateFtaStatus,
    CandidateFtaTree,
)
from contracts.evidence_locator_review_contract import (
    EvidenceLocatorSpan,
    EvidenceLocatorTargetField,
    EvidenceOccurrenceLocatorReview,
)
from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from core.model_client import ModelClientError
from core.model_client import CallableModelClient
from extraction.text_extraction_adapter import TextExtractionAdapter
from fta.candidate_fta_application_service import CandidateFtaApplicationService
from fta.candidate_fta_extraction_service import (
    CandidateFtaExtractionService,
)
from fta.gate_confidence_policy import GateConfidencePolicy


class CandidateFtaApplicationServiceTests(unittest.TestCase):
    SOURCE = (
        "A01631 SI P1: motor holding brake/SBC configuration not practical\n"
        "Cause: A configuration of motor holding brake and SBC was detected that is not practical.\n"
        "The following configurations can result in this message:\n"
        '- "No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1).\n'
        "Remedy: Check the parameterization of the motor holding brake and SBC and correct."
    )
    DESCRIPTION = "motor holding brake/SBC configuration not practical"
    CAUSES = (
        "A configuration of motor holding brake and SBC was detected that is not practical.",
        "No motor holding brake available and SBC enabled.",
    )
    CAUSE_QUOTES = (
        CAUSES[0],
        'No motor holding brake available" (p1215 = 0) and "SBC" enabled',
    )
    NO_BRAKE = '"No motor holding brake available" (p1215 = 0)'
    SBC_ENABLED = '"SBC" enabled (p9602 = 1)'
    GATE_QUOTE = "The following configurations can result in this message:"
    LOCAL_SCOPE = f"{CAUSES[0]}\n{GATE_QUOTE}\n- {NO_BRAKE} and {SBC_ENABLED}."

    class StubExtractor:
        def __init__(self, result):
            self.result = result
            self.calls = []

        def extract(self, text):
            self.calls.append(text)
            return self.result

    def _extraction(self):
        record = FaultRecord(
            fault_code="A01631",
            description=self.DESCRIPTION,
            causes=self.CAUSES,
            parameters=("p1215", "p9602"),
        )
        spans = []
        for field, quote, value_index in (
            (EvidenceField.DESCRIPTION, self.DESCRIPTION, None),
            (EvidenceField.CAUSE, self.CAUSE_QUOTES[0], 0),
            (EvidenceField.CAUSE, self.CAUSE_QUOTES[1], 1),
        ):
            start = self.SOURCE.index(quote)
            spans.append(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=field,
                    source_id="input_text",
                    quote=quote,
                    start=start,
                    end=start + len(quote),
                    value_index=value_index,
                )
            )
        return ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=tuple(spans),
        ), record

    def _model_response(self, record):
        return json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "configuration_group",
                        "node_type": "intermediate_event_candidate",
                        "text": "Incompatible motor holding brake/SBC configuration",
                        "source_cause_indices": [0, 1],
                        "evidence_quote": self.CAUSES[0],
                    },
                    {
                        "node_id": "no_brake",
                        "node_type": "cause_candidate",
                        "text": "No motor holding brake available",
                        "source_cause_indices": [1],
                        "evidence_quote": self.NO_BRAKE,
                    },
                    {
                        "node_id": "sbc_enabled",
                        "node_type": "cause_candidate",
                        "text": "SBC enabled",
                        "source_cause_indices": [1],
                        "evidence_quote": self.SBC_ENABLED,
                    },
                ],
                "gate_assessments": [
                    {
                        "gate_id": "configuration_gate",
                        "output_node_id": "configuration_group",
                        "child_node_ids": ["no_brake", "sbc_enabled"],
                        "scope_type": "configuration_group",
                        "gate_probabilities": {"AND": 0.92, "OR": 0.03, "unknown": 0.05},
                        "scope_quote": self.LOCAL_SCOPE,
                        "gate_evidence_quote": "- " + self.NO_BRAKE + " and " + self.SBC_ENABLED + ".",
                        "cause_set_complete": True,
                        "cause_set_leaf_normalized": True,
                        "reason": "The configuration conditions are joined by and.",
                    },
                    {
                        "gate_id": "fault_event_gate",
                        "output_node_id": "__top_event__",
                        "child_node_ids": ["configuration_group"],
                        "scope_type": "fault_event_root",
                        "gate_probabilities": {"AND": 0.04, "OR": 0.06, "unknown": 0.90},
                        "scope_quote": self.SOURCE,
                        "gate_evidence_quote": "",
                        "cause_set_complete": False,
                        "cause_set_leaf_normalized": False,
                        "reason": "This does not prove an exhaustive root cause set.",
                    },
                ],
                "relations": [
                    {
                        "source_node_id": "configuration_group",
                        "target_node_id": "__top_event__",
                        "relation_type": "may_cause",
                        "relation_scope_quote": self.SOURCE[: self.SOURCE.index("Remedy:")],
                        "evidence_quote": self.GATE_QUOTE,
                    }
                ],
                "cause_dispositions": [
                    {
                        "source_cause_index": 0,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": self.CAUSE_QUOTES[0],
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "The manual gives this condition as a possible cause.",
                    },
                    {
                        "source_cause_index": 1,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": self.CAUSE_QUOTES[1],
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "The manual lists this configuration as a possible cause.",
                    },
                ],
                "cause_set_complete": True,
                "reason": "The manual states these configurations can lead to this message.",
            },
            ensure_ascii=False,
        )

    def _candidate_responses(self, record):
        full = json.loads(self._model_response(record))
        assessments = full.get("gate_assessments", [])
        structure = {
            "structure_status": "complete",
            "nodes": full.get("nodes", []),
            "gate_scopes": [
                {
                    key: gate[key]
                    for key in (
                        "gate_id",
                        "output_node_id",
                        "child_node_ids",
                        "scope_type",
                        "scope_quote",
                        "cause_set_complete",
                        "cause_set_leaf_normalized",
                        "reason",
                    )
                    if key in gate
                }
                for gate in assessments
            ],
            "unresolved_cause_indices": [],
            "reason": full.get("reason", ""),
        }
        gate_assessment = {
            "gate_assessments": [
                {
                    "gate_id": gate["gate_id"],
                    "gate_probabilities": gate.get("gate_probabilities"),
                    "gate_evidence_quote": gate.get("gate_evidence_quote", ""),
                    "reason": gate.get("reason", ""),
                }
                for gate in assessments
            ],
            "relations": full.get("relations", []),
            "reason": full.get("reason", ""),
        }
        return [
            json.dumps(
                {"cause_dispositions": full["cause_dispositions"]},
                ensure_ascii=False,
            ),
            json.dumps(structure, ensure_ascii=False),
            json.dumps(gate_assessment, ensure_ascii=False),
        ]

    def _candidate_client(self, record):
        responses = iter(self._candidate_responses(record))

        class SequenceClient:
            def complete(_self, _prompt):
                return next(responses)

        return SequenceClient()

    def _candidate_service(self, client):
        return CandidateFtaExtractionService(
            client,
            GateConfidencePolicy(
                policy_id="test-provisional-policy",
                minimum_probability=0.80,
                minimum_margin=0.20,
            ),
        )

    def test_original_s210_text_builds_local_and_edge_and_unknown_root_preview(self):
        extraction, record = self._extraction()
        extractor = self.StubExtractor(extraction)
        service = CandidateFtaApplicationService(
            extractor,
            self._candidate_service(
                self._candidate_client(record)
            ),
        )

        result = service.generate(self.SOURCE)

        self.assertEqual([self.SOURCE], extractor.calls)
        self.assertIs(result.extraction, extraction)
        self.assertEqual(CandidateFtaOutcomeStatus.PROPOSED, result.outcomes[0].status)
        tree = result.outcomes[0].tree
        gates = {gate.scope_type: gate for gate in tree.gate_assessments}
        self.assertEqual("AND", gates["configuration_group"].gate)
        self.assertEqual("unknown", gates["fault_event_root"].gate)
        self.assertEqual("may_cause", tree.relations[0].relation_type)
        self.assertFalse(tree.fta_ready)
        payload = result.to_payload()
        self.assertEqual("v3", payload["artifact_version"])
        self.assertEqual(2, len(payload["extraction"]["records"][0]["causes"]))
        self.assertEqual(3, len(payload["extraction"]["evidence_spans"]))
        json.dumps(payload, ensure_ascii=False)

    def test_retry_uses_retained_extraction_and_only_retries_selected_record(self):
        extraction, record = self._extraction()
        extractor = self.StubExtractor(extraction)

        class RetryOnce:
            def __init__(self):
                self.calls = 0
                self.responses = iter(self._responses())

            def _responses(inner_self):
                return self._candidate_responses(record)

            def complete(inner_self, _prompt):
                inner_self.calls += 1
                if inner_self.calls == 1:
                    raise ModelClientError("provider_timeout", "try again", retryable=True)
                return next(inner_self.responses)

        model = RetryOnce()
        service = CandidateFtaApplicationService(
            extractor,
            self._candidate_service(model),
        )
        first = service.generate(self.SOURCE)
        retried = service.retry_records(
            first,
            self.SOURCE,
            (record.record_id,),
        )

        self.assertEqual(CandidateFtaOutcomeStatus.FAILED, first.outcomes[0].status)
        self.assertTrue(first.outcomes[0].diagnostics[0].retryable)
        self.assertIs(retried.extraction, extraction)
        self.assertEqual(CandidateFtaOutcomeStatus.PROPOSED, retried.outcomes[0].status)
        self.assertEqual("unknown", next(
            gate.gate for gate in retried.outcomes[0].tree.gate_assessments
            if gate.scope_type == "fault_event_root"
        ))
        self.assertEqual(1, len(extractor.calls))
        self.assertEqual(4, model.calls)

    def test_one_record_provider_error_does_not_discard_other_record_outcome(self):
        extraction, first = self._extraction()
        second = FaultRecord(fault_code="A00002", description="Second event", causes=("Cause one", "Cause two"))
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(first, second),
            evidence_spans=extraction.evidence_spans,
        )

        class PerRecordProposer:
            def __init__(inner_self):
                inner_self.first_record_calls = 0

            def propose(inner_self, current, record_id, _source, locator_reviews=()):
                if record_id == first.record_id:
                    inner_self.first_record_calls += 1
                    if inner_self.first_record_calls == 1:
                        raise ModelClientError("provider_timeout", "temporary", retryable=True)
                return CandidateFtaTree(
                    extraction_result_id=current.result_id,
                    record_id=record_id,
                    fault_code=first.fault_code if record_id == first.record_id else "A00002",
                    source_text_sha256=sha256(self.SOURCE.encode("utf-8")).hexdigest(),
                    top_event_id=f"event:{record_id}",
                    nodes=(CandidateFtaNode(
                        f"event:{record_id}",
                        "top_event_candidate",
                        "First event" if record_id == first.record_id else "Second event",
                    ),),
                    status=CandidateFtaStatus.BLOCKED,
                    blockers=("no_gate_evidence",),
                )

        proposer = PerRecordProposer()
        service = CandidateFtaApplicationService(self.StubExtractor(extraction), proposer)
        result = service.generate(self.SOURCE)
        retry = service.retry_records(result, self.SOURCE, (first.record_id,))

        self.assertEqual(2, len(result.outcomes))
        self.assertEqual(CandidateFtaOutcomeStatus.FAILED, result.outcomes[0].status)
        self.assertEqual(CandidateFtaOutcomeStatus.BLOCKED, result.outcomes[1].status)
        self.assertIs(result.extraction, extraction)
        self.assertEqual(CandidateFtaOutcomeStatus.BLOCKED, retry.outcomes[0].status)
        self.assertEqual(result.outcomes[1], retry.outcomes[1])
        self.assertEqual(2, proposer.first_record_calls)

    def test_failed_extraction_is_preserved_without_candidate_calls(self):
        extraction = ExtractionResult(
            status=ExtractionStatus.FAILED,
            diagnostics=(ExtractionDiagnostic("extract_failed", "provider down", "provider", True),),
        )
        extractor = self.StubExtractor(extraction)

        class MustNotPropose:
            def propose(self, *_args):
                raise AssertionError("there are no records to propose")

        result = CandidateFtaApplicationService(extractor, MustNotPropose()).generate(self.SOURCE)

        self.assertIs(result.extraction, extraction)
        self.assertEqual((), result.outcomes)
        self.assertEqual("failed", result.to_payload()["extraction"]["status"])

    def test_retry_rejects_unknown_record_id(self):
        extraction, record = self._extraction()
        previous_service = CandidateFtaApplicationService(
            self.StubExtractor(extraction),
            self._candidate_service(
                self._candidate_client(record)
            ),
        )
        previous = previous_service.generate(self.SOURCE)

        class NoOpProposer:
            def propose(self, *_args):
                raise AssertionError("propose should not run for an unknown record")

        service = CandidateFtaApplicationService(self.StubExtractor(extraction), NoOpProposer())
        with self.assertRaises(ValueError):
            service.retry_records(previous, self.SOURCE, ("not-in-extraction",))

    def test_explicit_locator_review_is_forwarded_to_internal_candidate_service(self):
        extraction, record = self._extraction()
        quote = self.CAUSE_QUOTES[0]
        start = self.SOURCE.index(quote)
        span = EvidenceLocatorSpan(quote, start, start + len(quote))
        review = EvidenceOccurrenceLocatorReview(
            review_id="app-service-locator-review",
            extraction_result_id=extraction.result_id,
            record_id=record.record_id,
            source_text_sha256=sha256(self.SOURCE.encode("utf-8")).hexdigest(),
            target_field=EvidenceLocatorTargetField.CAUSE,
            value_index=0,
            selected_occurrence=span,
            scope=span,
            reviewer_provenance="user_authorized_ai_locator_review",
            reviewer_is_human_expert=False,
            rationale="Offline fixture confirms the exact cause occurrence.",
        )

        class CapturingProposer:
            received_reviews = ()

            def propose(inner_self, current, record_id, _source, locator_reviews=()):
                inner_self.received_reviews = locator_reviews
                return CandidateFtaTree(
                    extraction_result_id=current.result_id,
                    record_id=record_id,
                    fault_code=record.fault_code,
                    source_text_sha256=sha256(self.SOURCE.encode("utf-8")).hexdigest(),
                    top_event_id=f"event:{record_id}",
                    nodes=(CandidateFtaNode(
                        f"event:{record_id}",
                        "top_event_candidate",
                        record.description,
                    ),),
                    locator_reviews=locator_reviews,
                    status=CandidateFtaStatus.BLOCKED,
                    blockers=("offline_fixture_blocked",),
                )

        proposer = CapturingProposer()
        result = CandidateFtaApplicationService(
            self.StubExtractor(extraction), proposer
        ).propose_from_extraction(extraction, self.SOURCE, (review,))

        self.assertEqual((review,), proposer.received_reviews)
        self.assertEqual((review,), result.outcomes[0].tree.locator_reviews)
        self.assertFalse(
            result.outcomes[0].tree.to_payload()["locator_reviews"][0]["formal_gold"]
        )

    def test_retry_rejects_source_text_different_from_retained_extraction(self):
        extraction, record = self._extraction()
        service = CandidateFtaApplicationService(
            self.StubExtractor(extraction),
            self._candidate_service(
                self._candidate_client(record)
            ),
        )
        previous = service.generate(self.SOURCE)

        with self.assertRaisesRegex(ValueError, "does not match"):
            service.retry_records(previous, self.SOURCE + " changed", (record.record_id,))

    def test_actual_text_extraction_adapter_feeds_candidate_fta_from_raw_source(self):
        extraction_response = json.dumps(
            {
                "items": [
                    {
                        "fault_code": "A01631",
                        "description": self.DESCRIPTION,
                        "component": "SI",
                        "causes": [
                            self.CAUSES[0],
                            self.CAUSE_QUOTES[1],
                        ],
                        "parameters": ["p1215", "p9602"],
                    }
                ]
            },
            ensure_ascii=False,
        )
        extractor = TextExtractionAdapter(
            CallableModelClient(lambda _prompt: extraction_response),
            lambda text, _index, _total: text,
        )

        def gate_completion(_prompt):
            return next(candidate_responses)

        candidate_responses = iter(self._candidate_responses(None))

        service = CandidateFtaApplicationService(
            extractor,
            self._candidate_service(CallableModelClient(gate_completion)),
        )

        result = service.generate(self.SOURCE)

        self.assertEqual(ExtractionStatus.SUCCESS, result.extraction.status)
        self.assertEqual("A01631", result.extraction.records[0].fault_code)
        self.assertTrue(
            all(span.matches(self.SOURCE) for span in result.extraction.evidence_spans)
        )
        self.assertEqual(
            CandidateFtaOutcomeStatus.PROPOSED,
            result.outcomes[0].status,
            msg=(result.outcomes[0].tree.blockers if result.outcomes[0].tree else None),
        )
        self.assertEqual("AND", result.outcomes[0].tree.gate_assessments[0].gate)


if __name__ == "__main__":
    unittest.main()
