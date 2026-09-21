#!/usr/bin/env python3
"""Project reviewed related-component labels onto the explicit-relation policy."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


_RELATION_RE = re.compile(
    r"(?:associated\s+with|related\s+to|connected\s+(?:to|with)|linked\s+to|"
    r"关联(?:组件)?|连接(?:到|至)?|相连|相关组件(?:为|：)?)",
    re.IGNORECASE,
)

# The imported S210 expert values contain some bilingual text with legacy
# encoding artifacts. These stable English terms let the projection verify
# the relation against the original source without rewriting the expert value.
_KNOWN_COMPONENT_TERMS = (
    "control unit",
    "internal braking resistor",
    "encoder",
    "motor",
    "power unit",
    "dc link",
)


def _has_explicit_relation(source_text: str, raw_component: str) -> bool:
    source = source_text.casefold()
    component = raw_component.casefold()
    aliases = [term for term in _KNOWN_COMPONENT_TERMS if term in component]
    if not aliases:
        aliases = [component] if component and component in source else []
    if not aliases:
        return False

    clauses = re.split(r"[\n\r。！？!?；;]+", source_text)
    for clause in clauses:
        if not _RELATION_RE.search(clause):
            continue
        if any(alias in clause.casefold() for alias in aliases):
            return True
    return False


def project(payload: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(payload)
    changed: list[dict[str, Any]] = []
    for sample in projected.get("samples", []):
        source_text = str(sample.get("input_text", ""))
        for record in sample.get("gold_records", []):
            original = list(record.get("related_components") or [])
            filtered = [
                value
                for value in original
                if _has_explicit_relation(source_text, str(value))
            ]
            if filtered == original:
                continue
            record["related_components_original_v1"] = original
            record["related_components"] = filtered
            changed.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "fault_code": record.get("fault_code"),
                    "original": original,
                    "projected": filtered,
                    "reason": "普通正文提及不算关联组件；仅保留明确关系表达",
                }
            )

    dataset_info = projected.setdefault("dataset_info", {})
    dataset_info["version"] = "v2-related-component-policy"
    dataset_info["label_status"] = "expert_reviewed_with_policy_projection"
    projected["related_component_policy_projection"] = {
        "policy": "explicit_relation_only",
        "source_version": "v1",
        "preserves_original_values": True,
        "changed_record_count": len(changed),
        "changes": changed,
    }
    return projected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
        raise ValueError("input gold must contain a samples list")
    result = project(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "changed_record_count": result["related_component_policy_projection"][
                    "changed_record_count"
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
