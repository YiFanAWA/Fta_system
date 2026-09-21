#!/usr/bin/env python3
"""Evaluate the unified user-accepted expert review set without new API calls."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_EVALUATOR = ROOT / "evaluation/quality_eval/public_sources/evaluate_siemens_s210_gold.py"


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("unified_public_evaluator", PUBLIC_EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load evaluator: {PUBLIC_EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _predictions(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(sample["sample_id"]): {
            "records": [sample["model_prediction"]["record"]],
        }
        for sample in dataset.get("samples", [])
    }


def _subset(
    dataset: dict[str, Any],
    name: str,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    f1_ready: bool,
) -> dict[str, Any]:
    value = copy.deepcopy(dataset)
    value["samples"] = [sample for sample in value.get("samples", []) if predicate(sample)]
    value.setdefault("gold_status", {})["f1_ready"] = f1_ready
    value["gold_status"]["evaluation_subset"] = name
    return value


def _decision_counts(samples: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"审核通过": 0, "证据不足": 0, "语义需修改": 0, "无法判断": 0}
    for sample in samples:
        decision = sample.get("expert_review", {}).get("decision")
        if decision in counts:
            counts[decision] += 1
    return counts


def evaluate_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    evaluator = _load_evaluator()
    samples = list(dataset.get("samples", []))
    scopes = {
        "all_57_diagnostic": (lambda _sample: True, False),
        "value_confirmed_56": (
            lambda sample: sample.get("expert_review", {}).get("decision") != "无法判断",
            False,
        ),
        "fully_supported_50": (
            lambda sample: sample.get("expert_review", {}).get("decision")
            in {"审核通过", "语义需修改"},
            True,
        ),
        "approved_42": (
            lambda sample: sample.get("expert_review", {}).get("decision") == "审核通过",
            True,
        ),
    }
    reports: dict[str, Any] = {}
    for name, (predicate, f1_ready) in scopes.items():
        scoped = _subset(dataset, name, predicate, f1_ready=f1_ready)
        result = evaluator.evaluate(scoped, _predictions(scoped))
        result["review_decision_counts"] = _decision_counts(scoped["samples"])
        result["sample_ids"] = [sample["sample_id"] for sample in scoped["samples"]]
        result["interpretation_scope"] = {
            "all_57_diagnostic": "包含全部审核结果，只用于查看整体误差，不作为正式 F1。",
            "value_confirmed_56": "排除 1 条无法判断；仍包含 6 条证据不足，因此仍是诊断口径。",
            "fully_supported_50": "只包含审核通过和语义修正后的记录，可作为字段 F1 候选口径。",
            "approved_42": "只查看原始抽取直接通过的记录，用于观察无修正样本表现。",
        }[name]
        reports[name] = result

    reports["review_summary"] = {
        "total": len(samples),
        "decision_counts": _decision_counts(samples),
        "corrected_records": [
            sample["sample_id"]
            for sample in samples
            if sample.get("expert_review", {}).get("correction_applied")
        ],
        "logic_gate": "excluded; all current gate_type values remain unknown",
    }
    return reports


def _metric_line(metrics: dict[str, Any], field: str) -> str:
    item = metrics.get(field, {})
    values = item.get("metrics", {})
    return "| {} | {:.4f} | {:.4f} | {:.4f} |".format(
        field,
        float(values.get("precision", 0.0)),
        float(values.get("recall", 0.0)),
        float(values.get("f1", 0.0)),
    )


def render_markdown(reports: dict[str, Any]) -> str:
    lines = [
        "# FTA 57条用户确认专家审核集 F1 诊断报告",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "数据来源：`fta_unified_expert_review_57_2026-09-20.json`",
        "说明：本报告不调用新模型，只对已保存的模型抽取结果和专家修正结果进行离线重评分。",
        "",
        "## 审核结果分布",
        "",
    ]
    summary = reports["review_summary"]
    for decision, count in summary["decision_counts"].items():
        lines.append(f"- {decision}：{count} 条")
    lines.extend(
        [
            "",
            "## 三种评估口径",
            "",
            "| 口径 | 样本数 | 作用 |",
            "|---|---:|---|",
            "| all_57_diagnostic | 57 | 全量误差诊断，不作为正式 F1 |",
            "| value_confirmed_56 | 56 | 排除无法判断记录，仍含证据不足记录 |",
            "| fully_supported_50 | 50 | 只含审核通过和语义修正记录，可作为 F1 候选 |",
            "| approved_42 | 42 | 只观察原始结果直接通过的记录 |",
        ]
    )
    for name in ("all_57_diagnostic", "value_confirmed_56", "fully_supported_50", "approved_42"):
        result = reports[name]
        lines.extend(
            [
                "",
                f"## {name}",
                "",
                result["interpretation_scope"],
                "",
                "| 字段 | Precision | Recall | F1 |",
                "|---|---:|---:|---:|",
            ]
        )
        metrics = result.get("official_field_metrics", {})
        for field in ("fault_code", "component", "related_components", "description", "causes", "parameters"):
            lines.append(_metric_line(metrics, field))
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- `fully_supported_50` 是当前最适合用于字段 F1 的候选口径，但仍不评价 AND/OR 逻辑门。",
            "- 6 条“证据不足”记录保留在数据集中，用于修复证据绑定，不应静默删除。",
            "- 1 条“无法判断”记录保留在数据集中，等待后续补充资料或规则确认。",
            "- 该数据集仍属于测试/评估集，不直接用于训练模型。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    reports = evaluate_dataset(_load(args.dataset))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(reports), encoding="utf-8")
    print(json.dumps(reports["review_summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
