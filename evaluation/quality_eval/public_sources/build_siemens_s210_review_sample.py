#!/usr/bin/env python3
"""Select a deterministic stratified public-manual sample and render a blank review checklist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_QUOTAS = {"F": 20, "A": 8, "N": 2}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number} is not an object")
        rows.append(value)
    return rows


def _evenly_spaced(items: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 0:
        return []
    if len(items) < count:
        raise ValueError(f"need {count} records, only {len(items)} available")
    if count == 1:
        return [items[len(items) // 2]]
    indices = [round(index * (len(items) - 1) / (count - 1)) for index in range(count)]
    return [items[index] for index in indices]


def select_sample(
    records: list[dict[str, Any]],
    quotas: dict[str, int] | None = None,
    excluded_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    quotas = quotas or DEFAULT_QUOTAS
    excluded_ids = excluded_ids or set()
    grouped = {
        kind: sorted(
            (
                record
                for record in records
                if record["sample_id"] not in excluded_ids
                and str(record["weak_record"]["fault_code"]).startswith(kind)
            ),
            key=lambda item: item["sample_id"],
        )
        for kind in quotas
    }
    selected = []
    for kind, count in quotas.items():
        selected.extend(_evenly_spaced(grouped[kind], count))
    return sorted(selected, key=lambda item: item["sample_id"])


def build_review_dataset(
    records: list[dict[str, Any]],
    *,
    quotas: dict[str, int] | None = None,
    excluded_ids: set[str] | None = None,
    batch_name: str = "v1",
) -> dict[str, Any]:
    selected = select_sample(records, quotas, excluded_ids)
    samples = []
    for record in selected:
        sample = dict(record)
        sample["split"] = "expert_review_sample"
        sample["annotation"] = {
            "human_expert_reviewed": False,
            "decision": None,
            "reviewer_role": None,
            "reviewer_name": None,
            "review_date": None,
            "corrected_fields": [],
            "review_note": None,
            "logic_status": "unknown",
        }
        samples.append(sample)
    return {
        "dataset_info": {
            "name": "siemens_s210_public_fault_expert_review_sample",
            "version": batch_name,
            "label_status": "unlabeled_expert_review_sample",
            "human_expert_reviewed": False,
            "selection": {
                "method": "deterministic_even_spacing_within_message_type",
                "quotas": quotas or DEFAULT_QUOTAS,
                "total": len(samples),
                "excluded_count": len(excluded_ids or set()),
            },
            "review_rules": [
                "规则1：故障码、故障现象是否对应同一条故障记录",
                "规则2：组件是否属于主组件；组件为无时不强行指定主组件",
                "规则3：候选原因必须是故障原因或故障场景，而非处理动作",
                "规则4：参数是否确实属于该故障记录",
                "规则5：每个字段是否有原文支持证据",
            ],
            "logic_policy": "unknown_until_explicitly_expert_annotated",
        },
        "samples": samples,
    }


def _display(value: Any) -> str:
    if value is None or value == "":
        return "（空）"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "（空）"
    return str(value).replace("\n", " ").strip() or "（空）"


def render_markdown(dataset: dict[str, Any]) -> str:
    quotas = dataset["dataset_info"]["selection"]["quotas"]
    total = dataset["dataset_info"]["selection"]["total"]
    lines = [
        f"# SINAMICS S210 公开故障记录专家审核清单（{total}条扩展批次）",
        "",
        "> 本清单来自公开手册的新样本抽样，不提供预审结论，不是金标。请专家独立填写。",
        f"> 样本构成为 F 类 {quotas.get('F', 0)} 条、A 类 {quotas.get('A', 0)} 条、N 类 {quotas.get('N', 0)} 条；AND/OR 逻辑暂不审核时填写 unknown。",
        "> “故障现象候选、组件候选、参数候选”只是程序弱解析结果，仅用于定位，不是正确答案，也不是最终模型输出。",
        "> 专家应以“原文”为唯一依据，独立填写故障现象、主/关联组件、候选原因、参数和证据。",
        "",
        "## 审核结论",
        "",
        "- 审核通过：字段语义和证据均可接受。",
        "- 证据不足：原文不足以支持字段或记录。",
        "- 语义需修改：有证据，但字段归属或语义不正确。",
        "- 无法判断：需要其他手册或领域知识。",
        "",
        "## 每条记录填写内容",
        "",
        "审核结论、修改字段、修改后内容、原文证据、审核意见、审核者角色和日期。",
        "",
    ]
    for index, sample in enumerate(dataset["samples"], start=1):
        weak = sample["weak_record"]
        provenance = sample["provenance"]
        lines.extend(
            [
                f"## {index:02d}. {sample['sample_id']}",
                "",
                f"- 故障码：{_display(weak.get('fault_code'))}",
                f"- 故障现象候选：{_display(weak.get('description'))}",
                f"- 组件候选：{_display(weak.get('component'))}",
                f"- 参数候选：{_display(weak.get('parameters'))}",
                f"- 来源页码：{provenance.get('pdf_page_start')}–{provenance.get('pdf_page_end')}",
                "",
                "### 原文",
                "",
                "```text",
                sample.get("input_text", "").rstrip(),
                "```",
                "",
                "### 专家审核",
                "",
                "#### 专家确认后的最终字段（必须填写）",
                "",
                "| 字段 | 专家最终值 |",
                "|---|---|",
                "| 故障码 |  |",
                "| 故障现象 |  |",
                "| 主组件 |  |",
                "| 关联组件 |  |",
                "| 候选原因 |  |",
                "| 参数 |  |",
                "| gate_type | unknown（未明确标注时保持 unknown） |",
                "",
                "#### 专家确认的原文证据",
                "",
                "| 字段 | 原文引用 | 页码/位置 |",
                "|---|---|---|",
                "| 故障码 |  |  |",
                "| 故障现象 |  |  |",
                "| 主组件 |  |  |",
                "| 关联组件 |  |  |",
                "| 候选原因 |  |  |",
                "| 参数 |  |  |",
                "",
                "- [ ] 审核通过",
                "- [ ] 证据不足",
                "- [ ] 语义需修改",
                "- [ ] 无法判断",
                "",
                "修改字段：",
                "",
                "```text",
                "",
                "```",
                "",
                "审核意见：",
                "",
                "```text",
                "",
                "```",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument(
        "--exclude-json",
        type=Path,
        action="append",
        default=[],
        help="Existing review/gold JSON files whose sample_id values must be excluded",
    )
    parser.add_argument("--batch-name", default="v1")
    parser.add_argument("--quota-f", type=int, default=DEFAULT_QUOTAS["F"])
    parser.add_argument("--quota-a", type=int, default=DEFAULT_QUOTAS["A"])
    parser.add_argument("--quota-n", type=int, default=DEFAULT_QUOTAS["N"])
    args = parser.parse_args()
    excluded_ids: set[str] = set()
    for path in args.exclude_json:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for sample in payload.get("samples", []):
            sample_id = sample.get("sample_id")
            if sample_id:
                excluded_ids.add(str(sample_id))
    dataset = build_review_dataset(
        _read_jsonl(args.input_jsonl),
        quotas={"F": args.quota_f, "A": args.quota_a, "N": args.quota_n},
        excluded_ids=excluded_ids,
        batch_name=args.batch_name,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(dataset), encoding="utf-8")
    print(json.dumps(dataset["dataset_info"], ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output_json} and {args.output_md}")


if __name__ == "__main__":
    main()
