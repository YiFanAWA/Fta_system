#!/usr/bin/env python3
"""Build a conservative, project-owned evidence set from the handbook sample.

The handbook contains explicit fault-code sections and troubleshooting notes,
but it is not an expert-reviewed engineering standard. This builder therefore
preserves source spans and emits provisional labels only. It does not infer
FTA gates, top-event relations, or component ownership when the source says
that the component is unknown/related rather than directly identified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "backend-python" / "examples" / "manual_handbook_sample.txt"
DEFAULT_OUTPUT = (
    ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_project_handbook_evidence.json"
)

FAULT_HEADER_RE = re.compile(r"故障代码(?P<code>[A-Z]\d{5})")
TREATMENT_START_RE = re.compile(r"针对(?P<code>[A-Z]\d{5})")
SECTION_HEADING_RE = re.compile(r"(?m)^\d+(?:\.\d+)+\s+")
PARAMETER_RE = re.compile(r"(?<![A-Za-z0-9])[pr]\d{4,5}(?![A-Za-z0-9])", re.IGNORECASE)
CAUSE_SCENARIO_RE = re.compile(
    r"若故障值为[^（\n]*（(?P<cause>[^）]+)）"
)
CAUSE_AVOID_RE = re.compile(
    r"(?:避免|防止)(?P<cause>[^，。；]{2,20})导致"
)


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _source_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fault_block(text: str, code: str) -> Optional[Tuple[str, int, int]]:
    matches = list(FAULT_HEADER_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group("code") != code:
            continue
        start = match.start()
        next_fault_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        next_section = SECTION_HEADING_RE.search(text, match.end())
        next_section_start = next_section.start() if next_section else len(text)
        end = min(next_fault_start, next_section_start)
        return text[start:end].strip(), start, end
    return None


def _treatment_block(text: str, code: str) -> Optional[Tuple[str, int, int]]:
    matches = list(TREATMENT_START_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group("code") != code:
            continue
        start = match.start()
        next_treatment_start = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )
        next_section = SECTION_HEADING_RE.search(text, match.end())
        next_section_start = next_section.start() if next_section else len(text)
        end = min(next_treatment_start, next_section_start)
        # The document disclaimer is not part of a troubleshooting record.
        disclaimer = text.find("（注：", start, end)
        if disclaimer >= 0:
            end = disclaimer
        return text[start:end].strip(), start, end
    return None


def _span(
    input_text: str,
    start: int,
    end: int,
    target_path: str,
    source_column: str,
    evidence_status: str = "literal_match",
) -> Dict[str, Any]:
    return {
        "target_type": "field",
        "target_path": target_path,
        "evidence_text": input_text[start:end],
        "start_char": start,
        "end_char": end,
        "source_column": source_column,
        "evidence_status": evidence_status,
    }


def _field_match(
    block: str, pattern: str, group: str = "value"
) -> Optional[Tuple[str, int, int]]:
    match = re.search(pattern, block, flags=re.DOTALL)
    if match is None:
        return None
    start, end = match.span(group)
    return _compact(match.group(group)), start, end


def _parameters(input_text: str) -> List[Tuple[str, int, int]]:
    result: List[Tuple[str, int, int]] = []
    seen: set[str] = set()
    for match in PARAMETER_RE.finditer(input_text):
        value = match.group(0).lower()
        if value in seen:
            continue
        seen.add(value)
        result.append((value, match.start(), match.end()))
    return result


def _causes(
    input_text: str, treatment_offset: int, treatment: str
) -> List[Tuple[str, int, int]]:
    candidates: List[Tuple[str, int, int]] = []
    for match in CAUSE_SCENARIO_RE.finditer(treatment):
        start, end = match.span("cause")
        candidates.append((_compact(match.group("cause")), start, end))
    for match in CAUSE_AVOID_RE.finditer(treatment):
        start, end = match.span("cause")
        candidates.append((_compact(match.group("cause")), start, end))

    result: List[Tuple[str, int, int]] = []
    seen: set[str] = set()
    for value, start, end in sorted(candidates, key=lambda item: item[1]):
        if not value or value in seen:
            continue
        seen.add(value)
        result.append((value, treatment_offset + start, treatment_offset + end))
    return result


def _build_sample(text: str, source_path: Path, code: str, source_hash: str) -> Optional[Dict[str, Any]]:
    block_info = _fault_block(text, code)
    if block_info is None:
        return None
    block, source_start, source_end = block_info

    treatment_info = _treatment_block(text, code)
    treatment = treatment_info[0] if treatment_info else ""

    prefix = "故障定义：\n"
    separator = "\n\n故障处理：\n" if treatment else ""
    input_text = prefix + block + separator + treatment
    block_offset = len(prefix)
    treatment_offset = block_offset + len(block) + len(separator) if treatment else 0

    spans: List[Dict[str, Any]] = []
    code_match = re.search(r"故障代码(?P<code>[A-Z]\d{5})", block)
    if code_match is not None:
        code_start, code_end = code_match.span("code")
        spans.append(
            _span(
                input_text,
                block_offset + code_start,
                block_offset + code_end,
                "gold_records[0].fault_code",
                "fault_code",
            )
        )

    description_match = _field_match(block, r"故障现象为(?P<value>.+?)(?=。)")
    description = description_match[0] if description_match else None
    if description_match:
        _, start, end = description_match
        spans.append(
            _span(
                input_text,
                block_offset + start,
                block_offset + end,
                "gold_records[0].description",
                "fault_phenomenon",
                "literal_match_normalized_whitespace",
            )
        )

    component_match = _field_match(block, r"组\s*件\s*为(?P<value>.+?)(?=，|。)")
    component = None
    if component_match and not component_match[0].startswith("无"):
        component = component_match[0]
        _, start, end = component_match
        spans.append(
            _span(
                input_text,
                block_offset + start,
                block_offset + end,
                "gold_records[0].component",
                "component",
                "literal_match_normalized_whitespace",
            )
        )

    parameter_values = _parameters(input_text)
    for index, (_, start, end) in enumerate(parameter_values):
        spans.append(
            _span(
                input_text,
                start,
                end,
                f"gold_records[0].parameters[{index}]",
                "parameter_token",
            )
        )

    cause_values = _causes(input_text, treatment_offset, treatment)
    for index, (_, start, end) in enumerate(cause_values):
        spans.append(
            _span(
                input_text,
                start,
                end,
                f"gold_records[0].causes[{index}]",
                "fault_value_scenario",
                "literal_match_normalized_whitespace",
            )
        )

    record = {
        "fault_code": code,
        "component": component,
        "description": description,
        "causes": [value for value, _, _ in cause_values],
        "parameters": [value for value, _, _ in parameter_values],
        "gate_type": None,
    }

    source_rel = source_path.relative_to(ROOT).as_posix()
    return {
        "sample_id": f"PH-{code}",
        "split": "test",
        "source_type": "project_handbook_sample",
        "difficulty_tag": "medium" if treatment else "easy",
        "input_text": input_text,
        "gold_top_event": None,
        "gold_records": [record],
        "gold_relations": [],
        "evidence_spans": spans,
        "expected_metrics_tags": {
            "count_for_legality": True,
            "count_for_hallucination": True,
            "count_for_fta_productivity": False,
            "count_for_evidence": True,
            "count_for_causal_logic": False,
        },
        "source": {
            "dataset": "project_manual_handbook_sample",
            "source_file": source_rel,
            "source_sha256": source_hash,
            "source_char_start": source_start,
            "source_char_end": source_end,
            "source_line_start": _line_number(text, source_start),
            "source_line_end": _line_number(text, source_end),
            "source_columns": {
                "fault_code": "故障代码...",
                "description": "故障现象为...",
                "component": "组件为...（仅保留明确非无组件）",
                "parameters": "原文中的p/r参数标记",
                "causes": "故障处理中若故障值为...括号内场景标签",
            },
            "source_disclaimer": "原手册注明部分内容可能由AI生成。",
        },
        "annotation": {
            "label_status": "source_text_provisional",
            "human_expert_reviewed": False,
            "engineering_verified": False,
            "evidence_policy": "只接受输入文本中可回指的原文片段",
            "unknown_fields": ["gate_type", "gold_top_event", "gold_relations"],
            "causal_logic_status": "unknown",
            "cause_label_policy": "故障值场景候选，不等同于专家确认的根因",
        },
        "notes": (
            "该样本来自项目手册原文。字段可用于证据对齐和抽取回归，不能单独作为"
            "工程故障树金标或自动批准审核的依据。"
        ),
    }


def build_dataset(input_path: Path) -> Dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    source_hash = _source_file_hash(input_path)
    codes: List[str] = []
    seen_codes: set[str] = set()
    for match in FAULT_HEADER_RE.finditer(text):
        code = match.group("code")
        if code in seen_codes:
            continue
        block_info = _fault_block(text, code)
        if block_info is None or "故障现象为" not in block_info[0]:
            continue
        seen_codes.add(code)
        codes.append(code)
    samples = [
        sample
        for code in codes
        if (sample := _build_sample(text, input_path, code, source_hash)) is not None
    ]
    return {
        "dataset_info": {
            "name": "fta_project_handbook_evidence",
            "version": "1.0.0",
            "language": "zh-CN",
            "task": "project_owned_evidence_grounded_fault_record_extraction",
            "description": "从项目手册样例构建的、带原文偏移的临时证据集。",
            "created_at": date.today().isoformat(),
            "owner": "project_evaluation",
            "label_status": "source_text_provisional",
            "warning": (
                "该数据集不是专家审核的工程金标。手册注明部分内容可能由AI生成；"
                "逻辑门、顶事件关系和因果逻辑保持未知。"
            ),
            "source": {
                "dataset": "project_manual_handbook_sample",
                "file": input_path.relative_to(ROOT).as_posix(),
                "sha256": source_hash,
            },
            "stats": {
                "total": len(samples),
                "split": {"test": len(samples)},
                "with_evidence": sum(bool(sample["evidence_spans"]) for sample in samples),
                "with_cause_candidates": sum(
                    bool(sample["gold_records"][0]["causes"]) for sample in samples
                ),
            },
        },
        "label_schema": {
            "record_fields": ["fault_code", "component", "description", "causes", "parameters"],
            "evidence_span_fields": [
                "fault_code",
                "component",
                "description",
                "causes[*]",
                "parameters[*]",
            ],
            "unknown_policy": "原文没有明确值时使用null/[]，不自动补全工程语义。",
        },
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    payload = build_dataset(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] wrote {output} samples={payload['dataset_info']['stats']['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
