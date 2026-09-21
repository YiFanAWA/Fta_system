"""Contracts implemented by domain-specific fault adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from contracts.common_fault_schema import FaultEntity


@dataclass(frozen=True)
class RetrievalChunk:
    """A child retrieval unit that always points back to one parent entity."""

    chunk_id: str
    entity_id: str
    kind: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExactFieldMatches:
    """Structured identifiers extracted from a user query."""

    fault_codes: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    components: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalFieldValues:
    """Domain-neutral retrieval planes exposed by an adapter.

    The generic retriever only understands retrieval roles.  Labels used in
    the reranker document are supplied by the adapter so a domain can retain
    terminology without putting domain rules into the generic pipeline.
    """

    semantic_primary: str = ""
    semantic_cause: str = ""
    semantic_auxiliary: str = ""
    exact_identifier: str = ""
    exact_parameters: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    reranker_fields: tuple[tuple[str, tuple[str, ...]], ...] = ()


class DomainAdapter(Protocol):
    """Boundary between a source domain and the common retrieval contracts."""

    def parse_source(self, payload: dict[str, Any]) -> Sequence[FaultEntity]:
        ...

    def normalize_entity(self, entity: FaultEntity) -> FaultEntity:
        ...

    def build_retrieval_chunks(
        self, entities: Sequence[FaultEntity]
    ) -> Sequence[RetrievalChunk]:
        ...

    def extract_exact_fields(self, question: str) -> ExactFieldMatches:
        ...

    def retrieval_field_values(self, entity: FaultEntity) -> RetrievalFieldValues:
        ...
