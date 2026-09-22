"""Build the S210 RAG boundary expert-review bundle.

The source dataset contains engineering expectations.  This script deliberately
keeps those expectations separate from the blank expert fields so the output
cannot be mistaken for expert Gold data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KNOWLEDGE_STATUSES = (
    "supported",
    "supported_with_warning",
    "insufficient_evidence",
    "out_of_domain",
)
EXPECTED_ACTIONS = ("answer", "answer_with_warning", "ask_information", "reject")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("queries"), list):
        raise ValueError("boundary draft must be an object with a queries array")
    return value


def _cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def build_template(dataset: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in dataset["queries"]:
        rows.append(
            {
                "query_id": item.get("query_id"),
                "question": item.get("question"),
                "engineering_category": item.get("category"),
                "engineering_expectation": {
                    "knowledge_status": item.get("expected_knowledge_status"),
                    "response_policy": item.get("expected_response_policy"),
                    "answer_allowed": item.get("answer_allowed"),
                },
                "expert_review": {
                    "expert_status": "pending",
                    "expected_knowledge_status": None,
                    "answer_allowed": None,
                    "warning_required": None,
                    "need_additional_info": None,
                    "missing_information": [],
                    "expected_action": None,
                    "expert_reason": "",
                    "reviewer": "刘武",
                    "reviewed_at": "",
                },
            }
        )
    return {
        "dataset_info": {
            "name": "siemens_s210_rag_boundary_gold_v1",
            "version": "v1",
            "status": "pending_expert_review",
            "gold_source": "pending_named_expert_review",
            "not_for_training": True,
            "reviewer": "刘武",
            "source_draft": dataset.get("dataset_info", {}).get("name"),
        },
        "allowed_values": {
            "expected_knowledge_status": list(KNOWLEDGE_STATUSES),
            "expected_action": list(EXPECTED_ACTIONS),
            "expert_status": ["pending", "reviewed"],
        },
        "review_instructions": [
            "逐条依据 S210 知识库边界和问题本身判断，不把工程预期当成专家结论。",
            "supported 只表示当前问题有足够身份/证据可以正常回答；不是说答案中的每个事实都已验证。",
            "supported_with_warning 表示可以检索和回答，但必须降低确定性并提示补充信息。",
            "insufficient_evidence 表示不能给出确定诊断，必须请求补充信息。",
            "out_of_domain 表示问题明确超出 Siemens S210 当前知识库，不进入 S210 故障诊断回答。",
            "若选择 answer_allowed=true，必须说明为什么当前信息足够；若选择 false，必须填写 missing_information 或拒答理由。",
            "不要依据模型输出或当前实现行为审核；这里只审核边界策略的专家标准。",
        ],
        "rows": rows,
    }


def build_markdown(template: dict[str, Any]) -> str:
    info = template["dataset_info"]
    lines = [
        "# Siemens S210 RAG 边界策略专家审核清单 v1",
        "",
        f"> 审核专家：{info['reviewer']}",
        "> 审核状态：待专家填写；本文件不是 Gold 数据，不提供预审结论。",
        "> 审核对象：S210 RAG 在“可回答、需警告、证据不足、库外问题”之间的边界行为。",
        "",
        "## 一、审核目的",
        "",
        "请判断系统面对每个用户问题时，是否可以基于当前 Siemens S210 知识库给出回答，以及回答应采用的安全策略。这里只审核边界决策，不审核 embedding、检索排序、Reranker 或具体回答文本。",
        "",
        "## 二、标注规则",
        "",
        "| expected_knowledge_status | 判定标准 |",
        "| --- | --- |",
        "| `supported` | 有明确 S210/Siemens/SINAMICS 身份、故障码、参数或足够明确的 S210 故障实体，可正常回答。 |",
        "| `supported_with_warning` | 属于技术故障问题，可以检索和回答，但缺少型号、故障码、参数或组件等关键信息，必须降低确定性并提示补充。 |",
        "| `insufficient_evidence` | 信息过少，不能定位到具体故障，禁止输出确定诊断，必须请求补充信息。 |",
        "| `out_of_domain` | 明确属于当前 S210 知识库之外的领域，不进入 S210 故障诊断回答。 |",
        "",
        "| expected_action | 与状态的关系 |",
        "| --- | --- |",
        "| `answer` | 正常回答，仍须遵守证据引用合同。 |",
        "| `answer_with_warning` | 可以回答，但必须明确不确定性并列出建议补充信息。 |",
        "| `ask_information` | 先请求信息，不给确定故障诊断。 |",
        "| `reject` | 明确告知超出 S210 知识库范围，不生成该领域诊断。 |",
        "",
        "## 三、专家填写要求",
        "",
    ]
    for instruction in template["review_instructions"]:
        lines.append(f"- {instruction}")
    lines += [
        "",
        "每条记录必须填写：",
        "- `expected_knowledge_status`：四选一；",
        "- `answer_allowed`：是否允许给出知识库回答；",
        "- `warning_required`：是否必须带风险/不确定性提示；",
        "- `need_additional_info`：是否需要用户补充信息；",
        "- `missing_information`：需要补充的具体字段；",
        "- `expected_action`：四选一；",
        "- `expert_reason`：至少一句可复核理由；",
        "- `expert_status=reviewed`、审核人和日期。",
        "",
        "## 四、逐条审核表",
        "",
    ]
    for index, row in enumerate(template["rows"], start=1):
        engineering = row["engineering_expectation"]
        lines += [
            f"### {index}. {row['query_id']}",
            "",
            f"**用户问题：** {_cell(row['question'])}",
            "",
            f"**工程分类（仅供追踪，不是专家结论）：** `{_cell(row['engineering_category'])}`",
            f"**工程预期（仅供对照，不得直接复制）：** `{_cell(engineering['knowledge_status'])}` / `{_cell(engineering['response_policy'])}` / answer_allowed=`{engineering['answer_allowed']}`",
            "",
            "| 专家字段 | 填写值 |",
            "| --- | --- |",
            "| expert_status | `reviewed` |",
            "| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |",
            "| answer_allowed | `true` / `false` |",
            "| warning_required | `true` / `false` |",
            "| need_additional_info | `true` / `false` |",
            "| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |",
            "| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |",
            "| expert_reason | 说明依据和边界判断 |",
            "| reviewer | `刘武` |",
            "| reviewed_at | `YYYY-MM-DD` |",
            "",
            "**专家填写：**",
            "```text",
            "expected_knowledge_status:",
            "answer_allowed:",
            "warning_required:",
            "need_additional_info:",
            "missing_information:",
            "expected_action:",
            "expert_reason:",
            "```",
            "",
        ]
    lines += [
        "## 五、审核完成后的交付",
        "",
        "请将填写结果保存为 JSON，并保留 `query_id` 与原问题不变。使用项目校验脚本检查后，才能生成 Boundary Gold v1 和安全边界指标。未完成专家审核前，不得把工程预期字段改名为 Gold。",
        "",
        "建议文件名：`siemens_s210_rag_boundary_expert_gold_v1.json`。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--template-output", required=True)
    args = parser.parse_args()

    dataset = _load(Path(args.dataset))
    template = build_template(dataset)
    markdown_path = Path(args.markdown_output)
    template_path = Path(args.template_output)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(build_markdown(template), encoding="utf-8")
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"query_count": len(template["rows"]), "markdown": str(markdown_path), "template": str(template_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
