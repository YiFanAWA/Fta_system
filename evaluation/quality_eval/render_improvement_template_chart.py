#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

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


def _clip(v: float) -> float:
    return max(0.0, min(1.0, v))


def _bg(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    top = (244, 248, 254)
    bottom = (233, 239, 248)
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        draw.line((0, yy, w, yy), fill=c)


def _card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    draw.rounded_rectangle((x + 4, y + 6, x + w + 4, y + h + 6), radius=24, fill=(211, 219, 230))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=(250, 252, 255))


def _extract_metrics(general_report: Dict[str, Any], logic_report: Dict[str, Any]) -> List[Tuple[str, float, float]]:
    gs = general_report.get("summary", {}) if isinstance(general_report.get("summary"), dict) else {}
    ls = logic_report.get("summary", {}) if isinstance(logic_report.get("summary"), dict) else {}

    current = {
        "结构合法率": float(gs.get("legality_rate", 0.0)),
        "FTA生产率": float(gs.get("fta_productivity_rate", 0.0)),
        "低幻觉质量": 1.0 - float(gs.get("hallucination_rate", 0.0)),
        "基本事件F1": float(ls.get("basic_event_micro_f1", 0.0)),
        "严格逻辑一致率": float(ls.get("strict_logic_ok_rate", 0.0) or 0.0),
    }

    target = {
        "结构合法率": 0.98,
        "FTA生产率": 0.98,
        "低幻觉质量": 0.99,
        "基本事件F1": 0.85,
        "严格逻辑一致率": 0.80,
    }

    return [(k, _clip(current[k]), _clip(target[k])) for k in current.keys()]


def render(general_report_path: Path, logic_report_path: Path, output_path: Path) -> None:
    general_report = _load_json(general_report_path)
    logic_report = _load_json(logic_report_path)
    rows = _extract_metrics(general_report, logic_report)

    img = Image.new("RGB", (1700, 1100), (245, 248, 253))
    _bg(img)
    draw = ImageDraw.Draw(img)

    _card(draw, 70, 55, 1560, 940)
    title_f = _font(36)
    sub_f = _font(19)
    label_f = _font(23)
    val_f = _font(20)

    draw.text((100, 85), "优化前后对比图模板（当前指标 vs 目标指标）", fill=(17, 24, 36), font=title_f)
    draw.text((100, 135), "注：可在每轮模型/规则优化后更新当前值，用于答辩与里程碑评审", fill=(86, 98, 114), font=sub_f)

    legend_y = 176
    draw.rounded_rectangle((100, legend_y, 140, legend_y + 18), radius=6, fill=(95, 143, 220))
    draw.text((148, legend_y - 3), "当前", fill=(52, 63, 79), font=val_f)
    draw.rounded_rectangle((220, legend_y, 260, legend_y + 18), radius=6, fill=(84, 181, 116))
    draw.text((268, legend_y - 3), "目标", fill=(52, 63, 79), font=val_f)

    x0 = 100
    y = 230
    bar_w = 1080
    row_h = 128

    for name, cur, tar in rows:
        draw.text((x0, y), name, fill=(36, 47, 62), font=label_f)

        # base line
        by = y + 48
        draw.rounded_rectangle((x0, by, x0 + bar_w, by + 28), radius=12, fill=(231, 236, 243))

        # current
        c_w = int(bar_w * cur)
        if c_w > 0:
            draw.rounded_rectangle((x0, by, x0 + c_w, by + 28), radius=12, fill=(95, 143, 220))

        # target marker and overlay
        t_w = int(bar_w * tar)
        if t_w > 0:
            draw.rounded_rectangle((x0, by + 32, x0 + t_w, by + 48), radius=8, fill=(84, 181, 116))
            draw.line((x0 + t_w, by - 8, x0 + t_w, by + 58), fill=(62, 151, 95), width=3)

        draw.text((x0 + bar_w + 25, by - 2), f"当前 {_pct(cur)}", fill=(52, 63, 79), font=val_f)
        draw.text((x0 + bar_w + 25, by + 28), f"目标 {_pct(tar)}", fill=(52, 63, 79), font=val_f)
        y += row_h

    foot_f = _font(17)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((100, 1010), f"来源: {general_report_path.name} + {logic_report_path.name}", fill=(112, 122, 136), font=foot_f)
    draw.text((1360, 1010), f"生成时间: {ts}", fill=(112, 122, 136), font=foot_f)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render current-vs-target comparison template chart")
    parser.add_argument("--general-report", required=True, type=str)
    parser.add_argument("--logic-report", required=True, type=str)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    g = Path(args.general_report)
    l = Path(args.logic_report)
    out = Path(args.output) if args.output else l.with_name("optimization_compare_template_chart.png")
    render(g, l, out)
    print(f"[ok] chart: {out}")


if __name__ == "__main__":
    main()
