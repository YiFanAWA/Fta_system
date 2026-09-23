# Siemens S210 因果关系候选专家审核清单 v6

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。本批从 v1-v5 已审核候选之外的原因中生成，并保留现有 Gold 的原文证据；`causes` 字段本身不等于已证明的因果关系。

## 清单状态

- 审核状态：`pending_expert_review`
- 预计审核专家：刘武
- 候选数量：50 条
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

### CR-CAND-V6-001 · A01016

- 来源记录：`SIEMENS_S210_2019_A01016`（序号 None）
- 故障描述：Firmware changed
- 候选原因节点：File too many.
- 目标故障实体：`A01016` · Firmware changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01016:cause:5`，字符位置 `342-356`
- 证据原文：> File too many.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01016 Firmware changed
Reaction: NONE
Acknowledge: NONE
Cause: At least one firmware file in the directory was illegally changed on the non-volatile memory (memory card/device memory)
with respect to the version when shipped from the factory.
Alarm value (r2124, interpret decimal):
0: Checksum of one file is incorrect.
1: File missing.
2: File too many.
3: Incorrect firmware version.
4: Incorrect checksum of the back-up file.
Remedy: For the non-volatile memory for the firmware (memory card/device memory), restore the delivery condition.
Note:
The file involved can be read out using parameter r9925.
The status of the firmware check is displayed using r9926.
```

---

### CR-CAND-V6-004 · A01711

- 来源记录：`SIEMENS_S210_2019_A01711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：For message values 3, 44 ... 57, 232 and 1-encoder system, differently set encoder parameters.
- 目标故障实体：`A01711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01711:cause:4`，字符位置 `758-851`
- 证据原文：> For message values 3, 44 ... 57, 232 and 1-encoder system, differently set encoder parameters

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01711 SI Motion P1: Defect in a monitoring channel
Reaction: NONE
Acknowledge: NONE
462 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The drive has identified a difference between the input data or results of the monitoring functions and initiated A01711. Safe
operation is no longer possible.
At least one monitoring function is active, so that after the parameterized timer has expired, message F01701 is output.
The message value that resulted in this message is shown in r9725.
The following described message values involve the data cross-check between the two monitoring channels (safety
functions integrated in the drive).
The message values may also occur in the following cases if the cause that is explicitly mentioned does not apply:
- For message values 3, 44 ... 57, 232 and 1-encoder system, differently set encoder parameters.
- incorrect synchronization.
Message value (r2124, interpret decimal):
0 to 999: Number of the cross-compared data that resulted in this fault.
Message values that are not subsequently listed are only for internal Siemens troubleshooting.
0: Stop request from another monitoring channel.
1: Status image of monitoring functions SOS, SLS, SAM/SBR or SDI (result list 1) (r9710[0], r9710[1]).
2: Status image of monitoring function SSM (result list 2) (r9711[0], r9711[1]).
3: The position actual value differential (r9713[0/1]) between the two monitoring channels is greater than the tolerance in
p9542.
4: Error when synchronizing the data cross-check between the two channels.
5: Enable safe functions (p9501).
6: Limit value for SLS1 (p9531[0]).
7: Limit value for SLS2 (p9531[1]).
8: Limit value for SLS3 (p9531[2]).
9: Limit value for SLS4 (p9531[3]).
10: Standstill tolerance (p9530).
31: Position tolerance (p9542).
33: Time, speed switchover (p9551)
35: Delay time STO (p9556).
36: Test time, STO (p9557).
37: Transition time SS2 to SOS (p9552).
38: Transition time SS2E to SOS (p9553).
42: Shutdown speed STO (p9560).
43: Memory test stop response (STO).
44 ... 57: General
Possible cause 1 (during commissioning or parameter modification)
The tolerance value for the monitoring function is not the same on the two monitoring channels.
Possible cause 2 (during active operation)
The limit values are based on the actual value (r9713[0/1]). If the safe actual values on the two monitoring channels do not
match, the limit values, which have been set at a defined interval, will also be different (i.e. corresponding to message value
3). This can be ascertained by checking the safe actual positions.
Permissible deviation between the two monitoring channels: p9542.
44: Position actual value (r9713[0/1]) + limit value SLS1 (p9531[0]) * safety monitoring clock cycle.
45: Position actual value (r9713[0/1]) + limit value SLS1 (p9531[0]) * safety monitoring clock cycle.
46: Position actual value (r9713[0/1]) + limit value SLS2 (p9531[1]) * safety monitoring clock cycle.
47: Position actual value (r9713[0/1]) + limit value SLS2 (p9531[1]) * safety monitoring clock cycle.
48: Position actual value (r9713[0/1]) + limit value SLS3 (p9531[2]) * safety monitoring clock cycle.
49: Position actual value (r9713[0/1]) - limit value SLS3 (p9531[2]) * safety monitoring clock cycle.
50: Position actual value (r9713[0/1]) + limit value SLS4 (p9531[3]) * safety monitoring clock cycle.
51: Position actual value (r9713[0/1]) - limit value SLS4 (p9531[3]) * safety monitoring clock cycle.
52: Standstill position + tolerance (p9530).
53: Standstill position - tolerance (p9530).
54: Position actual value (r9713[0/1]) + limit value of SSM (p9546) * safety monitoring clock cycle + tolerance (p9542).
55: Position actual value (r9713[0/1]) + limit value of SSM (p9546) * safety monitoring clock cycle.
56: Position actual value (r9713[0/1]) - limit value of SSM (p9546) * safety monitoring clock cycle.
57: Position actual value (r9713[0/1]) - limit value of SSM (p9546) * safety monitoring clock cycle - tolerance (p9542).
58: Actual stop request.
75: Velocity limit of SSM (p9546).
When function "SSM" is enabled (p9501.16 = 1), then this message value is output - also for a different hysteresis tolerance
(p9547).
76: Stop response for SLS1 (p9563[0]).
77: Stop response for SLS2 (p9563[1]).
78: Stop response for SLS3 (p9563[2]).
79: Stop response for SLS4 (p9563[3]).
81: Velocity tolerance for SAM (p9548).
82: SGEs for SLS correction factor.
83: Acceptance test timer (p9558).
84: Transition time A01711 (p9555).
89: Encoder limit frequency.
230: Filter time constant for SSM.
231: Hysteresis tolerance for SSM.
232: Smoothed velocity actual value.
233: Limit value of SSM / safety monitoring clock cycle + hysteresis tolerance.
234: Limit value of SSM / safety monitoring clock cycle.
235: -Limit value of SSM / safety monitoring clock cycle.
236: -Limit value of SSM / safety monitoring clock cycle - hysteresis tolerance.
237: SGA SSM.
238: Speed limit value for SAM (p9568 or p9546).
239: Acceleration for SBR (p9581 and p9583).
240: Inverse value of acceleration for SBR (p9581 and p9583).
241: Deceleration time for SBR (p9582).
242: Function specification (p9506).
243: Function configuration (p9507).
247: SDI tolerance (p9564).
248: SDI positive upper limit (7FFFFFFF hex).
249: Position actual value (r9713[0/1]) - SDI tolerance (p9564).
250: Position actual value (r9713[0/1]) + SDI tolerance (p9564).
251: SDI negative lower limit (80000001 hex).
252: SDI stop response (p9566).
253: SDI delay time (p9565).
256: Status image of monitoring functions SOS, SLS, test stop, SBR, SDI (result list 1 ext) (r9710).
259: PROFIsafe telegram (p9611) is different between the monitoring channels.
261: Scaling factor for acceleration for SBR different.
262: Scaling factor for the inverse value of the acceleration for SBR different.
265: Status image of all change functions (results list 1) (r9710).
270: Screen form for SGE image: all functions, which are not supported/enabled for the actual parameterization (p9501,
p9601 and p9506).
273: speed limit value for flattening the ramp for SAM/SBR different.
276: Limit value for SLA1 (p9578/p9378).
277: Stop response for SLA1 (p9579/p9379).
278: Upper limit value for SLA1.
279: Lower limit value for SLA1.
280: Upper limit value for SLA1 (fine resolution).
281: Lower limit value for SLA1 (fine resolution).
282: SLA filter time (p9576/p9376).
283: Acceleration actual value (fine resolution).
1000: Watchdog timer has expired. Too many signal changes have occurred at safety-relevant inputs.
1001: Initialization error of watchdog timer.
464 Operating Instructions, 01/2019, A5E41702836B AC
1005: STO already active for test stop selection.
1011: Acceptance test status between the monitoring channels differ.
1012: Plausibility violation of the encoder actual value.
1020: Cyc. communication failure between the monit. channels.
1021: Cyclic communication failure between the monitoring channel and encoder evaluation.
1022: Sign-of-life error for DRIVE-CLiQ encoders monitoring channel 1.
1023: Error in the effectiveness test in the DRIVE-CLiQ encoder
1032: Sign-of-life error for DRIVE-CLiQ encoders monitoring channel 2.
1033: Error checking offset between POS1 and POS2 for DRIVE-CLiQ encoder monitoring channel 1.
1034: Error checking offset between POS1 and POS2 for DRIVE-CLiQ encoder monitoring channel 2.
1035: offset between POS1 and POS2 for DRIVE-CLiQ encoder on one of the monitoring channels has changed since the
last commissioning.
1039: Overflow when calculating the position.
5000 ... 5140:
PROFIsafe message values.
For these message values, the failsafe control signals (Failsafe Values) are transferred to the safety functions.
5000, 5014, 5023, 5024, 5030 ... 5032, 5042, 5043, 5052, 5053, 5068, 5072, 5073, 5082 ... 5087, 5090, 5091, 5122 ... 5125,
5132 ... 5135, 5140:
An internal software error has occurred (only for internal Siemens troubleshooting).
5012: Error when initializing the PROFIsafe driver.
5013: The result of the initialization is different for the two controllers.
5022: Error when evaluating the F parameters. The values of the transferred F parameters do not match the expected
values in the PROFIsafe driver.
5025: The result of the F parameterization is different for the two controllers.
5026: CRC error for the F parameters. The transferred CRC value of the F parameters does not match the value calculated
in the PST.
5065: A communications error was identified when receiving the PROFIsafe telegram.
5066: A time monitoring error (timeout) was identified when receiving the PROFIsafe telegram.
6000 ... 6166:
PROFIsafe message values (PROFIsafe driver for PROFIBUS DP V1/V2 and PROFINET).
For these message values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. If "SS1 after
failure of PROFIsafe communication" is parameterized (p9612), then transfer of the Failsafe Values is delayed.
The significance of the individual message values is described in safety fault F01611.
7000: Difference of the safe position higher than the parameterized tolerance (p9542).
7002: Cycle counter for transferring the safe position is different in both monitoring channels.
See also: p9555 (SI Motion transition time F01711 to SS1), r9725 (SI Motion diagnostics A01711)
Remedy: For message value = 0:
- no error was identified in this monitoring channel. Observe the error message of the other monitoring channel (A30711).
For message value = 3:
Commissioning phase:
- check encoder parameters, and if required, correct (p9516, p9517, p9518, p9520, p9521, p9522, p9526).
In operation:
- check the mechanical design and the encoder signals.
For message value = 232:
- increase the hysteresis tolerance (p9547). Possibly set the filtering higher (p9545).
For message value = 278, 279, 280, 281: - check whether the same acceleration limit has been set for both channels. A
different result depends on whether SLA is enabled and not selected - or enabled and selected. In this case, another
message value is possible.
For message value = 1 ... 999:
- if the message value is listed under cause: Check the cross-checked parameters to which the message value refers.
- copy safety parameters and confirm the data change (commissioning tool).
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- upgrade the drive software.
- correction of the encoder evaluation. The actual values differ as a result of mechanical faults (V belts, travel to a
mechanical endstop, wear and window setting that is too narrow, encoder fault, ...).
For message value = 1001:
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- upgrade the drive software.
For message value = 1005:
- check the conditions for deselecting STO.
For message value = 1007:
- check the PLC for the correct operating state (run state, basic program).
For message value = 1011:
- for diagnostics, refer to parameter (r9571).
For message value = 1012:
- upgrade the encoder evaluation firmware to a newer version.
- check encoder parameters to ensure that they are the same (p9515, p9519, p9523, p9524, p9525, p9529).
- start the copy function for encoder parameters (commissioning tool).
- the parameterized encoder does not correspond to the connected encoder - replace the encoder.
- check the electrical cabinet design and cable routing for EMC compliance
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- replace the hardware.
For message value = 1020, 1021:
- check the communication link.
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- replace the hardware.
For message value = 1035, if the safety encoder was replaced:
- acknowledge hardware replacement.
- save all parameters
- acknowledge fault.
For message value = 1039:
- check the conversion factors such as spindle pitch or gearbox ratios.
For message value = 5000, 5014, 5023, 5024, 5030, 5031, 5032, 5042, 5043, 5052, 5053, 5068, 5072, 5073, 5082 ... 5087,
5090, 5091, 5122 ... 5125, 5132 ... 5135, 5140:
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- upgrade firmware to later version.
- contact Technical Support.
- replace drive.
For message value = 5012:
466 Operating Instructions, 01/2019, A5E41702836B AC
- check the setting of the PROFIsafe address of the drive (p9610). It is not permissible for the PROFIsafe address to be 0
or FFFF!
- copy safety parameters and confirm the data change (commissioning tool).
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
For message value = 5013, 5025:
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- check the setting of the PROFIsafe address of the drive (p9610).
For message value = 5022:
- check the setting of the values of the F parameters at the PROFIsafe slave (F_SIL, F_CRC_Length, F_Par_Version,
F_Source_Add, F_Dest_add, F_WD_Time).
For message value = 5026:
- check the settings of the values of the F parameters and the F parameter CRC (CRC1) calculated from these at the
PROFIsafe slave and update.
For message value = 5065:
- check the configuration and communication at the PROFIsafe slave (cons. No. / CRC).
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
For message value = 5066:
- check the setting of the value for F parameter F_WD_Time on the PROFIsafe slave and increase if necessary.
- evaluate diagnostic information in the F host.
- check PROFIsafe connection.
For message value = 6000 ... 6999:
See the description of the message values for fault F01611.
Note:
SAM: Safe Acceleration Monitor (safe acceleration monitoring)
SBR: Safe Brake Ramp (safe ramp monitoring)
SDI: Safe Direction (safe motion direction)
SI: Safety Integrated
SLS: Safely-Limited Speed
SOS: Safe Operating Stop
SS1: Safe Stop 1
SS2: Safe Stop 2
SSM: Safe Speed Monitor (safety-relevant feedback signal from the speed monitoring)
```

