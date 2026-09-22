# Siemens S210 Causal Relation Revision Confirmation v6

本确认单只处理 A01691 和 A01782 两条待复核 revise 候选。建议修订不是 Gold 结论，必须由刘武专家逐条确认或替换。确认完成前，两条记录不得进入 Causal Relation Gold v7 或 FTA。

- 审核专家：刘武
- 当前状态：`pending_expert_revision`
- 审核日期：
- 通过门禁：`approve` + `causal` + `source_to_target` + `causes` + `fta_eligible=true` + 最终原因与证据一致

## 填写说明

1. 先核对完整原文和当前证据，不要只看建议文本。
2. `approve` 只有在最终原因、证据定位和因果关系都可接受时才可选择。
3. 选择 `revise` 时，必须填写最终原因文本、证据引用和修改理由；记录继续保持 pending。
4. 选择 `reject` 时，必须填写排除理由；记录不会进入 Gold。

## 1. A01691 CR-CAND-V5-007

- 故障描述：Ti and To unsuitable for PN cycle
- 当前候选原因：`No isochronous PROFINET: The PN clock cycle must be at least 4x the current controller clock cycle.`
- 上一轮结论：`revise`
- 上一轮专家意见：非等时 PROFINET 分支明确给出 PN clock cycle 的约束，结合上位 Cause 可确认不满足该约束会形成该告警；但当前候选写成“必须至少为 4 倍”的规范要求，而不是实际违规条件。建议规范化为“PN clock cycle is less than 4× the current controller clock cycle”后再入正式 Gold。
- 建议原因文本：`PN clock cycle is less than 4× the current controller clock cycle`
- 建议证据处理：保留原 Cause 证据，并确认该规范要求应规范化为实际违规条件。

### 当前证据

```json
[
  {
    "evidence_id": "SIEMENS_S210_2019_A01691:cause:5",
    "source_id": "input_text",
    "field": "cause",
    "quote": "No isochronous PROFINET:\nThe PN clock cycle must be at least 4x the current controller clock cycle.",
    "start": 447,
    "end": 546,
    "location": "",
    "source_span_index": 5
  }
]
```

### 完整原文

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

### 专家最终填写

| 字段 | 填写值 |
|---|---|
| causal_status |  |
| direction |  |
| relation_type |  |
| fta_eligible |  |
| overall_decision |  |
| final_cause_text |  |
| evidence_reference |  |
| evidence_text |  |
| evidence_start |  |
| evidence_end |  |
| expert_reason |  |
| reviewer | 刘武 |
| reviewed_at |  |

## 2. A01782 CR-CAND-V5-021

- 故障描述：SBT brake test incorrect control
- 当前候选原因：`The brake is not configured in p10202. There is a brake test configuration error.`
- 上一轮结论：`revise`
- 上一轮专家意见：当前候选文本是“brake 未在 p10202 配置/存在配置错误”，但本条证据引用实际指向 Bit 0 的“resetting the brake test selection”，候选与证据不一致。完整原文的 Bit 2 确实含有该候选语义，但在修正 evidence reference/offset 并重新核验前不得进入 Gold 或 FTA。
- 建议原因文本：`The brake is not configured in configured p10202. There is a brake test configuration error.`
- 建议证据处理：将证据改指向完整原文 Bit 2，而不是当前 Bit 0 的 resetting the brake test selection。

### 当前证据

```json
[
  {
    "evidence_id": "SIEMENS_S210_2019_A01782:cause:4",
    "source_id": "input_text",
    "field": "cause",
    "quote": "The safe brake test was canceled by resetting the brake test selection.",
    "start": 307,
    "end": 378,
    "location": "",
    "source_span_index": 4
  }
]
```

### 完整原文

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

### 专家最终填写

| 字段 | 填写值 |
|---|---|
| causal_status |  |
| direction |  |
| relation_type |  |
| fta_eligible |  |
| overall_decision |  |
| final_cause_text |  |
| evidence_reference |  |
| evidence_text |  |
| evidence_start |  |
| evidence_end |  |
| expert_reason |  |
| reviewer | 刘武 |
| reviewed_at |  |

## 汇总确认

- 两条记录是否均已完成复核：
- 可进入 Gold v7 的记录：
- 仍需暂缓的记录：
- 专家补充说明：
