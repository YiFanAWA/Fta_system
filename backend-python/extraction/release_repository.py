"""Persistence boundary for released extraction projections."""

from typing import Protocol

from contracts.release_contract import ReleasedExtractionResult


class ReleaseRepository(Protocol):
    def save_release(self, release: ReleasedExtractionResult) -> ReleasedExtractionResult:
        """Persist one immutable release projection."""
        ...

    def get_release(self, release_id: str) -> ReleasedExtractionResult | None:
        """Load one release projection by release ID."""
        ...


class InMemoryReleaseRepository:
    """Process-local release repository used by isolated tests."""

    def __init__(self) -> None:
        self._releases: dict[str, ReleasedExtractionResult] = {}

    def save_release(self, release: ReleasedExtractionResult) -> ReleasedExtractionResult:
        if not isinstance(release, ReleasedExtractionResult):
            raise TypeError("release must be a ReleasedExtractionResult")
        if release.release_id in self._releases:
            raise ValueError("release_id has already been stored")
        self._releases[release.release_id] = release
        return release

    def get_release(self, release_id: str) -> ReleasedExtractionResult | None:
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("release_id must be a non-empty string")
        return self._releases.get(release_id.strip())