---

### CR-CAND-V6-010 · A01714

- 来源记录：`SIEMENS_S210_2019_A01714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS3 exceeded.
- 目标故障实体：`A01714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01714:cause:6`，字符位置 `324-338`
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
A01714 SI Motion P1: Safely-Limited Speed exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The drive has moved faster than that specified by the velocity limit value (p9531). The drive is stopped by the configured
stop response (p9563).
Message value (r2124, interpret decimal):
100: SLS1 exceeded.
200: SLS2 exceeded.
300: SLS3 exceeded.
400: SLS4 exceeded.
1000: Encoder limit frequency exceeded.
Remedy: - check the traversing/motion program in the control.
- check limits for SLS and if required adapt accordingly (p9531).
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
See also: p9531 (SI Motion SLS limit values), p9563 (SI Motion SLS-specific stop response)
```

---

### CR-CAND-V6-013 · A01784

- 来源记录：`SIEMENS_S210_2019_A01784`（序号 None）
- 故障描述：SBT brake test canceled with fault
- 候选原因节点：the permissible position range of the axis was violated with the brake closed
- 目标故障实体：`A01784` · SBT brake test canceled with fault
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01784:cause:5`，字符位置 `425-502`
- 证据原文：> the permissible position range of the axis was violated with the brake closed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01784 SBT brake test canceled with fault
Reaction: NONE
Acknowledge: NONE
Cause: The safe brake test was canceled as a result of a fault.
Alarm value (r2124, interpret binary):
Bit 17 = 1: fault in the brake test sequence (cause, see bits 0 ... 10).
Bit 20 = 1: the brake is not opened (p10202).
Bit 21 = 1: axis position during the brake test not valid due to parking axis.
Bit 22 = 1: internal software error.
Bit 23 = 1: the permissible position range of the axis was violated with the brake closed (p10212/p10222).
Bit 24 = 1: the tested internal brake was opened while the brake test was active.
Bit 26 = 1: during the active brake test, the test torque left its tolerance bandwidth (20 %).
Cause for alarm value bit 17:
Bit 0 = 1: operation when selecting the brake test not enabled (r0899.2 = 0).
Bit 1 = 1: external fault occurred (e.g. the brake test that has already started is canceled by the user).
Bit 2 = 1: when selecting the brake test a brake is closed.
Bit 3 = 1: when determining the load torque a brake is closed.
Bit 4 = 1: A fault has occurred with stop response (e.g. OFF1, OFF2 or OFF3) - or the pulse enable was withdrawn (e.g. STO
selected or operation no longer enabled).
Bit 5 = 1: when selecting the brake test the axis speed setpoint is too high.
Bit 6 = 1: the actual speed (r0063) of the axis is too high (e.g. brake does not hold during the brake test).
Bit 8 = 1: closed-loop control not enabled or function generator active.
Bit 9 = 1: control does not switch over to the brake test (e.g. because PI speed control has not been parameterized).
Bit 10 = 1: torque limit reached (r1407.7, r1408.8).
Note:
SBT: Safe Brake Test
Remedy: - remove the fault cause.
- carry out a safe acknowledgment.
- if required, restart the brake test.
For bit 17 = 1 with bit 6 = 1 or bit 23 = 1:
If the brake closing time of the motor holding brake (p1217) has been set too low, then at the start of the brake test, the brake
is closed too late. The brake closing time should be adapted (p1217).
```

---

### CR-CAND-V6-027 · A01785

- 来源记录：`SIEMENS_S210_2019_A01785`（序号 None）
- 故障描述：SBT brake test configuration error
- 候选原因节点：The brake test is configured for an internal brake, however the safety brake control is not enabled
- 目标故障实体：`A01785` · SBT brake test configuration error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01785:cause:5`，字符位置 `402-501`
- 证据原文：> The brake test is configured for an internal brake, however the safety brake control is not enabled

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01785 SBT brake test configuration error
Reaction: NONE
Acknowledge: NONE
470 Operating Instructions, 01/2019, A5E41702836B AC
Cause: Error when parameterizing the brake test.
In this configuration, the brake test cannot be started or cannot be started without error.
Alarm value (r2124, interpret decimal):
1:
No motion monitoring functions have been enabled.
4:
No brake was configured (p10202).
8:
The brake test is configured for an internal brake, however the safety brake control is not enabled (p9602).
16:
The safe brake test and safety without encoder are simultaneously enabled (p9506). This is not permissible.
Note:
SBT: Safe Brake Test
Remedy: Check parameterization of the brake test.
```

---

### CR-CAND-V6-029 · A01900

- 来源记录：`SIEMENS_S210_2019_A01900`（序号 None）
- 故障描述：Configuration telegram error
- 候选原因节点：Uneven number of bytes for input or output.
- 目标故障实体：`A01900` · Configuration telegram error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01900:cause:6`，字符位置 `548-591`
- 证据原文：> Uneven number of bytes for input or output.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01900 PN: Configuration telegram error
Reaction: NONE
Acknowledge: NONE
Cause: A controller attempts to establish a connection using an incorrect configuring telegram.
Alarm value (r2124, interpret decimal):
1:
Connection established to more drive objects than configured in the device. The drive objects for process data exchange
and their sequence are defined in p0978.
2:
Too many PZD data words for output or input to a drive object. The number of possible PZD items in a drive object is
determined by the number of indices in r2050/p2051.
3:
Uneven number of bytes for input or output.
4:
Setting data for synchronization not accepted. For more information, see A01902.
211:
Unknown parameterizing block.
223:
Clock synchronization for the PZD interface set in p8815[0] is not permissible.
More than one PZD interface is operated in clock synchronism.
253:
PN Shared Device: Illegal mixed configuration of PROFIsafe and PZD.
254:
PN Shared Device: Illegal double assignment of a slot/subslot.
255:
PN: Configured drive object and existing drive object do not match.
256:
PN: configured telegram cannot be set.
500:
Illegal PROFIsafe configuration for the interface set in p8815[1].
More than one PZD interface is operated with PROFIsafe.
501:
PROFIsafe parameter error (e.g. F_dest).
502:
PROFIsafe telegram does not match.
503:
PROFIsafe connection is rejected as long as there is no isochronous connection (p8969).
Additional values:
Only for internal Siemens troubleshooting.
Remedy: Check the bus configuration on the master and the slave sides.
For alarm value = 1, 2:
- check the list of the drive objects with process data exchange (p0978).
Note:
With p0978[x] = 0, all of the following drive objects in the list are excluded from the process data exchange.
For alarm value = 2:
- check the number of data words for output and input to a drive object.
For alarm value = 211:
- Ensure offline version <= online version.
For alarm value = 223, 500:
- check the setting in p8839 and p8815.
- check for inserted but not configured CBE20.
- ensure that only one PZD interface is operated in clock synchronism or with PROFIsafe.
For alarm value = 255:
- check configured drive objects.
For alarm value = 256:
- check the configured telegram.
For alarm value = 501:
- check the set PROFIsafe address (p9610).
For alarm value = 502:
- check the set PROFIsafe telegram (p60022, p9611).
```

