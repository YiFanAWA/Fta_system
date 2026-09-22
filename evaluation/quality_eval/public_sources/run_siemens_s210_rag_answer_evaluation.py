"""Run the S210 RAG answer evaluation against a running local API.

The runner is deliberately separate from the evaluator so a response batch
can be archived before scoring. It sends only the public evaluation questions
and never enables API debug output.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from evaluate_siemens_s210_rag_answers import evaluate_dataset, load_json


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
    except Exception as exc:
        return 0, {"error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--responses-output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="并发 HTTP 请求数；默认 1，评测口径不变，仅缩短真实 API 回归耗时",
    )
    parser.add_argument("--query-id", action="append")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成待执行查询计划，不访问本地 API 或外部模型",
    )
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")

    dataset = load_json(args.dataset)
    selected_ids = set(args.query_id or [])
    queries = [
        query
        for query in dataset.get("queries", [])
        if not selected_ids or query.get("query_id") in selected_ids
    ]

    if args.dry_run:
        plan = {
            "mode": "dry_run",
            "dataset": dataset.get("dataset_info", {}).get("name", ""),
            "base_url": args.base_url,
            "top_k": args.top_k,
            "query_count": len(queries),
            "queries": [
                {
                    "query_id": query.get("query_id"),
                    "question": query.get("question"),
                    "expected_fault_codes": query.get("expected_fault_codes", []),
                }
                for query in queries
            ],
        }
        report = {
            "mode": "dry_run",
            "dataset": plan["dataset"],
            "query_count": len(queries),
            "metrics": None,
            "message": "未执行 API 调用；确认计划后去掉 --dry-run 执行正式评测。",
        }
        Path(args.responses_output).write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        Path(args.report_output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0

    def run_one(query: dict[str, Any]) -> dict[str, Any]:
        status, payload = _post_json(
            args.base_url,
            str(query.get("question") or ""),
            args.top_k,
            args.timeout,
        )
        return {
            "query_id": query.get("query_id"),
            "http_status": status,
            **(payload if isinstance(payload, dict) else {"payload": payload}),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        responses = list(executor.map(run_one, queries))

    response_payload = {
        "dataset": dataset.get("dataset_info", {}).get("name", ""),
        "base_url": args.base_url,
        "top_k": args.top_k,
        "workers": args.workers,
        "response_count": len(responses),
        "responses": responses,
    }
    report = evaluate_dataset(dataset, responses)
    report["http_statuses"] = {
        str(item["query_id"]): item["http_status"] for item in responses
    }

    Path(args.responses_output).write_text(
        json.dumps(response_payload, ensure_ascii=False, indent=2) + "\n",
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
