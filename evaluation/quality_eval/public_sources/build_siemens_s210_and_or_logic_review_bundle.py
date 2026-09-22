"""Build an expert review bundle for AND/OR gate decisions."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build(causal_gold: Mapping[str, Any], reviewer: str) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for relation in causal_gold.get("relations", []):
        grouped[relation["target_node"]["fault_code"]].append(relation)
    groups = {code: rels for code, rels in grouped.items() if len(rels) >= 2}
    events = []
    for ordinal, (fault_code, relations) in enumerate(sorted(groups.items()), start=1):
        target = relations[0]["target_node"]
        children = []
        for relation in relations:
            children.append(
                {
                    "relation_id": relation["relation_id"],
                    "source_node": relation["source_node"],
                    "relation_type": relation["relation_type"],
                    "direction": relation["direction"],
                    "evidence": relation["evidence"],
                }
            )
        events.append(
            {
                "logic_candidate_id": f"S210-LOGIC-CAND-{ordinal:03d}",
                "event_node": target,
                "children": children,
                "proposed_logic_gate": "unknown",
                "expert_review": {
                    "status": "pending_expert_review",
                    "child_set_complete": "pending",
                    "logic_gate": "pending",
                    "evidence_support": "pending",
                    "overall_decision": "pending",
                    "reviewer": None,
                    "reviewed_at": None,
                    "expert_reason": "",
                },
            }
        )
    return {
        "dataset_info": {
            "name": "siemens_s210_and_or_logic_candidates",
            "version": "v1",
            "status": "pending_expert_review",
            "review_type": "and_or_logic_candidate_bundle",
            "source_causal_gold": "siemens_s210_causal_relation_gold_v2.json",
            "source_relation_count": len(causal_gold.get("relations", [])),
            "event_count": len(events),
            "expected_reviewer": reviewer,
            "training_eligible": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
            "allowed_logic_gates": ["AND", "OR", "unknown", "not_applicable"],
        },
        "events": events,
    }


def checklist(bundle: Mapping[str, Any]) -> str:
    lines = [
        "# Siemens S210 AND OR 逻辑门专家审核清单 v1",
        "",
        "> 本清单只审核同一故障下多个已确认因果子节点之间的逻辑关系。不能因为存在多个原因就自动判定为 OR，也不能因为多个条件同时出现在原文中就自动判定为 AND。",
        "",
        "## 审核规则",
        "",
        "1. 先确认子原因集合是否完整：`complete`、`incomplete` 或 `unknown`。",
        "2. 只有原文或领域规则明确支持多个子原因任一成立即可触发故障时，才标记 `OR`。",
        "3. 只有原文或领域规则明确支持多个条件必须同时成立时，才标记 `AND`。",
        "4. 证据不足时标记 `unknown`，不得为了生成树而猜测。",
        "5. `overall_decision=approve` 仅允许在子原因集合、证据和逻辑门都可接受时使用。",
        "",
        "## 可填写枚举",
        "",
        "| 字段 | 可填写值 |",
        "|---|---|",
        "| `child_set_complete` | `complete` / `incomplete` / `unknown` |",
        "| `logic_gate` | `AND` / `OR` / `unknown` / `not_applicable` |",
        "| `evidence_support` | `supported` / `partial` / `unsupported` |",
        "| `overall_decision` | `approve` / `revise` / `reject` / `cannot_determine` |",
        "",
    ]
    for event in bundle["events"]:
        target = event["event_node"]
        lines.extend(
            [
                f"## {event['logic_candidate_id']} · {target['fault_code']}",
                "",
                f"- 目标故障：{target['fault_code']} · {target['description']}",
                f"- 系统预设：`unknown`（不代表结论）",
                "",
                "### 候选子原因",
                "",
            ]
        )
        for index, child in enumerate(event["children"], start=1):
            lines.append(f"{index}. `{child['relation_id']}`：{child['source_node']['text']}")
            for evidence in child["evidence"]:
                lines.append(f"   - 证据：`{evidence['citation_id']}`，{evidence['quote'].replace(chr(10), ' ')}")
        lines.extend(
            [
                "",
                "### 专家填写",
                "",
                "- child_set_complete：",
                "- logic_gate：",
                "- evidence_support：",
                "- overall_decision：",
                "- 审核意见：",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--causal-gold", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()
    gold = load(Path(args.causal_gold))
    bundle = build(gold, args.reviewer)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist_path = Path(args.checklist)
    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_path.write_text(checklist(bundle), encoding="utf-8")
    print(json.dumps({"output": str(output), "checklist": str(checklist_path), "event_count": len(bundle['events'])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
