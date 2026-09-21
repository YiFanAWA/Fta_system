#!/usr/bin/env python3
"""Run the current structured extractor against the project evidence set.

This is a read-only baseline runner. It does not call the database, review
service, release service, or tree builder. Unknown gold fields are excluded
from precision/recall/F1 and are reported separately instead of being treated
as false negatives.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
DEFAULT_DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_project_handbook_evidence.json"
DEFAULT_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_extraction_baseline.json"
sys.path.insert(0, str(BACKEND))

from workflows.ai_module import extract_fault_result_from_text  # noqa: E402


FIELDS = ("fault_code", "description", "component", "causes", "parameters")


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).casefold()


def _values(records: Sequence[Any], field: str) -> Set[str]:
    result: Set[str] = set()
    for record in records:
        value = record.get(field) if isinstance(record, dict) else getattr(record, field, None)
        values = value if field in {"causes", "parameters"} else [value]
        for item in values or []:
            normalized = _normalize(item)
            if normalized:
                result.add(normalized)
    return result


def _gold_values(sample: Dict[str, Any], field: str) -> Set[str]:
    records = sample.get("gold_records", [])
    result: Set[str] = set()
    for record in records:
        value = record.get(field)
        values = value if field in {"causes", "parameters"} else [value]
        for item in values or []:
            normalized = _normalize(item)
            if normalized:
                result.add(normalized)
    return result


def _score(gold: Set[str], predicted: Set[str]) -> Dict[str, Any]:
    if not gold:
        return {
            "status": "unknown_gold_excluded",
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "predicted_unknown": len(predicted),
        }
    tp = len(gold & predicted)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    return {"status": "scored", "tp": tp, "fp": fp, "fn": fn, "predicted_unknown": 0}


def _f1(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 6), "recall": round(recall, 6), "f1": round(f1, 6)}


def _record_dict(record: Any) -> Dict[str, Any]:
    return {
        "fault_code": record.fault_code,
        "description": record.description,
        "component": record.component,
        "related_components": list(record.related_components),
        "causes": list(record.causes),
        "parameters": list(record.parameters),
        "confidence": record.confidence,
    }


def _span_dict(span: Any, source_text: str) -> Dict[str, Any]:
    return {
        "field": span.field.value,
        "source_id": span.source_id,
        "quote": span.quote,
        "start": span.start,
        "end": span.end,
        "matches_input": span.matches(source_text),
        "value_index": span.value_index,
    }


def _diagnostic_dict(diagnostic: Any) -> Dict[str, Any]:
    return {
        "code": diagnostic.code,
        "stage": diagnostic.stage,
        "retryable": diagnostic.retryable,
    }


def _run_sample(sample: Dict[str, Any], chunk_size: int, overlap: int) -> Dict[str, Any]:
    source_text = str(sample.get("input_text", ""))
    started = time.perf_counter()
    try:
        result = extract_fault_result_from_text(
            source_text,
            chunk_size_chars=chunk_size,
            overlap_chars=overlap,
        )
    except Exception as exc:  # baseline must preserve failures for diagnosis
        return {
            "sample_id": sample.get("sample_id"),
            "status": "runner_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    predicted = {field: _values(result.records, field) for field in FIELDS}
    gold = {field: _gold_values(sample, field) for field in FIELDS}
    field_scores = {field: _score(gold[field], predicted[field]) for field in FIELDS}
    evidence = [_span_dict(span, source_text) for span in result.evidence_spans]
    valid_evidence = sum(1 for span in evidence if span["matches_input"])

    return {
        "sample_id": sample.get("sample_id"),
        "status": result.status.value,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "record_count": len(result.records),
        "records": [_record_dict(record) for record in result.records],
        "field_scores": field_scores,
        "evidence": {
            "gold_expected_count": len(sample.get("evidence_spans", [])),
            "predicted_count": len(evidence),
            "valid_predicted_count": valid_evidence,
            "spans": evidence,
        },
        "diagnostics": [_diagnostic_dict(item) for item in result.diagnostics],
    }


def _replay_sample(sample: Dict[str, Any], previous_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Re-score saved predictions after changing only dataset annotations.

    This avoids another provider call when a source parser/label boundary is
    corrected but the sample input text is unchanged.
    """
    records = previous_detail.get("records", [])
    predicted = {field: _values(records, field) for field in FIELDS}
    gold = {field: _gold_values(sample, field) for field in FIELDS}
    evidence = previous_detail.get("evidence", {})
    return {
        **previous_detail,
        "field_scores": {
            field: _score(gold[field], predicted[field]) for field in FIELDS
        },
        "evidence": {
            **evidence,
            "gold_expected_count": len(sample.get("evidence_spans", [])),
        },
    }