---

### CR-CAND-V6-041 · A01902

- 来源记录：`SIEMENS_S210_2019_A01902`（序号 None）
- 故障描述：clock cycle synchronous operation parameterization not permissible
- 候选原因节点：Bus cycle time Tdp is not an integer multiple of the current controller sampling time.
- 目标故障实体：`A01902` · clock cycle synchronous operation parameterization not permissible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01902:cause:6`，字符位置 `287-373`
- 证据原文：> Bus cycle time Tdp is not an integer multiple of the current controller sampling time.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01902 PN: clock cycle synchronous operation parameterization not permissible
Reaction: NONE
Acknowledge: NONE
Cause: Parameterization for isochronous operation is not permissible.
Alarm value (r2124, interpret decimal):
0: Bus cycle time Tdp < 0.5 ms.
1: Bus cycle time Tdp > 32 ms.
2: Bus cycle time Tdp is not an integer multiple of the current controller sampling time.
3: Instant of the actual value sensing Ti > Bus cycle time Tdp or Ti = 0.
4: Instant of the actual value sensing Ti is not an integer multiple of the current controller sampling time.
5: Instant of the setpoint acceptance To >= Bus cycle time Tdp or To = 0.
6: Instant of the setpoint acceptance To is not an integer multiple of the current controller sampling time.
7: Master application cycle time Tmapc is not an integer multiple of the speed controller sampling time.
8: Bus reserve bus cycle time Tdp - data exchange time Tdx less than two current controller sampling times.
10: Instant of the setpoint acceptance To <= data exchange time Tdx + current controller sampling time
11: Master application cycle time Tmapc > 14 x Tdp or Tmapc = 0.
12: PLL tolerance window Tpll_w > Tpll_w_max.
13: Bus cycle time Tdp is not a multiple of all basic clock cycles p0110[x].
16: For COMM BOARD, the instant in time for the actual value sensing Ti is less than two current controller sampling times.
Remedy: - adapt the bus parameterization Tdp, Ti, To.
- adapt the sampling time for the current controller or speed controller.
For alarm value = 10:
- reduce Tdx by using fewer bus participants or shorter telegrams.
Note:
PN: PROFINET
```

---

### CR-CAND-V6-053 · A01943

- 来源记录：`SIEMENS_S210_2019_A01943`（序号 None）
- 故障描述：Clock cycle signal error when the bus is being established
- 候选原因节点：the master is using another clock synchronous DP clock cycle than was transferred to the slave in the parameterizing telegram.
- 目标故障实体：`A01943` · Clock cycle signal error when the bus is being established
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01943:cause:6`，字符位置 `376-502`
- 证据原文：> the master is using another clock synchronous DP clock cycle than was transferred to the slave in the parameterizing telegram.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01943 PN: Clock cycle signal error when the bus is being established
Reaction: NONE
Acknowledge: NONE
Cause: The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing
telegram.
The global control telegram for synchronization is being irregularly received.
-.the master is sending an irregular global control telegram.
- the master is using another clock synchronous DP clock cycle than was transferred to the slave in the parameterizing
telegram.
Remedy: - check the master application and bus configuration.
- check the consistency between the clock cycle input when configuring the slave and clock cycle setting at the master.
Note:
PN: PROFINET
```

---

### CR-CAND-V6-054 · A07012

- 来源记录：`SIEMENS_S210_2019_A07012`（序号 None）
- 故障描述：Motor temperature model 1/3 overtemperature
- 候选原因节点：Motor temperature model 3: temperature too high.
- 目标故障实体：`A07012` · Motor temperature model 1/3 overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07012:cause:5`，字符位置 `299-347`
- 证据原文：> Motor temperature model 3: temperature too high.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07012 Drive: Motor temperature model 1/3 overtemperature
Reaction: NONE
Acknowledge: NONE
Cause: The motor temperature model 1/3 identified that the alarm threshold was exceeded.
Hysteresis:2K
Alarm value (r2124, interpret decimal):
200:
Motor temperature model 1 (I2t): temperature too high.
300:
Motor temperature model 3: temperature too high.
See also: r0034 (Motor utilization thermal), p0613 (Motor temperature model ambient temperature)
Remedy: - check the motor load and if required, reduce.
- check the motor ambient temperature.
See also: r0034 (Motor utilization thermal)
```

---

### CR-CAND-V6-055 · A07091

- 来源记录：`SIEMENS_S210_2019_A07091`（序号 None）
- 故障描述：determined current controller dynamic response invalid
- 候选原因节点：PRBS amplitude set too high
- 目标故障实体：`A07091` · determined current controller dynamic response invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07091:cause:4`，字符位置 `368-395`
- 证据原文：> PRBS amplitude set too high

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07091 Drive: determined current controller dynamic response invalid
Reaction: NONE
Acknowledge: NONE
Cause: When one button tuning is activated (p5300 = 1), the current controller is measured after the pulses have been enabled.
Evaluation has indicated that the current control loop was not appropriately set.
Possible causes:
- incorrectly set current controller.
- PRBS amplitude set too high (p5296).
Alarm value (r2124, interpret hexadecimal):
1: Dynamic response too low.
2: Current controller unstable.
Note:
PRBS: Pseudo Random Binary Signal (binary noise)
Remedy: - the measurement can be repeated with a smaller excitation amplitude (p5296).
- if required, adapt the current controller proportional gain (p1715).
```

---

### CR-CAND-V6-058 · A08511

- 来源记录：`SIEMENS_S210_2019_A08511`（序号 None）
- 故障描述：Receive configuration data invalid
- 候选原因节点：Too many PZD data words for output or input to a drive object.
- 目标故障实体：`A08511` · Receive configuration data invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A08511:cause:5`，字符位置 `420-482`
- 证据原文：> Too many PZD data words for output or input to a drive object.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A08511 PN/COMM BOARD: Receive configuration data invalid
Reaction: NONE
Acknowledge: NONE
Cause: The drive unit did not accept the receive configuration data.
Alarm value (r2124, interpret decimal):
Return value of the receive configuration data check.
1: Connection established to more drive objects than configured in the device. The drive objects for process data exchange
and their sequence are defined in p0978.
2: Too many PZD data words for output or input to a drive object. The number of possible PZD items in a drive object is
determined by the number of indices in r2050/p2051 for PZD IF1, and in r8850/p8851 for PZD IF2.
3: Uneven number of bytes for input or output.
4: Setting data for synchronization not accepted. For more information, see A01902.
5: Cyclic operation not active.
17: CBE20 Shared Device: Configuration of the F-CPU has been changed.
223: Illegal clock synchronization for the PZD interface set in p8815[0].
500: Illegal PROFIsafe configuration for the interface set in p8815[1].
501: PROFIsafe parameter error (e.g. F_dest).
503: PROFIsafe connection is rejected as long as there is no isochronous connection (p8969).
Additional values:
Only for internal Siemens troubleshooting.
488 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: Check the receive configuration data.
For alarm value = 1, 2:
- check the list of the drive objects with process data exchange (p0978). With p0978[x] = 0, all of the following drive objects
in the list are excluded from the process data exchange.
For alarm value = 2:
- check the number of data words for output and input to a drive object.
For alarm value = 17:
- CBE20 Shared Device: Unplug/plug A-CPU.
For alarm value = 223, 500:
- check the setting in p8839 and p8815.
- ensure that only one PZD interface is operated in clock synchronism or with PROFIsafe.
For alarm value = 501:
- check the set PROFIsafe address (p9610).
```

---

### CR-CAND-V6-067 · A09000

- 来源记录：`SIEMENS_S210_2019_A09000`（序号 33）
- 故障描述：Web server user incorrectly configured
- 候选原因节点：Invalid admin password
- 目标故障实体：`A09000` · Web server user incorrectly configured
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A09000:cause:10`，字符位置 `206-228`
- 证据原文：> Invalid admin password

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A09000 Web server user incorrectly configured
Reaction: NONE
Acknowledge: NONE
Cause: An error occurred when configuring the web server user.
Fault value (r0949, interpret decimal):
0: No admin password
1: Invalid admin password
2: Invalid SINAMICS password
Remedy: Correct the user configuration, enter a correct password.
```

---

### CR-CAND-V6-069 · A30031

- 来源记录：`SIEMENS_S210_2019_A30031`（序号 None）
- 故障描述：Hardware current limiting in phase U
- 候选原因节点：the power cables exceed the maximum permissible length.
- 目标故障实体：`A30031` · Hardware current limiting in phase U
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30031:cause:5`，字符位置 `302-357`
- 证据原文：> the power cables exceed the maximum permissible length.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30031 Power unit: Hardware current limiting in phase U
Reaction: NONE
Acknowledge: NONE
Cause: Hardware current limit for phase U responded. The pulsing in this phase is inhibited for one pulse period.
- closed-loop control is incorrectly parameterized.
- fault in the motor or in the power cables.
- the power cables exceed the maximum permissible length.
- motor load too high
- power unit defective.
Note:
Alarm A30031 is always output if, for a Power Module, the hardware current limiting of phase U, V or W responds.
Remedy: - check the motor data and if required, recalculate the control parameters (p0340 = 3). As an alternative, run a motor data
identification (p1910 = 1, p1960 = 1).
- check the motor circuit configuration (star/delta).
- check the motor load.
- check the power cable connections.
- check the power cables for short-circuit or ground fault.
- check the length of the power cables.
```

---

### CR-CAND-V6-072 · A30034

