# Siemens S210 因果关系修订确认单 v4-A01730

## 使用说明

本单仅用于复核第四批审核中的 1 条 `revise` 候选，不是预填 Gold。请专家根据完整原文和证据独立确认；专家确认前不得将该候选写入正式因果 Gold 或 FTA。

- 审核专家：刘武
- 故障码：`A01730`
- 候选编号：`CR-CAND-V4-029`
- 当前状态：`pending_expert_revision`

## 原始候选

- 目标故障：`A01730` — Reference block for dynamic Safely-Limited Speed invalid
- 原候选原因：`requested, invalid reference block`
- 原关系：`causes` / `source_to_target`
- 原 FTA 资格：`proposed_not_confirmed`（尚未获得专家确认）

## 原文与证据

证据引用：
- `SIEMENS_S210_2019_A01730:cause:4`："requested, invalid reference block"，字符位置 426–460

原文：

```text
A01730 SI Motion P1: Reference block for dynamic Safely-Limited Speed invalid
Reaction: NONE
Acknowledge: NONE
Cause: The reference block transferred via PROFIsafe is negative.
A reference block is used to generate a referred velocity limit value based on the reference quantity "Velocity limit value
SLS1" (p9531[0]).
The drive is stopped by the configured stop response (p9563[0]).
Message value (r2124, interpret decimal):
requested, invalid reference block.
Remedy: In the PROFIsafe telegram, input data S_SLS_LIMIT_IST must be corrected.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
```

## 修订提示

专家上一轮意见指出：原候选原因未完整表达 Cause 段落的语义。建议核对下列规范化表达，但不得视为预先批准：

> `PROFIsafe transferred reference block is negative`

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
