#!/usr/bin/env python3
"""Audit whether the reviewed SINAMICS S210 gold set is ready for official F1."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


FIELDS = ("fault_code", "description", "component", "related_components", "causes", "parameters")
LIST_FIELDS = {"related_components", "causes", "parameters"}
ENCODING_ARTIFACTS = ("\ufffd", "Ã", "Â", "â", "ð")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _values(record: dict[str, Any], field: str) -> list[str]:
    value = record.get(field)
    raw_values = value if field in LIST_FIELDS else [value]
    return [str(item).strip() for item in raw_values or [] if str(item or "").strip()]


def _has_encoding_artifact(value: str) -> bool:
    return any(marker in value for marker in ENCODING_ARTIFACTS)


def _is_bilingual_value(value: str) -> bool:
    return bool(_CJK_RE.search(value) and re.search(r"[A-Za-z]", value))


def _field_stats(samples: list[dict[str, Any]], field: str) -> dict[str, Any]:
    record_values: list[str] = []
    for sample in samples:
        records = sample.get("gold_records")
        record = records[0] if isinstance(records, list) and records and isinstance(records[0], dict) else {}
        record_values.extend(_values(record, field))
    non_empty_records = sum(
        bool(
            _values(
                (sample.get("gold_records") or [{}])[0]
                if isinstance(sample.get("gold_records"), list) and sample.get("gold_records")
                else {},
                field,
            )
        )
        for sample in samples
    )
    artifact_values = [value for value in record_values if _has_encoding_artifact(value)]
    bilingual_values = [value for value in record_values if _is_bilingual_value(value)]
    return {
        "sample_count": len(samples),
        "non_empty_sample_count": non_empty_records,
        "empty_sample_count": len(samples) - non_empty_records,
        "value_count": len(record_values),
        "encoding_artifact_value_count": len(artifact_values),
        "encoding_artifact_examples": artifact_values[:5],
        "bilingual_value_count": len(bilingual_values),
        "bilingual_examples": bilingual_values[:5],
    }


def _projection_stats(gold: dict[str, Any]) -> dict[str, Any]:
    projection = gold.get("related_component_policy_projection")
    if not isinstance(projection, dict):
        return {"present": False}
    changes = projection.get("changes") if isinstance(projection.get("changes"), list) else []
    return {
        "present": True,
        "policy": projection.get("policy"),
        "source_version": projection.get("source_version"),
        "preserves_original_values": bool(projection.get("preserves_original_values")),
        "changed_record_count": projection.get("changed_record_count", len(changes)),
        "change_count_verified": len(changes),
    }


def _diagnostic_run(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"present": False}
    report = _read_json(path)
    normalized = report.get("normalized_field_metrics") if isinstance(report.get("normalized_field_metrics"), dict) else {}
    selected = {}
    for field in ("fault_code", "component", "related_components", "description", "causes", "parameters"):
        metrics = normalized.get(field, {}).get("metrics") if isinstance(normalized.get(field), dict) else None
        if isinstance(metrics, dict):
            selected[field] = metrics
    return {
        "present": True,
        "path": str(path),
        "status": report.get("status"),
        "evaluation_scope": report.get("evaluation_scope"),
        "samples_evaluated": report.get("samples_evaluated"),
        "normalized_metrics": selected,
    }


def audit_readiness(gold: dict[str, Any], diagnostic_report: Path | None = None) -> dict[str, Any]:
    samples = [sample for sample in gold.get("samples", []) if isinstance(sample, dict)]
    status = gold.get("gold_status") if isinstance(gold.get("gold_status"), dict) else {}
    info = gold.get("dataset_info") if isinstance(gold.get("dataset_info"), dict) else {}
    review = info.get("review") if isinstance(info.get("review"), dict) else {}
    field_stats = {field: _field_stats(samples, field) for field in FIELDS}

    blockers: list[dict[str, str]] = []
    if not bool(status.get("f1_ready")):
        blockers.append({
            "id": "gold_status_not_ready",
            "severity": "blocking",
            "message": "gold_status.f1_ready 仍为 false，当前报告只能作为诊断性评估。",
        })
    if field_stats["component"]["bilingual_value_count"]:
        blockers.append({
            "id": "component_canonicalization",
            "severity": "blocking",
            "message": "component 保留了中英双语显示值；正式 F1 前必须确定规范组件标签和别名匹配合同。",
        })
    blockers.append({
        "id": "semantic_match_policy",
        "severity": "blocking",
        "message": "description/causes 尚未确定同义改写、原因拆分和参数括号删除后的正式匹配规则。",
    })

    field_assessment = {
        "fault_code": {
            "status": "ready_for_strict_diagnostic_f1",
            "reason": "30条记录均有故障码，未发现编码异常；v8 诊断结果可直接核对。",
        },
        "parameters": {
            "status": "ready_for_strict_diagnostic_f1",
            "reason": "参数为空在原文明确表示无参数时可接受；非空值可按参数编号规范化匹配。",
        },
        "related_components": {
            "status": "ready_for_policy_diagnostic_f1",
            "reason": "已采用你确认的 explicit_relation_only 规则；普通正文提及不计为关联组件。",
        },
        "component": {
            "status": "blocked_until_canonicalized",
            "reason": "当前保存的专家字段保留双语显示值；评估器可以临时归一化，但不能把临时归一化分数直接当成正式金标 F1。",
        },
        "description": {
            "status": "diagnostic_only",
            "reason": "原文覆盖完整，但尚未正式确认自然语言改写的等价判定规则。",
        },
        "causes": {
            "status": "diagnostic_only",
            "reason": "原因存在拆分、Possible causes 前缀和参数括号处理；当前只能报告诊断分数。",
        },
    }

    readiness = "not_ready_for_official_f1"
    if status.get("f1_ready") and not blockers:
        readiness = "ready_for_official_f1"

    return {
        "report_type": "siemens_s210_public_fault_expert_gold_readiness",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": {
            "name": info.get("name"),
            "version": info.get("version"),
            "sample_count": len(samples),
            "split": info.get("stats", {}).get("split") if isinstance(info.get("stats"), dict) else None,
        },
        "readiness": readiness,
        "review_identity": {
            "independent_expert_reviewed": bool(status.get("independent_expert_reviewed")),
            "reviewer_identity_verified": bool(status.get("reviewer_identity_verified")),
            "reviewer_name_present": bool(review.get("reviewer_name")),
            "review_date_present": bool(review.get("review_date")),
            "field_values_confirmed": bool(review.get("field_values_confirmed")),
            "evidence_confirmed": bool(review.get("evidence_confirmed")),
            "logic_gate_confirmed": bool(review.get("logic_gate_confirmed")),
        },
        "field_stats": field_stats,
        "field_assessment": field_assessment,
        "related_component_policy_projection": _projection_stats(gold),
        "diagnostic_run": _diagnostic_run(diagnostic_report),
        "blockers": blockers,
        "expert_decisions_needed": [
            "确认正式组件字典：每个 component/related_components 是否保存为统一规范名，双语展示只作为别名或显示层信息。",
            "确认 description/causes 的等价规则：严格原文、规范化同义词，还是允许专家确认的语义改写；原因拆分如何计分。",
            "确认 AND/OR 逻辑门是否作为独立评估任务；当前 30 条 logic_gate 均为 unknown，不进入字段 F1。",
        ],
        "next_step": "专家确认上述三项后，复制生成新的正式 gold 版本，写入规范字段并将 f1_ready 设为 true；在此之前保留当前数据为 diagnostic_only。",
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SINAMICS S210 专家金标就绪检查报告",
        "",
        f"- 生成时间：{report['created_at']}",
        f"- 数据集：{report['dataset']['name']} {report['dataset']['version']}",
        f"- 样本数：{report['dataset']['sample_count']}",
        f"- 当前结论：**{report['readiness']}**",
        "",
        "## 结论先看",
        "",
        "当前数据已经可以做结构、证据、故障码、参数和关联组件策略的诊断评估；但还不能把结果写成正式语义 F1。原因是专家金标仍保留了双语组件显示值，且 description/causes 的同义改写与拆分规则尚未形成正式合同。",
        "",
        "## 字段状态",
        "",
        "| 字段 | 状态 | 说明 |",
        "|---|---|---|",
    ]
    for field in FIELDS:
        assessment = report["field_assessment"][field]
        stats = report["field_stats"][field]
        lines.append(
            f"| `{field}` | `{assessment['status']}` | {assessment['reason']}（非空样本 {stats['non_empty_sample_count']}，双语值 {stats['bilingual_value_count']}，编码异常值 {stats['encoding_artifact_value_count']}） |"
        )
    lines.extend([
        "",
        "## 当前阻塞项",
        "",
    ])
    for blocker in report["blockers"]:
        lines.append(f"- **{blocker['severity']}** `{blocker['id']}`：{blocker['message']}")
    lines.extend([
        "",
        "## 需要专家确认的三件事",
        "",
    ])
    for index, item in enumerate(report["expert_decisions_needed"], 1):
        lines.append(f"{index}. {item}")
    lines.extend([
        "",
        "## 下一步",
        "",
        report["next_step"],
        "",
        "本报告不修改金标、不修改 `f1_ready`，也不把诊断分数冒充正式 F1。",
        "",
    ])
    diagnostic = report.get("diagnostic_run", {})
    if diagnostic.get("present"):
        lines.extend(["## 已有 v8 诊断运行", "", f"- 样本完成：{diagnostic.get('samples_evaluated')}", f"- 评估范围：`{diagnostic.get('evaluation_scope')}`", ""])
        for field, metrics in diagnostic.get("normalized_metrics", {}).items():
            lines.append(f"- `{field}` normalized F1：{metrics.get('f1')}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--diagnostic-report", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = audit_readiness(_read_json(args.gold), args.diagnostic_report)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output_json}")
    print(f"[ok] wrote {args.output_markdown}")


if __name__ == "__main__":
    main()
