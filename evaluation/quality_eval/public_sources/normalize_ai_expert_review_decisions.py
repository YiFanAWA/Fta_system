"""Normalize AI-assisted review decisions for the existing finalizer contract.

The AI review artifact uses ``correction_override.records`` for revised gold
records.  The shared finalizer accepts the same payload under
``correction_override.gold_records``.  This script preserves the original
artifact and writes a normalized derivative; it does not finalize the queue
or import anything into SQLite.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    decisions = result.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("decisions must be a list")

    normalized = 0
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError("each decision must be an object")
        override = decision.get("correction_override")
        if not isinstance(override, dict):
            continue
        records = override.get("records")
        if records and not override.get("gold_records"):
            override["gold_records"] = deepcopy(records)
            normalized += 1

    result["normalization"] = {
        "status": "normalized_for_existing_finalizer_contract",
        "source_field": "correction_override.records",
        "target_field": "correction_override.gold_records",
        "normalized_revision_count": normalized,
        "queue_or_database_written": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input JSON must contain an object")
    result = normalize(payload)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["normalization"], ensure_ascii=False))


if __name__ == "__main__":
    main()
