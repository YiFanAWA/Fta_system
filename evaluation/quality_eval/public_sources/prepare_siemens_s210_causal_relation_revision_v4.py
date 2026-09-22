"""Prepare a single expert revision package for the v4 revise candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CANDIDATE_BUNDLE = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json"
)
DEFAULT_CANDIDATE_ID = "CR-CAND-V4-029"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_revision_package(
    bundle: Mapping[str, Any], candidate_id: str, reviewer: str
) -> dict[str, Any]:
    candidates = [
        candidate
        for candidate in bundle.get("candidates", [])
        if _clean(candidate.get("candidate_id")) == candidate_id
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one candidate for {candidate_id}, got {len(candidates)}")

    candidate = json.loads(json.dumps(candidates[0], ensure_ascii=False))
    source_context = candidate.get("source_context") or {}
    evidence = candidate.get("evidence") or []
    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_revision",
            "version": "v4-a01730",
            "status": "pending_expert_revision",
            "review_type": "causal_relation_revision",
            "source_candidate_bundle": "siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json",
            "candidate_count": 1,
            "expected_reviewer": reviewer,
            "expert_validated": False,
            "training_eligible": False,
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
        },
        "revision_request": {
            "candidate_id": candidate_id,
            "fault_code": candidate["target_node"]["fault_code"],
            "reason": (
                "原候选原因只摘录了 message value 的短语，未完整表达 Cause 段落中的因果语义。"
            ),
            "suggested_normalized_cause": "PROFIsafe transferred reference block is negative",
            "expert_must_confirm_or_replace": True,
        },
        "revisions": [
            {
                "candidate_id": candidate_id,
                "original_candidate": candidate,
                "evidence_check": {
                    "source_text_contains_original_quote": all(
                        _clean(item.get("quote")) in _clean(source_context.get("input_text"))
                        for item in evidence
                    ),
                    "evidence_count": len(evidence),
                },
                "expert_review": {
                    "status": "pending_expert_review",
                    "causal_status": "pending",
                    "direction": "pending",
                    "relation_type": "pending",
                    "fta_eligible": "pending",
                    "overall_decision": "pending",
                    "final_cause_text": "",
                    "reviewer": None,
                    "reviewed_at": None,
                    "expert_reason": "",
                },
            }
        ],
    }


def build_checklist(package: Mapping[str, Any]) -> str:
    request = package["revision_request"]
    revision = package["revisions"][0]
    candidate = revision["original_candidate"]
    target = candidate["target_node"]
    source = candidate["source_context"]
    evidence_lines = "\n".join(
        f'- `{item.get("evidence_id")}`："{item.get("quote")}"，字符位置 {item.get("start")}–{item.get("end")}'
        for item in candidate.get("evidence", [])
    )
    return f'''# Siemens S210 因果关系修订确认单 v4-A01730

## 使用说明

本单仅用于复核第四批审核中的 1 条 `revise` 候选，不是预填 Gold。请专家根据完整原文和证据独立确认；专家确认前不得将该候选写入正式因果 Gold 或 FTA。

- 审核专家：{package["dataset_info"]["expected_reviewer"]}
- 故障码：`{request["fault_code"]}`
- 候选编号：`{request["candidate_id"]}`
- 当前状态：`pending_expert_revision`

## 原始候选

- 目标故障：`{target["fault_code"]}` — {target["description"]}
- 原候选原因：`{candidate["source_node"]["text"]}`
- 原关系：`causes` / `source_to_target`
- 原 FTA 资格：`{candidate["proposed_relation"].get("status")}`（尚未获得专家确认）

## 原文与证据

证据引用：
{evidence_lines}

原文：

```text
{source.get("input_text", "")}
```

## 修订提示

专家上一轮意见指出：原候选原因未完整表达 Cause 段落的语义。建议核对下列规范化表达，但不得视为预先批准：

> `{request["suggested_normalized_cause"]}`

请确认该表达是否准确；如不准确，请填写专家认可的最终原因文本。

## 专家填写

- `causal_status`：`causal` / `associated_only` / `unsupported` / `cannot_determine`
- `direction`：`source_to_target` / `target_to_source` / `undirected` / `unknown`
- `relation_type`：`causes` / `associated_with` / `shared_parameter` / `paired_fault_message` / `unknown`
- `fta_eligible`：`true` / `false`
- `overall_decision`：`approve` / `revise` / `reject`
- `final_cause_text`：
- `expert_reason`：
- `reviewer`：
- `reviewed_at`：

## 入库门禁

只有同时满足以下条件，才可以进入下一版 Gold：

1. `overall_decision=approve`；
2. `causal_status=causal`；
3. `direction=source_to_target`；
4. `relation_type=causes`；
5. `fta_eligible=true`；
6. 最终原因文本和证据语义一致。
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-bundle", default=str(DEFAULT_CANDIDATE_BUNDLE))
    parser.add_argument("--candidate-id", default=DEFAULT_CANDIDATE_ID)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()

    package = build_revision_package(
        _load(Path(args.candidate_bundle)), args.candidate_id, args.reviewer
    )
    output = Path(args.output)
    checklist = Path(args.checklist)
    output.parent.mkdir(parents=True, exist_ok=True)
    checklist.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist.write_text(build_checklist(package), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "checklist": str(checklist),
                "candidate_id": args.candidate_id,
                "status": package["dataset_info"]["status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
