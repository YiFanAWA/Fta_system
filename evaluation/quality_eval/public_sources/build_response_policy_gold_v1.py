"""Build response-policy Gold from the expert-reviewed action labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(source: dict[str, Any], source_path: Path, root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in source.get("queries", []):
        source_action = str(row["recommended_action"])
        if source_action == "retrieve":
            retrieval_policy = "allow"
            response_policy = "normal"
        elif source_action == "retrieve_with_warning":
            retrieval_policy = "allow"
            response_policy = "warning"
        elif source_action in {"clarify", "clarification_required"}:
            retrieval_policy = "allow"
            response_policy = "clarify"
        else:
            raise ValueError(f"unsupported action: {source_action}")
        rows.append(
            {
                "query_id": row["query_id"],
                "query": row["query"],
                "query_type": row.get("query_type"),
                "domain_decision": row["domain_decision"],
                "sufficiency_decision": row["sufficiency_decision"],
                "retrieval_policy": retrieval_policy,
                "response_policy": response_policy,
                "source_action": source_action,
                "missing_information": list(row.get("missing_information", [])),
                "reason": row.get("expert_notes", ""),
                "expert": row.get("expert"),
            }
        )
    counts = {
        "retrieval_policy": {
            "allow": sum(row["retrieval_policy"] == "allow" for row in rows),
        },
        "response_policy": {
            value: sum(row["response_policy"] == value for row in rows)
            for value in ("normal", "warning", "clarify")
        },
    }
    try:
        source_ref = str(source_path.resolve().relative_to(root.resolve()))
    except ValueError:
        source_ref = str(source_path.resolve())
    return {
        "dataset_info": {
            "name": "response_policy_gold_v1",
            "version": date.today().isoformat(),
            "purpose": "post-retrieval answer-risk policy Gold",
            "reviewer": source.get("expert"),
            "source_file": source_ref,
            "source_sha256": _sha256(source_path),
            "query_count": len(rows),
            "counts": counts,
            "production_use": False,
            "contract_note": "all policies allow retrieval; warning changes answer wording and certainty, while clarify requests missing context before presenting a definitive answer.",
        },
        "label_schema": {
            "retrieval_policy": {
                "allow": "retrieval is allowed",
                "allow": "retrieval is allowed; the answer policy controls certainty and whether clarification is requested",
            },
            "response_policy": {
                "normal": "normal evidence-grounded answer",
                "warning": "answer with uncertainty and request missing context",
                "clarify": "ask for missing context instead of presenting a definitive answer",
            },
        },
        "queries": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    payload = _build(_read(args.source), args.source, root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["dataset_info"]["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
