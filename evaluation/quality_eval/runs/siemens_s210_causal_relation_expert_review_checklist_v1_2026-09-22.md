# Siemens S210 因果关系候选专家审核清单 v1

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。候选关系由现有 Gold 的 `causes` 字段和原文证据生成；`causes` 字段本身不等于已证明的因果关系。

## 清单状态

- 审核状态：`pending_expert_review`
- 预计审核专家：刘武
- 候选数量：30 条
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

### CR-CAND-001 · A01006

- 来源记录：`SIEMENS_S210_2019_A01006`（序号 28）
- 故障描述：Firmware update for DRIVE-CLiQ component required
- 候选原因节点：No suitable firmware or firmware version in the component for operation with the Control Unit
- 目标故障实体：`A01006` · Firmware update for DRIVE-CLiQ component required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01006:cause:7`，字符位置 `164-257`
- 证据原文：> no suitable firmware or firmware version in the component for operation with the Control Unit

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01006 Firmware update for DRIVE-CLiQ component required
Reaction: NONE
Acknowledge: NONE
Cause: The firmware of a DRIVE-CLiQ component must be updated as there is no suitable firmware or firmware version in the
component for operation with the Control Unit.
Alarm value (r2124, interpret decimal):
Component number of the DRIVE-CLiQ component.
Remedy: Update the firmware using the commissioning tool:
The firmware version of all of the components on the "Version overview" page can be read in the Project Navigator under
"Configuration" of the associated drive unit and an appropriate firmware update can be carried out.
Firmware update via parameter:
- take the component number from the alarm value and enter into p7828.
- start the firmware download with p7829 = 1.
```

---

### CR-CAND-002 · A01069

- 来源记录：`SIEMENS_S210_2019_A01069`（序号 None）
- 故障描述：Parameter backup and device incompatible
- 候选原因节点：The parameter backup on the memory card and the drive unit do not match.
- 目标故障实体：`A01069` · Parameter backup and device incompatible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01069:cause:2`，字符位置 `88-160`
- 证据原文：> The parameter backup on the memory card and the drive unit do not match.

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

### CR-CAND-003 · A01631

- 来源记录：`SIEMENS_S210_2019_A01631`（序号 None）
- 故障描述：motor holding brake/SBC configuration not practical
- 候选原因节点：A configuration of motor holding brake and SBC was detected that is not practical.
- 目标故障实体：`A01631` · motor holding brake/SBC configuration not practical
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01631:cause:3`，字符位置 `106-188`
- 证据原文：> A configuration of motor holding brake and SBC was detected that is not practical.

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

### CR-CAND-004 · A01699

- 来源记录：`SIEMENS_S210_2019_A01699`（序号 None）
- 故障描述：Test stop for STO required
- 候选原因节点：The time set in p9659 for the forced checking procedure (test stop) for the 'STO' function has been exceeded.
- 目标故障实体：`A01699` · Test stop for STO required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01699:cause:5`，字符位置 `81-189`
- 证据原文：> The time set in p9659 for the forced checking procedure (test stop) for the "STO" function has been exceeded

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01699 SI P1: Test stop for STO required
Reaction: NONE
Acknowledge: NONE
Cause: The time set in p9659 for the forced checking procedure (test stop) for the "STO" function has been exceeded. A new forced
checking procedure is required.
After the next time the "STO" function is deselected, the message is withdrawn and the monitoring time is reset.
Note:
- this message does not result in a safety stop response.
- the test must be performed within a defined, maximum time interval (p9659) in order to comply with the requirements as
laid down in the standards for timely fault detection and the conditions to calculate the failure rates of safety functions (PFH
value). Operation beyond this maximum time period is permissible if it can be ensured that the forced checking procedure
is performed before persons enter the hazardous area and who are depending on the safety functions correctly functioning.
See also: p9659 (SI forced checking procedure timer), r9660 (SI forced checking procedure remaining time)
Remedy: Select STO and then deselect again.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-005 · A01780

- 来源记录：`SIEMENS_S210_2019_A01780`（序号 None）
- 故障描述：SBT When selected, the brake is closed
- 候选原因节点：When selecting the brake test or starting the brake test, the brake was not open
- 目标故障实体：`A01780` · SBT When selected, the brake is closed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01780:cause:3`，字符位置 `86-166`
- 证据原文：> When selecting the brake test or starting the brake test, the brake was not open

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

