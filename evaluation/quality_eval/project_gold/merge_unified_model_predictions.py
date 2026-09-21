#!/usr/bin/env python3
"""Merge fresh project/public extraction outputs into a unified evaluation copy."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _project_predictions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for detail in payload.get("details", []):
        sample_id = str(detail.get("sample_id", ""))
        if not sample_id:
            continue
        if detail.get("status") != "success" or not detail.get("records"):
            raise ValueError(f"project sample did not succeed: {sample_id}")
        result[sample_id] = {
            "record": copy.deepcopy(detail["records"][0]),
            "evidence_spans": copy.deepcopy(detail.get("evidence", {}).get("spans", [])),
            "run_status": detail.get("status"),
        }
    return result


def _public_predictions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in payload.get("predictions", []):
        sample_id = str(row.get("sample_id", ""))
        if not sample_id:
            continue
        if row.get("status") != "success" or not isinstance(row.get("prediction"), dict):
            raise ValueError(f"public sample did not succeed: {sample_id}")
        prediction = row["prediction"]
        records = prediction.get("records", [])
        if not records:
            raise ValueError(f"public sample has no record: {sample_id}")
        result[sample_id] = {
            "record": copy.deepcopy(records[0]),
            "evidence_spans": copy.deepcopy(prediction.get("evidence_spans", [])),
            "run_status": row.get("status"),
        }
    return result


def merge(
    dataset: dict[str, Any],
    project: dict[str, Any],
    public: dict[str, Any],
    *,
    run_name: str,
) -> dict[str, Any]:
    merged_predictions = {}
    merged_predictions.update(_project_predictions(project))
    merged_predictions.update(_public_predictions(public))

    output = copy.deepcopy(dataset)
    expected_ids = {str(sample["sample_id"]) for sample in output.get("samples", [])}
    missing = sorted(expected_ids - set(merged_predictions))
    extra = sorted(set(merged_predictions) - expected_ids)
    if missing or extra:
        raise ValueError(f"prediction coverage mismatch: missing={missing}, extra={extra}")

    for sample in output.get("samples", []):
        sample_id = str(sample["sample_id"])
        fresh = merged_predictions[sample_id]
        sample["model_prediction"] = {
            "record": fresh["record"],
            "evidence_spans": fresh["evidence_spans"],
        }
        sample.setdefault("run_history", []).append(
            {
                "run": run_name,
                "status": fresh["run_status"],
                "source": "local_api_replay",
            }
        )
    output["evaluation_run"] = {
        "name": run_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_success": len(_project_predictions(project)),
        "public_success": len(_public_predictions(public)),
        "total_success": len(merged_predictions),
        "model_prediction_replaced": True,
        "gold_records_preserved": True,
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--public", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()

    value = merge(
        _load(args.dataset),
        _load(args.project),
        _load(args.public),
        run_name=args.run_name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value["evaluation_run"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
