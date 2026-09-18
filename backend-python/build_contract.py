"""Contracts for downstream FTA tree-building attempts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class BuildAttemptStatus(str, Enum):
    """Outcome of one immutable FTA tree-building attempt."""

    SUCCEEDED = "succeeded"
    REJECTED = "rejected"


@dataclass(frozen=True)
class FaultTreeBuildAttempt:
    """One append-only attempt to build a tree from a released projection."""

    release_id: str
    source_result_id: str
    top_event: str
    status: BuildAttemptStatus
    reason: str | None = None
    retryable: bool = False
    tree: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempt_id: str = field(default_factory=lambda: str(uuid4()), init=False)

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.release_id, "release_id"),
            (self.source_result_id, "source_result_id"),
            (self.top_event, "top_event"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
            object.__setattr__(self, field_name, value.strip())

        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", BuildAttemptStatus(self.status))
            except ValueError as exc:
                raise ValueError(f"unsupported build attempt status: {self.status}") from exc
        elif not isinstance(self.status, BuildAttemptStatus):
            raise TypeError("status must be a BuildAttemptStatus")

        if self.reason is not None:
            if not isinstance(self.reason, str):
                raise TypeError("reason must be a string or None")
            object.__setattr__(self, "reason", self.reason.strip() or None)

        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a boolean")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(timezone.utc),
        )

        if self.status is BuildAttemptStatus.SUCCEEDED:
            if not isinstance(self.tree, dict):
                raise ValueError("successful build attempts require a tree")
            if self.reason is not None:
                raise ValueError("successful build attempts cannot have a reason")
            if self.retryable:
                raise ValueError("successful build attempts cannot be retryable")
        else:
            if self.tree is not None:
                raise ValueError("rejected build attempts cannot contain a tree")
            if self.reason is None:
                raise ValueError("rejected build attempts require a reason")
