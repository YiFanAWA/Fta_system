"""Merge a full answer batch with selected incremental query reruns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_siemens_s210_rag_answers import evaluate_dataset, load_json


def _responses(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        return [item for item in payload["responses"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def merge_batches(base: Any, replacements: Any) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {
        str(item.get("query_id")): item
        for item in _responses(base)
        if item.get("query_id")
    }
    for item in _responses(replacements):
        query_id = str(item.get("query_id") or "")
        if query_id:
            merged[query_id] = item
    return [merged[key] for key in sorted(merged)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-responses", required=True)
    parser.add_argument("--replacement-responses", action="append", required=True)
    parser.add_argument("--responses-output", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    dataset = load_json(args.dataset)
    responses = merge_batches(
        load_json(args.base_responses),
        [item for path in args.replacement_responses for item in _responses(load_json(path))],
    )
    batch = {
        "dataset": dataset.get("dataset_info", {}).get("name", ""),
        "mode": "merged_incremental_reruns",
        "response_count": len(responses),
        "responses": responses,
    }
    report = evaluate_dataset(dataset, responses)
    Path(args.responses_output).write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path(args.report_output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["metrics"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