- 来源记录：`SIEMENS_S210_2019_A30034`（序号 None）
- 故障描述：Internal overtemperature
- 候选原因节点：insufficient cooling, fan failure.
- 目标故障实体：`A30034` · Internal overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30034:cause:5`，字符位置 `357-391`
- 证据原文：> insufficient cooling, fan failure.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30034 Power unit: Internal overtemperature
Reaction: NONE
Acknowledge: NONE
500 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The alarm threshold for internal overtemperature has been reached.
If the temperature inside the power unit increases up to the fault threshold, then fault F30036 is triggered.
- ambient temperature might be too high.
- insufficient cooling, fan failure.
Alarm value (r2124, interpret binary):
Bit 0 = 1: Overtemperature in the control electronics area.
Bit 1 = 1: Overtemperature in the power electronics area.
Bit 2 = 1: Overtemperature in the processor area.
Bit 3 = 1: Overtemperature in the processor area.
Bit 4 = 1: Overtemperature when the internal fan is defective.
Bit 5 = 1: Intake air overtemperature.
Remedy: - check the ambient temperature.
- check the fan for the inside of the unit.
```

---

### CR-CAND-V6-078 · A30042

- 来源记录：`SIEMENS_S210_2019_A30042`（序号 None）
- 故障描述：Fan has reached the maximum operating hours
- 候选原因节点：The wear counter of the heat sink fan has reached 99 %; the remaining service life is 1%.
- 目标故障实体：`A30042` · Fan has reached the maximum operating hours
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30042:cause:11`，字符位置 `447-534`
- 证据原文：> The wear counter of the heat sink fan has reached 99 %. The remaining service life is 1

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30042 Power unit: Fan has reached the maximum operating hours
Reaction: NONE
Acknowledge: NONE
Cause: The maximum operating time of at least one fan will soon be reached, or has already been exceeded.
Alarm value (r2124, interpret binary):
Bit 0 = 1:
The operating hours counter of the heat sink fan will reach the maximum operating time in 500 hours. After 500 hours has
elapsed, bit 0 is cleared and bit 2 is set in the alarm value.
Bit 1 = 1:
The wear counter of the heat sink fan has reached 99 %. The remaining service life is 1%. After this 1% has elapsed, bit 1
is cleared and bit 2 is set in the alarm value.
Bit 2 = 1:
The operating hours counter of the heat sink fan has exceeded the maximum operating time - and/or the wear counter has
exceeded 100%.
Bit 8 = 1:
The operating hours counter of the fan inside the device will reach the maximum operating time in 500 hours. After 500
hours has elapsed, bit 8 is cleared and bit 10 is set in the alarm value.
Bit 10 = 1:
The operating hours counter of the fan inside the device has exceeded the maximum operating time.
Remedy: For the fan involved, carry out the following:
- replace the fan.
- reset the operating hours counter (p0251, p0254).
See also: p0251 (Power unit heat sink fan operating hours counter)
```

---

### CR-CAND-V6-082 · A30502

- 来源记录：`SIEMENS_S210_2019_A30502`（序号 None）
- 故障描述：DC link overvoltage
- 候选原因节点：line reactor incorrectly dimensioned
- 目标故障实体：`A30502` · DC link overvoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30502:cause:4`，字符位置 `190-226`
- 证据原文：> line reactor incorrectly dimensioned

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30502 Power unit: DC link overvoltage
Reaction: NONE
Acknowledge: NONE
Cause: The power unit has detected overvoltage in the DC link on a pulse inhibit.
- device supply voltage too high.
- line reactor incorrectly dimensioned.
Alarm value (r0949, interpret decimal):
DC link voltage [1 bit = 100 mV].
See also: r0070 (Actual DC link voltage)
Remedy: - check the device supply voltage (p0210).
- check the dimensioning of the line reactor.
See also: p0210 (Drive unit line supply voltage)
```

---

### CR-CAND-V6-083 · A30706

- 来源记录：`SIEMENS_S210_2019_A30706`（序号 None）
- 故障描述：SAM/SBR limit exceeded
- 候选原因节点：Motion monitoring functions with encoder (SBR): after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance.
- 目标故障实体：`A30706` · SAM/SBR limit exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30706:cause:6`，字符位置 `212-374`
- 证据原文：> Motion monitoring functions with encoder (SBR, p9506 = 2): - after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30706 SI Motion P2: SAM/SBR limit exceeded
Reaction: NONE
Acknowledge: NONE
Cause: Motion monitoring functions with encoder (SAM, p9506 = 0):
- after initiating SS1 or SS2, the speed exceeded the set tolerance.
Motion monitoring functions with encoder (SBR, p9506 = 2):
- after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance.
The drive is stopped by message F30700.
Remedy: Check the braking behavior and, if necessary, adapt the parameterization of the parameter settings of the "SAM" or the
"SBR" function.
Note:
This message can be acknowledged via PROFIsafe (safe acknowledgment).
SAM: Safe Acceleration Monitor (safe acceleration monitoring)
SBR: Safe Brake Ramp (safe ramp monitoring)
SI: Safety Integrated
SS1: Safe Stop 1
SS2: Safe Stop 2
SLS: Safely-Limited Speed
See also: p9548 (SI Motion SAM actual speed tolerance)
```

---

### CR-CAND-V6-084 · A30711

- 来源记录：`SIEMENS_S210_2019_A30711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：incorrect synchronization
- 目标故障实体：`A30711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30711:cause:4`，字符位置 `553-578`
- 证据原文：> incorrect synchronization

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30711 SI Motion P2: Defect in a monitoring channel
Reaction: NONE
Acknowledge: NONE
516 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The drive has identified a difference between the input data or results of the monitoring functions and initiated A30711. Safe
operation is no longer possible.
At least one monitoring function is active, so that after the parameterized timer has expired, message F30701 is output.
The following message values may also occur in the following cases if the cause that is explicitly mentioned does not apply:
- incorrect synchronization.
Message value (r2124, interpret decimal):
0 ... 999:
Number of the cross-compared data that resulted in this message.
The significance of the individual message values is described in message A01711.
1000: Watchdog timer has expired. Too many signal changes have occurred at safety-relevant inputs.
1001: Initialization error of watchdog timer.
1005: STO already active for test stop selection.
1011: Acceptance test status between the monitoring channels differ.
1012: Plausibility violation of the encoder actual value.
1020: Cyc. communication failure between the monit. channels.
1021: Cyclic communication failure between the monitoring channel and encoder evaluation.
1023: Error in the effectiveness test in the DRIVE-CLiQ encoder
1030: Encoder fault detected from another monitoring channel.
1045: CRC of the standstill position incorrect.
5000 ... 5140:
PROFIsafe message values.
For these message values, the failsafe control signals (Failsafe Values) are transferred to the safety functions.
The significance of the individual message values is described in message A01711.
6000 ... 6166:
PROFIsafe message values (PROFIsafe driver for PROFIBUS DP V1/V2 and PROFINET).
For these message values, the failsafe control signals (Failsafe Values) are transferred to the safety functions. If "SS1 after
failure of PROFIsafe communication" is parameterized, then transfer of the Failsafe Values is delayed.
The significance of the individual message values is described in safety fault F01611.
See also: p9555 (SI Motion transition time F01711 to SS1), r9725 (SI Motion diagnostics A01711)
Remedy: For message value = 1005:
- check the conditions for deselecting STO.
For message value = 1012:
- upgrade the encoder evaluation firmware to a newer version.
- check encoder parameters to ensure that they are the same (p9515, p9519, p9523, p9524, p9525, p9529).
- start the copy function for encoder parameters (commissioning tool).
- the parameterized encoder does not correspond to the connected encoder - replace the encoder.
- check the electrical cabinet design and cable routing for EMC compliance
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- replace the hardware.
For message value = 1024:
- check the communication link.
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
- replace the hardware.
For message value = 1030:
- check the encoder connection.
- if required, replace the encoder.
Adapt the encoder parameterization for the second channel as follows:
- activate the safety commissioning mode (p0010 = 95).
- start the copy function for encoder parameters (commissioning tool).
- exit the safety commissioning mode (p0010 = 0).
- save the parameters in a non-volatile fashion (copy RAM to ROM).
- carry out a POWER ON (switch off/switch on) or a warm restart (p0009 = 30, p0976 = 2, 3).
The following always applies:
- check the encoder connection.
- if required, replace the encoder.
For message value = 6000 ... 6999:
- the significance of the individual message values are described in fault F01611.
For other message values:
- the significance of the individual message values is described in message A01711.
Note:
SI: Safety Integrated
SS1: Safe Stop 1
```

---

### CR-CAND-V6-095 · A30716

- 来源记录：`SIEMENS_S210_2019_A30716`（序号 None）
- 故障描述：Tolerance for safe motion direction exceeded
- 候选原因节点：Tolerance for function 'safe motion direction positive' exceeded
- 目标故障实体：`A30716` · Tolerance for safe motion direction exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30716:cause:5`，字符位置 `274-338`
- 证据原文：> Tolerance for function "safe motion direction positive" exceeded

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30716 SI Motion P2: Tolerance for safe motion direction exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The tolerance for the "safe motion direction" function was exceeded. The drive is stopped by the configured stop response.
Message value (r2124, interpret decimal):
0: Tolerance for function "safe motion direction positive" exceeded.
1: Tolerance for function "safe motion direction negative" exceeded.
Remedy: - check the traversing/motion program in the control.
- check the tolerance for the "SDI" function and adapt if necessary.
This message can be acknowledged as follows:
Deselect/select SDI and perform safe acknowledgment via PROFIsafe.
Note:
SDI: Safe Direction (safe motion direction)
SI: Safety Integrated
```

---

### CR-CAND-V6-097 · A30730

- 来源记录：`SIEMENS_S210_2019_A30730`（序号 None）
- 故障描述：Reference block for dynamic Safely-Limited Speed invalid
- 候选原因节点：requested, invalid reference block.
- 目标故障实体：`A30730` · Reference block for dynamic Safely-Limited Speed invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30730:cause:4`，字符位置 `426-461`
- 证据原文：> requested, invalid reference block.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30730 SI Motion P2: Reference block for dynamic Safely-Limited Speed invalid
Reaction: NONE
Acknowledge: NONE
Cause: The reference block transferred via PROFIsafe is negative.
A reference block is used to generate a referred velocity limit value based on the reference quantity "Velocity limit value
SLS1" (p9531[0]).
The drive is stopped by the configured stop response (p9563[0]).
Message value (r2124, interpret decimal):
requested, invalid reference block.
Remedy: In the PROFIsafe telegram, input data S_SLS_LIMIT_IST must be corrected.
This message can be acknowledged without a POWER ON as follows (safe acknowledgment):
- PROFIsafe.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
```

---

### CR-CAND-V6-098 · A30788

