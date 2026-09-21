"""Attach sufficiency strata to an already completed aerospace dev run.

This does not rerun or alter model rankings.  It is valid only when query
texts and relevant entity labels are unchanged; the script checks that
precondition before rewriting the diagnostic report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "backend-python") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend-python"))

from run_aerospace_generic_retrieval_dev import _average, _by_type, render_markdown  # noqa: E402


def augment(report_path: Path, dev_path: Path) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dev = json.loads(dev_path.read_text(encoding="utf-8"))
    by_id = {query["query_id"]: query for query in dev["queries"]}
    rows = report["queries"]
    if set(by_id) != {row["query_id"] for row in rows}:
        raise ValueError("development query ids do not match the completed report")
    for row in rows:
        query = by_id[row["query_id"]]
        if query["query"] != row["query"] or set(query["relevant_entity_ids"]) != set(row["relevant_entity_ids"]):
            raise ValueError(f"query content changed for {row['query_id']}; rerun retrieval")
        row["query_sufficiency"] = query["query_sufficiency"]
        row["sufficiency_reason"] = query["sufficiency_reason"]

    report["evaluation_info"]["report_revision"] = "sufficiency_stratified_without_model_rerun"
    report["evaluation_info"]["benchmark_source"] = str(dev_path)
    for section in ("candidate_recall", "reranked"):
        metric_field = "candidate_metrics" if section == "candidate_recall" else "reranked_metrics"
        report[section]["metrics_by_sufficiency"] = _by_type(
            [{**row[metric_field], "query_type": row["query_sufficiency"]} for row in rows]
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = augment(args.report, args.dev)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"output": str(args.output_json), "report_revision": report["evaluation_info"]["report_revision"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
