"""Evaluate the deterministic RAG boundary policy on its draft query set.

This is a policy/unit evaluation, not a semantic expert gold evaluation. It
checks the explainable pre-generation boundary decisions before real API
answers are generated.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from rag.response_policy import ResponsePolicyLayer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    queries = payload.get("queries", [])
    layer = ResponsePolicyLayer()
    rows: list[dict[str, Any]] = []
    for item in queries:
        decision = layer.assess_boundary(
            question=str(item.get("question") or ""),
            contexts=[object()],
        )
        expected = str(item.get("expected_knowledge_status") or "")
        actual = decision.knowledge_status
        rows.append(
            {
                "query_id": item.get("query_id"),
                "question": item.get("question"),
                "expected_knowledge_status": expected,
                "actual_knowledge_status": actual,
                "expected_response_policy": item.get("expected_response_policy"),
                "actual_response_policy": decision.response_policy,
                "match": expected == actual,
                "decision": decision.to_dict(),
            }
        )

    matches = sum(1 for row in rows if row["match"])
    expected_counts = Counter(row["expected_knowledge_status"] for row in rows)
    actual_counts = Counter(row["actual_knowledge_status"] for row in rows)
    report = {
        "dataset": payload.get("dataset_info", {}).get("name", dataset_path.name),
        "status": "engineering_policy_check",
        "expert_validated": False,
        "query_count": len(rows),
        "matched": matches,
        "accuracy": matches / len(rows) if rows else 0.0,
        "expected_counts": dict(expected_counts),
        "actual_counts": dict(actual_counts),
        "mismatches": [row for row in rows if not row["match"]],
        "results": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: report[key] for key in ("query_count", "matched", "accuracy", "mismatches")},
            ensure_ascii=False,
        )
    )
    return 0 if not report["mismatches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