### CR-CAND-006 · A01799

- 来源记录：`SIEMENS_S210_2019_A01799`（序号 None）
- 故障描述：Acceptance test mode active
- 候选原因节点：The acceptance test mode is active
- 目标故障实体：`A01799` · Acceptance test mode active
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01799:cause:3`，字符位置 `89-123`
- 证据原文：> The acceptance test mode is active

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01799 SI Motion P1: Acceptance test mode active
Reaction: NONE
Acknowledge: NONE
Cause: The acceptance test mode is active.
This means that the setpoint speed limiting is deactivated (r9733).
Remedy: Not necessary.
The message is automatically withdrawn when exiting the acceptance test mode.
Note:
SI: Safety Integrated
```

---

### CR-CAND-007 · A01981

- 来源记录：`SIEMENS_S210_2019_A01981`（序号 None）
- 故障描述：Maximum number of controllers exceeded
- 候选原因节点：A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections
- 目标故障实体：`A01981` · Maximum number of controllers exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01981:cause:3`，字符位置 `90-225`
- 证据原文：> A controller attempts to establish a connection to the drive, and as a consequence exceeds the permitted number of PROFINET connections

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

### CR-CAND-008 · A07094

- 来源记录：`SIEMENS_S210_2019_A07094`（序号 None）
- 故障描述：General parameter limit violation
- 候选原因节点：violation of a parameter limit
- 目标故障实体：`A07094` · General parameter limit violation
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07094:cause:2`，字符位置 `100-130`
- 证据原文：> violation of a parameter limit

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

### CR-CAND-009 · A13021

- 来源记录：`SIEMENS_S210_2019_A13021`（序号 None）
- 故障描述：Licensing for output frequencies > 550 Hz missing
- 候选原因节点：Configuring the converter results in an output frequency greater than 550 Hz
- 目标故障实体：`A13021` · Licensing for output frequencies > 550 Hz missing
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13021:cause:2`，字符位置 `97-173`
- 证据原文：> Configuring the converter results in an output frequency greater than 550 Hz

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13021 Licensing for output frequencies > 550 Hz missing
Reaction: NONE
Acknowledge: NONE
Cause: Configuring the converter results in an output frequency greater than 550 Hz. This function requires a license. The "High
Output Frequency" license is required.
Note:
- in this specific case, the output frequency is limited to 550 Hz.
- the "Trial License" function is not effective for license "High Output Frequency".
Remedy: - enter and activate the license key for "High Output Frequency" and activate (p9920, p9921).
- if necessary operate the motor below the output frequency of 550 Hz.
```

---

### CR-CAND-010 · A30044

- 来源记录：`SIEMENS_S210_2019_A30044`（序号 None）
- 故障描述：Overvolt 24/48 V alarm
- 候选原因节点：For the power unit power supply, the upper threshold has been violated.
- 目标故障实体：`A30044` · Overvolt 24/48 V alarm
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30044:cause:3`，字符位置 `82-153`
- 证据原文：> For the power unit power supply, the upper threshold has been violated.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30044 Power unit: Overvolt 24/48 V alarm
Reaction: NONE
Acknowledge: NONE
Cause: For the power unit power supply, the upper threshold has been violated.
Alarm value (r2124, interpret hexadecimal):
yyxxxx hex: yy = channel, xxxx = voltage [0.1 V]
yy = 0: 24 V power supply
yy = 1: 48 V power supply
Remedy: Check the power supply of the power unit.
502 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-011 · A30714

- 来源记录：`SIEMENS_S210_2019_A30714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：The drive had moved faster than that specified by the velocity limit value.
- 目标故障实体：`A30714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30714:cause:3`，字符位置 `91-166`
- 证据原文：> The drive had moved faster than that specified by the velocity limit value.

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

### CR-CAND-012 · F01000

