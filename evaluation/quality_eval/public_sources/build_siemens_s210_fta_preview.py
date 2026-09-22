"""Build a provenance-preserving, non-production FTA preview from expert Gold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_preview(logic_gold: Mapping[str, Any]) -> dict[str, Any]:
    preview_trees: list[dict[str, Any]] = []
    excluded_events: list[dict[str, Any]] = []
    for event in logic_gold.get("events", []):
        review = event.get("expert_review", {})
        gate = event.get("logic_gate")
        if review.get("overall_decision") == "approve" and gate in {"AND", "OR"}:
            preview_trees.append(
                {
                    "preview_tree_id": f"S210-FTA-PREVIEW-{len(preview_trees) + 1:03d}",
                    "top_event": event["event_node"],
                    "gate": gate,
                    "gate_provenance": {
                        "logic_candidate_id": event["logic_candidate_id"],
                        "review_status": review.get("status"),
                        "reviewer": review.get("reviewer"),
                        "reviewed_at": review.get("reviewed_at"),
                        "evidence_support": review.get("evidence_support"),
                    },
                    "children": [
                        {
                            "relation_id": child["relation_id"],
                            "node": child["source_node"],
                            "relation_type": child["relation_type"],
                            "direction": child["direction"],
                            "evidence": child["evidence"],
                        }
                        for child in event.get("children", [])
                    ],
                    "status": "preview_only",
                }
            )
        else:
            excluded_events.append(
                {
                    "logic_candidate_id": event.get("logic_candidate_id"),
                    "fault_code": event.get("event_node", {}).get("fault_code"),
                    "logic_gate": gate,
                    "overall_decision": review.get("overall_decision"),
                    "reason": "logic gate is unknown or event is not approved",
                }
            )

    return {
        "dataset_info": {
            "name": "siemens_s210_fta_preview",
            "version": "v1",
            "status": "preview_only",
            "source_logic_gold": "siemens_s210_and_or_logic_gold_v1.json",
            "tree_count": len(preview_trees),
            "excluded_event_count": len(excluded_events),
            "production_ready": False,
            "fta_ready": False,
            "evidence_required": True,
            "automatic_causal_inference": False,
            "note": (
                "This preview contains only expert-approved logic events. It is not a complete FTA "
                "for all 281 faults and must not be written to the production tree registry."
            ),
        },
        "trees": preview_trees,
        "excluded_events": excluded_events,
    }


def render_markdown(preview: Mapping[str, Any]) -> str:
    lines = [
        "# Siemens S210 FTA Preview v1",
        "",
        "> 这是带证据的受限范围预览，不是生产 FTA，也不是 281 条故障的完整故障树。",
        "",
        f"- 预览树数量：{preview['dataset_info']['tree_count']}",
        f"- 排除事件数量：{preview['dataset_info']['excluded_event_count']}",
        "- 生产可用：否",
        "- 因果自动推断：否",
        "",
    ]
    for tree in preview["trees"]:
        top = tree["top_event"]
        lines.extend(
            [
                f"## {tree['preview_tree_id']} · {top['fault_code']}",
                "",
                f"- 目标故障：{top['description']}",
                f"- 逻辑门：`{tree['gate']}`",
                f"- 逻辑审核来源：`{tree['gate_provenance']['logic_candidate_id']}`",
                "",
                "### 子原因和证据",
                "",
            ]
        )
        for index, child in enumerate(tree["children"], start=1):
            lines.append(f"{index}. `{child['relation_id']}`：{child['node']['text']}")
            for evidence in child["evidence"]:
                lines.append(
                    f"   - 证据 `{evidence['citation_id']}`：{evidence['quote'].replace(chr(10), ' ')}"
                )
        lines.extend(["", "---", ""])

    if preview["excluded_events"]:
        lines.extend(["## 未纳入预览的事件", ""])
        for event in preview["excluded_events"]:
            lines.append(
                f"- `{event['fault_code']}`：logic_gate=`{event['logic_gate']}`，"
                f"decision=`{event['overall_decision']}`；{event['reason']}"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logic-gold", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    preview = build_preview(load(Path(args.logic_gold)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = Path(args.markdown)
    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(render_markdown(preview), encoding="utf-8")
    print(json.dumps({"output": str(output), "markdown": str(markdown), "trees": len(preview["trees"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
