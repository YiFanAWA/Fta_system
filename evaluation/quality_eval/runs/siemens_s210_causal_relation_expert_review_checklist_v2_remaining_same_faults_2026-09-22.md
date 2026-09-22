# Siemens S210 因果关系候选专家审核清单 v2

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。候选关系由现有 Gold 的 `causes` 字段和原文证据生成；`causes` 字段本身不等于已证明的因果关系。

## 清单状态

- 审核状态：`pending_expert_review`
- 预计审核专家：刘武
- 候选数量：66 条
- 来源记录：281 条 S210 故障记录
- 训练用途：否
- FTA 用途：审核完成前禁止使用

## 专家审核规则

1. 先阅读候选原因、故障描述和完整原文，不得仅凭字段名 `Cause` 判定为因果。
2. 只有原文明确表达“该原因/条件导致、触发、引起该故障”的，才可标记 `causal`。
3. 原文只说明共同出现、诊断关联、参数解释或处理建议的，标记 `associated_only`，不要升级为 `causal`。
4. 原文证据不足以判断时标记 `cannot_determine`；引用与候选原因不一致时标记 `unsupported`。
5. 方向必须单独判断：原因节点 → 故障实体才是 `source_to_target`；无法证明方向时用 `unknown` 或 `undirected`。
6. `fta_eligible=true` 只允许用于明确因果、方向清楚、证据直接支持的候选；否则为 `false`。

## 可填写枚举

| 字段 | 可填写值 |
|---|---|
| `causal_status` | `causal` / `associated_only` / `unsupported` / `cannot_determine` |
| `direction` | `source_to_target` / `target_to_source` / `undirected` / `unknown` |
| `relation_type` | `causes` / `caused_by` / `associated_with` / `no_relation` |
| `fta_eligible` | `true` / `false` |
| `overall_decision` | `approve` / `revise` / `reject` / `cannot_determine` |

## 逐条审核

### CR-CAND-V2-001 · A01069

- 来源记录：`SIEMENS_S210_2019_A01069`（序号 None）
- 故障描述：Parameter backup and device incompatible
- 候选原因节点：Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.
- 目标故障实体：`A01069` · Parameter backup and device incompatible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01069:cause:3`，字符位置 `214-331`
- 证据原文：> Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01069 Parameter backup and device incompatible
Reaction: NONE
Acknowledge: NONE
Cause: The parameter backup on the memory card and the drive unit do not match.
The module boots with the factory settings.
Example:
Devices A and B. are not compatible and a memory card with the parameter backup for device A is inserted in device B.
Remedy: - insert a memory card with compatible parameter backup and carry out a POWER ON.
- insert a memory card without parameter backup and carry out a POWER ON.
- save the parameters (p0977 = 1).
```

---

### CR-CAND-V2-002 · A01631

- 来源记录：`SIEMENS_S210_2019_A01631`（序号 None）
- 故障描述：motor holding brake/SBC configuration not practical
- 候选原因节点：No motor holding brake available and SBC enabled.
- 目标故障实体：`A01631` · motor holding brake/SBC configuration not practical
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01631:cause:6`，字符位置 `249-312`
- 证据原文：> No motor holding brake available" (p1215 = 0) and "SBC" enabled

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01631 SI P1: motor holding brake/SBC configuration not practical
Reaction: NONE
Acknowledge: NONE
Cause: A configuration of motor holding brake and SBC was detected that is not practical.
The following configurations can result in this message:
- "No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1).
Remedy: Check the parameterization of the motor holding brake and SBC and correct.
Note:
SBC: Safe Brake Control
See also: p1215 (Motor holding brake configuration), p9602 (SI enable safe brake control)
```

---

### CR-CAND-V2-003 · A01780

- 来源记录：`SIEMENS_S210_2019_A01780`（序号 None）
- 故障描述：SBT When selected, the brake is closed
- 候选原因节点：The internal brake is closed
- 目标故障实体：`A01780` · SBT When selected, the brake is closed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01780:cause:4`，字符位置 `218-246`
- 证据原文：> The internal brake is closed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01780 SBT When selected, the brake is closed
Reaction: NONE
Acknowledge: NONE
Cause: When selecting the brake test or starting the brake test, the brake was not open.
Alarm value (r2124, interpret binary):
Bit 0 = 1:
The internal brake is closed.
Note:
The alarm is also signaled if no brake is configured in p10202.
SBT: Safe Brake Test
See also: p10202 (SI Motion SBT brake)
Remedy: Open the brake and reselect the brake test.
```

---

### CR-CAND-V2-004 · A01780

- 来源记录：`SIEMENS_S210_2019_A01780`（序号 None）
- 故障描述：SBT When selected, the brake is closed
- 候选原因节点：No brake is configured in p10202
- 目标故障实体：`A01780` · SBT When selected, the brake is closed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01780:cause:5`，字符位置 `284-316`
- 证据原文：> no brake is configured in p10202

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01780 SBT When selected, the brake is closed
Reaction: NONE
Acknowledge: NONE
Cause: When selecting the brake test or starting the brake test, the brake was not open.
Alarm value (r2124, interpret binary):
Bit 0 = 1:
The internal brake is closed.
Note:
The alarm is also signaled if no brake is configured in p10202.
SBT: Safe Brake Test
See also: p10202 (SI Motion SBT brake)
Remedy: Open the brake and reselect the brake test.
```

