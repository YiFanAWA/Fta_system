"""Build a material-backed manual review bundle for Router and sufficiency.

The bundle is a review artifact, not a Gold dataset. It preserves source
paths, source-record identifiers, evidence snippets, machine diagnostics and
blank human decisions in one versioned package.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _signal_items(scope: dict[str, Any], group: str) -> list[dict[str, str]]:
    values = scope.get(group, {})
    if isinstance(values, list):
        return [{"term": str(value), "status": "confirmed"} for value in values]
    result: list[dict[str, str]] = []
    for status in ("confirmed", "pending_manual_confirmation"):
        for value in values.get(status, []):
            result.append({"term": str(value), "status": status})
    return result


def _find_evidence(samples: Iterable[dict[str, Any]], term: str, limit: int = 3) -> list[dict[str, str]]:
    escaped = re.escape(term)
    if term.casefold() == "jasc":
        pattern = re.compile(r"\bJASC(?:Code)?\b", re.IGNORECASE)
    elif term.casefold() in {"sdr", "faa"}:
        pattern = re.compile(rf"\b{escaped}\b|{escaped}(?=Code|Form|$)", re.IGNORECASE)
    else:
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
    evidence: list[dict[str, str]] = []
    for sample in samples:
        text = str(sample.get("input_text") or "")
        match = pattern.search(text)
        if not match:
            continue
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 180)
        evidence.append(
            {
                "sample_id": str(sample.get("sample_id") or sample.get("source_record_id") or ""),
                "source_record_id": str(sample.get("source_record_id") or ""),
                "quote": text[start:end].replace("\n", " "),
            }
        )
        if len(evidence) >= limit:
            break
    return evidence


def _entity_evidence(
    entity_ids: Iterable[str],
    siemens_samples: Iterable[dict[str, Any]],
    aerospace_samples: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    siemens_by_code = {
        str(record.get("fault_code", "")).upper(): (sample, record)
        for sample in siemens_samples
        for record in sample.get("gold_records", [])
        if record.get("fault_code")
    }
    aerospace_by_record = {
        str(sample.get("source_record_id") or sample.get("raw_record", {}).get("OperatorControlNumber", "")): sample
        for sample in aerospace_samples
    }
    result: list[dict[str, Any]] = []
    for entity_id in entity_ids:
        code = str(entity_id).rsplit(":", 1)[-1].upper()
        if code in siemens_by_code:
            sample, record = siemens_by_code[code]
            text = str(sample.get("input_text") or "")
            result.append(
                {
                    "entity_id": entity_id,
                    "sample_id": sample.get("sample_id"),
                    "fault_code": record.get("fault_code"),
                    "source_file": sample.get("source_file"),
                    "structured_gold": {
                        "description": record.get("description"),
                        "causes": record.get("causes", []),
                        "parameters": record.get("parameters", []),
                    },
                    "raw_evidence_quote": text[:900],
                }
            )
            continue
        if code in aerospace_by_record:
            sample = aerospace_by_record[code]
            raw = sample.get("raw_record", {})
            result.append(
                {
                    "entity_id": entity_id,
                    "sample_id": sample.get("sample_id"),
                    "source_record_id": sample.get("source_record_id"),
                    "jasc_code": raw.get("JASCCode"),
                    "raw_evidence_quote": str(sample.get("input_text") or "")[:900],
                }
            )
    return result


def _source_materials(paths: dict[str, Path], datasets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    siemens_info = datasets["siemens"].get("dataset_info", {})
    faa_source = datasets["aerospace"].get("source", {})
    return [
        {
            "material_id": "siemens_s210_public_fault_gold_candidate",
            "path": str(paths["siemens"]),
            "material_type": "public_manual_derived_record_set",
            "record_count": len(datasets["siemens"].get("samples", [])),
            "authority": siemens_info.get("review_authority"),
            "limitation": "AI-assisted review; explicitly not equivalent to a human domain expert review.",
        },
        {
            "material_id": "faa_sdr_2024_public_sample",
            "path": str(paths["aerospace"]),
            "material_type": "public_raw_development_sample",
            "record_count": len(datasets["aerospace"].get("samples", [])),
            "authority": faa_source.get("provider"),
            "source_url": faa_source.get("source_url"),
            "limitation": "Adapter-development sample; not an expert Gold set.",
        },
        {
            "material_id": "mixed_domain_router_comparison",
            "path": str(paths["router_report"]),
            "material_type": "frozen_mixed_domain_diagnostic",
            "record_count": len(datasets["router_report"].get("queries", [])),
            "authority": "benchmark plus deterministic evaluation harness",
            "limitation": "Router and retrieval diagnostic; not a human label source.",
        },
    ]


def build(args: argparse.Namespace) -> dict[str, Any]:
    registry = _read(args.registry)
    taxonomy = _read(args.taxonomy)
    sufficiency = _read(args.sufficiency)
    router_report = _read(args.router_report)
    siemens = _read(args.siemens)
    aerospace = _read(args.aerospace)
    datasets = {
        "siemens": siemens,
        "aerospace": aerospace,
        "router_report": router_report,
    }
    samples_by_scope = {
        "siemens_s210": siemens.get("samples", []),
        "faa_sdr": aerospace.get("samples", []),
    }

    signal_review: list[dict[str, Any]] = []
    for scope_id, scope in registry["scopes"].items():
        for group in ("high_signal", "medium_signal"):
            for item in _signal_items(scope, group):
                signal_review.append(
                    {
                        "scope_id": scope_id,
                        "domain": scope.get("domain"),
                        "manufacturer": scope.get("manufacturer"),
                        "system": scope.get("system"),
                        "signal_group": group,
                        "term": item["term"],
                        "registry_status": item["status"],
                        "positive_presence_evidence": _find_evidence(samples_by_scope[scope_id], item["term"]),
                        "uniqueness_status": "requires_human_confirmation",
                        "human_judgement": None,
                        "approved_router_role": None,
                        "human_notes": None,
                    }
                )

    suff_by_id = {row["query_id"]: row for row in sufficiency["queries"]}
    router_by_id = {row["query_id"]: row for row in router_report["queries"]}
    taxonomy_by_id = {row["query_id"]: row for row in taxonomy["cross_domain_rows"]}
    all_query_reviews: list[dict[str, Any]] = []
    for query_id, router_row in router_by_id.items():
        suff_row = suff_by_id[query_id]
        all_query_reviews.append(
            {
                "query_id": query_id,
                "query": router_row["query"],
                "query_type": router_row.get("query_type"),
                "benchmark_expected_domain": router_row.get("query_domain"),
                "relevant_entity_ids": router_row.get("relevant_entity_ids", []),
                "relevant_entity_evidence": _entity_evidence(
                    router_row.get("relevant_entity_ids", []),
                    siemens.get("samples", []),
                    aerospace.get("samples", []),
                ),
                "router_machine_decision": router_row.get("router"),
                "sufficiency_machine_decision": suff_row.get("sufficiency"),
                "taxonomy_machine_decision": taxonomy_by_id.get(query_id),
                "human_domain_decision": None,
                "human_sufficiency_decision": None,
                "human_action_decision": None,
                "human_notes": None,
            }
        )

    cross_domain_reviews = [row for row in all_query_reviews if row["router_machine_decision"]["mode"] == "cross_domain"]
    return {
        "bundle_info": {
            "name": "domain_router_manual_review_bundle_v1",
            "version": "2026-09-21",
            "status": "awaiting_human_review",
            "is_gold": False,
            "changes_router": False,
            "changes_retrieval": False,
            "human_review_required": True,
            "scope": "all registry signals + all mixed-domain queries + focused cross-domain review",
        },
        "materials": _source_materials(
            {
                "siemens": args.siemens,
                "aerospace": args.aerospace,
                "router_report": args.router_report,
            },
            datasets,
        ),
        "signal_review": signal_review,
        "cross_domain_review": cross_domain_reviews,
        "all_query_review": all_query_reviews,
        "review_contract": {
            "domain_decisions": ["industrial_drive", "aerospace", "both_or_ambiguous", "cannot_determine"],
            "sufficiency_decisions": ["sufficient", "partially_sufficient", "insufficient", "cannot_determine"],
            "action_decisions": ["scope_industrial_drive", "scope_aerospace", "cross_domain", "clarify_first"],
            "promotion_rule": "only human-confirmed signals may move from pending_manual_confirmation to confirmed",
            "clarification_rule": "insufficient queries should not be forced into a domain; record the missing information to request",
        },
        "final_review": {
            "reviewer": None,
            "review_date": None,
            "a_signal_conclusion": None,
            "query_sufficiency_gold_ready": None,
            "router_v2_allowed": None,
            "notes": None,
        },
    }


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render(report: dict[str, Any]) -> str:
    info = report["bundle_info"]
    lines = [
        "# Domain Router / Query Sufficiency 完整人工审核材料包 v1",
        "",
        f"状态：`{info['status']}`；不是 Gold；不会自动修改 Router 或 Retrieval。",
        "",
        "## 一、审核范围",
        "",
        "这不是片段式提问，而是把当前所有需要人工确认的材料集中到一份包中：",
        "",
        "- 注册表中全部领域信号：已确认词、待确认词、正向原文证据；",
        "- 全部 79 条混合域查询：领域、相关实体、Router 决策、充分性机器判断和人工空白栏；",
        "- 重点 22 条 `cross_domain` 查询：要求人工决定应 scope、保持跨域还是先澄清；",
        "- 澄清问题与 Router v2 放行结论。",
        "",
        "## 二、材料来源与限制",
        "",
        "| 材料 | 用途 | 限制 |",
        "|---|---|---|",
    ]
    for material in report["materials"]:
        lines.append(f"| `{_cell(material['material_id'])}` | `{_cell(material['path'])}` | {_cell(material['limitation'])} |")
    lines.extend([
        "",
        "正向出现证据只能证明该词在领域材料中出现，不能单独证明它对其他领域具有唯一性；“是否可以缩小 scope”仍必须由专家确认。",
        "",
        "## 三、全部领域信号确认",
        "",
        "| Scope | 组别 | 词 | 注册状态 | 原文证据 | 专家判断 | Router 角色 | 备注 |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for row in report["signal_review"]:
        evidence = row["positive_presence_evidence"]
        quote = evidence[0]["quote"] if evidence else "未在当前样本中找到直接出现证据"
        lines.append(
            f"| {_cell(row['scope_id'])} | {_cell(row['signal_group'])} | `{_cell(row['term'])}` | {_cell(row['registry_status'])} | {_cell(quote)} |  |  |  |"
        )
    lines.extend([
        "",
        "专家填写：",
        "- 判断：`是 / 条件是 / 否 / 无法判断`；",
        "- Router 角色：`high_signal / medium_signal / 不加入`；",
        "- 必须说明是否需要与厂商、系统或故障码联合出现。",
        "",
        "## 四、22 条 cross-domain 重点确认",
        "",
        "| Query | 查询 | 机器领域标签 | 机器充分性 | 相关实体/故障 | 材料记录 | 人工领域结论 | 人工充分性 | 最终动作 | 备注 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in report["cross_domain_review"]:
        tax = row.get("taxonomy_machine_decision") or {}
        suff = row.get("sufficiency_machine_decision") or {}
        evidence = row.get("relevant_entity_evidence") or []
        evidence_ids = ", ".join(str(item.get("sample_id")) for item in evidence if item.get("sample_id")) or "无"
        lines.append(
            f"| {_cell(row['query_id'])} | {_cell(row['query'])} | {_cell(tax.get('classification', '未分类'))} | {_cell(suff.get('level'))} ({_cell(suff.get('sufficiency_score'))}) | {_cell(', '.join(row['relevant_entity_ids']))} | {_cell(evidence_ids)} |  |  |  |"
        )
    lines.extend([
        "",
        "人工领域结论：`industrial_drive / aerospace / both_or_ambiguous / cannot_determine`。",
        "人工充分性：`sufficient / partially_sufficient / insufficient / cannot_determine`。",
        "最终动作：`scope_industrial_drive / scope_aerospace / cross_domain / clarify_first`。",
        "",
        "## 五、全部 79 条查询充分性确认",
        "",
        "以下不是只列异常项，而是完整保留所有查询，供专家确认机器充分性判断是否合理。",
        "",
        "| Query | 查询 | 基准领域 | Router 模式 | 机器充分性 | 分数 | 是否澄清 | 人工充分性 | 最终动作 | 备注 |",
        "|---|---|---|---|---|---:|---|---|---|---|",
    ])
    for row in report["all_query_review"]:
        suff = row["sufficiency_machine_decision"]
        router = row["router_machine_decision"]
        lines.append(
            f"| {_cell(row['query_id'])} | {_cell(row['query'])} | {_cell(row['benchmark_expected_domain'])} | {_cell(router.get('mode'))} | {_cell(suff.get('level'))} | {_cell(suff.get('sufficiency_score'))} | {_cell(suff.get('requires_clarification'))} |  |  |  |"
        )
    lines.extend([
        "",
        "## 六、系统澄清行为确认",
        "",
        "请专家确认下列问题是否足够、是否需要增删：",
        "",
        "1. 请补充设备型号、系统名称或厂商。",
        "2. 如果有，请提供完整故障码、报警码或参数号。",
        "3. 请说明涉及的组件、模块或部件。",
        "4. 请补充故障现象、触发条件或报警值。",
        "5. 如果信息仍不足，是否允许返回多个候选故障，而不是强行给出唯一答案？",
        "",
        "专家结论：____________________________________________________________",
        "",
        "## 七、最终签字结论",
        "",
        "- [ ] A 类领域词已完成审核；",
        "- [ ] 全部 22 条 cross-domain 查询已完成审核；",
        "- [ ] 全部查询充分性已完成审核；",
        "- [ ] 可以形成 `query_sufficiency_gold_v1`；",
        "- [ ] 允许生成 Router v2；",
        "- [ ] 暂不允许 Router v2，继续使用 Router v1。",
        "",
        "审核人：____________________    日期：____________________",
        "",
        "## 版本边界",
        "",
        "本材料包不把 AI 辅助审核、公开样本或机器诊断直接升级为真人专家金标。专家填写后应生成新的版本化审核结果，不覆盖本材料包。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, required=True)
    parser.add_argument("--sufficiency", type=Path, required=True)
    parser.add_argument("--router-report", type=Path, required=True)
    parser.add_argument("--siemens", type=Path, required=True)
    parser.add_argument("--aerospace", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    report = build(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render(report), encoding="utf-8")
    print(render(report))


if __name__ == "__main__":
    main()
