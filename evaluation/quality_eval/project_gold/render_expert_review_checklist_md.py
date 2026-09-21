#!/usr/bin/env python3
"""Render a blank, expert-facing Markdown review checklist."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _display(value: Any) -> str:
    if value is None or value == "":
        return "（空）"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "（空）"
    return str(value).replace("\n", " ").strip() or "（空）"


def _escape_cell(value: Any) -> str:
    return _display(value).replace("|", "\\|")


def _field_label(field: Any) -> str:
    return {
        "fault_code": "故障码",
        "primary_component": "主组件",
        "related_component": "关联组件",
        "component_declaration": "主组件声明",
        "driver_object_declaration": "驱动对象声明",
        "component": "组件（旧字段）",
        "description": "故障现象",
        "cause": "候选原因",
        "parameter": "参数",
    }.get(str(field), str(field))


def _source_section(input_text: str, start: Any) -> str:
    if not isinstance(start, int):
        return "未标注"
    definition = input_text.rfind("故障定义", 0, start + 1)
    handling = input_text.rfind("故障处理", 0, start + 1)
    if handling > definition:
        return "故障处理"
    if definition >= 0:
        return "故障定义"
    return "未标注"


def _display_quote(value: Any) -> str:
    """Fold source line breaks for the table; the full source remains below."""
    if value is None:
        return "（空）"
    return re.sub(r"\s+", "", str(value)).replace("|", "\\|") or "（空）"


def _review_overview(sample_count: int) -> list[str]:
    """Return the expert-facing scope and index before the record-by-record pages."""
    return [
        "## 审核规则（5条核心规则）",
        "",
        "| 规则 | 内容 |",
        "|---|---|",
        "| 规则1 | 故障码、故障现象是否对应同一条故障记录 |",
        "| 规则2 | 组件是否属于主组件；原文写“组件为无”时，不要强行指定主组件 |",
        "| 规则3 | 候选原因必须是故障原因/故障场景，而非更换、检查、升级等处理动作 |",
        "| 规则4 | 参数是否确实属于该故障记录 |",
        "| 规则5 | 每个字段是否都能在原文中找到支持证据 |",
        "",
        "## 审核结论（4种）",
        "",
        "- **审核通过**：记录语义和证据均可接受。",
        "- **证据不足**：原文不足以支持该字段或该记录。",
        "- **语义需修改**：有证据，但字段归属、原因或组件理解不正确。",
        "- **无法判断**：需要其他手册、领域规则或专家意见。",
        "",
        f"## {sample_count}条故障记录分类概览",
        "",
        "### 按组件类型分组",
        "",
        "| 主组件类型 | 记录编号 | 数量 |",
        "|---|---|---:|",
        "| **控制单元（CU）** | 01、03、04、05、06、16、17、18、19、27 | 10条 |",
        "| **组件为无（关联其他组件）** | 02、07、10、11、12、13、14、15、20、21、22、23、25、26 | 14条 |",
        "| **DRIVE-CLiQ组件（特殊）** | 24 | 1条 |",
        "| **未声明组件字段** | 08、09 | 2条 |",
        "",
        "### 按故障类别分组",
        "",
        "| 故障类别 | 涉及记录 | 典型特征 |",
        "|---|---|---|",
        "| **安全监控通道故障（PROFIdrive编号10）** | 10、11、12、13、14、15、19、20 | 涉及 SI（Safety Integrated）功能，如 STOP 触发、STO 状态、制动控制、断流阀控制等 |",
        "| **硬件/软件故障（编号1）** | 01、03、04、05、18、20、26 | 内部软件错误、超时、RAM 写入失败等 |",
        "| **参数设置/配置故障（编号18）** | 21、22 | 单位转换、参考参数相关 |",
        "| **一般驱动故障（编号19）** | 06、08、09、16、17、24、25 | 组件更换应答、风扇寿命、组件列表更改等 |",
        "| **电子组件过热（编号6）** | 27 | 控制单元过热 |",
        "| **固件相关（未明确编号）** | 07、23 | 固件修改、固件下载失败 |",
        "",
        "## 每条记录的标准结构",
        "",
        "| 部分 | 内容 |",
        "|---|---|",
        "| **A. 模型抽取结果** | 故障码、故障现象、主组件、关联组件、候选原因、参数 |",
        "| **B. 抽取证据** | 每个字段对应的原文引用位置，含段落来源和字符位置 |",
        "| **C. 原文** | 故障定义 + 故障处理的完整原文 |",
        "| **D. 专家审核** | 审核结论、审核意见、需修改字段，均为空白待填写 |",
        "",
        "## 关键参数分布（仅供定位，不代表参数语义已确认）",
        "",
        "- **r0949**：出现频率最高的参数，作为关联故障值出现在多数记录中，用于传递故障值、参数号或组件号等诊断信息。",
        "- **r2124**：出现在报警类故障中，传递故障值说明。",
        "- **p0977**：多次出现，用于保存参数（p0977=1）。",
        "- **p9601/p9602/p9650**：安全监控通道相关参数。",
        "- **p7828/p7829**：DRIVE-CLiQ 组件固件升级相关参数。",
        "",
        "## 上一轮问题领域（修复后重点复核）",
        "",
        "以下问题来自 v1 专家反馈。本版已在后端增加对应约束，但不预设专家结论，请继续核对：",
        "",
        "1. **关联组件填写**：主组件不能重复出现在关联组件；关联组件必须有原文声明。",
        "2. **组件为无的证据**：应存在指向“组件为无”的组件声明证据。",
        "3. **候选原因和参数值说明**：确认“0表示……/故障值为……”是否已提炼为故障场景，且不是单纯参数解释。",
        "4. **来源段落**：候选原因或参数若来自故障处理段，应核对证据表中的来源标注。",
        "5. **Record 24 字段归属**：确认“驱动对象为无（关联 DRIVE-CLiQ 组件及编码器模块）”没有被误判为组件关联。",
        "",
        "---",
        "",
    ]


def render(bundle: dict[str, Any]) -> str:
    samples = bundle.get("samples") or []
    lines = [
        "# FTA 故障记录专家审核清单（文本版）",
        "",
        "> 用途：请专家依据每条记录的原文和证据，审核模型抽取是否合理。",
        "> 本清单不提供预审结论，不是专家金标；请专家独立填写。",
        "",
        *_review_overview(len(samples)),
        "## 审核结论填写方式",
        "",
        "每条记录只能选择一个结论，并补充修改意见：",
        "",
        "- [ ] 审核通过：记录语义和证据均可接受。",
        "- [ ] 证据不足：原文不足以支持该字段或该记录。",
        "- [ ] 语义需修改：有证据，但字段归属、原因或组件理解不正确。",
        "- [ ] 无法判断：需要其他手册、领域规则或专家意见。",
        "",
        f"共 {len(samples)} 条故障记录。",
        "",
    ]

    for index, sample in enumerate(samples, start=1):
        prediction = sample.get("prediction") or {}
        records = prediction.get("records") or []
        record = records[0] if records else {}
        spans = prediction.get("evidence_spans") or []
        sample_id = sample.get("sample_id") or f"sample-{index}"
        code = sample.get("fault_code") or record.get("fault_code") or "（无故障码）"

        lines.extend(
            [
                f"## {index:02d}. {sample_id}｜故障码：{code}",
                "",
                "### A. 模型抽取结果",
                "",
                "| 字段 | 抽取结果 |",
                "|---|---|",
                f"| 故障码 | {_escape_cell(record.get('fault_code'))} |",
                f"| 故障现象 | {_escape_cell(record.get('description'))} |",
                f"| 主组件 | {_escape_cell(record.get('component'))} |",
                f"| 关联组件 | {_escape_cell(record.get('related_components'))} |",
                f"| 候选原因 | {_escape_cell(record.get('causes'))} |",
                f"| 参数 | {_escape_cell(record.get('parameters'))} |",
                "",
                "### B. 抽取证据",
                "",
            ]
        )
        if spans:
            lines.extend([
                "| 字段 | 来源段落 | 原文引用（折叠换行） | 字符位置 |",
                "|---|---|---|---|",
            ])
            for span in spans:
                lines.append(
                    f"| {_escape_cell(_field_label(span.get('field')))} | "
                    f"{_escape_cell(_source_section(str(sample.get('input_text') or ''), span.get('start')))} | "
                    f"{_display_quote(span.get('quote'))} | "
                    f"{_escape_cell(span.get('start'))}–{_escape_cell(span.get('end'))} |"
                )
        else:
            lines.append("（没有可回指原文的证据跨度。）")
        lines.extend(
            [
                "",
                "### C. 原文",
                "",
                "```text",
                str(sample.get("input_text") or "").rstrip(),
                "```",
                "",
                "### D. 专家审核",
                "",
                "- [ ] 审核通过",
                "- [ ] 证据不足",
                "- [ ] 语义需修改",
                "- [ ] 无法判断",
                "",
                "审核意见：",
                "",
                "```text",
                "",
                "```",
                "",
                "需要修改的字段：",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(bundle), encoding="utf-8")
    print(f"[ok] wrote {output} samples={len(bundle.get('samples') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
