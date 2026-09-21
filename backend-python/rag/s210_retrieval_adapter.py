"""Runtime S210 Retrieval Pipeline v1 adapter.

This module is the production-side adapter for the retrieval pipeline that was
validated under ``evaluation/quality_eval``.  It intentionally exposes only
the ``FaultRetriever`` port to the RAG service; the API layer does not know
about BGE, RRF, Alarm chunks, or Cross-Encoder details.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from contracts.rag_contract import RetrievedFault
from rag.rag_service import GoldFaultContextStore, RagServiceError


_FAULT_CODE_RE = re.compile(r"(?<![A-Z0-9])[AFN]\d{5}(?![A-Z0-9])", re.IGNORECASE)
_PARAMETER_RE = re.compile(r"(?<![A-Z0-9])[PR]\d{4,5}(?:\[\d+\])?(?![A-Z0-9])", re.IGNORECASE)
_RRF_K = 60
_FAULT_CODE_BOOST = 100.0
_PARAMETER_BOOST = 0.25


def _normalize_parameter(value: str) -> str:
    return re.sub(r"\[\d+\]$", "", str(value).strip().upper())


def _extract_fault_codes(text: str) -> set[str]:
    return {value.upper() for value in _FAULT_CODE_RE.findall(str(text))}


def _extract_parameters(text: str) -> set[str]:
    return {_normalize_parameter(value) for value in _PARAMETER_RE.findall(str(text))}


def _rank_from_scores(scores: Sequence[float], codes: Sequence[str]) -> list[str]:
    order = sorted(range(len(codes)), key=lambda index: (-float(scores[index]), codes[index]))
    return [str(codes[index]) for index in order]


def _rrf_scores(description_rank: Sequence[str], cause_rank: Sequence[str]) -> dict[str, float]:
    scores: defaultdict[str, float] = defaultdict(float)
    for rank, code in enumerate(description_rank, start=1):
        scores[str(code)] += 1.0 / (_RRF_K + rank)
    for rank, code in enumerate(cause_rank, start=1):
        scores[str(code)] += 1.0 / (_RRF_K + rank)
    return dict(scores)


def _rrf_rank(description_rank: Sequence[str], cause_rank: Sequence[str]) -> list[str]:
    scores = _rrf_scores(description_rank, cause_rank)
    return [code for code, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def _d2_rank(
    base_rank: Sequence[str],
    base_scores: dict[str, float],
    query: str,
    parameters_by_code: dict[str, set[str]],
) -> tuple[list[str], dict[str, Any]]:
    query_codes = _extract_fault_codes(query)
    query_parameters = _extract_parameters(query)
    positions = {code: index for index, code in enumerate(base_rank)}
    scored: dict[str, float] = {}
    matched_parameters: dict[str, list[str]] = {}
    exact_codes: list[str] = []
    for code in base_rank:
        params = sorted(query_parameters & parameters_by_code.get(code, set()))
        exact = code in query_codes
        if exact:
            exact_codes.append(code)
        matched_parameters[code] = params
        scored[code] = (
            base_scores[code]
            + (_FAULT_CODE_BOOST if exact else 0.0)
            + _PARAMETER_BOOST * len(params)
        )
    active_codes = set(exact_codes)
    ranked = sorted(
        base_rank,
        key=lambda code: (
            0 if code in active_codes else 1,
            -scored[code],
            positions[code],
            code,
        ),
    )
    return ranked, {
        "exact_fault_codes": sorted(exact_codes),
        "query_parameters": sorted(query_parameters),
        "parameter_matches_by_fault": {
            code: values for code, values in matched_parameters.items() if values
        },
        "scores": scored,
    }


def _merge_candidate_pool(
    d2_rank: Sequence[str],
    alarm_rank: Sequence[str],
    *,
    d2_top_k: int = 20,
    alarm_top_k: int = 10,
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for code in [*d2_rank[:d2_top_k], *alarm_rank[:alarm_top_k]]:
        code = str(code)
        if code not in seen:
            result.append(code)
            seen.add(code)
    return result


def _candidate_text(context: Any) -> str:
    return "\n".join(
        [
            f"Fault code: {context.fault_code}",
            f"Component: {context.component or '(none)'}",
            f"Related components: {', '.join(context.related_components) or '(none)'}",
            f"Description: {context.description}",
            f"Causes: {' | '.join(context.causes) or '(none)'}",
            f"Parameters: {', '.join(context.parameters) or '(none)'}",
            f"Alarm value section: {context.alarm_value or '(none)'}",
        ]
    )


class S210BgeRetriever:
    """Concrete BGE-M3 + Alarm + bge-reranker-v2-m3 retriever."""

    def __init__(
        self,
        gold_path: str | Path,
        *,
        embedding_model: str = "BAAI/bge-m3",
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        cache_dir: str | Path | None = None,
        device: str = "cpu",
        d2_top_k: int = 20,
        alarm_top_k: int = 10,
    ) -> None:
        if d2_top_k < 1 or alarm_top_k < 1:
            raise ValueError("candidate pool limits must be positive")
        try:
            import numpy as np
            from sentence_transformers import CrossEncoder, SentenceTransformer
        except ImportError as exc:  # pragma: no cover - environment gate
            raise RagServiceError(
                "retrieval_dependency_missing",
                "S210 Retrieval Pipeline 需要 sentence-transformers 和 numpy",
            ) from exc

        self._np = np
        self._device = device
        self._d2_top_k = d2_top_k
        self._alarm_top_k = alarm_top_k
        self._store = GoldFaultContextStore(gold_path)
        self._contexts = tuple(self._store.all_contexts())
        if not self._contexts:
            raise RagServiceError("gold_empty", "S210 Gold 没有可检索的故障记录")

        cache = str(cache_dir) if cache_dir else None
        self._embedding = SentenceTransformer(embedding_model, cache_folder=cache, device=device)
        self._reranker = CrossEncoder(
            reranker_model,
            max_length=512,
            device=device,
            cache_folder=cache,
        )
        self._codes = [context.fault_code for context in self._contexts]
        self._parameters_by_code = {
            context.fault_code: {_normalize_parameter(value) for value in context.parameters}
            for context in self._contexts
        }
        self._description_vectors = self._encode([context.description for context in self._contexts])
        self._cause_vectors = self._encode([
            " ".join(context.causes) for context in self._contexts
        ])
        self._alarm_vectors = self._encode([
            context.alarm_value for context in self._contexts
        ])

    def _encode(self, texts: Sequence[str]):
        return self._embedding.encode(
            list(texts),
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def retrieve(self, question: str, *, limit: int) -> Sequence[RetrievedFault]:
        if not isinstance(question, str) or not question.strip():
            raise RagServiceError("question_empty", "检索问题不能为空")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
            raise RagServiceError("retrieval_limit_invalid", "检索 limit 必须是 1 到 10 之间的整数")

        query_vector = self._encode([question])[0]
        description_scores = self._description_vectors @ query_vector
        cause_scores = self._cause_vectors @ query_vector
        alarm_scores = self._alarm_vectors @ query_vector
        description_rank = _rank_from_scores(description_scores, self._codes)
        cause_rank = _rank_from_scores(cause_scores, self._codes)
        alarm_rank = _rank_from_scores(alarm_scores, self._codes)
        base_scores = _rrf_scores(description_rank, cause_rank)
        d2_rank, d2_signals = _d2_rank(
            _rrf_rank(description_rank, cause_rank),
            base_scores,
            question,
            self._parameters_by_code,
        )
        candidate_pool = _merge_candidate_pool(
            d2_rank,
            alarm_rank,
            d2_top_k=self._d2_top_k,
            alarm_top_k=self._alarm_top_k,
        )
        contexts_by_code = {context.fault_code: context for context in self._contexts}
        pairs = [[question, _candidate_text(contexts_by_code[code])] for code in candidate_pool]
        scores = [float(value) for value in self._reranker.predict(pairs, batch_size=8, show_progress_bar=False)]
        score_by_code = dict(zip(candidate_pool, scores))
        raw_rank = sorted(candidate_pool, key=lambda code: (-score_by_code[code], code))
        exact_codes = set(d2_signals["exact_fault_codes"])
        guarded_rank = [code for code in raw_rank if code in exact_codes]
        guarded_rank.extend(code for code in raw_rank if code not in exact_codes)
        d2_positions = {code: index + 1 for index, code in enumerate(d2_rank)}
        alarm_positions = {code: index + 1 for index, code in enumerate(alarm_rank)}
        return tuple(
            RetrievedFault(
                fault_code=code,
                score=score_by_code[code],
                rank=index + 1,
                signals={
                    "d2_rank": d2_positions.get(code),
                    "alarm_rank": alarm_positions.get(code),
                    "candidate_pool_size": len(candidate_pool),
                    "exact_fault_codes": sorted(exact_codes),
                    "matched_parameters": d2_signals["parameter_matches_by_fault"].get(code, []),
                    "reranker_strategy": "guarded" if exact_codes else "raw",
                },
            )
            for index, code in enumerate(guarded_rank[:limit])
        )
