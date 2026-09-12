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


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _draw_vertical_gradient(img: Image.Image, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for yy in range(h):
        color = _mix(top, bottom, yy / max(h - 1, 1))
        draw.line((0, yy, w, yy), fill=color)


def _draw_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, radius: int = 26) -> None:
    draw.rounded_rectangle((x + 6, y + 8, x + w + 6, y + h + 8), radius=radius, fill=(208, 216, 226))
    draw.rounded_rectangle((x + 3, y + 4, x + w + 3, y + h + 4), radius=radius, fill=(220, 228, 236))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=(249, 251, 255))


def _draw_metric_bars(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, summary: Dict[str, Any]) -> int:
    _draw_card(draw, x, y, w, h)

    title_font = _font(34)
    sub_font = _font(18)
    text_font = _font(24)
    draw.text((x + 34, y + 24), "评测结果可视化", fill=(16, 23, 35), font=title_font)
    draw.text((x + 34, y + 68), "Track-1 API真实测评", fill=(84, 96, 112), font=sub_font)
    y += 110

    items = [
        ("合法率", float(summary.get("legality_rate", 0.0)), (53, 126, 220)),
        ("幻觉率(越低越好)", float(summary.get("hallucination_rate", 0.0)), (231, 93, 70)),
        ("FTA生产率", float(summary.get("fta_productivity_rate", 0.0)), (45, 176, 101)),
    ]

    bar_h = 38
    gap = 34
    usable = w - 390
    for label, value, color in items:
        draw.text((x + 34, y), label, fill=(37, 49, 64), font=text_font)
        bar_x = x + 300
        draw.rounded_rectangle((bar_x, y + 2, bar_x + usable, y + 2 + bar_h), radius=14, fill=(231, 236, 243))
        fill_w = int(max(0.0, min(1.0, value)) * usable)
        if fill_w > 0:
            draw.rounded_rectangle((bar_x, y + 2, bar_x + fill_w, y + 2 + bar_h), radius=14, fill=color)
        draw.text((bar_x + usable + 18, y), _pct(value), fill=(31, 40, 52), font=text_font)
        y += bar_h + gap

    stat_font = _font(23)
    y += 4
    draw.text((x + 34, y), f"样本数: {summary.get('samples_evaluated', 0)}", fill=(69, 81, 96), font=stat_font)
    y += 36
    draw.text((x + 34, y), f"平均时延: {summary.get('avg_latency_ms', '-')} ms", fill=(69, 81, 96), font=stat_font)
    y += 36
    counts = summary.get("counts", {})
    draw.text(
        (x + 34, y),
        f"幻觉字段: {counts.get('hallucination_bad_fields', 0)} / {counts.get('hallucination_total_fields', 0)}",
        fill=(69, 81, 96),
        font=stat_font,
    )
    return y + 62


def _draw_latency_hist(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, details: List[Dict[str, Any]]) -> None:
    _draw_card(draw, x, y, w, h)
    title_font = _font(29)
    text_font = _font(18)
    draw.text((x + 34, y + 24), "时延分布 (ms)", fill=(16, 23, 35), font=title_font)
    y += 78

    values = [int(d.get("latency_ms")) for d in details if isinstance(d.get("latency_ms"), int)]
    if not values:
        draw.text((x + 34, y), "无可用时延数据", fill=(100, 100, 100), font=text_font)
        return

    bins = [0, 1000, 2000, 3000, 5000, 8000, 12000]
    labels = ["0-1s", "1-2s", "2-3s", "3-5s", "5-8s", "8-12s+"]
    freq = [0] * (len(bins) - 1)
    for v in values:
        placed = False
        for i in range(len(bins) - 1):
            if bins[i] <= v < bins[i + 1]:
                freq[i] += 1
                placed = True
                break
        if not placed:
            freq[-1] += 1

    max_f = max(freq) if max(freq) > 0 else 1
    chart_h = h - 130
    bar_w = int((w - 120) / len(freq))
    chart_x = x + 34
    base_y = y + chart_h

    for i in range(5):
        gy = base_y - int(i * (chart_h / 4))
        draw.line((chart_x, gy, chart_x + w - 68, gy), fill=(228, 233, 242), width=1)

    for i, f in enumerate(freq):
        bx = chart_x + 6 + i * bar_w
        bh = int((f / max_f) * (chart_h - 20))
        by = base_y - bh
        draw.rounded_rectangle((bx, by, bx + bar_w - 20, base_y), radius=10, fill=(112, 148, 212))
        draw.text((bx + 2, base_y + 10), labels[i], fill=(78, 88, 101), font=text_font)
        draw.text((bx + 8, by - 24), str(f), fill=(50, 57, 67), font=text_font)

    p95_idx = int(len(values) * 0.95) - 1
    p95 = sorted(values)[max(0, p95_idx)]
    stat_font = _font(20)
    draw.text((x + w - 350, y - 42), f"P95时延: {p95} ms", fill=(84, 96, 112), font=stat_font)


def _render_hq(report_path: Path) -> Image.Image:
    report = _load_json(report_path)
    summary = report.get("summary", {})
    details = report.get("details", []) if isinstance(report.get("details"), list) else []

    img = Image.new("RGB", (3200, 2000), (245, 248, 252))
    _draw_vertical_gradient(img, (244, 248, 253), (233, 239, 248))
    draw = ImageDraw.Draw(img)

    y2 = _draw_metric_bars(draw, 120, 90, 2960, 760, summary)
    _draw_latency_hist(draw, 120, y2, 2960, 920, details)

    footer_font = _font(28)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((120, 1938), f"来源: {report_path.name}", fill=(112, 123, 137), font=footer_font)
    draw.text((2450, 1938), f"生成时间: {stamp}", fill=(112, 123, 137), font=footer_font)
    return img


def render(report_path: Path, output_path: Path) -> None:
    # Draw on 2x canvas then downsample to get smoother edges and text.
    img_hq = _render_hq(report_path)
    img = img_hq.resize((1600, 1000), resample=Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render benchmark report to PNG")
    parser.add_argument("--report", required=True, type=str)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    report = Path(args.report)
    output = Path(args.output) if args.output else report.with_name(report.stem + "_chart.png")
    render(report, output)
    print(f"[ok] chart: {output}")


if __name__ == "__main__":
    main()
