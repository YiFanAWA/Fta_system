"""Merge confirmed expert rows and model candidates into one review queue.

This artifact is deliberately not an importable gold dataset.  Rows without an
explicit expert decision remain pending and contain model predictions only.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


APPROVED_DECISIONS = {"审核通过", "approved"}
CORRECTED_DECISIONS = {"语义需修改", "needs_revision"}
BLOCKING_DECISIONS = {"证据不足", "无法判断", "evidence_insufficient", "undetermined"}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"无法解析 {path}:{line_number}: {exc}") from exc
    return rows


def _decision_is_resolved(item: dict[str, Any]) -> bool:
    review = item.get("expert_review") or {}
    decision = review.get("decision")
    if decision in APPROVED_DECISIONS:
        return True
    return decision in CORRECTED_DECISIONS and bool(review.get("correction_applied"))


def _confirmed_row(item: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(item)
    row["review_queue"] = {
        "status": "confirmed_expert",
        "reason": "user_accepted_expert_review",
        "decision": (row.get("expert_review") or {}).get("decision"),
        "source_kind": "confirmed_expert_review",
    }
    return row


def _needs_resolution_row(item: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(item)
    review = row.get("expert_review") or {}
    row["review_queue"] = {
        "status": "needs_resolution",
        "reason": "expert_decision_not_importable",
        "decision": review.get("decision"),
        "source_kind": "confirmed_expert_review",
        "resolution_required": review.get("modified_content") or review.get("opinion"),
    }
    return row


def _pending_row(
    corpus_row: dict[str, Any],
    candidate_row: dict[str, Any],
    batch_name: str,
) -> dict[str, Any]:
    prediction = deepcopy(candidate_row.get("model_prediction") or {})
    if prediction.get("status") != "success":
        raise ValueError(f"候选 {corpus_row['sample_id']} 没有成功的模型预测")
    evidence_audit = candidate_row.get("review_queue", {}).get("evidence_audit") or {}
    if evidence_audit.get("status") != "valid":
        raise ValueError(f"候选 {corpus_row['sample_id']} 的证据位置未通过校验")

    row = deepcopy(corpus_row)
    row["split"] = "expert_review_queue"
    row["model_prediction"] = prediction
    row["evidence_spans"] = deepcopy(prediction.get("evidence_spans") or [])
    row["gold_records"] = []
    row["gold_relations"] = []
    row["logic_status"] = "unknown"
    row["expert_review"] = {
        "decision": None,
        "fields_to_modify": None,
        "modified_content": None,
        "opinion": None,
        "reviewer_name": None,
        "review_date": None,
        "correction_applied": False,
        "accepted_as_expert_by_user": False,
    }
    row["review_history"] = []
    row["review_queue"] = {
        "status": "pending",
        "reason": "awaiting_expert_confirmation",
        "source_kind": "model_candidate",
        "candidate_batch": batch_name,
        "evidence_audit": deepcopy(evidence_audit),
    }
    return row


def build_full_review_queue(
    corpus: dict[str, Any],
    confirmed_dataset: dict[str, Any],
    candidate_datasets: list[tuple[str, dict[str, Any]]],
    expected_confirmed_count: int = 30,
) -> dict[str, Any]:
    corpus_rows = {row["sample_id"]: row for row in _load_jsonl(Path(corpus["path"]))}
    confirmed_rows = {
        row["sample_id"]: row
        for row in confirmed_dataset.get("samples", [])
        if row.get("sample_id") in corpus_rows
    }
    if len(confirmed_rows) != expected_confirmed_count:
        raise ValueError(
            f"已确认公开专家记录应为{expected_confirmed_count}条，实际为{len(confirmed_rows)}条"
        )
    unsupported_decisions = [
        (sample_id, (row.get("expert_review") or {}).get("decision"))
        for sample_id, row in confirmed_rows.items()
        if (row.get("expert_review") or {}).get("decision") not in (
            APPROVED_DECISIONS | CORRECTED_DECISIONS | BLOCKING_DECISIONS
        )
    ]
    if unsupported_decisions:
        raise ValueError(f"已有专家记录包含未知结论: {unsupported_decisions[:5]}")

    candidates: dict[str, tuple[str, dict[str, Any]]] = {}
    for batch_name, dataset in candidate_datasets:
        for row in dataset.get("samples", []):
            sample_id = row.get("sample_id")
            if sample_id in confirmed_rows:
                raise ValueError(f"候选批次 {batch_name} 与已确认记录重叠: {sample_id}")
            if sample_id not in corpus_rows:
                raise ValueError(f"候选批次 {batch_name} 含有不在公开语料中的记录: {sample_id}")
            if sample_id in candidates:
                raise ValueError(f"候选批次重复覆盖: {sample_id}")
            candidates[sample_id] = (batch_name, row)

    expected_ids = set(corpus_rows)
    actual_ids = set(confirmed_rows) | set(candidates)
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    if missing or extra:
        raise ValueError(f"全量覆盖不完整: missing={missing[:5]}, extra={extra[:5]}")

    rows: list[dict[str, Any]] = []
    for sample_id in sorted(expected_ids):
        if sample_id in confirmed_rows:
            confirmed_row = confirmed_rows[sample_id]
            decision = (confirmed_row.get("expert_review") or {}).get("decision")
            if decision in BLOCKING_DECISIONS:
                rows.append(_needs_resolution_row(confirmed_row))
            else:
                rows.append(_confirmed_row(confirmed_row))
        else:
            batch_name, candidate = candidates[sample_id]
            rows.append(_pending_row(corpus_rows[sample_id], candidate, batch_name))

    reviewed_count = sum(row["sample_id"] in confirmed_rows for row in rows)
    confirmed_count = sum(row["review_queue"]["status"] == "confirmed_expert" for row in rows)
    needs_resolution_count = sum(row["review_queue"]["status"] == "needs_resolution" for row in rows)
    pending_count = sum(row["review_queue"]["status"] == "pending" for row in rows)
    return {
        "dataset_info": {
            "name": "siemens_s210_public_fault_full_review_queue",
            "version": "2026-09-20",
            "source_corpus": corpus["path"],
            "source_records": len(rows),
            "expert_review_decided_records": reviewed_count,
            "confirmed_expert_records": confirmed_count,
            "needs_resolution_records": needs_resolution_count,
            "pending_review_records": pending_count,
            "label_status": "partial_expert_review_queue",
            "import_ready": False,
            "training_eligible": False,
            "logic_policy": "unknown_until_explicitly_expert_annotated",
            "review_rule": "未有明确专家结论的记录不得视为金标，不得入库",
        },
        "samples": rows,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-jsonl", required=True, type=Path)
    parser.add_argument("--confirmed-json", required=True, type=Path)
    parser.add_argument("--candidate-json", action="append", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def render_markdown(dataset: dict[str, Any]) -> str:
    info = dataset["dataset_info"]
    lines = [
        "# SINAMICS S210 全量故障记录审核队列（281条）",
        "",
        "> 本文件是审核工作包，不是自动生成的金标。`pending` 记录必须由专家填写结论后才能入库。",
        "",
        f"- 总记录：{info['source_records']}",
        f"- 已有专家结论：{info['expert_review_decided_records']}",
        f"- 已确认专家结果：{info['confirmed_expert_records']}",
        f"- 待审核候选：{info['pending_review_records']}",
        f"- 当前可入库：{info['import_ready']}",
        "- 审核结论：审核通过 / 证据不足 / 语义需修改 / 无法判断",
        "",
        "## 审核填写要求",
        "",
        "1. 以原文为依据核对故障码、故障现象、主组件、关联组件、候选原因、参数。",
        "2. 每个非空字段都要有字段级原文证据；原文未声明的组件不得推断填写。",
        "3. `pending` 只表示等待审核，不代表正确；只有有明确专家结论的记录才能进入最终金标。",
        "4. AND/OR 未有明确标注时保持 `unknown`，不在本批次强行推断。",
        "",
        "## 逐条记录",
        "",
    ]
    for index, row in enumerate(dataset["samples"], 1):
        queue = row.get("review_queue") or {}
        prediction = row.get("model_prediction") or {}
        if "records" in prediction:
            extracted = prediction.get("records")
        else:
            extracted = [prediction.get("record")] if prediction.get("record") else []
        lines.extend(
            [
                f"### {index:03d}. {row['sample_id']}",
                "",
                f"- 当前状态：`{queue.get('status')}`",
                f"- 来源批次：`{queue.get('candidate_batch', 'confirmed_expert_review')}`",
                f"- 故障码（弱标签）：`{row.get('weak_record', {}).get('fault_code', '')}`",
                "",
                "#### 模型候选/已确认记录",
                "",
                "```json",
                json.dumps(extracted, ensure_ascii=False, indent=2),
                "```",
                "",
                "#### 原文",
                "",
                "```text",
                row.get("input_text", ""),
                "```",
                "",
                "#### 字段级证据",
                "",
                "```json",
                json.dumps(row.get("evidence_spans", []), ensure_ascii=False, indent=2),
                "```",
                "",
                "#### 专家审核",
                "",
                f"- 审核结论：{(row.get('expert_review') or {}).get('decision') or '待填写'}",
                f"- 审核意见：{(row.get('expert_review') or {}).get('opinion') or ''}",
                "- 需修改字段：",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    corpus = {"path": str(args.corpus_jsonl), "rows": _load_jsonl(args.corpus_jsonl)}
    confirmed = _load_json(args.confirmed_json)
    candidates = []
    for path in args.candidate_json:
        dataset = _load_json(path)
        batch_name = path.stem
        candidates.append((batch_name, dataset))
    output = build_full_review_queue(corpus, confirmed, candidates)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(output), encoding="utf-8")
    print(json.dumps(output["dataset_info"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
