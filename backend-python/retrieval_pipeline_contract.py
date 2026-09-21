"""Domain-neutral candidate fusion contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CandidateHit:
    """A hit from one retrieval channel, usually representing a child chunk."""

    entity_id: str
    chunk_id: str
    channel: str
    score: float | None = None
    rank: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EntityCandidate:
    """A parent-level candidate after child hits are deduplicated."""

    entity_id: str
    chunk_ids: tuple[str, ...]
    channels: tuple[str, ...]
    best_score: float | None = None
    best_rank: int | None = None
    signals: Mapping[str, Any] = field(default_factory=dict)


class CandidateUnion:
    """Union channel hits and aggregate them by common entity identity."""

    def merge(
        self,
        channel_hits: Mapping[str, Sequence[CandidateHit]],
        *,
        per_channel_limit: int | Mapping[str, int] | None = None,
    ) -> tuple[EntityCandidate, ...]:
        grouped: dict[str, list[CandidateHit]] = {}
        for channel, hits in channel_hits.items():
            limit = self._limit_for(channel, per_channel_limit)
            for hit in list(hits)[:limit]:
                entity_id = str(hit.entity_id or "").strip()
                if not entity_id:
                    continue
                grouped.setdefault(entity_id, []).append(
                    CandidateHit(
                        entity_id=entity_id,
                        chunk_id=str(hit.chunk_id or ""),
                        channel=str(hit.channel or channel),
                        score=hit.score,
                        rank=hit.rank,
                        metadata=hit.metadata,
                    )
                )

        candidates: list[EntityCandidate] = []
        for entity_id, hits in grouped.items():
            ordered = sorted(
                hits,
                key=lambda hit: (
                    -(float(hit.score) if hit.score is not None else float("-inf")),
                    hit.rank if hit.rank is not None else 10**9,
                    hit.channel,
                    hit.chunk_id,
                ),
            )
            best = ordered[0]
            candidates.append(
                EntityCandidate(
                    entity_id=entity_id,
                    chunk_ids=tuple(dict.fromkeys(hit.chunk_id for hit in ordered if hit.chunk_id)),
                    channels=tuple(dict.fromkeys(hit.channel for hit in ordered if hit.channel)),
                    best_score=best.score,
                    best_rank=best.rank,
                    signals={
                        "hit_count": len(ordered),
                        "channels": tuple(dict.fromkeys(hit.channel for hit in ordered)),
                        "scores_by_channel": {
                            channel: max(
                                (
                                    float(hit.score)
                                    for hit in ordered
                                    if hit.channel == channel and hit.score is not None
                                ),
                                default=None,
                            )
                            for channel in dict.fromkeys(hit.channel for hit in ordered)
                        },
                    },
                )
            )
        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    -(float(candidate.best_score) if candidate.best_score is not None else float("-inf")),
                    candidate.best_rank if candidate.best_rank is not None else 10**9,
                    candidate.entity_id,
                ),
            )
        )

    @staticmethod
    def _limit_for(
        channel: str,
        limit: int | Mapping[str, int] | None,
    ) -> int | None:
        if limit is None:
            return None
        if isinstance(limit, int):
            if limit < 1:
                raise ValueError("per_channel_limit must be positive")
            return limit
        value = limit.get(channel)
        if value is None:
            return None
        if value < 1:
            raise ValueError("per-channel limit must be positive")
        return value
