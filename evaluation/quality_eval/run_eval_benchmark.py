#!/usr/bin/env python3
"""Run benchmark for legality rate, hallucination rate, and FTA productivity.

Modes:
1) evaluate existing predictions file
2) call local API to generate predictions and then evaluate

Examples:
  python evaluation/quality_eval/run_eval_benchmark.py \
    --dataset evaluation/quality_eval/datasets/fta_eval_seed.json \
    --predictions evaluation/quality_eval/runs/preds.json

  python evaluation/quality_eval/run_eval_benchmark.py \
    --dataset evaluation/quality_eval/datasets/fta_eval_seed.json \
    --predict-mode api --api-url http://127.0.0.1:8000/api/fta/generate
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, request


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_eval_seed.json"
RUNS_DIR = ROOT / "evaluation" / "quality_eval" / "runs"


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[，。；：、,.!?:;\-_/()（）\[\]{}\"'`]+", "", s)
    return s


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _text_value(value: Any) -> str:
    """Return a field value without turning an unknown null into 'None'."""
    if value is None:
        return ""
    return str(value).strip()


def _extract_pred_records(pred: Dict[str, Any]) -> List[Dict[str, Any]]:
    extracted = pred.get("extracted_faults")
    if isinstance(extracted, dict):
        records = extracted.get("records")
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)]

    records = pred.get("records")
    if isinstance(records, list):
        return [r for r in records if isinstance(r, dict)]

    events = pred.get("events")
    if isinstance(events, list):
        return [e for e in events if isinstance(e, dict)]

    return []


def _is_legal_prediction(pred: Dict[str, Any]) -> bool:
    if not isinstance(pred, dict):
        return False

    records = _extract_pred_records(pred)
    records_valid = True
    if records:
        for rec in records:
            if not isinstance(rec, dict):
                records_valid = False
                break
            desc = str(rec.get("description", "") or rec.get("name", "")).strip()
            causes = rec.get("causes", [])
            if not isinstance(causes, list):
                records_valid = False
                break
            if not desc:
                records_valid = False
                break

    tree = pred.get("tree")
    has_tree = isinstance(tree, dict) and len(tree) > 0
    dot = str(pred.get("dot_content", "") or pred.get("dot", "")).strip()
    has_dot = dot.startswith("digraph")
    return records_valid and (bool(records) or has_tree or has_dot)


def _pred_fields_for_hallucination(pred: Dict[str, Any]) -> List[str]:
    records = _extract_pred_records(pred)
    values: List[str] = []

    for rec in records:
        for key in ("fault_code", "component", "description", "name"):
            v = _text_value(rec.get(key, ""))
            if v:
                values.append(v)

        for c in _safe_list(rec.get("causes")):
            cc = (
                _text_value(c.get("name", c))
                if isinstance(c, dict)
                else _text_value(c)
            )
            if cc:
                values.append(cc)

        for p in _safe_list(rec.get("parameters")):
            pp = (
                _text_value(p.get("name", p))
                if isinstance(p, dict)
                else _text_value(p)
            )
            if pp:
                values.append(pp)

    return values


def _hallucination_counts(sample: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, int]:
    input_text = _normalize(str(sample.get("input_text", "")))
    pred_fields = _pred_fields_for_hallucination(pred)

    total = 0
    hallucinated = 0
    for field in pred_fields:
        norm = _normalize(field)
        if not norm:
            continue
        total += 1
        if norm not in input_text:
            hallucinated += 1

    return {"total": total, "hallucinated": hallucinated}


def _fta_productive(pred: Dict[str, Any]) -> bool:
    tree = pred.get("tree")
    if isinstance(tree, dict) and len(tree) > 0:
        return True

    dot = str(pred.get("dot_content", "") or pred.get("dot", "")).strip()
    if dot.startswith("digraph"):
        return True

    files = pred.get("files")
    if isinstance(files, dict):
        xml_path = str(files.get("xml", "")).strip()
        if xml_path and Path(xml_path).exists():
            return True

    return False


def _call_api(api_url: str, sample: Dict[str, Any], timeout_s: int) -> Dict[str, Any]:
    payload = {
        "system": "评测系统",
        "top_event": str(sample.get("gold_top_event", "系统故障") or "系统故障"),
        "source": "text",
        "raw_text": str(sample.get("input_text", "")),
        "use_knowledge_graph": False,
        "run_analysis_report": False,
        "run_draft_review": False,
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_predictions(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("predictions"), list):
        arr = payload["predictions"]
    elif isinstance(payload, list):
        arr = payload
    else:
        raise ValueError("predictions file must be list or object with 'predictions'")

    out: Dict[str, Dict[str, Any]] = {}
    for row in arr:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("sample_id", "")).strip()
        pred = row.get("prediction") if isinstance(row.get("prediction"), dict) else row
        if sid and isinstance(pred, dict):
            out[sid] = pred
    return out


def evaluate(
    dataset: Dict[str, Any],
    predict_mode: str,
    api_url: str,
    predictions_map: Dict[str, Dict[str, Any]],
    split_filter: str,
    timeout_s: int,
) -> Dict[str, Any]:
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        raise ValueError("invalid dataset: samples must be list")

    total = 0
    legal_ok = 0
    fta_ok = 0
    hall_total = 0
    hall_bad = 0
    details: List[Dict[str, Any]] = []

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        split = str(sample.get("split", "")).strip() or "train"
        if split_filter != "all" and split != split_filter:
            continue

        sid = str(sample.get("sample_id", "")).strip()
        if not sid:
            continue

        total += 1
        pred: Dict[str, Any]
        err = ""
        latency_ms = None

        if predict_mode == "predictions":
            pred = predictions_map.get(sid, {})
            if not pred:
                err = "missing prediction"
        elif predict_mode == "api":
            t0 = time.time()
            try:
                pred = _call_api(api_url, sample, timeout_s)
            except error.HTTPError as exc:
                pred = {}
                err = f"HTTPError {exc.code}"
            except Exception as exc:
                pred = {}
                err = f"APIError {exc}"
            latency_ms = int((time.time() - t0) * 1000)
        else:  # gold mode for pipeline check
            pred = {
                "extracted_faults": {"records": sample.get("gold_records", [])},
                "tree": {"top_event": sample.get("gold_top_event", "")},
                "dot_content": "digraph FTA { top [label=\"TOP\"]; }",
            }

        legal = _is_legal_prediction(pred)
        fta_prod = _fta_productive(pred)
        hall = _hallucination_counts(sample, pred)

        legal_ok += 1 if legal else 0
        fta_ok += 1 if fta_prod else 0
        hall_total += hall["total"]
        hall_bad += hall["hallucinated"]

        details.append(
            {
                "sample_id": sid,
                "split": split,
                "source_type": sample.get("source_type", ""),
                "legal": legal,
                "fta_productive": fta_prod,
                "hallucination_total_fields": hall["total"],
                "hallucinated_fields": hall["hallucinated"],
                "latency_ms": latency_ms,
                "error": err,
            }
        )

    legality_rate = (legal_ok / total) if total else 0.0
    hallucination_rate = (hall_bad / hall_total) if hall_total else 0.0
    fta_productivity_rate = (fta_ok / total) if total else 0.0

    latencies = [d["latency_ms"] for d in details if isinstance(d.get("latency_ms"), int)]
    avg_latency = (sum(latencies) / len(latencies)) if latencies else None

    return {
        "summary": {
            "samples_evaluated": total,
            "predict_mode": predict_mode,
            "split_filter": split_filter,
            "legality_rate": round(legality_rate, 6),
            "hallucination_rate": round(hallucination_rate, 6),
            "fta_productivity_rate": round(fta_productivity_rate, 6),
            "counts": {
                "legal_ok": legal_ok,
                "hallucination_bad_fields": hall_bad,
                "hallucination_total_fields": hall_total,
                "fta_ok": fta_ok,
            },
            "avg_latency_ms": round(avg_latency, 2) if avg_latency is not None else None,
        },
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate legality/hallucination/FTA productivity")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET))
    parser.add_argument("--predict-mode", choices=["predictions", "api", "gold"], default="predictions")
    parser.add_argument("--predictions", type=str, default="", help="predictions JSON path")
    parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000/api/fta/generate")
    parser.add_argument("--split", choices=["all", "train", "dev", "test"], default="test")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    dataset = _read_json(Path(args.dataset))

    predictions_map: Dict[str, Dict[str, Any]] = {}
    if args.predict_mode == "predictions":
        if not args.predictions:
            raise ValueError("--predictions is required when --predict-mode=predictions")
        predictions_map = _load_predictions(Path(args.predictions))

    result = evaluate(
        dataset=dataset,
        predict_mode=args.predict_mode,
        api_url=args.api_url,
        predictions_map=predictions_map,
        split_filter=args.split,
        timeout_s=max(1, args.timeout),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else RUNS_DIR / f"metric_report_{ts}.json"
    _write_json(output_path, result)

    s = result["summary"]
    print(f"[ok] report: {output_path}")
    print(f"[ok] samples: {s['samples_evaluated']} split={s['split_filter']} mode={s['predict_mode']}")
    print(
        "[ok] legality={:.2%} hallucination={:.2%} fta_productivity={:.2%}".format(
            s["legality_rate"], s["hallucination_rate"], s["fta_productivity_rate"]
        )
    )


if __name__ == "__main__":
    main()
