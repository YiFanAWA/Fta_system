"""Build the second causal-review batch for additional causes of approved faults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from build_siemens_s210_causal_relation_review_bundle import _candidate, _load, build_checklist


DEFAULT_SOURCE = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
)
DEFAULT_GOLD = Path(
    "evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v1.json"
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def build_remaining_bundle(
    source: Mapping[str, Any], causal_gold: Mapping[str, Any], reviewer: str
) -> dict[str, Any]:
    approved_codes = {
        _clean(relation.get("target_node", {}).get("fault_code")).upper()
        for relation in causal_gold.get("relations", [])
    }
    candidates: list[dict[str, Any]] = []
    ordinal = 1
    target_record_count = 0
    for row in source["samples"]:
        record = (row.get("gold_records") or [{}])[0]
        fault_code = _clean(record.get("fault_code")).upper()
        causes = record.get("causes") or []
        if fault_code not in approved_codes or len(causes) <= 1:
            continue
        target_record_count += 1
        for cause_index in range(1, len(causes)):
            candidate = _candidate(row, cause_index, ordinal)
            if candidate is None:
                continue
            candidate["candidate_id"] = f"CR-CAND-V2-{ordinal:03d}"
            candidate["selection_reason"] = (
                "second_batch_remaining_causes_for_faults_with_expert_approved_causal_edge"
            )
            candidates.append(candidate)
            ordinal += 1

    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_candidates",
            "version": "v2",
            "status": "pending_expert_review",
            "review_type": "causal_relation_candidate_bundle",
            "source_dataset": source.get("dataset_info", {}).get("name"),
            "source_dataset_version": source.get("dataset_info", {}).get("version"),
            "source_causal_gold": "siemens_s210_causal_relation_gold_v1.json",
            "source_record_count": len(source["samples"]),
            "target_fault_count": len(approved_codes),
            "multi_cause_target_fault_count": target_record_count,
            "candidate_count": len(candidates),
            "selection_policy": (
                "All remaining extracted causes (cause index >= 1) for target faults that "
                "already have one expert-approved causal relation. This batch is required "
                "before judging AND/OR and does not pre-approve any edge."
            ),
            "expected_reviewer": reviewer,
            "gold_source": "pending_named_expert_review",
            "training_eligible": False,
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
        },
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--causal-gold", default=str(DEFAULT_GOLD))
    parser.add_argument("--output", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()

    source = _load(Path(args.source))
    causal_gold = json.loads(Path(args.causal_gold).read_text(encoding="utf-8"))
    bundle = build_remaining_bundle(source, causal_gold, args.reviewer)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist_text = build_checklist(bundle).replace(
        "# Siemens S210 因果关系候选专家审核清单 v1",
        "# Siemens S210 因果关系候选专家审核清单 v2",
        1,
    )
    checklist_text = checklist_text.replace(
        "这是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。",
        "这是第二批因果关系候选审核包，不是专家金标，也不是可直接建树的数据。",
        1,
    )
    checklist = Path(args.checklist)
    checklist.parent.mkdir(parents=True, exist_ok=True)
    checklist.write_text(checklist_text, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "checklist": str(checklist),
                "candidate_count": len(bundle["candidates"]),
                "multi_cause_target_fault_count": bundle["dataset_info"][
                    "multi_cause_target_fault_count"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
