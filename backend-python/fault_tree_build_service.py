"""Build released extraction records and persist every attempt outcome."""

from collections.abc import Callable
from typing import Any

from build_attempt_repository import BuildAttemptRepository
from build_contract import BuildAttemptStatus, FaultTreeBuildAttempt
from extraction_contract import FaultRecord
from fault_record_tree_mapper import fault_record_to_tree_input
from fta_tree_contract import validate_fault_tree
from release_contract import ReleasedExtractionResult


class FaultTreeBuildService:
    """Keep tree building separate from review and release decisions."""

    def __init__(
        self,
        repository: BuildAttemptRepository,
        builder: Callable[[str, list[dict[str, Any]]], dict[str, Any]],
        mapper: Callable[[FaultRecord], dict[str, Any]] = fault_record_to_tree_input,
    ) -> None:
        if not callable(builder):
            raise TypeError("builder must be callable")
        if not callable(mapper):
            raise TypeError("mapper must be callable")
        self._repository = repository
        self._builder = builder
        self._mapper = mapper

    def build(
        self,
        release: ReleasedExtractionResult,
        top_event: str,
    ) -> FaultTreeBuildAttempt:
        if not isinstance(release, ReleasedExtractionResult):
            raise TypeError("release must be a ReleasedExtractionResult")
        if not isinstance(top_event, str) or not top_event.strip():
            raise ValueError("top_event must be a non-empty string")

        failures = [self._mapper(record) for record in release.records]

        try:
            tree = validate_fault_tree(self._builder(top_event.strip(), failures))
        except (TypeError, ValueError) as exc:
            attempt = FaultTreeBuildAttempt(
                release_id=release.release_id,
                source_result_id=release.source_result_id,
                top_event=top_event,
                status=BuildAttemptStatus.REJECTED,
                reason=str(exc),
                retryable=False,
            )
        except Exception as exc:
            # The attempt itself is still an auditable domain outcome. The
            # retryable flag leaves room for a caller to retry provider or
            # runtime failures without pretending the release was invalid.
            attempt = FaultTreeBuildAttempt(
                release_id=release.release_id,
                source_result_id=release.source_result_id,
                top_event=top_event,
                status=BuildAttemptStatus.REJECTED,
                reason=str(exc) or "fault tree builder failed",
                retryable=True,
            )
        else:
            attempt = FaultTreeBuildAttempt(
                release_id=release.release_id,
                source_result_id=release.source_result_id,
                top_event=top_event,
                status=BuildAttemptStatus.SUCCEEDED,
                tree=tree,
            )

        return self._repository.append_build_attempt(attempt)
