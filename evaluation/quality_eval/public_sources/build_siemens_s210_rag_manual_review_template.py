"""Build a blank manual-review template for the frozen S210 answer eval set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_template(dataset: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for query in dataset.get("queries", []):
        rows.append(
            {
                "query_id": query.get("query_id"),
                "question": query.get("question"),
                "query_type": query.get("query_type"),
                "difficulty": query.get("difficulty"),
                "expected_fault_codes": query.get("expected_fault_codes", []),
                "required_evidence_fields": query.get("required_evidence_fields", []),
                "response": {
                    "http_status": None,
                    "fault_codes": [],
                    "answer_text": None,
                    "citations": [],
                },
                "manual_review": {
                    "decision": None,
                    "fault_code_correct": None,
                    "cause_semantic_correctness": None,
                    "remedy_semantic_correctness": None,
                    "evidence_supports_claims": None,
                    "unsupported_claims": None,
                    "cross_fault_contamination": None,
                    "reviewer": None,
                    "reviewed_at": None,
                    "notes": None,
                },
            }
        )
    return {
        "dataset": dataset.get("dataset_info", {}).get("name", ""),
        "template_version": "rag_answer_manual_review_v1",
        "review_decisions": [
            "pass",
            "needs_revision",
            "insufficient_evidence",
            "uncertain",
        ],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    template = build_template(load_json(args.dataset))
    Path(args.output).write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"row_count": len(template["rows"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