- 来源记录：`SIEMENS_S210_2019_A30788`（序号 None）
- 故障描述：wait for STO deselection via SMM
- 候选原因节点：the STO function is selected via Safety Extended Functions.
- 目标故障实体：`A30788` · wait for STO deselection via SMM
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30788:cause:3`，字符位置 `194-253`
- 证据原文：> the STO function is selected via Safety Extended Functions.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30788 Automatic test stop: wait for STO deselection via SMM
Reaction: NONE
Acknowledge: NONE
Cause: The automatic test stop was not able to be carried out after powering up.
Possible causes:
- the STO function is selected via Safety Extended Functions.
- a safety message is present, that resulted in a STO.
Note:
STO: Safe Torque Off
Remedy: - Deselect STO via Safety Extended Functions.
- remove the cause of the safety messages and acknowledge the messages.
Note:
The automatic test stop is performed after removing the cause.
```

---

### CR-CAND-V6-100 · A30999

- 来源记录：`SIEMENS_S210_2019_A30999`（序号 None）
- 故障描述：Unknown alarm
- 候选原因节点：firmware on this component is more recent than the firmware on the Control Unit
- 目标故障实体：`A30999` · Unknown alarm
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30999:cause:4`，字符位置 `188-267`
- 证据原文：> firmware on this component is more recent than the firmware on the Control Unit

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30999 Power unit: Unknown alarm
Reaction: NONE
Acknowledge: NONE
Cause: An alarm occurred on the power unit that cannot be interpreted by the Control Unit firmware.
This can occur if the firmware on this component is more recent than the firmware on the Control Unit.
Alarm value (r2124, interpret decimal):
Alarm number.
Note:
If required, the significance of this new alarm can be read about in a more recent description of the Control Unit.
Remedy: - replace the firmware on the power unit by an older firmware version (r0128).
- upgrade the firmware on the Control Unit (r0018).
```

---

### CR-CAND-V6-101 · A31700

- 来源记录：`SIEMENS_S210_2019_A31700`（序号 None）
- 故障描述：Functional safety monitoring initiated
- 候选原因节点：Self-test of the DRIVE-CLiQ encoder has detected a fault
- 目标故障实体：`A31700` · Functional safety monitoring initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A31700:cause:4`，字符位置 `130-186`
- 证据原文：> Self-test of the DRIVE-CLiQ encoder has detected a fault

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A31700 Encoder 1: Functional safety monitoring initiated
Reaction: NONE
Acknowledge: NONE
Cause: Functional safety was activated. Self-test of the DRIVE-CLiQ encoder has detected a fault.
Alarm value (r2124, interpret binary):
Bit x = 1: Effectivity test x unsuccessful.
Remedy: Replace encoder.
```

---

### CR-CAND-V6-103 · F01001

- 来源记录：`SIEMENS_S210_2019_F01001`（序号 None）
- 故障描述：FloatingPoint exception
- 候选原因节点：The error may be caused by the basic system or a technology function (e.g. FBLOCKS, DCC, TEC).
- 目标故障实体：`F01001` · FloatingPoint exception
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01001:cause:3`，字符位置 `151-245`
- 证据原文：> The error may be caused by the basic system or a technology function (e.g. FBLOCKS, DCC, TEC).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01001 FloatingPoint exception
Reaction: OFF2
Acknowledge: POWER ON
Cause: An exception occurred during an operation with the FloatingPoint data type.
The error may be caused by the basic system or a technology function (e.g. FBLOCKS, DCC, TEC).
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Note:
Refer to r9999 for further information about this fault.
r9999[0]: Fault number.
r9999[1]: Program counter at the time when the exception occurred.
r9999[2]: Cause of the FloatingPoint exception.
Bit 0 = 1: Operation invalid
Bit 1 = 1: Division by zero
Bit 2 = 1: Overflow
Bit 3 = 1: Underflow
Bit 4 = 1: Inaccurate result
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- check configuration and signals of the blocks in FBLOCKS.
- check configuration and signals of DCC charts.
- check configuration and signals of TEC charts.
- upgrade firmware to later version.
- contact Technical Support.
```

---

### CR-CAND-V6-109 · F01005

- 来源记录：`SIEMENS_S210_2019_F01005`（序号 None）
- 故障描述：Firmware download for DRIVE-CLiQ component unsuccessful
- 候选原因节点：DRIVE-CLiQ component has detected a checksum error.
- 目标故障实体：`F01005` · Firmware download for DRIVE-CLiQ component unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01005:cause:4`，字符位置 `359-410`
- 证据原文：> DRIVE-CLiQ component has detected a checksum error.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01005 Firmware download for DRIVE-CLiQ component unsuccessful
Reaction: NONE
Acknowledge: IMMEDIATELY
422 Operating Instructions, 01/2019, A5E41702836B AC
Cause: It was not possible to download the firmware to a DRIVE-CLiQ component.
Fault value (r0949, interpret hexadecimal):
yyxxxx hex: yy = component number, xxxx = fault cause
xxxx = 000B hex = 11 dec:
DRIVE-CLiQ component has detected a checksum error.
xxxx = 000F hex = 15 dec:
The selected DRIVE-CLiQ component did not accept the contents of the firmware file.
xxxx = 0012 hex = 18 dec:
Firmware version is too old and is not accepted by the component.
xxxx = 0013 hex = 19 dec:
Firmware version is not suitable for the hardware release of the component.
xxxx = 0065 hex = 101 dec:
After several communication attempts, no response from the DRIVE-CLiQ component.
xxxx = 008B hex = 139 dec:
Initially, a new boot loader is loaded (must be repeated after POWER ON).
xxxx = 008C hex = 140 dec:
Firmware file for the DRIVE-CLiQ component not available on the memory card.
xxxx = 008D hex = 141 dec:
An inconsistent length of the firmware file was signaled. The firmware download may have been caused by a loss of
connection to the firmware file. This can occur during a project download/reset in the case of a SINAMICS Integrated Control
Unit, for example.
xxxx = 008F hex = 143 dec:
Component has not changed to the mode for firmware download. It was not possible to delete the existing firmware.
xxxx = 0090 hex = 144 dec:
When checking the firmware that was downloaded (checksum), the component detected a fault. It is possible that the file
on the memory card is defective.
xxxx = 0091 hex = 145 dec:
Checking the loaded firmware (checksum) was not completed by the component in the appropriate time.
xxxx = 009C hex = 156 dec:
Component with the specified component number is not available (p7828).
xxxx = Additional values:
Only for internal Siemens troubleshooting.
Remedy: - check the selected component number (p7828).
- check the DRIVE-CLiQ wiring.
- save suitable firmware file for download in the directory "/siemens/sinamics/code/sac/".
- use a component with a suitable hardware version
- after POWER ON has been carried out again for the DRIVE-CLiQ component, download firmware again. Depending on
p7826, the firmware will be automatically downloaded.
```

---

### CR-CAND-V6-121 · F01011

- 来源记录：`SIEMENS_S210_2019_F01011`（序号 None）
- 故障描述：Download interrupted
- 候选原因节点：The user prematurely interrupted the project download.
- 目标故障实体：`F01011` · Download interrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01011:cause:3`，字符位置 `156-210`
- 证据原文：> The user prematurely interrupted the project download.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01011 Download interrupted
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The project download was interrupted.
Fault value (r0949, interpret decimal):
1: The user prematurely interrupted the project download.
2: The communication cable was interrupted (e.g. cable breakage, cable withdrawn).
3: The project download was prematurely exited by the commissioning tool.
100: Different versions between the firmware version and project files which were loaded by loading into the file system
"Download from memory card".
Note:
The response to an interrupted download is the state "first commissioning".
Remedy: - check the communication cable.
- download the project again.
- boot from previously saved files (switch-off/switch-on or p0976).
- when loading into the file system (download from memory card), use the matching version.
```

---

### CR-CAND-V6-125 · F01012

- 来源记录：`SIEMENS_S210_2019_F01012`（序号 None）
- 故障描述：Project conversion error
- 候选原因节点：The temperature evaluation is no longer assigned to the power unit but to the encoder evaluation.
- 目标故障实体：`F01012` · Project conversion error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01012:cause:3`，字符位置 `295-392`
- 证据原文：> The temperature evaluation is no longer assigned to the power unit but to the encoder evaluation.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01012 Project conversion error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: When converting the project of an older firmware version, an error occurred.
Fault value (r0949, interpret decimal):
Parameter number of the parameter causing the error.
For fault value = 600, the following applies:
The temperature evaluation is no longer assigned to the power unit but to the encoder evaluation.
Notice:
Monitoring of the motor temperature is no longer ensured.
424 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: Check the parameter indicated in the fault value and correctly adjust it accordingly.
For fault value = 600:
Parameter p0600 must be set to the values 1, 2 or 3 in accordance with the assignment of the internal encoder evaluation
to the encoder interface.
Value 1 means: The internal encoder evaluation is assigned to the encoder interface 1 via p0187.
Value 2 means: The internal encoder evaluation is assigned to the encoder interface 2 via p0188.
Value 3 means: The internal encoder evaluation is assigned to the encoder interface 3 via p0189.
- if necessary, the internal encoder evaluation must be assigned to an encoder interface via parameters p0187, p0188 or
p0189 accordingly.
- if necessary, upgrade the firmware to a later version.
```

---

### CR-CAND-V6-126 · F01018

- 来源记录：`SIEMENS_S210_2019_F01018`（序号 None）
- 故障描述：Booting has been interrupted several times
- 候选原因节点：CPU crashed
- 目标故障实体：`F01018` · Booting has been interrupted several times
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01018:cause:4`，字符位置 `279-290`
- 证据原文：> CPU crashed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01018 Booting has been interrupted several times
Reaction: NONE
Acknowledge: POWER ON
Cause: Module booting was interrupted several times. As a consequence, the module boots with the factory setting.
Possible reasons for booting being interrupted:
- power supply interrupted.
- CPU crashed.
- parameterization invalid.
Remedy: - carry out a POWER ON (switch-off/switch-on). After switching on, the module reboots from the valid parameterization (if
available).
- restore the valid parameterization.
Examples:
a) Carry out a first commissioning, save, carry out a POWER ON (switch-off/switch-on).
b) Load another valid parameter backup (e.g. from the memory card), save, carry out a POWER ON (switch-off/switch-on).
Note:
If the fault situation is repeated, then this fault is again output after several interrupted boots.
```

---

### CR-CAND-V6-128 · F01033

