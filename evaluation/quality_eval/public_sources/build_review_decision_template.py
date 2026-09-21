"""Create a blank structured decision template for pending review rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_template(queue: dict[str, Any]) -> dict[str, Any]:
    decisions = []
    for row in queue.get("samples", []):
        if (row.get("review_queue") or {}).get("status") != "pending":
            continue
        decisions.append(
            {
                "sample_id": row.get("sample_id"),
                "decision": None,
                "reviewer_name": None,
                "review_date": None,
                "fields_to_modify": None,
                "opinion": None,
                "correction_applied": False,
                "correction_override": {},
                "excluded": False,
            }
        )
    return {
        "dataset": queue.get("dataset_info", {}).get("name"),
        "instructions": [
            "每个 sample_id 都必须填写 decision 和 reviewer_name。",
            "审核通过可直接使用模型候选作为 gold_records；语义需修改必须提供修正后的 gold_records。",
            "证据不足或无法判断不能入库；若明确排除必须填写 excluded=true 和理由。",
            "逻辑门未有明确原文/专家标注时保持 unknown。",
        ],
        "decisions": decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    queue = json.loads(args.queue_json.read_text(encoding="utf-8"))
    result = build_template(queue)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision_rows": len(result["decisions"]), "output": str(args.output_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
