"""Persistence boundary for append-only FTA build attempts."""

from typing import Protocol

from contracts.build_contract import FaultTreeBuildAttempt


class BuildAttemptRepository(Protocol):
    def append_build_attempt(
        self,
        attempt: FaultTreeBuildAttempt,
    ) -> FaultTreeBuildAttempt:
        """Persist one build attempt without modifying previous attempts."""
        ...

    def get_build_attempt(self, attempt_id: str) -> FaultTreeBuildAttempt | None:
        """Load one build attempt by attempt ID."""
        ...

    def list_build_attempts(self, release_id: str) -> tuple[FaultTreeBuildAttempt, ...]:
        """Return all attempts for one release in insertion order."""
        ...


class InMemoryBuildAttemptRepository:
    """Process-local build-attempt repository used by isolated tests."""

    def __init__(self) -> None:
        self._build_attempts: dict[str, FaultTreeBuildAttempt] = {}

    def append_build_attempt(
        self,
        attempt: FaultTreeBuildAttempt,
    ) -> FaultTreeBuildAttempt:
        if not isinstance(attempt, FaultTreeBuildAttempt):
            raise TypeError("attempt must be a FaultTreeBuildAttempt")
        if attempt.attempt_id in self._build_attempts:
            raise ValueError("attempt_id has already been stored")
        self._build_attempts[attempt.attempt_id] = attempt
        return attempt

    def get_build_attempt(self, attempt_id: str) -> FaultTreeBuildAttempt | None:
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise ValueError("attempt_id must be a non-empty string")
        return self._build_attempts.get(attempt_id.strip())

    def list_build_attempts(self, release_id: str) -> tuple[FaultTreeBuildAttempt, ...]:
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("release_id must be a non-empty string")
        return tuple(
            attempt
            for attempt in self._build_attempts.values()
            if attempt.release_id == release_id.strip()
        )
