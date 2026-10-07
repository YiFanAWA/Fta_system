#!/usr/bin/env python3
"""Build a non-scoring qualitative review of the single seen v4 Dev run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.event_scope_tree_contract import validate_event_scope_tree  # noqa: E402
from evaluation.quality_eval.fta_event_scope_packet_contract import model_input_payload  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v2 import PACKET_PATH  # noqa: E402
from evaluation.quality_eval.public_sources.run_fta_event_scope_model_v4 import (  # noqa: E402
    ASSESSMENT_PATH,
    RUN_PATH,
    _evidence_check,
)


GOLD_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"
REPORT_JSON_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.json"
REPORT_MD_PATH = ROOT / "evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md"


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
    model_input = model_input_payload(packet)
    parsed = run.get("model_output", {}).get("parsed_json")
    if not isinstance(parsed, dict):
        raise ValueError("v4 run has no parsed JSON object")
    input_hash = run.get("case", {}).get("model_input_sha256")
    if packet.get("packet_id") != gold.get("packet_id") or packet.get("packet_id") != run.get("case", {}).get("packet_id"):
        raise ValueError("packet identity mismatch")
    if input_hash != gold.get("model_input_sha256") or input_hash != run.get("case", {}).get("model_input_sha256"):
        raise ValueError("model input hash mismatch")
    if run.get("case", {}).get("exposure_status") != "seen_development_only":
        raise ValueError("v4 comparison is restricted to the already-seen Development packet")
    request = run.get("request", {})
    if request.get("request_count") != 1 or request.get("retry_count") != 0:
        raise ValueError("v4 run must represent exactly one request and no retry")
    if request.get("gold_included_in_model_input") is not False:
        raise ValueError("Gold must not be visible to the model")

    structure = validate_event_scope_tree(parsed)
    evidence = _evidence_check(parsed, model_input)
    stored = assessment.get("output_assessment", {})
    if structure != stored.get("structure_contract") or evidence != stored.get("evidence_location_check"):
        raise ValueError("saved assessment does not match the current offline contracts")

    nodes = {node["id"]: node for node in parsed["nodes"] if isinstance(node, dict) and isinstance(node.get("id"), str)}
    gates = parsed["gates"]
    root_gate = next((gate for gate in gates if gate.get("output_node_id") == structure.get("root_node_id")), None)
    if root_gate is None:
        raise ValueError("v4 output has no scope for its root event")
    reviews = {item["scope_id"]: item for item in gold.get("text_gate_reviews", [])}
    root_reference = reviews.get("module-failure-gate")
    if not isinstance(root_reference, dict):
        raise ValueError("missing AI-reviewed text reference for root scope")
    reviewer_role = root_reference.get("review_provenance", {}).get("reviewer_role")
    if reviewer_role != "ai_role_review":
        raise ValueError("this report is explicitly scoped to the recorded AI-role-reviewed references")

    findings = [
        {
            "finding_id": "request_boundary",
            "status": "passed",
            "observation": "One v4 request completed with zero retries; thinking was disabled and Gold was excluded from model-visible input.",
            "request_count": request["request_count"],
            "retry_count": request["retry_count"],
            "finish_reason": request.get("finish_reason"),
        },
        {
            "finding_id": "tree_hierarchy_contract",
            "status": "blocked" if not structure["valid"] else "passed",
            "observation": "The non-mutating gate-scope hierarchy contract blocks invalid structures and never repairs the saved output.",
            "hierarchy_owner": structure["hierarchy_owner"],
            "blockers": structure["blockers"],
            "output_mutated": structure["output_mutated"],
        },
        {
            "finding_id": "evidence_location",
            "status": "passed_literal_unique_matching_only" if not evidence["blockers"] else "blocked",
            "observation": "Literal unique segment matching checks citation location only; it does not prove semantic entailment.",
            "checked": evidence["checked"],
            "valid": evidence["valid"],
            "blockers": evidence["blockers"],
        },
        {
            "finding_id": "root_gate_vs_ai_text_review",
            "status": "label_disagreement",
            "observation": "The model abstained with unknown on the root scope, while the AI-role-reviewed text reference labels the root scope OR. This is one seen-case qualitative disagreement, not a human-expert error score.",
            "model": {"scope_id": root_gate.get("scope_id"), "gate": root_gate.get("gate"), "output_node_text": nodes.get(root_gate.get("output_node_id"), {}).get("text")},
            "reference": {
                "scope_id": "module-failure-gate",
                "text_authorized_gate": root_reference.get("text_authorized_gate"),
                "reviewer_role": reviewer_role,
                "evidence_quote": root_reference.get("evidence", {}).get("quote"),
            },
        },
        {
            "finding_id": "remaining_gate_scope_coverage",
            "status": "qualitative_scope_mismatch_not_scored",
            "observation": "All emitted gate labels are unknown. The prediction does not emit the AI-role-reviewed secondary-explosion AND decision; internal scope IDs do not provide a validated one-to-one mapping to the reference scopes, so no gate accuracy is computed.",
            "predicted_gate_counts": {label: sum(gate.get("gate") == label for gate in gates) for label in ("AND", "OR", "unknown")},
            "reference_text_gate_counts": {label: sum(item.get("text_authorized_gate") == label for item in reviews.values()) for label in ("AND", "OR", "unknown")},
            "scope_mapping": "not_established",
        },
    ]
    return {
        "artifact_type": "fta_event_scope_qualitative_dev_comparison",
        "artifact_version": "v1",
        "comparison_date": "2026-09-29",
        "review_method": "offline_non_scoring_comparison_after_single_v4_run",
        "reviewer_role": "AI engineering review; not a human domain expert",
        "case": {
            "packet_id": packet["packet_id"],
            "source_cluster_id": run["case"]["source_cluster_id"],
            "exposure_status": "seen_development_only",
            "model_input_sha256": input_hash,
        },
        "model_run": {
            "run_path": str(RUN_PATH.relative_to(ROOT)).replace("\\", "/"),
            "assessment_path": str(ASSESSMENT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "requested_model": request.get("requested_model"),
            "prompt_version": request.get("prompt_version"),
            "prompt_sha256": request.get("prompt_sha256"),
            "request_count": request["request_count"],
            "retry_count": request["retry_count"],
            "strict_json_parsed": stored.get("strict_json_parsed") is True,
        },
        "reference_provenance": {
            "gold_path": str(GOLD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "reviewer_role": reviewer_role,
            "formal_human_expert_gold": False,
            "diagram_gate_labels_used_as_text_gold": False,
        },
        "findings": findings,
        "summary": {
            "semantic_tree_status": "not_accepted_for_fta_preview",
            "structure_status": parsed.get("structure_status"),
            "structure_contract_status": "blocked" if not structure["valid"] else "passed",
            "structure_blocker_count": len(structure["blockers"]),
            "literal_evidence_location": f"{evidence['valid']}/{evidence['checked']}",
            "all_predicted_gate_labels_unknown": all(gate.get("gate") == "unknown" for gate in gates),
            "quantitative_score": None,
            "accuracy_or_calibration_claim_allowed": False,
            "gold_modified": False,
            "database_or_production_written": False,
            "fta_ready": False,
            "production_ready": False,
            "limitations": [
                "One already-seen Development case only; qualitative error analysis, no accuracy/F1/calibration score.",
                "Reference labels were AI-role-reviewed, not human-expert signed or formal Gold.",
                "Literal quote matching checks citation location, not semantic entailment.",
                "Model and reference gate scopes do not have a validated one-to-one mapping; do not compute gate accuracy.",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    findings = {item["finding_id"]: item for item in report["findings"]}
    root = findings["root_gate_vs_ai_text_review"]
    hierarchy = findings["tree_hierarchy_contract"]
    evidence = findings["evidence_location"]
    return "\n".join([
        "# NASA Figure 7 v4 开发样例：离线定性复核",
        "",
        f"日期：{report['comparison_date']}  ",
        f"样本：`{report['case']['packet_id']}`（已见 Development；单样例）  ",
        "结论：**结构合同阻断，不接受为 FTA Preview 树。**",
        "",
        "本报告只做单样例离线定性检查。参考标签由 AI 角色审核，非真人专家 Gold；不计算准确率、F1、校准或泛化指标；图示门标签没有被当作原文语义金标。",
        "",
        "## 运行与合同结果",
        "",
        "| 项目 | 结果 | 边界 |",
        "| --- | --- | --- |",
        f"| 请求 | {report['model_run']['request_count']} 次，重试 {report['model_run']['retry_count']} 次；`finish_reason={findings['request_boundary']['finish_reason']}` | thinking disabled；输入不含 Gold |",
        f"| 严格 JSON | {'通过' if report['model_run']['strict_json_parsed'] else '未通过'} | 仅格式检查 |",
        f"| 层级合同 | {'阻断' if hierarchy['status'] == 'blocked' else '通过'}；{len(hierarchy['blockers'])} 个 blocker | `S2` 只有 1 个直接子项，原输出不修复 |",
        f"| 引文位置 | {evidence['valid']}/{evidence['checked']} 唯一匹配 | 只证明原文定位，不证明语义蕴含 |",
        "| 门型输出 | 3 个 scope 均为 `unknown` | 根 scope 与 AI 角色审核的 OR 标签不同；次级 AND 未被输出；无准确率结论 |",
        "",
        "## 定性发现",
        "",
        f"根 scope：模型输出 `{root['model']['gate']}`，AI 角色审核的文本参考为 `{root['reference']['text_authorized_gate']}`。这是单个已见样例上的标签分歧，不是真人专家结论。模型给全部 scope 都选择 unknown，说明当前提示词在本例偏保守。",
        "",
        "结构上，根 scope 连接 E2 与 E4，但 E2 的 S2 scope 只有 E3 一个 child，因此整棵树按合同阻断。模型确实产生了引用段落定位，但这不能补救层级不完整。内部 scope 与参考 Gold scope 没有经过验证的一对一映射，所以不计算门型准确率。",
        "",
        "## 限制与后续",
        "",
        "- v4 仅是一轮 seen-Dev 对照；其输出不进入 Gold、数据库或生产服务。",
        "- 不能据此宣称一般性模型改善或退化；只能确认这一个输出的合同和观察结果。",
        "- 后续若调整 prompt，Figure 7 应留作开发回归；最终泛化需用未见来源独立验证。",
        "- `fta_ready=false`、`production_ready=false` 保持不变。",
        "",
        f"机器可读记录：`{REPORT_JSON_PATH.relative_to(ROOT).as_posix()}`。",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the checked-in comparison artifacts")
    args = parser.parse_args()
    report = build_report()
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    rendered_md = render_markdown(report)
    if args.check:
        if not REPORT_JSON_PATH.exists() or REPORT_JSON_PATH.read_text(encoding="utf-8") != rendered_json:
            parser.exit(1, "v4 qualitative comparison JSON is stale\n")
        if not REPORT_MD_PATH.exists() or REPORT_MD_PATH.read_text(encoding="utf-8") != rendered_md:
            parser.exit(1, "v4 qualitative comparison Markdown is stale\n")
        print(json.dumps({"status": "current", "findings": len(report["findings"]), "tree_status": report["summary"]["semantic_tree_status"]}, ensure_ascii=False))
        return 0
    REPORT_JSON_PATH.write_text(rendered_json, encoding="utf-8", newline="\n")
    REPORT_MD_PATH.write_text(rendered_md, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "findings": len(report["findings"]), "tree_status": report["summary"]["semantic_tree_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
