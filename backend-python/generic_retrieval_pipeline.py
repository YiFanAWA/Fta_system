"""Domain-neutral parent loading and retrieval orchestration.

This module deliberately contains no Siemens, manufacturer, or manual-specific
rules.  A domain adapter provides retrieval roles; this module owns vector
channel ranking, exact signal fusion, parent-level candidate union, and the
generic reranker document contract.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping, Sequence

from common_fault_schema import FaultEntity
from domain_adapter_contract import (
    DomainAdapter,
    ExactFieldMatches,
    RetrievalFieldValues,
)
from retrieval_pipeline_contract import CandidateHit, CandidateUnion


@dataclass(frozen=True)
class GenericRetrievalConfig:
    """Stable knobs for the first generic retrieval profile."""

    rrf_k: int = 60
    identifier_boost: float = 100.0
    parameter_boost: float = 0.25
    main_top_k: int = 20
    auxiliary_top_k: int = 10

    def validate(self) -> None:
        if self.rrf_k < 1:
            raise ValueError("rrf_k must be positive")
        if self.main_top_k < 1 or self.auxiliary_top_k < 1:
            raise ValueError("candidate pool limits must be positive")


@dataclass(frozen=True)
class ParentEntityLoader:
    """Immutable in-memory parent entity store keyed by common entity_id."""

    _entities_by_id: Mapping[str, FaultEntity]

    @classmethod
    def from_entities(cls, entities: Sequence[FaultEntity]) -> "ParentEntityLoader":
        values: dict[str, FaultEntity] = {}
        for entity in entities:
            entity.validate()
            if entity.entity_id in values:
                raise ValueError(f"duplicate parent entity_id: {entity.entity_id}")
            values[entity.entity_id] = entity
        if not values:
            raise ValueError("parent entity loader cannot be empty")
        return cls(values)

    def load(self, entity_id: str) -> FaultEntity:
        key = str(entity_id or "").strip()
        try:
            return self._entities_by_id[key]
        except KeyError as exc:
            raise KeyError(f"unknown parent entity_id: {key}") from exc

    def load_many(self, entity_ids: Sequence[str]) -> tuple[FaultEntity, ...]:
        return tuple(self.load(entity_id) for entity_id in entity_ids)

    def all(self) -> tuple[FaultEntity, ...]:
        return tuple(self._entities_by_id.values())


@dataclass(frozen=True)
class RerankerDocument:
    """Reranker text plus parent identity metadata."""

    entity_id: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class GenericRerankerDocumentBuilder:
    """Build a parent-scoped reranker document from adapter-declared fields."""

    def build(
        self,
        entity: FaultEntity,
        values: RetrievalFieldValues,
    ) -> RerankerDocument:
        lines: list[str] = []
        for label, raw_values in values.reranker_fields:
            normalized = tuple(str(value).strip() for value in raw_values if str(value).strip())
            lines.append(f"{label}: {', '.join(normalized) if normalized else '(none)'}")
        return RerankerDocument(
            entity_id=entity.entity_id,
            text="\n".join(lines),
            metadata={
                "entity_id": entity.entity_id,
                "fault_code": entity.fault_code,
                **dict(values.metadata),
            },
        )


@dataclass(frozen=True)
class GenericRetrievalOutput:
    """Inspectable parent-level output used by parity tests and diagnostics."""

    query: str
    exact_fields: ExactFieldMatches
    primary_rank: tuple[str, ...]
    cause_rank: tuple[str, ...]
    auxiliary_rank: tuple[str, ...]
    rrf_rank: tuple[str, ...]
    main_rank: tuple[str, ...]
    candidate_pool: tuple[str, ...]
    raw_reranker_rank: tuple[str, ...]
    guarded_rank: tuple[str, ...]
    matched_parameters_by_entity: Mapping[str, tuple[str, ...]]
    exact_identifier_entities: tuple[str, ...]
    reranker_scores: Mapping[str, float]


class GenericFaultRetrievalPipeline:
    """Run role-based dense retrieval, exact fusion, union, and reranking."""

    def __init__(
        self,
        adapter: DomainAdapter,
        entities: Sequence[FaultEntity],
        encode: Callable[[Sequence[str]], Any],
        rerank: Callable[[Sequence[Sequence[str]]], Sequence[float]] | None = None,
        *,
        config: GenericRetrievalConfig | None = None,
        document_builder: GenericRerankerDocumentBuilder | None = None,
    ) -> None:
        self._adapter = adapter
        self._loader = ParentEntityLoader.from_entities(entities)
        self._entities = self._loader.all()
        self._encode = encode
        self._rerank = rerank
        self._config = config or GenericRetrievalConfig()
        self._config.validate()
        self._document_builder = document_builder or GenericRerankerDocumentBuilder()
        self._values = {
            entity.entity_id: adapter.retrieval_field_values(entity)
            for entity in self._entities
        }
        self._ids = tuple(entity.entity_id for entity in self._entities)
        self._primary_vectors = self._encode(
            [self._values[entity_id].semantic_primary for entity_id in self._ids]
        )
        self._cause_vectors = self._encode(
            [self._values[entity_id].semantic_cause for entity_id in self._ids]
        )
        self._auxiliary_vectors = self._encode(
            [self._values[entity_id].semantic_auxiliary for entity_id in self._ids]
        )
        self._documents = {
            entity.entity_id: self._document_builder.build(entity, self._values[entity.entity_id])
            for entity in self._entities
        }
        self._parameter_values = {
            entity_id: {
                self._normalize_exact(value)
                for value in self._values[entity_id].exact_parameters
                if self._normalize_exact(value)
            }
            for entity_id in self._ids
        }

    @property
    def parent_loader(self) -> ParentEntityLoader:
        return self._loader

    @property
    def config(self) -> GenericRetrievalConfig:
        """Expose the immutable retrieval profile for diagnostics."""

        return self._config

    @property
    def reranker_documents(self) -> Mapping[str, RerankerDocument]:
        return self._documents

    def retrieve(self, question: str) -> GenericRetrievalOutput:
        text = str(question or "").strip()
        if not text:
            raise ValueError("question cannot be empty")
        query_vector = self._encode([text])[0]
        return self._retrieve_with_vector(text, query_vector)

    def retrieve_many(self, questions: Sequence[str]) -> tuple[GenericRetrievalOutput, ...]:
        """Retrieve a batch using one encoder call, preserving batch semantics."""

        texts = tuple(str(question or "").strip() for question in questions)
        if any(not text for text in texts):
            raise ValueError("questions cannot contain empty values")
        if not texts:
            return ()
        vectors = self._encode(texts)
        preliminary = tuple(
            self._retrieve_with_vector(text, vector, apply_rerank=False)
            for text, vector in zip(texts, vectors)
        )
        if self._rerank is None:
            return preliminary

        pairs = [
            [text, self._documents[entity_id].text]
            for output in preliminary
            for text in (output.query,)
            for entity_id in output.candidate_pool
        ]
        scores = [float(value) for value in self._rerank(pairs)]
        expected = sum(len(output.candidate_pool) for output in preliminary)
        if len(scores) != expected:
            raise ValueError("reranker returned a score count different from batched candidates")
        completed: list[GenericRetrievalOutput] = []
        cursor = 0
        for output in preliminary:
            pool = list(output.candidate_pool)
            local_scores = scores[cursor : cursor + len(pool)]
            cursor += len(pool)
            score_by_entity = dict(zip(pool, local_scores))
            raw_rank = sorted(pool, key=lambda entity_id: (-score_by_entity[entity_id], entity_id))
            exact_set = set(output.exact_identifier_entities)
            guarded_rank = tuple(
                [entity_id for entity_id in raw_rank if entity_id in exact_set]
                + [entity_id for entity_id in raw_rank if entity_id not in exact_set]
            )
            completed.append(
                replace(
                    output,
                    raw_reranker_rank=tuple(raw_rank),
                    guarded_rank=guarded_rank,
                    reranker_scores=score_by_entity,
                )
            )
        return tuple(completed)

    def _retrieve_with_vector(
        self,
        text: str,
        query_vector: Any,
        *,
        apply_rerank: bool = True,
    ) -> GenericRetrievalOutput:
        primary_rank = self._rank(self._primary_vectors @ query_vector)
        cause_rank = self._rank(self._cause_vectors @ query_vector)
        auxiliary_rank = self._rank(self._auxiliary_vectors @ query_vector)
        main_scores = self._rrf_scores(primary_rank, cause_rank)
        base_rank = self._rrf_rank(main_scores)
        main_rank = self._exact_rank(base_rank, main_scores, text)
        exact_fields = self._adapter.extract_exact_fields(text)
        exact_identifier_entities = tuple(
            entity_id
            for entity_id in self._ids
            if self._normalize_exact(self._values[entity_id].exact_identifier)
            in {self._normalize_exact(value) for value in exact_fields.fault_codes}
        )
        matched_parameters = {
            entity_id: tuple(
                sorted(
                    {
                        value
                        for value in exact_fields.parameters
                        if self._normalize_exact(value) in self._parameter_values[entity_id]
                    }
                )
            )
            for entity_id in self._ids
        }
        candidate_pool = self._stable_union(
            main_rank[: self._config.main_top_k],
            auxiliary_rank[: self._config.auxiliary_top_k],
        )
        if apply_rerank:
            raw_rank, reranker_scores = self._rerank_candidates(text, candidate_pool)
        else:
            raw_rank = list(candidate_pool)
            reranker_scores = {entity_id: 0.0 for entity_id in candidate_pool}
        exact_set = set(exact_identifier_entities)
        guarded_rank = tuple(
            [entity_id for entity_id in raw_rank if entity_id in exact_set]
            + [entity_id for entity_id in raw_rank if entity_id not in exact_set]
        )
        return GenericRetrievalOutput(
            query=text,
            exact_fields=exact_fields,
            primary_rank=tuple(primary_rank),
            cause_rank=tuple(cause_rank),
            auxiliary_rank=tuple(auxiliary_rank),
            rrf_rank=tuple(base_rank),
            main_rank=tuple(main_rank),
            candidate_pool=tuple(candidate_pool),
            raw_reranker_rank=tuple(raw_rank),
            guarded_rank=guarded_rank,
            matched_parameters_by_entity={
                entity_id: values
                for entity_id, values in matched_parameters.items()
                if values
            },
            exact_identifier_entities=exact_identifier_entities,
            reranker_scores=reranker_scores,
        )

    def _rank(self, scores: Sequence[float]) -> list[str]:
        return [
            entity_id
            for _, entity_id in sorted(
                zip(scores, self._ids),
                key=lambda item: (-float(item[0]), item[1]),
            )
        ]

    def _rrf_scores(self, primary_rank: Sequence[str], cause_rank: Sequence[str]) -> dict[str, float]:
        scores: defaultdict[str, float] = defaultdict(float)
        for rank, entity_id in enumerate(primary_rank, start=1):
            scores[entity_id] += 1.0 / (self._config.rrf_k + rank)
        for rank, entity_id in enumerate(cause_rank, start=1):
            scores[entity_id] += 1.0 / (self._config.rrf_k + rank)
        return dict(scores)

    def _rrf_rank(self, scores: Mapping[str, float]) -> list[str]:
        return [
            entity_id
            for entity_id, _ in sorted(
                scores.items(), key=lambda item: (-float(item[1]), item[0])
            )
        ]

    def _exact_rank(
        self,
        base_rank: Sequence[str],
        base_scores: Mapping[str, float],
        question: str,
    ) -> list[str]:
        exact_fields = self._adapter.extract_exact_fields(question)
        query_ids = {self._normalize_exact(value) for value in exact_fields.fault_codes}
        query_parameters = {self._normalize_exact(value) for value in exact_fields.parameters}
        positions = {entity_id: index for index, entity_id in enumerate(base_rank)}
        scored: dict[str, float] = {}
        exact_entities: set[str] = set()
        for entity_id in base_rank:
            identifier = self._normalize_exact(self._values[entity_id].exact_identifier)
            exact = bool(identifier and identifier in query_ids)
            if exact:
                exact_entities.add(entity_id)
            parameter_count = len(query_parameters & self._parameter_values[entity_id])
            scored[entity_id] = (
                float(base_scores[entity_id])
                + (self._config.identifier_boost if exact else 0.0)
                + self._config.parameter_boost * parameter_count
            )
        return sorted(
            base_rank,
            key=lambda entity_id: (
                0 if entity_id in exact_entities else 1,
                -scored[entity_id],
                positions[entity_id],
                entity_id,
            ),
        )

    def _rerank_candidates(
        self,
        question: str,
        candidate_pool: Sequence[str],
    ) -> tuple[list[str], dict[str, float]]:
        if self._rerank is None:
            return list(candidate_pool), {entity_id: 0.0 for entity_id in candidate_pool}
        pairs = [
            [question, self._documents[entity_id].text]
            for entity_id in candidate_pool
        ]
        scores = [float(value) for value in self._rerank(pairs)]
        if len(scores) != len(candidate_pool):
            raise ValueError("reranker returned a score count different from candidates")
        score_by_entity = dict(zip(candidate_pool, scores))
        ranked = sorted(candidate_pool, key=lambda entity_id: (-score_by_entity[entity_id], entity_id))
        return ranked, score_by_entity

    @staticmethod
    def _stable_union(*rankings: Sequence[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for ranking in rankings:
            for entity_id in ranking:
                if entity_id not in seen:
                    seen.add(entity_id)
                    result.append(entity_id)
        return result

    @staticmethod
    def _normalize_exact(value: Any) -> str:
        return str(value or "").strip().upper()
