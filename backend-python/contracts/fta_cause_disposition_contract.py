"""Auditable semantic disposition of extracted causes for candidate FTA use."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from contracts.evidence_locator_review_contract import (
    EvidenceOccurrenceLocatorReview,
)


HOST_DISPOSITION_NORMALIZATION_PROVENANCE = "fta_cause_disposition_host_policy"


class CauseSemanticRole(str, Enum):
    CAUSAL_CONDITION = "causal_condition"
    DIAGNOSTIC_MAPPING = "diagnostic_mapping"
    FAULT_VALUE_MODE = "fault_value_mode"
    CONSEQUENCE = "consequence"
    STATE = "state"
    CAUSAL_SUMMARY = "causal_summary"
    REMEDY = "remedy"
    OTHER = "other"
    MIXED_UNRESOLVED = "mixed_unresolved"


class FtaCauseDispositionKind(str, Enum):
    FTA_EVENT_CANDIDATE = "fta_event_candidate"
    DETACHED_OBSERVATION = "detached_observation"
    RELATION_ONLY = "relation_only"
    EXCLUDE_FROM_TREE = "exclude_from_tree"
    UNRESOLVED = "unresolved"


class CauseDispositionReasonCode(str, Enum):
    DIRECT_CAUSAL_OR_CONDITION_STATEMENT = "direct_causal_or_condition_statement"
    DIAGNOSTIC_MAPPING_WITHOUT_INSTANCE_EVIDENCE = "diagnostic_mapping_without_instance_evidence"
    FAULT_VALUE_MODE_WITHOUT_INSTANCE_EVIDENCE = "fault_value_mode_without_instance_evidence"
    DOWNSTREAM_CONSEQUENCE = "downstream_consequence"
    REMEDY_ACTION = "remedy_action"
    SUMMARY_NOT_INDEPENDENT_EVENT = "summary_not_independent_event"
    DESCRIPTIVE_ASSOCIATION = "descriptive_association"
    MIXED_SEMANTICS = "mixed_semantics"
    SEMANTIC_ROLE_UNCERTAIN = "semantic_role_uncertain"
    EVIDENCE_MISSING_OR_AMBIGUOUS = "evidence_missing_or_ambiguous"
    CLASSIFICATION_MISSING = "classification_missing"
    SEMANTIC_DISPOSITION_CONFLICT = "semantic_disposition_conflict"
    OTHER_NON_CAUSAL_CONTENT = "other_non_causal_content"


@dataclass(frozen=True)
class CauseDispositionEvidence:
    """A uniquely bound source quotation supporting one disposition proposal."""

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
class CauseDisposition:
    """One explicit, review-only decision for an original cause index."""

    source_cause_index: int
    source_cause_text: str
    semantic_role: CauseSemanticRole
    proposed_disposition: FtaCauseDispositionKind
    disposition: FtaCauseDispositionKind
    reason_code: CauseDispositionReasonCode
    rationale: str
    evidence: tuple[CauseDispositionEvidence, ...] = ()
    review_status: str = "ai_proposed"
    provenance: str = "fta_cause_disposition_model"

    def __post_init__(self) -> None:
        if isinstance(self.source_cause_index, bool) or not isinstance(
            self.source_cause_index, int
        ):
            raise TypeError("source_cause_index must be an integer")
        if self.source_cause_index < 0:
            raise ValueError("source_cause_index must be non-negative")
        if not isinstance(self.source_cause_text, str) or not self.source_cause_text.strip():
            raise ValueError("source_cause_text must be a non-empty string")

        for attribute, enum_type, label in (
            ("semantic_role", CauseSemanticRole, "semantic_role"),
            ("proposed_disposition", FtaCauseDispositionKind, "proposed_disposition"),
            ("disposition", FtaCauseDispositionKind, "disposition"),
            ("reason_code", CauseDispositionReasonCode, "reason_code"),
        ):
            value = getattr(self, attribute)
            if isinstance(value, str):
                try:
                    object.__setattr__(self, attribute, enum_type(value))
                except ValueError as exc:
                    raise ValueError(f"unsupported {label}: {value}") from exc
            elif not isinstance(value, enum_type):
                raise TypeError(f"{label} must be a {enum_type.__name__}")

        if self.disposition is not FtaCauseDispositionKind.UNRESOLVED:
            if self.proposed_disposition is not self.disposition:
                is_detached_observation_normalization = (
                    self.proposed_disposition is FtaCauseDispositionKind.RELATION_ONLY
                    and self.disposition is FtaCauseDispositionKind.DETACHED_OBSERVATION
                    and self.semantic_role is CauseSemanticRole.STATE
                    and self.reason_code is CauseDispositionReasonCode.DESCRIPTIVE_ASSOCIATION
                    and self.provenance == HOST_DISPOSITION_NORMALIZATION_PROVENANCE
                )
                if not is_detached_observation_normalization:
                    raise ValueError(
                        "only unresolved or the explicit descriptive-association host normalization "
                        "may override the model disposition"
                    )
            if not self.evidence:
                raise ValueError("a resolved disposition requires source evidence")

        if self.semantic_role is CauseSemanticRole.MIXED_UNRESOLVED and (
            self.disposition is not FtaCauseDispositionKind.UNRESOLVED
        ):
            raise ValueError("mixed_unresolved role must have unresolved disposition")

        if self.disposition is FtaCauseDispositionKind.DETACHED_OBSERVATION and (
            self.semantic_role is not CauseSemanticRole.STATE
            or self.reason_code is not CauseDispositionReasonCode.DESCRIPTIVE_ASSOCIATION
        ):
            raise ValueError(
                "detached observations require state role and descriptive-association evidence"
            )

        tree_roles = {
            CauseSemanticRole.CAUSAL_CONDITION,
            CauseSemanticRole.STATE,
        }
        if (
            self.disposition is FtaCauseDispositionKind.FTA_EVENT_CANDIDATE
            and self.semantic_role not in tree_roles
        ):
            raise ValueError("only causal_condition/state may become tree event candidates")

        non_tree_only_roles = {
            CauseSemanticRole.DIAGNOSTIC_MAPPING,
            CauseSemanticRole.FAULT_VALUE_MODE,
            CauseSemanticRole.CONSEQUENCE,
            CauseSemanticRole.CAUSAL_SUMMARY,
            CauseSemanticRole.REMEDY,
            CauseSemanticRole.OTHER,
        }
        if (
            self.semantic_role in non_tree_only_roles
            and self.disposition is FtaCauseDispositionKind.FTA_EVENT_CANDIDATE
        ):
            raise ValueError("non-causal semantic roles cannot be tree event candidates")

        evidence = tuple(self.evidence)
        if not all(isinstance(item, CauseDispositionEvidence) for item in evidence):
            raise TypeError("evidence must contain CauseDispositionEvidence values")
        if len({item.citation_id for item in evidence}) != len(evidence):
            raise ValueError("cause disposition evidence citation IDs must be unique")
        for value, name in (
            (self.rationale, "rationale"),
            (self.review_status, "review_status"),
            (self.provenance, "provenance"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.review_status != "ai_proposed":
            raise ValueError("this preview contract only represents ai_proposed decisions")
        object.__setattr__(self, "evidence", evidence)

    def to_payload(self) -> dict[str, object]:
        return {
            "source_cause_index": self.source_cause_index,
            "source_cause_text": self.source_cause_text,
            "semantic_role": self.semantic_role.value,
            "proposed_disposition": self.proposed_disposition.value,
            "disposition": self.disposition.value,
            "reason_code": self.reason_code.value,
            "rationale": self.rationale,
            "evidence": [
                {
                    "citation_id": item.citation_id,
                    "source_id": item.source_id,
                    "quote": item.quote,
                    "start": item.start,
                    "end": item.end,
                }
                for item in self.evidence
            ],
            "review_status": self.review_status,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class FtaCauseDispositionBatch:
    """Complete disposition ledger for every cause in one extracted record."""

    extraction_result_id: str
    record_id: str
    source_text_sha256: str
    dispositions: tuple[CauseDisposition, ...]
    locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = ()

    def __post_init__(self) -> None:
        for value, name in (
            (self.extraction_result_id, "extraction_result_id"),
            (self.record_id, "record_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if (
            not isinstance(self.source_text_sha256, str)
            or len(self.source_text_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.source_text_sha256)
        ):
            raise ValueError("source_text_sha256 must be a lowercase SHA-256 digest")
        dispositions = tuple(self.dispositions)
        if not all(isinstance(item, CauseDisposition) for item in dispositions):
            raise TypeError("dispositions must contain CauseDisposition values")
        indices = tuple(item.source_cause_index for item in dispositions)
        if indices != tuple(range(len(dispositions))):
            raise ValueError("dispositions must cover every source cause index exactly once in order")
        if any(
            any(item.source_id != "input_text" for item in disposition.evidence)
            for disposition in dispositions
        ):
            raise ValueError("cause disposition evidence must reference input_text")
        locator_reviews = tuple(self.locator_reviews)
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
            raise ValueError("locator reviews must match the disposition batch identity")
        object.__setattr__(self, "dispositions", dispositions)
        object.__setattr__(self, "locator_reviews", locator_reviews)

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_type": "fta_cause_disposition_batch",
            "artifact_version": "v3",
            "extraction_result_id": self.extraction_result_id,
            "record_id": self.record_id,
            "source_text_sha256": self.source_text_sha256,
            "review_status": "ai_proposed",
            "dispositions": [item.to_payload() for item in self.dispositions],
            "locator_reviews": [item.to_payload() for item in self.locator_reviews],
        }


def candidate_source_indices(
    dispositions: Iterable[CauseDisposition],
) -> tuple[int, ...]:
    """Return the source indices admitted as review-only FTA event candidates."""

    return tuple(
        item.source_cause_index
        for item in dispositions
        if item.disposition is FtaCauseDispositionKind.FTA_EVENT_CANDIDATE
    )


__all__ = [
    "CauseDispositionEvidence",
    "CauseDispositionReasonCode",
    "CauseSemanticRole",
    "FtaCauseDispositionKind",
    "FtaCauseDispositionBatch",
    "CauseDisposition",
    "candidate_source_indices",
]
