#!/usr/bin/env python3
"""Build a human-review bundle for the latest online extraction outputs.

The benchmark report contains metrics, while the extracted JSON files contain
the records and evidence that a reviewer actually needs to inspect.  This
renderer joins those two sources without changing the frontend or production
API.  Pairing is explicit and conservative: a project sample is paired by its
fault code with the newest matching ``*_extracted_faults.json`` file.
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_project_handbook_evidence.json"
DEFAULT_REPORT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_online_baseline_after_fallback_merge.json"
DEFAULT_OUTPUT_DIR = ROOT / "backend-python" / "outputs"
DEFAULT_JSON_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_online_review_bundle.json"
DEFAULT_HTML_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_project_handbook_online_review_checklist.html"


def _fault_code(sample: dict[str, Any]) -> str | None:
    records = sample.get("gold_records") or []
    code = records[0].get("fault_code") if records else None
    return str(code).strip() if code else None


def _prediction_codes(payload: dict[str, Any]) -> set[str]:
    return {
        str(record.get("fault_code")).strip()
        for record in payload.get("records", [])
        if record.get("fault_code")
    }


def _load_prediction_index(output_dir: Path) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for path in output_dir.glob("*_extracted_faults.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        entry = {
            "path": path,
            "payload": payload,
            "mtime": path.stat().st_mtime,
        }
        for code in _prediction_codes(payload):
            index.setdefault(code, []).append(entry)
    for entries in index.values():
        entries.sort(key=lambda item: (item["mtime"], item["path"].name))
    return index


def _evidence_audit(input_text: str, prediction: dict[str, Any] | None) -> dict[str, Any]:
    if not prediction:
        return {"total": 0, "valid": 0, "issues": ["未找到对应在线输出文件"]}
    issues: list[str] = []
    valid = 0
    spans = prediction.get("evidence_spans") or []
    record_ids = {record.get("record_id") for record in prediction.get("records", [])}
    for index, span in enumerate(spans):
        start = span.get("start")
        end = span.get("end")
        quote = span.get("quote")
        if not isinstance(start, int) or not isinstance(end, int) or not isinstance(quote, str):
            issues.append(f"证据 {index + 1} 字段不完整")
            continue
        if input_text[start:end] != quote:
            issues.append(f"证据 {index + 1} 无法回指原文")
            continue
        if span.get("record_id") not in record_ids:
            issues.append(f"证据 {index + 1} 指向不存在的记录")
            continue
        valid += 1
    return {"total": len(spans), "valid": valid, "issues": issues}


def build_bundle(
    dataset: dict[str, Any],
    report: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    index = _load_prediction_index(output_dir)
    report_by_id = {
        item.get("sample_id"): item
        for item in report.get("details", [])
        if item.get("sample_id")
    }
    samples: list[dict[str, Any]] = []
    warnings: list[str] = []
    for sample in dataset.get("samples", []):
        sample_id = str(sample.get("sample_id") or "")
        code = _fault_code(sample)
        candidates = index.get(code or "", [])
        selected = candidates[-1] if candidates else None
        prediction = selected["payload"] if selected else None
        evidence = _evidence_audit(str(sample.get("input_text") or ""), prediction)
        pairing_status = "matched" if selected else "unmatched"
        if len(candidates) > 1:
            pairing_status = "matched_latest_of_multiple"
        if not selected:
            warnings.append(f"{sample_id}: 没有找到故障码 {code or 'unknown'} 对应的在线输出")
        if evidence["issues"]:
            warnings.extend(f"{sample_id}: {issue}" for issue in evidence["issues"])
        samples.append(
            {
                "sample_id": sample_id,
                "fault_code": code,
                "input_text": sample.get("input_text", ""),
                "source": sample.get("source", {}),
                "provisional_source_record": (sample.get("gold_records") or [None])[0],
                "annotation": sample.get("annotation", {}),
                "prediction": prediction,
                "benchmark_detail": report_by_id.get(sample_id, {}),
                "pairing": {
                    "status": pairing_status,
                    "candidate_count": len(candidates),
                    "selected_file": selected["path"].name if selected else None,
                },
                "evidence_audit": evidence,
            }
        )
    return {
        "bundle_type": "online_extraction_review",
        "pairing_rule": "按项目样本故障码选择输出目录中最新的 *_extracted_faults.json；本清单不替代专家金标。",
        "source_report": str(DEFAULT_REPORT.relative_to(ROOT)).replace("\\", "/"),
        "dataset_info": dataset.get("dataset_info", {}),
        "report_summary": report.get("summary", {}),
        "warnings": warnings,
        "samples": samples,
    }


def _html_cell(value: Any, empty: str = "—") -> str:
    if value is None:
        return empty
    if isinstance(value, list):
        value = "、".join(str(item) for item in value) or empty
    return escape(str(value).replace("\n", " ").strip() or empty)


def _render_record(record: dict[str, Any] | None) -> str:
    record = record or {}
    return (
        "<div class=\"field-grid\">"
        f"<div><label>故障码</label><span class=\"value code\">{_html_cell(record.get('fault_code'))}</span></div>"
        f"<div><label>故障现象</label><span class=\"value\">{_html_cell(record.get('description'))}</span></div>"
        f"<div><label>组件</label><span class=\"value\">{_html_cell(record.get('component'))}</span></div>"
        f"<div><label>参数</label><span class=\"value\">{_html_cell(record.get('parameters'))}</span></div>"
        f"<div class=\"wide\"><label>候选原因（仍需语义审核）</label>"
        f"<span class=\"value\">{_html_cell(record.get('causes'))}</span></div>"
        "</div>"
    )


def _render_evidence(sample: dict[str, Any]) -> str:
    prediction = sample.get("prediction") or {}
    spans = prediction.get("evidence_spans") or []
    if not spans:
        evidence = '<p class="muted">没有在线证据跨度。</p>'
    else:
        rows = []
        for span in spans:
            rows.append(
                "<tr>"
                f"<td>{_html_cell(span.get('field'))}</td>"
                f"<td><code>{_html_cell(span.get('quote'))}</code></td>"
                f"<td>{_html_cell(span.get('start'))}–{_html_cell(span.get('end'))}</td>"
                f"<td>{_html_cell(span.get('record_id'))}</td>"
                "</tr>"
            )
        evidence = (
            '<table class="evidence-table"><thead><tr><th>字段</th><th>原文引用</th>'
            '<th>字符位置</th><th>记录 ID</th></tr></thead><tbody>'
            + "".join(rows)
            + "</tbody></table>"
        )
    source = sample.get("source") or {}
    audit = sample.get("evidence_audit") or {}
    audit_label = f"{audit.get('valid', 0)}/{audit.get('total', 0)} 条证据可回指原文"
    return (
        '<details class="evidence-details"><summary>查看原文与证据（'
        + escape(audit_label)
        + ")</summary>"
        f"<div class=\"source-meta\">来源行：{_html_cell(source.get('source_line_start'))}–"
        f"{_html_cell(source.get('source_line_end'))}　源文件：{_html_cell(source.get('source_file'))}</div>"
        f"<pre>{escape(str(sample.get('input_text') or ''))}</pre>"
        + evidence
        + "</details>"
    )


def render_html(bundle: dict[str, Any], initial_decisions: dict[str, Any] | None = None) -> str:
    samples = bundle.get("samples", [])
    matched = sum(item.get("pairing", {}).get("status") != "unmatched" for item in samples)
    evidence_ok = sum(
        bool(item.get("evidence_audit", {}).get("total"))
        and not item.get("evidence_audit", {}).get("issues")
        for item in samples
    )
    flagged = sum(bool(item.get("benchmark_detail", {}).get("hallucinated_fields")) for item in samples)
    cards = []
    for index, sample in enumerate(samples, start=1):
        prediction = sample.get("prediction") or {}
        records = prediction.get("records") or []
        record = records[0] if records else None
        sample_id = str(sample.get("sample_id") or f"sample-{index}")
        detail = sample.get("benchmark_detail") or {}
        pairing = sample.get("pairing") or {}
        search = " ".join(
            str(value or "")
            for value in (
                sample_id,
                sample.get("fault_code"),
                record.get("description") if record else "",
                record.get("component") if record else "",
                record.get("causes") if record else "",
            )
        ).lower()
        pairing_text = {
            "matched": "已配对",
            "matched_latest_of_multiple": "已配对（多次中最新）",
            "unmatched": "未配对",
        }.get(pairing.get("status"), "未知")
        prediction_status = prediction.get("status") or "无在线输出"
        source_record = sample.get("provisional_source_record")
        cards.append(
            '<article class="review-card" '
            f'data-search="{escape(search, quote=True)}" data-sample-id="{escape(sample_id, quote=True)}">'
            '<div class="card-top">'
            f'<div><span class="index">{index:02d}</span><strong>{_html_cell(sample_id)}</strong>'
            f'<span class="badge">{escape(pairing_text)}</span></div>'
            f'<select class="status-select" aria-label="审核状态" data-sample-id="{escape(sample_id, quote=True)}">'
            '<option value="待人工审核">待人工审核</option><option value="审核通过（证据级）">审核通过（证据级）</option>'
            '<option value="证据不足">证据不足</option><option value="语义需修改">语义需修改</option>'
            '<option value="无法判断">无法判断</option></select></div>'
            '<div class="meta-row">'
            f'<span>在线状态：<b>{_html_cell(prediction_status)}</b></span>'
            f'<span>输出文件：<code>{_html_cell(pairing.get("selected_file"))}</code></span>'
            f'<span>报告疑似问题字段：<b>{_html_cell(detail.get("hallucinated_fields"), "0")}</b></span>'
            '</div>'
            '<h3>模型抽取结果</h3>'
            + _render_record(record)
            + '<details class="reference-details"><summary>查看项目原文候选参考（非专家金标）</summary>'
            + _render_record(source_record)
            + '</details>'
            + f'<textarea class="review-note" data-sample-id="{escape(sample_id, quote=True)}" '
            'placeholder="填写审核备注：证据是否支持、字段哪里需要修改、是否暂不能判断"></textarea>'
            + _render_evidence(sample)
            + '</article>'
        )

    template = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FTA 在线抽取结果审核清单</title>
<style>
:root { --ink:#172033; --muted:#687386; --line:#e5e7eb; --panel:#fff; --bg:#f4f7fb; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; --shadow:0 8px 24px rgba(31,41,55,.07); }
* { box-sizing:border-box; } body { margin:0; color:var(--ink); background:var(--bg); font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif; }
.shell { max-width:1480px; margin:0 auto; padding:32px 28px 60px; } .hero { display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:18px; }
h1 { margin:0 0 8px; font-size:30px; letter-spacing:-.02em; } .subtitle { margin:0; color:var(--muted); } .source { color:var(--muted); font-size:12px; text-align:right; }
.notice { border:1px solid #fcd34d; background:#fffbeb; color:#92400e; border-radius:12px; padding:12px 15px; margin:0 0 18px; }
.stats { display:grid; grid-template-columns:repeat(4,minmax(130px,1fr)); gap:12px; margin-bottom:18px; } .stat { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:15px 18px; box-shadow:var(--shadow); }
.stat strong { display:block; font-size:25px; color:var(--blue); } .stat span { color:var(--muted); font-size:12px; }
.toolbar { display:flex; gap:10px; flex-wrap:wrap; align-items:center; background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; margin-bottom:18px; box-shadow:var(--shadow); }
.toolbar input,.toolbar select,.toolbar button { border:1px solid #d1d5db; border-radius:9px; padding:9px 12px; background:#fff; color:var(--ink); font:inherit; } .toolbar input { flex:1 1 320px; }
.toolbar button { cursor:pointer; border-color:var(--blue); color:var(--blue); } .toolbar button.primary { background:var(--blue); color:#fff; } .hint { color:var(--muted); font-size:12px; margin-left:auto; }
.review-card { background:var(--panel); border:1px solid var(--line); border-radius:16px; margin:0 0 14px; padding:18px; box-shadow:var(--shadow); } .review-card.hidden { display:none; }
.card-top { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; } .index { display:inline-grid; place-items:center; width:30px; height:30px; border-radius:9px; background:#eff6ff; color:var(--blue); font-weight:700; margin-right:7px; }
.badge { display:inline-block; margin-left:10px; color:var(--muted); font-size:12px; border:1px solid var(--line); border-radius:999px; padding:2px 8px; }
.status-select { border:1px solid #d1d5db; border-radius:9px; padding:7px 10px; font:inherit; background:#fff; } .meta-row { display:flex; flex-wrap:wrap; gap:12px; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); padding-bottom:11px; }
.meta-row b { color:var(--ink); } h3 { font-size:14px; margin:14px 0 9px; } .field-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; } .field-grid > div { min-width:0; background:#f8fafc; border-radius:10px; padding:10px 12px; }
.field-grid .wide { grid-column:span 2; } label { display:block; color:var(--muted); font-size:12px; margin-bottom:3px; } .value { display:block; word-break:break-word; } .code { color:var(--blue); font-weight:700; }
.review-note { width:100%; min-height:42px; resize:vertical; margin-top:13px; border:1px solid var(--line); border-radius:9px; padding:9px 11px; font:inherit; } details { margin-top:13px; } summary { cursor:pointer; color:var(--blue); font-weight:600; }
.reference-details { border-top:1px dashed var(--line); padding-top:10px; } .evidence-details { border-top:1px solid var(--line); padding-top:11px; } .source-meta { color:var(--muted); font-size:12px; margin:10px 0; }
pre { max-height:310px; overflow:auto; white-space:pre-wrap; background:#111827; color:#e5e7eb; border-radius:10px; padding:14px; font:12px/1.7 Consolas,monospace; } .evidence-table { width:100%; border-collapse:collapse; margin-top:10px; font-size:12px; }
.evidence-table th,.evidence-table td { text-align:left; vertical-align:top; border-bottom:1px solid var(--line); padding:7px; } .evidence-table th { color:var(--muted); font-weight:600; } .muted { color:var(--muted); }
@media (max-width:900px) { .hero { display:block; } .source { text-align:left; margin-top:8px; } .field-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .field-grid .wide { grid-column:span 2; } .hint { width:100%; margin-left:0; } }
@media (max-width:560px) { .shell { padding:22px 14px 40px; } h1 { font-size:24px; } .stats { grid-template-columns:repeat(2,1fr); } .field-grid { grid-template-columns:1fr; } .field-grid .wide { grid-column:span 1; } }
</style></head><body><main class="shell">
<section class="hero"><div><h1>FTA 在线抽取结果审核清单</h1><p class="subtitle">审核的是模型语义和证据，不是统计指标；审核结果不会修改原始在线输出。</p></div><div class="source">来源：当前在线基线 + 项目手册 27 条样本<br>本清单为独立审核副本</div></section>
<div class="notice">注意：项目手册候选参考仍是 <b>source_text_provisional</b>，不是专家金标。请先看模型字段和原文证据，再决定“证据支持 / 证据不足 / 语义需修改 / 无法判断”。</div>
<section class="stats"><div class="stat"><strong>__TOTAL__</strong><span>待审核样本</span></div><div class="stat"><strong>__MATCHED__</strong><span>已配对在线输出</span></div><div class="stat"><strong>__EVIDENCE_OK__</strong><span>证据可回指原文</span></div><div class="stat"><strong id="done-count">0</strong><span>已填写审核状态</span></div></section>
<section class="toolbar"><input id="search" type="search" placeholder="搜索故障码、描述、组件或原因…"><select id="filter"><option value="全部">全部审核状态</option><option>待人工审核</option><option>审核通过（证据级）</option><option>证据不足</option><option>语义需修改</option><option>无法判断</option></select><button class="primary" id="save">保存到本机</button><button id="export">导出审核结果</button><span class="hint">状态和备注仅保存在当前浏览器，可导出 JSON</span></section>
<section id="cards">__CARDS__</section></main>
<script>
const storageKey = 'fta-online-extraction-review-v1';
const initialState = __INITIAL_STATE__;
const savedState = JSON.parse(localStorage.getItem(storageKey) || 'null');
const state = savedState && Object.keys(savedState).length ? savedState : initialState;
const cards = [...document.querySelectorAll('.review-card')]; const selects = [...document.querySelectorAll('.status-select')]; const notes = [...document.querySelectorAll('.review-note')];
function entry(id) { return state[id] || {status:'待人工审核', note:''}; }
function paint(select) { const item=entry(select.dataset.sampleId); select.value=item.status; select.dataset.status=item.status; }
function updateDone() { document.querySelector('#done-count').textContent=selects.filter(s=>entry(s.dataset.sampleId).status!=='待人工审核').length; }
function applyFilter() { const query=document.querySelector('#search').value.trim().toLowerCase(); const filter=document.querySelector('#filter').value; cards.forEach(card=>{ const select=card.querySelector('.status-select'); const okText=!query||card.dataset.search.includes(query); const okStatus=filter==='全部'||select.value===filter; card.classList.toggle('hidden',!(okText&&okStatus)); }); }
selects.forEach(select=>{ paint(select); select.addEventListener('change',()=>{ const item=entry(select.dataset.sampleId); item.status=select.value; state[select.dataset.sampleId]=item; select.dataset.status=select.value; localStorage.setItem(storageKey,JSON.stringify(state)); updateDone(); applyFilter(); }); });
notes.forEach(note=>{ const item=entry(note.dataset.sampleId); note.value=item.note||''; note.addEventListener('input',()=>{ const current=entry(note.dataset.sampleId); current.note=note.value; state[note.dataset.sampleId]=current; localStorage.setItem(storageKey,JSON.stringify(state)); }); });
document.querySelector('#search').addEventListener('input',applyFilter); document.querySelector('#filter').addEventListener('change',applyFilter); document.querySelector('#save').addEventListener('click',()=>{ localStorage.setItem(storageKey,JSON.stringify(state)); alert('审核状态已保存到当前浏览器。'); });
document.querySelector('#export').addEventListener('click',()=>{ const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='fta-online-extraction-review-decisions.json'; a.click(); URL.revokeObjectURL(a.href); }); updateDone(); applyFilter();
</script></body></html>"""
    replacements = {
        "__TOTAL__": str(len(samples)),
        "__MATCHED__": str(matched),
        "__EVIDENCE_OK__": str(evidence_ok),
        "__CARDS__": "".join(cards),
        "__INITIAL_STATE__": json.dumps(initial_decisions or {}, ensure_ascii=False),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--decisions", default="", help="optional provisional review decisions JSON")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT))
    parser.add_argument("--html-output", default=str(DEFAULT_HTML_OUTPUT))
    args = parser.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    bundle = build_bundle(dataset, report, Path(args.output_dir))
    report_path = Path(args.report).resolve()
    try:
        bundle["source_report"] = report_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        bundle["source_report"] = str(report_path)
    decision_payload: dict[str, Any] = {}
    if args.decisions:
        decision_payload = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
        bundle["provisional_review"] = decision_payload
    json_output = Path(args.json_output)
    html_output = Path(args.html_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    decision_map = {
        sample_id: {"status": item.get("status", "待人工审核"), "note": item.get("reason", "")}
        for sample_id, item in (decision_payload.get("decisions") or {}).items()
    }
    html_output.write_text(render_html(bundle, decision_map), encoding="utf-8")
    matched = sum(item["pairing"]["status"] != "unmatched" for item in bundle["samples"])
    print(f"[ok] wrote {json_output} samples={len(bundle['samples'])} matched={matched}")
    print(f"[ok] wrote {html_output}")
    if bundle["warnings"]:
        print(f"[warning] {len(bundle['warnings'])} audit warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
