import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from contracts.fta_cause_disposition_contract import (
    CauseDisposition,
    CauseDispositionEvidence,
    CauseDispositionReasonCode,
    CauseSemanticRole,
    FtaCauseDispositionBatch,
    FtaCauseDispositionKind,
)
from core.model_client import CallableModelClient
from fta.cause_disposition_service import (
    CAUSE_DISPOSITION_PROMPT_VERSION,
    CauseDispositionService,
    CauseDispositionValidationError,
    build_cause_disposition_prompt,
)
from extraction.text_extraction_adapter import TextExtractionAdapter


class FtaCauseDispositionTests(unittest.TestCase):
    SOURCE = (
        "F00001: Drive stopped. Cause: valve stuck. "
        "Fault-value mapping: 0 means ready. Remedy: inspect the valve."
    )
    DESCRIPTION = "Drive stopped"
    CAUSES = (
        "valve stuck",
        "0 means ready",
        "inspect the valve",
    )
    QUOTES = ("valve stuck", "0 means ready", "inspect the valve")

    def setUp(self):
        self.record = FaultRecord(
            fault_code="F00001",
            description=self.DESCRIPTION,
            causes=self.CAUSES,
        )
        spans = [
            EvidenceSpan(
                record_id=self.record.record_id,
                field=EvidenceField.DESCRIPTION,
                source_id="input_text",
                quote=self.DESCRIPTION,
                start=self.SOURCE.index(self.DESCRIPTION),
                end=self.SOURCE.index(self.DESCRIPTION) + len(self.DESCRIPTION),
            )
        ]
        spans.extend(
            EvidenceSpan(
                record_id=self.record.record_id,
                field=EvidenceField.CAUSE,
                source_id="input_text",
                quote=cause,
                start=self.SOURCE.index(cause),
                end=self.SOURCE.index(cause) + len(cause),
                value_index=index,
            )
            for index, cause in enumerate(self.CAUSES)
        )
        self.extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=tuple(spans),
        )

    @staticmethod
    def _entry(index, role, disposition, quote, reason, rationale="reviewable proposal"):
        return {
            "source_cause_index": index,
            "semantic_role": role,
            "fta_disposition": disposition,
            "evidence_quote": quote,
            "reason_code": reason,
            "rationale": rationale,
        }

    def _response(self, rows=None):
        return json.dumps(
            {"cause_dispositions": rows if rows is not None else [
                self._entry(
                    0,
                    "causal_condition",
                    "fta_event_candidate",
                    "valve stuck",
                    "direct_causal_or_condition_statement",
                ),
                self._entry(
                    1,
                    "fault_value_mode",
                    "relation_only",
                    "0 means ready",
                    "fault_value_mode_without_instance_evidence",
                ),
                self._entry(
                    2,
                    "remedy",
                    "exclude_from_tree",
                    "inspect the valve",
                    "remedy_action",
                ),
            ]},
            ensure_ascii=False,
        )

    def _service(self, response=None):
        class Client:
            def complete(_self, _prompt):
                return response if response is not None else self._response()

        return CauseDispositionService(Client())

    def test_proposes_total_indexed_ledger_and_preserves_source_text(self):
        batch = self._service().propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual((0, 1, 2), tuple(item.source_cause_index for item in batch.dispositions))
        self.assertEqual(self.CAUSES, tuple(item.source_cause_text for item in batch.dispositions))
        self.assertEqual(CauseSemanticRole.CAUSAL_CONDITION, batch.dispositions[0].semantic_role)
        self.assertEqual("fta_event_candidate", batch.dispositions[0].disposition.value)
        self.assertEqual(CauseSemanticRole.FAULT_VALUE_MODE, batch.dispositions[1].semantic_role)
        self.assertEqual("relation_only", batch.dispositions[1].disposition.value)
        self.assertEqual("exclude_from_tree", batch.dispositions[2].disposition.value)
        self.assertEqual(self.QUOTES, tuple(item.evidence[0].quote for item in batch.dispositions))
        self.assertEqual("ai_proposed", batch.to_payload()["review_status"])
        self.assertEqual("v3", batch.to_payload()["artifact_version"])

    def test_descriptive_state_can_be_retained_as_detached_observation(self):
        response = self._response([
            self._entry(
                0,
                "state",
                "detached_observation",
                self.QUOTES[0],
                "descriptive_association",
            ),
            self._entry(
                1,
                "fault_value_mode",
                "relation_only",
                self.QUOTES[1],
                "fault_value_mode_without_instance_evidence",
            ),
            self._entry(
                2,
                "remedy",
                "exclude_from_tree",
                self.QUOTES[2],
                "remedy_action",
            ),
        ])

        batch = self._service(response).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        detached = batch.dispositions[0]
        self.assertEqual(CauseSemanticRole.STATE, detached.semantic_role)
        self.assertEqual(
            FtaCauseDispositionKind.DETACHED_OBSERVATION, detached.disposition
        )
        self.assertEqual("valve stuck", detached.evidence[0].quote)

    def test_relation_only_descriptive_state_is_narrowly_normalized_by_host(self):
        response = self._response([
            self._entry(
                0,
                "state",
                "relation_only",
                self.QUOTES[0],
                "descriptive_association",
                rationale="仅记录了该状态，没有说明它导致当前故障。",
            ),
            self._entry(
                1,
                "fault_value_mode",
                "relation_only",
                self.QUOTES[1],
                "fault_value_mode_without_instance_evidence",
            ),
            self._entry(
                2,
                "remedy",
                "exclude_from_tree",
                self.QUOTES[2],
                "remedy_action",
            ),
        ])

        batch = self._service(response).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        normalized = batch.dispositions[0]
        self.assertEqual(
            FtaCauseDispositionKind.RELATION_ONLY,
            normalized.proposed_disposition,
        )
        self.assertEqual(
            FtaCauseDispositionKind.DETACHED_OBSERVATION,
            normalized.disposition,
        )
        self.assertEqual("descriptive_association", normalized.reason_code.value)
        self.assertEqual(
            "fta_cause_disposition_host_policy", normalized.provenance
        )
        self.assertEqual("valve stuck", normalized.evidence[0].quote)
        self.assertEqual(
            FtaCauseDispositionKind.RELATION_ONLY,
            batch.dispositions[1].disposition,
            "diagnostic/fault-value relation_only must not be normalized",
        )

    def test_prompt_defines_semantic_boundary_and_includes_complete_source(self):
        prompt = build_cause_disposition_prompt(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertIn("按命题语义与该段落的交际功能分类", prompt)
        self.assertIn("必须把每条原因命题与 payload 中的 top_event 做语义比较", prompt)
        self.assertIn("只是在定义、释义、同义改写或重复 top_event", prompt)
        self.assertIn("summary_not_independent_event", prompt)
        self.assertIn("只有原文直接支持、且语义上不同于顶事件本身的上游条件/机制", prompt)
        self.assertIn("明确列为该故障可能原因的自然语言故障条件/场景", prompt)
        self.assertIn("诊断映射必须与自然语言原因区分", prompt)
        self.assertIn("detached_observation", prompt)
        self.assertIn("不得连接到顶事件，也不得参与 AND/OR", prompt)
        self.assertIn("不得仅凭这条映射自动连到当前顶事件", prompt)
        self.assertIn("映射之外另有直接证据", prompt)
        self.assertIn("不要仅因包含状态和因果子句就判 mixed_unresolved", prompt)
        self.assertIn(CAUSE_DISPOSITION_PROMPT_VERSION, prompt)
        self.assertEqual("fta-cause-disposition-v6", CAUSE_DISPOSITION_PROMPT_VERSION)
        self.assertIn("unresolved", prompt)
        self.assertIn("source_cause_index", prompt)
        self.assertIn(self.SOURCE, prompt)

    def test_top_event_restatement_can_be_recorded_as_summary_not_tree_event(self):
        source = (
            "F01681: Incorrect parameter value. Cause: "
            "The parameter cannot be parameterized with this value."
        )
        record = FaultRecord(
            fault_code="F01681",
            description="Incorrect parameter value",
            causes=("The parameter cannot be parameterized with this value.",),
        )
        description_start = source.index(record.description)
        cause_start = source.index(record.causes[0])
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=record.description,
                    start=description_start,
                    end=description_start + len(record.description),
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=record.causes[0],
                    start=cause_start,
                    end=cause_start + len(record.causes[0]),
                    value_index=0,
                ),
            ),
        )
        row = self._entry(
            0,
            "causal_summary",
            "relation_only",
            record.causes[0],
            "summary_not_independent_event",
            rationale="该句只是对顶事件的释义，没有给出独立上游机制。",
        )

        batch = self._service(self._response(rows=[row])).propose(
            extraction, record.record_id, source
        )

        self.assertEqual(CauseSemanticRole.CAUSAL_SUMMARY, batch.dispositions[0].semantic_role)
        self.assertEqual(FtaCauseDispositionKind.RELATION_ONLY, batch.dispositions[0].disposition)
        self.assertEqual(
            CauseDispositionReasonCode.SUMMARY_NOT_INDEPENDENT_EVENT,
            batch.dispositions[0].reason_code,
        )
        self.assertEqual(record.causes[0], batch.dispositions[0].evidence[0].quote)

    def test_host_downgrades_top_event_summary_mislabelled_as_tree_candidate(self):
        source = (
            "F01681: Incorrect parameter value. Cause: "
            "The parameter cannot be parameterized with this value."
        )
        record = FaultRecord(
            fault_code="F01681",
            description="Incorrect parameter value",
            causes=("The parameter cannot be parameterized with this value.",),
        )
        cause_start = source.index(record.causes[0])
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=record.causes[0],
                    start=cause_start,
                    end=cause_start + len(record.causes[0]),
                    value_index=0,
                ),
            ),
        )
        row = self._entry(
            0,
            "causal_summary",
            "fta_event_candidate",
            record.causes[0],
            "direct_causal_or_condition_statement",
        )

        batch = self._service(self._response(rows=[row])).propose(
            extraction, record.record_id, source
        )

        item = batch.dispositions[0]
        self.assertEqual(FtaCauseDispositionKind.FTA_EVENT_CANDIDATE, item.proposed_disposition)
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(CauseDispositionReasonCode.SEMANTIC_DISPOSITION_CONFLICT, item.reason_code)

    def test_non_unique_evidence_forces_unresolved_without_guessing_location(self):
        repeated_source = self.SOURCE + " Repeated: 0 means ready."
        response = self._response()
        batch = self._service(response).propose(
            self.extraction, self.record.record_id, repeated_source
        )

        item = batch.dispositions[1]
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
            item.reason_code,
        )
        self.assertEqual((), item.evidence)

    def test_disposition_quote_cannot_replace_missing_extraction_cause_evidence(self):
        extraction_without_cause_spans = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=tuple(
                span
                for span in self.extraction.evidence_spans
                if span.field is not EvidenceField.CAUSE
            ),
        )

        batch = self._service().propose(
            extraction_without_cause_spans,
            self.record.record_id,
            self.SOURCE,
        )

        item = batch.dispositions[0]
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
            item.reason_code,
        )
        self.assertEqual((), item.evidence)
        self.assertIn("抽取阶段", item.rationale)

    def test_multiple_extraction_cause_spans_require_manual_location(self):
        repeated_source = self.SOURCE + " Repeated: valve stuck."
        extraction_with_repeated_cause = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=tuple(
                span
                for span in self.extraction.evidence_spans
                if span.field is not EvidenceField.CAUSE
            )
            + (
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote="valve stuck",
                    start=repeated_source.index("valve stuck"),
                    end=repeated_source.index("valve stuck") + len("valve stuck"),
                    value_index=0,
                ),
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote="valve stuck",
                    start=repeated_source.rindex("valve stuck"),
                    end=repeated_source.rindex("valve stuck") + len("valve stuck"),
                    value_index=0,
                ),
                *(
                    span
                    for span in self.extraction.evidence_spans
                    if span.field is EvidenceField.CAUSE and span.value_index != 0
                ),
            ),
        )

        batch = self._service().propose(
            extraction_with_repeated_cause,
            self.record.record_id,
            repeated_source,
        )

        item = batch.dispositions[0]
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
            item.reason_code,
        )
        self.assertEqual((), item.evidence)

    def test_f30021_possible_cause_and_fault_value_duplicate_remain_unresolved(self):
        source = (
            "F30021 Drive: ground fault\nReaction: OFF2\n"
            "Acknowledge: IMMEDIATELY\n"
            "496 Operating Instructions, 01/2019, A5E41702836B AC\n"
            "Cause: The drive has detected a ground fault.\nPossible causes:\n"
            "- ground fault in the power cables.\n- ground fault at the motor.\n"
            "- when the brake closes, this causes the hardware DC current monitoring to respond.\n"
            "- short-circuit at the braking resistor.\n"
            "Fault value (r0949, interpret decimal):\n0:\n"
            "- the hardware DC current monitoring has responded.\n"
            "- short-circuit at the braking resistor.\n> 0:\n"
            "Absolute value summation current amplitude.\n"
            "Remedy: - check the power cable connections.\n"
        )
        repeated_cause = "short-circuit at the braking resistor"
        extraction_payload = json.dumps({
            "items": [{
                "fault_code": "F30021",
                "description": "ground fault",
                "component": "Drive",
                "causes": [
                    "ground fault in the power cables",
                    "ground fault at the motor",
                    "when the brake closes, this causes the hardware DC current monitoring to respond",
                    repeated_cause,
                    "the hardware DC current monitoring has responded",
                ],
                "parameters": ["r0949"],
            }]
        })
        extractor = TextExtractionAdapter(
            CallableModelClient(lambda _prompt: extraction_payload),
            lambda chunk, _index, _total: chunk,
        )
        extraction = extractor.extract(source)
        record = extraction.records[0]
        repeated_spans = [
            span for span in extraction.evidence_spans
            if span.field is EvidenceField.CAUSE and span.value_index == 3
        ]
        self.assertEqual(2, len(repeated_spans))
        self.assertEqual(
            [source.index(repeated_cause), source.rindex(repeated_cause)],
            [span.start for span in repeated_spans],
        )

        proposed = self._entry(
            3,
            "causal_condition",
            "fta_event_candidate",
            repeated_cause,
            "direct_causal_or_condition_statement",
        )
        service = CauseDispositionService(
            CallableModelClient(lambda _prompt: self._response(rows=[proposed]))
        )
        batch = service.propose(extraction, record.record_id, source)

        disposition = batch.dispositions[3]
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, disposition.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
            disposition.reason_code,
        )
        self.assertEqual((), disposition.evidence)
        self.assertIn("多重/歧义", disposition.rationale)

    def test_missing_index_is_retained_as_unresolved(self):
        batch = self._service(self._response(rows=[])).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual(3, len(batch.dispositions))
        self.assertTrue(
            all(item.disposition is FtaCauseDispositionKind.UNRESOLVED for item in batch.dispositions)
        )
        self.assertTrue(
            all(item.reason_code is CauseDispositionReasonCode.CLASSIFICATION_MISSING for item in batch.dispositions)
        )

    def test_duplicate_model_indexes_become_explicit_unresolved(self):
        row = self._entry(
            0,
            "causal_condition",
            "fta_event_candidate",
            "valve stuck",
            "direct_causal_or_condition_statement",
        )
        batch = self._service(self._response(rows=[row, dict(row)])).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual(
            CauseDispositionReasonCode.CLASSIFICATION_MISSING,
            batch.dispositions[0].reason_code,
        )
        self.assertEqual(
            FtaCauseDispositionKind.UNRESOLVED,
            batch.dispositions[0].disposition,
        )

    def test_role_disposition_conflict_is_downgraded_not_sent_to_tree(self):
        row = self._entry(
            0,
            "remedy",
            "fta_event_candidate",
            "valve stuck",
            "direct_causal_or_condition_statement",
        )
        batch = self._service(self._response(rows=[row])).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        item = batch.dispositions[0]
        self.assertEqual(FtaCauseDispositionKind.FTA_EVENT_CANDIDATE, item.proposed_disposition)
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.SEMANTIC_DISPOSITION_CONFLICT,
            item.reason_code,
        )

    def test_diagnostic_mapping_cannot_be_promoted_to_candidate_edge(self):
        row = self._entry(
            1,
            "diagnostic_mapping",
            "fta_event_candidate",
            "0 means ready",
            "direct_causal_or_condition_statement",
        )
        batch = self._service(self._response(rows=[row])).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        item = batch.dispositions[1]
        self.assertEqual(FtaCauseDispositionKind.FTA_EVENT_CANDIDATE, item.proposed_disposition)
        self.assertEqual(FtaCauseDispositionKind.UNRESOLVED, item.disposition)
        self.assertEqual(
            CauseDispositionReasonCode.SEMANTIC_DISPOSITION_CONFLICT,
            item.reason_code,
        )
        self.assertIn("角色与建树处置不相容", item.rationale)

    def test_out_of_range_index_fails_validation_instead_of_being_ignored(self):
        row = self._entry(
            3,
            "causal_condition",
            "fta_event_candidate",
            "valve stuck",
            "direct_causal_or_condition_statement",
        )
        with self.assertRaises(CauseDispositionValidationError):
            self._service(self._response(rows=[row])).propose(
                self.extraction, self.record.record_id, self.SOURCE
            )

    def test_batch_rejects_missing_or_reordered_indices(self):
        valid = self._service().propose(
            self.extraction, self.record.record_id, self.SOURCE
        )
        with self.assertRaises(ValueError):
            FtaCauseDispositionBatch(
                extraction_result_id=valid.extraction_result_id,
                record_id=valid.record_id,
                source_text_sha256=valid.source_text_sha256,
                dispositions=(valid.dispositions[1],),
            )

    def test_contract_rejects_noncausal_role_as_tree_event(self):
        evidence = CauseDispositionEvidence(
            citation_id="input_text:cause_disposition:0-10",
            source_id="input_text",
            quote="inspect it",
            start=0,
            end=10,
        )
        with self.assertRaises(ValueError):
            CauseDisposition(
                source_cause_index=0,
                source_cause_text="inspect it",
                semantic_role=CauseSemanticRole.REMEDY,
                proposed_disposition=FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                disposition=FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                reason_code=CauseDispositionReasonCode.DIRECT_CAUSAL_OR_CONDITION_STATEMENT,
                rationale="invalid combination",
                evidence=(evidence,),
            )

        with self.assertRaises(ValueError):
            CauseDisposition(
                source_cause_index=0,
                source_cause_text="The parameter cannot be parameterized with this value.",
                semantic_role=CauseSemanticRole.CAUSAL_SUMMARY,
                proposed_disposition=FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                disposition=FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                reason_code=CauseDispositionReasonCode.DIRECT_CAUSAL_OR_CONDITION_STATEMENT,
                rationale="a top-event restatement is not an independent cause",
                evidence=(evidence,),
            )


if __name__ == "__main__":
    unittest.main()
