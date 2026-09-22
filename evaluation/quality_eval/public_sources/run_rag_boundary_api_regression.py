"""Run the expert-reviewed S210 boundary Gold against the real HTTP API.

This runner deliberately evaluates only the boundary decision returned by the
API.  It does not score answer semantics, retrieval ranking, or citations;
those concerns have separate evaluation datasets and reports.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from evaluate_rag_boundary_expert_gold import score_policy
from validate_rag_boundary_expert_gold import load, validate


def _post_json(base_url: str, question: str, top_k: int, timeout: float) -> tuple[int, Any]:
    body = json.dumps(
        {"question": question, "top_k": top_k, "debug": False},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/rag/query",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return int(exc.code), payload
    except Exception as exc:  # pragma: no cover - exercised by live API failures
        return 0, {"error": f"{type(exc).__name__}: {exc}"}


def _boundary_from_response(payload: dict[str, Any]) -> dict[str, Any] | None:
    boundary = payload.get("boundary")
    if isinstance(boundary, dict):
        return boundary
    pipeline = payload.get("pipeline")
    if not isinstance(pipeline, dict):
        return None
    keys = (
        "knowledge_status",
        "response_policy",
        "answer_allowed",
        "warning_required",
        "need_additional_info",
    )
    if not any(key in pipeline for key in keys):
        return None
    return {key: pipeline.get(key) for key in keys}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--responses-output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")

    gold = load(Path(args.gold))
    errors = validate(gold)
    if errors:
        raise SystemExit("expert Gold is not valid: " + "; ".join(errors))

    def run_one(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        query_id = str(row["query_id"])
        status, payload = _post_json(
            args.base_url,
            str(row["question"]),
            args.top_k,
            args.timeout,
        )
        response_row: dict[str, Any] = {
            "query_id": query_id,
            "question": row["question"],
            "http_status": status,
        }
        if isinstance(payload, dict):
            response_row.update(payload)
        else:
            response_row["payload"] = payload

        boundary = _boundary_from_response(payload) if isinstance(payload, dict) else None
        actual_row = None
        if status == 200 and boundary is not None:
            actual_row = {"query_id": query_id, **boundary}
        return response_row, actual_row

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        completed = list(executor.map(run_one, gold["rows"]))
    responses = [item[0] for item in completed]
    actual_rows = [item[1] for item in completed if item[1] is not None]

    failed = [row for row in responses if row["http_status"] != 200]
    missing_boundary = [
        row["query_id"]
        for row in responses
        if row["http_status"] == 200 and row["query_id"] not in {item["query_id"] for item in actual_rows}
    ]
    metrics = None
    if not failed and not missing_boundary:
        metrics = score_policy(gold, actual_rows)

    response_payload = {
        "dataset": gold["dataset_info"].get("name"),
        "base_url": args.base_url,
        "top_k": args.top_k,
        "workers": args.workers,
        "response_count": len(responses),
        "responses": responses,
    }
    report = {
        "dataset": gold["dataset_info"].get("name"),
        "status": "real_http_boundary_regression" if metrics is not None else "real_http_boundary_regression_incomplete",
        "expert_validated": True,
        "query_count": len(responses),
        "successful_response_count": len(responses) - len(failed),
        "failed_query_ids": [row["query_id"] for row in failed],
        "missing_boundary_query_ids": missing_boundary,
        "metrics": metrics,
        "results": actual_rows,
    }

    responses_path = Path(args.responses_output)
    responses_path.parent.mkdir(parents=True, exist_ok=True)
    responses_path.write_text(json.dumps(response_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = Path(args.report_output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if metrics is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
