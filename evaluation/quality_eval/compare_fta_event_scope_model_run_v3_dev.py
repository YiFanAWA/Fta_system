#!/usr/bin/env python3
"""Create a qualitative, non-scoring comparison of the seen Figure 7 Dev run and reference labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.event_scope_tree_contract import validate_event_scope_tree


PACKET_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
GOLD_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"
RUN_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json"
ASSESSMENT_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v3_2026-09-29.json"
REPORT_JSON_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json"
REPORT_MD_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def build_report() -> dict[str, Any]:
    packet = _read(PACKET_PATH)
    gold = _read(GOLD_PATH)
    run = _read(RUN_PATH)
    assessment = _read(ASSESSMENT_PATH)

    packet_id = packet["packet_id"]
    input_hash = run["case"]["model_input_sha256"]
    if packet_id != gold.get("packet_id") or packet_id != run["case"].get("packet_id"):
        raise ValueError("packet identity mismatch across input, Gold, and run")
    if input_hash != gold.get("model_input_sha256") or input_hash != run["case"].get("model_input_sha256"):
        raise ValueError("model-input hash mismatch across Gold and run")
    if run["case"].get("exposure_status") != "seen_development_only":
        raise ValueError("this comparison is restricted to the already-seen Development packet")

    parsed = run["model_output"].get("parsed_json")
    if not isinstance(parsed, dict):
        raise ValueError("model run has no parsed JSON output")
    tree_contract = validate_event_scope_tree(parsed)
    nodes = {item["id"]: item for item in parsed.get("nodes", [])}
    gates = parsed.get("gates", [])
    reviews = {item["scope_id"]: item for item in gold.get("text_gate_reviews", [])}
    gold_diagram_gates = {item["scope_id"]: item for item in gold.get("diagram_gates", [])}
    root_node_id = gold["root_node_id"]
    root_node = nodes["E1"]
    root_gate = next(item for item in gates if item.get("output_node_id") == "E1")
    secondary_review = reviews["secondary-explosion-gate"]
    structural_review = reviews["module-structural-failure-gate"]
    secondary_gate = next(item for item in gates if item.get("scope_id") == "S3")
    structural_gate = next(item for item in gates if item.get("scope_id") == "S2")

    source_text = "\n".join(segment["text"] for segment in packet["model_input"]["source_segments"])
    quotes = [item.get("evidence_quote", "") for item in parsed.get("nodes", []) + gates]
    valid_quotes = sum(bool(quote) and quote in source_text for quote in quotes)
    if len(quotes) != 8 or valid_quotes != 8:
        raise ValueError(f"expected all 8 emitted quotes to match the model input; got {valid_quotes}/{len(quotes)}")

    findings = [
        {
            "finding_id": "top_event_text",
            "status": "aligned",
            "observation": "The predicted top-event wording matches the packet top-event wording.",
            "prediction": root_node["text"],
            "reference": packet["model_input"]["top_event"]["text"],
        },
        {
            "finding_id": "top_level_branch_topology",
            "status": "not_aligned",
            "observation": "The OR label is present, but its predicted child set is not the two alternative compound branches described by the source. E3 is nested under E2 in parent_id while also listed as a direct child of the top OR gate.",
            "prediction": {
                "gate": root_gate["gate"],
                "child_node_ids": root_gate["child_node_ids"],
                "child_texts": [nodes[node_id]["text"] for node_id in root_gate["child_node_ids"]],
                "parent_ids": {node_id: nodes[node_id].get("parent_id") for node_id in root_gate["child_node_ids"]},
            },
            "reference": {
                "text_authorized_gate": reviews["module-failure-gate"]["text_authorized_gate"],
                "diagram_scope_children": gold_diagram_gates["module-failure-gate"]["child_node_ids"],
                "source_expression": "(single cell exploding AND module vent failure) OR (single cell exploding AND module operates nominally AND sympathetic secondary explosion)",
            },
        },
        {
            "finding_id": "secondary_explosion_scope",
            "status": "not_aligned",
            "observation": "The text-authorized reference marks this scope AND. The model marks its corresponding compound event scope unknown and does not create a separate module-operates-nominally event; the emitted child list contains only sympathetic secondary explosion.",
            "prediction": {
                "output_node_id": secondary_gate["output_node_id"],
                "output_text": nodes[secondary_gate["output_node_id"]]["text"],
                "gate": secondary_gate["gate"],
                "child_texts": [nodes[node_id]["text"] for node_id in secondary_gate["child_node_ids"]],
                "has_separate_module_operates_nominally_node": any("module operating nominally" in item["text"].lower() and item["id"] != secondary_gate["output_node_id"] for item in parsed.get("nodes", [])),
            },
            "reference": {
                "scope_id": "secondary-explosion-gate",
                "text_authorized_gate": secondary_review["text_authorized_gate"],
                "diagram_children": gold_diagram_gates["secondary-explosion-gate"]["child_node_ids"],
            },
        },
        {
            "finding_id": "structural_branch_scope",
            "status": "scope_mismatch_unresolved",
            "observation": "The reference deliberately leaves the exact text-authorized structural gate unknown because the diagram's specific leaf is not stated at that scope in prose. The model also says unknown, but attaches that decision to E2 (single cell explodes) with only E3 as a child; matching the label does not establish matching scope.",
            "prediction": {
                "output_node_id": structural_gate["output_node_id"],
                "output_text": nodes[structural_gate["output_node_id"]]["text"],
                "gate": structural_gate["gate"],
                "child_texts": [nodes[node_id]["text"] for node_id in structural_gate["child_node_ids"]],
            },
            "reference": {
                "scope_id": "module-structural-failure-gate",
                "text_authorized_gate": structural_review["text_authorized_gate"],
                "unknown_reason": structural_review["unknown_reason"],
                "diagram_output_node": gold_diagram_gates["module-structural-failure-gate"]["output_node_id"],
            },
        },
        {
            "finding_id": "tree_hierarchy_contract",
            "status": "blocked" if not tree_contract["valid"] else "passed",
            "observation": "Gate scopes are the sole hierarchy source. Any legacy parent_id is checked against that projection and is never repaired; the original model output remains unchanged.",
            "prediction": {
                "hierarchy_owner": tree_contract["hierarchy_owner"],
                "valid": tree_contract["valid"],
                "blockers": tree_contract["blockers"],
                "output_mutated": tree_contract["output_mutated"],
            },
            "reference": {"policy": "reject_conflict_preserve_raw_output"},
        },
        {
            "finding_id": "source_quote_matching",
            "status": "passed_literal_matching_only",
            "observation": "All eight emitted evidence quotes are literal substrings of the model-input source text. This verifies quote matching, not that a quote supports the full semantic claim or tree topology.",
            "prediction": {"quote_count": len(quotes), "literal_matches": valid_quotes},
            "reference": {"source_segment_count": len(packet["model_input"]["source_segments"])},
        },
    ]

    return {
        "artifact_type": "fta_event_scope_qualitative_dev_comparison",
        "artifact_version": "v2",
        "comparison_date": "2026-09-29",
        "review_method": "offline_post_run_qualitative_comparison",
        "reviewer_role": "AI engineering review; not a human domain expert",
        "case": {
            "packet_id": packet_id,
            "source_cluster_id": run["case"]["source_cluster_id"],
            "exposure_status": "seen_development_only",
            "model_input_sha256": input_hash,
        },
        "reference_provenance": {
            "gold_path": str(GOLD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "reviewer_role": gold["text_gate_reviews"][0]["review_provenance"]["reviewer_role"],
            "formal_human_expert_gold": False,
            "diagram_gate_labels_used_as_text_gold": False,
        },
        "model_run": {
            "run_path": str(RUN_PATH.relative_to(ROOT)).replace("\\", "/"),
            "assessment_path": str(ASSESSMENT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "requested_model": run["request"]["requested_model"],
            "prompt_version": run["request"]["prompt_version"],
            "request_count": run["request"]["request_count"],
            "retry_count": run["request"]["retry_count"],
            "machine_quote_check_count": assessment["output_assessment"]["quote_checks"],
            "machine_invalid_quote_count": assessment["output_assessment"]["invalid_quotes"],
        },
        "findings": findings,
        "summary": {
            "semantic_tree_status": "not_accepted_for_fta_preview",
            "tree_hierarchy_contract": {
                "status": "blocked" if not tree_contract["valid"] else "passed",
                "hierarchy_owner": tree_contract["hierarchy_owner"],
                "blocker_count": len(tree_contract["blockers"]),
                "output_mutated": tree_contract["output_mutated"],
            },
            "quantitative_score": None,
            "accuracy_or_generalization_claim_allowed": False,
            "gold_modified": False,
            "database_or_production_written": False,
            "fta_ready": False,
            "production_ready": False,
            "limitations": [
                "One already-seen Development case only; qualitative error analysis, no accuracy/F1/calibration score.",
                "Reference labels were AI-role-reviewed, not human-expert signed or formal Gold.",
                "Literal quote matching does not establish semantic entailment or correct gate scope.",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    hierarchy_finding = next(item for item in report["findings"] if item["finding_id"] == "tree_hierarchy_contract")
    lines = [
        "# NASA Figure 7 v3 开发样例：离线语义对照",
        "",
        f"日期：{report['comparison_date']}  ",
        f"样本：`{report['case']['packet_id']}`（已见 Development；单样例）  ",
        "结论：**当前候选树语义未通过，不接受为可用 FTA Preview 树。**",
        "",
        "本报告是模型运行后的定性错误分析，不计算准确率、F1、校准或泛化指标。参考标签由 AI 角色审核，非真人领域专家签署、非正式 Gold。比较只使用 `text_gate_reviews` 作为文本授权门型依据；没有把图示门型直接当作原文真值。Gold 未修改。",
        "",
        "## 结果",
        "",
        "| 检查项 | 结果 | 说明 |",
        "| --- | --- | --- |",
        f"| 层级结构合同 | {'阻断' if hierarchy_finding['status'] == 'blocked' else '通过'} | gate scopes 唯一负责层级；检测到 {len(hierarchy_finding['prediction']['blockers'])} 个 blocker；不修复原始输出 |",
        "| 顶事件文字 | 对齐 | 模型与输入包一致 |",
        "| 顶层分支结构 | 不对齐 | OR 标签虽一致，但没有表达两个复合分支；E3 同时作为 E2 子节点和根 OR 直接子项 |",
        "| 次生爆炸作用域 | 不对齐 | 参考文本标签为 AND；模型输出 unknown，且未把“模块正常运行”建成独立子事件 |",
        "| 结构失效作用域 | scope 不匹配/仍不确定 | 参考文本授权标签为 unknown；模型也输出 unknown，但作用域挂在“单体爆炸”上，不能算正确匹配 |",
        f"| 原文引文逐字匹配 | {report['model_run']['machine_quote_check_count']}/{report['model_run']['machine_quote_check_count']} | 只验证引用字符串能在输入中找到，不证明引用支持完整语义或树拓扑 |",
        "",
        "## 关键问题",
        "",
        "原文描述的是两个由 OR 连接的复合条件：`(单体爆炸 AND 模块排气口失效) OR (单体爆炸 AND 模块正常运行 AND 次生爆炸)`。模型的根 OR 却直接连接 `单体爆炸`、`排气口失效`、以及一个合并了“正常运行+次生爆炸”的事件；同时 `parent_id` 与 gate scope 推导出的父子关系冲突。新结构合同因此阻断该树，保留原模型 JSON，不自动修复或重新挂接节点。",
        "",
        "因此，JSON 可解析、结构字段合法、8 条引文都能回到原文，只能说明输出技术上可处理、引用可定位；不能说明因果分支和局部门建对了。",
        "",
        "## 边界",
        "",
        "- 不重跑模型，不调整提示词，不修改参考 Gold。",
        "- 层级以 gate scope 为唯一来源；若旧 `parent_id` 与其冲突，只阻断并记录 blocker，绝不自动选择其一或改写原输出。",
        "- 新版评测 prompt 尚未提交模型运行；本次只是对已保存 v3 输出增加离线合同检查。",
        "- 不把单个已见开发样例用作模型成绩或 Final 验证。",
        "- `fta_ready=false`、`production_ready=false` 保持不变。",
        "- 下一步若需改生成逻辑，先针对这些错误建立明确结构表示和回归断言，再使用新的未见来源验证；本样例之后只能作为开发回归。",
        "",
        f"机器可读记录：`{REPORT_JSON_PATH.relative_to(ROOT).as_posix()}`。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the checked-in comparison artifacts")
    args = parser.parse_args()
    report = build_report()
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    rendered_md = render_markdown(report)
    if args.check:
        if not REPORT_JSON_PATH.exists() or REPORT_JSON_PATH.read_text(encoding="utf-8") != rendered_json:
            parser.exit(1, "qualitative comparison JSON is stale\n")
        if not REPORT_MD_PATH.exists() or REPORT_MD_PATH.read_text(encoding="utf-8") != rendered_md:
            parser.exit(1, "qualitative comparison Markdown is stale\n")
        print(json.dumps({"status": "current", "findings": len(report["findings"]), "semantic_tree_status": report["summary"]["semantic_tree_status"]}, ensure_ascii=False))
        return 0
    REPORT_JSON_PATH.write_text(rendered_json, encoding="utf-8", newline="\n")
    REPORT_MD_PATH.write_text(rendered_md, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "json": str(REPORT_JSON_PATH), "markdown": str(REPORT_MD_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