---

### CR-CAND-V2-005 · A01981

- 来源记录：`SIEMENS_S210_2019_A01981`（序号 None）
- 故障描述：Maximum number of controllers exceeded
- 候选原因节点：number of RT connections exceeded
- 目标故障实体：`A01981` · Maximum number of controllers exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01981:cause:4`，字符位置 `391-424`
- 证据原文：> number of RT connections exceeded

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01981 PN: Maximum number of controllers exceeded
Reaction: NONE
Acknowledge: NONE
Cause: A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of
PROFINET connections.
The alarm is automatically withdrawn after approx. 30 seconds.
Alarm value (r2124, interpret hexadecimal):
yyyyxxxx hex: yyyy = info. 1, xxxx = info. 2
Info 1 = 0: number of RT connections exceeded
Info 1 > 0: number of IRT connections exceeded
Info 2: permitted number of connections
Remedy: Check the configuration of the PROFINET controllers.
```

---

### CR-CAND-V2-006 · A01981

- 来源记录：`SIEMENS_S210_2019_A01981`（序号 None）
- 故障描述：Maximum number of controllers exceeded
- 候选原因节点：number of IRT connections exceeded
- 目标故障实体：`A01981` · Maximum number of controllers exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01981:cause:5`，字符位置 `437-471`
- 证据原文：> number of IRT connections exceeded

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01981 PN: Maximum number of controllers exceeded
Reaction: NONE
Acknowledge: NONE
Cause: A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of
PROFINET connections.
The alarm is automatically withdrawn after approx. 30 seconds.
Alarm value (r2124, interpret hexadecimal):
yyyyxxxx hex: yyyy = info. 1, xxxx = info. 2
Info 1 = 0: number of RT connections exceeded
Info 1 > 0: number of IRT connections exceeded
Info 2: permitted number of connections
Remedy: Check the configuration of the PROFINET controllers.
```

---

### CR-CAND-V2-007 · A07094

- 来源记录：`SIEMENS_S210_2019_A07094`（序号 None）
- 故障描述：General parameter limit violation
- 候选原因节点：Minimum limit violated
- 目标故障实体：`A07094` · General parameter limit violation
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07094:cause:3`，字符位置 `181-203`
- 证据原文：> Minimum limit violated

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07094 General parameter limit violation
Reaction: NONE
Acknowledge: NONE
Cause: As a result of the violation of a parameter limit, the parameter value was automatically corrected.
Minimum limit violated --> parameter is set to the minimum value.
Maximum limit violated --> parameter is set to the maximum value.
Alarm value (r2124, interpret decimal):
Parameter number, whose value had to be adapted.
Remedy: Check the adapted parameter values and if required correct.
```

---

### CR-CAND-V2-008 · A07094

- 来源记录：`SIEMENS_S210_2019_A07094`（序号 None）
- 故障描述：General parameter limit violation
- 候选原因节点：Maximum limit violated
- 目标故障实体：`A07094` · General parameter limit violation
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07094:cause:4`，字符位置 `247-269`
- 证据原文：> Maximum limit violated

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07094 General parameter limit violation
Reaction: NONE
Acknowledge: NONE
Cause: As a result of the violation of a parameter limit, the parameter value was automatically corrected.
Minimum limit violated --> parameter is set to the minimum value.
Maximum limit violated --> parameter is set to the maximum value.
Alarm value (r2124, interpret decimal):
Parameter number, whose value had to be adapted.
Remedy: Check the adapted parameter values and if required correct.
```

---

