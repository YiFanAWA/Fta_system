# Siemens S210 FTA Preview v1

> 这是带证据的受限范围预览，不是生产 FTA，也不是 281 条故障的完整故障树。

- 预览树数量：5
- 排除事件数量：1
- 生产可用：否
- 因果自动推断：否

## S210-FTA-PREVIEW-001 · A01069

- 目标故障：Parameter backup and device incompatible
- 逻辑门：`OR`
- 逻辑审核来源：`S210-LOGIC-CAND-001`

### 子原因和证据

1. `S210-CAUSAL-002`：The parameter backup on the memory card and the drive unit do not match.
   - 证据 `SIEMENS_S210_2019_A01069:cause:2`：The parameter backup on the memory card and the drive unit do not match.
2. `S210-CAUSAL-V2-001`：Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.
   - 证据 `SIEMENS_S210_2019_A01069:cause:3`：Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.

---

## S210-FTA-PREVIEW-002 · A01631

- 目标故障：motor holding brake/SBC configuration not practical
- 逻辑门：`OR`
- 逻辑审核来源：`S210-LOGIC-CAND-002`

### 子原因和证据

1. `S210-CAUSAL-003`：A configuration of motor holding brake and SBC was detected that is not practical.
   - 证据 `SIEMENS_S210_2019_A01631:cause:3`：A configuration of motor holding brake and SBC was detected that is not practical.
2. `S210-CAUSAL-V2-002`：No motor holding brake available and SBC enabled.
   - 证据 `SIEMENS_S210_2019_A01631:cause:6`：No motor holding brake available" (p1215 = 0) and "SBC" enabled

---

## S210-FTA-PREVIEW-003 · A01981

- 目标故障：Maximum number of controllers exceeded
- 逻辑门：`OR`
- 逻辑审核来源：`S210-LOGIC-CAND-003`

### 子原因和证据

1. `S210-CAUSAL-007`：A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections
   - 证据 `SIEMENS_S210_2019_A01981:cause:3`：A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections
2. `S210-CAUSAL-V2-005`：number of RT connections exceeded
   - 证据 `SIEMENS_S210_2019_A01981:cause:4`：number of RT connections exceeded
3. `S210-CAUSAL-V2-006`：number of IRT connections exceeded
   - 证据 `SIEMENS_S210_2019_A01981:cause:5`：number of IRT connections exceeded

---

## S210-FTA-PREVIEW-004 · A07094

- 目标故障：General parameter limit violation
- 逻辑门：`OR`
- 逻辑审核来源：`S210-LOGIC-CAND-004`

### 子原因和证据

1. `S210-CAUSAL-008`：violation of a parameter limit
   - 证据 `SIEMENS_S210_2019_A07094:cause:2`：violation of a parameter limit
2. `S210-CAUSAL-V2-007`：Minimum limit violated
   - 证据 `SIEMENS_S210_2019_A07094:cause:3`：Minimum limit violated
3. `S210-CAUSAL-V2-008`：Maximum limit violated
   - 证据 `SIEMENS_S210_2019_A07094:cause:4`：Maximum limit violated

---

## S210-FTA-PREVIEW-005 · A30714

- 目标故障：Safely-Limited Speed exceeded
- 逻辑门：`OR`
- 逻辑审核来源：`S210-LOGIC-CAND-005`

### 子原因和证据

1. `S210-CAUSAL-011`：The drive had moved faster than that specified by the velocity limit value.
   - 证据 `SIEMENS_S210_2019_A30714:cause:3`：The drive had moved faster than that specified by the velocity limit value.
2. `S210-CAUSAL-V2-009`：SLS1 exceeded.
   - 证据 `SIEMENS_S210_2019_A30714:cause:4`：SLS1 exceeded.
3. `S210-CAUSAL-V2-010`：SLS2 exceeded.
   - 证据 `SIEMENS_S210_2019_A30714:cause:5`：SLS2 exceeded.
4. `S210-CAUSAL-V2-011`：SLS3 exceeded.
   - 证据 `SIEMENS_S210_2019_A30714:cause:6`：SLS3 exceeded.
5. `S210-CAUSAL-V2-012`：SLS4 exceeded.
   - 证据 `SIEMENS_S210_2019_A30714:cause:7`：SLS4 exceeded.
6. `S210-CAUSAL-V2-013`：Encoder limit frequency exceeded.
   - 证据 `SIEMENS_S210_2019_A30714:cause:8`：Encoder limit frequency exceeded.

---

## 未纳入预览的事件

- `F01611`：logic_gate=`unknown`，decision=`cannot_determine`；logic gate is unknown or event is not approved
