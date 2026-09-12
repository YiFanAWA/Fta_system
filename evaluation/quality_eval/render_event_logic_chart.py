#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _font(size: int):
    for name in ["msyh.ttc", "simhei.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _mix(c1, c2, t: float):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _bg(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for yy in range(h):
        color = _mix((245, 248, 253), (233, 239, 248), yy / max(1, h - 1))
        draw.line((0, yy, w, yy), fill=color)


def _card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    draw.rounded_rectangle((x + 5, y + 7, x + w + 5, y + h + 7), radius=24, fill=(207, 216, 227))
    draw.rounded_rectangle((x + 2, y + 4, x + w + 2, y + h + 4), radius=24, fill=(221, 229, 238))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=(249, 251, 255))


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _pct_or_na(v: Any) -> str:
    if isinstance(v, (int, float)):
        return _pct(float(v))
    return "N/A"


def _bars(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, summary: Dict[str, Any]) -> int:
    _card(draw, x, y, w, 630)
    title_f = _font(34)
    sub_f = _font(18)
    label_f = _font(23)
    val_f = _font(20)

    draw.text((x + 30, y + 24), "故障树事件与逻辑评估", fill=(17, 24, 36), font=title_f)
    draw.text((x + 30, y + 68), "规则评估 + AI严格口径", fill=(83, 97, 112), font=sub_f)

    items = [
        ("基本事件F1", float(summary.get("basic_event_micro_f1", 0.0)), (82, 130, 214)),
        ("树合法率", float(summary.get("tree_valid_rate", 0.0)), (55, 172, 106)),
        ("门合法率", float(summary.get("gate_valid_rate", 0.0)), (55, 172, 106)),
    ]

    h_val = summary.get("heuristic_logic_ok_rate")
    if isinstance(h_val, (int, float)):
        items.append(("启发式逻辑一致率", float(h_val), (95, 153, 224)))

    strict_v = summary.get("strict_logic_ok_rate")
    if isinstance(strict_v, (int, float)):
        items.append(("严格逻辑一致率", float(strict_v), (225, 110, 71)))

    bar_y = y + 112
    bar_h = 34
    gap = 26
    bar_x = x + 300
    usable = w - 430
    for label, value, color in items:
        draw.text((x + 30, bar_y), label, fill=(39, 50, 65), font=label_f)
        draw.rounded_rectangle((bar_x, bar_y + 2, bar_x + usable, bar_y + 2 + bar_h), radius=12, fill=(231, 236, 243))
        fill_w = int(max(0.0, min(1.0, value)) * usable)
        if fill_w > 0:
            draw.rounded_rectangle((bar_x, bar_y + 2, bar_x + fill_w, bar_y + 2 + bar_h), radius=12, fill=color)
        draw.text((bar_x + usable + 16, bar_y), _pct(value), fill=(31, 40, 52), font=label_f)
        bar_y += bar_h + gap

    if not isinstance(h_val, (int, float)):
        draw.text((x + 30, bar_y - 8), "启发式逻辑一致率: N/A（样本缺少明确AND/OR文本线索）", fill=(106, 116, 128), font=val_f)
        bar_y += 24

    stat_f = _font(21)
    counts = summary.get("counts", {}) if isinstance(summary.get("counts"), dict) else {}
    draw.text((x + 30, y + 470), f"样本数: {summary.get('samples_evaluated', 0)}", fill=(71, 82, 97), font=stat_f)
    draw.text((x + 260, y + 470), f"平均时延: {summary.get('avg_latency_ms', '-')} ms", fill=(71, 82, 97), font=stat_f)
    draw.text((x + 30, y + 505), f"TP/FP/FN: {counts.get('event_tp', 0)} / {counts.get('event_fp', 0)} / {counts.get('event_fn', 0)}", fill=(71, 82, 97), font=stat_f)
    if counts.get("heuristic_logic_applicable") is not None:
        draw.text((x + 30, y + 575), f"启发式适用样本数: {counts.get('heuristic_logic_applicable', 0)}", fill=(71, 82, 97), font=stat_f)

    th = summary.get("ai_logic_threshold")
    if th is not None:
        draw.text((x + 30, y + 540), f"AI阈值: {th}  |  AI平均逻辑分: {summary.get('ai_logic_score_avg', '-')}", fill=(71, 82, 97), font=stat_f)

    return y + 650


def _top_worst(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, details: List[Dict[str, Any]]) -> None:
    _card(draw, x, y, w, 360)
    title_f = _font(28)
    row_f = _font(20)
    draw.text((x + 30, y + 20), "低分样本（按AI逻辑分）", fill=(18, 26, 37), font=title_f)

    filtered = [d for d in details if isinstance(d.get("ai_logic_score"), (int, float))]
    filtered.sort(key=lambda d: float(d.get("ai_logic_score", 0.0)))
    show = filtered[:5]
    if not show:
        draw.text((x + 30, y + 80), "当前报告未启用AI评分或无可用数据", fill=(110, 120, 133), font=row_f)
        return

    yy = y + 78
    for i, d in enumerate(show, start=1):
        sid = str(d.get("sample_id", "-"))
        score = float(d.get("ai_logic_score", 0.0))
        ef1 = float(d.get("event_f1", 0.0))
        txt = f"{i}. {sid}  |  AI逻辑分: {score:.2f}  |  事件F1: {ef1:.2f}"
        draw.text((x + 30, yy), txt, fill=(62, 73, 87), font=row_f)
        yy += 50


def render(report_path: Path, output_path: Path) -> None:
    data = _load_json(report_path)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    details = data.get("details", []) if isinstance(data.get("details"), list) else []

    img = Image.new("RGB", (1700, 1200), (245, 248, 253))
    _bg(img)
    draw = ImageDraw.Draw(img)

    y2 = _bars(draw, 70, 60, 1560, summary)
    _top_worst(draw, 70, y2, 1560, details)

    foot_f = _font(17)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((70, 1166), f"来源: {report_path.name}", fill=(112, 122, 136), font=foot_f)
    draw.text((1340, 1166), f"生成时间: {stamp}", fill=(112, 122, 136), font=foot_f)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render event-logic evaluation report to PNG")
    parser.add_argument("--report", required=True, type=str)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    report = Path(args.report)
    output = Path(args.output) if args.output else report.with_name(report.stem + "_chart.png")
    render(report, output)
    print(f"[ok] chart: {output}")


if __name__ == "__main__":
    main()