### CR-CAND-V2-009 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS1 exceeded.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:4`，字符位置 `268-282`
- 证据原文：> SLS1 exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30714 SI Motion P2: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive had moved faster than that specified by the velocity limit value. The drive is stopped by the configured stop
response.
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check the limits for the "SLS" function and if required adapt.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
518 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V2-010 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS2 exceeded.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:5`，字符位置 `288-302`
- 证据原文：> SLS2 exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30714 SI Motion P2: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive had moved faster than that specified by the velocity limit value. The drive is stopped by the configured stop
response.
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check the limits for the "SLS" function and if required adapt.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
518 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V2-011 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS3 exceeded.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:6`，字符位置 `308-322`
- 证据原文：> SLS3 exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30714 SI Motion P2: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive had moved faster than that specified by the velocity limit value. The drive is stopped by the configured stop
response.
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check the limits for the "SLS" function and if required adapt.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
518 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V2-012 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS4 exceeded.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:7`，字符位置 `328-342`
- 证据原文：> SLS4 exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30714 SI Motion P2: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive had moved faster than that specified by the velocity limit value. The drive is stopped by the configured stop
response.
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check the limits for the "SLS" function and if required adapt.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
518 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V2-013 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：Encoder limit frequency exceeded.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:8`，字符位置 `349-382`
- 证据原文：> Encoder limit frequency exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30714 SI Motion P2: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive had moved faster than that specified by the velocity limit value. The drive is stopped by the configured stop
response.
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check the limits for the "SLS" function and if required adapt.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
518 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V2-014 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Watchdog timer has expired
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:4`，字符位置 `1083-1109`
- 证据原文：> Watchdog timer has expired

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-015 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：The signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:5`，字符位置 `1193-1314`
- 证据原文：> the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-016 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than or equal to the discrepancy time (p9650)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:6`，字符位置 `1318-1477`
- 证据原文：> via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than or equal to the discrepancy time (p9650)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-017 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Initialization error, change timer / check timer
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:7`，字符位置 `1491-1539`
- 证据原文：> Initialization error, change timer / check timer

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-018 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：CRC error in the SAFETY sector
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:8`，字符位置 `1547-1577`
- 证据原文：> CRC error in the SAFETY sector

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-019 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：CRC error in the ITCM sector
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:9`，字符位置 `1585-1613`
- 证据原文：> CRC error in the ITCM sector

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-020 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Overloading in the ITCM sector has occurred in operation
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:10`，字符位置 `1621-1677`
- 证据原文：> Overloading in the ITCM sector has occurred in operation

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-021 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Internal parameterizing error for CRC calculation
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:11`，字符位置 `1685-1734`
- 证据原文：> Internal parameterizing error for CRC calculation

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-022 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Status of the STO selection for both monitoring channels different
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:12`，字符位置 `1742-1808`
- 证据原文：> Status of the STO selection for both monitoring channels different

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-023 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Feedback signal of STO shutdown for both monitoring channels different
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:13`，字符位置 `1816-1886`
- 证据原文：> Feedback signal of STO shutdown for both monitoring channels different

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-024 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:14`，字符位置 `1962-2064`
- 证据原文：> Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-025 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Status of the STO terminal for both monitoring channels different
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:15`，字符位置 `2072-2137`
- 证据原文：> Status of the STO terminal for both monitoring channels different

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-026 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Error in the PROFIsafe control
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:16`，字符位置 `2154-2184`
- 证据原文：> Error in the PROFIsafe control

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-027 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：A fatal PROFIsafe communication error has occurred
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:17`，字符位置 `2363-2413`
- 证据原文：> A fatal PROFIsafe communication error has occurred

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-028 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Error when evaluating the F parameter. The values of the transferred F parameters do not match the expected values in the PROFIsafe driver
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:18`，字符位置 `2430-2568`
- 证据原文：> error when evaluating the F parameter. The values of the transferred F parameters do not match the expected values in the PROFIsafe driver

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-029 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Destination address and PROFIsafe address are different (F_Dest_Add)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:19`，字符位置 `2576-2644`
- 证据原文：> Destination address and PROFIsafe address are different (F_Dest_Add)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-030 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Destination address not valid (F_Dest_Add)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:20`，字符位置 `2652-2694`
- 证据原文：> Destination address not valid (F_Dest_Add)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-031 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Source address not valid (F_Source_Add)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:21`，字符位置 `2702-2741`
- 证据原文：> Source address not valid (F_Source_Add)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-032 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Watchdog time not valid (F_WD_Time)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:22`，字符位置 `2749-2784`
- 证据原文：> Watchdog time not valid (F_WD_Time)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-033 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Incorrect SIL level (F_SIL)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:23`，字符位置 `2792-2819`
- 证据原文：> Incorrect SIL level (F_SIL)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-034 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Incorrect F-CRC length (F_CRC_Length)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:24`，字符位置 `2827-2864`
- 证据原文：> Incorrect F-CRC length (F_CRC_Length)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-035 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Incorrect F parameter version (F_Par_Version)
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:25`，字符位置 `2872-2917`
- 证据原文：> Incorrect F parameter version (F_Par_Version)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-036 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value calculated in the PROFIsafe driver
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:26`，字符位置 `2925-3069`
- 证据原文：> CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value calculated in the PROFIsafe driver

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-037 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：F parameterization is inconsistent
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:27`，字符位置 `3077-3111`
- 证据原文：> F parameterization is inconsistent

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-038 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in the PROFINET cable
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:28`，字符位置 `3119-3368`
- 证据原文：> A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in the PROFINET cable

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-039 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:29`，字符位置 `3376-3462`
- 证据原文：> A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01611 SI P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: IMMEDIATELY
438 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1. As a result of this fault,
after the parameterized transition time has elapsed (p9658), fault F01600 is output.
Fault value (r0949, interpret decimal):
0: Stop request from another monitoring channel.
1 ... 999:
Number of the cross-compared data that resulted in this fault. This number is also displayed in r9795.
2: SI enable safety functions (p9601). Crosswise data comparison is only carried out for the supported bits.
3: SI SGE changeover discrepancy time (p9650).
4: SI transition time from F01611 to STO (p9658).
5: SI enable Safe Brake Control (p9602).
6: SI Motion enable safety functions (p9501).
7: SI delay time of STO for Safe Stop 1 (p9652).
8: SI PROFIsafe address (p9610).
9: SI debounce time for STO/SBC/SS1 (p9651).
14: SI PROFIsafe telegram selection (p9611).
15: SI PROFIsafe bus failure response (p9612).
1000: Watchdog timer has expired.
Within the time of approx. 5 x p9650, alternatively, the following was defined:
- the signal at F-DI for STO/SS1 continually changes with time intervals less than or equal to the discrepancy time (p9650).
- via PROFIsafe, STO (also as subsequent response) was continually selected and deselected with time intervals less than
or equal to the discrepancy time (p9650).
1001, 1002: Initialization error, change timer / check timer.
1900: CRC error in the SAFETY sector.
1901: CRC error in the ITCM sector.
1902: Overloading in the ITCM sector has occurred in operation.
1903: Internal parameterizing error for CRC calculation.
2000: Status of the STO selection for both monitoring channels different.
2001: Feedback signal of STO shutdown for both monitoring channels different. This value can also subsequently occur as
a result of other faults.
2002: Status of the delay timer SS1 on both monitoring channels are different (status of the timer in p9650).
2003: Status of the STO terminal for both monitoring channels different.
6000 ... 6999:
Error in the PROFIsafe control.
For these fault values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. For p9612 = 1,
the transfer of Failsafe Values is delayed.
6000: A fatal PROFIsafe communication error has occurred.
6064 ... 6071: error when evaluating the F parameter. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
6064: Destination address and PROFIsafe address are different (F_Dest_Add).
6065: Destination address not valid (F_Dest_Add).
6066: Source address not valid (F_Source_Add).
6067: Watchdog time not valid (F_WD_Time).
6068: Incorrect SIL level (F_SIL).
6069: Incorrect F-CRC length (F_CRC_Length).
6070: Incorrect F parameter version (F_Par_Version).
6071: CRC error for the F parameters (CRC1). The transferred CRC value of the F parameters does not match the value
calculated in the PROFIsafe driver.
6072: F parameterization is inconsistent.
6165: A communications error was identified when receiving the PROFIsafe telegram. The fault can also occur if an
inconsistent or out-of-date PROFIsafe telegram has been received after switching the drive off and on or after plugging in
the PROFINET cable.
6166: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
Remedy: For fault value = 1 ... 5 and 7 ... 999:
- check the data that caused the fault.
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 6:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1000:
Check the wiring of the F-DI for STO/SS1 (contact problems).
- PROFIsafe: Resolve contact problems/faults at the PROFINET controller.
- check the discrepancy time, and if required, increase the value (p9650).
For fault value = 1001, 1002:
- carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade the drive software.
For fault value = 1900, 1901, 1902:
- carry out a POWER ON (switch-off/switch-on) for all components.
- replace drive.
- upgrade the drive software.
For fault value = 2000, 2001, 2002, 2003:
- check the discrepancy time, and if required, increase the value (p9650, p9652).
- check the wiring of the safety-relevant inputs (SGE) (contact problems).
- replace drive.
- diagnose the other active faults and resolve the causes.
Note:
This fault can be acknowledged after removing the cause of the error and after correct selection/deselection of STO.
For fault value = 6000:
- carry out a POWER ON (switch-off/switch-on) for all components.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For fault value = 6064:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave.
- check the setting of the PROFIsafe address (p9610). Using the commissioning tool, copy the safety parameters and
confirm the data change.
For fault value = 6065:
- check the setting of the value in the F parameter F_Dest_Add at the PROFIsafe slave. It is not permissible for the
destination address to be either 0 or FFFF!
For fault value = 6066:
- check the setting of the value in the F parameter F_Source_Add at the PROFIsafe slave. It is not permissible for the source
address to be either 0 or FFFF!
For fault value = 6067:
- check the setting of the value in the F parameter F_WD_Time at the PROFIsafe slave. It is not permissible for the watch
time to be 0!
For fault value = 6068:
- check the setting of the value in the F parameter F_SIL at the PROFIsafe slave. The SIL level must correspond to SIL2!
For fault value = 6069:
- check the setting of the value in the F parameter F_CRC_Length at the PROFIsafe slave. The setting of the CRC2 length
is 2-byte CRC in the V1 mode and 3-byte CRC in the V2 mode!
For fault value = 6070:
- check the setting of the value in the F parameter F_Par_Version at the PROFIsafe slave. The value for the F parameter
version is 0 in the V1 mode and 1 in the V2 mode!
440 Operating Instructions, 01/2019, A5E41702836B AC
For fault value = 6071:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and, if required, update.
For fault value = 6072:
- check the settings of the values for the F parameters and, if required, correct.
The following combinations are permissible for F parameters F_CRC_Length and F_Par_Version:
F_CRC_Length = 2-byte CRC and F_Par_Version = 0
F_CRC_Length = 3-byte CRC and F_Par_Version = 1
For fault value = 6165:
- if the fault occurs after powering up or after inserting the PROFINET cable, acknowledge the fault.
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- check whether all F parameters of the drive match the F parameters of the F host.
For fault value = 6166:
- check the configuration and communication at the PROFIsafe slave.
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
- check whether all F parameters of the drive match the F parameters of the F host.
Note:
F-DI: Failsafe Digital Input
SGE: Safety-relevant input
SI: Safety Integrated
SS1: Safe Stop 1
STO: Safe Torque Off
```

---

### CR-CAND-V2-040 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：Safety parameters for monitoring channel 2 corrupted.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:4`，字符位置 `331-384`
- 证据原文：> safety parameters for monitoring channel 2 corrupted.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01656 SI P1: Parameters monitoring channel 2 error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has
occurred.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
129:
- safety parameters for monitoring channel 2 corrupted.
- drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
131: Internal software error on monitoring channel 2.
132: Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
255: Internal software error on monitoring channel 1.
Remedy: - re-commission the safety functions.
- upgrade the drive software.
- replace the memory card or drive.
For fault value = 129:
- activate the safety commissioning mode (p0010 = 95).
- adapt the PROFIsafe address (p9610).
- using the commissioning tool, copy the safety parameters and confirm the data change.
- exit the safety commissioning mode (p0010 = 0).
- save all parameters (copy RAM to ROM).
- carry out a POWER ON (switch-off/switch-on).
For fault value = 132:
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V2-041 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：Drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:5`，字符位置 `387-507`
- 证据原文：> drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01656 SI P1: Parameters monitoring channel 2 error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has
occurred.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
129:
- safety parameters for monitoring channel 2 corrupted.
- drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
131: Internal software error on monitoring channel 2.
132: Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
255: Internal software error on monitoring channel 1.
Remedy: - re-commission the safety functions.
- upgrade the drive software.
- replace the memory card or drive.
For fault value = 129:
- activate the safety commissioning mode (p0010 = 95).
- adapt the PROFIsafe address (p9610).
- using the commissioning tool, copy the safety parameters and confirm the data change.
- exit the safety commissioning mode (p0010 = 0).
- save all parameters (copy RAM to ROM).
- carry out a POWER ON (switch-off/switch-on).
For fault value = 132:
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V2-042 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：Internal software error on monitoring channel 2.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:6`，字符位置 `513-561`
- 证据原文：> Internal software error on monitoring channel 2.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01656 SI P1: Parameters monitoring channel 2 error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has
occurred.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
129:
- safety parameters for monitoring channel 2 corrupted.
- drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
131: Internal software error on monitoring channel 2.
132: Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
255: Internal software error on monitoring channel 1.
Remedy: - re-commission the safety functions.
- upgrade the drive software.
- replace the memory card or drive.
For fault value = 129:
- activate the safety commissioning mode (p0010 = 95).
- adapt the PROFIsafe address (p9610).
- using the commissioning tool, copy the safety parameters and confirm the data change.
- exit the safety commissioning mode (p0010 = 0).
- save all parameters (copy RAM to ROM).
- carry out a POWER ON (switch-off/switch-on).
For fault value = 132:
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V2-043 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:7`，字符位置 `567-665`
- 证据原文：> Communication errors when uploading or downloading the safety parameters for monitoring channel 2.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01656 SI P1: Parameters monitoring channel 2 error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has
occurred.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
129:
- safety parameters for monitoring channel 2 corrupted.
- drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
131: Internal software error on monitoring channel 2.
132: Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
255: Internal software error on monitoring channel 1.
Remedy: - re-commission the safety functions.
- upgrade the drive software.
- replace the memory card or drive.
For fault value = 129:
- activate the safety commissioning mode (p0010 = 95).
- adapt the PROFIsafe address (p9610).
- using the commissioning tool, copy the safety parameters and confirm the data change.
- exit the safety commissioning mode (p0010 = 0).
- save all parameters (copy RAM to ROM).
- carry out a POWER ON (switch-off/switch-on).
For fault value = 132:
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V2-044 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：Internal software error on monitoring channel 1.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:8`，字符位置 `671-719`
- 证据原文：> Internal software error on monitoring channel 1.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01656 SI P1: Parameters monitoring channel 2 error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has
occurred.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
129:
- safety parameters for monitoring channel 2 corrupted.
- drive with enabled safety functions was possibly copied offline using the commissioning tool and the project downloaded.
131: Internal software error on monitoring channel 2.
132: Communication errors when uploading or downloading the safety parameters for monitoring channel 2.
255: Internal software error on monitoring channel 1.
Remedy: - re-commission the safety functions.
- upgrade the drive software.
- replace the memory card or drive.
For fault value = 129:
- activate the safety commissioning mode (p0010 = 95).
- adapt the PROFIsafe address (p9610).
- using the commissioning tool, copy the safety parameters and confirm the data change.
- exit the safety commissioning mode (p0010 = 0).
- save all parameters (copy RAM to ROM).
- carry out a POWER ON (switch-off/switch-on).
For fault value = 132:
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V2-045 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：SS2E via PROFIsafe is not supported (p9501.18).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:4`，字符位置 `350-397`
- 证据原文：> SS2E via PROFIsafe is not supported (p9501.18).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01674 SI Motion P1: Safety function not supported by PROFIsafe telegram
Reaction: OFF2
Acknowledge: POWER ON
Cause: The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret bitwise):
Bit 18 = 1:
SS2E via PROFIsafe is not supported (p9501.18).
Bit 24 = 1:
Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
Bit 25 = 1:
Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
Bit 26 = 1:
Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
Bit 28 = 1:
SCA via PROFIsafe is not supported (p9501.28).
Remedy: - Deselect the monitoring function involved (p9501, p9601).
- set the matching PROFIsafe telegram (p9611).
Note:
SCA: Safe Cam
SI: Safety Integrated
SLS: Safely-Limited Speed
SP: Safe Position
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
STO: Safe Torque Off
```

