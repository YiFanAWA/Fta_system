"""Build the sixth causal-relation expert review batch after v1-v5 coverage."""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Mapping

from build_siemens_s210_causal_relation_review_bundle import _candidate, _load, build_checklist


DEFAULT_SOURCE = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _reviewed_node_ids(candidate_bundles: list[Mapping[str, Any]]) -> set[str]:
    return {
        _clean(candidate.get("source_node", {}).get("node_id"))
        for bundle in candidate_bundles
        for candidate in bundle.get("candidates", [])
        if _clean(candidate.get("source_node", {}).get("node_id"))
    }


def _remaining_candidates(
    source: Mapping[str, Any], reviewed_node_ids: set[str]
) -> list[dict[str, Any]]:
    remaining: list[dict[str, Any]] = []
    ordinal = 1
    for row in source["samples"]:
        record = (row.get("gold_records") or [{}])[0]
        for cause_index in range(len(record.get("causes") or [])):
            candidate = _candidate(row, cause_index, ordinal)
            if candidate is None or candidate["source_node"]["node_id"] in reviewed_node_ids:
                continue
            candidate["candidate_id"] = f"CR-CAND-V6-{ordinal:03d}"
            candidate["selection_reason"] = (
                "sixth_batch_unreviewed_causes_round_robin_by_fault_code"
            )
            remaining.append(candidate)
            ordinal += 1
    return remaining


def _select_diverse(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for candidate in candidates:
        grouped.setdefault(candidate["target_node"]["fault_code"], []).append(candidate)
    selected: list[dict[str, Any]] = []
    round_index = 0
    while len(selected) < min(limit, len(candidates)):
        added_this_round = False
        for group in grouped.values():
            if round_index < len(group):
                selected.append(group[round_index])
                added_this_round = True
                if len(selected) >= limit:
                    break
        if not added_this_round:
            break
        round_index += 1
    return selected


def build_bundle(
    source: Mapping[str, Any],
    candidate_bundles: list[Mapping[str, Any]],
    limit: int,
    reviewer: str,
) -> dict[str, Any]:
    reviewed_node_ids = _reviewed_node_ids(candidate_bundles)
    remaining = _remaining_candidates(source, reviewed_node_ids)
    selected = _select_diverse(remaining, limit)
    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_candidates",
            "version": "v6",
            "status": "pending_expert_review",
            "review_type": "causal_relation_candidate_bundle",
            "source_dataset": source.get("dataset_info", {}).get("name"),
            "source_dataset_version": source.get("dataset_info", {}).get("version"),
            "source_record_count": len(source["samples"]),
            "source_causal_gold": "siemens_s210_causal_relation_gold_v6.json",
            "source_candidate_bundles": [
                "siemens_s210_causal_relation_candidates_v1.json",
                "siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json",
                "siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json",
                "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json",
            ],
            "reviewed_candidate_count": len(reviewed_node_ids),
            "remaining_unreviewed_candidate_count": len(remaining),
            "candidate_count": len(selected),
            "target_fault_count": len({item["target_node"]["fault_code"] for item in selected}),
            "selection_policy": (
                "Exclude every cause node already present in candidate batches v1-v5, then "
                "select unreviewed causes round-robin by fault code to expand target-fault coverage."
            ),
            "expected_reviewer": reviewer,
            "gold_source": "pending_named_expert_review",
            "training_eligible": False,
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
        },
        "candidates": selected,
    }


def build_v6_checklist(bundle: Mapping[str, Any]) -> str:
    text = build_checklist(bundle)
    text = text.replace(
        "# Siemens S210 因果关系候选专家审核清单 v1",
        "# Siemens S210 因果关系候选专家审核清单 v6",
        1,
    )
    text = text.replace(
        "候选关系由现有 Gold 的 `causes` 字段和原文证据生成；",
        "本批从 v1-v5 已审核候选之外的原因中生成，并保留现有 Gold 的原文证据；",
        1,
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--candidate-v1", required=True)
    parser.add_argument("--candidate-v2", required=True)
    parser.add_argument("--candidate-v3", required=True)
    parser.add_argument("--candidate-v4", required=True)
    parser.add_argument("--candidate-v5", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()

    source = _load(Path(args.source))
    candidate_bundles = [
        json.loads(Path(path).read_text(encoding="utf-8"))
        for path in (
            args.candidate_v1,
            args.candidate_v2,
            args.candidate_v3,
            args.candidate_v4,
            args.candidate_v5,
        )
    ]
    bundle = build_bundle(source, candidate_bundles, args.limit, args.reviewer)
    output = Path(args.output)
    checklist = Path(args.checklist)
    output.parent.mkdir(parents=True, exist_ok=True)
    checklist.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist.write_text(build_v6_checklist(bundle), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "checklist": str(checklist),
                "candidate_count": len(bundle["candidates"]),
                "remaining_unreviewed_candidate_count": bundle["dataset_info"][
                    "remaining_unreviewed_candidate_count"
                ],
                "target_fault_count": bundle["dataset_info"]["target_fault_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