- 来源记录：`SIEMENS_S210_2019_F01000`（序号 36）
- 故障描述：Internal software error
- 候选原因节点：An internal software error has occurred.
- 目标故障实体：`F01000` · Internal software error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01000:cause:6`，字符位置 `75-115`
- 证据原文：> An internal software error has occurred.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01000 Internal software error
Reaction: OFF2
Acknowledge: POWER ON
Cause: An internal software error has occurred.
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - evaluate fault buffer (r0945).
- carry out a POWER ON (switch-off/switch-on) for all components.
- if required, check the data on the non-volatile memory (e.g. memory card).
- upgrade firmware to later version.
- contact Technical Support.
- replace the Control Unit.
```

---

### CR-CAND-013 · F01030

- 来源记录：`SIEMENS_S210_2019_F01030`（序号 None）
- 故障描述：Sign-of-life failure for master control
- 候选原因节点：For active PC master control, no sign-of-life was received within the monitoring time.
- 目标故障实体：`F01030` · Sign-of-life failure for master control
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01030:cause:3`，字符位置 `94-180`
- 证据原文：> For active PC master control, no sign-of-life was received within the monitoring time.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01030 Sign-of-life failure for master control
Reaction: OFF3
Acknowledge: IMMEDIATELY
Cause: For active PC master control, no sign-of-life was received within the monitoring time.
The master control was returned to the active BICO interconnection.
Remedy: Set the monitoring time higher at the PC or, if required, completely disable the monitoring function.
The monitoring time is set as follows using the commissioning tool:
<Drive> -> Commissioning -> Control panel -> Button "Fetch master control" -> A window is displayed to set the monitoring
time in milliseconds.
Notice:
The monitoring time should be set as short as possible. A long monitoring time means a late response when the
communication fails!
```

---

### CR-CAND-014 · F01044

- 来源记录：`SIEMENS_S210_2019_F01044`（序号 None）
- 故障描述：Descriptive data error
- 候选原因节点：An error was detected when loading the descriptive data saved in the non-volatile memory.
- 目标故障实体：`F01044` · Descriptive data error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01044:cause:3`，字符位置 `78-167`
- 证据原文：> An error was detected when loading the descriptive data saved in the non-volatile memory.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01044 CU: Descriptive data error
Reaction: OFF2
Acknowledge: POWER ON
Cause: An error was detected when loading the descriptive data saved in the non-volatile memory.
Remedy: Replace the memory card or Control Unit.
```

---

### CR-CAND-015 · F01611

- 来源记录：`SIEMENS_S210_2019_F01611`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：Stop request from another monitoring channel
- 目标故障实体：`F01611` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01611:cause:3`，字符位置 `405-449`
- 证据原文：> Stop request from another monitoring channel

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

### CR-CAND-016 · F01656

- 来源记录：`SIEMENS_S210_2019_F01656`（序号 None）
- 故障描述：Parameters monitoring channel 2 error
- 候选原因节点：When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has occurred.
- 目标故障实体：`F01656` · Parameters monitoring channel 2 error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01656:cause:3`，字符位置 `99-222`
- 证据原文：> When accessing the Safety Integrated parameters for monitoring channel 2 in the non-volatile memory, an error has occurred.

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

### CR-CAND-017 · F01674

- 来源记录：`SIEMENS_S210_2019_F01674`（序号 None）
- 故障描述：Safety function not supported by PROFIsafe telegram
- 候选原因节点：The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).
- 目标故障实体：`F01674` · Safety function not supported by PROFIsafe telegram
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01674:cause:3`，字符位置 `117-233`
- 证据原文：> The monitoring function enabled in p9501 and p9601 is not supported by the currently set PROFIsafe telegram (p9611).

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

### CR-CAND-018 · F01694

- 来源记录：`SIEMENS_S210_2019_F01694`（序号 None）
- 故障描述：Firmware version monitoring channel 2 older than monitoring channel 1
- 候选原因节点：The firmware version of monitoring channel 2 is older than monitoring channel 1.
- 目标故障实体：`F01694` · Firmware version monitoring channel 2 older than monitoring channel 1
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01694:cause:3`，字符位置 `138-218`
- 证据原文：> The firmware version of monitoring channel 2 is older than monitoring channel 1.

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

### CR-CAND-019 · F06310

