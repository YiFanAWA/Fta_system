#!/usr/bin/env python3
"""Build a seed evaluation dataset from project text sources.

Usage:
  python evaluation/quality_eval/build_eval_dataset.py
  python evaluation/quality_eval/build_eval_dataset.py --limit 300
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DEFAULT = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_eval_seed.json"


@dataclass
class Sample:
    sample_id: str
    split: str
    source_type: str
    difficulty_tag: str
    input_text: str
    gold_top_event: str
    gold_records: List[Dict[str, Any]]
    gold_relations: List[Dict[str, str]]
    evidence_spans: List[Dict[str, Any]]
    expected_metrics_tags: Dict[str, bool]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "split": self.split,
            "source_type": self.source_type,
            "difficulty_tag": self.difficulty_tag,
            "input_text": self.input_text,
            "gold_top_event": self.gold_top_event,
            "gold_records": self.gold_records,
            "gold_relations": self.gold_relations,
            "evidence_spans": self.evidence_spans,
            "expected_metrics_tags": self.expected_metrics_tags,
            "notes": self.notes,
        }


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s


def _split_for_manual(text: str, max_chars: int = 900) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    cur = ""
    for p in paragraphs:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + "\n" + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


def _difficulty_from_text(text: str) -> str:
    n = len(text)
    if n < 220:
        return "easy"
    if n < 900:
        return "medium"
    return "hard"


def _stable_split(key: str) -> str:
    digest = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % 100
    if digest < 15:
        return "dev"
    if digest < 35:
        return "test"
    return "train"


def _record_to_text(record: Dict[str, Any]) -> str:
    fault_code = str(record.get("fault_code", "")).strip()
    component = str(record.get("component", "")).strip()
    description = str(record.get("description", "")).strip()
    causes = record.get("causes", []) if isinstance(record.get("causes"), list) else []
    parameters = record.get("parameters", []) if isinstance(record.get("parameters"), list) else []
    cause_text = "、".join([str(x).strip() for x in causes if str(x).strip()])
    param_text = "、".join([str(x).strip() for x in parameters if str(x).strip()])

    lines = [
        f"故障代码：{fault_code or '未知'}",
        f"组件：{component or '未知'}",
        f"故障描述：{description or '未知'}",
    ]
    if cause_text:
        lines.append(f"可能原因：{cause_text}")
    if param_text:
        lines.append(f"相关参数：{param_text}")
    return "。".join(lines) + "。"


def _basic_relation_from_record(record: Dict[str, Any]) -> List[Dict[str, str]]:
    description = str(record.get("description", "")).strip()
    causes = record.get("causes", []) if isinstance(record.get("causes"), list) else []
    out = []
    for c in causes:
        cc = str(c).strip()
        if cc and description:
            out.append({"cause": cc, "effect": description, "relation": "CAUSES"})
    return out


def _build_sample_from_record(idx: int, record: Dict[str, Any], source_type: str, note: str) -> Sample:
    input_text = _record_to_text(record)
    desc = str(record.get("description", "")).strip()
    top_event = desc or "系统关键故障"
    key = f"{record.get('fault_code','')}|{desc}|{source_type}"
    split = _stable_split(key)

    sample_id = f"S{idx:05d}"
    relations = _basic_relation_from_record(record)
    return Sample(
        sample_id=sample_id,
        split=split,
        source_type=source_type,
        difficulty_tag=_difficulty_from_text(input_text),
        input_text=input_text,
        gold_top_event=top_event,
        gold_records=[
            {
                "fault_code": str(record.get("fault_code", "")).strip(),
                "component": str(record.get("component", "")).strip(),
                "description": desc,
                "causes": [str(x).strip() for x in record.get("causes", []) if str(x).strip()],
                "parameters": [str(x).strip() for x in record.get("parameters", []) if str(x).strip()],
            }
        ],
        gold_relations=relations,
        evidence_spans=[],
        expected_metrics_tags={
            "count_for_legality": True,
            "count_for_hallucination": True,
            "count_for_fta_productivity": True,
        },
        notes=note,
    )


def _build_sample_from_raw(idx: int, text: str, source_type: str, note: str) -> Sample:
    cleaned = _clean_text(text)
    sample_id = f"S{idx:05d}"
    split = _stable_split(cleaned[:80])
    return Sample(
        sample_id=sample_id,
        split=split,
        source_type=source_type,
        difficulty_tag=_difficulty_from_text(cleaned),
        input_text=cleaned,
        gold_top_event="待标注",
        gold_records=[],
        gold_relations=[],
        evidence_spans=[],
        expected_metrics_tags={
            "count_for_legality": True,
            "count_for_hallucination": False,
            "count_for_fta_productivity": True,
        },
        notes=note,
    )


def collect_seed_samples(limit: int) -> Tuple[List[Sample], Dict[str, int]]:
    samples: List[Sample] = []
    dedup = set()
    seq = 1

    def add_sample(sample: Sample, dedup_key: str) -> None:
        nonlocal seq
        if dedup_key in dedup:
            return
        dedup.add(dedup_key)
        sample.sample_id = f"S{seq:05d}"
        samples.append(sample)
        seq += 1

    corrected = _read_json(ROOT / "evaluation" / "data_correction" / "outputs" / "kb_corrected_v2.json")
    if corrected and isinstance(corrected.get("records"), list):
        for record in corrected["records"]:
            if not isinstance(record, dict):
                continue
            desc = str(record.get("description", "")).strip()
            if not desc:
                continue
            sample = _build_sample_from_record(seq, record, "kb_corrected", "silver label from corrected KB")
            add_sample(sample, f"kb|{record.get('fault_code','')}|{desc}")
            if len(samples) >= limit:
                break

    if len(samples) < limit:
        output_dir = ROOT / "backend-python" / "outputs"
        for path in sorted(output_dir.glob("*_extracted_faults.json"), reverse=True):
            payload = _read_json(path)
            records = payload.get("records", []) if isinstance(payload, dict) else []
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                desc = str(record.get("description", "")).strip()
                if not desc:
                    continue
                sample = _build_sample_from_record(seq, record, "extracted_output", f"from {path.name}")
                add_sample(sample, f"ex|{record.get('fault_code','')}|{desc}")
                if len(samples) >= limit:
                    break
            if len(samples) >= limit:
                break

    if len(samples) < limit:
        manual_text = _read_text(ROOT / "manual_handbook_sample.txt")
        if manual_text:
            for chunk in _split_for_manual(manual_text):
                sample = _build_sample_from_raw(seq, chunk, "manual_text", "raw handbook chunk; needs annotation")
                add_sample(sample, f"mt|{chunk[:120]}")
                if len(samples) >= limit:
                    break

    if len(samples) < limit:
        req = _read_json(ROOT / "request_text.json")
        if req and req.get("raw_text"):
            text = str(req.get("raw_text", "")).strip()
            if text:
                sample = _build_sample_from_raw(seq, text, "request_text", "raw_text from request payload")
                add_sample(sample, f"rq|{text}")

    stats = {
        "total": len(samples),
        "kb_corrected": sum(1 for s in samples if s.source_type == "kb_corrected"),
        "extracted_output": sum(1 for s in samples if s.source_type == "extracted_output"),
        "manual_text": sum(1 for s in samples if s.source_type == "manual_text"),
        "request_text": sum(1 for s in samples if s.source_type == "request_text"),
    }
    return samples[:limit], stats


def build_dataset(samples: List[Sample], stats: Dict[str, int]) -> Dict[str, Any]:
    split_count = {
        "train": sum(1 for s in samples if s.split == "train"),
        "dev": sum(1 for s in samples if s.split == "dev"),
        "test": sum(1 for s in samples if s.split == "test"),
    }

    return {
        "dataset_info": {
            "name": "fta_eval_seed",
            "version": "1.0.0",
            "language": "zh-CN",
            "task": "fault_extraction_and_fta_generation",
            "description": "Auto-collected seed dataset from handbook and extracted outputs",
            "created_at": str(date.today()),
            "owner": "auto_builder",
            "warning": "Contains silver labels; complete evidence_spans and verify gold labels before formal benchmark.",
        },
        "label_schema": {
            "record_fields": ["fault_code", "component", "description", "causes", "parameters"],
            "required_fields": ["description", "causes"],
            "fta_min_requirements": {
                "must_have_top_event": True,
                "min_first_level_causes": 1,
                "allow_gate": ["OR", "AND"],
            },
        },
        "stats": {
            **stats,
            "split": split_count,
        },
        "samples": [s.to_dict() for s in samples],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build seed eval dataset from project text sources")
    parser.add_argument("--limit", type=int, default=300, help="max number of samples")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DEFAULT), help="output JSON path")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    samples, stats = collect_seed_samples(limit=max(1, args.limit))
    dataset = build_dataset(samples, stats)
    output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] wrote dataset: {output}")
    print(f"[ok] total samples: {len(samples)}")
    print(f"[ok] source stats: {stats}")


if __name__ == "__main__":
    main()
