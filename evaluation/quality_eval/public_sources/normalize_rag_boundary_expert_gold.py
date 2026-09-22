"""Normalize the flat Liu Wu boundary review file into the project Gold schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_rag_boundary_expert_gold import validate


FIELDS = (
    "expert_status",
    "expected_knowledge_status",
    "answer_allowed",
    "warning_required",
    "need_additional_info",
    "missing_information",
    "expected_action",
    "expert_reason",
    "reviewer",
    "reviewed_at",
)


def normalize(source: dict[str, Any]) -> dict[str, Any]:
    rows = source.get("rows")
    if not isinstance(rows, list):
        raise ValueError("source expert file must contain rows")
    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each expert row must be an object")
        review = {field: row.get(field) for field in FIELDS}
        normalized_rows.append(
            {
                "query_id": row.get("query_id"),
                "question": row.get("query"),
                "expert_review": review,
            }
        )
    info = source.get("dataset_info", {})
    payload = {
        "dataset_info": {
            "name": info.get("name", "siemens_s210_rag_boundary_expert_gold_v1"),
            "version": "v1",
            "status": "expert_validated",
            "gold_source": "named_expert_review",
            "not_for_training": True,
            "reviewer": source.get("reviewer") or info.get("reviewer"),
            "reviewed_at": source.get("reviewed_at") or info.get("reviewed_at"),
            "source_file": source.get("source") or info.get("source_file"),
            "record_count": len(normalized_rows),
        },
        "rows": normalized_rows,
    }
    errors = validate(payload)
    if errors:
        raise ValueError("normalized expert Gold is invalid: " + "; ".join(errors))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    payload = normalize(source)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "expert_gold_validated", "query_count": len(payload["rows"]), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