- 来源记录：`SIEMENS_S210_2019_F06310`（序号 None）
- 故障描述：Supply voltage (p0210) incorrectly parameterized
- 候选原因节点：The measured DC voltage lies outside the tolerance range after precharging has been completed (1.16 * p0210 < r0070 < 1.6 * p0210).
- 目标故障实体：`F06310` · Supply voltage (p0210) incorrectly parameterized
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F06310:cause:4`，字符位置 `179-355`
- 证据原文：> the measured DC voltage lies outside the tolerance range after precharging has been completed. The following applies for the tolerance range: 1.16 * p0210 < r0070 < 1.6 * p0210

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F06310 Supply voltage (p0210) incorrectly parameterized
Reaction: NONE
Acknowledge: IMMEDIATELY
478 Operating Instructions, 01/2019, A5E41702836B AC
Cause: For AC/AC drive units, the measured DC voltage lies outside the tolerance range after precharging has been completed.
The following applies for the tolerance range: 1.16 * p0210 < r0070 < 1.6 * p0210
Note:
The fault can only be acknowledged when the drive is switched off.
See also: p0210 (Drive unit line supply voltage)
Remedy: - check the parameterized supply voltage and if required change (p0210).
- check the line supply voltage.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-020 · F07433

- 来源记录：`SIEMENS_S210_2019_F07433`（序号 None）
- 故障描述：Closed-loop control with encoder is not possible as the encoder has not been unparked
- 候选原因节点：The changeover to closed-loop control with encoder is not possible as the encoder has not been unparked.
- 目标故障实体：`F07433` · Closed-loop control with encoder is not possible as the encoder has not been unparked
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F07433:cause:3`，字符位置 `147-251`
- 证据原文：> The changeover to closed-loop control with encoder is not possible as the encoder has not been unparked.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F07433 Drive: Closed-loop control with encoder is not possible as the encoder has not been unparked
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The changeover to closed-loop control with encoder is not possible as the encoder has not been unparked.
Remedy: - check whether the encoder firmware supports the "parking" function (r0481.6 = 1).
- upgrade the firmware.
Note:
For long-stator motors (p3870.0 = 1), the following applies:
The encoder must have completed the unparking procedure (r3875.0 = 1) before a changeover can be made to closed-loop
control with encoder. The encoder is unparked using binector input p3876 = 0/1 signal and remains until a 0 signal in this
state.
```

---

### CR-CAND-021 · F07955

- 来源记录：`SIEMENS_S210_2019_F07955`（序号 None）
- 故障描述：Motor has been changed
- 候选原因节点：The code number of the actual motor with DRIVE-CLiQ does not match the saved number.
- 目标故障实体：`F07955` · Motor has been changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F07955:cause:3`，字符位置 `84-168`
- 证据原文：> The code number of the actual motor with DRIVE-CLiQ does not match the saved number.

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

### CR-CAND-022 · F30003

- 来源记录：`SIEMENS_S210_2019_F30003`（序号 47）
- 故障描述：DC link undervoltage
- 候选原因节点：line supply failure
- 目标故障实体：`F30003` · DC link undervoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30003:cause:8`，字符位置 `154-173`
- 证据原文：> line supply failure

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

### CR-CAND-023 · F30027

- 来源记录：`SIEMENS_S210_2019_F30027`（序号 48）
- 故障描述：Precharging DC link time monitoring
- 候选原因节点：The power unit DC link was not able to be precharged within the expected time.
- 目标故障实体：`F30027` · Precharging DC link time monitoring
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30027:cause:17`，字符位置 `155-233`
- 证据原文：> The power unit DC link was not able to be precharged within the expected time.

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

### CR-CAND-024 · F30078

