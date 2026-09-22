"""Validate the restricted, evidence-bound FTA preview contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info", {})
    trees = payload.get("trees", [])
    if info.get("status") != "preview_only":
        errors.append("dataset_info.status must be preview_only")
    if info.get("production_ready") is not False or info.get("fta_ready") is not False:
        errors.append("preview must not be marked production_ready or fta_ready")
    if info.get("automatic_causal_inference") is not False:
        errors.append("preview must not enable automatic causal inference")
    if info.get("tree_count") != len(trees):
        errors.append("tree_count does not match trees length")
    tree_ids = [tree.get("preview_tree_id") for tree in trees]
    if len(tree_ids) != len(set(tree_ids)):
        errors.append("preview_tree_id values must be unique")
    for tree in trees:
        tree_id = tree.get("preview_tree_id", "<missing>")
        if tree.get("status") != "preview_only":
            errors.append(f"{tree_id}: status must be preview_only")
        if tree.get("gate") not in {"AND", "OR"}:
            errors.append(f"{tree_id}: gate must be AND or OR")
        provenance = tree.get("gate_provenance", {})
        if provenance.get("review_status") != "expert_reviewed":
            errors.append(f"{tree_id}: gate is not expert reviewed")
        if provenance.get("evidence_support") != "supported":
            errors.append(f"{tree_id}: gate evidence is not supported")
        children = tree.get("children")
        if not isinstance(children, list) or not children:
            errors.append(f"{tree_id}: children must be non-empty")
            continue
        for child in children:
            if not child.get("relation_id") or not child.get("node", {}).get("text"):
                errors.append(f"{tree_id}: child node or relation_id is missing")
            evidence = child.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{tree_id}: child {child.get('relation_id')} has no evidence")
            for citation in evidence or []:
                if not citation.get("citation_id") or not citation.get("quote"):
                    errors.append(f"{tree_id}: child evidence is incomplete")
    if info.get("excluded_event_count") != len(payload.get("excluded_events", [])):
        errors.append("excluded_event_count does not match excluded_events length")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = load(Path(args.input))
    errors = validate(payload)
    report = {
        "status": "fta_preview_validated" if not errors else "validation_failed",
        "preview_only": payload.get("dataset_info", {}).get("status") == "preview_only",
        "tree_count": len(payload.get("trees", [])),
        "excluded_event_count": len(payload.get("excluded_events", [])),
        "production_ready": payload.get("dataset_info", {}).get("production_ready"),
        "fta_ready": payload.get("dataset_info", {}).get("fta_ready"),
        "errors": errors,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
