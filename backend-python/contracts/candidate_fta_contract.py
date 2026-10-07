"""Contracts for evidence-bound, non-production FTA candidates."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import math
from typing import Iterable

from contracts.extraction_contract import (
    ExtractionResult,
)
from contracts.evidence_locator_review_contract import (
    EvidenceOccurrenceLocatorReview,
)
from contracts.fta_cause_disposition_contract import (
    CauseDisposition,
    FtaCauseDispositionBatch,
    FtaCauseDispositionKind,
    candidate_source_indices,
)


class CandidateFtaStatus(str, Enum):
    """Whether a proposed recursive tree passed its structural evidence checks."""

    CANDIDATE_READY_FOR_REVIEW = "candidate_ready_for_review"
    BLOCKED = "blocked"


class CandidateFtaOutcomeStatus(str, Enum):
    """Outcome of proposing a tree for one extracted record."""

    PROPOSED = "proposed"
    BLOCKED = "blocked"
    FAILED = "failed"


class UnknownGateReasonCode(str, Enum):
    """Machine-readable primary reason for an unresolved Boolean gate."""

    NO_DIRECT_LOGIC_EVIDENCE = "no_direct_logic_evidence"
    INCOMPLETE_CHILD_SET = "incomplete_child_set"
    SEMANTIC_SCOPE_AMBIGUITY = "semantic_scope_ambiguity"
    EVIDENCE_MISSING_OR_AMBIGUOUS = "evidence_missing_or_ambiguous"
    CONFIDENCE_POLICY_UNAVAILABLE = "confidence_policy_unavailable"
    MODEL_CONFIDENCE_BELOW_POLICY = "model_confidence_below_policy"
    MODEL_PREFERS_UNKNOWN_GATE = "model_prefers_unknown_gate"
    UNRESOLVED_STRUCTURE = "unresolved_structure"
    LEGACY_UNSPECIFIED = "legacy_unspecified"


@dataclass(frozen=True)
class CandidateFtaOutcomeDiagnostic:
    code: str
    message: str
    stage: str
    retryable: bool

    def __post_init__(self) -> None:
        for value, name in (
            (self.code, "code"),
            (self.message, "message"),
            (self.stage, "stage"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a boolean")


@dataclass(frozen=True)
class CandidateFtaRecordOutcome:
    record_id: str
    fault_code: str | None
    status: CandidateFtaOutcomeStatus
    tree: CandidateFtaTree | None = None
    diagnostics: tuple[CandidateFtaOutcomeDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        if self.fault_code is not None and not isinstance(self.fault_code, str):
            raise TypeError("fault_code must be a string or None")
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", CandidateFtaOutcomeStatus(self.status))
            except ValueError as exc:
                raise ValueError("unsupported candidate FTA outcome status") from exc
        elif not isinstance(self.status, CandidateFtaOutcomeStatus):
            raise TypeError("status must be a CandidateFtaOutcomeStatus")
        diagnostics = tuple(self.diagnostics)
        if not all(isinstance(item, CandidateFtaOutcomeDiagnostic) for item in diagnostics):
            raise TypeError("diagnostics must contain CandidateFtaOutcomeDiagnostic values")
        if self.status is CandidateFtaOutcomeStatus.PROPOSED:
            if (
                self.tree is None
                or self.tree.status is not CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW
                or diagnostics
            ):
                raise ValueError("proposed outcome requires a reviewable candidate tree only")
        elif self.status is CandidateFtaOutcomeStatus.BLOCKED:
            if self.tree is None or self.tree.status is not CandidateFtaStatus.BLOCKED:
                raise ValueError("blocked outcome requires a blocked candidate tree")
            if diagnostics:
                raise ValueError("blocked outcome uses tree blockers, not diagnostics")
        elif self.tree is not None or not diagnostics:
            raise ValueError("failed outcome requires diagnostics and no tree")
        if self.tree is not None and self.tree.record_id != self.record_id:
            raise ValueError("outcome tree must reference the same record_id")
        object.__setattr__(self, "diagnostics", diagnostics)

    def to_payload(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "fault_code": self.fault_code,
            "status": self.status.value,
            "tree": self.tree.to_payload() if self.tree else None,
            "diagnostics": [
                {
                    "code": item.code,
                    "message": item.message,
                    "stage": item.stage,
                    "retryable": item.retryable,
                }
                for item in self.diagnostics
            ],
        }


@dataclass(frozen=True)
class CandidateFtaGenerationResult:
    """In-memory retry envelope retaining extraction facts and evidence."""

    extraction: ExtractionResult
    source_text_sha256: str
    outcomes: tuple[CandidateFtaRecordOutcome, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")
        if (
            not isinstance(self.source_text_sha256, str)
            or len(self.source_text_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.source_text_sha256)
        ):
            raise ValueError("source_text_sha256 must be a lowercase SHA-256 digest")
        outcomes = tuple(self.outcomes)
        if not all(isinstance(item, CandidateFtaRecordOutcome) for item in outcomes):
            raise TypeError("outcomes must contain CandidateFtaRecordOutcome values")
        extracted_ids = {record.record_id for record in self.extraction.records}
        outcome_ids = [outcome.record_id for outcome in outcomes]
        if len(set(outcome_ids)) != len(outcome_ids) or not set(outcome_ids) <= extracted_ids:
            raise ValueError("outcomes must uniquely reference records in the extraction")
        object.__setattr__(self, "outcomes", outcomes)

    def to_payload(self) -> dict[str, object]:
        """Serialize the retained extraction so a caller can retry without re-extracting."""
        return {
            "artifact_type": "candidate_fta_generation_result",
            "artifact_version": "v3",
            "source_text_sha256": self.source_text_sha256,
            "extraction": {
                "result_id": self.extraction.result_id,
                "status": self.extraction.status.value,
                "records": [
                    {
                        "record_id": record.record_id,
                        "fault_code": record.fault_code,
                        "description": record.description,
                        "component": record.component,
                        "related_components": list(record.related_components),
                        "causes": list(record.causes),
                        "parameters": list(record.parameters),
                        "confidence": record.confidence,
                    }
                    for record in self.extraction.records
                ],
                "evidence_spans": [
                    {
                        "record_id": span.record_id,
                        "field": span.field.value,
                        "source_id": span.source_id,
                        "quote": span.quote,
                        "start": span.start,
                        "end": span.end,
                        "value_index": span.value_index,
                    }
                    for span in self.extraction.evidence_spans
                ],
                "diagnostics": [
                    {
                        "code": diagnostic.code,
                        "message": diagnostic.message,
                        "stage": diagnostic.stage,
                        "retryable": diagnostic.retryable,
                    }
                    for diagnostic in self.extraction.diagnostics
                ],
            },
            "outcomes": [item.to_payload() for item in self.outcomes],
        }

    @classmethod
    def for_source(
        cls,
        extraction: ExtractionResult,
        source_text: str,
        outcomes: Iterable[CandidateFtaRecordOutcome] = (),
    ) -> "CandidateFtaGenerationResult":
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must be a non-empty string")
        return cls(
            extraction=extraction,
            source_text_sha256=sha256(source_text.encode("utf-8")).hexdigest(),
            outcomes=tuple(outcomes),
        )


@dataclass(frozen=True)
class CandidateFtaEvidence:
    """An exact, uniquely bound quotation from the supplied source text."""

    citation_id: str
    source_id: str
    quote: str
    start: int
    end: int

    def __post_init__(self) -> None:
        for value, name in (
            (self.citation_id, "citation_id"),
            (self.source_id, "source_id"),
            (self.quote, "quote"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.start, bool) or not isinstance(self.start, int):
            raise TypeError("start must be an integer")
        if isinstance(self.end, bool) or not isinstance(self.end, int):
            raise TypeError("end must be an integer")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("evidence offsets must satisfy 0 <= start < end")
        if self.end - self.start != len(self.quote):
            raise ValueError("evidence offsets must have the same length as quote")


@dataclass(frozen=True)
class CandidateFtaNode:
    """One event/condition in a recursive, evidence-bound candidate graph."""

    node_id: str
    node_type: str
    text: str
    evidence: tuple[CandidateFtaEvidence, ...] = ()
    source_cause_indices: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        for value, name in ((self.node_id, "node_id"), (self.text, "text")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.node_type not in {
            "top_event_candidate",
            "intermediate_event_candidate",
            "cause_candidate",
            "observation_candidate",
        }:
            raise ValueError("unsupported candidate FTA node_type")
        evidence = tuple(self.evidence)
        if not all(isinstance(item, CandidateFtaEvidence) for item in evidence):
            raise TypeError("node evidence must contain CandidateFtaEvidence values")
        if self.node_type == "observation_candidate" and not evidence:
            raise ValueError("detached observation candidates require exact source evidence")
        cause_indices = tuple(self.source_cause_indices)
        if any(
            isinstance(index, bool) or not isinstance(index, int) or index < 0
            for index in cause_indices
        ):
            raise ValueError("source_cause_indices must contain non-negative integers")
        if len(set(cause_indices)) != len(cause_indices):
            raise ValueError("source_cause_indices must not contain duplicates")
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "source_cause_indices", cause_indices)


@dataclass(frozen=True)
class CandidateFtaGateAssessment:
    """An independently assessed gate at one explicit event scope."""

    gate_node_id: str
    output_node_id: str
    child_node_ids: tuple[str, ...]
    scope_type: str
    gate: str
    gate_probabilities: tuple[tuple[str, float], ...]
    scope_evidence: tuple[CandidateFtaEvidence, ...]
    gate_evidence: tuple[CandidateFtaEvidence, ...] = ()
    cause_set_complete: bool = False
    cause_set_leaf_normalized: bool = False
    confidence_policy_id: str | None = None
    confidence_policy_basis: str | None = None
    minimum_gate_probability: float | None = None
    minimum_gate_margin: float | None = None
    decision_reason: str = ""
    unknown_reason_code: UnknownGateReasonCode | None = None
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, name in (
            (self.gate_node_id, "gate_node_id"),
            (self.output_node_id, "output_node_id"),
            (self.scope_type, "scope_type"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.gate not in {"AND", "OR", "unknown", "not_applicable"}:
            raise ValueError("gate must be AND, OR, unknown, or not_applicable")
        children = tuple(self.child_node_ids)
        if not children or not all(isinstance(item, str) and item.strip() for item in children):
            raise ValueError("a gate assessment must reference at least one child node")
        if len(set(children)) != len(children) or self.output_node_id in children:
            raise ValueError("gate child IDs must be unique and cannot include the output node")
        if self.gate in {"AND", "OR"} and len(children) < 2:
            raise ValueError("AND/OR gate assessments require at least two child nodes")
        if not isinstance(self.cause_set_complete, bool) or not isinstance(
            self.cause_set_leaf_normalized, bool
        ):
            raise TypeError("cause-set state fields must be booleans")
        probabilities = tuple(self.gate_probabilities)
        if self.gate == "not_applicable":
            if (
                len(children) != 1
                or not self.cause_set_complete
                or not self.cause_set_leaf_normalized
            ):
                raise ValueError(
                    "not_applicable requires one complete normalized child"
                )
            if probabilities:
                raise ValueError("not_applicable must not carry gate-type probabilities")
        else:
            probability_map = dict(probabilities)
            if len(probability_map) != 3 or set(probability_map) != {
                "AND",
                "OR",
                "unknown",
            }:
                raise ValueError(
                    "gate_probabilities must contain AND, OR, and unknown exactly once"
                )
            for value in probability_map.values():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError("gate probabilities must be numeric")
                if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                    raise ValueError("gate probabilities must be finite and in [0, 1]")
            if abs(sum(float(value) for value in probability_map.values()) - 1.0) > 0.02:
                raise ValueError("gate probabilities must sum to 1.0")
            probabilities = tuple(
                (key, float(probability_map[key])) for key in ("AND", "OR", "unknown")
            )
        scope_evidence = tuple(self.scope_evidence)
        gate_evidence = tuple(self.gate_evidence)
        if not scope_evidence or not all(
            isinstance(item, CandidateFtaEvidence) for item in scope_evidence
        ):
            raise ValueError("every gate scope requires exact scope evidence")
        if not all(isinstance(item, CandidateFtaEvidence) for item in gate_evidence):
            raise TypeError("gate_evidence must contain CandidateFtaEvidence values")
        if self.gate in {"AND", "OR"}:
            if not gate_evidence:
                raise ValueError("a selected AND/OR gate requires direct gate evidence")
            if not self.cause_set_complete or not self.cause_set_leaf_normalized:
                raise ValueError("a selected gate requires a complete normalized child set")
        if self.confidence_policy_basis not in {None, "provisional"}:
            raise ValueError("unsupported confidence_policy_basis")
        thresholds = (self.minimum_gate_probability, self.minimum_gate_margin)
        if any(value is not None for value in thresholds):
            if any(value is None for value in thresholds):
                raise ValueError("both confidence thresholds must be provided together")
            for value in thresholds:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError("confidence thresholds must be numeric")
                if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                    raise ValueError("confidence thresholds must be finite and in [0, 1]")
        policy = (
            self.confidence_policy_id,
            self.confidence_policy_basis,
            self.minimum_gate_probability,
            self.minimum_gate_margin,
        )
        if any(value is not None for value in policy) and any(value is None for value in policy):
            raise ValueError("confidence policy ID, basis, and thresholds must be recorded together")
        if self.confidence_policy_id is not None and not self.confidence_policy_id.strip():
            raise ValueError("confidence_policy_id must be non-empty")
        if not isinstance(self.decision_reason, str):
            raise TypeError("decision_reason must be a string")
        unknown_reason_code = self.unknown_reason_code
        if unknown_reason_code is not None and not isinstance(
            unknown_reason_code, UnknownGateReasonCode
        ):
            try:
                unknown_reason_code = UnknownGateReasonCode(unknown_reason_code)
            except (TypeError, ValueError) as exc:
                raise ValueError("unsupported unknown_reason_code") from exc
        if self.gate == "unknown" and unknown_reason_code is None:
            raise ValueError("unknown gate requires exactly one unknown_reason_code")
        if self.gate != "unknown" and unknown_reason_code is not None:
            raise ValueError("only unknown gates may carry unknown_reason_code")
        if self.gate == "not_applicable":
            if gate_evidence:
                raise ValueError("not_applicable must not carry direct gate evidence")
            if any(value is not None for value in policy):
                raise ValueError("not_applicable must not carry a gate confidence policy")
            if not self.decision_reason.strip():
                raise ValueError("not_applicable requires a decision reason")
        blockers = tuple(self.blockers)
        if not all(isinstance(item, str) and item.strip() for item in blockers):
            raise TypeError("blockers must contain non-empty strings")
        object.__setattr__(self, "child_node_ids", children)
        object.__setattr__(self, "gate_probabilities", probabilities)
        object.__setattr__(self, "scope_evidence", scope_evidence)
        object.__setattr__(self, "gate_evidence", gate_evidence)
        object.__setattr__(self, "unknown_reason_code", unknown_reason_code)
        object.__setattr__(self, "blockers", blockers)


@dataclass(frozen=True)
class CandidateFtaRelation:
    """A directed causal/association edge, separate from Boolean gate logic."""

    relation_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    scope_evidence: tuple[CandidateFtaEvidence, ...]
    evidence: tuple[CandidateFtaEvidence, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.relation_id, "relation_id"),
            (self.source_node_id, "source_node_id"),
            (self.target_node_id, "target_node_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.source_node_id == self.target_node_id:
            raise ValueError("candidate relation cannot point a node to itself")
        if self.relation_type not in {"causes", "may_cause", "associated_with"}:
            raise ValueError("unsupported candidate relation_type")
        scope_evidence = tuple(self.scope_evidence)
        evidence = tuple(self.evidence)
        if not scope_evidence or not all(
            isinstance(item, CandidateFtaEvidence) for item in scope_evidence
        ):
            raise ValueError("candidate relation requires exact relation scope evidence")
        if not evidence or not all(isinstance(item, CandidateFtaEvidence) for item in evidence):
            raise ValueError("candidate relation requires exact source evidence")
        if any(
            not any(
                scope.source_id == item.source_id
                and scope.start <= item.start
                and item.end <= scope.end
                for scope in scope_evidence
            )
            for item in evidence
        ):
            raise ValueError("relation evidence must be contained in its relation scope")
        object.__setattr__(self, "scope_evidence", scope_evidence)
        object.__setattr__(self, "evidence", evidence)


def find_disconnected_candidate_node_ids(
    top_event_id: str,
    nodes: Iterable[CandidateFtaNode],
    gate_assessments: Iterable[CandidateFtaGateAssessment],
    relations: Iterable[CandidateFtaRelation],
) -> tuple[str, ...]:
    """Return nodes without a structural/cause path to the top event.

    Gate child-to-output links and explicit causes/may_cause relations define
    candidate-tree connectivity. associated_with is descriptive only and must
    not make an otherwise detached node appear connected to the FTA.
    """

    node_sequence = tuple(nodes)
    reverse_adjacency: dict[str, set[str]] = {
        node.node_id: set() for node in node_sequence
    }
    for gate in gate_assessments:
        for child_node_id in gate.child_node_ids:
            reverse_adjacency.setdefault(gate.output_node_id, set()).add(child_node_id)
    for relation in relations:
        if relation.relation_type in {"causes", "may_cause"}:
            reverse_adjacency.setdefault(relation.target_node_id, set()).add(
                relation.source_node_id
            )

    reachable = {top_event_id}
    pending = deque((top_event_id,))
    while pending:
        node_id = pending.popleft()
        for predecessor_id in reverse_adjacency.get(node_id, ()):
            if predecessor_id not in reachable:
                reachable.add(predecessor_id)
                pending.append(predecessor_id)

    return tuple(node.node_id for node in node_sequence if node.node_id not in reachable)


@dataclass(frozen=True)
class CandidateFtaTree:
    """A recursive, evidence-checked suggestion; never a production-ready tree."""

    extraction_result_id: str
    record_id: str
    fault_code: str | None
    source_text_sha256: str
    top_event_id: str
    nodes: tuple[CandidateFtaNode, ...]
    gate_assessments: tuple[CandidateFtaGateAssessment, ...] = ()
    relations: tuple[CandidateFtaRelation, ...] = ()
    cause_dispositions: tuple[CauseDisposition, ...] = ()
    locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = ()
    status: CandidateFtaStatus = CandidateFtaStatus.BLOCKED
    blockers: tuple[str, ...] = ()
    decision_reason: str = ""
    reviewer_provenance: str = "not_reviewed"
    confidence_semantics: str = "uncalibrated_model_estimate"
    human_reviewed: bool = field(default=False, init=False)
    fta_ready: bool = field(default=False, init=False)
    production_ready: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.extraction_result_id, "extraction_result_id"),
            (self.record_id, "record_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.fault_code is not None and not isinstance(self.fault_code, str):
            raise TypeError("fault_code must be a string or None")
        if (
            not isinstance(self.source_text_sha256, str)
            or len(self.source_text_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.source_text_sha256)
        ):
            raise ValueError("source_text_sha256 must be a lowercase SHA-256 digest")
        if not isinstance(self.top_event_id, str) or not self.top_event_id.strip():
            raise ValueError("top_event_id must be a non-empty string")
        nodes = tuple(self.nodes)
        gates = tuple(self.gate_assessments)
        relations = tuple(self.relations)
        cause_dispositions = tuple(self.cause_dispositions)
        locator_reviews = tuple(self.locator_reviews)
        if not nodes or not all(isinstance(item, CandidateFtaNode) for item in nodes):
            raise ValueError("nodes must contain CandidateFtaNode values")
        if not all(isinstance(item, CandidateFtaGateAssessment) for item in gates):
            raise TypeError("gate_assessments must contain CandidateFtaGateAssessment values")
        if not all(isinstance(item, CandidateFtaRelation) for item in relations):
            raise TypeError("relations must contain CandidateFtaRelation values")
        if not all(isinstance(item, CauseDisposition) for item in cause_dispositions):
            raise TypeError("cause_dispositions must contain CauseDisposition values")
        if not all(
            isinstance(item, EvidenceOccurrenceLocatorReview)
            for item in locator_reviews
        ):
            raise TypeError(
                "locator_reviews must contain EvidenceOccurrenceLocatorReview values"
            )
        if any(
            item.extraction_result_id != self.extraction_result_id
            or item.record_id != self.record_id
            or item.source_text_sha256 != self.source_text_sha256
            for item in locator_reviews
        ):
            raise ValueError("locator reviews must match the candidate tree identity")
        locator_targets = [
            (item.target_field, item.value_index) for item in locator_reviews
        ]
        if len(set(locator_targets)) != len(locator_targets):
            raise ValueError("candidate tree cannot contain duplicate locator targets")
        cause_indices = tuple(item.source_cause_index for item in cause_dispositions)
        if cause_indices != tuple(range(len(cause_dispositions))):
            raise ValueError("cause_dispositions must cover source causes in index order")
        node_ids = [node.node_id for node in nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("candidate node IDs must be unique")
        node_by_id = {node.node_id: node for node in nodes}
        eligible_cause_indices = set(candidate_source_indices(cause_dispositions))
        mapped_cause_indices = {
            cause_index
            for node in nodes
            for cause_index in node.source_cause_indices
        }
        if mapped_cause_indices and not cause_dispositions:
            if "cause_disposition_ledger_missing" not in self.blockers:
                raise ValueError("cause nodes require a complete cause disposition ledger")
        if any(index >= len(cause_dispositions) for index in mapped_cause_indices):
            raise ValueError("candidate nodes reference an unknown source cause index")
        observation_nodes_by_index: dict[int, list[CandidateFtaNode]] = {}
        for node in nodes:
            if node.node_type == "observation_candidate":
                if len(node.source_cause_indices) != 1:
                    raise ValueError("observation candidates must map to exactly one source cause")
                observation_nodes_by_index.setdefault(
                    node.source_cause_indices[0], []
                ).append(node)
        detached_observation_indices = {
            item.source_cause_index
            for item in cause_dispositions
            if item.disposition is FtaCauseDispositionKind.DETACHED_OBSERVATION
        }
        if set(observation_nodes_by_index) != detached_observation_indices:
            raise ValueError(
                "each detached observation disposition must have exactly one observation candidate"
            )
        if any(len(items) != 1 for items in observation_nodes_by_index.values()):
            raise ValueError("detached observations must not be duplicated as candidate nodes")
        for disposition in cause_dispositions:
            index = disposition.source_cause_index
            if disposition.disposition is FtaCauseDispositionKind.UNRESOLVED and (
                f"cause_disposition_unresolved:{index}" not in self.blockers
            ):
                raise ValueError("every unresolved cause disposition must block the tree")
            if (
                index in mapped_cause_indices
                and index not in eligible_cause_indices
                and f"cause_disposition_conflict:{index}" not in self.blockers
                and disposition.disposition
                is not FtaCauseDispositionKind.DETACHED_OBSERVATION
            ):
                raise ValueError("non-tree dispositions cannot be used as candidate nodes")
            if (
                disposition.disposition is FtaCauseDispositionKind.DETACHED_OBSERVATION
                and index in mapped_cause_indices
                and any(
                    node.node_type != "observation_candidate"
                    for node in nodes
                    if index in node.source_cause_indices
                )
            ):
                raise ValueError("detached observations cannot be mapped to FTA event nodes")
        if eligible_cause_indices - mapped_cause_indices and (
            "source_cause_mapping_incomplete" not in self.blockers
        ):
            raise ValueError("every FTA event candidate must map to a tree node")
        if self.top_event_id not in node_by_id:
            raise ValueError("top_event_id must reference a candidate node")
        if node_by_id[self.top_event_id].node_type != "top_event_candidate":
            raise ValueError("top_event_id must reference a top_event_candidate")
        blockers = tuple(self.blockers)
        if not all(isinstance(item, str) and item.strip() for item in blockers):
            raise TypeError("blockers must contain non-empty strings")
        gate_ids = [gate.gate_node_id for gate in gates]
        if len(set(gate_ids)) != len(gate_ids):
            raise ValueError("gate_node_ids must be unique within the candidate tree")
        for gate in gates:
            if gate.output_node_id not in node_by_id or any(
                child_id not in node_by_id for child_id in gate.child_node_ids
            ):
                raise ValueError("gate assessments must reference existing candidate nodes")
            scoped_node_ids = (gate.output_node_id, *gate.child_node_ids)
            uncovered = [
                evidence
                for node_id in scoped_node_ids
                for evidence in node_by_id[node_id].evidence
                if not any(
                    scope.source_id == evidence.source_id
                    and scope.start <= evidence.start
                    and evidence.end <= scope.end
                    for scope in gate.scope_evidence
                )
            ]
            if uncovered and "gate_scope_does_not_contain_all_node_evidence" not in gate.blockers:
                raise ValueError("gate scope evidence must contain all output/child evidence")
            if uncovered and not blockers:
                raise ValueError("an invalid gate scope must block the candidate tree")
            outside_gate = [
                evidence
                for evidence in gate.gate_evidence
                if not any(
                    scope.source_id == evidence.source_id
                    and scope.start <= evidence.start
                    and evidence.end <= scope.end
                    for scope in gate.scope_evidence
                )
            ]
            if outside_gate and "gate_evidence_outside_scope" not in gate.blockers:
                raise ValueError("gate evidence must be within its scope evidence")
            if outside_gate and not blockers:
                raise ValueError("gate evidence outside its scope must block the candidate tree")
        relation_ids = [relation.relation_id for relation in relations]
        if len(set(relation_ids)) != len(relation_ids):
            raise ValueError("relation IDs must be unique within the candidate tree")
        if any(
            relation.source_node_id not in node_by_id
            or relation.target_node_id not in node_by_id
            for relation in relations
        ):
            raise ValueError("candidate relations must reference existing nodes")
        observation_node_ids = {
            node.node_id for node in nodes if node.node_type == "observation_candidate"
        }
        if any(
            gate.output_node_id in observation_node_ids
            or observation_node_ids.intersection(gate.child_node_ids)
            for gate in gates
        ):
            raise ValueError("detached observation candidates cannot participate in gate scopes")
        if any(
            relation.source_node_id in observation_node_ids
            or relation.target_node_id in observation_node_ids
            for relation in relations
        ):
            raise ValueError("detached observation candidates cannot participate in relations")
        for relation in relations:
            endpoint_evidence = (
                *node_by_id[relation.source_node_id].evidence,
                *node_by_id[relation.target_node_id].evidence,
            )
            relation_index = relation.relation_id.rsplit(":", 1)[-1]
            has_scope_blocker = (
                f"relation_scope_does_not_contain_endpoints:{relation_index}" in blockers
            )
            if not endpoint_evidence and not has_scope_blocker:
                raise ValueError("candidate relation endpoints require source evidence")
            uncovered = [
                evidence
                for evidence in endpoint_evidence
                if not any(
                    scope.source_id == evidence.source_id
                    and scope.start <= evidence.start
                    and evidence.end <= scope.end
                    for scope in relation.scope_evidence
                )
            ]
            if uncovered and not has_scope_blocker:
                raise ValueError("relation scope evidence must contain both endpoint evidence")
            if uncovered and not blockers:
                raise ValueError("an invalid relation scope must block the candidate tree")
        disconnected_ids = find_disconnected_candidate_node_ids(
            self.top_event_id,
            nodes,
            gates,
            relations,
        )
        missing_connectivity_blockers = tuple(
            f"node_disconnected_from_top_event:{node_id}"
            for node_id in disconnected_ids
            if f"node_disconnected_from_top_event:{node_id}" not in blockers
        )
        if missing_connectivity_blockers:
            raise ValueError(
                "disconnected candidate nodes must block the whole tree and be retained "
                "with explicit blockers: "
                + ", ".join(missing_connectivity_blockers)
            )
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", CandidateFtaStatus(self.status))
            except ValueError as exc:
                raise ValueError("unsupported candidate FTA status") from exc
        elif not isinstance(self.status, CandidateFtaStatus):
            raise TypeError("status must be a CandidateFtaStatus")
        if self.status is CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW:
            if (
                any(not node.evidence for node in nodes)
                or not gates
                or blockers
            ):
                raise ValueError("reviewable candidate requires evidenced nodes and gate scopes")
        elif not blockers:
            raise ValueError("blocked candidate requires at least one blocker")

        if not isinstance(self.decision_reason, str):
            raise TypeError("decision_reason must be a string")
        if self.reviewer_provenance not in {
            "not_reviewed",
            "user_authorized_ai_expert_role",
        }:
            raise ValueError("unsupported reviewer_provenance")
        if self.confidence_semantics != "uncalibrated_model_estimate":
            raise ValueError("confidence_semantics must disclose uncalibrated estimates")

        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "gate_assessments", gates)
        object.__setattr__(self, "relations", relations)
        object.__setattr__(self, "cause_dispositions", cause_dispositions)
        object.__setattr__(self, "locator_reviews", locator_reviews)
        object.__setattr__(self, "blockers", blockers)

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-compatible artifact projection."""

        def evidence_payload(item: CandidateFtaEvidence) -> dict[str, object]:
            return {
                "citation_id": item.citation_id,
                "source_id": item.source_id,
                "quote": item.quote,
                "start": item.start,
                "end": item.end,
            }

        def node_payload(node: CandidateFtaNode) -> dict[str, object]:
            return {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "text": node.text,
                "evidence": [evidence_payload(item) for item in node.evidence],
                "source_cause_indices": list(node.source_cause_indices),
            }

        def gate_payload(gate: CandidateFtaGateAssessment) -> dict[str, object]:
            return {
                "gate_node_id": gate.gate_node_id,
                "output_node_id": gate.output_node_id,
                "child_node_ids": list(gate.child_node_ids),
                "scope_type": gate.scope_type,
                "gate": gate.gate,
                "gate_probabilities": dict(gate.gate_probabilities),
                "scope_evidence": [evidence_payload(item) for item in gate.scope_evidence],
                "gate_evidence": [evidence_payload(item) for item in gate.gate_evidence],
                "cause_set_complete": gate.cause_set_complete,
                "cause_set_leaf_normalized": gate.cause_set_leaf_normalized,
                "confidence_policy_id": gate.confidence_policy_id,
                "confidence_policy_basis": gate.confidence_policy_basis,
                "minimum_gate_probability": gate.minimum_gate_probability,
                "minimum_gate_margin": gate.minimum_gate_margin,
                "decision_reason": gate.decision_reason,
                "unknown_reason_code": (
                    gate.unknown_reason_code.value
                    if gate.unknown_reason_code is not None
                    else None
                ),
                "blockers": list(gate.blockers),
            }

        def relation_payload(relation: CandidateFtaRelation) -> dict[str, object]:
            return {
                "relation_id": relation.relation_id,
                "source_node_id": relation.source_node_id,
                "target_node_id": relation.target_node_id,
                "relation_type": relation.relation_type,
                "scope_evidence": [
                    evidence_payload(item) for item in relation.scope_evidence
                ],
                "evidence": [evidence_payload(item) for item in relation.evidence],
            }

        return {
            "artifact_type": "candidate_fta_tree",
            "artifact_version": "v7",
            "extraction_result_id": self.extraction_result_id,
            "record_id": self.record_id,
            "fault_code": self.fault_code,
            "source_text_sha256": self.source_text_sha256,
            "top_event_id": self.top_event_id,
            "nodes": [node_payload(item) for item in self.nodes],
            "cause_dispositions": [
                item.to_payload() for item in self.cause_dispositions
            ],
            "locator_reviews": [item.to_payload() for item in self.locator_reviews],
            "gate_assessments": [gate_payload(item) for item in self.gate_assessments],
            "unknown_gate_reason_counts": {
                reason.value: sum(
                    gate.unknown_reason_code is reason
                    for gate in self.gate_assessments
                )
                for reason in UnknownGateReasonCode
                if any(
                    gate.unknown_reason_code is reason
                    for gate in self.gate_assessments
                )
            },
            "relations": [relation_payload(item) for item in self.relations],
            "gate_confidence_semantics": self.confidence_semantics,
            "status": self.status.value,
            "blockers": list(self.blockers),
            "decision_reason": self.decision_reason,
            "reviewer_provenance": self.reviewer_provenance,
            "human_reviewed": self.human_reviewed,
            "fta_ready": self.fta_ready,
            "production_ready": self.production_ready,
        }


def normalize_blockers(values: Iterable[str]) -> tuple[str, ...]:
    """Deduplicate blocker codes while preserving their first-seen order."""

    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = [
    "CandidateFtaEvidence",
    "CandidateFtaGateAssessment",
    "UnknownGateReasonCode",
    "CandidateFtaGenerationResult",
    "CandidateFtaOutcomeDiagnostic",
    "CandidateFtaOutcomeStatus",
    "CandidateFtaNode",
    "CandidateFtaRelation",
    "CandidateFtaRecordOutcome",
    "CandidateFtaStatus",
    "CandidateFtaTree",
]
