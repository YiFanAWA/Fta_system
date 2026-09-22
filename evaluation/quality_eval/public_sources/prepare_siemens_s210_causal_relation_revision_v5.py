"""Prepare expert revision packages for v5 revise candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CANDIDATE_BUNDLE = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json"
)

REVISION_HINTS = {
    "CR-CAND-V5-007": {
        "suggested_cause_text": "PN clock cycle is less than 4× the current controller clock cycle",
        "suggested_evidence_action": "保留原 Cause 证据，并确认该规范要求应规范化为实际违规条件。",
    },
    "CR-CAND-V5-021": {
        "suggested_cause_text": (
            "The brake is not configured in configured p10202. "
            "There is a brake test configuration error."
        ),
        "suggested_evidence_action": (
            "将证据改指向完整原文 Bit 2，而不是当前 Bit 0 的 resetting the brake test selection。"
        ),
    },
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_candidate(bundle: Mapping[str, Any], candidate_id: str) -> Mapping[str, Any]:
    matches = [
        candidate
        for candidate in bundle.get("candidates", [])
        if _clean(candidate.get("candidate_id")) == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one candidate for {candidate_id}, got {len(matches)}")
    return matches[0]


def _find_review(review: Mapping[str, Any], candidate_id: str) -> Mapping[str, Any]:
    matches = [
        record for record in review.get("records", []) if record.get("candidate_id") == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one review record for {candidate_id}, got {len(matches)}")
    return matches[0]


def _suggested_bit2_evidence(candidate: Mapping[str, Any]) -> dict[str, Any] | None:
    source_text = _clean(candidate.get("source_context", {}).get("input_text"))
    marker = source_text.find("Bit 2:")
    if marker < 0:
        return None
    end_marker = source_text.find("Note:", marker)
    if end_marker < 0:
        end_marker = len(source_text)
    quote = source_text[marker + len("Bit 2:") : end_marker].strip()
    start = source_text.find(quote, marker + len("Bit 2:"))
    if start < 0:
        return None
    return {
        "source_id": "input_text",
        "field": "cause",
        "quote": quote,
        "start": start,
        "end": start + len(quote),
    }


def build_revision_package(
    bundle: Mapping[str, Any], review: Mapping[str, Any], reviewer: str
) -> dict[str, Any]:
    revisions = []
    for candidate_id, hint in REVISION_HINTS.items():
        candidate = _find_candidate(bundle, candidate_id)
        expert_record = _find_review(review, candidate_id)
        revision = {
            "candidate_id": candidate_id,
            "fault_code": candidate["target_node"]["fault_code"],
            "original_candidate": candidate,
            "previous_expert_review": expert_record,
            "revision_request": {
                "suggested_cause_text": hint["suggested_cause_text"],
                "suggested_evidence_action": hint["suggested_evidence_action"],
                "expert_must_confirm_or_replace": True,
            },
            "suggested_evidence": (
                _suggested_bit2_evidence(candidate) if candidate_id == "CR-CAND-V5-021" else None
            ),
            "expert_review": {
                "status": "pending_expert_review",
                "causal_status": "pending",
                "direction": "pending",
                "relation_type": "pending",
                "fta_eligible": "pending",
                "overall_decision": "pending",
                "final_cause_text": "",
                "evidence_reference": "",
                "evidence_text": "",
                "evidence_start": None,
                "evidence_end": None,
                "reviewer": None,
                "reviewed_at": None,
                "expert_reason": "",
            },
        }
        revisions.append(revision)
    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_revision",
            "version": "v5",
            "status": "pending_expert_revision",
            "review_type": "causal_relation_revision",
            "source_candidate_bundle": "siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json",
            "candidate_count": len(revisions),
            "expected_reviewer": reviewer,
            "expert_validated": False,
            "training_eligible": False,
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
        },
        "revisions": revisions,
    }


def build_checklist(package: Mapping[str, Any]) -> str:
    lines = [
        "# Siemens S210 因果关系修订确认清单 v5",
        "",
        "本清单只处理第五批审核中的 2 条 `revise` 候选。建议文本和建议证据不是预填 Gold，必须由刘武专家重新确认。",
        "",
        f"- 审核专家：{package['dataset_info']['expected_reviewer']}",
        "- 当前状态：`pending_expert_revision`",
        "- 通过门禁：`approve` + `causal` + `source_to_target` + `causes` + `fta_eligible=true`",
        "",
    ]
    for index, revision in enumerate(package["revisions"], start=1):
        candidate = revision["original_candidate"]
        request = revision["revision_request"]
        previous = revision["previous_expert_review"]
        lines.extend(
            [
                f"## {index}. {revision['fault_code']} / {revision['candidate_id']}",
                "",
                f"- 故障描述：{candidate['target_node']['description']}",
                f"- 原候选原因：`{candidate['source_node']['text']}`",
                f"- 当前专家结论：`{previous['overall_decision']}`",
                f"- 专家意见：{previous.get('review_comment', '')}",
                f"- 建议规范化原因：`{request['suggested_cause_text']}`",
                f"- 建议证据处理：{request['suggested_evidence_action']}",
                "",
                "### 原文",
                "",
                "```text",
                candidate["source_context"]["input_text"],
                "```",
                "",
                "### 专家重新填写",
                "",
                "- `causal_status`：",
                "- `direction`：",
                "- `relation_type`：",
                "- `fta_eligible`：",
                "- `overall_decision`：",
                "- `final_cause_text`：",
                "- `evidence_reference`：",
                "- `evidence_text`：",
                "- `evidence_start/end`：",
                "- `expert_reason`：",
                "- `reviewer/reviewed_at`：",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-bundle", default=str(DEFAULT_CANDIDATE_BUNDLE))
    parser.add_argument("--review-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()
    package = build_revision_package(
        _load(Path(args.candidate_bundle)), _load(Path(args.review_json)), args.reviewer
    )
    output = Path(args.output)
    checklist = Path(args.checklist)
    output.parent.mkdir(parents=True, exist_ok=True)
    checklist.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist.write_text(build_checklist(package), encoding="utf-8")
    print(json.dumps({"output": str(output), "checklist": str(checklist), "candidate_count": 2}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