- 来源记录：`SIEMENS_S210_2019_F01033`（序号 None）
- 故障描述：Reference parameter value invalid
- 候选原因节点：When changing over the units to the referred representation type, a required reference parameter is equal to 0.0
- 目标故障实体：`F01033` · Reference parameter value invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01033:cause:7`，字符位置 `106-257`
- 证据原文：> When changing over the units to the referred representation type, it is not permissible for any of the required reference parameters to be equal to 0.0

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01033 Units changeover: Reference parameter value invalid
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: When changing over the units to the referred representation type, it is not permissible for any of the required reference
parameters to be equal to 0.0
Fault value (r0949, parameter):
Reference parameter whose value is 0.0.
Remedy: Set the value of the reference parameter to a number different than 0.0.
See also: r0304 (Rated motor voltage), r0305 (Rated motor current), p2000 (Reference speed), p2003 (Reference torque)
```

---

### CR-CAND-V6-129 · F01034

- 来源记录：`SIEMENS_S210_2019_F01034`（序号 None）
- 故障描述：Calculation parameter values after reference value change unsuccessful
- 候选原因节点：The change of a reference parameter meant that for an involved parameter the selected value was not able to be re-calculated in the per unit representation.
- 目标故障实体：`F01034` · Calculation parameter values after reference value change unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01034:cause:2`，字符位置 `143-300`
- 证据原文：> The change of a reference parameter meant that for an involved parameter the selected value was not able to be re- calculated in the per unit representation.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01034 Units changeover: Calculation parameter values after reference value change unsuccessful
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The change of a reference parameter meant that for an involved parameter the selected value was not able to be re-
calculated in the per unit representation. The change was rejected and the original parameter value restored.
Fault value (r0949, parameter):
Parameter whose value was not able to be re-calculated.
See also: r0304 (Rated motor voltage), r0305 (Rated motor current), p2000 (Reference speed), p2003 (Reference torque)
Remedy: - Select the value of the reference parameter such that the parameter involved can be calculated in the per unit
representation.
- technology unit selection (p0595) before changing the reference parameter p0596, set p0595 = 1.
```

---

### CR-CAND-V6-130 · F01036

- 来源记录：`SIEMENS_S210_2019_F01036`（序号 None）
- 故障描述：Parameter back-up file missing
- 候选原因节点：When downloading the device parameterization, a parameter back-up file PSxxxyyy.ACX associated with a drive object cannot be found.
- 目标故障实体：`F01036` · Parameter back-up file missing
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01036:cause:4`，字符位置 `90-221`
- 证据原文：> When downloading the device parameterization, a parameter back-up file PSxxxyyy.ACX associated with a drive object cannot be found.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01036 ACX: Parameter back-up file missing
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: When downloading the device parameterization, a parameter back-up file PSxxxyyy.ACX associated with a drive object
cannot be found.
Fault value (r0949, interpret hexadecimal):
Byte 1: yyy in the file name PSxxxyyy.ACX
yyy = 000 --> consistency back-up file
yyy = 001 ... 062 --> drive object number
yyy = 099 --> PROFIBUS parameter back-up file
Byte 2, 3, 4:
Only for internal Siemens troubleshooting.
Remedy: If you have saved your project data using the commissioning tool, carry-out a new download for your project.
Save using the function "Copy RAM to ROM" or with p0977 = 1.
This means that the parameter files are again completely written into the non-volatile memory.
Note:
If the project data have not been backed up, then a new first commissioning is required.
```

---

### CR-CAND-V6-131 · F01039

- 来源记录：`SIEMENS_S210_2019_F01039`（序号 None）
- 故障描述：Writing to the parameter back-up file was unsuccessful
- 候选原因节点：in the directory /USER/SINAMICS/DATA/ at least one parameter back-up file PSxxxyyy.*** has the 'read only' file attribute and cannot be overwritten
- 目标故障实体：`F01039` · Writing to the parameter back-up file was unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01039:cause:8`，字符位置 `221-368`
- 证据原文：> in the directory /USER/SINAMICS/DATA/ at least one parameter back-up file PSxxxyyy.*** has the "read only" file attribute and cannot be overwritten

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01039 ACX: Writing to the parameter back-up file was unsuccessful
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: Writing to at least one parameter back-up file PSxxxyyy.*** in the non-volatile memory was unsuccessful.
- in the directory /USER/SINAMICS/DATA/ at least one parameter back-up file PSxxxyyy.*** has the "read only" file attribute
and cannot be overwritten.
- there is not sufficient free memory space available.
- the non-volatile memory is defective and cannot be written to.
Fault value (r0949, interpret hexadecimal):
dcba hex
a = yyy in the file names PSxxxyyy.***
a = 000 --> consistency back-up file
a = 001 ... 062 --> drive object number
a = 070 --> FEPROM.BIN
a = 080 --> DEL4BOOT.TXT
a = 099 --> PROFIBUS parameter back-up file
b = xxx in the file names PSxxxyyy.***
b = 000 --> data save started with p0977 = 1 or p0971 = 1
b = 010 --> data save started with p0977 = 10
b = 011 --> data save started with p0977 = 11
b = 012 --> data save started with p0977 = 12
d, c:
Only for internal Siemens troubleshooting.
Remedy: - check the file attribute of the files (PSxxxyyy.***, CAxxxyyy.***, CCxxxyyy.***) and, if required, change from "read only" to
"writeable".
- check the free memory space in the non-volatile memory. Approx. 80 kbyte of free memory space is required for every
drive object in the system.
- replace the memory card or Control Unit.
```

---

### CR-CAND-V6-134 · F01040

