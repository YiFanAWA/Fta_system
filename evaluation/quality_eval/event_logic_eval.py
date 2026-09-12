#!/usr/bin/env python3
"""Evaluate basic-event extraction and fault-tree logic quality.

This script complements run_eval_benchmark.py with two extra focuses:
1) basic event extraction quality (precision/recall/F1)
2) logic quality (tree structure validity, gate validity, and optional AI logic score)

Examples:
  python evaluation/quality_eval/event_logic_eval.py \
    --dataset evaluation/quality_eval/datasets/fta_eval_seed.json \
    --mode api --split test

  python evaluation/quality_eval/event_logic_eval.py \
    --dataset evaluation/quality_eval/datasets/fta_eval_seed.json \
    --mode api --split test --ai-judge
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib import error, request

try:
    import openai
except Exception:
    openai = None  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_eval_seed.json"
RUNS_DIR = ROOT / "evaluation" / "quality_eval" / "runs"


def _load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _first_non_empty(*values: str) -> str:
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


_load_local_env()


OPENAI_API_KEY = _first_non_empty(os.getenv("OPENAI_API_KEY", ""), os.getenv("QWEN_API_KEY", ""))
OPENAI_API_BASE = _first_non_empty(
    os.getenv("OPENAI_API_BASE", ""),
    os.getenv("OPENAI_BASE_URL", ""),
    os.getenv("QWEN_BASE_URL", ""),
)
OPENAI_MODEL = _first_non_empty(os.getenv("OPENAI_MODEL", ""), os.getenv("QWEN_MODEL", ""), "qwen-plus")
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))


@dataclass
class SampleResult:
    sample_id: str
    split: str
    source_type: str
    event_precision: float
    event_recall: float
    event_f1: float
    event_tp: int
    event_fp: int
    event_fn: int
    tree_valid: bool
    gate_valid: bool
    heuristic_logic_ok: Optional[bool]
    strict_logic_ok: Optional[bool]
    ai_logic_score: Optional[float]
    ai_logic_reason: str
    latency_ms: Optional[int]
    error: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "split": self.split,
            "source_type": self.source_type,
            "event_precision": round(self.event_precision, 6),
            "event_recall": round(self.event_recall, 6),
            "event_f1": round(self.event_f1, 6),
            "event_tp": self.event_tp,
            "event_fp": self.event_fp,
            "event_fn": self.event_fn,
            "tree_valid": self.tree_valid,
            "gate_valid": self.gate_valid,
            "heuristic_logic_ok": self.heuristic_logic_ok,
            "strict_logic_ok": self.strict_logic_ok,
            "ai_logic_score": self.ai_logic_score,
            "ai_logic_reason": self.ai_logic_reason,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


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


def _f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def _extract_gold_basic_events(sample: Dict[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for rec in _safe_list(sample.get("gold_records")):
        if not isinstance(rec, dict):
            continue
        for c in _safe_list(rec.get("causes")):
            cc = str(c.get("name", c)).strip() if isinstance(c, dict) else str(c).strip()
            if cc:
                out.add(_normalize(cc))
    return out


def _extract_pred_records(pred: Dict[str, Any]) -> List[Dict[str, Any]]:
    extracted = pred.get("extracted_faults")
    if isinstance(extracted, dict) and isinstance(extracted.get("records"), list):
        return [r for r in extracted["records"] if isinstance(r, dict)]
    events = pred.get("events")
    if isinstance(events, list):
        return [r for r in events if isinstance(r, dict)]
    return []


def _collect_tree_leaf_events(node: Dict[str, Any], sink: Set[str]) -> None:
    if not isinstance(node, dict):
        return
    children = node.get("children")
    name = str(node.get("name", "") or node.get("top", "")).strip()
    if not isinstance(children, list) or not children:
        if name:
            sink.add(_normalize(name))
        return
    for child in children:
        if isinstance(child, dict):
            _collect_tree_leaf_events(child, sink)


def _extract_pred_basic_events(pred: Dict[str, Any]) -> Set[str]:
    out: Set[str] = set()

    for rec in _extract_pred_records(pred):
        for c in _safe_list(rec.get("causes")):
            cc = str(c.get("name", c)).strip() if isinstance(c, dict) else str(c).strip()
            if cc:
                out.add(_normalize(cc))

    tree = pred.get("tree")
    if isinstance(tree, dict):
        _collect_tree_leaf_events(tree, out)
    return out


def _validate_tree(tree: Dict[str, Any]) -> Tuple[bool, bool]:
    if not isinstance(tree, dict) or not tree:
        return False, False

    has_top = isinstance(tree.get("top"), str) and bool(tree.get("top", "").strip())
    if not has_top:
        return False, False

    gate_valid = True

    def dfs(node: Dict[str, Any], path: Set[int]) -> bool:
        nonlocal gate_valid
        nid = id(node)
        if nid in path:
            return False
        path.add(nid)

        gate = node.get("gate")
        if gate is not None and str(gate).upper() not in {"AND", "OR"}:
            gate_valid = False

        children = node.get("children")
        if children is None:
            path.remove(nid)
            return True
        if not isinstance(children, list):
            path.remove(nid)
            return False

        for ch in children:
            if not isinstance(ch, dict):
                path.remove(nid)
                return False
            if not dfs(ch, path):
                path.remove(nid)
                return False

        path.remove(nid)
        return True

    valid = dfs(tree, set())
    return valid, gate_valid


def _heuristic_expected_gate(input_text: str) -> str:
    text = input_text or ""
    and_markers = ["同时", "并且", "且", "均", "全部", "都发生"]
    for m in and_markers:
        if m in text:
            return "AND"

    or_markers = ["任一", "任意", "之一", "任一项", "任一原因", "任一条件"]
    for m in or_markers:
        if m in text:
            return "OR"

    return ""


def _heuristic_logic_ok(sample: Dict[str, Any], pred: Dict[str, Any]) -> Optional[bool]:
    tree = pred.get("tree")
    if not isinstance(tree, dict):
        return None
    expected = _heuristic_expected_gate(str(sample.get("input_text", "")))
    if not expected:
        return None
    actual = str(tree.get("gate", "OR")).upper()
    return actual == expected


def _call_generate_api(api_url: str, sample: Dict[str, Any], timeout_s: int) -> Dict[str, Any]:
    payload = {
        "system": "评测系统",
        "top_event": str(sample.get("gold_top_event", "系统故障") or "系统故障"),
        "source": "text",
        "raw_text": str(sample.get("input_text", "")),
        "use_knowledge_graph": False,
        "run_analysis_report": False,
        "run_draft_review": False,
    }
    req = request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _chat_completion(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY未配置，无法启用AI评审")
    if openai is None:
        raise RuntimeError("openai库不可用，无法启用AI评审")

    if hasattr(openai, "OpenAI"):
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_API_BASE:
            kwargs["base_url"] = OPENAI_API_BASE
        client = openai.OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return (content or "").strip()

    if OPENAI_API_BASE:
        openai.api_base = OPENAI_API_BASE
    openai.api_key = OPENAI_API_KEY
    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        request_timeout=OPENAI_TIMEOUT_SECONDS,
    )
    return resp["choices"][0]["message"]["content"].strip()


def _ai_logic_judge(sample: Dict[str, Any], pred: Dict[str, Any]) -> Tuple[Optional[float], str]:
    tree = pred.get("tree")
    if not isinstance(tree, dict):
        return None, "tree为空，无法AI评审"

    prompt = (
        "你是FTA评审专家。请根据输入文本评估故障树逻辑是否合理。\n"
        "只输出JSON对象，格式:\n"
        "{\"logic_score\": 0.0-1.0, \"reason\": \"...\"}\n"
        "评分标准:\n"
        "1. 逻辑门(AND/OR)是否与文本描述一致\n"
        "2. 父子因果方向是否合理\n"
        "3. 是否有明显缺失或不相关节点\n\n"
        f"输入文本:\n{sample.get('input_text','')}\n\n"
        f"故障树JSON:\n{json.dumps(tree, ensure_ascii=False)}\n"
    )
    try:
        text = _chat_completion(prompt)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or start >= end:
            return None, "AI返回非JSON"
        obj = json.loads(text[start : end + 1])
        score = float(obj.get("logic_score", 0.0))
        score = max(0.0, min(1.0, score))
        reason = str(obj.get("reason", "")).strip()
        return score, reason
    except Exception as exc:
        return None, f"AI评审失败: {exc}"


def evaluate(
    dataset: Dict[str, Any],
    mode: str,
    api_url: str,
    split_filter: str,
    timeout_s: int,
    ai_judge: bool,
    max_samples: int,
    ai_logic_threshold: float,
) -> Dict[str, Any]:
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        raise ValueError("dataset.samples必须是list")

    details: List[SampleResult] = []
    sum_tp = sum_fp = sum_fn = 0
    tree_valid_cnt = gate_valid_cnt = heuristic_logic_cnt = 0
    heuristic_logic_applicable_cnt = 0
    strict_logic_cnt = 0
    ai_scores: List[float] = []

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        split = str(sample.get("split", "train")).strip() or "train"
        if split_filter != "all" and split != split_filter:
            continue

        sid = str(sample.get("sample_id", "")).strip()
        if not sid:
            continue

        if max_samples > 0 and len(details) >= max_samples:
            break

        err = ""
        latency_ms: Optional[int] = None

        if mode == "api":
            t0 = time.time()
            try:
                pred = _call_generate_api(api_url, sample, timeout_s)
            except error.HTTPError as exc:
                pred = {}
                err = f"HTTPError {exc.code}"
            except Exception as exc:
                pred = {}
                err = f"APIError {exc}"
            latency_ms = int((time.time() - t0) * 1000)
        else:  # gold debug mode
            pred = {
                "extracted_faults": {"records": sample.get("gold_records", [])},
                "tree": {
                    "top": sample.get("gold_top_event", "系统故障"),
                    "gate": "OR",
                    "children": [],
                },
            }

        gold = _extract_gold_basic_events(sample)
        pred_events = _extract_pred_basic_events(pred)

        tp = len(gold & pred_events)
        fp = len(pred_events - gold)
        fn = len(gold - pred_events)
        p, r, f1 = _f1(tp, fp, fn)

        sum_tp += tp
        sum_fp += fp
        sum_fn += fn

        tree_valid, gate_valid = _validate_tree(pred.get("tree", {}))
        heuristic_logic_ok = _heuristic_logic_ok(sample, pred)

        tree_valid_cnt += 1 if tree_valid else 0
        gate_valid_cnt += 1 if gate_valid else 0
        if heuristic_logic_ok is not None:
            heuristic_logic_applicable_cnt += 1
            heuristic_logic_cnt += 1 if heuristic_logic_ok else 0

        ai_score = None
        ai_reason = ""
        strict_logic_ok: Optional[bool] = None
        if ai_judge:
            ai_score, ai_reason = _ai_logic_judge(sample, pred)
            if ai_score is not None:
                ai_scores.append(ai_score)
            strict_logic_ok = ai_score >= ai_logic_threshold
            strict_logic_cnt += 1 if strict_logic_ok else 0

        details.append(
            SampleResult(
                sample_id=sid,
                split=split,
                source_type=str(sample.get("source_type", "")),
                event_precision=p,
                event_recall=r,
                event_f1=f1,
                event_tp=tp,
                event_fp=fp,
                event_fn=fn,
                tree_valid=tree_valid,
                gate_valid=gate_valid,
                heuristic_logic_ok=heuristic_logic_ok,
                strict_logic_ok=strict_logic_ok,
                ai_logic_score=ai_score,
                ai_logic_reason=ai_reason,
                latency_ms=latency_ms,
                error=err,
            )
        )

    n = len(details)
    micro_p, micro_r, micro_f1 = _f1(sum_tp, sum_fp, sum_fn)
    avg_latency = (
        sum(d.latency_ms for d in details if isinstance(d.latency_ms, int))
        / len([d for d in details if isinstance(d.latency_ms, int)])
        if any(isinstance(d.latency_ms, int) for d in details)
        else None
    )

    summary = {
        "samples_evaluated": n,
        "mode": mode,
        "split_filter": split_filter,
        "basic_event_micro_precision": round(micro_p, 6),
        "basic_event_micro_recall": round(micro_r, 6),
        "basic_event_micro_f1": round(micro_f1, 6),
        "tree_valid_rate": round((tree_valid_cnt / n) if n else 0.0, 6),
        "gate_valid_rate": round((gate_valid_cnt / n) if n else 0.0, 6),
        "heuristic_logic_ok_rate": (
            round((heuristic_logic_cnt / heuristic_logic_applicable_cnt), 6)
            if heuristic_logic_applicable_cnt
            else None
        ),
        "strict_logic_ok_rate": round((strict_logic_cnt / n), 6) if (n and ai_judge) else None,
        "ai_logic_threshold": ai_logic_threshold if ai_judge else None,
        "ai_logic_score_avg": round((sum(ai_scores) / len(ai_scores)), 6) if ai_scores else None,
        "counts": {
            "event_tp": sum_tp,
            "event_fp": sum_fp,
            "event_fn": sum_fn,
            "tree_valid": tree_valid_cnt,
            "gate_valid": gate_valid_cnt,
            "heuristic_logic_ok": heuristic_logic_cnt,
            "heuristic_logic_applicable": heuristic_logic_applicable_cnt,
            "strict_logic_ok": strict_logic_cnt,
            "ai_scored": len(ai_scores),
        },
        "avg_latency_ms": round(avg_latency, 2) if avg_latency is not None else None,
    }

    return {
        "summary": summary,
        "details": [d.to_dict() for d in details],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate basic events and logic quality of FTA outputs")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET))
    parser.add_argument("--mode", choices=["api", "gold"], default="api")
    parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000/api/fta/generate")
    parser.add_argument("--split", choices=["all", "train", "dev", "test"], default="test")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--ai-judge", action="store_true")
    parser.add_argument("--ai-logic-threshold", type=float, default=0.8)
    parser.add_argument("--max-samples", type=int, default=0, help="0 means evaluate all samples")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    dataset = _read_json(Path(args.dataset))
    result = evaluate(
        dataset=dataset,
        mode=args.mode,
        api_url=args.api_url,
        split_filter=args.split,
        timeout_s=max(1, args.timeout),
        ai_judge=args.ai_judge,
        max_samples=max(0, args.max_samples),
        ai_logic_threshold=max(0.0, min(1.0, args.ai_logic_threshold)),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = Path(args.output) if args.output else RUNS_DIR / f"event_logic_report_{ts}.json"
    _write_json(output, result)

    s = result["summary"]
    print(f"[ok] report: {output}")
    print(f"[ok] samples: {s['samples_evaluated']} split={s['split_filter']} mode={s['mode']}")
    logic_rate = s.get("heuristic_logic_ok_rate")
    logic_text = f"{logic_rate:.2%}" if isinstance(logic_rate, (int, float)) else "N/A"
    print(
        "[ok] event_f1={:.2%} tree_valid={:.2%} gate_valid={:.2%} logic_ok={}".format(
            s["basic_event_micro_f1"],
            s["tree_valid_rate"],
            s["gate_valid_rate"],
            logic_text,
        )
    )
    if s.get("ai_logic_score_avg") is not None:
        print(f"[ok] ai_logic_score_avg={s['ai_logic_score_avg']:.4f}")
    if s.get("strict_logic_ok_rate") is not None:
        print(
            "[ok] strict_logic_ok_rate={:.2%} (threshold={:.2f})".format(
                s["strict_logic_ok_rate"],
                s["ai_logic_threshold"],
            )
        )


if __name__ == "__main__":
    main()
