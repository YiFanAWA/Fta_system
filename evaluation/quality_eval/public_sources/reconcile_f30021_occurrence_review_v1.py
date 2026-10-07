#!/usr/bin/env python3
"""Reconcile the saved F30021 locator review with the latest raw v5 run offline.

This tool validates source identity and occurrence/scope offsets. It does not
rewrite the raw run, promote evidence into the current tree, call a model, or
change any Gold/readiness state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
QUALITY_EVAL = ROOT / "evaluation/quality_eval"
CORPUS_PATH = QUALITY_EVAL / "datasets/siemens_s210_public_fault_corpus_v1.jsonl"
RAW_RUN_PATH = QUALITY_EVAL / "runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json"
LOCATOR_REVIEW_PATH = QUALITY_EVAL / "runs/siemens_s210_F30021_C04_locator_ai_review_v1_2026-09-27.json"
OUTPUT_JSON_PATH = QUALITY_EVAL / "runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.json"
OUTPUT_MD_PATH = QUALITY_EVAL / "runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.md"

SAMPLE_ID = "SIEMENS_S210_2019_F30021"
CAUSE_INDEX = 3
CAUSE_TEXT = "short-circuit at the braking resistor"
EXACT_QUOTE = "- short-circuit at the braking resistor."
EXPECTED_OCCURRENCES = ((332, 372), (468, 508))
EXPECTED_SCOPE = (166, 372)


class ReconciliationError(ValueError):
    """Raised when a source/review/run identity or offset check fails."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _all_occurrences(text: str, needle: str) -> list[tuple[int, int]]:
    positions: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            return positions
        positions.append((start, start + len(needle)))
        cursor = start + 1


def _load_source_record(path: Path) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReconciliationError(f"invalid corpus JSONL at line {line_number}: {exc}") from exc
        if row.get("sample_id") == SAMPLE_ID:
            matches.append(row)
    if len(matches) != 1:
        raise ReconciliationError(f"expected exactly one {SAMPLE_ID} source record, found {len(matches)}")
    return matches[0]


