"""Provider-neutral contracts for the evidence-bound fault RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class RetrievedFault:
    """A candidate returned by any retrieval implementation."""

    fault_code: str
    score: float | None = None
    rank: int | None = None
    signals: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceCitation:
    """A source span that the answer is allowed to cite."""

    citation_id: str
    field: str
    quote: str
    source_id: str
    source_file: str
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True)
class FaultContext:
    """Complete fault entity context loaded after retrieval."""

    fault_code: str
    description: str
    component: str = ""
    related_components: tuple[str, ...] = ()
    causes: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    alarm_value: str = ""
    remedy: str = ""
    evidence: tuple[EvidenceCitation, ...] = ()
    source_file: str = ""
    raw_text: str = ""


@dataclass(frozen=True)
class GeneratedAnswer:
    """Model output plus the evidence citations it declared."""

    text: str
    citations: tuple[str, ...] = ()
    model: str = ""


@dataclass(frozen=True)
class RagResponse:
    """Stable service response consumed by a future API adapter."""

    question: str
    answer: GeneratedAnswer
    retrieved: tuple[RetrievedFault, ...]
    contexts: tuple[FaultContext, ...]
    evidence_status: str


class FaultRetriever(Protocol):
    """Retrieval port; BGE/D2/Alarm/Reranker implementations stay outside it."""

    def retrieve(self, question: str, *, limit: int) -> Sequence[RetrievedFault]:
        ...


class FaultContextLoader(Protocol):
    """Loads full parent fault entities after candidate ranking."""

    def load(self, fault_codes: Sequence[str]) -> Sequence[FaultContext]:
        ...


class AnswerGenerator(Protocol):
    """Generation port; model provider and prompt policy stay replaceable."""

    def generate(
        self,
        question: str,
        contexts: Sequence[FaultContext],
    ) -> GeneratedAnswer:
        ...
