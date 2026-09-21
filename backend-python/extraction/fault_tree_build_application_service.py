"""Application orchestration for building a persisted release projection."""

from typing import Protocol

from extraction.build_attempt_repository import BuildAttemptRepository
from contracts.build_contract import FaultTreeBuildAttempt
from contracts.release_contract import ReleasedExtractionResult
from extraction.release_repository import ReleaseRepository


class ReleaseNotFoundError(ValueError):
    """Raised when a build request references no persisted release."""


class FaultTreeBuildPort(Protocol):
    """Minimal build capability required by the application orchestration."""

    def build(
        self,
        release: ReleasedExtractionResult,
        top_event: str,
    ) -> FaultTreeBuildAttempt:
        ...


class FaultTreeBuildApplicationService:
    """Load releases and delegate tree construction without owning tree rules."""

    def __init__(
        self,
        release_repository: ReleaseRepository,
        build_attempt_repository: BuildAttemptRepository,
        build_service: FaultTreeBuildPort,
    ) -> None:
        self._release_repository = release_repository
        self._build_attempt_repository = build_attempt_repository
        self._build_service = build_service

    def build(
        self,
        release_id: str,
        top_event: str,
    ) -> FaultTreeBuildAttempt:
        release = self._get_release(release_id)
        return self._build_service.build(release, top_event)

    def list_attempts(self, release_id: str) -> tuple[FaultTreeBuildAttempt, ...]:
        self._get_release(release_id)
        return self._build_attempt_repository.list_build_attempts(release_id)

    def _get_release(self, release_id: str) -> ReleasedExtractionResult:
        release = self._release_repository.get_release(release_id)
        if release is None:
            raise ReleaseNotFoundError("release not found")
        return release