- 来源记录：`SIEMENS_S210_2019_F30078`（序号 None）
- 故障描述：defective fan or line reactor has overheated
- 候选原因节点：The temperature monitoring of the internal braking resistor or the line reactor has responded.
- 目标故障实体：`F30078` · defective fan or line reactor has overheated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30078:cause:3`，字符位置 `111-205`
- 证据原文：> The temperature monitoring of the internal braking resistor or the line reactor has responded.

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

### CR-CAND-025 · F30657

- 来源记录：`SIEMENS_S210_2019_F30657`（序号 None）
- 故障描述：PROFIsafe telegram number invalid
- 候选原因节点：The PROFIsafe telegram number that has been set is not valid.
- 目标故障实体：`F30657` · PROFIsafe telegram number invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30657:cause:3`，字符位置 `92-153`
- 证据原文：> The PROFIsafe telegram number that has been set is not valid.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30657 SI P2: PROFIsafe telegram number invalid
Reaction: OFF2
Acknowledge: POWER ON
Cause: The PROFIsafe telegram number that has been set is not valid.
When PROFIsafe is enabled (p9601.3 = 1), then telegram number 30 or 901 must be used.
The copy function was not used.
Note:
This fault does not result in a safety stop response.
See also: p9611 (SI PROFIsafe telegram selection), r60022 (PROFIsafe telegram selection)
Remedy: Enter a valid PROFIsafe telegram number (p9611 = 30, 901).
```

---

### CR-CAND-026 · F30701

- 来源记录：`SIEMENS_S210_2019_F30701`（序号 None）
- 故障描述：SS1 initiated
- 候选原因节点：The drive is stopped using SS1.
- 目标故障实体：`F30701` · SS1 initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F30701:cause:3`，字符位置 `82-113`
- 证据原文：> The drive is stopped using SS1.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F30701 SI Motion P2: SS1 initiated
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The drive is stopped using SS1.
As a result of this fault, after the time parameterized in p9556 has expired, or the speed threshold parameterized in p9560
has been fallen below, message F30700 "SI Motion P2: STO initiated" is output.
Possible causes:
- stop request from another monitoring channel.
- subsequent response, following messages: A30714, A30711, A30707, A30716
Remedy: - remove the cause of the fault on the first monitoring channel.
- carry out diagnostics for the active messages (A30714, A30711, A30707, A30716).
Note:
SI: Safety Integrated
SS1: Safe Stop 1
```

---

### CR-CAND-027 · F31138

- 来源记录：`SIEMENS_S210_2019_F31138`（序号 None）
- 故障描述：Fault when determining the position (multiturn)
- 候选原因节点：A position determination fault has occurred in the DRIVE-CLiQ encoder.
- 目标故障实体：`F31138` · Fault when determining the position (multiturn)
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F31138:cause:3`，字符位置 `171-241`
- 证据原文：> A position determination fault has occurred in the DRIVE-CLiQ encoder.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F31138 Encoder 1: Fault when determining the position (multiturn)
Reaction: ENCODER
Acknowledge: PULSE INHIBIT
526 Operating Instructions, 01/2019, A5E41702836B AC
Cause: A position determination fault has occurred in the DRIVE-CLiQ encoder.
Fault value (r0949, interpret binary):
yyxxxxxx hex: yy = encoder version, xxxxxx = bit coding of the fault cause
----------
For yy = 8 (0000 1000 bin), the following applies:
Bit 1: Signal monitoring (sin/cos).
Bit 8: F1 (safety status display) error position word 1.
Bit 9: F2 (safety status display) error position word 2.
Bit 16: LED monitoring.
Bit 17: Fault when determining the position (multiturn).
Bit 23: Temperature outside the limit values.
----------
For yy = 11 (0000 1011 bin), the following applies:
Bit 0: Position word 1 difference between rotation counter and software counter (XC_ERR).
Bit 1: Position word 1 track error of the incremental signals (LIS_ERR).
Bit 2: Position word 1 error when aligning between incremental track signals and absolute value (ST_ERR).
Bit 3: Maximum permissible temperature exceeded (TEMP_ERR).
Bit 4: Power supply overvoltage (MON_OVR_VOLT).
Bit 5: Power supply overcurrent (MON_OVR_CUR).
Bit 6: Power supply undervoltage (MON_UND_VOLT).
Bit 7: Rotation error counter (MT_ERR).
Bit 8: F1 (safety status display) error position word 1.
Bit 9: F2 (safety status display) error position word 2.
Bit 11: Position word 1 status bit: singleturn position OK (ADC_ready).
Bit 12: Position word 1 status bit: rotation counter OK (MT_ready).
Bit 13: Position word 1 memory error (MEM_ERR).
Bit 14: Position word 1 absolute position error (MLS_ERR).
Bit 15: position word 1 LED error, lighting unit error (LED_ERR).
Bit 18: Position word 2 error when aligning between incremental track signals and absolute value (ST_ERR).
Bit 21: Position word 2 memory error (MEM_ERR).
Bit 22: Position word 2 absolute position error (MLS_ERR).
Bit 23: position word 2 LED error, lighting unit error (LED_ERR).
----------
For yy = 14 (0000 1110 bin), the following applies:
Bit 0: Position word 1 temperature outside limit value.
Bit 1: Position word 1 position determination error (multiturn).
Bit 2: Position word 1 FPGA error.
Bit 3: Position word 1 velocity error.
Bit 4: Position word 1 communication error between FPGAs/error in the incremental signal.
Bit 5: Position word 1 timeout absolute value/error when determining the position (singleturn).
Bit 6: Position word 1 internal hardware fault (clock/power monitor IC/power).
Bit 7: Position word 1 internal error (FPGA communication/FPGA parameterization/self-test/software).
Bit 8: F1 (safety status display) error position word 1.
Bit 9: F2 (safety status display) error position word 2.
Bit 16: Position word 2 temperature outside limit value.
Bit 17: Position word 2 position determination error (multiturn).
Bit 18: Position word 2 FPGA error.
Bit 19: Position word 2 velocity error.
Bit 20: Position word 2 communication error between FPGAs.
Bit 21: Position word 2 position determination error (singleturn).
Bit 22: Position word 2 internal hardware fault (clock/power monitor IC/power).
Bit 23: Position word 2 internal error (self-test/software).
----------
Note:
For an encoder version that is not described here, please contact the encoder manufacturer for more detailed information
on the bit coding.
Remedy: - determine the detailed cause of the fault using the fault value.
- if required, replace the DRIVE-CLiQ encoder.
```

---

### CR-CAND-028 · F31836

- 来源记录：`SIEMENS_S210_2019_F31836`（序号 None）
- 故障描述：Send error for DRIVE-CLiQ data
- 候选原因节点：A DRIVE-CLiQ communication error has occurred from the Control Unit to the encoder involved. Data were not able to be sent.
- 目标故障实体：`F31836` · Send error for DRIVE-CLiQ data
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F31836:cause:4`，字符位置 `110-233`
- 证据原文：> A DRIVE-CLiQ communication error has occurred from the Control Unit to the encoder involved. Data were not able to be sent.

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