def build_reconciliation(
    source_record: dict[str, Any], raw_run: dict[str, Any], locator_review: dict[str, Any]
) -> dict[str, Any]:
    text = source_record.get("input_text")
    if not isinstance(text, str) or not text:
        raise ReconciliationError("source input_text is missing")

    source_hash = _sha256_text(text)
    provenance = source_record.get("provenance", {})
    raw_source = raw_run.get("source", {})
    review_source = locator_review.get("source", {})
    if raw_run.get("artifact_type") != "candidate_fta_raw_source_development_probe":
        raise ReconciliationError("raw run artifact type does not match the expected development probe")
    if locator_review.get("artifact_type") != "fta_gate_node_evidence_locator_review":
        raise ReconciliationError("locator review artifact type does not match the expected review record")
    if locator_review.get("artifact_version") != "v1":
        raise ReconciliationError("unsupported locator review artifact version")
    if source_record.get("sample_id") != SAMPLE_ID:
        raise ReconciliationError("source sample_id does not match F30021")
    if raw_source.get("sample_id") != SAMPLE_ID or review_source.get("sample_id") != SAMPLE_ID:
        raise ReconciliationError("raw run and locator review must reference the same F30021 sample")
    if raw_source.get("input_text_sha256") != source_hash:
        raise ReconciliationError("raw run input_text hash does not match the corpus source")
    if review_source.get("source_sha256") != source_hash:
        raise ReconciliationError("locator review source hash does not match the corpus source")
    if raw_run.get("result", {}).get("source_text_sha256") != source_hash:
        raise ReconciliationError("derived result source hash does not match the corpus source")
    if locator_review.get("reviewer_is_human_expert") is not False:
        raise ReconciliationError("locator review provenance must remain explicitly non-human")
    if locator_review.get("formal_gold") is not False:
        raise ReconciliationError("locator review must not be promoted to formal Gold")

    scope = locator_review.get("scope_anchor", {})
    scope_quote = scope.get("quote")
    scope_start, scope_end = scope.get("start"), scope.get("end")
    if (scope_start, scope_end) != EXPECTED_SCOPE or text[scope_start:scope_end] != scope_quote:
        raise ReconciliationError("reviewed Possible causes scope anchor does not match the source offsets")
    if scope.get("occurrence_count_in_source") != 1 or len(_all_occurrences(text, scope_quote)) != 1:
        raise ReconciliationError("reviewed Possible causes scope anchor is not unique")

    exact_occurrences = _all_occurrences(text, EXACT_QUOTE)
    if tuple(exact_occurrences) != EXPECTED_OCCURRENCES:
        raise ReconciliationError(f"unexpected exact-quote occurrence offsets: {exact_occurrences}")
    review_occurrences = locator_review.get("all_exact_occurrences", [])
    reviewed_positions = [(item.get("start"), item.get("end")) for item in review_occurrences]
    if tuple(reviewed_positions) != EXPECTED_OCCURRENCES:
        raise ReconciliationError("locator review occurrence list does not match recomputed source positions")
    for item, (start, end) in zip(review_occurrences, EXPECTED_OCCURRENCES, strict=True):
        if text[start:end] != EXACT_QUOTE or item.get("inside_reviewed_scope") is not (scope_start <= start and end <= scope_end):
            raise ReconciliationError("locator review occurrence text/scope membership is inconsistent")

    selected = locator_review.get("selected_evidence", {})
    if (selected.get("start"), selected.get("end"), selected.get("quote")) != (
        EXPECTED_OCCURRENCES[0][0], EXPECTED_OCCURRENCES[0][1], EXACT_QUOTE
    ):
        raise ReconciliationError("saved locator selection is not the unique occurrence inside the reviewed scope")
    if locator_review.get("decision") != "resolved_by_scoped_occurrence":
        raise ReconciliationError("saved locator decision is not a scoped-occurrence resolution")
    if locator_review.get("gate_label_before") != "unknown" or locator_review.get("gate_label_after") != "unknown":
        raise ReconciliationError("locator review must leave the gate label unknown")
    if locator_review.get("gate_evidence_added") is not False:
        raise ReconciliationError("locator review must not add gate evidence")

    extraction = raw_run.get("result", {}).get("extraction", {})
    spans = extraction.get("evidence_spans", [])
    cause_spans = [
        (item.get("start"), item.get("end"))
        for item in spans
        if item.get("field") == "cause" and item.get("value_index") == CAUSE_INDEX
    ]
    context_spans = [
        (item.get("start"), item.get("end"))
        for item in spans
        if item.get("field") == "cause_context" and item.get("value_index") == CAUSE_INDEX
    ]
    if cause_spans != [(334, 371), (470, 507)] or context_spans != list(EXPECTED_OCCURRENCES):
        raise ReconciliationError("latest raw run does not preserve both exact cause/context occurrences")
    for item in spans:
        if item.get("field") in {"cause", "cause_context"} and item.get("value_index") == CAUSE_INDEX:
            if text[item["start"]:item["end"]] != item.get("quote"):
                raise ReconciliationError("latest raw run contains an inexact cause evidence span")

    outcome = raw_run.get("result", {}).get("outcomes", [])
    if len(outcome) != 1 or outcome[0].get("status") != "blocked":
        raise ReconciliationError("latest raw run must remain a single blocked F30021 outcome")
    tree = outcome[0].get("tree", {})
    disposition = next(
        (item for item in tree.get("cause_dispositions", []) if item.get("source_cause_index") == CAUSE_INDEX),
        None,
    )
    if (
        not disposition
        or disposition.get("disposition") != "unresolved"
        or disposition.get("reason_code") != "evidence_missing_or_ambiguous"
        or disposition.get("evidence") != []
    ):
        raise ReconciliationError("latest raw run must retain C04 as unresolved without confirmed evidence")
    gate_scopes = tree.get("gate_assessments", [])
    if len(gate_scopes) != 1 or gate_scopes[0].get("gate") != "unknown" or gate_scopes[0].get("gate_evidence") != []:
        raise ReconciliationError("latest raw run must retain unknown gate and no gate evidence")
    if gate_scopes[0].get("cause_set_complete") is not False:
        raise ReconciliationError("latest raw run must retain incomplete child-set status")
    blockers = tree.get("blockers", [])
    required_blockers = {"top_event_evidence_ambiguous", f"cause_disposition_unresolved:{CAUSE_INDEX}"}
    if not required_blockers.issubset(set(blockers)):
        raise ReconciliationError("latest raw run is missing the expected fail-closed blockers")

    top_event_occurrences = _all_occurrences(text, "ground fault")
    if len(top_event_occurrences) != 4:
        raise ReconciliationError("top-event phrase occurrence count no longer matches the recorded ambiguity")

    return {
        "artifact_type": "fta_f30021_occurrence_review_reconciliation",
        "artifact_version": "v1",
        "created_on": "2026-10-07",
        "reviewer_provenance": "offline_engineering_reconciliation_of_user_authorized_ai_locator_review_not_human_expert_signoff",
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "model_requests_performed": 0,
        "source": {
            "sample_id": SAMPLE_ID,
            "fault_code": "F30021",
            "source_sha256": source_hash,
            "source_pdf_sha256": provenance.get("source_sha256"),
            "section": provenance.get("section"),
            "pdf_page_start": provenance.get("pdf_page_start"),
            "pdf_page_end": provenance.get("pdf_page_end"),
            "offset_unit": "Unicode code point",
            "offset_convention": "zero-based half-open [start,end)",
        },
        "locator_review": {
            "review_id": locator_review.get("review_id"),
            "reviewer_provenance": locator_review.get("reviewer_provenance"),
            "reviewer_is_human_expert": False,
            "formal_gold": False,
            "decision": locator_review.get("decision"),
            "scope_anchor": {"start": scope_start, "end": scope_end, "quote": scope_quote},
            "all_exact_occurrences": [
                {
                    "start": start,
                    "end": end,
                    "quote": text[start:end],
                    "inside_reviewed_scope": scope_start <= start and end <= scope_end,
                }
                for start, end in exact_occurrences
            ],
            "selected_occurrence": {"start": selected["start"], "end": selected["end"], "quote": selected["quote"]},
            "scope_consistency": "passed_unique_possible_causes_occurrence",
            "gate_label_before": "unknown",
            "gate_label_after": "unknown",
            "gate_evidence_added": False,
        },
        "latest_raw_run": {
            "path": "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json",
            "cause_disposition_prompt": raw_run.get("prompt_versions", {}).get("cause_disposition"),
            "cause_index": CAUSE_INDEX,
            "cause_text": CAUSE_TEXT,
            "cause_value_spans": [{"start": start, "end": end} for start, end in cause_spans],
            "cause_context_spans": [{"start": start, "end": end} for start, end in context_spans],
            "current_disposition": "unresolved",
            "current_disposition_reason": "evidence_missing_or_ambiguous",
            "current_disposition_evidence": [],
            "prior_locator_decision_applied": False,
            "tree_status": "blocked",
            "top_event_phrase": "ground fault",
            "top_event_occurrence_count": len(top_event_occurrences),
            "gate": "unknown",
            "gate_evidence": [],
            "cause_set_complete": False,
            "blockers": sorted(blockers),
        },
        "reconciliation_result": {
            "scope_and_offsets_consistent": True,
            "prior_locator_selection_valid_within_reviewed_scope": True,
            "prior_locator_decision_applied_to_latest_run": False,
            "latest_raw_run_remains_blocked": True,
            "semantic_defects_closed": 0,
            "shared_contract_changed": False,
            "gold_changed": False,
            "readiness_changed": False,
        },
        "limitations": [
            "The saved locator decision is an authorized AI subagent review, not human expert signoff or formal Gold.",
            "This offline reconciliation validates source identity, exact offsets, and scope membership only; it does not revise the immutable v5 run.",
            "The current runtime does not consume the historical locator decision, so C04 remains unresolved in the latest run.",
            "The top-event phrase remains ambiguous, the child set remains incomplete, and gate confidence policy remains unavailable; the tree stays blocked.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    source = report["source"]
    review = report["locator_review"]
    run = report["latest_raw_run"]
    return "\n".join(
        [
            "# F30021 重复证据定位离线对账 v1",
            "",
            "日期：2026-10-07  ",
            "性质：离线工程复核；无模型调用，不改原始运行、Gold、数据库、共享合同或 readiness。",
            "",
            "## 结论",
            "",
            "已有 C04 定位审核在来源哈希、原文偏移和唯一 Possible causes scope 上一致：`[332,372)` 是原因列表内的唯一出现，`[468,508)` 位于后续 r0949 故障值说明。该历史定位结果本次**没有回填**到最新 v5 原始运行。",
            "",
            f"因此最新运行仍为 `{run['tree_status']}`：C04=`unresolved` 且没有已确认 evidence；顶事件短语在原文出现 {run['top_event_occurrence_count']} 次；child 集合不完整；门型为 `unknown`。本次关闭的是定位工件与来源的离线一致性核对，不是 FTA 语义缺陷。",
            "",
            "## 来源与偏移核验",
            "",
            f"- 样本：`{source['sample_id']}` / `{source['fault_code']}`",
            f"- 原文 SHA-256：`{source['source_sha256']}`",
            f"- 偏移：{source['offset_unit']}，{source['offset_convention']}",
            f"- 唯一审核 scope：`[{review['scope_anchor']['start']},{review['scope_anchor']['end']})`，其中 exact quote 位于 `[{review['selected_occurrence']['start']},{review['selected_occurrence']['end']})`",
            f"- 全文重复 exact quote：`[{review['all_exact_occurrences'][0]['start']},{review['all_exact_occurrences'][0]['end']})`（scope 内）；`[{review['all_exact_occurrences'][1]['start']},{review['all_exact_occurrences'][1]['end']})`（scope 外）",
            "- 原定位材料来源：授权 AI 子智能体审核；`reviewer_is_human_expert=false`、`formal_gold=false`。",
            "",
            "## 最新运行未解除的阻断",
            "",
            f"- 当前原因处置：index {run['cause_index']} `{run['cause_text']}` → `{run['current_disposition']}` / `{run['current_disposition_reason']}`，`evidence=[]`。",
            f"- 原始抽取仍保留两个 cause span：`{run['cause_value_spans'][0]['start']}–{run['cause_value_spans'][0]['end']}`、`{run['cause_value_spans'][1]['start']}–{run['cause_value_spans'][1]['end']}`；对应 context span：`{run['cause_context_spans'][0]['start']}–{run['cause_context_spans'][0]['end']}`、`{run['cause_context_spans'][1]['start']}–{run['cause_context_spans'][1]['end']}`。",
            f"- Blockers：`{', '.join(run['blockers'])}`。",
            "- 门型继续 `unknown`，没有添加门证据；本材料不推 OR/AND。",
            "",
            "## 边界与下一步",
            "",
            "本轮不改共享 evidence/API 合同。若未来要让运行时或审核端消费已确认的定位，必须先明确唯一 owner 与持久化/审核出口，再单独评审合同变更；在此之前，最新 v5 原始运行保持不可变且 blocked。任何新的在线模型请求都需要针对该次请求重新授权。",
            "",
        ]
    )


def build_from_repository() -> dict[str, Any]:
    source = _load_source_record(CORPUS_PATH)
    raw_run = json.loads(RAW_RUN_PATH.read_text(encoding="utf-8"))
    locator_review = json.loads(LOCATOR_REVIEW_PATH.read_text(encoding="utf-8"))
    report = build_reconciliation(source, raw_run, locator_review)
    report["input_artifacts"] = {
        "source_corpus_path": CORPUS_PATH.relative_to(ROOT).as_posix(),
        "raw_run_path": RAW_RUN_PATH.relative_to(ROOT).as_posix(),
        "raw_run_sha256": hashlib.sha256(RAW_RUN_PATH.read_bytes()).hexdigest(),
        "locator_review_path": LOCATOR_REVIEW_PATH.relative_to(ROOT).as_posix(),
        "locator_review_sha256": hashlib.sha256(LOCATOR_REVIEW_PATH.read_bytes()).hexdigest(),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved report matches current inputs without writing")
    args = parser.parse_args()
    report = build_from_repository()
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    rendered_md = render_markdown(report)
    if args.check:
        if not OUTPUT_JSON_PATH.exists() or OUTPUT_JSON_PATH.read_text(encoding="utf-8") != rendered_json:
            parser.exit(1, "F30021 occurrence reconciliation JSON differs from current inputs\n")
        if not OUTPUT_MD_PATH.exists() or OUTPUT_MD_PATH.read_text(encoding="utf-8") != rendered_md:
            parser.exit(1, "F30021 occurrence reconciliation Markdown differs from current inputs\n")
        status = "current"
    else:
        OUTPUT_JSON_PATH.write_text(rendered_json, encoding="utf-8", newline="\n")
        OUTPUT_MD_PATH.write_text(rendered_md, encoding="utf-8", newline="\n")
        status = "written"
    print(json.dumps({
        "status": status,
        "scope_and_offsets_consistent": report["reconciliation_result"]["scope_and_offsets_consistent"],
        "prior_locator_decision_applied": report["latest_raw_run"]["prior_locator_decision_applied"],
        "tree_status": report["latest_raw_run"]["tree_status"],
        "semantic_defects_closed": report["reconciliation_result"]["semantic_defects_closed"],
        "model_requests_performed": report["model_requests_performed"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
