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
from fta.candidate_fta_extraction_service import CandidateFtaExtractionService
from fta.gate_confidence_policy import GateConfidencePolicy


class RecursiveCandidateFtaExtractionServiceTests(unittest.TestCase):
    SOURCE = (
        "A01631 SI P1: motor holding brake/SBC configuration not practical\n"
        "Reaction: NONE\n"
        "Acknowledge: NONE\n"
        "Cause: A configuration of motor holding brake and SBC was detected that is not practical.\n"
        "The following configurations can result in this message:\n"
        '- "No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1).\n'
        "Remedy: Check the parameterization of the motor holding brake and SBC and correct.\n"
        "Note:\n"
        "SBC: Safe Brake Control\n"
        "See also: p1215 (Motor holding brake configuration), p9602 (SI enable safe brake control)"
    )
    DESCRIPTION = "motor holding brake/SBC configuration not practical"
    CAUSE = "A configuration of motor holding brake and SBC was detected that is not practical."
    SCOPE = '- "No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1).'
    NO_BRAKE = '"No motor holding brake available" (p1215 = 0)'
    SBC_ENABLED = '"SBC" enabled (p9602 = 1)'
    RELATION = "The following configurations can result in this message:"

    @staticmethod
    def _three_stage_responses(response):
        full = json.loads(response)
        assessments = full.get("gate_assessments", [])
        dispositions = full.get("cause_dispositions")
        if dispositions is None:
            cause_quotes = {}
            for node in full.get("nodes", []):
                if node.get("node_type") != "cause_candidate":
                    continue
                quote = node.get("evidence_quote", "")
                for cause_index in node.get("source_cause_indices", []):
                    cause_quotes.setdefault(cause_index, quote)
            dispositions = [
                {
                    "source_cause_index": index,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": cause_quotes[index],
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source states this event condition.",
                }
                for index in sorted(cause_quotes)
            ]
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
        self.record = FaultRecord(
            fault_code="A01631",
            description=self.DESCRIPTION,
            causes=(self.CAUSE,),
            parameters=("p1215", "p9602"),
        )
        start = self.SOURCE.index(self.DESCRIPTION)
        self.extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=self.DESCRIPTION,
                    start=start,
                    end=start + len(self.DESCRIPTION),
                ),
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=self.CAUSE,
                    start=self.SOURCE.index(self.CAUSE),
                    end=self.SOURCE.index(self.CAUSE) + len(self.CAUSE),
                    value_index=0,
                ),
            ),
        )

    def _response(self, *, repeat_leaf=False, root_probabilities=None):
        repeated_quote = self.NO_BRAKE if repeat_leaf else self.SCOPE
        repeated_node_quote = repeated_quote if repeat_leaf else self.NO_BRAKE
        return json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "configuration_group",
                        "node_type": "intermediate_event_candidate",
                        "text": "Incompatible motor holding brake and SBC configuration",
                        "source_cause_indices": [0],
                        "evidence_quote": self.CAUSE,
                    },
                    {
                        "node_id": "no_brake",
                        "node_type": "cause_candidate",
                        "text": "No motor holding brake is available (p1215 = 0)",
                        "source_cause_indices": [0],
                        "evidence_quote": repeated_node_quote,
                    },
                    {
                        "node_id": "sbc_enabled",
                        "node_type": "cause_candidate",
                        "text": "SBC is enabled (p9602 = 1)",
                        "source_cause_indices": [0],
                        "evidence_quote": self.SBC_ENABLED,
                    },
                ],
                "gate_assessments": [
                    {
                        "gate_id": "configuration_gate",
                        "output_node_id": "configuration_group",
                        "child_node_ids": ["no_brake", "sbc_enabled"],
                        "scope_type": "motor_holding_brake_sbc_configuration",
                        "gate_probabilities": {"AND": 0.91, "OR": 0.03, "unknown": 0.06},
                        "scope_quote": self.SOURCE[
                            self.SOURCE.index(self.CAUSE):
                            self.SOURCE.index(self.SCOPE) + len(self.SCOPE)
                        ],
                        "gate_evidence_quote": self.SCOPE,
                        "cause_set_complete": True,
                        "cause_set_leaf_normalized": True,
                        "reason": "The source joins both configuration conditions with and.",
                    },
                    {
                        "gate_id": "top_event_gate",
                        "output_node_id": "__top_event__",
                        "child_node_ids": ["configuration_group"],
                        "scope_type": "fault_event_root",
                        "gate_probabilities": root_probabilities or {"AND": 0.08, "OR": 0.10, "unknown": 0.82},
                        "scope_quote": self.SOURCE[: self.SOURCE.index(self.SCOPE) + len(self.SCOPE)],
                        "gate_evidence_quote": "",
                        "cause_set_complete": False,
                        "cause_set_leaf_normalized": False,
                        "reason": "One documented configuration does not prove the complete top-event gate.",
                    },
                ],
                "relations": [
                    {
                        "source_node_id": "configuration_group",
                        "target_node_id": "__top_event__",
                        "relation_type": "may_cause",
                        "relation_scope_quote": self.SOURCE[: self.SOURCE.index(self.SCOPE) + len(self.SCOPE)],
                        "evidence_quote": self.RELATION,
                    }
                ],
                "cause_dispositions": [
                    {
                        "source_cause_index": 0,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": self.CAUSE,
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "The cause sentence is retained as a candidate event for review.",
                    }
                ],
                "cause_set_complete": True,
                "reason": "Preserve the local configuration gate and the unresolved event gate.",
            },
            ensure_ascii=False,
        )

    def _service(self, response):
        responses = iter(self._three_stage_responses(response))

        class Client:
            def complete(self, _prompt):
                return next(responses)

        return CandidateFtaExtractionService(
            Client(),
            GateConfidencePolicy("test-provisional", 0.75, 0.15),
        )

    def test_a01631_preserves_local_and_gate_possible_cause_edge_and_unknown_root(self):
        tree = self._service(self._response()).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual(CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW, tree.status)
        self.assertEqual("event:" + self.record.record_id, tree.top_event_id)
        nodes = {node.node_id: node for node in tree.nodes}
        gates = {gate.scope_type: gate for gate in tree.gate_assessments}
        self.assertEqual("AND", gates["motor_holding_brake_sbc_configuration"].gate)
        no_brake = nodes["cause:" + self.record.record_id + ":no_brake"].evidence[0]
        self.assertEqual(self.SOURCE.index(self.NO_BRAKE), no_brake.start)
        self.assertEqual(no_brake.start + len(self.NO_BRAKE), no_brake.end)
        local_scope = gates["motor_holding_brake_sbc_configuration"].scope_evidence[0]
        self.assertEqual(self.SOURCE.index(self.CAUSE), local_scope.start)
        self.assertEqual(self.SOURCE.index(self.SCOPE) + len(self.SCOPE), local_scope.end)
        self.assertEqual("unknown", gates["fault_event_root"].gate)
        self.assertEqual(
            {"AND": 0.91, "OR": 0.03, "unknown": 0.06},
            dict(gates["motor_holding_brake_sbc_configuration"].gate_probabilities),
        )
        self.assertEqual(
            {"AND": 0.08, "OR": 0.10, "unknown": 0.82},
            dict(gates["fault_event_root"].gate_probabilities),
        )
        self.assertEqual(2, len(gates["motor_holding_brake_sbc_configuration"].child_node_ids))
        self.assertEqual(self.SOURCE.index(self.NO_BRAKE), nodes["cause:" + self.record.record_id + ":no_brake"].evidence[0].start)
        self.assertEqual("may_cause", tree.relations[0].relation_type)
        self.assertEqual(self.RELATION, tree.relations[0].evidence[0].quote)
        self.assertFalse(tree.fta_ready)
        self.assertFalse(tree.production_ready)
        payload = tree.to_payload()
        self.assertEqual("v7", payload["artifact_version"])
        root_payload = next(
            item
            for item in payload["gate_assessments"]
            if item["scope_type"] == "fault_event_root"
        )
        self.assertEqual("unknown", root_payload["gate"])
        self.assertIn(root_payload["unknown_reason_code"], {
            reason.value for reason in UnknownGateReasonCode
        })
        self.assertEqual(
            sum(item["gate"] == "unknown" for item in payload["gate_assessments"]),
            sum(payload["unknown_gate_reason_counts"].values()),
        )
        json.dumps(payload, ensure_ascii=False)

    def test_disconnected_nodes_block_entire_tree_but_remain_for_review(self):
        expected_disconnected = {
            "intermediate_event:" + self.record.record_id + ":configuration_group",
            "cause:" + self.record.record_id + ":no_brake",
            "cause:" + self.record.record_id + ":sbc_enabled",
        }
        for relation_type in (None, "associated_with"):
            with self.subTest(relation_type=relation_type):
                response = json.loads(self._response())
                response["gate_assessments"] = response["gate_assessments"][:1]
                if relation_type is None:
                    response["relations"] = []
                else:
                    response["relations"][0]["relation_type"] = relation_type

                tree = self._service(json.dumps(response, ensure_ascii=False)).propose(
                    self.extraction, self.record.record_id, self.SOURCE
                )

                self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
                disconnected_ids = {
                    blocker.removeprefix("node_disconnected_from_top_event:")
                    for blocker in tree.blockers
                    if blocker.startswith("node_disconnected_from_top_event:")
                }
                self.assertEqual(expected_disconnected, disconnected_ids)
                self.assertTrue(
                    expected_disconnected.issubset(
                        {node.node_id for node in tree.nodes}
                    ),
                    "blocked trees must retain detached nodes for investigation",
                )
                self.assertIn(tree.top_event_id, {node.node_id for node in tree.nodes})

                with self.assertRaisesRegex(ValueError, "disconnected"):
                    replace(
                        tree,
                        status=CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW,
                        blockers=(),
                    )

    def test_root_gate_is_unknown_even_if_model_prefers_or_when_scope_is_incomplete(self):
        root_probabilities = {"AND": 0.04, "OR": 0.92, "unknown": 0.04}
        tree = self._service(self._response(root_probabilities=root_probabilities)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        root = next(gate for gate in tree.gate_assessments if gate.scope_type == "fault_event_root")
        self.assertEqual("unknown", root.gate)
        self.assertEqual(
            tuple(root_probabilities.items()),
            root.gate_probabilities,
        )
        self.assertIn("cause_set_incomplete_or_not_leaf_normalized", root.blockers)
        self.assertEqual(
            UnknownGateReasonCode.INCOMPLETE_CHILD_SET,
            root.unknown_reason_code,
        )

    def test_complete_single_child_scope_is_not_applicable_and_has_no_gate_confidence(self):
        response = json.loads(self._response())
        root = response["gate_assessments"][1]
        root["cause_set_complete"] = True
        root["cause_set_leaf_normalized"] = True
        root.pop("gate_probabilities")

        tree = self._service(json.dumps(response, ensure_ascii=False)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        root_assessment = next(
            gate for gate in tree.gate_assessments if gate.scope_type == "fault_event_root"
        )
        self.assertEqual("not_applicable", root_assessment.gate)
        self.assertEqual((), root_assessment.gate_probabilities)
        self.assertFalse(root_assessment.gate_evidence)
        self.assertIsNone(root_assessment.confidence_policy_id)
        self.assertIn("single_complete_child_scope_has_no_boolean_gate", root_assessment.decision_reason)
        serialized = next(
            gate
            for gate in tree.to_payload()["gate_assessments"]
            if gate["scope_type"] == "fault_event_root"
        )
        self.assertEqual("not_applicable", serialized["gate"])
        self.assertEqual({}, serialized["gate_probabilities"])

    def test_not_applicable_contract_rejects_incomplete_or_multi_child_scope(self):
        evidence = CandidateFtaEvidence(
            citation_id="source:0-4",
            source_id="input_text",
            quote="text",
            start=0,
            end=4,
        )
        with self.assertRaisesRegex(ValueError, "not_applicable requires one complete normalized child"):
            CandidateFtaGateAssessment(
                gate_node_id="gate-1",
                output_node_id="out",
                child_node_ids=("child-1", "child-2"),
                scope_type="scope",
                gate="not_applicable",
                gate_probabilities=(),
                scope_evidence=(evidence,),
                cause_set_complete=True,
                cause_set_leaf_normalized=True,
                decision_reason="No Boolean gate applies.",
            )

    def test_nested_and_and_root_or_keep_independent_scope_evidence_and_probabilities(self):
        source = (
            "Drive trips if either the pump stalls when pressure is low and the seal is damaged "
            "or the fan is broken."
        )
        description = "Drive trips"
        record = FaultRecord(
            fault_code="FTEST",
            description=description,
            causes=("pump condition", "fan failure"),
        )
        pump_quote = "the pump stalls when pressure is low and the seal is damaged"
        pressure_quote = "pressure is low"
        seal_quote = "the seal is damaged"
        fan_quote = "the fan is broken"
        root_gate_quote = "either " + pump_quote + " or " + fan_quote
        description_start = source.index(description)
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=description,
                    start=description_start,
                    end=description_start + len(description),
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=pump_quote,
                    start=source.index(pump_quote),
                    end=source.index(pump_quote) + len(pump_quote),
                    value_index=0,
                ),
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=fan_quote,
                    start=source.index(fan_quote),
                    end=source.index(fan_quote) + len(fan_quote),
                    value_index=1,
                ),
            ),
        )
        payload = {
            "nodes": [
                {
                    "node_id": "pump_condition",
                    "node_type": "intermediate_event_candidate",
                    "text": "Pump stalls under the stated pressure/seal conditions",
                    "source_cause_indices": [0],
                    "evidence_quote": pump_quote,
                },
                {
                    "node_id": "pressure_low",
                    "node_type": "cause_candidate",
                    "text": "Pressure is low",
                    "source_cause_indices": [0],
                    "evidence_quote": pressure_quote,
                },
                {
                    "node_id": "seal_damaged",
                    "node_type": "cause_candidate",
                    "text": "Seal is damaged",
                    "source_cause_indices": [0],
                    "evidence_quote": seal_quote,
                },
                {
                    "node_id": "fan_broken",
                    "node_type": "cause_candidate",
                    "text": "Fan is broken",
                    "source_cause_indices": [1],
                    "evidence_quote": fan_quote,
                },
            ],
            "gate_assessments": [
                {
                    "gate_id": "pump-local",
                    "output_node_id": "pump_condition",
                    "child_node_ids": ["pressure_low", "seal_damaged"],
                    "scope_type": "pump_condition",
                    "gate_probabilities": {"AND": 0.89, "OR": 0.04, "unknown": 0.07},
                    "scope_quote": pump_quote,
                    "gate_evidence_quote": "pressure is low and the seal is damaged",
                    "cause_set_complete": True,
                    "cause_set_leaf_normalized": True,
                    "reason": "Both conditions are stated within the pump clause.",
                },
                {
                    "gate_id": "fault-root",
                    "output_node_id": "__top_event__",
                    "child_node_ids": ["pump_condition", "fan_broken"],
                    "scope_type": "fault_event_root",
                    "gate_probabilities": {"AND": 0.03, "OR": 0.93, "unknown": 0.04},
                    "scope_quote": source,
                    "gate_evidence_quote": root_gate_quote,
                    "cause_set_complete": True,
                    "cause_set_leaf_normalized": True,
                    "reason": "The top event has two explicitly alternative branches.",
                },
            ],
            "relations": [],
            "reason": "Nested local gate example.",
        }

        responses = self._three_stage_responses(json.dumps(payload, ensure_ascii=False))
        response_index = 0

        class Client:
            def complete(self, _prompt):
                nonlocal response_index
                response = responses[response_index % len(responses)]
                response_index += 1
                return response

        service = CandidateFtaExtractionService(
            Client(), GateConfidencePolicy("nested-test", 0.75, 0.15)
        )
        tree = service.propose(extraction, record.record_id, source)

        gates = {gate.scope_type: gate for gate in tree.gate_assessments}
        self.assertEqual(CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW, tree.status)
        self.assertEqual("AND", gates["pump_condition"].gate)
        self.assertEqual("OR", gates["fault_event_root"].gate)
        self.assertNotEqual(
            gates["pump_condition"].gate_node_id,
            gates["fault_event_root"].gate_node_id,
        )
        self.assertEqual(0.89, dict(gates["pump_condition"].gate_probabilities)["AND"])
        self.assertEqual(0.93, dict(gates["fault_event_root"].gate_probabilities)["OR"])

        second_record = FaultRecord(
            fault_code="FTEST",
            description=description,
            causes=("pump condition", "fan failure"),
        )
        second_extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(second_record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=second_record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=description,
                    start=description_start,
                    end=description_start + len(description),
                ),
                EvidenceSpan(
                    record_id=second_record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=pump_quote,
                    start=source.index(pump_quote),
                    end=source.index(pump_quote) + len(pump_quote),
                    value_index=0,
                ),
                EvidenceSpan(
                    record_id=second_record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=fan_quote,
                    start=source.index(fan_quote),
                    end=source.index(fan_quote) + len(fan_quote),
                    value_index=1,
                ),
            ),
        )
        second_tree = service.propose(second_extraction, second_record.record_id, source)
        self.assertEqual(
            {gate.gate_node_id for gate in tree.gate_assessments},
            {gate.gate_node_id for gate in second_tree.gate_assessments},
        )

    def test_f06000_preserves_outer_reason_list_and_local_ground_fault_or_short_circuit(self):
        description = "Infeed: Precharging monitoring time expired"
        reason_texts = (
            "There is no line voltage connected.",
            "The line contactor/line side switch has not been closed.",
            "The line voltage is too low.",
            "Line voltage incorrectly set (p0210).",
            "The precharging resistors are overheated as there were too many precharging operations per time unit.",
            "The precharging resistors are overheated as the DC link capacitance is too high.",
            'The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit, power is taken from the DC link.',
            "The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the Braking Module.",
            "The DC link has either a ground fault or a short-circuit.",
            "The precharging circuit is possibly defective (only for chassis units).",
        )
        numbered_reasons = tuple(
            f"{index + 1}) {text}" for index, text in enumerate(reason_texts)
        )
        list_intro = (
            "The end of the DC link precharging was not able to be completed "
            "for one of the following reasons:"
        )
        cause_scope = list_intro + "\n" + "\n".join(numbered_reasons)
        source = description + "\nCause: " + cause_scope
        group_quote = numbered_reasons[8]
        causes = reason_texts
        record = FaultRecord(fault_code="F06000", description=description, causes=causes)
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=description,
                    start=0,
                    end=len(description),
                ),
                *(
                    EvidenceSpan(
                        record_id=record.record_id,
                        field=EvidenceField.CAUSE,
                        source_id="input_text",
                        quote=reason,
                        start=source.index(reason),
                        end=source.index(reason) + len(reason),
                        value_index=index,
                    )
                    for index, reason in enumerate(reason_texts)
                ),
            ),
        )

        nodes = [
            {
                "node_id": "precharging_incomplete",
                "node_type": "intermediate_event_candidate",
                "text": "The end of DC link precharging could not be completed",
                "source_cause_indices": list(range(10)),
                "evidence_quote": list_intro,
            }
        ]
        nodes.extend(
            {
                "node_id": f"reason_{index + 1}",
                "node_type": "cause_candidate",
                "text": reason,
                "source_cause_indices": [index],
                "evidence_quote": numbered_reasons[index],
            }
            for index, reason in enumerate(reason_texts)
            if index != 8
        )
        nodes.extend(
            [
                {
                    "node_id": "dc_link_electrical_fault",
                    "node_type": "intermediate_event_candidate",
                    "text": "DC link ground fault or short-circuit",
                    "source_cause_indices": [8],
                    "evidence_quote": group_quote,
                },
                {
                    "node_id": "ground_fault",
                    "node_type": "cause_candidate",
                    "text": "Ground fault",
                    "source_cause_indices": [8],
                    "evidence_quote": "a ground fault",
                },
                {
                    "node_id": "short_circuit",
                    "node_type": "cause_candidate",
                    "text": "Short-circuit",
                    "source_cause_indices": [8],
                    "evidence_quote": "a short-circuit",
                },
            ]
        )
        scopes = [
            {
                "gate_id": "root-scope",
                "output_node_id": "__top_event__",
                "child_node_ids": ["precharging_incomplete"],
                "scope_type": "fault_event_root",
                "scope_quote": source,
                "cause_set_complete": False,
                "cause_set_leaf_normalized": False,
                "reason": "A single intermediate event does not establish the root gate.",
            },
            {
                "gate_id": "reason-list-scope",
                "output_node_id": "precharging_incomplete",
                "child_node_ids": [
                    *(f"reason_{index + 1}" for index in range(8)),
                    "dc_link_electrical_fault",
                    "reason_10",
                ],
                "scope_type": "precharging_completion_reason_list",
                "scope_quote": cause_scope,
                "cause_set_complete": True,
                "cause_set_leaf_normalized": True,
                "reason": "The complete ten-item reason list is preserved as one scope; its gate is not inferred from enumeration.",
            },
            {
                "gate_id": "dc-link-local-scope",
                "output_node_id": "dc_link_electrical_fault",
                "child_node_ids": ["ground_fault", "short_circuit"],
                "scope_type": "dc_link_fault_mode",
                "scope_quote": group_quote,
                "cause_set_complete": True,
                "cause_set_leaf_normalized": True,
                "reason": "The local either/or phrase stays nested under list item nine.",
            },
        ]
        assessments = [
            {
                "gate_id": "root-scope",
                "gate_probabilities": {"AND": 0.04, "OR": 0.06, "unknown": 0.90},
                "gate_evidence_quote": "",
                "reason": "No direct root-gate evidence.",
            },
            {
                "gate_id": "reason-list-scope",
                "gate_probabilities": {"AND": 0.04, "OR": 0.06, "unknown": 0.90},
                "gate_evidence_quote": "",
                "reason": "Numbering alone does not establish a Boolean gate.",
            },
            {
                "gate_id": "dc-link-local-scope",
                "gate_probabilities": {"AND": 0.02, "OR": 0.94, "unknown": 0.04},
                "gate_evidence_quote": "either a ground fault or a short-circuit",
                "reason": "The local source wording explicitly states either/or.",
            },
        ]
        structure_payload = {
            "structure_status": "complete",
            "nodes": nodes,
            "gate_scopes": scopes,
            "unresolved_cause_indices": [],
            "reason": "Preserve the local Boolean scope without flattening.",
        }
        assessment_payload = {
            "gate_assessments": assessments,
            "relations": [],
            "reason": "Gate probabilities are scope-local estimates only.",
        }

        cause_dispositions = []
        for index, reason in enumerate(reason_texts):
            evidence_quote = next(
                node["evidence_quote"]
                for node in nodes
                if node["node_type"] == "cause_candidate"
                and index in node["source_cause_indices"]
            )
            cause_dispositions.append(
                {
                    "source_cause_index": index,
                    "semantic_role": "causal_condition",
                    "fta_disposition": "fta_event_candidate",
                    "evidence_quote": evidence_quote,
                    "reason_code": "direct_causal_or_condition_statement",
                    "rationale": "The source explicitly lists this possible cause.",
                }
            )

        class Client:
            def __init__(self):
                self.responses = iter(
                    (
                        json.dumps(
                            {"cause_dispositions": cause_dispositions},
                            ensure_ascii=False,
                        ),
                        json.dumps(structure_payload, ensure_ascii=False),
                        json.dumps(assessment_payload, ensure_ascii=False),
                    )
                )

            def complete(self, _prompt):
                return next(self.responses)

        tree = CandidateFtaExtractionService(
            Client(), GateConfidencePolicy("test-provisional", 0.75, 0.15)
        ).propose(extraction, record.record_id, source)

        gates = {gate.scope_type: gate for gate in tree.gate_assessments}
        self.assertEqual("unknown", gates["fault_event_root"].gate)
        self.assertEqual("unknown", gates["precharging_completion_reason_list"].gate)
        self.assertEqual("OR", gates["dc_link_fault_mode"].gate)
        self.assertEqual(1, len(gates["fault_event_root"].child_node_ids))
        local_group_id = "intermediate_event:" + record.record_id + ":dc_link_electrical_fault"
        self.assertIn(local_group_id, gates["precharging_completion_reason_list"].child_node_ids)
        self.assertEqual(
            {"Ground fault", "Short-circuit"},
            {
                next(node for node in tree.nodes if node.node_id == child).text
                for child in gates["dc_link_fault_mode"].child_node_ids
            },
        )
        self.assertTrue(
            all(
                source[evidence.start : evidence.end] == evidence.quote
                for gate in tree.gate_assessments
                for evidence in gate.scope_evidence
            )
        )
        self.assertFalse(tree.fta_ready)

    def test_repeated_leaf_quote_blocks_candidate_instead_of_guessing_its_location(self):
        repeated_source = self.SOURCE + "Repeated phrase: " + self.NO_BRAKE
        tree = self._service(self._response(repeat_leaf=True)).propose(
            self.extraction, self.record.record_id, repeated_source
        )

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        node = next(node for node in tree.nodes if node.node_id.endswith(":no_brake"))
        self.assertFalse(node.evidence)
        self.assertIn("node_evidence_missing_or_ambiguous:no_brake", tree.blockers)
        self.assertFalse(tree.fta_ready)

    def test_relation_quote_must_share_scope_with_both_endpoint_events(self):
        response = json.loads(self._response())
        response["relations"][0]["relation_scope_quote"] = self.RELATION
        tree = self._service(json.dumps(response, ensure_ascii=False)).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("relation_scope_does_not_contain_endpoints:0", tree.blockers)

    def test_missing_source_cause_mapping_blocks_candidate(self):
        response = json.loads(self._response())
        two_cause_record = FaultRecord(
            fault_code="A01631",
            description=self.DESCRIPTION,
            causes=(self.CAUSE, "A second extracted cause omitted by the proposal."),
            parameters=("p1215", "p9602"),
        )
        response["cause_dispositions"] = [
            {
                "source_cause_index": 0,
                "semantic_role": "causal_condition",
                "fta_disposition": "fta_event_candidate",
                "evidence_quote": self.CAUSE,
                "reason_code": "direct_causal_or_condition_statement",
                "rationale": "The first cause is explicitly represented.",
            },
            {
                "source_cause_index": 1,
                "semantic_role": "causal_condition",
                "fta_disposition": "fta_event_candidate",
                "evidence_quote": self.RELATION,
                "reason_code": "direct_causal_or_condition_statement",
                "rationale": "The second input cause is deliberately left unmapped by the structure proposal.",
            },
        ]
        extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(two_cause_record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=two_cause_record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=self.DESCRIPTION,
                    start=self.SOURCE.index(self.DESCRIPTION),
                    end=self.SOURCE.index(self.DESCRIPTION) + len(self.DESCRIPTION),
                ),
                EvidenceSpan(
                    record_id=two_cause_record.record_id,
                    field=EvidenceField.CAUSE,
                    source_id="input_text",
                    quote=self.CAUSE,
                    start=self.SOURCE.index(self.CAUSE),
                    end=self.SOURCE.index(self.CAUSE) + len(self.CAUSE),
                    value_index=0,
                ),
            ),
        )
        tree = self._service(json.dumps(response, ensure_ascii=False)).propose(
            extraction, two_cause_record.record_id, self.SOURCE
        )

        self.assertEqual(CandidateFtaStatus.BLOCKED, tree.status)
        self.assertIn("cause_disposition_unresolved:1", tree.blockers)


if __name__ == "__main__":
    unittest.main()
