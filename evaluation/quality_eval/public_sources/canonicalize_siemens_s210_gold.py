#!/usr/bin/env python3
"""Build the canonicalized, official-evaluation SINAMICS S210 gold set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


# Exact values observed in the reviewed 30-sample set. The source value is
# retained on each record for audit; only the canonical value is used by F1.
COMPONENT_ALIASES: dict[str, str] = {
    "电机": "Motor",
    "Motor": "Motor",
    "编码器": "Encoder",
    "Encoder": "Encoder",
    "驱动器": "Drive",
    "Drive": "Drive",
    "PROFINET接口": "PROFINET interface",
    "PROFINET interface": "PROFINET interface",
    "控制单元": "Control Unit",
    "Control Unit": "Control Unit",
    "电源模块": "Power Module",
    "Power Module": "Power Module",
    "电缆": "Cable",
    "Cable": "Cable",
    "安全模块": "Safety Module",
    "Safety Module": "Safety Module",
    "DRIVE-CLiQ 组件": "DRIVE-CLiQ component",
    "SI Motion（安全集成运动监控）": "SI Motion",
    "SI Motion（安全集成运动）": "SI Motion",
    "SI（Safety Integrated 安全集成）": "Safety Integrated",
    "功能发生器（Function generator）": "Function generator",
    "Web 服务器": "Web server",
    "功率单元（Power unit）": "Power unit",
    "DRIVE-CLiQ 插座 X100": "DRIVE-CLiQ socket X100",
    "控制系统（内部软件）": "Control system (internal software)",
    "参数配置系统": "Parameter configuration system",
    "DRIVE-CLiQ 线路": "DRIVE-CLiQ line",
    "DRIVE-CLiQ": "DRIVE-CLiQ",
    "驱动器（Drive）": "Drive",
    "PN/COMM BOARD": "PN/COMM board",
    "编码器 1（Encoder 1）": "Encoder 1",
    "编码器 1（DRIVE-CLiQ）": "Encoder 1 (DRIVE-CLiQ)",
    "Control Unit（控制单元）": "Control Unit",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _canonical(value: Any, *, aliases: dict[str, str]) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return aliases[text]
    except KeyError as exc:
        raise ValueError(f"unmapped component value: {text!r}") from exc


def _canonicalize_list(values: Any, *, aliases: dict[str, str]) -> tuple[list[str], list[str]]:
    if not isinstance(values, list):
        return [], []
    original = [str(value).strip() for value in values if str(value or "").strip()]
    return [aliases[value] for value in original], original


def canonicalize_dataset(source: dict[str, Any]) -> dict[str, Any]:
    dataset = json.loads(json.dumps(source, ensure_ascii=False))
    aliases = dict(COMPONENT_ALIASES)
    changed_records = 0
    for sample in dataset.get("samples", []):
        records = sample.get("gold_records") if isinstance(sample, dict) else None
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            original_component = record.get("component")
            canonical_component = _canonical(original_component, aliases=aliases)
            if canonical_component is not None:
                record["component_original_v2"] = original_component
                record["component"] = canonical_component
                changed_records += 1
            canonical_related, original_related = _canonicalize_list(
                record.get("related_components"), aliases=aliases
            )
            if original_related:
                record["related_components_original_v2"] = original_related
                record["related_components"] = canonical_related

    dataset["component_aliases"] = aliases
    dataset["evaluation_policy"] = {
        "component": {
            "storage": "canonical_english_label",
            "aliases": "component_aliases maps source/display aliases to canonical labels",
            "display": "source values remain in component_original_v2/related_components_original_v2 for audit",
        },
        "description": {
            "level": "L3",
            "core_proposition": ["fault_phenomenon", "involved_component", "behavior_or_state"],
            "allowed": ["synonym replacement", "active_passive variation", "sentence restructuring"],
            "disallowed": ["missing core proposition", "new unsupported fault object"],
            "scores": {"fully_equivalent": 1.0, "partially_equivalent": 0.5, "not_equivalent": 0.0},
        },
        "causes": {
            "level": "L4",
            "preprocess": ["remove Possible causes prefix", "ignore parameter subscript in parentheses when context is unique"],
            "split": "a compound gold cause may match multiple predicted atomic causes",
            "score": "coverage multiplied by precision",
        },
        "logic_gate": {"status": "excluded_from_f1", "reason": "all current samples are unknown"},
    }

    info = dataset.setdefault("dataset_info", {})
    info["version"] = "v3-official-f1"
    info["label_status"] = "expert_reviewed_canonicalized_official"
    info["canonical_component_count"] = len(set(aliases.values()))
    review = info.setdefault("review", {})
    review["component_canonicalization_confirmed"] = True
    review["semantic_match_policy_confirmed"] = True
    review["logic_gate_confirmed"] = False
    review["canonicalized_record_count"] = changed_records

    status = dataset.setdefault("gold_status", {})
    status.update(
        {
            "independent_expert_reviewed": True,
            "reviewer_identity_verified": True,
            "not_for_training": True,
            "f1_ready": True,
            "f1_blocker": None,
            "f1_scope": "official field F1 with L3 description and L4 causes; AND/OR logic gates excluded",
            "logic_gate_status": "excluded_from_f1",
        }
    )
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = canonicalize_dataset(_read_json(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": dataset["dataset_info"]["version"],
        "f1_ready": dataset["gold_status"]["f1_ready"],
        "sample_count": len(dataset.get("samples", [])),
        "alias_count": len(dataset["component_aliases"]),
    }, ensure_ascii=False, indent=2))
    print(f"[ok] wrote {args.output}")


if __name__ == "__main__":
    main()