def _summary(details: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    details = list(details)
    totals = {field: Counter() for field in FIELDS}
    for detail in details:
        for field, score in detail.get("field_scores", {}).items():
            totals[field].update(
                {key: int(score.get(key, 0)) for key in ("tp", "fp", "fn", "predicted_unknown")}
            )

    field_metrics = {}
    for field in FIELDS:
        values = totals[field]
        field_metrics[field] = {
            "counts": dict(values),
            "metrics": _f1(values["tp"], values["fp"], values["fn"]),
            "scored": any(
                detail.get("field_scores", {}).get(field, {}).get("status") == "scored"
                for detail in details
            ),
        }

    expected_evidence = sum(detail.get("evidence", {}).get("gold_expected_count", 0) for detail in details)
    predicted_evidence = sum(detail.get("evidence", {}).get("predicted_count", 0) for detail in details)
    valid_evidence = sum(detail.get("evidence", {}).get("valid_predicted_count", 0) for detail in details)
    return {
        "samples": len(details),
        "successful_samples": sum(detail.get("status") in {"success", "partial"} for detail in details),
        "failed_or_runner_error_samples": sum(
            detail.get("status") not in {"success", "partial"} for detail in details
        ),
        "field_metrics": field_metrics,
        "evidence": {
            "gold_expected_count": expected_evidence,
            "predicted_count": predicted_evidence,
            "valid_predicted_count": valid_evidence,
            "valid_predicted_rate": round(valid_evidence / predicted_evidence, 6)
            if predicted_evidence
            else None,
        },
        "interpretation": (
            "字段指标只对原文明确标注的字段计算；原文未知字段单独统计，"
            "不把未知误判成模型漏抽。该报告不评价FTA逻辑门。"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--chunk-size", type=int, default=6000)
    parser.add_argument("--overlap", type=int, default=300)
    parser.add_argument(
        "--replay-report",
        default="",
        help="Re-score a saved report after annotation changes without calling the model",
    )
    args = parser.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    samples = list(dataset.get("samples", []))
    if args.max_samples > 0:
        samples = samples[: args.max_samples]
    if args.replay_report:
        previous = json.loads(Path(args.replay_report).read_text(encoding="utf-8"))
        previous_by_id = {
            detail.get("sample_id"): detail for detail in previous.get("details", [])
        }
        missing = [sample.get("sample_id") for sample in samples if sample.get("sample_id") not in previous_by_id]
        if missing:
            raise ValueError(f"replay report is missing samples: {missing}")
        details = [_replay_sample(sample, previous_by_id[sample.get("sample_id")]) for sample in samples]
    else:
        details = [_run_sample(sample, args.chunk_size, args.overlap) for sample in samples]
    payload = {
        "report_type": "project_extraction_baseline",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(Path(args.dataset).as_posix()),
        "extractor": "extract_fault_result_from_text",
        "read_only": True,
        "replayed_from": str(Path(args.replay_report).as_posix()) if args.replay_report else None,
        "summary": _summary(details),
        "details": details,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"[ok] report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
