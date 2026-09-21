"""Normalize Liu Wu's query review into an action-oriented Gold contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {"retrieve", "retrieve_with_warning", "clarify"}


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(source: dict[str, Any], source_path: Path, root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in source.get("queries", []):
        action = str(row.get("recommended_action", "")).strip()
        if action == "retrieve_with_warning":
            normalized_action = "retrieve_with_warning"
        elif action == "retrieve":
            normalized_action = "retrieve"
        elif action in {"clarify", "clarification_required"}:
            normalized_action = "clarify"
        else:
            raise ValueError(f"unsupported reviewer action for {row.get('query_id')}: {action}")
        rows.append(
            {
                "query_id": row["query_id"],
                "query": row["query"],
                "query_type": row.get("query_type"),
                "domain_decision": row["domain_decision"],
                "sufficiency_decision": row["sufficiency_decision"],
                "action": normalized_action,
                "reviewer_should_clarify_flag": bool(row.get("should_clarify")),
                "reviewer_recommended_action": action,
                "missing_information": list(row.get("missing_information", [])),
                "reason": row.get("expert_notes", ""),
                "expert": row.get("expert"),
                "expert_role": row.get("expert_role"),
            }
        )
    if not rows:
        raise ValueError("source contains no reviewed queries")
    action_counts = {action: sum(row["action"] == action for row in rows) for action in sorted(ALLOWED_ACTIONS)}
    return {
        "dataset_info": {
            "name": "query_action_gold_v2",
            "version": date.today().isoformat(),
            "purpose": "separate retrieval action from information sufficiency",
            "reviewer": source.get("expert"),
            "review_status": source.get("status"),
            "source_file": str(source_path.resolve().relative_to(root.resolve()))
            if source_path.resolve().is_relative_to(root.resolve())
            else str(source_path.resolve()),
            "source_sha256": _sha256(source_path),
            "query_count": len(rows),
            "action_counts": action_counts,
            "production_use": False,
            "contract_note": "should_clarify is retained as reviewer metadata; action controls system behavior. retrieve_with_warning is not a blocking clarification.",
        },
        "label_schema": {
            "action": {
                "retrieve": "允许直接检索并回答",
                "retrieve_with_warning": "允许检索，但回答中提示需要型号/故障码等信息确认",
                "clarify": "必须先请求补充信息，再决定是否检索",
            },
            "domain_decision": ["industrial_drive", "aerospace"],
            "sufficiency_decision": ["sufficient", "partially_sufficient", "insufficient", "cannot_determine"],
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
    print(json.dumps({"query_count": len(payload["queries"]), "action_counts": payload["dataset_info"]["action_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
