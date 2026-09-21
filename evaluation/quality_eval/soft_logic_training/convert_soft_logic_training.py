#!/usr/bin/env python3
"""Convert canonical soft-logic samples into task-specific SFT JSONL.

This converter is deliberately provider-neutral. It creates partial-label
record/evidence SFT files, a relation-only SFT file, and a non-training gate
review file. Missing source annotations are not converted into negative labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


RECORD_FIELDS = ("fault_code", "component", "description", "causes", "parameters")

RECORD_SYSTEM = (
    "你是故障记录与证据抽取器。只根据输入文本和本样本声明的可监督字段输出 JSON。"
    "未声明的字段表示来源没有标注，不要把它当成负样本，也不要臆造故障码、参数或根因。"
    "每个输出字段必须能由输入文本中的 evidence_spans 支持。不要决定正式 FTA 的 AND/OR 逻辑门。"
)

RELATION_SYSTEM = (
    "你是维修文本关系抽取器。只抽取输入文本中来源已经标注的关系，输出 JSON。"
    "关系标签是来源标注，不代表项目专家确认的 FTA 因果或逻辑门。"
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _field_from_target_path(target_path: str) -> str | None:
    prefix = "gold_records[0]."
    if not target_path.startswith(prefix):
        return None
    field = target_path[len(prefix) :]
    for candidate in RECORD_FIELDS:
        if field == candidate or field.startswith(f"{candidate}["):
            return candidate
    return None


def _supported_fields(sample: dict[str, Any]) -> list[str]:
    fields = {
        field
        for span in sample.get("evidence_spans", [])
        if isinstance(span, dict)
        for field in [_field_from_target_path(str(span.get("target_path") or ""))]
        if field
    }
    return [field for field in RECORD_FIELDS if field in fields]


def _partial_record(sample: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    records = sample.get("target", {}).get("records", [])
    source_record = records[0] if records and isinstance(records[0], dict) else {}
    return {field: source_record.get(field) for field in fields if field in source_record}


def _record_target(sample: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    evidence = [
        span
        for span in sample.get("evidence_spans", [])
        if isinstance(span, dict)
        and _field_from_target_path(str(span.get("target_path") or "")) in fields
    ]
    target: dict[str, Any] = {
        "records": [_partial_record(sample, fields)],
        "evidence_spans": evidence,
    }
    if "description" in fields and sample.get("target", {}).get("top_event") is not None:
        target["top_event"] = sample["target"]["top_event"]
    return target


def _record_sample(sample: dict[str, Any]) -> dict[str, Any] | None:
    fields = _supported_fields(sample)
    if not fields:
        return None
    target = _record_target(sample, fields)
    return {
        "messages": [
            {"role": "system", "content": RECORD_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"可监督字段：{', '.join(fields)}\n"
                    f"输入文本：\n{sample['input_text']}"
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(target, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "metadata": {
            "sample_id": sample["sample_id"],
            "split": sample["split"],
            "source": sample["provenance"]["dataset"],
            "label_scope": fields,
            "label_status": sample["provenance"]["label_status"],
            "human_expert_reviewed": sample["provenance"]["human_expert_reviewed"],
        },
    }


def _relation_sample(sample: dict[str, Any]) -> dict[str, Any] | None:
    relations = sample.get("target", {}).get("relations", [])
    if not relations:
        return None
    target = {"relations": relations}
    return {
        "messages": [
            {"role": "system", "content": RELATION_SYSTEM},
            {"role": "user", "content": f"输入文本：\n{sample['input_text']}"},
            {
                "role": "assistant",
                "content": json.dumps(target, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "metadata": {
            "sample_id": sample["sample_id"],
            "split": sample["split"],
            "source": sample["provenance"]["dataset"],
            "label_scope": ["relations"],
            "label_status": sample["provenance"]["label_status"],
            "human_expert_reviewed": sample["provenance"]["human_expert_reviewed"],
        },
    }


def _gate_review_sample(sample: dict[str, Any]) -> dict[str, Any] | None:
    candidate = (sample.get("target", {}).get("logic_candidates") or [None])[0]
    if not isinstance(candidate, dict) or candidate.get("gate_candidate") is None:
        return None
    return {
        "sample_id": sample["sample_id"],
        "split": sample["split"],
        "input_text": sample["input_text"],
        "candidate": candidate,
        "review_status": "needs_human_confirmation",
        "provenance": sample["provenance"],
    }


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    rows = list(rows)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(rows)


def _write_split_files(
    output_dir: Path,
    prefix: str,
    samples: list[dict[str, Any]],
    builder,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for split in ("train", "dev", "test"):
        rows = [converted for sample in samples if sample["split"] == split if (converted := builder(sample))]
        counts[split] = _write_jsonl(output_dir / f"{prefix}_{split}.jsonl", rows)
    return counts


def convert(input_path: Path, output_dir: Path) -> dict[str, Any]:
    samples = _read_jsonl(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "conversion_version": "soft_logic_sft.v1",
        "input": str(input_path),
        "sample_count": len(samples),
        "outputs": {
            "fault_record_evidence_sft": _write_split_files(
                output_dir, "fault_record_evidence_sft", samples, _record_sample
            ),
            "causal_relation_sft": _write_split_files(
                output_dir, "causal_relation_sft", samples, _relation_sample
            ),
            "gate_candidate_review": {},
        },
        "policy": {
            "partial_labels_are_not_negative_labels": True,
            "project_handbook_is_test_only": True,
            "gate_candidates_are_not_sft_targets": True,
            "provider_adapter_must_strip_metadata_if_unsupported": True,
        },
    }
    gate_rows = [
        converted
        for sample in samples
        if (converted := _gate_review_sample(sample))
    ]
    manifest["outputs"]["gate_candidate_review"] = {
        "all": _write_jsonl(output_dir / "gate_candidate_review.jsonl", gate_rows),
        "by_status": dict(Counter(row["candidate"]["status"] for row in gate_rows)),
    }
    (output_dir / "conversion_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = convert(args.input, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