### CR-CAND-029 · F31887

- 来源记录：`SIEMENS_S210_2019_F31887`（序号 None）
- 故障描述：Component fault
- 候选原因节点：Faulty hardware cannot be excluded.
- 目标故障实体：`F31887` · Component fault
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F31887:cause:4`，字符位置 `183-218`
- 证据原文：> Faulty hardware cannot be excluded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F31887 Encoder 1 DRIVE-CLiQ (CU): Component fault
Reaction: ENCODER
Acknowledge: IMMEDIATELY
Cause: Fault detected on the DRIVE-CLiQ component involved (Sensor Module for encoder 1). Faulty hardware cannot be
excluded.
Fault cause:
32 (= 20 hex):
Error in the telegram header.
35 (= 23 hex):
Receive error: The telegram buffer memory contains an error.
66 (= 42 hex):
Send error: The telegram buffer memory contains an error.
67 (= 43 hex):
Send error: The telegram buffer memory contains an error.
96 (= 60 hex):
Response received too late during runtime measurement.
97 (= 61 hex):
Time taken to exchange characteristic data too long.
Note regarding the message value:
The individual information is coded as follows in the message value (r0949/r2124):
0000yyxx hex: yy = component number, xx = error cause
Remedy: - check the DRIVE-CLiQ wiring (interrupted cable, contacts, ...).
- check the electrical cabinet design and cable routing for EMC compliance
- if required, use another DRIVE-CLiQ socket (p9904).
- replace the component involved.
```

---

### CR-CAND-030 · N30800

- 来源记录：`SIEMENS_S210_2019_N30800`（序号 57）
- 故障描述：Group signal
- 候选原因节点：The power unit has detected at least one fault
- 目标故障实体：`N30800` · Group signal
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_N30800:cause:4`，字符位置 `72-118`
- 证据原文：> The power unit has detected at least one fault

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
N30800 Power unit: Group signal
Reaction: OFF2
Acknowledge: NONE
Cause: The power unit has detected at least one fault.
Remedy: Evaluate the other messages that are presently available.
```

---
