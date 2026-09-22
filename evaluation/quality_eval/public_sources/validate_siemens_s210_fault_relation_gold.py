"""Validate the expert-reviewed S210 association-relation Gold contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


ALLOWED_RELATION_TYPES = {"paired_fault_message", "shared_parameter"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("relations"), list):
        raise ValueError("relation Gold must be an object with relations")
    return value


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _relation_key(relation: Mapping[str, Any]) -> tuple[Any, ...]:
    endpoints = tuple(sorted(_clean(value).upper() for value in relation.get("endpoints", [])))
    evidence = tuple(
        sorted(
            (
                _clean(item.get("fault_code")).upper(),
                _clean(item.get("citation_id")),
                _clean(item.get("field")),
            )
            for item in relation.get("evidence", [])
            if isinstance(item, Mapping)
        )
    )
    return (
        endpoints,
        _clean(relation.get("relation_type")),
        tuple(sorted(_clean(value).casefold() for value in relation.get("query_triggers", []))),
        evidence,
    )


def validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info")
    if not isinstance(info, Mapping):
        return ["dataset_info must be an object"]
    if info.get("status") != "expert_validated":
        errors.append("dataset_info.status must be expert_validated")
    if info.get("gold_source") != "named_expert_review":
        errors.append("dataset_info.gold_source must be named_expert_review")
    if info.get("relation_scope") != "association_only":
        errors.append("dataset_info.relation_scope must be association_only")
    if info.get("causal_relations_complete") is not False:
        errors.append("causal_relations_complete must remain false in association Gold v1")
    if info.get("logic_gates_complete") is not False:
        errors.append("logic_gates_complete must remain false in association Gold v1")
    if not _clean(info.get("reviewer")):
        errors.append("dataset_info.reviewer is required")

    seen_ids: set[str] = set()
    relations = payload.get("relations")
    if not isinstance(relations, list) or not relations:
        errors.append("relations must be a non-empty list")
        return errors

    for index, relation in enumerate(relations, start=1):
        prefix = f"relations[{index}]"
        if not isinstance(relation, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        relation_id = _clean(relation.get("relation_id"))
        if not relation_id or relation_id in seen_ids:
            errors.append(f"{prefix}.relation_id must be unique and non-empty")
        seen_ids.add(relation_id)
        endpoints = relation.get("endpoints")
        endpoint_codes = tuple(_clean(value).upper() for value in endpoints) if isinstance(endpoints, list) else ()
        if len(endpoint_codes) != 2 or not all(endpoint_codes) or len(set(endpoint_codes)) != 2:
            errors.append(f"{prefix}.endpoints must contain two distinct fault codes")
        if relation.get("relation_type") not in ALLOWED_RELATION_TYPES:
            errors.append(f"{prefix}.relation_type is not allowed in association Gold v1")
        if relation.get("direction") != "undirected":
            errors.append(f"{prefix}.direction must be undirected")
        triggers = relation.get("query_triggers")
        if not isinstance(triggers, list) or not all(_clean(value) for value in triggers):
            errors.append(f"{prefix}.query_triggers must be a non-empty string list")
        evidence = relation.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be non-empty")
        else:
            for evidence_index, item in enumerate(evidence, start=1):
                evidence_prefix = f"{prefix}.evidence[{evidence_index}]"
                if not isinstance(item, Mapping):
                    errors.append(f"{evidence_prefix} must be an object")
                    continue
                code = _clean(item.get("fault_code")).upper()
                if code not in endpoint_codes:
                    errors.append(f"{evidence_prefix}.fault_code must be one of endpoints")
                if not _clean(item.get("citation_id")) or not _clean(item.get("field")):
                    errors.append(f"{evidence_prefix} requires citation_id and field")

        review = relation.get("expert_review")
        if not isinstance(review, Mapping):
            errors.append(f"{prefix}.expert_review must be an object")
            continue
        expected_review = {
            "relation_completeness": "complete",
            "relation_type_correctness": "correct",
            "relation_evidence_support": "supported",
            "unsupported_parameter_semantics": "no",
            "overall_decision": "pass",
        }
        for field, expected in expected_review.items():
            if review.get(field) != expected:
                errors.append(f"{prefix}.expert_review.{field} must be {expected}")
        if not _clean(review.get("reviewer")) or not _clean(review.get("reviewed_at")):
            errors.append(f"{prefix}.expert_review requires reviewer and reviewed_at")
    return errors


def compare_registry(gold: Mapping[str, Any], registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    gold_relations = {relation.get("relation_id"): relation for relation in gold.get("relations", [])}
    registry_relations = {relation.get("relation_id"): relation for relation in registry.get("relations", [])}
    if set(gold_relations) != set(registry_relations):
        errors.append("Gold and runtime registry relation IDs differ")
        return errors
    for relation_id, gold_relation in gold_relations.items():
        registry_relation = registry_relations[relation_id]
        if _relation_key(gold_relation) != _relation_key(
            {
                "endpoints": registry_relation.get("fault_codes"),
                "relation_type": registry_relation.get("relation_type"),
                "query_triggers": registry_relation.get("query_triggers"),
                "evidence": registry_relation.get("evidence"),
            }
        ):
            errors.append(f"Gold/runtime registry mismatch: {relation_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--registry")
    parser.add_argument("--output")
    args = parser.parse_args()

    gold = load(Path(args.gold))
    errors = validate(gold)
    if args.registry:
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        errors.extend(compare_registry(gold, registry))
    report = {
        "status": "relation_gold_validated" if not errors else "not_ready",
        "expert_validated": not errors,
        "relation_count": len(gold.get("relations", [])),
        "scope": gold.get("dataset_info", {}).get("relation_scope"),
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