- 来源记录：`SIEMENS_S210_2019_F01040`（序号 None）
- 故障描述：Save parameter settings and carry out a POWER ON
- 候选原因节点：A parameter was changed
- 目标故障实体：`F01040` · Save parameter settings and carry out a POWER ON
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01040:cause:2`，字符位置 `100-123`
- 证据原文：> A parameter was changed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01040 Save parameter settings and carry out a POWER ON
Reaction: OFF2
Acknowledge: POWER ON
Cause: A parameter was changed, which means that it is necessary to save the parameters and reboot.
Remedy: - save parameters (p0977).
- carry out a POWER ON (switch-off/switch-on).
Then:
‑ upload the data to the converter (commissioning tool).
428 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V6-135 · F01041

- 来源记录：`SIEMENS_S210_2019_F01041`（序号 None）
- 故障描述：Parameter save necessary
- 候选原因节点：Defective or missing files were detected on the memory card when booting.
- 目标故障实体：`F01041` · Parameter save necessary
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01041:cause:2`，字符位置 `79-152`
- 证据原文：> Defective or missing files were detected on the memory card when booting.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01041 Parameter save necessary
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: Defective or missing files were detected on the memory card when booting.
Fault value (r0949, interpret decimal):
1: Source file cannot be opened.
2: Source file cannot be read.
3: Target directory cannot be set up.
4. Target file cannot be set up/opened.
5. Target file cannot be written to.
Additional values:
Only for internal Siemens troubleshooting.
Remedy: - save the parameters.
- download the project again to the drive unit.
- update the firmware
- if required, replace the Control Unit and/or memory card card.
```

---

### CR-CAND-V6-141 · F01042

- 来源记录：`SIEMENS_S210_2019_F01042`（序号 38）
- 故障描述：Parameter error during project download
- 候选原因节点：An error was detected when downloading a project using the commissioning software (e.g. incorrect parameter value)
- 目标故障实体：`F01042` · Parameter error during project download
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01042:cause:59`，字符位置 `94-208`
- 证据原文：> An error was detected when downloading a project using the commissioning software (e.g. incorrect parameter value)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01042 Parameter error during project download
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: An error was detected when downloading a project using the commissioning software (e.g. incorrect parameter value). It
is possible that the parameter limits are dependent on other parameters.
The detailed cause of the fault can be determined using the fault value.
Fault value (r0949, interpret hexadecimal):
ccbbaaaa hex
aaaa = Parameter
bb = Index
cc = fault cause
0: Parameter number illegal.
1: Parameter value cannot be changed.
2: Lower or upper value limit exceeded.
3: Sub-index incorrect.
4: No array, no sub-index.
5: Data type incorrect.
6: Setting not permitted (only resetting).
7: Descriptive element cannot be changed.
9: Descriptive data not available.
11: No master control.
15: No text array available.
17: Task cannot be executed due to operating state.
20: Illegal value.
21: Response too long.
22: Parameter address illegal.
23: Format illegal.
24: Number of values not consistent.
25: Drive object does not exist.
101: Presently deactivated.
104: Illegal value.
107: Write access not permitted when controller enabled.
108: Unit unknown.
109: Write access only in the commissioning state, encoder (p0010 = 4).
110: Write access only in the commissioning state, motor (p0010 = 3).
111: Write access only in the commissioning state, power unit (p0010 = 2).
112: Write access only in the quick commissioning mode (p0010 = 1).
113: Write access only in the ready mode (p0010 = 0).
114: Write access only in the commissioning state, parameter reset (p0010 = 30).
115: Write access only in the Safety Integrated commissioning state (p0010 = 95).
116: Write access only in the commissioning state, technological application/units (p0010 = 5).
117: Write access only in the commissioning state (p0010 not equal to 0).
118: Write access only in the commissioning state, download (p0010 = 29).
119: Parameter may not be written in download.
120: Write access only in the commissioning state, drive basic configuration (device: p0009 = 3).
121: Write access only in the commissioning state, define drive type (device: p0009 = 2).
122: Write access only in the commissioning state, data set basic configuration (device: p0009 = 4).
123: Write access only in the commissioning state, device configuration (device: p0009 = 1).
124: Write access only in the commissioning state, device download (device: p0009 = 29).
125: Write access only in the commissioning state, device parameter reset (device: p0009 = 30).
126: Write access only in the commissioning state, device ready (device: p0009 = 0).
127: Write access only in the commissioning state, device (device: p0009 not equal to 0).
129: Parameter may not be written in download.
130: Transfer of the master control is inhibited via binector input p0806.
131: Required BICO interconnection not possible because BICO output does not supply floating value
430 Operating Instructions, 01/2019, A5E41702836B AC
132: Free BICO interconnection inhibited via p0922.
133: Access method not defined.
200: Below the valid values.
201: Above the valid values.
202: Cannot be accessed from the Basic Operator Panel (BOP).
203: Cannot be read from the Basic Operator Panel (BOP).
204: Write access not permitted.
Remedy: - correct the parameterization in the commissioning tool and download the project again.
- enter the correct value in the specified parameter.
- identify the parameter that restricts the limits of the specified parameter.
```

---

### CR-CAND-V6-192 · F01043

- 来源记录：`SIEMENS_S210_2019_F01043`（序号 None）
- 故障描述：Fatal error at project download
- 候选原因节点：A fatal error was detected when downloading a project using the commissioning tool.
- 目标故障实体：`F01043` · Fatal error at project download
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01043:cause:2`，字符位置 `86-169`
- 证据原文：> A fatal error was detected when downloading a project using the commissioning tool.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01043 Fatal error at project download
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: A fatal error was detected when downloading a project using the commissioning tool.
Fault value (r0949, interpret decimal):
1: Device status cannot be changed to Device Download (drive object ON?).
2: Incorrect drive object number.
3: A drive object that has already been deleted is deleted again.
4: Deleting of a drive object that has already been registered for generation.
5: Deleting a drive object that does not exist.
6: Generating an undeleted drive object that already existed.
7: Regenerating a drive object already registered for generation.
8: Maximum number of drive objects that can be generated exceeded.
9: Error while generating a device drive object.
10: Error while generating target topology parameters (p9902 and p9903).
11: Error while generating a drive object (global component).
12: Error while generating a drive object (drive component).
13: Unknown drive object type.
14: Drive status cannot be changed to "ready for operation" (r0947 and r0949).
15: Drive status cannot be changed to drive download.
16: Device status cannot be changed to "ready for operation".
17: It is not possible to download the topology. The component wiring should be checked, taking into account the various
messages/signals.
18: A new download is only possible if the factory settings are restored for the drive unit.
19: The slot for the option module has been configured several times (e.g. CAN and COMM BOARD)
20: The configuration is inconsistent (e.g. CAN for Control Unit, however no CAN configured for drive objects A_INF,
SERVO or VECTOR).
21: Error when accepting the download parameters.
22: Software-internal download error.
23: download not possible when know-how protection is activated.
24: download not possible during a partial power up after inserting a component.
25: The configuration is inconsistent. Know-how protection is either not activated or only partially.
Additional values:
Only for internal Siemens troubleshooting.
Remedy: - use the current version of the commissioning tool.
- modify the offline project and carry out a new download (e.g. compare the number of drive objects, motor, encoder, power
unit in the offline project and at the drive).
- change the drive state (is a drive rotating or is there a message/signal?).
- carefully note any other active messages/signals and remove their cause (e.g. correct any incorrectly set parameters).
- automatically calculate the control parameters (p0340). Then set p0010 = 0.
- boot from previously saved files (switch-off/switch-on or p0976).
- before a new download, restore the factory setting if the know-how protection was not activated on all drive objects.
```

---

### CR-CAND-V6-218 · F01050

- 来源记录：`SIEMENS_S210_2019_F01050`（序号 None）
- 故障描述：Memory card and device incompatible
- 候选原因节点：The memory card and the device type do not match (e.g. a memory card for SINAMICS S is inserted in SINAMICS G).
- 目标故障实体：`F01050` · Memory card and device incompatible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01050:cause:2`，字符位置 `90-201`
- 证据原文：> The memory card and the device type do not match (e.g. a memory card for SINAMICS S is inserted in SINAMICS G).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01050 Memory card and device incompatible
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The memory card and the device type do not match (e.g. a memory card for SINAMICS S is inserted in SINAMICS G).
Remedy: - insert the matching memory card.
- use the matching Control Unit or power unit.
```

---

### CR-CAND-V6-219 · F01072

- 来源记录：`SIEMENS_S210_2019_F01072`（序号 None）
- 故障描述：Memory card restored from the backup copy
- 候选原因节点：The Control Unit was switched-off while writing to the memory card. This is why the visible partition became defective.
- 目标故障实体：`F01072` · Memory card restored from the backup copy
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01072:cause:3`，字符位置 `96-215`
- 证据原文：> The Control Unit was switched-off while writing to the memory card. This is why the visible partition became defective.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01072 Memory card restored from the backup copy
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: The Control Unit was switched-off while writing to the memory card. This is why the visible partition became defective.
After switching on, the data from the non-visible partition (backup copy) were written to the visible partition.
Remedy: Check that the firmware and parameterization is up-to-date.
```

---

### CR-CAND-V6-220 · F01082

- 来源记录：`SIEMENS_S210_2019_F01082`（序号 None）
- 故障描述：Parameter error when powering up from data backup
- 候选原因节点：Parameterizing errors have been detected (e.g. incorrect parameter value)
- 目标故障实体：`F01082` · Parameter error when powering up from data backup
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01082:cause:3`，字符位置 `104-177`
- 证据原文：> Parameterizing errors have been detected (e.g. incorrect parameter value)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01082 Parameter error when powering up from data backup
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: Parameterizing errors have been detected (e.g. incorrect parameter value). It is possible that the parameter limits are
dependent on other parameters.
The detailed cause of the fault can be determined using the fault value.
Fault value (r0949, interpret hexadecimal):
ccbbaaaa hex
aaaa = Parameter
bb = Index
cc = fault cause
0: Parameter number illegal.
1: Parameter value cannot be changed.
2: Lower or upper value limit exceeded.
3: Sub-index incorrect.
4: No array, no sub-index.
5: Data type incorrect.
6: Setting not permitted (only resetting).
7: Descriptive element cannot be changed.
9: Descriptive data not available.
11: No master control.
15: No text array available.
17: Task cannot be executed due to operating state.
20: Illegal value.
21: Response too long.
22: Parameter address illegal.
23: Format illegal.
24: Number of values not consistent.
25: Drive object does not exist.
101: Presently deactivated.
104: Illegal value.
107: Write access not permitted when controller enabled.
108: Unit unknown.
109: Write access only in the commissioning state, encoder (p0010 = 4).
110: Write access only in the commissioning state, motor (p0010 = 3).
111: Write access only in the commissioning state, power unit (p0010 = 2).
112: Write access only in the quick commissioning mode (p0010 = 1).
113: Write access only in the ready mode (p0010 = 0).
114: Write access only in the commissioning state, parameter reset (p0010 = 30).
115: Write access only in the Safety Integrated commissioning state (p0010 = 95).
116: Write access only in the commissioning state, technological application/units (p0010 = 5).
117: Write access only in the commissioning state (p0010 not equal to 0).
118: Write access only in the commissioning state, download (p0010 = 29).
119: Parameter may not be written in download.
120: Write access only in the commissioning state, drive basic configuration (device: p0009 = 3).
121: Write access only in the commissioning state, define drive type (device: p0009 = 2).
122: Write access only in the commissioning state, data set basic configuration (device: p0009 = 4).
123: Write access only in the commissioning state, device configuration (device: p0009 = 1).
124: Write access only in the commissioning state, device download (device: p0009 = 29).
125: Write access only in the commissioning state, device parameter reset (device: p0009 = 30).
126: Write access only in the commissioning state, device ready (device: p0009 = 0).
127: Write access only in the commissioning state, device (device: p0009 not equal to 0).
129: Parameter may not be written in download.
130: Transfer of the master control is inhibited via binector input p0806.
131: Required BICO interconnection not possible because BICO output does not supply floating value
434 Operating Instructions, 01/2019, A5E41702836B AC
132: Free BICO interconnection inhibited via p0922.
133: Access method not defined.
200: Below the valid values.
201: Above the valid values.
202: Cannot be accessed from the Basic Operator Panel (BOP).
203: Cannot be read from the Basic Operator Panel (BOP).
204: Write access not permitted.
Remedy: - correct the parameterization in the commissioning tool and download the project again.
- enter the correct value in the specified parameter.
- identify the parameter that restricts the limits of the specified parameter.
```

---

### CR-CAND-V6-271 · F01120

- 来源记录：`SIEMENS_S210_2019_F01120`（序号 None）
- 故障描述：Terminal initialization has failed
- 候选原因节点：An internal software error occurred while the terminal functions were being initialized.
- 目标故障实体：`F01120` · Terminal initialization has failed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01120:cause:3`，字符位置 `89-177`
- 证据原文：> An internal software error occurred while the terminal functions were being initialized.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01120 Terminal initialization has failed
Reaction: OFF1
Acknowledge: IMMEDIATELY
Cause: An internal software error occurred while the terminal functions were being initialized.
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade firmware to later version.
- contact Technical Support.
- replace the Control Unit.
```

---

### CR-CAND-V6-272 · F01122

- 来源记录：`SIEMENS_S210_2019_F01122`（序号 None）
- 故障描述：Frequency at the measuring probe input too high
- 候选原因节点：The frequency of the pulses at the measuring probe input is too high.
- 目标故障实体：`F01122` · Frequency at the measuring probe input too high
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01122:cause:2`，字符位置 `102-171`
- 证据原文：> The frequency of the pulses at the measuring probe input is too high.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01122 Frequency at the measuring probe input too high
Reaction: OFF1
Acknowledge: IMMEDIATELY
Cause: The frequency of the pulses at the measuring probe input is too high.
Fault value (r0949, interpret decimal):
1: DI/DO 9 (X122.8)
2: DI/DO 10 (X122.10)
4: DI/DO 11 (X122.11)
8: DI/DO 13 (X132.8)
16: DI/DO 14 (X132.10)
32: DI/DO 15 (X132.11)
64: DI/DO 8 (X122.7)
128: DI/DO 12 (X132.7)
Remedy: Reduce the frequency of the pulses at the measuring probe input.
```

---

### CR-CAND-V6-273 · F01250

- 来源记录：`SIEMENS_S210_2019_F01250`（序号 None）
- 故障描述：CU-EEPROM incorrect read-only data
- 候选原因节点：Error when reading the read-only data of the EEPROM in the Control Unit.
- 目标故障实体：`F01250` · CU-EEPROM incorrect read-only data
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01250:cause:3`，字符位置 `90-162`
- 证据原文：> Error when reading the read-only data of the EEPROM in the Control Unit.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01250 CU: CU-EEPROM incorrect read-only data
Reaction: NONE
Acknowledge: POWER ON
Cause: Error when reading the read-only data of the EEPROM in the Control Unit.
Fault value (r0949, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on).
- replace the Control Unit.
```

---

### CR-CAND-V6-274 · F01357

- 来源记录：`SIEMENS_S210_2019_F01357`（序号 39）
- 故障描述：Topology: Two Control Units identified on the DRIVE-CLiQ line
- 候选原因节点：In the actual topology, 2 Control Units are connected with one another through DRIVE-CLiQ.
- 目标故障实体：`F01357` · Topology: Two Control Units identified on the DRIVE-CLiQ line
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01357:cause:6`，字符位置 `116-206`
- 证据原文：> In the actual topology, 2 Control Units are connected with one another through DRIVE-CLiQ.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01357 Topology: Two Control Units identified on the DRIVE-CLiQ line
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: In the actual topology, 2 Control Units are connected with one another through DRIVE-CLiQ.
As standard, this is not permitted.
This is only permitted if the Technology Extension OALINK has already been installed on the two Control Units and has been
commissioned online.
Fault value (r0949, interpret hexadecimal):
yyxx hex:
yy = connection number of the Control Unit at which the second Control Unit is connected
xx = component number of the Control Unit at which the second Control Unit is connected
Note:
Pulse enable is withdrawn and prevented.
Remedy: In general:
- remove the connection to the second Control Unit and restart.
- for the S120M component DRIVE-CLiQ extension, interchange the hybrid cable (IN/OUT).
When using OALINK:
- remove the DRIVE-CLiQ connection and restart the systems.
- install OALINK on both Control Units and activate.
- Check the configuration of the DRIVE-CLiQ sockets in OALINK.
```

---

### CR-CAND-V6-275 · F01600

- 来源记录：`SIEMENS_S210_2019_F01600`（序号 None）
- 故障描述：STO initiated
- 候选原因节点：The 'Safety Integrated' function integrated in the drive has identified a fault in monitoring channel 1, and has initiated STO.
- 目标故障实体：`F01600` · STO initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01600:cause:9`，字符位置 `75-201`
- 证据原文：> The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1, and has initiated STO

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01600 SI P1: STO initiated
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function integrated in the drive has identified a fault in monitoring channel 1, and has initiated STO.
- forced checking procedure (test stop) of the safety switch-off signal path of monitoring channel 1 unsuccessful.
- subsequent response to fault F01611 (defect in a monitoring channel).
Fault value (r0949, decimal interpretation):
0: Stop request from another monitoring channel.
1005: STO active, although no STO is selected and no stop response with STO is active.
1010: STO inactive, although STO is selected or a stop response with STO is active.
9999: Subsequent response to fault F01611.
Remedy: - select Safe Torque Off and deselect again.
- replace drive.
For fault value = 9999:
- carry out diagnostics for fault F01611.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V6-280 · F01625

