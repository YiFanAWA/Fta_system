#!/usr/bin/env python3
"""Audit record/text overlap between the S120/S150 holdout and S210 artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any, Iterable, Sequence


DEFAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_S120 = DEFAULT_ROOT / "evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.jsonl"
DEFAULT_S210 = DEFAULT_ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl"
DEFAULT_S210_GATE_REVIEW = (
    DEFAULT_ROOT
    / "evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v6_locator_reconciled_ai_role_review.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: str | None) -> str:
    """Normalize only Unicode form, case, and whitespace; preserve punctuation."""
    return " ".join(unicodedata.normalize("NFKC", value or "").casefold().split())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def _row_code(row: dict[str, Any]) -> str:
    value = row.get("weak_record", {}).get("fault_code")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("every corpus row must have a non-empty weak_record.fault_code")
    return value.strip().upper()


def _cause(row: dict[str, Any]) -> str:
    value = row.get("weak_record", {}).get("causes_text")
    return normalize_text(value if isinstance(value, str) else None)


def _is_substring_overlap(left: str, right: str, *, min_chars: int) -> bool:
    if not left or not right or left == right or min(len(left), len(right)) < min_chars:
        return False
    return left in right or right in left


def _group_counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[field]].append(row)
    return {
        name: {
            "record_count": len(items),
            "unique_fault_code_count": len({item["fault_code"] for item in items}),
        }
        for name, items in sorted(grouped.items())
    }


def build_overlap_audit(
    s120_rows: Sequence[dict[str, Any]],
    s210_rows: Sequence[dict[str, Any]],
    gate_review: dict[str, Any],
    *,
    s120_path: Path,
    s210_path: Path,
    gate_review_path: Path,
    audit_date: str | None = None,
    min_containment_chars: int = 32,
) -> dict[str, Any]:
    if min_containment_chars < 1:
        raise ValueError("min_containment_chars must be positive")

    s210_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exact_cause_any_code: dict[str, list[str]] = defaultdict(list)
    s210_causes: list[tuple[str, str]] = []
    for row in s210_rows:
        code = _row_code(row)
        s210_by_code[code].append(row)
        cause = _cause(row)
        if cause:
            exact_cause_any_code[cause].append(row["sample_id"])
            s210_causes.append((row["sample_id"], cause))

    detailed_rows: list[dict[str, Any]] = []
    for row in s120_rows:
        code = _row_code(row)
        cause = _cause(row)
        same_code_rows = s210_by_code.get(code, [])
        exact_same_code_ids = [candidate["sample_id"] for candidate in same_code_rows if cause and _cause(candidate) == cause]
        partial_same_code_ids = [
            candidate["sample_id"]
            for candidate in same_code_rows
            if cause
            and _is_substring_overlap(
                cause, _cause(candidate), min_chars=min_containment_chars
            )
        ]
        global_exact_ids = exact_cause_any_code.get(cause, []) if cause else []
        global_partial_ids = [
            sample_id
            for sample_id, old_cause in s210_causes
            if cause
            and _is_substring_overlap(
                cause, old_cause, min_chars=min_containment_chars
            )
        ]

        if exact_same_code_ids:
            stratum = "same_code_exact_cause_text"
        elif partial_same_code_ids:
            stratum = "same_code_partial_cause_text"
        elif same_code_rows:
            stratum = "same_fault_code_other_cause_text"
        elif global_exact_ids:
            stratum = "unseen_code_exact_cause_text_reused"
        else:
            stratum = "unseen_fault_code_no_exact_full_cause_text_overlap"

        provenance = row.get("provenance", {})
        detailed_rows.append(
            {
                "sample_id": row.get("sample_id"),
                "fault_code": code,
                "pdf_page_start": provenance.get("pdf_page_start"),
                "same_fault_code_in_s210": bool(same_code_rows),
                "same_code_exact_cause_text_match": bool(exact_same_code_ids),
                "same_code_partial_cause_text_match_min_chars": bool(partial_same_code_ids),
                "exact_cause_text_match_any_s210_code": bool(global_exact_ids),
                "partial_cause_text_containment_match_any_s210_code_min_chars": bool(global_partial_ids),
                "overlap_stratum": stratum,
                "matched_s210_sample_ids": exact_same_code_ids or partial_same_code_ids or [],
                "matched_s210_exact_cause_sample_ids_any_code": global_exact_ids,
                "matched_s210_partial_cause_sample_ids_any_code": global_partial_ids,
            }
        )

    s120_code_set = {_row_code(row) for row in s120_rows}
    s210_code_set = set(s210_by_code)
    reviewed_nodes = [
        node
        for node in gate_review.get("gate_nodes", [])
        if node.get("review_status") == "reviewed"
    ]
    reviewer_provenance_counts = Counter(
        value
        for node in reviewed_nodes
        for value in [node.get("reviewer_provenance")]
        if isinstance(value, str) and value.strip()
    )
    s120_text_by_code: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in s120_rows:
        s120_text_by_code[_row_code(row)].append(
            (row["sample_id"], normalize_text(row.get("input_text")))
        )

    gate_overlap_details: list[dict[str, Any]] = []
    for node in reviewed_nodes:
        code = str(node.get("fault_code", "")).strip().upper()
        quote = normalize_text(node.get("scope_anchor", {}).get("quote"))
        matching_ids = [
            sample_id
            for sample_id, raw_text in s120_text_by_code.get(code, [])
            if quote and quote in raw_text
        ]
        gate_overlap_details.append(
            {
                "gate_node_id": node.get("gate_node_id"),
                "fault_code": code,
                "s120_same_fault_code_exists": code in s120_code_set,
                "scope_anchor_exact_text_reused_in_s120": bool(matching_ids),
                "matching_s120_sample_ids": matching_ids,
            }
        )

    strata_counts = _group_counts(detailed_rows, "overlap_stratum")
    same_code_nodes = [item for item in gate_overlap_details if item["s120_same_fault_code_exists"]]
    exact_scope_nodes = [
        item for item in gate_overlap_details if item["scope_anchor_exact_text_reused_in_s120"]
    ]

    return {
        "artifact_type": "external_source_overlap_audit",
        "artifact_version": "1.0.0",
        "audit_date": audit_date or date.today().isoformat(),
        "status": "descriptive_overlap_audit_not_model_evaluation",
        "sources": {
            "s120_s150_holdout_v2": {
                "path": str(s120_path),
                "sha256": sha256_file(s120_path),
                "record_count": len(s120_rows),
                "unique_fault_code_count": len(s120_code_set),
            },
            "s210_public_corpus_v1": {
                "path": str(s210_path),
                "sha256": sha256_file(s210_path),
                "record_count": len(s210_rows),
                "unique_fault_code_count": len(s210_code_set),
            },
            "s210_gate_node_review": {
                "path": str(gate_review_path),
                "artifact_name": gate_review_path.name,
                "artifact_version": gate_review.get("artifact_version"),
                "sha256": sha256_file(gate_review_path),
                "reviewer_is_human_expert": gate_review.get("reviewer_is_human_expert"),
                "reviewer_provenance": gate_review.get("reviewer_provenance"),
                "reviewer_provenance_counts": dict(sorted(reviewer_provenance_counts.items())),
                "reviewed_gate_node_count": len(reviewed_nodes),
            },
        },
        "method": {
            "text_normalization": "Unicode NFKC + casefold + whitespace collapse; punctuation preserved",
            "exact_cause_text": "full parser-produced weak_record.causes_text strings are equal after normalization",
            "partial_cause_text": (
                "one full parser-produced causes_text is a proper substring of the other after normalization; "
                f"shorter string length >= {min_containment_chars} characters"
            ),
            "partial_cause_text_match_scope": "all S210 fault codes; a lexical screen, not a semantic duplication label",
            "scope_anchor_reuse": "normalized reviewed S210 scope_anchor.quote occurs verbatim in S120/S150 input_text with same fault_code",
            "limitations": [
                "Cause strings and scopes are parser/review artifact text, not semantic equivalence labels.",
                "Fault-code overlap means the record identity is not unseen; it does not itself prove gate evidence leakage.",
                "Text overlap is a contamination warning, not an accuracy score.",
                "The S120/S150 manual remains one source cluster; records are not independent source samples.",
            ],
        },
        "summary": {
            "unique_fault_code_intersection_s120_s210": len(s120_code_set & s210_code_set),
            "s120_records_with_s210_fault_code": sum(item["same_fault_code_in_s210"] for item in detailed_rows),
            "s120_records_with_partial_cause_text_containment_any_s210_code_min_chars": sum(
                item["partial_cause_text_containment_match_any_s210_code_min_chars"]
                for item in detailed_rows
            ),
            "s120_records_by_overlap_stratum": strata_counts,
            "s210_reviewed_gate_nodes": len(reviewed_nodes),
            "s210_reviewed_gate_nodes_with_same_fault_code_in_s120": len(same_code_nodes),
            "s210_reviewed_gate_nodes_with_same_code_and_exact_scope_anchor_text_in_s120": len(exact_scope_nodes),
            "unique_s210_reviewed_gate_fault_codes": len({item["fault_code"] for item in gate_overlap_details}),
            "unique_s210_reviewed_gate_fault_codes_present_in_s120": len(
                {item["fault_code"] for item in gate_overlap_details if item["s120_same_fault_code_exists"]}
            ),
            "unique_s210_reviewed_gate_fault_codes_absent_from_s120": sorted(
                {item["fault_code"] for item in gate_overlap_details if not item["s120_same_fault_code_exists"]}
            ),
        },
        "interpretation": {
            "document_level_holdout": "valid as a different manual/edition source holdout, provided it was not used to tune the tested system",
            "unseen_fault_semantic_generalization": "must be reported on the unseen-fault-code stratum separately; exact cause-text reuse should be disclosed",
            "calibration_claim": "not supported by this single source cluster or by this overlap audit",
            "automatic_gate_labels": "not produced; explicit local evidence and complete child scope still require review; absent direct evidence stays unknown",
            "ai_review_provenance": "AI-role analysis is not a human expert signature or formal Gold",
        },
        "s120_records": detailed_rows,
        "s210_reviewed_gate_node_overlap": gate_overlap_details,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    gate_review_source = report["sources"]["s210_gate_node_review"]
    rows = [
        "# S120/S150 与 S210 来源重叠审计",
        "",
        f"审计日期：{report['audit_date']}；审计方法版本：{report['artifact_version']}。本报告是来源/文本重叠审计，不是模型评测或 Gold。",
        "",
        "## 结果",
        "",
        f"- S120/S150：{report['sources']['s120_s150_holdout_v2']['record_count']} 条记录，{report['sources']['s120_s150_holdout_v2']['unique_fault_code_count']} 个故障码。",
        f"- S210：{report['sources']['s210_public_corpus_v1']['record_count']} 条记录，{report['sources']['s210_public_corpus_v1']['unique_fault_code_count']} 个故障码。",
        f"- 两份语料故障码交集：{summary['unique_fault_code_intersection_s120_s210']} 个；S120/S150 中有 {summary['s120_records_with_s210_fault_code']} 条记录使用 S210 已出现的故障码。",
        f"- 跨故障码解析 causes_text 包含筛查（较短文本≥32字符）：{summary['s120_records_with_partial_cause_text_containment_any_s210_code_min_chars']} 条 S120/S150 记录与任意 S210 记录有可能的局部文本重合。",
        f"- S210 已审核门节点：{summary['s210_reviewed_gate_nodes']} 个；同码出现在 S120/S150 的有 {summary['s210_reviewed_gate_nodes_with_same_fault_code_in_s120']} 个，其中原审核 scope 引文在 S120/S150 同码原文中精确复现 {summary['s210_reviewed_gate_nodes_with_same_code_and_exact_scope_anchor_text_in_s120']} 个。",
        "",
        "| S120/S150 记录分层 | 记录数 | 唯一故障码数 |",
        "| --- | ---: | ---: |",
    ]
    labels = {
        "same_code_exact_cause_text": "同故障码 + 解析 causes_text 完整文本精确重合",
        "same_code_partial_cause_text": "同故障码 + 解析 causes_text 完整文本局部包含（≥32字符）",
        "same_fault_code_other_cause_text": "同故障码，但未发现上述解析文本重合",
        "unseen_code_exact_cause_text_reused": "故障码未见，但解析 causes_text 在任意 S210 记录精确重合",
        "unseen_fault_code_no_exact_full_cause_text_overlap": "故障码未见，解析 causes_text 无精确重合",
    }
    for key, value in summary["s120_records_by_overlap_stratum"].items():
        rows.append(
            f"| {labels.get(key, key)} | {value['record_count']} | {value['unique_fault_code_count']} |"
        )
    rows.extend(
        [
            "",
            "## 判读边界",
            "",
            "- 该材料仍是整本手册/版本级留出，但由于同产品家族的故障码和原文重复，不能把全部记录称为独立故障语义泛化测试。",
            "- 最强的未见故障码子集须单独报告；完整文本没有精确重复也不等同于语义独立，仍需人工看局部重复和关系标签是否泄漏。",
            "- S210 的 AI 角色门审核标签不是人类专家签署；同故障码或原文重复只提示潜在泄漏，不自动证明标签泄漏。",
            "- 本审计未生成 AND/OR 标签、未调用模型 API、未校准概率、未修改 Gold/数据库；无直接作用域门证据仍应标 unknown。",
            "",
            "## 可复核产物",
            "",
            f"- 明细 JSON：`{report['artifact_type']}`，包含每条 S120 记录的分层和匹配 S210 sample_id。",
            f"- S120 corpus SHA-256：`{report['sources']['s120_s150_holdout_v2']['sha256']}`",
            f"- S210 corpus SHA-256：`{report['sources']['s210_public_corpus_v1']['sha256']}`",
            f"- S210 gate review：`{gate_review_source['artifact_name']}`（{gate_review_source['reviewed_gate_node_count']} 个 reviewed 节点；真人专家标记：{gate_review_source['reviewer_is_human_expert']}）",
            f"- S210 gate review SHA-256：`{gate_review_source['sha256']}`",
            "",
        ]
    )
    return "\n".join(rows)


def load_and_audit(
    s120_path: Path = DEFAULT_S120,
    s210_path: Path = DEFAULT_S210,
    gate_review_path: Path = DEFAULT_S210_GATE_REVIEW,
    *,
    audit_date: str | None = None,
) -> dict[str, Any]:
    with gate_review_path.open("r", encoding="utf-8") as stream:
        gate_review = json.load(stream)
    return build_overlap_audit(
        read_jsonl(s120_path),
        read_jsonl(s210_path),
        gate_review,
        s120_path=s120_path,
        s210_path=s210_path,
        gate_review_path=gate_review_path,
        audit_date=audit_date,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s120", type=Path, default=DEFAULT_S120)
    parser.add_argument("--s210", type=Path, default=DEFAULT_S210)
    parser.add_argument("--gate-review", type=Path, default=DEFAULT_S210_GATE_REVIEW)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output_json.resolve() == args.output_md.resolve():
        raise ValueError("JSON and Markdown outputs must use different paths")
    if args.output_json.exists() or args.output_md.exists():
        raise FileExistsError("refusing to overwrite an existing overlap audit")

    report = load_and_audit(args.s120, args.s210, args.gate_review)
    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    markdown_text = render_markdown(report)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    try:
        for path, content in ((args.output_json, json_text), (args.output_md, markdown_text)):
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            written.append(path)
    except Exception:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
