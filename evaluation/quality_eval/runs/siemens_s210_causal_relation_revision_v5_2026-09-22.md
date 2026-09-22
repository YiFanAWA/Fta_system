# Siemens S210 因果关系修订确认清单 v5

本清单只处理第五批审核中的 2 条 `revise` 候选。建议文本和建议证据不是预填 Gold，必须由刘武专家重新确认。

- 审核专家：刘武
- 当前状态：`pending_expert_revision`
- 通过门禁：`approve` + `causal` + `source_to_target` + `causes` + `fta_eligible=true`

## 1. A01691 / CR-CAND-V5-007

- 故障描述：Ti and To unsuitable for PN cycle
- 原候选原因：`No isochronous PROFINET: The PN clock cycle must be at least 4x the current controller clock cycle.`
- 当前专家结论：`revise`
- 专家意见：非等时 PROFINET 分支明确给出 PN clock cycle 的约束，结合上位 Cause 可确认不满足该约束会形成该告警；但当前候选写成“必须至少为 4 倍”的规范要求，而不是实际违规条件。建议规范化为“PN clock cycle is less than 4× the current controller clock cycle”后再入正式 Gold。
- 建议规范化原因：`PN clock cycle is less than 4× the current controller clock cycle`
- 建议证据处理：保留原 Cause 证据，并确认该规范要求应规范化为实际违规条件。

### 原文

```text
A01691 SI Motion: Ti and To unsuitable for PN cycle
Reaction: NONE
Acknowledge: NONE
Cause: The configured times for PROFINET communication are not permitted and the PN cycle is used as the actual value
acquisition cycle for the safe movement monitoring functions:
Isochronous PROFINET:
The sum of Ti and To is too high for the selected PN cycle. The PN clock cycle should be at least 1 current controller cycle
greater than the sum of Ti and To.
No isochronous PROFINET:
The PN clock cycle must be at least 4x the current controller clock cycle.
Notice:
If this alarm is not observed, then message A01711 or A30711 – with the value 1020 ... 1021 – can sporadically occur.
Remedy: Configure Ti and To low so that they are suitable for the PN cycle or increase the PN cycle time.
```

### 专家重新填写

- `causal_status`：
- `direction`：
- `relation_type`：
- `fta_eligible`：
- `overall_decision`：
- `final_cause_text`：
- `evidence_reference`：
- `evidence_text`：
- `evidence_start/end`：
- `expert_reason`：
- `reviewer/reviewed_at`：

## 2. A01782 / CR-CAND-V5-021

- 故障描述：SBT brake test incorrect control
- 原候选原因：`The brake is not configured in p10202. There is a brake test configuration error.`
- 当前专家结论：`revise`
- 专家意见：当前候选文本是“brake 未在 p10202 配置/存在配置错误”，但本条证据引用实际指向 Bit 0 的“resetting the brake test selection”，候选与证据不一致。完整原文的 Bit 2 确实含有该候选语义，但在修正 evidence reference/offset 并重新核验前不得进入 Gold 或 FTA。
- 建议规范化原因：`The brake is not configured in configured p10202. There is a brake test configuration error.`
- 建议证据处理：将证据改指向完整原文 Bit 2，而不是当前 Bit 0 的 resetting the brake test selection。

### 原文

```text
A01782 SBT brake test incorrect control
Reaction: NONE
Acknowledge: NONE
Cause: The brake test was canceled as a result of incorrect control.
Alarm value (r2124, interpret binary):
Alarm value 0:
The brake test was canceled as a result of a fault (brake opening time or brake closing time exceeded).
Bit 0:
The safe brake test was canceled by resetting the brake test selection.
Bit 1:
The safe brake test was canceled by resetting the brake test start.
Bit 2:
The brake is not configured in configured p10202.
There is a brake test configuration error. In this case, alarm A01785 is also output.
Note:
SBT: Safe Brake Test
See also: p10202 (SI Motion SBT brake)
Remedy: - check parameterization of the brake test (p10202).
- check as to whether alarm A01785 is present, and if so, evaluate.
- carry out a safe acknowledgment.
- if required, restart the brake test.
```

### 专家重新填写

- `causal_status`：
- `direction`：
- `relation_type`：
- `fta_eligible`：
- `overall_decision`：
- `final_cause_text`：
- `evidence_reference`：
- `evidence_text`：
- `evidence_start/end`：
- `expert_reason`：
- `reviewer/reviewed_at`：
