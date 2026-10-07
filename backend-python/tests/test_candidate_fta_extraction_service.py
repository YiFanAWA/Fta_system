import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.candidate_fta_contract import (
    CandidateFtaEvidence,
    CandidateFtaGateAssessment,
    CandidateFtaStatus,
    UnknownGateReasonCode,
)
from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from core.model_client import CallableModelClient
from extraction.text_extraction_adapter import TextExtractionAdapter
from fta.candidate_fta_extraction_service import (
    CandidateFtaExtractionService,
    CandidateFtaValidationError,
)
from fta.cause_disposition_service import CauseDispositionService
from fta.gate_confidence_policy import GateConfidencePolicy


class CandidateFtaExtractionServiceTests(unittest.TestCase):
    SOURCE = "Drive stops when pump overload and fan failure occur together."
    DESCRIPTION = "Drive stops"
    CAUSES = ("pump overload", "fan failure")
    GATE_QUOTE = "pump overload and fan failure occur together"

    @staticmethod
    def _replay_extraction_response(extraction_response, source_text):
        adapter = TextExtractionAdapter(
            CallableModelClient(lambda _prompt: extraction_response),
            lambda text, _index, _total: text,
        )
        return adapter.extract(source_text)

    @staticmethod
    def _three_stage_responses(response):
        try:
            full = json.loads(response)
        except (TypeError, json.JSONDecodeError):
            return [response]
        assessments = full.get("gate_assessments", [])
        dispositions = full.get(
            "cause_dispositions",
            [
                {
                    "source_cause_index": 0,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": "pump overload",
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source names this condition.",
                },
                {
                    "source_cause_index": 1,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": "fan failure",
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source names this condition.",
                },
            ],
        )
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
            json.dumps({"cause_dispositions": dispositions}, ensure_ascii=False),
            json.dumps(structure, ensure_ascii=False),
            json.dumps(gate_assessment, ensure_ascii=False),
        ]

    def setUp(self):
        self.record = FaultRecord(description=self.DESCRIPTION, causes=self.CAUSES)
        spans = []
        for field, quote, value_index in (
            (EvidenceField.DESCRIPTION, self.DESCRIPTION, None),
            (EvidenceField.CAUSE, self.CAUSES[0], 0),
            (EvidenceField.CAUSE, self.CAUSES[1], 1),
        ):
            start = self.SOURCE.index(quote)
            spans.append(
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=field,
                    source_id="input_text",
                    quote=quote,
                    start=start,
                    end=start + len(quote),
                    value_index=value_index,
                )
            )
        self.extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=tuple(spans),
        )

    def _payload(self, probabilities=None, gate_quote=None):
        return {
            "nodes": [
                {
                    "node_id": "pump",
                    "node_type": "cause_candidate",
                    "text": "Pump overload",
                    "source_cause_indices": [0],
                    "evidence_quote": "pump overload",
                },
                {
                    "node_id": "fan",
                    "node_type": "cause_candidate",
                    "text": "Fan failure",
                    "source_cause_indices": [1],
                    "evidence_quote": "fan failure",
                },
            ],
            "gate_assessments": [
                {
                    "gate_id": "root-gate",
                    "output_node_id": "__top_event__",
                    "child_node_ids": ["pump", "fan"],
                    "scope_type": "fault_event_root",
                    "gate_probabilities": probabilities or {"AND": 0.91, "OR": 0.04, "unknown": 0.05},
                    "scope_quote": self.SOURCE,
                    "gate_evidence_quote": self.GATE_QUOTE if gate_quote is None else gate_quote,
                    "cause_set_complete": True,
                    "cause_set_leaf_normalized": True,
                    "reason": "The source states both conditions occur together.",
                }
            ],
            "relations": [
                {
                    "source_node_id": "pump",
                    "target_node_id": "__top_event__",
                    "relation_type": "causes",
                    "relation_scope_quote": self.SOURCE,
                    "evidence_quote": self.SOURCE,
                }
            ],
            "cause_set_complete": True,
            "cause_dispositions": [
                {
                    "source_cause_index": 0,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": "pump overload",
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source names this condition.",
                },
                {
                    "source_cause_index": 1,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": "fan failure",
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source names this condition.",
                },
            ],
            "reason": "A test candidate.",
        }

    def _service(self, response, policy=True):
        responses = iter(self._three_stage_responses(response))

        class Client:
            def complete(self, _prompt):
                return next(responses)

        confidence_policy = (
            GateConfidencePolicy("test-provisional", 0.75, 0.15)
            if policy
            else None
        )
        return CandidateFtaExtractionService(Client(), confidence_policy)

    def test_prompt_contains_record_identity_and_bound_source_evidence(self):
        payload = self._payload()

        class CapturingClient:
            prompts = []
            responses = iter(CandidateFtaExtractionServiceTests._three_stage_responses(
                json.dumps(payload, ensure_ascii=False)
            ))

            def complete(inner_self, prompt):
                inner_self.prompts.append(prompt)
                return next(inner_self.responses)

        service = CandidateFtaExtractionService(
            CapturingClient(), GateConfidencePolicy("test", 0.75, 0.15)
        )
        tree = service.propose(self.extraction, self.record.record_id, self.SOURCE)

        self.assertEqual(CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW, tree.status)
        self.assertEqual("AND", tree.gate_assessments[0].gate)
        self.assertEqual(2, len(tree.gate_assessments[0].child_node_ids))
        self.assertFalse(tree.fta_ready)
        self.assertEqual(3, len(CapturingClient.prompts))
        self.assertIn("逐项分类", CapturingClient.prompts[0])
        self.assertIn("只做结构分解", CapturingClient.prompts[1])
        self.assertIn("必须逐条扫描每个原因内部", CapturingClient.prompts[1])
        self.assertIn("C组的局部 scope（X、Y）", CapturingClient.prompts[1])
        self.assertIn("多个报警/观察状态在同一段落共现", CapturingClient.prompts[1])
        self.assertIn("节点证据不等于节点间关系证据", CapturingClient.prompts[1])
        self.assertIn("because", CapturingClient.prompts[1])
        self.assertIn(
            "cause 候选只是未确认输入，不因字段名就等于已验证因果",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "参数值/故障值查表是条件映射，不证明该状态已在某台设备实例中发生",
            CapturingClient.prompts[1],
        )
        self.assertIn("门型依据完整命题之间的语义关系判断", CapturingClient.prompts[2])
        self.assertIn("不要求原文出现 AND/OR", CapturingClient.prompts[2])
        self.assertIn("每条路径可各自导致该 output", CapturingClient.prompts[2])
        self.assertIn("必须共同成立/共同作用才产生同一 output", CapturingClient.prompts[2])
        self.assertIn("仅共同出现、同时记录、时间先后或原因列表不能证明 OR/AND", CapturingClient.prompts[2])
        self.assertIn("自然语言原因边界", CapturingClient.prompts[1])
        self.assertIn("可生成到顶事件的候选连接", CapturingClient.prompts[1])
        self.assertIn("这是待审核的候选边", CapturingClient.prompts[1])
        self.assertIn("诊断映射边界", CapturingClient.prompts[1])
        self.assertIn("不得仅凭映射本身生成顶事件节点连接", CapturingClient.prompts[1])
        self.assertIn("映射之外存在独立、直接的原文因果证据", CapturingClient.prompts[1])
        self.assertIn(
            "cause_set_complete 只表示：在该 scope 的原文限定范围内",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "它不表示这些事件已在某台具体设备上发生，也不要求现场参数读数",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "at least one of the following",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "才标记 false",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "此数组只能包含 fta_event_candidates 中列出的索引",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "处置账已标为 unresolved、relation_only 或 exclude_from_tree 的索引已由宿主单独记录",
            CapturingClient.prompts[1],
        )
        self.assertIn("必须保留每个命题的肯定/否定极性", CapturingClient.prompts[1])
        self.assertIn(
            "不得将\"C or D is not possible\"改写为正向叶节点\"C\"和\"D\"",
            CapturingClient.prompts[1],
        )
        self.assertIn(
            "无法保留极性或情态，则保留完整命题并标记 unresolved",
            CapturingClient.prompts[1],
        )
        self.assertIn("不得增加、删除、改名或摊平任何节点/scope", CapturingClient.prompts[2])
        self.assertIn("不得仅因原因列在", CapturingClient.prompts[2])
        self.assertIn(
            "通用 Cause 摘要或故障释义不能仅凭 Cause 标题连成顶事件的独立基本原因",
            CapturingClient.prompts[2],
        )
        self.assertIn("诊断映射（fault code/value、参数号、位号或索引到解释文本）本身不构成因果边证据", CapturingClient.prompts[2])
        self.assertIn("即使映射后的解释是自然语言，也不得仅凭该映射生成 gate child 或关系边", CapturingClient.prompts[2])

    def test_detached_observations_are_kept_as_nodes_and_never_linked(self):
        source = (
            "alarm A was logged and alarm B was logged before pump shutdown. "
            "The report does not say either alarm caused shutdown or both were required."
        )
        causes = ("alarm A was logged", "alarm B was logged")
        record = FaultRecord(description="pump shutdown", causes=causes)
        spans = [
            EvidenceSpan(
                record_id=record.record_id,
                field=EvidenceField.DESCRIPTION,
                source_id="input_text",
                quote=record.description,
                start=source.index(record.description),
                end=source.index(record.description) + len(record.description),
            )
        ]
        spans.extend(
            EvidenceSpan(
                record_id=record.record_id,
                field=EvidenceField.CAUSE,
                source_id="input_text",
                quote=cause,
                start=source.index(cause),
                end=source.index(cause) + len(cause),
                value_index=index,
            )
            for index, cause in enumerate(causes)
        )
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=tuple(spans),
        )
        response = json.dumps({
            "cause_dispositions": [
                {
                    "source_cause_index": index,
                    "semantic_role": "state",
                    "fta_disposition": "relation_only",
                    "evidence_quote": cause,
                    "reason_code": "descriptive_association",
                    "rationale": "原文只说明记录先后，不证明因果。",
                }
                for index, cause in enumerate(causes)
            ]
        }, ensure_ascii=False)

        class OneCallClient:
            call_count = 0

            def complete(self, _prompt):
                self.call_count += 1
                return response

        model_client = OneCallClient()
        tree = CandidateFtaExtractionService(model_client).propose(
            extraction, record.record_id, source
        )

        observations = [
            node for node in tree.nodes if node.node_type == "observation_candidate"
        ]
        self.assertEqual(1, model_client.call_count)
        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertEqual(causes, tuple(node.text for node in observations))
        self.assertEqual(2, len(observations))
        self.assertTrue(all(node.evidence for node in observations))
        self.assertTrue(all(
            f"node_disconnected_from_top_event:{node.node_id}" in tree.blockers
            for node in observations
        ))
        self.assertEqual((), tree.gate_assessments)
        self.assertEqual((), tree.relations)
        self.assertEqual(
            {"detached_observation"},
            {item.disposition.value for item in tree.cause_dispositions},
        )
        with self.assertRaisesRegex(ValueError, "cannot participate in gate scopes"):
            replace(
                tree,
                gate_assessments=(CandidateFtaGateAssessment(
                    gate_node_id="gate:must-not-attach-observation",
                    output_node_id=tree.top_event_id,
                    child_node_ids=(observations[0].node_id,),
                    scope_type="fault_event_root",
                    gate="unknown",
                    gate_probabilities=(("AND", 0.0), ("OR", 0.0), ("unknown", 1.0)),
                    scope_evidence=(CandidateFtaEvidence(
                        citation_id="input_text:scope:0-end",
                        source_id="input_text",
                        quote=source,
                        start=0,
                        end=len(source),
                    ),),
                    unknown_reason_code=UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE,
                ),),
            )

    def test_repeated_top_event_quote_blocks_candidate_tree(self):
        source_text = f"{self.SOURCE} {self.DESCRIPTION}"
        tree = self._service(json.dumps(self._payload())).propose(
            self.extraction,
            self.record.record_id,
            source_text,
        )

        self.assertIn("top_event_evidence_ambiguous", tree.blockers)
        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertEqual(self.DESCRIPTION, tree.nodes[0].evidence[0].quote)

    def test_unknown_confidence_is_kept_in_reviewable_preview(self):
        payload = self._payload(
            probabilities={"AND": 0.42, "OR": 0.38, "unknown": 0.20}
        )
        tree = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        gate = tree.gate_assessments[0]
        self.assertEqual("unknown", gate.gate)
        self.assertEqual(CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW, tree.status)
        self.assertIn("gate_confidence_below_threshold", gate.blockers)
        self.assertEqual(
            UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY,
            gate.unknown_reason_code,
        )
        self.assertEqual(
            UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY.value,
            tree.to_payload()["gate_assessments"][0]["unknown_reason_code"],
        )
        self.assertEqual(
            {UnknownGateReasonCode.MODEL_CONFIDENCE_BELOW_POLICY.value: 1},
            tree.to_payload()["unknown_gate_reason_counts"],
        )

    def test_unknown_gate_can_retain_exact_direct_evidence_without_selecting_gate(self):
        payload = self._payload()
        payload["gate_assessments"][0]["reason"] = (
            "The source supports an AND gate."
        )
        tree = self._service(json.dumps(payload), policy=False).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        gate = tree.gate_assessments[0]
        self.assertEqual("unknown", gate.gate)
        self.assertEqual(self.GATE_QUOTE, gate.gate_evidence[0].quote)
        self.assertEqual(
            self.GATE_QUOTE,
            self.SOURCE[gate.gate_evidence[0].start : gate.gate_evidence[0].end],
        )
        self.assertIn("gate_confidence_policy_unavailable", gate.blockers)
        self.assertEqual(
            UnknownGateReasonCode.CONFIDENCE_POLICY_UNAVAILABLE,
            gate.unknown_reason_code,
        )
        self.assertIn("model gate proposal is not accepted", gate.decision_reason)
        self.assertLess(
            gate.decision_reason.index("model gate proposal is not accepted"),
            gate.decision_reason.index("The source supports an AND gate."),
        )

    def test_repeated_gate_quote_abstains_without_blocking_evidenced_preview(self):
        payload = self._payload()
        ambiguous_quote = "Drive stops when"
        repeated_source = self.SOURCE + " Repeated: " + ambiguous_quote
        payload["gate_assessments"][0]["gate_evidence_quote"] = ambiguous_quote
        tree = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, repeated_source
        )

        gate = tree.gate_assessments[0]
        self.assertEqual("unknown", gate.gate)
        self.assertIn("gate_evidence_missing_or_ambiguous", gate.blockers)
        self.assertEqual(
            UnknownGateReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
            gate.unknown_reason_code,
        )
        self.assertFalse(gate.gate_evidence)
        self.assertIn("top_event_evidence_ambiguous", tree.blockers)
        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)

    def test_unknown_gate_without_quote_is_classified_as_no_direct_logic_evidence(self):
        payload = self._payload(gate_quote="")
        tree = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        gate = tree.gate_assessments[0]
        self.assertEqual("unknown", gate.gate)
        self.assertEqual(
            UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE,
            gate.unknown_reason_code,
        )

    def test_gate_evidence_outside_scope_gets_scope_ambiguity_reason(self):
        payload = self._payload()
        payload["gate_assessments"][0]["scope_quote"] = self.GATE_QUOTE
        payload["gate_assessments"][0]["gate_evidence_quote"] = "Drive stops when"
        tree = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        gate = tree.gate_assessments[0]
        self.assertEqual("unknown", gate.gate)
        self.assertIn("gate_evidence_outside_scope", gate.blockers)
        self.assertEqual(
            UnknownGateReasonCode.SEMANTIC_SCOPE_AMBIGUITY,
            gate.unknown_reason_code,
        )

    def test_gate_reason_code_is_required_only_for_unknown_gates(self):
        payload = self._payload(
            probabilities={"AND": 0.42, "OR": 0.38, "unknown": 0.20}
        )
        tree = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )
        gate = tree.gate_assessments[0]

        with self.assertRaisesRegex(ValueError, "unknown gate requires"):
            from dataclasses import replace

            replace(gate, unknown_reason_code=None)

        payload = self._payload()
        accepted = self._service(json.dumps(payload)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        ).gate_assessments[0]
        with self.assertRaisesRegex(ValueError, "only unknown gates"):
            from dataclasses import replace

            replace(
                accepted,
                unknown_reason_code=UnknownGateReasonCode.NO_DIRECT_LOGIC_EVIDENCE,
            )

    def test_invalid_gate_distribution_is_rejected(self):
        payload = self._payload(
            probabilities={"AND": 0.7, "OR": 0.4, "unknown": 0.1}
        )
        with self.assertRaises(CandidateFtaValidationError):
            self._service(json.dumps(payload)).propose(
                self.extraction, self.record.record_id, self.SOURCE
            )

    def test_invalid_model_json_is_rejected(self):
        with self.assertRaises(CandidateFtaValidationError):
            self._service("not-json").propose(
                self.extraction, self.record.record_id, self.SOURCE
            )

    def test_gate_assessment_must_match_every_fixed_structure_scope(self):
        responses = self._three_stage_responses(json.dumps(self._payload()))
        assessment = json.loads(responses[2])
        assessment["gate_assessments"][0]["gate_id"] = "different-scope"
        responses[2] = json.dumps(assessment)

        class Client:
            def __init__(self):
                self.responses = iter(responses)

            def complete(self, _prompt):
                return next(self.responses)

        service = CandidateFtaExtractionService(
            Client(), GateConfidencePolicy("test", 0.75, 0.15)
        )
        with self.assertRaisesRegex(CandidateFtaValidationError, "do not match structure"):
            service.propose(self.extraction, self.record.record_id, self.SOURCE)

    def test_unresolved_structure_is_blocked_not_promoted_to_a_complete_tree(self):
        responses = self._three_stage_responses(json.dumps(self._payload()))
        structure = json.loads(responses[1])
        structure["structure_status"] = "unresolved"
        structure["unresolved_cause_indices"] = [1]
        responses[1] = json.dumps(structure)

        class Client:
            def __init__(self):
                self.responses = iter(responses)

            def complete(self, _prompt):
                return next(self.responses)

        service = CandidateFtaExtractionService(
            Client(), GateConfidencePolicy("test", 0.75, 0.15)
        )
        tree = service.propose(self.extraction, self.record.record_id, self.SOURCE)

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("cause_structure_unresolved:1", tree.blockers)
        self.assertFalse(tree.fta_ready)

    def test_unresolved_cause_is_retained_and_blocks_whole_candidate_tree(self):
        responses = self._three_stage_responses(json.dumps(self._payload()))
        dispositions = json.loads(responses[0])["cause_dispositions"]
        dispositions[1].update(
            {
                "semantic_role": "mixed_unresolved",
                "fta_disposition": "unresolved",
                "evidence_quote": "",
                "reason_code": "mixed_semantics",
                "rationale": "The extracted item combines distinct propositions; keep for review.",
            }
        )
        responses[0] = json.dumps({"cause_dispositions": dispositions})

        class Client:
            def __init__(self):
                self.responses = iter(responses)

            def complete(self, _prompt):
                return next(self.responses)

        tree = CandidateFtaExtractionService(
            Client(), GateConfidencePolicy("test", 0.75, 0.15)
        ).propose(self.extraction, self.record.record_id, self.SOURCE)

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("cause_disposition_unresolved:1", tree.blockers)
        self.assertIn("cause_disposition_conflict:1", tree.blockers)
        self.assertEqual("fan failure", tree.cause_dispositions[1].source_cause_text)
        self.assertFalse(tree.fta_ready)

    def test_excluded_causes_remain_in_ledger_and_skip_structure_generation(self):
        dispositions = [
            {
                "source_cause_index": index,
                "semantic_role": "diagnostic_mapping",
                "fta_disposition": "relation_only",
                "evidence_quote": quote,
                "reason_code": "diagnostic_mapping_without_instance_evidence",
                "rationale": "This mapping is retained as reference, not an event instance.",
            }
            for index, quote in enumerate(self.CAUSES)
        ]

        class Client:
            calls = 0

            def complete(inner_self, _prompt):
                inner_self.calls += 1
                return json.dumps({"cause_dispositions": dispositions})

        client = Client()
        tree = CandidateFtaExtractionService(client).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertEqual(1, client.calls)
        self.assertEqual(2, len(tree.cause_dispositions))
        self.assertEqual(["pump overload", "fan failure"], [
            item.source_cause_text for item in tree.cause_dispositions
        ])
        self.assertEqual(("no_fta_event_candidates",), tree.blockers)
        self.assertEqual(1, len(tree.nodes))

    def test_structure_mapping_of_non_candidate_cause_is_blocked(self):
        responses = self._three_stage_responses(json.dumps(self._payload()))
        dispositions = json.loads(responses[0])["cause_dispositions"]
        dispositions[1].update(
            {
                "semantic_role": "diagnostic_mapping",
                "fta_disposition": "relation_only",
                "reason_code": "diagnostic_mapping_without_instance_evidence",
                "rationale": "This is a diagnostic mapping, not an event instance.",
            }
        )
        responses[0] = json.dumps({"cause_dispositions": dispositions})

        class Client:
            def __init__(self):
                self.responses = iter(responses)
                self.prompts = []

            def complete(inner_self, prompt):
                inner_self.prompts.append(prompt)
                return next(inner_self.responses)

        client = Client()
        tree = CandidateFtaExtractionService(
            client, GateConfidencePolicy("test", 0.75, 0.15)
        ).propose(self.extraction, self.record.record_id, self.SOURCE)
        structure_prompt_payload = json.loads(
            client.prompts[1][client.prompts[1].rfind("\n{") + 1 :]
        )

        self.assertEqual([0], [
            item["source_cause_index"]
            for item in structure_prompt_payload["fta_event_candidates"]
        ])
        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("cause_disposition_conflict:1", tree.blockers)
        self.assertFalse(tree.fta_ready)

    def test_f01681_fault_value_modes_stay_out_of_candidate_tree_and_are_audited(self):
        repository_root = ROOT.parent
        corpus_path = (
            repository_root
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_public_fault_corpus_v1.jsonl"
        )
        source_record = next(
            json.loads(line)
            for line in corpus_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["weak_record"]["fault_code"] == "F01681"
        )
        preview_path = (
            repository_root
            / "evaluation"
            / "quality_eval"
            / "runs"
            / "siemens_s210_2019_f01681_candidate_fta_polarity_and_gate_disclaimer_v5_2026-09-27.json"
        )
        prior_preview = json.loads(preview_path.read_text(encoding="utf-8"))
        extraction_response = next(
            item["responses"][0]
            for item in prior_preview["model_stage_responses"]
            if item["stage"] == "fault_extraction"
        )
        source_text = source_record["input_text"]
        extraction = self._replay_extraction_response(extraction_response, source_text)
        record = extraction.records[0]

        cause_spans = [
            span
            for span in extraction.evidence_spans
            if span.field is EvidenceField.CAUSE
        ]
        indexed_cause_spans = {span.value_index: span for span in cause_spans}
        self.assertEqual(16, len(cause_spans))
        self.assertEqual(16, len(indexed_cause_spans))
        self.assertEqual(set(range(16)), set(indexed_cause_spans))
        self.assertTrue(
            all(
                sum(span.value_index == index for span in cause_spans) == 1
                for index in range(16)
            )
        )
        self.assertEqual((376, 512), (
            indexed_cause_spans[1].start,
            indexed_cause_spans[1].end,
        ))
        self.assertTrue(all(span.matches(source_text) for span in indexed_cause_spans.values()))

        def unique_source_quote(cause):
            for size in range(len(cause), 7, -1):
                for start in range(len(cause) - size + 1):
                    quote = cause[start : start + size]
                    first = source_text.find(quote)
                    if first >= 0 and source_text.find(quote, first + 1) < 0:
                        return quote
            self.fail(f"no unique source quote available for cause: {cause}")

        dispositions = [
            {
                "source_cause_index": index,
                "semantic_role": (
                    "causal_summary" if index == 0 else "fault_value_mode"
                ),
                "fta_disposition": "relation_only",
                "evidence_quote": unique_source_quote(cause),
                "reason_code": (
                    "summary_not_independent_event"
                    if index == 0
                    else "fault_value_mode_without_instance_evidence"
                ),
                "rationale": (
                    "The Cause summary is retained without duplicating it as an independent event."
                    if index == 0
                    else "This item is a fault-value table mode; no device-instance reading is supplied."
                ),
            }
            for index, cause in enumerate(record.causes)
        ]

        class Client:
            prompts = []

            def complete(self, _prompt):
                self.prompts.append(_prompt)
                return json.dumps({"cause_dispositions": dispositions})

        client = Client()
        tree = CandidateFtaExtractionService(client).propose(
            extraction, record.record_id, source_text
        )

        self.assertEqual(16, len(tree.cause_dispositions))
        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("no_fta_event_candidates", tree.blockers)
        self.assertEqual(1, len(tree.nodes))
        self.assertEqual(1, len(client.prompts))
        self.assertIn("fta-cause-disposition-v6", client.prompts[0])
        self.assertIn("必须把每条原因命题与 payload 中的 top_event 做语义比较", client.prompts[0])
        self.assertIn("不得仅凭这条映射自动连到当前顶事件", client.prompts[0])
        self.assertTrue(
            all(
                item.disposition.value == "relation_only"
                for item in tree.cause_dispositions
            )
        )
        self.assertTrue(
            all(
                source_text[item.evidence[0].start : item.evidence[0].end]
                == item.evidence[0].quote
                for item in tree.cause_dispositions
            )
        )
        self.assertFalse(tree.fta_ready)

    def test_f30027_possible_causes_and_fault_value_modes_get_distinct_dispositions(self):
        repository_root = ROOT.parent
        corpus_path = (
            repository_root
            / "evaluation"
            / "quality_eval"
            / "datasets"
            / "siemens_s210_public_fault_corpus_v1.jsonl"
        )
        source_record = next(
            json.loads(line)
            for line in corpus_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["weak_record"]["fault_code"] == "F30027"
        )
        preview_path = (
            repository_root
            / "evaluation"
            / "quality_eval"
            / "runs"
            / "siemens_s210_2019_f30027_candidate_fta_preview_prompt_guard_v3_2026-09-27.json"
        )
        prior_preview = json.loads(preview_path.read_text(encoding="utf-8"))
        extraction_response = next(
            item["responses"][0]
            for item in prior_preview["model_stage_responses"]
            if item["stage"] == "fault_extraction"
        )
        source_text = source_record["input_text"]
        extraction = self._replay_extraction_response(extraction_response, source_text)
        record = extraction.records[0]
        cause_spans = [
            span
            for span in extraction.evidence_spans
            if span.field is EvidenceField.CAUSE
        ]
        indexed_cause_spans = {span.value_index: span for span in cause_spans}
        self.assertEqual(23, len(cause_spans))
        self.assertEqual(23, len(indexed_cause_spans))
        self.assertEqual(set(range(23)), set(indexed_cause_spans))
        self.assertTrue(
            all(
                sum(span.value_index == index for span in cause_spans) == 1
                for index in range(23)
            )
        )
        self.assertTrue(all(span.matches(source_text) for span in indexed_cause_spans.values()))

        def unique_source_quote(cause):
            for size in range(len(cause), 7, -1):
                for start in range(len(cause) - size + 1):
                    quote = cause[start : start + size]
                    first = source_text.find(quote)
                    if first >= 0 and source_text.find(quote, first + 1) < 0:
                        return quote
            self.fail(f"no unique source quote available for cause: {cause}")

        rows = []
        for index, cause in enumerate(record.causes):
            if index == 0:
                role = "causal_summary"
                disposition = "relation_only"
                reason_code = "summary_not_independent_event"
                rationale = "Keep the summary auditable without duplicating it as a leaf event."
            elif 1 <= index <= 9:
                role = "causal_condition"
                disposition = "fta_event_candidate"
                reason_code = "direct_causal_or_condition_statement"
                rationale = "This item belongs to the explicitly enumerated Possible causes section."
            else:
                role = "fault_value_mode"
                disposition = "relation_only"
                reason_code = "fault_value_mode_without_instance_evidence"
                rationale = "A fault-value bit meaning is not evidence that the mode occurred in this instance."
            rows.append(
                {
                    "source_cause_index": index,
                    "semantic_role": role,
                    "fta_disposition": disposition,
                    "evidence_quote": unique_source_quote(cause),
                    "reason_code": reason_code,
                    "rationale": rationale,
                }
            )

        class Client:
            def complete(self, _prompt):
                return json.dumps({"cause_dispositions": rows})

        batch = CauseDispositionService(Client()).propose(
            extraction, record.record_id, source_text
        )

        self.assertEqual(23, len(batch.dispositions))
        self.assertEqual(tuple(range(1, 10)), tuple(
            item.source_cause_index
            for item in batch.dispositions
            if item.disposition.value == "fta_event_candidate"
        ))
        self.assertEqual("relation_only", batch.dispositions[0].disposition.value)
        self.assertTrue(
            all(
                batch.dispositions[index].disposition.value == "relation_only"
                and batch.dispositions[index].semantic_role.value == "fault_value_mode"
                for index in range(10, 23)
            )
        )
        self.assertEqual(23, len(record.causes))


if __name__ == "__main__":
    unittest.main()
