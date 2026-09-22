"""Validate the pending S210 causal-relation candidate contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


CAUSAL_STATUS = {"causal", "associated_only", "unsupported", "cannot_determine"}
DIRECTIONS = {"source_to_target", "target_to_source", "undirected", "unknown"}


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("candidate bundle must be an object")
    return payload


def _clean(value: Any) -> str:
    return str(value or "").strip()


def validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    info = payload.get("dataset_info")
    candidates = payload.get("candidates")
    if not isinstance(info, Mapping):
        return ["dataset_info must be an object"]
    if info.get("status") != "pending_expert_review":
        errors.append("dataset_info.status must be pending_expert_review")
    if info.get("not_expert_gold") is not True:
        errors.append("dataset_info.not_expert_gold must remain true")
    if info.get("causal_relations_complete") is not False:
        errors.append("causal_relations_complete must remain false")
    if info.get("logic_gates_complete") is not False:
        errors.append("logic_gates_complete must remain false")
    if info.get("fta_ready") is not False:
        errors.append("fta_ready must remain false")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
        return errors

    ids: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = _clean(candidate.get("candidate_id"))
        if not candidate_id or candidate_id in ids:
            errors.append(f"{prefix}.candidate_id must be unique and non-empty")
        ids.add(candidate_id)
        source = candidate.get("source_node")
        target = candidate.get("target_node")
        if not isinstance(source, Mapping) or not _clean(source.get("text")):
            errors.append(f"{prefix}.source_node.text is required")
        if not isinstance(target, Mapping) or not _clean(target.get("fault_code")):
            errors.append(f"{prefix}.target_node.fault_code is required")
        proposal = candidate.get("proposed_relation")
        if not isinstance(proposal, Mapping) or proposal.get("status") != "proposed_not_confirmed":
            errors.append(f"{prefix}.proposed_relation must remain proposed_not_confirmed")
        evidence = candidate.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be non-empty")
        else:
            context = (candidate.get("source_context") or {}).get("input_text", "")
            for evidence_index, item in enumerate(evidence, start=1):
                ep = f"{prefix}.evidence[{evidence_index}]"
                if not isinstance(item, Mapping):
                    errors.append(f"{ep} must be an object")
                    continue
                quote = _clean(item.get("quote"))
                start, end = item.get("start"), item.get("end")
                if not quote or not isinstance(start, int) or not isinstance(end, int):
                    errors.append(f"{ep} requires quote/start/end")
                elif isinstance(context, str) and context[start:end] != quote:
                    errors.append(f"{ep} quote does not match source_context.input_text offsets")
        review = candidate.get("expert_review")
        if not isinstance(review, Mapping):
            errors.append(f"{prefix}.expert_review must be an object")
            continue
        for field in ("causal_status", "direction", "relation_type", "fta_eligible", "overall_decision"):
            if review.get(field) != "pending":
                errors.append(f"{prefix}.expert_review.{field} must remain pending")
        if review.get("status") != "pending_expert_review":
            errors.append(f"{prefix}.expert_review.status must be pending_expert_review")
        if review.get("reviewer") is not None or review.get("reviewed_at") is not None:
            errors.append(f"{prefix}.expert_review reviewer fields must remain empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = load(Path(args.input))
    errors = validate(payload)
    report = {
        "status": "candidate_bundle_validated" if not errors else "not_ready",
        "expert_validated": False,
        "candidate_count": len(payload.get("candidates", [])),
        "causal_relations_complete": False,
        "logic_gates_complete": False,
        "fta_ready": False,
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