- 来源记录：`SIEMENS_S210_2019_F01625`（序号 None）
- 故障描述：sign-of-life error in the safety data
- 候选原因节点：DRIVE-CLiQ communication error or communication has failed
- 目标故障实体：`F01625` · sign-of-life error in the safety data
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01625:cause:3`，字符位置 `287-345`
- 证据原文：> DRIVE-CLiQ communication error or communication has failed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01625 SI P1: sign-of-life error in the safety data
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function integrated in the drive has identified an error in the sign-of-life of the safety data in
monitoring channel 1, and has initiated STO.
- there is either a DRIVE-CLiQ communication error or communication has failed.
- a time slice overflow of the safety software has occurred.
Fault value (r0949, decimal interpretation):
Only for internal Siemens troubleshooting.
Remedy: - select STO and then deselect again.
- carry out a POWER ON (switch-off/switch-on).
- check whether there is a DRIVE-CLiQ communication error between the two monitoring channels and, if required, carry
out a diagnostics routine for the faults identified.
- deselect all drive functions that are not absolutely necessary.
- check the electrical cabinet design and cable routing for EMC compliance
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V6-282 · F01630

- 来源记录：`SIEMENS_S210_2019_F01630`（序号 None）
- 故障描述：Brake control error
- 候选原因节点：OCC cable shield is not correctly connected.
- 目标故障实体：`F01630` · Brake control error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01630:cause:3`，字符位置 `225-269`
- 证据原文：> OCC cable shield is not correctly connected.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01630 SI P1: Brake control error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function integrated in the drive has identified a brake control fault in monitoring channel 1, and has
initiated STO.
- OCC cable shield is not correctly connected.
- defect in the brake control circuit of the drive.
Fault value (r0949, decimal interpretation):
10, 11:
Fault in "open brake" operation.
- brake not closed or interrupted cable.
- ground fault in brake cable.
20:
Fault in "brake open" state.
- short-circuit in brake winding.
30, 31:
Fault in "close brake" operation.
- brake not closed or interrupted cable.
- short-circuit in brake winding.
40:
Fault in "brake closed" state.
50:
Fault in the brake control of the drive or a communication error (brake control diagnostics).
442 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: - select STO and then deselect again.
- check the motor holding brake connection.
- check the function of the motor holding brake.
- carry out a diagnostics routine for the faults involved.
- check for EMC-compliant control cabinet design and cable routing (e.g. shield OCC cable with shield terminal and shield
plate, check the connection of the brake conductors).
- replace drive.
Note:
OCC: One Cable Connection (one cable system)
SBC: Safe Brake Control
SI: Safety Integrated
STO: Safe Torque Off
See also: p1215 (Motor holding brake configuration)
```

---

### CR-CAND-V6-292 · F01640

- 来源记录：`SIEMENS_S210_2019_F01640`（序号 None）
- 故障描述：component exchange identified and acknowledge/save necessary
- 候选原因节点：'Safety Integrated' has identified that a component has been replaced.
- 目标故障实体：`F01640` · component exchange identified and acknowledge/save necessary
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01640:cause:10`，字符位置 `123-191`
- 证据原文：> Safety Integrated" has identified that a component has been replaced

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01640 SI P1: component exchange identified and acknowledge/save necessary
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: "Safety Integrated" has identified that a component has been replaced.
It is no longer possible to operate the particular drive without fault.
When safety functions are active, after a component has been replaced it is necessary to carry out a partial acceptance test.
Fault value (r0949, interpret binary):
Bit 0 = 1:
It has been identified that the drive has been replaced.
Bit 3 = 1:
It has been identified that the Sensor Module has been replaced.
Bit 5 = 1:
It has been identified that the sensor has been replaced.
Remedy: - save all parameters
- acknowledge fault.
Note:
In addition to the fault, diagnostics bits r9776.2 and r9776.3 are set.
See also: r9776 (SI diagnostics)
```

---

### CR-CAND-V6-296 · F01641

- 来源记录：`SIEMENS_S210_2019_F01641`（序号 None）
- 故障描述：component exchange identified and save necessary
- 候选原因节点：Safety Integrated has identified that a component has been replaced
- 目标故障实体：`F01641` · component exchange identified and save necessary
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01641:cause:8`，字符位置 `111-179`
- 证据原文：> Safety Integrated" has identified that a component has been replaced

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01641 SI P1: component exchange identified and save necessary
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: "Safety Integrated" has identified that a component has been replaced.
No additional fault response is initiated, therefore operation of the particular drive is not restricted.
When safety functions are active, after a component has been replaced it is necessary to carry out a partial acceptance test.
Fault value (r0949, interpret binary):
Bit 0 = 1:
It has been identified that the drive has been replaced.
Bit 3 = 1:
It has been identified that the Sensor Module has been replaced.
Bit 5 = 1:
It has been identified that the sensor has been replaced.
Remedy: - save all parameters
- acknowledge fault.
See also: r9776 (SI diagnostics)
```

---

### CR-CAND-V6-300 · F01649

- 来源记录：`SIEMENS_S210_2019_F01649`（序号 None）
- 故障描述：Internal software error
- 候选原因节点：An internal error in the Safety Integrated software in monitoring channel 1 has occurred.
- 目标故障实体：`F01649` · Internal software error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01649:cause:3`，字符位置 `85-174`
- 证据原文：> An internal error in the Safety Integrated software in monitoring channel 1 has occurred.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01649 SI P1: Internal software error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: An internal error in the Safety Integrated software in monitoring channel 1 has occurred.
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on).
- re-commission the "Safety Integrated" function and carry out a POWER ON.
- upgrade the drive firmware to a later version.
- contact Technical Support.
- replace drive.
Note:
SI: Safety Integrated
STO: Safe Torque Off
444 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V6-301 · F01650

- 来源记录：`SIEMENS_S210_2019_F01650`（序号 40）
- 故障描述：Acceptance test required
- 候选原因节点：The 'Safety Integrated' function on monitoring channel 1 requires an acceptance test.
- 目标故障实体：`F01650` · Acceptance test required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01650:cause:2`，字符位置 `86-171`
- 证据原文：> The "Safety Integrated" function on monitoring channel 1 requires an acceptance test.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01650 SI P1: Acceptance test required
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function on monitoring channel 1 requires an acceptance test.
Note:
This fault results in an STO that can be acknowledged.
Fault value (r0949, interpret decimal):
130: Safety parameters for monitoring channel 2 not available.
Note:
This fault value is always output when Safety Integrated is commissioned for the first time.
1000: Reference and actual checksum in monitoring channel 1 are not identical (booting).
- safety parameters set offline and loaded to the drive.
- at least one checksum-checked piece of data is defective.
2000: Reference and actual checksum in monitoring channel 1 are not identical (commissioning mode).
2001: Reference and actual checksum in monitoring channel 2 are not identical (commissioning mode).
2002: Enable of safety-related functions between the two monitoring channels differ.
2003: Acceptance test is required as a safety parameter has been changed.
2004: An acceptance test is required because a project with enabled safety-functions has been downloaded.
2005: The safety logbook has identified that the safety checksums have changed.
2010: Safe brake control enable different between both monitoring channels.
2020: Error when saving the safety parameters for the monitoring channel 2.
3003: Acceptance test is required as a hardware-related safety parameter has been changed.
3005: The Safety logbook has identified that a hardware-related safety checksum has changed.
9999: Subsequent response of another safety-related fault that occurred when booting that requires an acceptance test.
Remedy: For fault value = 130:
- carry out safety commissioning routine.
For fault value = 1000:
- again carry out safety commissioning routine.
- replace the memory card or drive.
For fault value = 2000:
- confirm the data change using the commissioning tool.
For fault value = 2001:
- confirm the data change using the commissioning tool.
For fault value = 2002:
- using the commissioning tool, copy the safety parameters and confirm the data change.
For fault value = 2003, 2004, 2005:
- carry out an acceptance test and generate an acceptance report.
Note:
The fault with fault value 2005 can only be acknowledged when the "STO" function is deselected.
For fault value = 2010:
- check that safe brake control is enabled.
- using the commissioning tool, copy the safety parameters and confirm the data change.
For fault value = 2020:
- again carry out safety commissioning routine.
- replace the memory card or drive.
For fault value = 3003:
- carry out the function checks for the modified hardware and generate an acceptance report.
For fault value = 3005:
- carry out the function checks for the modified hardware and generate an acceptance report.
Note:
The fault with fault value 3005 can only be acknowledged when the "STO" function is deselected.
For fault value = 9999:
- carry out diagnostics for the other safety-related fault that is present.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---
