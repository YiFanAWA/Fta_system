"""Build a bounded, evidence-backed causal-relation review bundle.

The source Gold contains extracted ``causes`` and evidence spans, but that
does not prove a causal relation.  This builder deliberately emits pending
expert-review candidates only; it never promotes a cause to a confirmed FTA
edge.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_INPUT = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
)
DEFAULT_JSON = Path(
    "evaluation/quality_eval/datasets/"
    "siemens_s210_causal_relation_candidates_v1.json"
)
DEFAULT_CHECKLIST = Path(
    "evaluation/quality_eval/runs/"
    "siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md"
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
        raise ValueError("source Gold must contain a samples list")
    return payload


def _source_span(row: Mapping[str, Any], cause_index: int) -> dict[str, Any] | None:
    spans = [
        (index, item)
        for index, item in enumerate(row.get("evidence_spans", []))
        if isinstance(item, Mapping)
        and item.get("field") == "cause"
        and _clean(item.get("quote"))
    ]
    if not spans:
        return None

    indexed = [item for item in spans if item[1].get("value_index") == cause_index]
    selected_index, selected = (indexed[0] if indexed else spans[min(cause_index, len(spans) - 1)])
    return {
        "evidence_id": f"{row['sample_id']}:cause:{selected_index}",
        "source_id": _clean(selected.get("source_id")) or "input_text",
        "field": "cause",
        "quote": _clean(selected.get("quote")),
        "start": selected.get("start"),
        "end": selected.get("end"),
        "location": _clean(selected.get("location")),
        "source_span_index": selected_index,
    }


def _candidate(row: Mapping[str, Any], cause_index: int, ordinal: int) -> dict[str, Any] | None:
    record = (row.get("gold_records") or [{}])[0]
    causes = record.get("causes") or []
    if cause_index >= len(causes):
        return None
    evidence = _source_span(row, cause_index)
    if evidence is None:
        return None
    fault_code = _clean(record.get("fault_code")).upper()
    sample_id = _clean(row.get("sample_id"))
    candidate_id = f"CR-CAND-{ordinal:03d}"
    return {
        "candidate_id": candidate_id,
        "selection_reason": "pilot_batch_stratified_by_source_sequence_one_cause_per_fault",
        "source_record": {
            "sample_id": sample_id,
            "sequence": row.get("sequence"),
            "source_file": _clean(row.get("source_file")),
            "fault_code": fault_code,
            "description": _clean(record.get("description")),
        },
        "source_node": {
            "node_id": f"siemens_s210:cause:{sample_id}:{cause_index}",
            "node_type": "cause_candidate",
            "text": _clean(causes[cause_index]),
            "source_field": "causes",
        },
        "target_node": {
            "node_id": f"siemens_s210:fault:{fault_code}",
            "node_type": "fault_entity",
            "fault_code": fault_code,
            "description": _clean(record.get("description")),
        },
        "proposed_relation": {
            "relation_type": "causes",
            "direction": "source_to_target",
            "status": "proposed_not_confirmed",
        },
        "evidence": [evidence],
        "source_context": {
            "input_text": _clean(row.get("input_text")),
            "source_record_evidence_policy": (
                "The quoted span is extracted from the current Gold cause evidence; "
                "the complete source record is included for expert context."
            ),
        },
        "expert_review": {
            "status": "pending_expert_review",
            "causal_status": "pending",
            "direction": "pending",
            "relation_type": "pending",
            "fta_eligible": "pending",
            "overall_decision": "pending",
            "reviewer": None,
            "reviewed_at": None,
            "expert_reason": "",
            "modified_relation": None,
        },
    }


def select_rows(rows: list[Mapping[str, Any]], limit: int) -> list[Mapping[str, Any]]:
    eligible = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and (row.get("gold_records") or [{}])[0].get("causes")
        and any(
            isinstance(span, Mapping)
            and span.get("field") == "cause"
            and _clean(span.get("quote"))
            for span in row.get("evidence_spans", [])
        )
    ]
    if limit <= 0:
        raise ValueError("limit must be positive")
    if limit >= len(eligible):
        return eligible
    if limit == 1:
        return [eligible[0]]
    positions = [round(index * (len(eligible) - 1) / (limit - 1)) for index in range(limit)]
    return [eligible[position] for position in positions]


def build_bundle(source: Mapping[str, Any], limit: int, reviewer: str) -> dict[str, Any]:
    selected_rows = select_rows(source["samples"], limit)
    candidates = []
    for ordinal, row in enumerate(selected_rows, start=1):
        built = _candidate(row, 0, ordinal)
        if built is not None:
            candidates.append(built)
    return {
        "dataset_info": {
            "name": "siemens_s210_causal_relation_candidates",
            "version": "v1",
            "status": "pending_expert_review",
            "review_type": "causal_relation_candidate_bundle",
            "source_dataset": source.get("dataset_info", {}).get("name"),
            "source_dataset_version": source.get("dataset_info", {}).get("version"),
            "source_record_count": len(source["samples"]),
            "candidate_count": len(candidates),
            "selection_policy": (
                "Pilot batch: evenly spaced source records, one explicitly extracted cause "
                "candidate per fault, with its original evidence and full input_text."
            ),
            "expected_reviewer": reviewer,
            "gold_source": "pending_named_expert_review",
            "training_eligible": False,
            "causal_relations_complete": False,
            "logic_gates_complete": False,
            "fta_ready": False,
            "not_expert_gold": True,
            "allowed_causal_status": [
                "causal",
                "associated_only",
                "unsupported",
                "cannot_determine",
            ],
            "allowed_direction": [
                "source_to_target",
                "target_to_source",
                "undirected",
                "unknown",
            ],
        },
        "candidates": candidates,
    }


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def build_checklist(bundle: Mapping[str, Any]) -> str:
    info = bundle["dataset_info"]
    lines = [
        "# Siemens S210 因果关系候选专家审核清单 v1",
        "",
        "> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。候选关系由现有 Gold 的 `causes` 字段和原文证据生成；`causes` 字段本身不等于已证明的因果关系。",
        "",
        "## 清单状态",
        "",
        f"- 审核状态：`{info['status']}`",
        f"- 预计审核专家：{info['expected_reviewer']}",
        f"- 候选数量：{info['candidate_count']} 条",
        f"- 来源记录：{info['source_record_count']} 条 S210 故障记录",
        "- 训练用途：否",
        "- FTA 用途：审核完成前禁止使用",
        "",
        "## 专家审核规则",
        "",
        "1. 先阅读候选原因、故障描述和完整原文，不得仅凭字段名 `Cause` 判定为因果。",
        "2. 只有原文明确表达“该原因/条件导致、触发、引起该故障”的，才可标记 `causal`。",
        "3. 原文只说明共同出现、诊断关联、参数解释或处理建议的，标记 `associated_only`，不要升级为 `causal`。",
        "4. 原文证据不足以判断时标记 `cannot_determine`；引用与候选原因不一致时标记 `unsupported`。",
        "5. 方向必须单独判断：原因节点 → 故障实体才是 `source_to_target`；无法证明方向时用 `unknown` 或 `undirected`。",
        "6. `fta_eligible=true` 只允许用于明确因果、方向清楚、证据直接支持的候选；否则为 `false`。",
        "",
        "## 可填写枚举",
        "",
        "| 字段 | 可填写值 |",
        "|---|---|",
        "| `causal_status` | `causal` / `associated_only` / `unsupported` / `cannot_determine` |",
        "| `direction` | `source_to_target` / `target_to_source` / `undirected` / `unknown` |",
        "| `relation_type` | `causes` / `caused_by` / `associated_with` / `no_relation` |",
        "| `fta_eligible` | `true` / `false` |",
        "| `overall_decision` | `approve` / `revise` / `reject` / `cannot_determine` |",
        "",
        "## 逐条审核",
        "",
    ]
    for candidate in bundle["candidates"]:
        source = candidate["source_record"]
        node = candidate["source_node"]
        target = candidate["target_node"]
        evidence = candidate["evidence"][0]
        context = candidate["source_context"]["input_text"]
        lines.extend(
            [
                f"### {candidate['candidate_id']} · {source['fault_code']}",
                "",
                f"- 来源记录：`{source['sample_id']}`（序号 {source.get('sequence')}）",
                f"- 故障描述：{source['description']}",
                f"- 候选原因节点：{node['text']}",
                f"- 目标故障实体：`{target['fault_code']}` · {target['description']}",
                "- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）",
                f"- 证据引用：`{evidence['evidence_id']}`，字符位置 `{evidence.get('start')}-{evidence.get('end')}`",
                f"- 证据原文：> {evidence['quote'].replace(chr(10), ' ')}",
                "",
                "**专家填写：**",
                "",
                "- causal_status：",
                "- direction：",
                "- relation_type：",
                "- fta_eligible：",
                "- overall_decision：",
                "- 审核意见：",
                "",
                "**完整原文：**",
                "",
                "```text",
                context,
                "```",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_JSON))
    parser.add_argument("--checklist", default=str(DEFAULT_CHECKLIST))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--reviewer", default="刘武")
    args = parser.parse_args()

    source = _load(Path(args.input))
    bundle = build_bundle(source, args.limit, args.reviewer)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist = Path(args.checklist)
    checklist.parent.mkdir(parents=True, exist_ok=True)
    checklist.write_text(build_checklist(bundle), encoding="utf-8")
    print(json.dumps({"output": str(output), "checklist": str(checklist), "candidate_count": len(bundle["candidates"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
