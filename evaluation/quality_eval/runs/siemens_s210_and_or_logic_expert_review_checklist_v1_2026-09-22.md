# Siemens S210 AND OR 逻辑门专家审核清单 v1

> 本清单只审核同一故障下多个已确认因果子节点之间的逻辑关系。不能因为存在多个原因就自动判定为 OR，也不能因为多个条件同时出现在原文中就自动判定为 AND。

## 审核规则

1. 先确认子原因集合是否完整：`complete`、`incomplete` 或 `unknown`。
2. 只有原文或领域规则明确支持多个子原因任一成立即可触发故障时，才标记 `OR`。
3. 只有原文或领域规则明确支持多个条件必须同时成立时，才标记 `AND`。
4. 证据不足时标记 `unknown`，不得为了生成树而猜测。
5. `overall_decision=approve` 仅允许在子原因集合、证据和逻辑门都可接受时使用。

## 可填写枚举

| 字段 | 可填写值 |
|---|---|
| `child_set_complete` | `complete` / `incomplete` / `unknown` |
| `logic_gate` | `AND` / `OR` / `unknown` / `not_applicable` |
| `evidence_support` | `supported` / `partial` / `unsupported` |
| `overall_decision` | `approve` / `revise` / `reject` / `cannot_determine` |

## S210-LOGIC-CAND-001 · A01069

- 目标故障：A01069 · Parameter backup and device incompatible
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-002`：The parameter backup on the memory card and the drive unit do not match.
   - 证据：`SIEMENS_S210_2019_A01069:cause:2`，The parameter backup on the memory card and the drive unit do not match.
2. `S210-CAUSAL-V2-001`：Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.
   - 证据：`SIEMENS_S210_2019_A01069:cause:3`，Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---

## S210-LOGIC-CAND-002 · A01631

- 目标故障：A01631 · motor holding brake/SBC configuration not practical
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-003`：A configuration of motor holding brake and SBC was detected that is not practical.
   - 证据：`SIEMENS_S210_2019_A01631:cause:3`，A configuration of motor holding brake and SBC was detected that is not practical.
2. `S210-CAUSAL-V2-002`：No motor holding brake available and SBC enabled.
   - 证据：`SIEMENS_S210_2019_A01631:cause:6`，No motor holding brake available" (p1215 = 0) and "SBC" enabled

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---

## S210-LOGIC-CAND-003 · A01981

- 目标故障：A01981 · Maximum number of controllers exceeded
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-007`：A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections
   - 证据：`SIEMENS_S210_2019_A01981:cause:3`，A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections
2. `S210-CAUSAL-V2-005`：number of RT connections exceeded
   - 证据：`SIEMENS_S210_2019_A01981:cause:4`，number of RT connections exceeded
3. `S210-CAUSAL-V2-006`：number of IRT connections exceeded
   - 证据：`SIEMENS_S210_2019_A01981:cause:5`，number of IRT connections exceeded

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---

## S210-LOGIC-CAND-004 · A07094

- 目标故障：A07094 · General parameter limit violation
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-008`：violation of a parameter limit
   - 证据：`SIEMENS_S210_2019_A07094:cause:2`，violation of a parameter limit
2. `S210-CAUSAL-V2-007`：Minimum limit violated
   - 证据：`SIEMENS_S210_2019_A07094:cause:3`，Minimum limit violated
3. `S210-CAUSAL-V2-008`：Maximum limit violated
   - 证据：`SIEMENS_S210_2019_A07094:cause:4`，Maximum limit violated

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---

## S210-LOGIC-CAND-005 · A30714

- 目标故障：A30714 · Safely-Limited Speed exceeded
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-011`：The drive had moved faster than that specified by the velocity limit value.
   - 证据：`SIEMENS_S210_2019_A30714:cause:3`，The drive had moved faster than that specified by the velocity limit value.
2. `S210-CAUSAL-V2-009`：SLS1 exceeded.
   - 证据：`SIEMENS_S210_2019_A30714:cause:4`，SLS1 exceeded.
3. `S210-CAUSAL-V2-010`：SLS2 exceeded.
   - 证据：`SIEMENS_S210_2019_A30714:cause:5`，SLS2 exceeded.
4. `S210-CAUSAL-V2-011`：SLS3 exceeded.
   - 证据：`SIEMENS_S210_2019_A30714:cause:6`，SLS3 exceeded.
5. `S210-CAUSAL-V2-012`：SLS4 exceeded.
   - 证据：`SIEMENS_S210_2019_A30714:cause:7`，SLS4 exceeded.
6. `S210-CAUSAL-V2-013`：Encoder limit frequency exceeded.
   - 证据：`SIEMENS_S210_2019_A30714:cause:8`，Encoder limit frequency exceeded.

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---

## S210-LOGIC-CAND-006 · F01611

- 目标故障：F01611 · Defect in a monitoring channel
- 系统预设：`unknown`（不代表结论）

### 候选子原因

1. `S210-CAUSAL-015`：Stop request from another monitoring channel
   - 证据：`SIEMENS_S210_2019_F01611:cause:3`，Stop request from another monitoring channel
2. `S210-CAUSAL-V2-014`：Watchdog timer has expired
   - 证据：`SIEMENS_S210_2019_F01611:cause:4`，Watchdog timer has expired
3. `S210-CAUSAL-V2-015`：The signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650)
   - 证据：`SIEMENS_S210_2019_F01611:cause:5`，the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650)
4. `S210-CAUSAL-V2-016`：Via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than or equal to the discrepancy time (p9650)
   - 证据：`SIEMENS_S210_2019_F01611:cause:6`，via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than or equal to the discrepancy time (p9650)

### 专家填写

- child_set_complete：
- logic_gate：
- evidence_support：
- overall_decision：
- 审核意见：

---
