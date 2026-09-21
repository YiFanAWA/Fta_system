"""Non-destructive parity gate for the generic S210 retrieval pipeline.

The gate protects semantic behavior while treating exact candidate ordering as
diagnostic information.  It intentionally does not rerun embedding or
reranking models; the heavy parity runner produces the JSON artifacts that
this script checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric(report: dict[str, Any], name: str) -> float:
    values = report["metrics"]["generic_E_reranker_guarded"]
    key = "reciprocal_rank" if name == "mrr" else name
    return float(values[key])


def _candidate_recall(report: dict[str, Any]) -> float:
    parity = report.get("parity", {})
    if "candidate_recall" in parity:
        return float(parity["candidate_recall"])
    rows = report.get("candidate_rows", [])
    hits = sum(
        bool(set(row.get("relevant_fault_codes", [])) & set(row.get("generic_candidate_pool", [])))
        for row in rows
    )
    return hits / len(rows) if rows else 0.0


def evaluate_gate(
    baseline: dict[str, Any],
    current: dict[str, Any],
    *,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    baseline_info = baseline["evaluation_info"]
    current_info = current["evaluation_info"]
    baseline_count = int(baseline_info["entity_count"])
    current_count = int(current_info["entity_count"])
    baseline_query_count = int(baseline_info["benchmark_query_count"])
    current_query_count = int(current_info["benchmark_query_count"])

    metric_checks = {
        name: {
            "baseline": _metric(baseline, name),
            "current": _metric(current, name),
            "delta": _metric(current, name) - _metric(baseline, name),
        }
        for name in ("recall_at_1", "recall_at_3", "recall_at_5", "recall_at_10", "recall_at_20", "mrr")
    }
    for value in metric_checks.values():
        value["pass"] = value["current"] + tolerance >= value["baseline"]

    current_parity = current.get("parity", {})
    top1_preserved_rate = current_parity.get("top1_relevant_preserved_rate")
    if top1_preserved_rate is None:
        # v1 reports persisted exact Top-1 sequence rather than the newer
        # relevance-preservation field; use it as the compatible fallback.
        top1_preserved_rate = current_parity.get("guarded_top_k_sequence_match_rate", {}).get("1", 0.0)
    checks = {
        "entity_count_unchanged": current_count == baseline_count == 281,
        "query_count_unchanged": current_query_count == baseline_query_count == 39,
        "candidate_recall_is_complete": _candidate_recall(current) >= 1.0 - tolerance,
        "candidate_recall_not_regressed": _candidate_recall(current) + tolerance >= _candidate_recall(baseline),
        "top1_relevant_preserved": float(top1_preserved_rate) >= 1.0 - tolerance,
        "core_metrics_not_regressed": all(value["pass"] for value in metric_checks.values()),
    }
    informational = {
        "candidate_set_exact_match_rate": current_parity.get("candidate_set_exact_match_rate"),
        "candidate_order_exact_match_rate": current_parity.get("candidate_order_exact_match_rate"),
        "guarded_top_k_sequence_match_rate": current_parity.get("guarded_top_k_sequence_match_rate", {}),
        "stage_diagnostics_count": current_parity.get("stage_diagnostics_count", 0),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "baseline": {
            "path": baseline_info.get("name"),
            "entity_count": baseline_count,
            "query_count": baseline_query_count,
            "candidate_recall": _candidate_recall(baseline),
        },
        "current": {
            "path": current_info.get("name"),
            "entity_count": current_count,
            "query_count": current_query_count,
            "candidate_recall": _candidate_recall(current),
        },
        "checks": checks,
        "metric_checks": metric_checks,
        "informational_only": informational,
        "policy": {
            "candidate_set_exact_and_top_k_sequence_are_diagnostic_only": True,
            "metric_tolerance": tolerance,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    result = evaluate_gate(_load(args.baseline), _load(args.current))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
