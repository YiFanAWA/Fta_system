"""Validate the expert-reviewed pilot Causal Relation Gold contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("relations"), list):
        raise ValueError("causal Relation Gold must contain relations")
    return payload


def _clean(value: Any) -> str:
    return str(value or "").strip()


def validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info")
    if not isinstance(info, Mapping):
        return ["dataset_info must be an object"]
    expected = {
        "status": "expert_validated",
        "gold_source": "named_expert_review",
        "relation_scope": "causal_only",
    }
    for field, value in expected.items():
        if info.get(field) != value:
            errors.append(f"dataset_info.{field} must be {value}")
    for field in ("causal_relations_complete", "logic_gates_complete", "fta_ready", "runtime_registry_updated"):
        if info.get(field) is not False:
            errors.append(f"dataset_info.{field} must remain false for pilot Gold")
    if not _clean(info.get("reviewer")) or not _clean(info.get("reviewed_at")):
        errors.append("dataset_info reviewer and reviewed_at are required")
    relations = payload.get("relations")
    if not relations:
        errors.append("relations must be non-empty")
        return errors
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations, start=1):
        prefix = f"relations[{index}]"
        if not isinstance(relation, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        relation_id = _clean(relation.get("relation_id"))
        if not relation_id or relation_id in relation_ids:
            errors.append(f"{prefix}.relation_id must be unique and non-empty")
        relation_ids.add(relation_id)
        source = relation.get("source_node")
        target = relation.get("target_node")
        if not isinstance(source, Mapping) or not _clean(source.get("node_id")):
            errors.append(f"{prefix}.source_node.node_id is required")
        if not isinstance(target, Mapping) or not _clean(target.get("node_id")):
            errors.append(f"{prefix}.target_node.node_id is required")
        if relation.get("relation_type") != "causes":
            errors.append(f"{prefix}.relation_type must be causes")
        if relation.get("direction") != "source_to_target":
            errors.append(f"{prefix}.direction must be source_to_target")
        evidence = relation.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be non-empty")
        review = relation.get("expert_review")
        if not isinstance(review, Mapping):
            errors.append(f"{prefix}.expert_review must be an object")
        else:
            if review.get("causal_status") != "causal":
                errors.append(f"{prefix}.expert_review.causal_status must be causal")
            if review.get("fta_eligible") is not True:
                errors.append(f"{prefix}.expert_review.fta_eligible must be true")
            if review.get("overall_decision") != "approve":
                errors.append(f"{prefix}.expert_review.overall_decision must be approve")
            if not _clean(review.get("reviewer")) or not _clean(review.get("reviewed_at")):
                errors.append(f"{prefix}.expert_review reviewer fields are required")
    excluded = payload.get("excluded_candidates")
    if not isinstance(excluded, list):
        errors.append("excluded_candidates must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = load(Path(args.input))
    errors = validate(payload)
    info = payload.get("dataset_info", {})
    report = {
        "status": "causal_relation_gold_validated" if not errors else "not_ready",
        "expert_validated": not errors,
        "relation_count": len(payload.get("relations", [])),
        "excluded_candidate_count": len(payload.get("excluded_candidates", [])),
        "causal_relations_complete": info.get("causal_relations_complete"),
        "logic_gates_complete": info.get("logic_gates_complete"),
        "fta_ready": info.get("fta_ready"),
        "summary_discrepancy_present": bool(info.get("summary_discrepancy")),
        "errors": errors,
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
