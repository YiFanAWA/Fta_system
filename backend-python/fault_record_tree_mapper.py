"""Map released extraction records into the tree-builder input contract."""

from typing import Any

from extraction_contract import FaultRecord


def fault_record_to_tree_input(record: FaultRecord) -> dict[str, Any]:
    """Create one tree-builder event without changing extraction semantics."""
    if not isinstance(record, FaultRecord):
        raise TypeError("record must be a FaultRecord")

    return {
        "name": record.description,
        "probability": record.confidence,
        "gate": "OR",
        "source_record_ids": [record.record_id],
        "causes": [
            {
                "name": cause,
                "probability": None,
                "gate": "OR",
                "causes": [],
            }
            for cause in record.causes
        ],
    }
