#!/usr/bin/env python3
"""Render a compact human-review checklist from the project evidence dataset."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_project_handbook_evidence.json"
DEFAULT_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_review_checklist.md"
DEFAULT_HTML_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_review_checklist.html"


def _cell(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        value = "、".join(str(item) for item in value) or "—"
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def render(payload: dict) -> str:
    samples = payload.get("samples", [])
    lines = [
        "# 项目手册故障记录人工审核清单",
        "",
        "这是一份原文级审核清单，不等同于专家金标。请先确认字段是否能在输入原文中找到；",
        "不确定的工程原因、组件归属和 AND/OR 逻辑保持 `unknown`，不要强行选择。",
        "",
        f"样本数：{len(samples)}；来源：`backend-python/examples/manual_handbook_sample.txt`。",
        "",
        "| 序号 | 样本 | 故障码 | 故障现象 | 组件 | 参数 | 候选场景 | 原文行 | 审核状态 |",
        "| ---: | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for index, sample in enumerate(samples, start=1):
        record = (sample.get("gold_records") or [{}])[0]
        source = sample.get("source") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _cell(sample.get("sample_id")),
                    _cell(record.get("fault_code")),
                    _cell(record.get("description")),
                    _cell(record.get("component")),
                    _cell(record.get("parameters")),
                    _cell(record.get("causes")),
                    f"{source.get('source_line_start', '—')}-{source.get('source_line_end', '—')}",
                    "待人工原文确认",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 审核结论建议",
            "",
            "- `source_confirmed`：字段和证据在原文中明确存在。",
            "- `source_rejected`：字段与原文不一致，记录拒绝原因。",
            "- `unknown`：原文不足以判断工程语义，保留未知。",
            "- `expert_verified`：只有具备领域知识的审核者确认后才能使用。",
        ]
    )
    return "\n".join(lines) + "\n"


def _html_cell(value: object, *, empty: str = "未标注") -> str:
    if value is None:
        return empty
    if isinstance(value, list):
        value = "、".join(str(item) for item in value) or empty
    return escape(str(value).replace("\n", " ").strip() or empty)


def _html_evidence(sample: dict) -> str:
    spans = sample.get("evidence_spans") or []
    span_rows = []
    for span in spans:
        span_rows.append(
            "<tr>"
            f"<td>{_html_cell(span.get('target_path'))}</td>"
            f"<td>{_html_cell(span.get('evidence_text'))}</td>"
            f"<td>{_html_cell(span.get('start_char'))}–{_html_cell(span.get('end_char'))}</td>"
            "</tr>"
        )
    evidence_table = (
        "<table class=\"evidence-table\"><thead><tr>"
        "<th>字段</th><th>原文证据</th><th>字符位置</th>"
        "</tr></thead><tbody>"
        + "".join(span_rows)
        + "</tbody></table>"
        if span_rows
        else "<p class=\"muted\">没有生成字段证据。</p>"
    )
    source = sample.get("source") or {}
    return (
        "<details class=\"evidence-details\">"
        "<summary>查看原文与证据</summary>"
        f"<div class=\"source-meta\">来源行：{_html_cell(source.get('source_line_start'))}–"
        f"{_html_cell(source.get('source_line_end'))}　字符：{_html_cell(source.get('source_char_start'))}–"
        f"{_html_cell(source.get('source_char_end'))}</div>"
        f"<pre>{escape(str(sample.get('input_text') or ''))}</pre>"
        f"{evidence_table}"
        "</details>"
    )


def render_html(payload: dict) -> str:
    samples = payload.get("samples", [])
    cause_count = sum(bool((sample.get("gold_records") or [{}])[0].get("causes")) for sample in samples)
    component_count = sum(bool((sample.get("gold_records") or [{}])[0].get("component")) for sample in samples)
    rows = []
    for index, sample in enumerate(samples, start=1):
        record = (sample.get("gold_records") or [{}])[0]
        sample_id = str(sample.get("sample_id") or f"sample-{index}")
        search_text = " ".join(
            str(value or "")
            for value in (
                sample_id,
                record.get("fault_code"),
                record.get("description"),
                record.get("component"),
                record.get("causes"),
                record.get("parameters"),
            )
        ).lower()
        rows.append(
            "<article class=\"review-card\" "
            f"data-sample-id=\"{escape(sample_id, quote=True)}\" "
            f"data-search=\"{escape(search_text, quote=True)}\">"
            "<div class=\"card-top\">"
            f"<div><span class=\"index\">{index:02d}</span> "
            f"<strong>{_html_cell(sample_id)}</strong></div>"
            "<select class=\"status-select\" aria-label=\"审核状态\" "
            f"data-sample-id=\"{escape(sample_id, quote=True)}\">"
            "<option value=\"待审核\">待审核</option>"
            "<option value=\"原文确认\">原文确认</option>"
            "<option value=\"原文拒绝\">原文拒绝</option>"
            "<option value=\"未知\">未知</option>"
            "<option value=\"专家已确认\">专家已确认</option>"
            "</select></div>"
            "<div class=\"field-grid\">"
            f"<div><label>故障码</label><span class=\"value code\">{_html_cell(record.get('fault_code'))}</span></div>"
            f"<div><label>故障现象</label><span class=\"value\">{_html_cell(record.get('description'))}</span></div>"
            f"<div><label>组件</label><span class=\"value\">{_html_cell(record.get('component'))}</span></div>"
            f"<div><label>参数</label><span class=\"value\">{_html_cell(record.get('parameters'))}</span></div>"
            f"<div class=\"wide\"><label>候选原因（暂不等同于工程根因）</label>"
            f"<span class=\"value\">{_html_cell(record.get('causes'))}</span></div>"
            "</div>"
            f"<textarea class=\"review-note\" data-sample-id=\"{escape(sample_id, quote=True)}\" "
            "placeholder=\"填写审核备注（可选）\"></textarea>"
            f"{_html_evidence(sample)}"
            "</article>"
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FTA 项目手册故障记录审核清单</title>
<style>
:root {{
  --ink: #172033; --muted: #6b7280; --line: #e5e7eb; --panel: #ffffff;
  --bg: #f4f7fb; --blue: #2563eb; --blue-soft: #eff6ff; --green: #047857;
  --amber: #b45309; --red: #b91c1c; --shadow: 0 8px 24px rgba(31, 41, 55, .07);
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; color: var(--ink); background: var(--bg); font: 14px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }}
.shell {{ max-width: 1440px; margin: 0 auto; padding: 34px 28px 60px; }}
.hero {{ display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 24px; }}
h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: -.02em; }}
.subtitle {{ margin: 0; color: var(--muted); }}
.source {{ color: var(--muted); font-size: 12px; text-align: right; }}
.stats {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; margin-bottom: 18px; }}
.stat {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 15px 18px; box-shadow: var(--shadow); }}
.stat strong {{ display: block; font-size: 25px; color: var(--blue); }}
.stat span {{ color: var(--muted); font-size: 12px; }}
.toolbar {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; margin-bottom: 18px; box-shadow: var(--shadow); }}
.toolbar input, .toolbar select, .toolbar button {{ border: 1px solid #d1d5db; border-radius: 9px; padding: 9px 12px; background: #fff; color: var(--ink); font: inherit; }}
.toolbar input {{ flex: 1 1 300px; }}
.toolbar button {{ cursor: pointer; border-color: var(--blue); color: var(--blue); }}
.toolbar button.primary {{ background: var(--blue); color: #fff; }}
.hint {{ color: var(--muted); font-size: 12px; margin-left: auto; }}
.review-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 16px; margin: 0 0 14px; padding: 18px; box-shadow: var(--shadow); }}
.review-card.hidden {{ display: none; }}
.card-top {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 15px; }}
.index {{ display: inline-grid; place-items: center; width: 30px; height: 30px; border-radius: 9px; background: var(--blue-soft); color: var(--blue); font-weight: 700; margin-right: 7px; }}
.status-select {{ border: 1px solid #d1d5db; border-radius: 9px; padding: 7px 10px; font: inherit; background: #fff; }}
.status-select[data-status="原文确认"] {{ color: var(--green); border-color: #86efac; background: #f0fdf4; }}
.status-select[data-status="原文拒绝"] {{ color: var(--red); border-color: #fca5a5; background: #fef2f2; }}
.status-select[data-status="专家已确认"] {{ color: #6d28d9; border-color: #c4b5fd; background: #f5f3ff; }}
.field-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
.field-grid > div {{ min-width: 0; background: #f8fafc; border-radius: 10px; padding: 10px 12px; }}
.field-grid .wide {{ grid-column: span 2; }}
label {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 3px; }}
.value {{ display: block; word-break: break-word; }}
.code {{ color: var(--blue); font-weight: 700; }}
.review-note {{ width: 100%; min-height: 38px; resize: vertical; margin-top: 13px; border: 1px solid var(--line); border-radius: 9px; padding: 9px 11px; font: inherit; }}
.evidence-details {{ margin-top: 13px; border-top: 1px solid var(--line); padding-top: 11px; }}
.evidence-details summary {{ cursor: pointer; color: var(--blue); font-weight: 600; }}
.source-meta {{ color: var(--muted); font-size: 12px; margin: 10px 0; }}
pre {{ max-height: 280px; overflow: auto; white-space: pre-wrap; background: #111827; color: #e5e7eb; border-radius: 10px; padding: 14px; font: 12px/1.7 Consolas, monospace; }}
.evidence-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
.evidence-table th, .evidence-table td {{ text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); padding: 7px; }}
.evidence-table th {{ color: var(--muted); font-weight: 600; }}
.muted {{ color: var(--muted); }}
@media (max-width: 900px) {{ .hero {{ display: block; }} .source {{ text-align: left; margin-top: 8px; }} .field-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .field-grid .wide {{ grid-column: span 2; }} .hint {{ width: 100%; margin-left: 0; }} }}
@media (max-width: 560px) {{ .shell {{ padding: 22px 14px 40px; }} h1 {{ font-size: 24px; }} .stats {{ grid-template-columns: repeat(2, 1fr); }} .field-grid {{ grid-template-columns: 1fr; }} .field-grid .wide {{ grid-column: span 1; }} }}
</style>
</head>
<body>
<main class="shell">
  <section class="hero">
    <div><h1>FTA 项目手册故障记录审核清单</h1><p class="subtitle">先确认原文事实，再决定是否进入后续审核；候选原因不等同于工程根因。</p></div>
    <div class="source">来源：manual_handbook_sample.txt<br>生成时间：本地数据集</div>
  </section>
  <section class="stats">
    <div class="stat"><strong>{len(samples)}</strong><span>待审核样本</span></div>
    <div class="stat"><strong>{component_count}</strong><span>原文明确组件</span></div>
    <div class="stat"><strong>{cause_count}</strong><span>含候选原因</span></div>
    <div class="stat"><strong id="done-count">0</strong><span>已填写审核状态</span></div>
  </section>
  <section class="toolbar">
    <input id="search" type="search" placeholder="搜索故障码、描述、组件或参数…">
    <select id="filter"><option value="全部">全部状态</option><option>待审核</option><option>原文确认</option><option>原文拒绝</option><option>未知</option><option>专家已确认</option></select>
    <button class="primary" id="save">保存到本机</button><button id="export">导出审核结果</button><span class="hint">审核状态和备注保存在当前浏览器本地</span>
  </section>
  <section id="cards">{"".join(rows)}</section>
</main>
<script>
const storageKey = 'fta-project-handbook-review-v1';
const state = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
const cards = [...document.querySelectorAll('.review-card')];
const selects = [...document.querySelectorAll('.status-select')];
const notes = [...document.querySelectorAll('.review-note')];
function entry(id) {{ return state[id] || {{status: '待审核', note: ''}}; }}
function paint(select) {{ const item = entry(select.dataset.sampleId); select.value = item.status; select.dataset.status = item.status; }}
function updateDone() {{ document.querySelector('#done-count').textContent = selects.filter(s => entry(s.dataset.sampleId).status !== '待审核').length; }}
function applyFilter() {{
  const query = document.querySelector('#search').value.trim().toLowerCase();
  const filter = document.querySelector('#filter').value;
  cards.forEach(card => {{ const select = card.querySelector('.status-select'); const okText = !query || card.dataset.search.includes(query); const okStatus = filter === '全部' || select.value === filter; card.classList.toggle('hidden', !(okText && okStatus)); }});
}}
selects.forEach(select => {{ paint(select); select.addEventListener('change', () => {{ const item = entry(select.dataset.sampleId); item.status = select.value; state[select.dataset.sampleId] = item; select.dataset.status = select.value; localStorage.setItem(storageKey, JSON.stringify(state)); updateDone(); applyFilter(); }}); }});
notes.forEach(note => {{ const item = entry(note.dataset.sampleId); note.value = item.note || ''; note.addEventListener('input', () => {{ const current = entry(note.dataset.sampleId); current.note = note.value; state[note.dataset.sampleId] = current; localStorage.setItem(storageKey, JSON.stringify(state)); }}); }});
document.querySelector('#search').addEventListener('input', applyFilter); document.querySelector('#filter').addEventListener('change', applyFilter);
document.querySelector('#save').addEventListener('click', () => {{ localStorage.setItem(storageKey, JSON.stringify(state)); alert('审核状态已保存到当前浏览器。'); }});
document.querySelector('#export').addEventListener('click', () => {{ const blob = new Blob([JSON.stringify(state, null, 2)], {{type: 'application/json'}}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'fta-project-handbook-review-decisions.json'; a.click(); URL.revokeObjectURL(a.href); }});
updateDone(); applyFilter();
</script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--html-output", default=str(DEFAULT_HTML_OUTPUT))
    args = parser.parse_args()
    payload = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(payload), encoding="utf-8")
    html_output = Path(args.html_output)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(render_html(payload), encoding="utf-8")
    print(f"[ok] wrote {output} samples={len(payload.get('samples', []))}")
    print(f"[ok] wrote {html_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
