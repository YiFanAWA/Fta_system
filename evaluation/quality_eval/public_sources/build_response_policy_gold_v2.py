"""Expand response-policy v1 labels into the explicit v2 answer contract."""

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


def _contract(policy: str) -> dict[str, Any]:
    if policy == "normal":
        return {
            "policy": "P0_DIRECT_ANSWER",
            "answer_allowed": True,
            "confidence_level": "high",
            "need_additional_info": False,
            "warning_required": False,
        }
    if policy == "warning":
        return {
            "policy": "P1_ANSWER_WITH_WARNING",
            "answer_allowed": True,
            "confidence_level": "medium",
            "need_additional_info": True,
            "warning_required": True,
        }
    if policy == "clarify":
        return {
            "policy": "P2_ASK_BEFORE_DEFINITIVE_ANSWER",
            "answer_allowed": False,
            "confidence_level": "low",
            "need_additional_info": True,
            "warning_required": False,
        }
    raise ValueError(f"unsupported response policy: {policy}")


def build(source: dict[str, Any], source_path: Path, root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in source.get("queries", []):
        policy = str(row["response_policy"])
        rows.append(
            {
                "query_id": row["query_id"],
                "query": row["query"],
                "query_type": row.get("query_type"),
                "domain_decision": row.get("domain_decision"),
                "sufficiency_decision": row.get("sufficiency_decision"),
                "retrieval_policy": "allow",
                "response_policy_v1": policy,
                **_contract(policy),
                "source_action": row.get("source_action"),
                "missing_information": list(row.get("missing_information", [])),
                "reason": row.get("reason", ""),
                "expert": row.get("expert"),
            }
        )
    try:
        source_ref = str(source_path.resolve().relative_to(root.resolve()))
    except ValueError:
        source_ref = str(source_path.resolve())
    counts = {policy: sum(row["policy"] == policy for row in rows) for policy in (
        "P0_DIRECT_ANSWER",
        "P1_ANSWER_WITH_WARNING",
        "P2_ASK_BEFORE_DEFINITIVE_ANSWER",
    )}
    return {
        "dataset_info": {
            "name": "response_policy_gold_v2",
            "version": date.today().isoformat(),
            "purpose": "explicit post-retrieval answer contract Gold",
            "reviewer": source.get("dataset_info", {}).get("reviewer"),
            "source_file": source_ref,
            "source_sha256": _sha256(source_path),
            "query_count": len(rows),
            "policy_counts": counts,
            "retrieval_policy": "allow_for_all_policies",
            "production_use": False,
            "clarify_gold_support": counts["P2_ASK_BEFORE_DEFINITIVE_ANSWER"],
            "contract_note": "P0/P1/P2 control answer permission and certainty after retrieval; they never change Retrieval scope or ranking.",
        },
        "label_schema": {
            "policy": {
                "P0_DIRECT_ANSWER": "answer directly from evidence",
                "P1_ANSWER_WITH_WARNING": "answer with uncertainty and request missing context",
                "P2_ASK_BEFORE_DEFINITIVE_ANSWER": "ask for missing context before any definitive answer",
            },
            "fields": {
                "answer_allowed": "whether a definitive answer may be presented",
                "confidence_level": "high, medium, or low",
                "need_additional_info": "whether the user should provide more context",
                "warning_required": "whether uncertainty wording is mandatory",
            },
        },
        "queries": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build(_read(args.source), args.source, Path(__file__).resolve().parents[3])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["dataset_info"]["policy_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
