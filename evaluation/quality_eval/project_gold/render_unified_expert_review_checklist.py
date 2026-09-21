"""Render one complete expert checklist from the project and public runs."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from extraction_contract import (  # noqa: E402
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from review_preparation_service import ReviewPreparationService  # noqa: E402


PROJECT_DATASET = ROOT / "evaluation/quality_eval/datasets/fta_project_handbook_evidence.json"
PROJECT_REPORT = ROOT / "evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline_current_registry.json"
PUBLIC_DATASET = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v3_official.json"
PUBLIC_PREDICTIONS = ROOT / "evaluation/quality_eval/runs/siemens_s210_public_predictions_v11.json"
OUTPUT_HTML = ROOT / "evaluation/quality_eval/runs/fta_unified_expert_review_checklist_57_2026-09-20.html"
OUTPUT_MD = ROOT / "evaluation/quality_eval/runs/fta_unified_expert_review_checklist_57_2026-09-20.md"

FIELD_LABELS = {
    "fault_code": "故障码",
    "component": "主组件",
    "related_components": "关联组件",
    "description": "故障现象",
    "causes": "候选原因",
    "parameters": "参数",
}
EVIDENCE_LABELS = {
    "fault_code": "故障码",
    "primary_component": "主组件",
    "component": "组件（兼容字段）",
    "related_component": "关联组件",
    "component_declaration": "组件声明",
    "driver_object_declaration": "驱动对象声明",
    "description": "故障现象",
    "cause": "候选原因",
    "parameter": "参数",
}
RULES = (
    ("规则1", "故障码、故障现象是否对应同一条故障记录"),
    ("规则2", "组件是否属于主组件；原文写“组件为无”时，不要强行指定主组件"),
    ("规则3", "候选原因必须是故障原因/故障场景，而非更换、检查、升级等处理动作"),
    ("规则4", "参数是否确实属于该故障记录"),
    ("规则5", "每个字段是否都能在原文中找到支持证据"),
)
DECISIONS = (
    "审核通过：记录语义和证据均可接受",
    "证据不足：原文不足以支持该字段或该记录",
    "语义需修改：有证据，但字段归属、原因或组件理解不正确",
    "无法判断：需要其他手册、领域规则或专家意见",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _record_dict(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "fault_code": record.get("fault_code") or None,
        "component": record.get("component") or None,
        "related_components": _list(record.get("related_components")),
        "description": str(record.get("description") or ""),
        "causes": _list(record.get("causes")),
        "parameters": _list(record.get("parameters")),
        "confidence": record.get("confidence"),
    }


def _review_for(sample_id: str, record_data: dict[str, Any], evidence_data: list[dict[str, Any]]):
    normalized = _record_dict(record_data)
    record = FaultRecord(
        description=normalized["description"] or "未提供故障现象",
        fault_code=normalized["fault_code"],
        component=normalized["component"],
        related_components=tuple(normalized["related_components"]),
        causes=tuple(normalized["causes"]),
        parameters=tuple(normalized["parameters"]),
        confidence=normalized["confidence"],
    )
    object.__setattr__(record, "record_id", sample_id)

    spans = []
    for item in evidence_data:
        spans.append(
            EvidenceSpan(
                record_id=sample_id,
                field=EvidenceField(item["field"]),
                source_id=str(item.get("source_id") or "input_text"),
                quote=str(item["quote"]),
                start=int(item["start"]),
                end=int(item["end"]),
                value_index=item.get("value_index"),
            )
        )
    result = ExtractionResult(
        status=ExtractionStatus.SUCCESS,
        records=(record,),
        evidence_spans=tuple(spans),
    )
    review = ReviewPreparationService().prepare(result)[0]
    return normalized, review


def _project_items() -> list[dict[str, Any]]:
    dataset = _load(PROJECT_DATASET)
    report = _load(PROJECT_REPORT)
    samples = {str(item["sample_id"]): item for item in dataset["samples"]}
    items = []
    for detail in report["details"]:
        sample_id = str(detail["sample_id"])
        source = samples[sample_id]
        record_data = detail["records"][0]
        evidence = detail.get("evidence", {}).get("spans", [])
        normalized, review = _review_for(sample_id, record_data, evidence)
        items.append(
            {
                "sample_id": sample_id,
                "dataset": "项目手册 27 条",
                "source_type": "项目手册样本",
                "source_file": "backend-python/examples/manual_handbook_sample.txt",
                "input_text": source.get("input_text", ""),
                "record": normalized,
                "evidence": evidence,
                "automatic_status": review.status.value,
                "automatic_reason": review.reason,
            }
        )
    return items


def _public_items() -> list[dict[str, Any]]:
    dataset = _load(PUBLIC_DATASET)
    predictions = _load(PUBLIC_PREDICTIONS)
    samples = {str(item["sample_id"]): item for item in dataset["samples"]}
    items = []
    for row in predictions["predictions"]:
        sample_id = str(row["sample_id"])
        prediction = row["prediction"]["extracted_faults"]
        source = samples[sample_id]
        record_data = prediction["records"][0]
        evidence = prediction.get("evidence_spans", [])
        normalized, review = _review_for(sample_id, record_data, evidence)
        provenance = source.get("provenance", {})
        items.append(
            {
                "sample_id": sample_id,
                "dataset": "公开 SINAMICS S210 30 条",
                "source_type": "公开手册专家审核样本",
                "source_file": provenance.get("source_pdf") or "S210 public manual",
                "input_text": source.get("input_text", ""),
                "record": normalized,
                "evidence": evidence,
                "automatic_status": review.status.value,
                "automatic_reason": review.reason,
            }
        )
    return items


def build_items() -> list[dict[str, Any]]:
    items = _project_items() + _public_items()
    for index, item in enumerate(items, start=1):
        item["sequence"] = index
    return items


def _value_text(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value) if value else "（空）"
    if value is None or value == "":
        return "（空）"
    return str(value)


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_markdown(items: list[dict[str, Any]]) -> str:
    lines = [
        "# FTA 故障记录专家审核清单（统一完整版·57条）",
        "",
        "审核版本：统一真实数据审核版（2026-09-20）",
        "审核对象：项目手册 27 条 + 公开 SINAMICS S210 30 条",
        "审核说明：本清单不提供专家预审结论；系统分流提示仅用于定位，不等于审核结论，不是金标数据。",
        "",
        "## 一、审核规则",
        "",
    ]
    lines.extend(f"- **{name}**：{content}" for name, content in RULES)
    lines.extend(["", "## 二、审核结论（专家填写）", ""])
    lines.extend(f"- {decision}" for decision in DECISIONS)
    lines.extend(
        [
            "",
            "## 三、统一审核说明",
            "",
            "57 条记录都因当前模型未提供置信度而进入系统 `pending`；这不是语义错误结论。",
            "其中 6 条还存在系统检测到的候选原因证据缺口，专家应优先核对，但仍需按同一模板审核全部字段。",
            "",
            "## 四、逐条审核清单",
            "",
        ]
    )
    for item in items:
        record = item["record"]
        lines.extend(
            [
                f"## {item['sequence']:02d}. {item['sample_id']}",
                "",
                f"数据来源：{item['dataset']}；原文来源：{item['source_file']}",
                f"系统分流提示（不是专家结论）：`{item['automatic_status']}`；`{item['automatic_reason']}`",
                "",
                "### A. 模型抽取结果",
                "",
                "| 字段 | 抽取值 |",
                "|---|---|",
            ]
        )
        for field, label in FIELD_LABELS.items():
            lines.append(f"| {label} | {_md_escape(_value_text(record.get(field)))} |")
        lines.extend(
            [
                "",
                "### B. 抽取证据",
                "",
                "| 序号 | 字段 | 原文引用 | 字符位置 | 来源 |",
                "|---:|---|---|---:|---|",
            ]
        )
        if item["evidence"]:
            for evidence_index, evidence in enumerate(item["evidence"], start=1):
                field = EVIDENCE_LABELS.get(evidence["field"], evidence["field"])
                source = evidence.get("source_id", "input_text")
                lines.append(
                    f"| {evidence_index} | {field} | {_md_escape(evidence.get('quote', ''))} | "
                    f"{evidence.get('start', '')}-{evidence.get('end', '')} | {source} |"
                )
        else:
            lines.append("| - | 未找到证据 | （空） | - | - |")
        lines.extend(
            [
                "",
                "### C. 原文",
                "",
                "```text",
                item["input_text"],
                "```",
                "",
                "### D. 专家审核（请填写）",
                "",
                "- 审核结论：□ 审核通过　□ 证据不足　□ 语义需修改　□ 无法判断",
                "- 需修改字段：",
                "- 修改后内容：",
                "- 专家意见：",
                "- 专家姓名：",
                "- 审核日期：",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _html_value(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return "<span class='empty'>（空）</span>"
        return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in value) + "</ul>"
    if value is None or value == "":
        return "<span class='empty'>（空）</span>"
    return html.escape(str(value)).replace("\n", "<br>")


def _render_html(items: list[dict[str, Any]]) -> str:
    cards = []
    for item in items:
        record = item["record"]
        field_rows = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{_html_value(record.get(field))}</td></tr>"
            for field, label in FIELD_LABELS.items()
        )
        evidence_rows = "".join(
            "<tr>"
            f"<td>{index}</td><td>{html.escape(EVIDENCE_LABELS.get(evidence['field'], evidence['field']))}</td>"
            f"<td>{html.escape(str(evidence.get('quote', '')))}</td>"
            f"<td>{evidence.get('start', '')}–{evidence.get('end', '')}</td>"
            f"<td>{html.escape(str(evidence.get('source_id', 'input_text')))}</td>"
            "</tr>"
            for index, evidence in enumerate(item["evidence"], start=1)
        ) or "<tr><td colspan='5' class='empty'>未找到证据</td></tr>"
        cards.append(
            f"""
            <article class="record-card" data-search="{html.escape((item['sample_id'] + ' ' + item['input_text']).casefold())}">
              <div class="record-header">
                <span class="record-number">{item['sequence']:02d}</span>
                <div><h2>{html.escape(item['sample_id'])}</h2>
                <p>{html.escape(item['dataset'])} · {html.escape(item['source_file'])}</p></div>
              </div>
              <div class="system-note"><strong>系统分流提示（不是专家结论）：</strong>
                <code>{html.escape(item['automatic_status'])}</code> · {html.escape(item['automatic_reason'])}
              </div>
              <h3>A. 模型抽取结果</h3>
              <table><tbody>{field_rows}</tbody></table>
              <h3>B. 抽取证据</h3>
              <table><thead><tr><th>#</th><th>字段</th><th>原文引用</th><th>字符位置</th><th>来源</th></tr></thead>
              <tbody>{evidence_rows}</tbody></table>
              <h3>C. 原文</h3>
              <pre>{html.escape(item['input_text'])}</pre>
              <h3>D. 专家审核（请填写）</h3>
              <div class="review-form">
                <p>审核结论：□ 审核通过　□ 证据不足　□ 语义需修改　□ 无法判断</p>
                <p>需修改字段：____________________________________________________________</p>
                <p>修改后内容：____________________________________________________________</p>
                <p>专家意见：______________________________________________________________</p>
                <p>专家姓名：____________________　审核日期：____________________</p>
              </div>
            </article>
            """
        )
    rules = "".join(f"<li><strong>{html.escape(name)}</strong>：{html.escape(content)}</li>" for name, content in RULES)
    decisions = "".join(f"<li>{html.escape(decision)}</li>" for decision in DECISIONS)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FTA 故障记录专家审核清单（57条统一完整版）</title>
<style>
:root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#d9dee8; --blue:#2457a6; --soft:#f5f7fb; --warn:#fff7e6; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:#eef1f6; color:var(--ink); font:15px/1.65 "Segoe UI","Microsoft YaHei",sans-serif; }}
.page {{ max-width:1200px; margin:0 auto; padding:28px 22px 60px; }}
.hero,.record-card {{ background:white; border:1px solid var(--line); border-radius:14px; box-shadow:0 5px 18px #1d35570d; }}
.hero {{ padding:28px 30px; margin-bottom:18px; }} h1 {{ margin:0 0 8px; font-size:28px; }} h2 {{ margin:0; font-size:20px; }} h3 {{ margin:24px 0 9px; color:var(--blue); font-size:17px; }}
.muted,p {{ color:var(--muted); }} .hero p {{ margin:6px 0; }}
.rule-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:8px 20px; padding-left:20px; }}
.decision-list {{ columns:2; padding-left:20px; }}
.toolbar {{ position:sticky; top:10px; z-index:2; display:flex; gap:12px; align-items:center; background:#ffffffed; border:1px solid var(--line); border-radius:12px; padding:10px 12px; margin:16px 0; backdrop-filter:blur(8px); }}
.toolbar input {{ flex:1; min-width:180px; border:1px solid #bcc5d5; border-radius:8px; padding:9px 11px; font:inherit; }} .count {{ color:var(--muted); white-space:nowrap; }}
.record-card {{ padding:22px 24px; margin:18px 0; }} .record-header {{ display:flex; gap:14px; align-items:center; }} .record-number {{ display:grid; place-items:center; width:42px; height:42px; border-radius:12px; background:#e8f0ff; color:var(--blue); font-weight:700; }}
.record-header p {{ margin:2px 0 0; font-size:13px; }} .system-note {{ margin-top:14px; padding:10px 12px; border-left:4px solid #e0a11a; background:var(--warn); color:#6b4c00; }} code {{ font-family:Consolas,monospace; }}
table {{ border-collapse:collapse; width:100%; }} th,td {{ border:1px solid var(--line); padding:8px 10px; vertical-align:top; text-align:left; }} th {{ background:var(--soft); width:180px; }} td ul {{ margin:0; padding-left:20px; }} .empty {{ color:#8a94a6; }}
pre {{ white-space:pre-wrap; word-break:break-word; background:#f8fafc; border:1px solid var(--line); border-radius:8px; padding:14px; max-height:420px; overflow:auto; }} .review-form {{ background:#fbfcfe; border:1px dashed #aab5c7; border-radius:8px; padding:5px 14px; }}
@media (max-width:700px) {{ .page {{ padding:14px 9px 40px; }} .hero,.record-card {{ padding:16px; }} .decision-list {{ columns:1; }} th {{ width:115px; }} }}
@media print {{ body {{ background:white; }} .toolbar {{ display:none; }} .hero,.record-card {{ box-shadow:none; break-inside:avoid; }} .record-card {{ break-before:page; }} }}
</style></head><body><main class="page">
<section class="hero"><h1>FTA 故障记录专家审核清单（统一完整版·57条）</h1>
<p>审核版本：统一真实数据审核版（2026-09-20）</p>
<p>范围：项目手册 27 条 + 公开 SINAMICS S210 30 条。每条记录包含模型抽取结果、逐字段证据、完整原文和专家填写区。</p>
<p><strong>重要：</strong>系统分流提示仅用于定位，不是专家预审结论，也不是金标数据。</p>
<h3>审核规则</h3><ol class="rule-grid">{rules}</ol>
<h3>审核结论</h3><ul class="decision-list">{decisions}</ul></section>
<div class="toolbar"><input id="search" placeholder="搜索故障码、记录编号或原文…"><span class="count" id="count">显示 {len(items)} / {len(items)}</span></div>
<section id="records">{''.join(cards)}</section>
</main><script>
const input=document.getElementById('search'), cards=[...document.querySelectorAll('.record-card')], count=document.getElementById('count');
input.addEventListener('input',()=>{{const q=input.value.trim().toLowerCase();let n=0;cards.forEach(c=>{{const show=!q||c.dataset.search.includes(q);c.style.display=show?'':'none';if(show)n++;}});count.textContent=`显示 ${{n}} / ${{cards.length}}`;}});
</script></body></html>"""


def main() -> None:
    items = build_items()
    if len(items) != 57:
        raise RuntimeError(f"expected 57 checklist items, got {len(items)}")
    OUTPUT_MD.write_text(_render_markdown(items), encoding="utf-8")
    OUTPUT_HTML.write_text(_render_html(items), encoding="utf-8")
    print(json.dumps({"items": len(items), "markdown": str(OUTPUT_MD), "html": str(OUTPUT_HTML)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