---

### CR-CAND-V2-046 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:5`，字符位置 `410-479`
- 证据原文：> Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01674 SI Motion P1: Safety function not supported by PROFIsafe telegram
Reaction: OFF2
Acknowledge: POWER ON
Cause: The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret bitwise):
Bit 18 = 1:
SS2E via PROFIsafe is not supported (p9501.18).
Bit 24 = 1:
Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
Bit 25 = 1:
Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
Bit 26 = 1:
Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
Bit 28 = 1:
SCA via PROFIsafe is not supported (p9501.28).
Remedy: - Deselect the monitoring function involved (p9501, p9601).
- set the matching PROFIsafe telegram (p9611).
Note:
SCA: Safe Cam
SI: Safety Integrated
SLS: Safely-Limited Speed
SP: Safe Position
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
STO: Safe Torque Off
```

---

### CR-CAND-V2-047 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:6`，字符位置 `492-562`
- 证据原文：> Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01674 SI Motion P1: Safety function not supported by PROFIsafe telegram
Reaction: OFF2
Acknowledge: POWER ON
Cause: The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret bitwise):
Bit 18 = 1:
SS2E via PROFIsafe is not supported (p9501.18).
Bit 24 = 1:
Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
Bit 25 = 1:
Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
Bit 26 = 1:
Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
Bit 28 = 1:
SCA via PROFIsafe is not supported (p9501.28).
Remedy: - Deselect the monitoring function involved (p9501, p9601).
- set the matching PROFIsafe telegram (p9611).
Note:
SCA: Safe Cam
SI: Safety Integrated
SLS: Safely-Limited Speed
SP: Safe Position
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
STO: Safe Torque Off
```

---

### CR-CAND-V2-048 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:7`，字符位置 `575-642`
- 证据原文：> Gearbox stage switchover via PROFIsafe is not supported (p9501.26).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01674 SI Motion P1: Safety function not supported by PROFIsafe telegram
Reaction: OFF2
Acknowledge: POWER ON
Cause: The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret bitwise):
Bit 18 = 1:
SS2E via PROFIsafe is not supported (p9501.18).
Bit 24 = 1:
Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
Bit 25 = 1:
Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
Bit 26 = 1:
Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
Bit 28 = 1:
SCA via PROFIsafe is not supported (p9501.28).
Remedy: - Deselect the monitoring function involved (p9501, p9601).
- set the matching PROFIsafe telegram (p9611).
Note:
SCA: Safe Cam
SI: Safety Integrated
SLS: Safely-Limited Speed
SP: Safe Position
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
STO: Safe Torque Off
```

---

### CR-CAND-V2-049 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：SCA via PROFIsafe is not supported (p9501.28).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:8`，字符位置 `655-701`
- 证据原文：> SCA via PROFIsafe is not supported (p9501.28).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01674 SI Motion P1: Safety function not supported by PROFIsafe telegram
Reaction: OFF2
Acknowledge: POWER ON
Cause: The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret bitwise):
Bit 18 = 1:
SS2E via PROFIsafe is not supported (p9501.18).
Bit 24 = 1:
Transfer SLS (SG) limit value via PROFIsafe not supported (p9501.24).
Bit 25 = 1:
Transfer safe position (SP) via PROFIsafe is not supported (p9501.25).
Bit 26 = 1:
Gearbox stage switchover via PROFIsafe is not supported (p9501.26).
Bit 28 = 1:
SCA via PROFIsafe is not supported (p9501.28).
Remedy: - Deselect the monitoring function involved (p9501, p9601).
- set the matching PROFIsafe telegram (p9611).
Note:
SCA: Safe Cam
SI: Safety Integrated
SLS: Safely-Limited Speed
SP: Safe Position
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
STO: Safe Torque Off
```

---

### CR-CAND-V2-050 · F01694

- 来源记录：`SIEMENS_S210_2019_F01694`（序号 None）
- 故障描述：Firmware version monitoring channel 2 older than monitoring channel 1
- 候选原因节点：after an automatic firmware update, a POWER ON was not carried out (Alarm A01007)
- 目标故障实体：`F01694` · Firmware version monitoring channel 2 older than monitoring channel 1
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01694:cause:4`，字符位置 `308-389`
- 证据原文：> after an automatic firmware update, a POWER ON was not carried out (Alarm A01007)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01694 SI Motion P1: Firmware version monitoring channel 2 older than monitoring channel 1
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The firmware version of monitoring channel 2 is older than monitoring channel 1.
Note:
This message does not result in a safety stop response.
This message can occur, if after an automatic firmware update, a POWER ON was not carried out (Alarm A01007).
Remedy: Carry out a POWER ON at the drive (switch-off/switch-on).
See also: r9590 (SI Motion version, safe motion monitoring functions)
```

---

### CR-CAND-V2-051 · F07955

- 来源记录：`SIEMENS_S210_2019_F07955`（序号 None）
- 故障描述：Motor has been changed
- 候选原因节点：If available: The code numbers of the bearings, gearbox or brake do not match the saved numbers.
- 目标故障实体：`F07955` · Motor has been changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F07955:cause:4`，字符位置 `169-265`
- 证据原文：> If available: The code numbers of the bearings, gearbox or brake do not match the saved numbers.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F07955 Drive: Motor has been changed
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The code number of the actual motor with DRIVE-CLiQ does not match the saved number. If available: The code numbers
of the bearings, gearbox or brake do not match the saved numbers.
Remedy: Connect the original motor, and switch on the Control Unit again (POWER ON) - or restore the factory settings. The data
for bearings, gearbox and brake are reloaded.
```

---

### CR-CAND-V2-052 · F30003

- 来源记录：`SIEMENS_S210_2019_F30003`（序号 47）
- 故障描述：DC link undervoltage
- 候选原因节点：line supply voltage below the permissible value
- 目标故障实体：`F30003` · DC link undervoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30003:cause:9`，字符位置 `176-223`
- 证据原文：> line supply voltage below the permissible value

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30003 Drive: DC link undervoltage
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The power unit has detected an undervoltage condition in the DC link.
- line supply failure
- line supply voltage below the permissible value.
- line supply infeed failed or interrupted.
- line phase interrupted.
Remedy: - check the line supply voltage
- check the line supply infeed and observe the fault messages relating to it (if there are any)
- check the line supply phases.
- check the line supply voltage setting (p0210).
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-053 · F30003

