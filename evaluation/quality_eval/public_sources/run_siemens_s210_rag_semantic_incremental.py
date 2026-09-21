"""Run the 30-query semantic RAG batch with checkpointed writes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_siemens_s210_rag_answers import evaluate_dataset, load_json
from run_siemens_s210_rag_answer_evaluation import _post_json


def _load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = load_json(path)
    responses = payload.get("responses", []) if isinstance(payload, dict) else []
    return {
        str(item.get("query_id")): item
        for item in responses
        if isinstance(item, dict) and item.get("query_id")
    }


def _write_checkpoint(
    *,
    dataset: dict[str, Any],
    responses: dict[str, dict[str, Any]],
    base_url: str,
    top_k: int,
    responses_path: Path,
    report_path: Path,
) -> None:
    ordered = [responses[key] for key in sorted(responses)]
    batch = {
        "dataset": dataset.get("dataset_info", {}).get("name", ""),
        "mode": "incremental_checkpointed",
        "base_url": base_url,
        "top_k": top_k,
        "response_count": len(ordered),
        "responses": ordered,
    }
    report = evaluate_dataset(dataset, ordered)
    responses_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    responses_path.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--responses-output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--query-id", action="append")
    args = parser.parse_args()

    dataset = load_json(args.dataset)
    responses_path = Path(args.responses_output)
    report_path = Path(args.report_output)
    responses = _load_existing(responses_path)
    selected_ids = set(args.query_id or [])
    queries = [
        query
        for query in dataset.get("queries", [])
        if not selected_ids or query.get("query_id") in selected_ids
    ]

    for index, query in enumerate(queries, start=1):
        query_id = str(query.get("query_id") or "")
        if not query_id or query_id in responses:
            continue
        status, payload = _post_json(
            args.base_url,
            str(query.get("question") or ""),
            args.top_k,
            args.timeout,
        )
        responses[query_id] = {
            "query_id": query_id,
            "http_status": status,
            **(payload if isinstance(payload, dict) else {"payload": payload}),
        }
        _write_checkpoint(
            dataset=dataset,
            responses=responses,
            base_url=args.base_url,
            top_k=args.top_k,
            responses_path=responses_path,
            report_path=report_path,
        )
        print(json.dumps({"completed": index, "query_id": query_id, "http_status": status}, ensure_ascii=False), flush=True)

    print(json.dumps({"response_count": len(responses), "query_count": len(queries)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
