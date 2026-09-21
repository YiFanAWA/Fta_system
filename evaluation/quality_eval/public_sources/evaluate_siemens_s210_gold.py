#!/usr/bin/env python3
"""Evaluate saved model predictions against the reviewed SINAMICS S210 gold set."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


FIELDS = ("fault_code", "description", "component", "related_components", "causes", "parameters")

# Evaluation-only aliases. These do not change persisted gold values or the
# extraction contract; they make bilingual public-manual annotations
# comparable without treating an omitted field as correct.
_COMPONENT_TERM_ALIASES = (
    ("控制单元", "controlunit"),
    ("control unit", "controlunit"),
    ("功率单元", "powerunit"),
    ("power unit", "powerunit"),
    ("驱动器", "drive"),
    ("drive", "drive"),
    ("编码器", "encoder"),
    ("encoder", "encoder"),
    ("内部软件", "internalsoftware"),
    ("internal software", "internalsoftware"),
    ("控制系统", "controlsystem"),
    ("control system", "controlsystem"),
    ("功能发生器", "functiongenerator"),
    ("function generator", "functiongenerator"),
    ("参数配置系统", "parameterconfigsystem"),
    ("安全集成运动监控", "simotionmonitoring"),
    ("安全集成运动", "simotion"),
    ("si motion", "simotion"),
    ("安全集成", "safetyintegrated"),
    ("safety integrated", "safetyintegrated"),
    ("电机", "motor"),
    ("motor", "motor"),
    ("传感器", "sensor"),
    ("sensor", "sensor"),
    ("插座", "socket"),
    ("socket", "socket"),
    ("线路", "line"),
    ("line", "line"),
)
_CAUSE_SPLIT_RE = re.compile(
    r"(?:possible\s+causes?\s*:\s*|可能原因\s*[:：]\s*|[;；\n]+|(?<=[.!?])\s+(?=[A-Z]))",
    re.IGNORECASE,
)
_CAUSE_PARAMETER_PAREN_RE = re.compile(
    r"\([^)]*\b[pr]\d+(?:\.\d+)?(?:\[[^\]]+\])?\s*=\s*[^)]*\)",
    re.IGNORECASE,
)
_SEMANTIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "the", "to", "was", "were", "with", "that",
    "this", "there", "then", "via", "when", "after", "during", "into", "must", "should",
}
_SEMANTIC_REPLACEMENTS = (
    ("取值", "值"),
    ("该参数", "参数"),
    ("导致", "因"),
    ("overheating", "overheat"),
    ("overheated", "overheat"),
    ("temperature too high", "overheat"),
    ("thermal overload", "overload"),
    ("failed", "fail"),
    ("failure", "fail"),
    ("errors", "error"),
    ("incorrectly", "incorrect"),
    ("incorrectly configured", "config error"),
    ("not successfully initialized", "initialization fail"),
    ("unable to", "cannot"),
    ("not able to", "cannot"),
    ("does not respond", "no response"),
    ("not responding", "no response"),
)
_SEMANTIC_ANCHORS = {
    "motor", "encoder", "control", "power", "drive", "server", "socket", "unit", "module",
    "component", "line", "system", "board", "function", "generator", "motion", "safety",
    "parameter", "firmware", "communication", "temperature", "thermal", "fault", "error",
    "overheat", "overload", "overflow", "synchron", "brake", "valve", "profi", "sto", "sbc",
}


def _normalize(value: Any) -> str:
    text = str(value or "").strip().casefold()
    return re.sub(r"\s+|[，。；：、,.!?:;\-_/()（）\[\]{}\"'`]+", "", text)


def _values(record: dict[str, Any], field: str) -> set[str]:
    value = record.get(field)
    values = value if field in {"related_components", "causes", "parameters"} else [value]
    return {_normalize(item) for item in values or [] if _normalize(item)}


def _normalize_component(value: Any) -> str:
    """Normalize bilingual component labels for evaluation only."""
    text = str(value or "").strip().casefold()
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    text = re.sub(r"\bcomponent\b|组件", "", text)
    for source, target in _COMPONENT_TERM_ALIASES:
        text = text.replace(source, target)
    return _normalize(text)


def _cause_units(value: Any) -> list[str]:
    """Split only explicit cause-list separators used by the source manual."""
    text = str(value or "").strip()
    if not text:
        return []
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = _CAUSE_PARAMETER_PAREN_RE.sub("", text)
    parts = [part.strip(" ，,。") for part in _CAUSE_SPLIT_RE.split(text) if part.strip(" ，,。")]
    expanded: list[str] = []
    for part in parts or [text]:
        compound = re.match(r"^(.*?)[（(]\s*(?:含|包括|包含)\s*(.+?)[）)]$", part)
        if compound:
            expanded.extend([compound.group(1).strip(), compound.group(2).strip()])
        else:
            expanded.append(part)
    return expanded


def _normalized_values(record: dict[str, Any], field: str) -> set[str]:
    value = record.get(field)
    values = value if field in {"related_components", "causes", "parameters"} else [value]
    if field in {"component", "related_components"}:
        normalized = {_normalize_component(item) for item in values or []}
    elif field == "causes":
        normalized = {_normalize(unit) for item in values or [] for unit in _cause_units(item)}
    else:
        normalized = {_normalize(item) for item in values or []}
    return {item for item in normalized if item}


def _semantic_tokens(value: Any) -> set[str]:
    """Create transparent, deterministic tokens for the L3/L4 policy."""
    text = str(value or "").casefold()
    text = _CAUSE_PARAMETER_PAREN_RE.sub(" ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\bsi\s+p(?=\d)", "sip", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    for source, target in sorted(_SEMANTIC_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    tokens = re.findall(r"[a-z0-9]+|[\u3400-\u9fff]+", text)
    normalized = set()
    for token in tokens:
        if re.fullmatch(r"[\u3400-\u9fff]+", token):
            normalized.add(token)
            normalized.update(token[index : index + 2] for index in range(len(token) - 1))
            continue
        if token in _SEMANTIC_STOPWORDS:
            continue
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 3:
            token = token[:-1]
        normalized.add(token)
    return normalized


def _description_semantic_score(gold: Any, predicted: Any) -> dict[str, Any]:
    """Score the confirmed L3 description equivalence policy.

    This is deliberately deterministic and auditable. It is not a claim that
    lexical overlap is a general-purpose semantic model; it implements the
    confirmed benchmark policy without calling another model during evaluation.
    """
    gold_text = str(gold or "").strip()
    predicted_text = str(predicted or "").strip()
    if not gold_text:
        return {"status": "unknown_gold_excluded", "score": 0.0}
    if not predicted_text:
        return {"status": "scored", "score": 0.0, "reason": "missing_prediction"}
    gold_tokens = _semantic_tokens(gold_text)
    predicted_tokens = _semantic_tokens(predicted_text)
    if not gold_tokens or not predicted_tokens:
        return {"status": "scored", "score": 0.0, "reason": "no_semantic_tokens"}
    if gold_tokens == predicted_tokens:
        return {"status": "scored", "score": 1.0, "reason": "semantic_token_exact"}
    overlap = gold_tokens & predicted_tokens
    gold_coverage = len(overlap) / len(gold_tokens)
    predicted_coverage = len(overlap) / len(predicted_tokens)
    gold_anchors = gold_tokens & _SEMANTIC_ANCHORS
    predicted_anchors = predicted_tokens & _SEMANTIC_ANCHORS
    if gold_anchors and not (gold_anchors & predicted_anchors):
        return {"status": "scored", "score": 0.0, "reason": "core_object_missing"}
    unsupported_anchors = predicted_anchors - gold_anchors
    if gold_coverage >= 0.75 and predicted_coverage >= 0.60 and not unsupported_anchors:
        return {"status": "scored", "score": 1.0, "reason": "core_proposition_preserved"}
    if gold_coverage >= 0.50 and predicted_coverage >= 0.35 and (gold_anchors & predicted_anchors or not gold_anchors):
        return {"status": "scored", "score": 0.5, "reason": "partial_core_proposition"}
    return {"status": "scored", "score": 0.0, "reason": "insufficient_equivalence"}


def _cause_units_from_value(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    units = []
    for item in values:
        units.extend(_cause_units(item))
    return units


def _official_causes_score(gold: Any, predicted: Any) -> dict[str, Any]:
    """Apply L4 coverage * precision after cause splitting."""
    gold_units = _cause_units_from_value(gold)
    predicted_units = _cause_units_from_value(predicted)
    if not gold_units:
        return {"status": "unknown_gold_excluded", "score": 0.0}
    if not predicted_units:
        return {
            "status": "scored",
            "coverage": 0.0,
            "precision": 0.0,
            "score": 0.0,
            "matched_gold": 0,
            "gold_count": len(gold_units),
            "predicted_count": 0,
        }
    used_gold: set[int] = set()
    matched_predicted = 0
    matched_gold = 0
    for predicted_unit in predicted_units:
        candidates = []
        for index, gold_unit in enumerate(gold_units):
            if index in used_gold:
                continue
            gold_compact = _normalize(gold_unit)
            predicted_compact = _normalize(predicted_unit)
            if (
                gold_compact
                and predicted_compact
                and (gold_compact in predicted_compact or predicted_compact in gold_compact)
                and min(len(gold_compact), len(predicted_compact))
                / max(len(gold_compact), len(predicted_compact))
                >= 0.45
            ):
                result = {"score": 1.0, "status": "scored", "reason": "cause_core_contained"}
            else:
                result = _description_semantic_score(gold_unit, predicted_unit)
            candidates.append((float(result.get("score", 0.0)), index))
        if not candidates:
            continue
        best_score, best_index = max(candidates)
        if best_score >= 0.5:
            used_gold.add(best_index)
            matched_predicted += 1
            matched_gold += 1
    coverage = matched_gold / len(gold_units)
    precision = matched_predicted / len(predicted_units)
    return {
        "status": "scored",
        "coverage": round(coverage, 6),
        "precision": round(precision, 6),
        "score": round(coverage * precision, 6),
        "matched_gold": matched_gold,
        "gold_count": len(gold_units),
        "predicted_count": len(predicted_units),
    }


def _macro_soft_metrics(scores: list[dict[str, Any]], *, metric_kind: str) -> dict[str, Any]:
    scored = [item for item in scores if item.get("status") == "scored"]
    if not scored:
        return {
            "metric_kind": metric_kind,
            "scored_samples": 0,
            "unknown_gold_excluded": len(scores),
            "metrics": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
        }
    if metric_kind == "l4_coverage_times_precision":
        precision = sum(float(item.get("precision", 0.0)) for item in scored) / len(scored)
        recall = sum(float(item.get("coverage", 0.0)) for item in scored) / len(scored)
        f1 = sum(float(item.get("score", 0.0)) for item in scored) / len(scored)
    else:
        precision = recall = f1 = sum(float(item.get("score", 0.0)) for item in scored) / len(scored)
    return {
        "metric_kind": metric_kind,
        "scored_samples": len(scored),
        "unknown_gold_excluded": len(scores) - len(scored),
        "metrics": {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        },
    }


def _score(gold: set[str], predicted: set[str]) -> dict[str, Any]:
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


def _metrics(counts: dict[str, int]) -> dict[str, float]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    value = _read_json(path)
    rows = value.get("predictions") if isinstance(value.get("predictions"), list) else value.get("samples")
    if not isinstance(rows, list):
        raise ValueError("predictions JSON must contain a predictions or samples list")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        sample_id = str(row.get("sample_id", "")).strip()
        prediction = row.get("prediction") if isinstance(row.get("prediction"), dict) else row
        if sample_id and isinstance(prediction, dict):
            result[sample_id] = prediction
    return result


def evaluate(gold: dict[str, Any], predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    details = []
    totals = {field: Counter() for field in FIELDS}
    normalized_totals = {field: Counter() for field in FIELDS}
    official_soft_scores = {"description": [], "causes": []}
    for sample in gold.get("samples", []):
        sample_id = str(sample.get("sample_id", ""))
        gold_records = sample.get("gold_records") if isinstance(sample.get("gold_records"), list) else []
        gold_record = gold_records[0] if gold_records and isinstance(gold_records[0], dict) else {}
        prediction = predictions.get(sample_id, {})
        pred_records = prediction.get("records")
        if not isinstance(pred_records, list):
            extracted = prediction.get("extracted_faults")
            pred_records = extracted.get("records") if isinstance(extracted, dict) else []
        pred_record = pred_records[0] if pred_records and isinstance(pred_records[0], dict) else {}
        field_scores = {}
        normalized_field_scores = {}
        official_field_scores = {}
        for field in FIELDS:
            score = _score(_values(gold_record, field), _values(pred_record, field))
            field_scores[field] = score
            totals[field].update({key: int(score.get(key, 0)) for key in ("tp", "fp", "fn", "predicted_unknown")})
            normalized_score = _score(
                _normalized_values(gold_record, field),
                _normalized_values(pred_record, field),
            )
            normalized_field_scores[field] = normalized_score
            normalized_totals[field].update(
                {key: int(normalized_score.get(key, 0)) for key in ("tp", "fp", "fn", "predicted_unknown")}
            )
            if field in {"fault_code", "component", "related_components", "parameters"}:
                official_field_scores[field] = {
                    "metric_kind": "canonical_exact",
                    **normalized_score,
                }
        description_score = _description_semantic_score(
            gold_record.get("description"), pred_record.get("description")
        )
        causes_score = _official_causes_score(
            gold_record.get("causes"), pred_record.get("causes")
        )
        official_soft_scores["description"].append(description_score)
        official_soft_scores["causes"].append(causes_score)
        official_field_scores["description"] = {
            "metric_kind": "l3_semantic_macro",
            **description_score,
        }
        official_field_scores["causes"] = {
            "metric_kind": "l4_coverage_times_precision",
            **causes_score,
        }
        details.append(
            {
                "sample_id": sample_id,
                "missing_prediction": sample_id not in predictions,
                "field_scores": field_scores,
                "normalized_field_scores": normalized_field_scores,
                "official_field_scores": official_field_scores,
            }
        )

    field_metrics = {
        field: {
            "counts": dict(totals[field]),
            "metrics": _metrics({key: int(totals[field][key]) for key in ("tp", "fp", "fn")}),
        }
        for field in FIELDS
    }
    normalized_field_metrics = {
        field: {
            "counts": dict(normalized_totals[field]),
            "metrics": _metrics({key: int(normalized_totals[field][key]) for key in ("tp", "fp", "fn")}),
        }
        for field in FIELDS
    }
    official_field_metrics = {}
    for field in ("fault_code", "component", "related_components", "parameters"):
        official_field_metrics[field] = {
            "metric_kind": "canonical_exact",
            "counts": dict(normalized_totals[field]),
            "metrics": _metrics({key: int(normalized_totals[field][key]) for key in ("tp", "fp", "fn")}),
        }
    official_field_metrics["description"] = _macro_soft_metrics(
        official_soft_scores["description"], metric_kind="l3_semantic_macro"
    )
    official_field_metrics["causes"] = _macro_soft_metrics(
        official_soft_scores["causes"], metric_kind="l4_coverage_times_precision"
    )
    gold_status = gold.get("gold_status") if isinstance(gold.get("gold_status"), dict) else {}
    f1_ready = bool(gold_status.get("f1_ready"))
    return {
        "report_type": "siemens_s210_public_fault_expert_gold_f1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "completed" if f1_ready else "diagnostic_completed",
        "evaluation_scope": "official" if f1_ready else "diagnostic_only",
        "samples_evaluated": len(details),
        "prediction_samples": len(predictions),
        "field_metrics": field_metrics,
        "normalized_field_metrics": normalized_field_metrics,
        "official_field_metrics": official_field_metrics,
        "normalization_policy": {
            "component": "中英组件别名归一化；空组件仍然是漏抽，不因归一化变成正确。",
            "description": "L3：核心命题保留时允许同义词、主动被动和句式重组；完全等价=1，部分等价=0.5，不等价=0。",
            "causes": "L4：剥离 Possible causes 前缀、忽略符合规则的参数下标，按原因单元计算 coverage * precision。",
            "other_fields": "沿用严格规范化字符串匹配。",
        },
        "details": details,
        "interpretation": (
            "official_field_metrics 对故障码、组件、关联组件、参数使用规范化后的精确集合匹配；"
            "description 使用 L3 确定性语义近似，causes 使用 L4 coverage * precision；空金标字段不计入漏召回。"
            + (
                "当前 gold_status.f1_ready=true，因此报告可作为正式字段 F1；AND/OR 逻辑门不在本次范围。"
                if f1_ready
                else "当前 gold_status.f1_ready=false，因此本报告只能作为诊断性结果，不能宣称为正式语义 F1。"
            )
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    gold = _read_json(args.gold)
    if args.predictions is None:
        report = {
            "report_type": "siemens_s210_public_fault_expert_gold_f1",
            "status": "blocked_missing_predictions",
            "gold_samples": len(gold.get("samples", [])),
            "reason": "缺少独立模型预测文件；不能用金标自身或复制结果冒充 F1。",
            "next_input": "--predictions <独立模型预测 JSON>",
        }
    else:
        report = evaluate(gold, _load_predictions(args.predictions))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output}")


if __name__ == "__main__":
    main()