- 来源记录：`SIEMENS_S210_2019_F30003`（序号 47）
- 故障描述：DC link undervoltage
- 候选原因节点：line supply infeed failed or interrupted
- 目标故障实体：`F30003` · DC link undervoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30003:cause:10`，字符位置 `227-267`
- 证据原文：> line supply infeed failed or interrupted

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30003 Drive: DC link undervoltage
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The power unit has detected an undervoltage condition in the DC link.
- line supply failure
- line supply voltage below the permissible value.
- line supply infeed failed or interrupted.
- line phase interrupted.
Remedy: - check the line supply voltage
- check the line supply infeed and observe the fault messages relating to it (if there are any)
- check the line supply phases.
- check the line supply voltage setting (p0210).
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-054 · F30003

- 来源记录：`SIEMENS_S210_2019_F30003`（序号 47）
- 故障描述：DC link undervoltage
- 候选原因节点：line phase interrupted
- 目标故障实体：`F30003` · DC link undervoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30003:cause:11`，字符位置 `271-293`
- 证据原文：> line phase interrupted

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30003 Drive: DC link undervoltage
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The power unit has detected an undervoltage condition in the DC link.
- line supply failure
- line supply voltage below the permissible value.
- line supply infeed failed or interrupted.
- line phase interrupted.
Remedy: - check the line supply voltage
- check the line supply infeed and observe the fault messages relating to it (if there are any)
- check the line supply phases.
- check the line supply voltage setting (p0210).
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-055 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：There is no line supply voltage connected.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:18`，字符位置 `237-279`
- 证据原文：> There is no line supply voltage connected.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-056 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The line contactor/line side switch has not been closed.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:19`，字符位置 `283-339`
- 证据原文：> The line contactor/line side switch has not been closed.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-057 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The line supply voltage is too low.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:20`，字符位置 `343-378`
- 证据原文：> The line supply voltage is too low.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-058 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：Line supply voltage incorrectly set.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:7`，字符位置 `379-426`
- 证据原文：> 4) Line supply voltage incorrectly set (p0210).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-059 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The precharging resistors are overheated as there were too many precharging operations per time unit.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:21`，字符位置 `430-531`
- 证据原文：> The precharging resistors are overheated as there were too many precharging operations per time unit.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-060 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The precharging resistors are overheated as the DC link capacitance is too high.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:22`，字符位置 `535-615`
- 证据原文：> The precharging resistors are overheated as the DC link capacitance is too high.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-061 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The precharging resistors are overheated because when there is no 'ready for operation' of the infeed unit, power is taken from the DC link.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:11`，字符位置 `616-769`
- 证据原文：> 7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit, power is taken from the DC link.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-062 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the Braking Module.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:23`，字符位置 `773-907`
- 证据原文：> The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the Braking Module

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-063 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The DC link has either a ground fault or a short-circuit.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:24`，字符位置 `912-969`
- 证据原文：> The DC link has either a ground fault or a short-circuit.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30027 Power unit: Precharging DC link time monitoring
Reaction: OFF2
Acknowledge: IMMEDIATELY
498 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The power unit DC link was not able to be precharged within the expected time.
1) There is no line supply voltage connected.
2) The line contactor/line side switch has not been closed.
3) The line supply voltage is too low.
4) Line supply voltage incorrectly set (p0210).
5) The precharging resistors are overheated as there were too many precharging operations per time unit.
6) The precharging resistors are overheated as the DC link capacitance is too high.
7) The precharging resistors are overheated because when there is no "ready for operation" (r0863.0) of the infeed unit,
power is taken from the DC link.
8) The precharging resistors are overheated as the line contactor was closed during the DC link fast discharge through the
Braking Module.
9) The DC link has either a ground fault or a short-circuit.
Fault value (r0949, interpret binary):
yyyyxxxx hex:
yyyy = power unit state
0: Fault status (wait for OFF and fault acknowledgment).
1: Restart inhibit (wait for OFF).
2: Overvoltage condition detected -> change into the fault state.
3: Undervoltage condition detected -> change into the fault state.
4: Wait for bridging contactor to open -> change into the fault state.
5: Wait for bridging contactor to open -> change into restart inhibit.
6: Wait for bypass contactor to open
7: Commissioning.
8: Ready for precharging.
9: Precharging started, DC link voltage lower than the minimum switch-on voltage
10: Precharging, DC link voltage end of precharging still not detected
11: Wait for the end of the de-bounce time of the main contactor after precharging has been completed.
12: Precharging completed, ready for pulse enable.
13: It was detected that the STO terminal was energized at the power unit
xxxx = Missing internal enable signals, power unit (inverted bit-coded, FFFF hex -> all internal enable signals available)
Bit 0: Power supply of the IGBT gating shut down.
Bit 1: Ground fault detected.
Bit 2: Peak current intervention.
Bit 3: I2t exceeded.
Bit 4. Thermal model overtemperature calculated.
Bit 5: (heat sink, gating module, power unit) overtemperature measured.
Bit 6: Reserved.
Bit 7: Overvoltage detected.
Bit 8: Power unit has completed precharging, ready for pulse enable.
Bit 9: STO terminal missing.
Bit 10: Overcurrent detected.
Bit 11: Armature short-circuit active.
Bit 12: DRIVE-CLiQ fault active.
Bit 13: Vce fault detected, transistor de-saturated due to overcurrent/short-circuit.
Bit 14: Undervoltage detected.
See also: p0210 (Drive unit line supply voltage)
Remedy: In general:
- check the line supply voltage at the input terminals.
- check the line supply voltage setting (p0210).
For 5):
- carefully observe the permissible precharging frequency (refer to the appropriate Manual).
For 6):
- check the total capacitance of the DC link and reduce in accordance with the maximum permissible DC link capacitance
if necessary (refer to the appropriate Manual).
For 7):
- interconnect the ready-for-operation signal from the infeed unit (r0863.0) in the enable logic of the drives connected to this
DC link
For 8):
- check the connections of the external line contactor. The line contactor must be open during DC link fast discharge.
For 9):
- check the DC link for ground faults or short circuits.
For 11):
- check the DC link voltage of the infeed (r0070) and Motor Modules (r0070).
If the DC link voltage generated by the infeed (or external) is not displayed for the Motor Modules (r0070), then a fuse has
ruptured in the Motor Module.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V2-064 · F30078

- 来源记录：`SIEMENS_S210_2019_F30078`（序号 None）
- 故障描述：defective fan or line reactor has overheated
- 候选原因节点：an overtemperature condition of the internal braking resistor can only be initiated as a result of a defective fan.
- 目标故障实体：`F30078` · defective fan or line reactor has overheated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30078:cause:4`，字符位置 `304-419`
- 证据原文：> an overtemperature condition of the internal braking resistor can only be initiated as a result of a defective fan.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30078 Power unit: defective fan or line reactor has overheated
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The temperature monitoring of the internal braking resistor or the line reactor has responded. In addition to the OFF2
response, the use of the internal braking resistor was inhibited.
Note:
- an overtemperature condition of the internal braking resistor can only be initiated as a result of a defective fan.
- an overtemperature condition of the line reactor can occur when a DC link coupling is used – and if the power when
motoring, which is fed into the DC link - is not evenly distributed across the rectifiers of the power units.
Remedy: - check the converter fan and replace if necessary.
- reduce the motoring power.
```

---

### CR-CAND-V2-065 · F30078

- 来源记录：`SIEMENS_S210_2019_F30078`（序号 None）
- 故障描述：defective fan or line reactor has overheated
- 候选原因节点：an overtemperature condition of the line reactor can occur when a DC link coupling is used – and if the power when motoring, which is fed into the DC link - is not evenly distributed across the rectifiers of the power units.
- 目标故障实体：`F30078` · defective fan or line reactor has overheated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30078:cause:5`，字符位置 `422-646`
- 证据原文：> an overtemperature condition of the line reactor can occur when a DC link coupling is used – and if the power when motoring, which is fed into the DC link - is not evenly distributed across the rectifiers of the power units.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30078 Power unit: defective fan or line reactor has overheated
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The temperature monitoring of the internal braking resistor or the line reactor has responded. In addition to the OFF2
response, the use of the internal braking resistor was inhibited.
Note:
- an overtemperature condition of the internal braking resistor can only be initiated as a result of a defective fan.
- an overtemperature condition of the line reactor can occur when a DC link coupling is used – and if the power when
motoring, which is fed into the DC link - is not evenly distributed across the rectifiers of the power units.
Remedy: - check the converter fan and replace if necessary.
- reduce the motoring power.
```

---

### CR-CAND-V2-066 · F31836

- 来源记录：`SIEMENS_S210_2019_F31836`（序号 None）
- 故障描述：Send error for DRIVE-CLiQ data
- 候选原因节点：Telegram type does not match send list.
- 目标故障实体：`F31836` · Send error for DRIVE-CLiQ data
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F31836:cause:5`，字符位置 `262-301`
- 证据原文：> Telegram type does not match send list.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F31836 Encoder 1 DRIVE-CLiQ: Send error for DRIVE-CLiQ data
Reaction: ENCODER
Acknowledge: IMMEDIATELY
Cause: A DRIVE-CLiQ communication error has occurred from the Control Unit to the encoder involved. Data were not able to be
sent.
Fault cause:
65 (= 41 hex):
Telegram type does not match send list.
Note regarding the message value:
The individual information is coded as follows in the message value (r0949/r2124):
0000yyxx hex: yy = component number, xx = error cause
Remedy: Carry out a POWER ON.
```

---
