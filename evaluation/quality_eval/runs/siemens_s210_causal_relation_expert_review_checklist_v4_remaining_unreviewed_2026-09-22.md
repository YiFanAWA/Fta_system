# Siemens S210 因果关系候选专家审核清单 v4

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。本批从 v1/v2/v3 已审核候选之外的原因中生成，并保留现有 Gold 的原文证据；`causes` 字段本身不等于已证明的因果关系。

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

### CR-CAND-V4-001 · A01016

- 来源记录：`SIEMENS_S210_2019_A01016`（序号 None）
- 故障描述：Firmware changed
- 候选原因节点：Checksum of one file is incorrect.
- 目标故障实体：`A01016` · Firmware changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01016:cause:3`，字符位置 `287-321`
- 证据原文：> Checksum of one file is incorrect.

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

### CR-CAND-V4-006 · A01035

- 来源记录：`SIEMENS_S210_2019_A01035`（序号 None）
- 故障描述：Parameter back-up file corrupted
- 候选原因节点：The last time that the parameterization was saved, it was not completely carried out.
- 目标故障实体：`A01035` · Parameter back-up file corrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01035:cause:4`，字符位置 `183-268`
- 证据原文：> The last time that the parameterization was saved, it was not completely carried out.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01035 ACX: Parameter back-up file corrupted
Reaction: NONE
Acknowledge: NONE
Cause: When the Control Unit is booted, no complete data set was found from the parameter back-up files. The last time that the
parameterization was saved, it was not completely carried out.
It is possible that the backup was interrupted by switching off or withdrawing the memory card.
Alarm value (r2124, interpret hexadecimal):
ddccbbaa hex:
aa = 01 hex:
Power up was realized without data backup. The drive is in the factory setting.
aa = 02 hex:
The last available backup data record was loaded. The parameterization must be checked. It is recommended that the
parameterization is downloaded again.
dd, cc, bb:
Only for internal Siemens troubleshooting.
See also: p0977 (Save all parameters)
Remedy: - download the project again using the commissioning tool.
- save all parameters (p0977 = 1 or "copy RAM to ROM").
See also: p0977 (Save all parameters)
```

---

### CR-CAND-V4-008 · A01654

- 来源记录：`SIEMENS_S210_2019_A01654`（序号 None）
- 故障描述：Deviating PROFIsafe configuration
- 候选原因节点：A PROFIsafe telegram is configured in the higher-level control, however PROFIsafe is not enabled in the drive (p9601.3).
- 目标故障实体：`A01654` · Deviating PROFIsafe configuration
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01654:cause:4`，字符位置 `321-441`
- 证据原文：> A PROFIsafe telegram is configured in the higher-level control, however PROFIsafe is not enabled in the drive (p9601.3).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01654 SI P1: Deviating PROFIsafe configuration
Reaction: NONE
Acknowledge: NONE
Cause: The configuration of a PROFIsafe telegram in the higher-level control (F-PLC) does not match the parameterization in the
drive.
Note:
This message does not result in a safety stop response.
Alarm value (r2124, interpret decimal):
1:
A PROFIsafe telegram is configured in the higher-level control, however PROFIsafe is not enabled in the drive (p9601.3).
2:
PROFIsafe is parameterized in the drive; however, a PROFIsafe telegram has not been configured in the higher-level
control.
Remedy: The following generally applies:
- check and, if necessary, correct the PROFIsafe configuration in the higher-level control.
For alarm value = 1:
- remove the PROFIsafe configuring in the higher-level F control or enable PROFIsafe in the drive.
For alarm value = 2:
- configure the PROFIsafe telegram to match the parameterization in the higher-level F-control.
```

---

### CR-CAND-V4-010 · A01691

- 来源记录：`SIEMENS_S210_2019_A01691`（序号 None）
- 故障描述：Ti and To unsuitable for PN cycle
- 候选原因节点：Isochronous PROFINET: The sum of Ti and To is too high for the selected PN cycle. The PN clock cycle should be at least 1 current controller cycle greater than the sum of Ti and To.
- 目标故障实体：`A01691` · Ti and To unsuitable for PN cycle
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01691:cause:4`，字符位置 `265-446`
- 证据原文：> Isochronous PROFINET: The sum of Ti and To is too high for the selected PN cycle. The PN clock cycle should be at least 1 current controller cycle greater than the sum of Ti and To.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

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

---

### CR-CAND-V4-012 · A01706

- 来源记录：`SIEMENS_S210_2019_A01706`（序号 30）
- 故障描述：SAM/SBR limit exceeded
- 候选原因节点：Motion monitoring functions with SBR: after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance
- 目标故障实体：`A01706` · SAM/SBR limit exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01706:cause:5`，字符位置 `203-357`
- 证据原文：> Motion monitoring functions with SBR (p9506 = 2): - after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01706 SI Motion P1: SAM/SBR limit exceeded
Reaction: NONE
Acknowledge: NONE
Cause: Motion monitoring functions with SAM (p9506 = 0):
- after initiating SS1 or SS2, the speed exceeded the set tolerance.
Motion monitoring functions with SBR (p9506 = 2):
- after initiating SS1 or SLS switchover to the lower speed level, the speed exceeded the set tolerance.
The drive is stopped by message F01700.
460 Operating Instructions, 01/2019, A5E41702836B AC
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
See also: p9548 (SI Motion SAM actual speed tolerance), p9581 (SI Motion brake ramp reference value), p9582 (SI Motion
brake ramp delay time), p9583 (SI Motion brake ramp monitoring time)
```

---

### CR-CAND-V4-013 · A01709

- 来源记录：`SIEMENS_S210_2019_A01709`（序号 None）
- 故障描述：SS2E initiated
- 候选原因节点：'Safe Operating Stop' (SOS) is activated after the parameterized time has expired.
- 目标故障实体：`A01709` · SS2E initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01709:cause:5`，字符位置 `133-213`
- 证据原文：> Safe Operating Stop" (SOS) is activated after the parameterized time has expired

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01709 SI Motion P1: SS2E initiated
Reaction: NONE
Acknowledge: NONE
Cause: The drive is stopped using SS2E (braking along a path).
"Safe Operating Stop" (SOS) is activated after the parameterized time has expired.
Possible causes:
Subsequent response, following messages: A01714, A01716
See also: p9553 (SI Motion transition time SS2E to SOS)
Remedy: - remove the cause of the fault at the control.
- carry out diagnostics for the active messages (A01714, A01716).
Note:
SI: Safety Integrated
SOS: Safe Operating Stop
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
```

---

### CR-CAND-V4-014 · A01711

- 来源记录：`SIEMENS_S210_2019_A01711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：The tolerance value for the monitoring function is not the same on the two monitoring channels.
- 目标故障实体：`A01711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01711:cause:135`，字符位置 `2101-2196`
- 证据原文：> The tolerance value for the monitoring function is not the same on the two monitoring channels.

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

### CR-CAND-V4-022 · A01714

- 来源记录：`SIEMENS_S210_2019_A01714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS1 exceeded.
- 目标故障实体：`A01714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01714:cause:4`，字符位置 `284-298`
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

### CR-CAND-V4-027 · A01716

- 来源记录：`SIEMENS_S210_2019_A01716`（序号 None）
- 故障描述：Tolerance for safe motion direction exceeded
- 候选原因节点：Tolerance for function 'safe motion direction positive' exceeded.
- 目标故障实体：`A01716` · Tolerance for safe motion direction exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01716:cause:8`，字符位置 `282-346`
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
A01716 SI Motion P1: Tolerance for safe motion direction exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The tolerance for the "safe motion direction" function was exceeded. The drive is stopped by the configured stop response
(p9566).
Message value (r2124, interpret decimal):
0: Tolerance for function "safe motion direction positive" exceeded.
1: Tolerance for function "safe motion direction negative" exceeded.
Remedy: - check the traversing/motion program in the control.
- check the tolerance for "SDI" function and if required, adapt (p9564).
This message can be acknowledged as follows:
Deselect/select SDI and perform safe acknowledgment via PROFIsafe.
Note:
SDI: Safe Direction (safe motion direction)
SI: Safety Integrated
See also: p9564 (SI Motion SDI tolerance), p9565 (SI Motion SDI delay time), p9566 (SI Motion SDI stop response)
```

---

### CR-CAND-V4-029 · A01730

- 来源记录：`SIEMENS_S210_2019_A01730`（序号 None）
- 故障描述：Reference block for dynamic Safely-Limited Speed invalid
- 候选原因节点：requested, invalid reference block
- 目标故障实体：`A01730` · Reference block for dynamic Safely-Limited Speed invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01730:cause:4`，字符位置 `426-460`
- 证据原文：> requested, invalid reference block

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

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

---

### CR-CAND-V4-030 · A01781

- 来源记录：`SIEMENS_S210_2019_A01781`（序号 None）
- 故障描述：SBT brake opening time exceeded
- 候选原因节点：during the brake test the drive went into a fault condition, and therefore the brake was closed by the drive.
- 目标故障实体：`A01781` · SBT brake opening time exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01781:cause:4`，字符位置 `176-285`
- 证据原文：> during the brake test the drive went into a fault condition, and therefore the brake was closed by the drive.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01781 SBT brake opening time exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The maximum time (11 s) to open the brake during the brake test was exceeded.
Possible causes:
- during the brake test the drive went into a fault condition, and therefore the brake was closed by the drive.
Alarm value (r2124, interpret binary):
Bit 0 = 1:
Internal brake was not able to be opened.
Note:
SBT: Safe Brake Test
Remedy: - carry out a safe acknowledgment.
- restart the brake test.
```

---

### CR-CAND-V4-032 · A01782

- 来源记录：`SIEMENS_S210_2019_A01782`（序号 None）
- 故障描述：SBT brake test incorrect control
- 候选原因节点：The brake test was canceled as a result of a fault (brake opening time or brake closing time exceeded).
- 目标故障实体：`A01782` · SBT brake test incorrect control
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01782:cause:3`，字符位置 `196-299`
- 证据原文：> The brake test was canceled as a result of a fault (brake opening time or brake closing time exceeded).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

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

---

### CR-CAND-V4-034 · A01783

- 来源记录：`SIEMENS_S210_2019_A01783`（序号 None）
- 故障描述：SBT brake closing time exceeded
- 候选原因节点：The brake was not able to be closed.
- 目标故障实体：`A01783` · SBT brake closing time exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01783:cause:4`，字符位置 `208-244`
- 证据原文：> The brake was not able to be closed.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01783 SBT brake closing time exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The maximum time (11 s) to close the brake during the brake test was exceeded.
Alarm value (r2124, interpret binary):
Bit 0 = 1:
The brake was not able to be closed.
Note:
SBT: Safe Brake Test
Remedy: - when using an internal brake with external feedback signal, check whether the feedback signal is correctly interconnected
with the extended brake control.
- carry out a safe acknowledgment.
- restart the brake test.
```

---

### CR-CAND-V4-035 · A01784

- 来源记录：`SIEMENS_S210_2019_A01784`（序号 None）
- 故障描述：SBT brake test canceled with fault
- 候选原因节点：axis position during the brake test not valid due to parking axis
- 目标故障实体：`A01784` · SBT brake test canceled with fault
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01784:cause:3`，字符位置 `309-374`
- 证据原文：> axis position during the brake test not valid due to parking axis

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

### CR-CAND-V4-051 · A01785

- 来源记录：`SIEMENS_S210_2019_A01785`（序号 None）
- 故障描述：SBT brake test configuration error
- 候选原因节点：No motion monitoring functions have been enabled
- 目标故障实体：`A01785` · SBT brake test configuration error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01785:cause:3`，字符位置 `312-360`
- 证据原文：> No motion monitoring functions have been enabled

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

### CR-CAND-V4-055 · A01788

- 来源记录：`SIEMENS_S210_2019_A01788`（序号 31）
- 故障描述：Automatic test stop waits for STO deselection via motion monitoring functions
- 候选原因节点：the STO function is selected via safe motion monitoring functions.
- 目标故障实体：`A01788` · Automatic test stop waits for STO deselection via motion monitoring functions
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01788:cause:7`，字符位置 `250-316`
- 证据原文：> the STO function is selected via safe motion monitoring functions.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01788 SI: Automatic test stop waits for STO deselection via motion monitoring functions
Reaction: NONE
Acknowledge: NONE
Cause: The automatic test stop (forced checking procedure) was not able to be carried out after powering up.
Possible causes:
- the STO function is selected via safe motion monitoring functions.
- a safety message is present, that resulted in a STO.
Note:
STO: Safe Torque Off
Remedy: - deselect STO via safe motion monitoring functions.
- remove the cause of the safety messages and acknowledge the messages.
Note:
The automatic test stop is performed after removing the cause.
```

---

### CR-CAND-V4-057 · A01796

- 来源记录：`SIEMENS_S210_2019_A01796`（序号 None）
- 故障描述：Wait for communication
- 候选原因节点：Wait for communication to be established to PROFIsafe F-Host.
- 目标故障实体：`A01796` · Wait for communication
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01796:cause:4`，字符位置 `267-328`
- 证据原文：> Wait for communication to be established to PROFIsafe F-Host.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01796 SI P1: Wait for communication
Reaction: NONE
Acknowledge: NONE
Cause: The drive waits for communication to be established to execute the safety-relevant motion monitoring functions.
Note:
STO is active in this state.
Alarm value (r2124, interpret decimal):
3: Wait for communication to be established to PROFIsafe F-Host.
Remedy: If the message is not automatically withdrawn after a longer period of time, then carry out the following checks:
- check any other PROFIsafe communication messages/signals present and evaluate them.
- check the operating state of the F-Host.
- check the communication connection to the F Host.
Note:
STO: Safe Torque Off
See also: p9601 (SI enable, functions integrated in the drive)
```

---

### CR-CAND-V4-058 · A01900

- 来源记录：`SIEMENS_S210_2019_A01900`（序号 None）
- 故障描述：Configuration telegram error
- 候选原因节点：Connection established to more drive objects than configured in the device. The drive objects for process data exchange and their sequence are defined in p0978.
- 目标故障实体：`A01900` · Configuration telegram error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01900:cause:4`，字符位置 `212-372`
- 证据原文：> Connection established to more drive objects than configured in the device. The drive objects for process data exchange and their sequence are defined in p0978.

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

### CR-CAND-V4-072 · A01902

- 来源记录：`SIEMENS_S210_2019_A01902`（序号 None）
- 故障描述：clock cycle synchronous operation parameterization not permissible
- 候选原因节点：Bus cycle time Tdp < 0.5 ms.
- 目标故障实体：`A01902` · clock cycle synchronous operation parameterization not permissible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01902:cause:4`，字符位置 `224-252`
- 证据原文：> Bus cycle time Tdp < 0.5 ms.

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

### CR-CAND-V4-086 · A01940

- 来源记录：`SIEMENS_S210_2019_A01940`（序号 None）
- 故障描述：Clock cycle synchronism not reached
- 候选原因节点：The master is using an isochronous DP clock cycle that is different than was transferred to the slave in the parameterizing telegram.
- 目标故障实体：`A01940` · Clock cycle synchronism not reached
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01940:cause:4`，字符位置 `438-571`
- 证据原文：> the master is using an isochronous DP clock cycle that is different than was transferred to the slave in the parameterizing telegram.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01940 PN: Clock cycle synchronism not reached
Reaction: NONE
Acknowledge: NONE
Cause: The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing
telegram. It was not possible to synchronize to the clock cycle specified by the master.
- the master does not send a clock synchronous global control telegram although clock synchronous operation was selected
when configuring the bus.
- the master is using an isochronous DP clock cycle that is different than was transferred to the slave in the parameterizing
telegram.
- at least one drive object has a pulse enable (also not controlled from PROFINET).
Remedy: - check the master application and bus configuration.
- check the consistency between the clock cycle input when configuring the slave and clock cycle setting at the master.
- check that no drive object has a pulse enable. Only enable the pulses after synchronizing the PROFINET drives.
Note:
PN: PROFINET
```

---

### CR-CAND-V4-088 · A01943

- 来源记录：`SIEMENS_S210_2019_A01943`（序号 None）
- 故障描述：Clock cycle signal error when the bus is being established
- 候选原因节点：The global control telegram for synchronization is being irregularly received.
- 目标故障实体：`A01943` · Clock cycle signal error when the bus is being established
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01943:cause:4`，字符位置 `233-311`
- 证据原文：> The global control telegram for synchronization is being irregularly received.

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

### CR-CAND-V4-091 · A01944

- 来源记录：`SIEMENS_S210_2019_A01944`（序号 None）
- 故障描述：Sign-of-life synchronism not reached
- 候选原因节点：The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing telegram.
- 目标故障实体：`A01944` · Sign-of-life synchronism not reached
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01944:cause:3`，字符位置 `88-210`
- 证据原文：> The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing telegram.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01944 PN: Sign-of-life synchronism not reached
Reaction: NONE
Acknowledge: NONE
Cause: The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing
telegram.
Synchronization with the master sign-of-life (STW2.12 ... STW2.15) could not be completed because the sign-of-life is
changing differently to how it was configured in the Tmapc time grid.
Remedy: - ensure that the master correctly increments the sign-of-life in the master application clock cycle Tmapc.
- correct the interconnection of the master sign-of-life (p2045).
Note:
PN: PROFINET
```

---

### CR-CAND-V4-093 · A01980

- 来源记录：`SIEMENS_S210_2019_A01980`（序号 None）
- 故障描述：cyclic connection interrupted
- 候选原因节点：The cyclic connection to the PROFINET controller is interrupted.
- 目标故障实体：`A01980` · cyclic connection interrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01980:cause:3`，字符位置 `81-145`
- 证据原文：> The cyclic connection to the PROFINET controller is interrupted.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01980 PN: cyclic connection interrupted
Reaction: NONE
Acknowledge: NONE
Cause: The cyclic connection to the PROFINET controller is interrupted.
See also: r8936 (Cyclic connection status)
Remedy: Establish the PROFINET connection and activate the PROFINET controller in the cyclic mode.
```

---

### CR-CAND-V4-094 · A01989

- 来源记录：`SIEMENS_S210_2019_A01989`（序号 None）
- 故障描述：internal cyclic data transfer error
- 候选原因节点：The cyclic actual values and/or setpoints were not transferred within the specified times.
- 目标故障实体：`A01989` · internal cyclic data transfer error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01989:cause:3`，字符位置 `87-177`
- 证据原文：> The cyclic actual values and/or setpoints were not transferred within the specified times.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01989 PN: internal cyclic data transfer error
Reaction: NONE
Acknowledge: NONE
Cause: The cyclic actual values and/or setpoints were not transferred within the specified times.
Alarm value (r2124, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: Correctly set T_io_input or T_io_output.
```

---

### CR-CAND-V4-095 · A02007

- 来源记录：`SIEMENS_S210_2019_A02007`（序号 32）
- 故障描述：Drive not SERVO / VECTOR / DC_CTRL
- 候选原因节点：The drive object specified for connection is not a SERVO / VECTOR or DC_CTRL.
- 目标故障实体：`A02007` · Drive not SERVO / VECTOR / DC_CTRL
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A02007:cause:4`，字符位置 `102-179`
- 证据原文：> The drive object specified for connection is not a SERVO / VECTOR or DC_CTRL.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A02007 Function generator: Drive not SERVO / VECTOR / DC_CTRL
Reaction: NONE
Acknowledge: NONE
Cause: The drive object specified for connection is not a SERVO / VECTOR or DC_CTRL.
Remedy: Use a SERVO / VECTOR / DC_CTRL drive object with the corresponding number.
Note:
The alarm is reset as follows:
- remove the cause of this alarm.
- restart the function generator.
```

---

### CR-CAND-V4-096 · A05000

- 来源记录：`SIEMENS_S210_2019_A05000`（序号 None）
- 故障描述：Overtemperature heat sink AC inverter
- 候选原因节点：The alarm threshold for overtemperature at the inverter heat sink has been reached
- 目标故障实体：`A05000` · Overtemperature heat sink AC inverter
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A05000:cause:3`，字符位置 `97-179`
- 证据原文：> The alarm threshold for overtemperature at the inverter heat sink has been reached

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A05000 Power unit: Overtemperature heat sink AC inverter
Reaction: NONE
Acknowledge: NONE
Cause: The alarm threshold for overtemperature at the inverter heat sink has been reached. The response is set using p0290.
If the heat sink temperature exceeds the value set in p0292[0], then fault F30004 is output.
Remedy: Check the following:
- is the ambient temperature within the defined limit values?
- have the load conditions and the load duty cycle been appropriately dimensioned?
- has the cooling failed?
```

---

### CR-CAND-V4-097 · A05001

- 来源记录：`SIEMENS_S210_2019_A05001`（序号 None）
- 故障描述：Overtemperature depletion layer chip
- 候选原因节点：Alarm threshold for overtemperature of the power semiconductor in the AC converter has been reached.
- 目标故障实体：`A05001` · Overtemperature depletion layer chip
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A05001:cause:3`，字符位置 `96-196`
- 证据原文：> Alarm threshold for overtemperature of the power semiconductor in the AC converter has been reached.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A05001 Power unit: Overtemperature depletion layer chip
Reaction: NONE
Acknowledge: NONE
Cause: Alarm threshold for overtemperature of the power semiconductor in the AC converter has been reached.
Note:
- the response is set using p0290.
- if the temperature of the barrier layer increases by the value set in p0292[1], then fault F30025 is initiated.
Remedy: Check the following:
- is the ambient temperature within the defined limit values?
- have the load conditions and the load duty cycle been appropriately dimensioned?
- has the cooling failed?
- pulse frequency too high?
See also: r0037 (Drive temperatures)
```

---

### CR-CAND-V4-098 · A05003

- 来源记录：`SIEMENS_S210_2019_A05003`（序号 None）
- 故障描述：Internal overtemperature
- 候选原因节点：The alarm threshold for internal overtemperature has been reached.
- 目标故障实体：`A05003` · Internal overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A05003:cause:3`，字符位置 `84-150`
- 证据原文：> The alarm threshold for internal overtemperature has been reached.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A05003 Power unit: Internal overtemperature
Reaction: NONE
Acknowledge: NONE
Cause: The alarm threshold for internal overtemperature has been reached.
If the temperature inside the power unit increases by an additional 5 K, then fault F30036 is triggered.
Remedy: Check the following:
- is the ambient temperature within the defined limit values?
- has the fan failed? Check the direction of rotation.
```

---

### CR-CAND-V4-099 · A05006

- 来源记录：`SIEMENS_S210_2019_A05006`（序号 None）
- 故障描述：Overtemperature thermal model
- 候选原因节点：The temperature difference between the chip and heat sink has exceeded the permissible limit value (blocksize power units only).
- 目标故障实体：`A05006` · Overtemperature thermal model
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A05006:cause:3`，字符位置 `89-217`
- 证据原文：> The temperature difference between the chip and heat sink has exceeded the permissible limit value (blocksize power units only).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A05006 Power unit: Overtemperature thermal model
Reaction: NONE
Acknowledge: NONE
Cause: The temperature difference between the chip and heat sink has exceeded the permissible limit value (blocksize power units
only).
Depending on p0290, an appropriate overload response is initiated.
See also: r0037 (Drive temperatures)
Remedy: Not necessary.
This alarm is automatically withdrawn once the limit value has been fallen below.
Note:
If the alarm is not automatically withdrawn and the temperature continues to rise, this can result in fault F30024.
```

---

### CR-CAND-V4-100 · A07012

- 来源记录：`SIEMENS_S210_2019_A07012`（序号 None）
- 故障描述：Motor temperature model 1/3 overtemperature
- 候选原因节点：The motor temperature model 1/3 identified that the alarm threshold was exceeded.
- 目标故障实体：`A07012` · Motor temperature model 1/3 overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07012:cause:3`，字符位置 `98-179`
- 证据原文：> The motor temperature model 1/3 identified that the alarm threshold was exceeded.

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

### CR-CAND-V4-103 · A07091

- 来源记录：`SIEMENS_S210_2019_A07091`（序号 None）
- 故障描述：determined current controller dynamic response invalid
- 候选原因节点：When one button tuning is activated, the current controller is measured after the pulses have been enabled.
- 目标故障实体：`A07091` · determined current controller dynamic response invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07091:cause:11`，字符位置 `109-227`
- 证据原文：> When one button tuning is activated (p5300 = 1), the current controller is measured after the pulses have been enabled

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

### CR-CAND-V4-108 · A07092

- 来源记录：`SIEMENS_S210_2019_A07092`（序号 None）
- 故障描述：moment of inertia estimator still not ready
- 候选原因节点：The moment of inertia estimator has still not determined any valid values.
- 目标故障实体：`A07092` · moment of inertia estimator still not ready
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07092:cause:3`，字符位置 `98-172`
- 证据原文：> The moment of inertia estimator has still not determined any valid values.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07092 Drive: moment of inertia estimator still not ready
Reaction: NONE
Acknowledge: NONE
Cause: The moment of inertia estimator has still not determined any valid values.
The acceleration cannot be calculated.
The moment of inertia estimator has stabilized, if the frictional values (p1563, p1564) as well as the moment of inertia value
(p1493) have been determined and the appropriate status signal is set (r1407.26 = 1).
The following parameters influence the response of the moment of the inertia estimator:
p1560, p1561, p1562
Remedy: Traverse the axis until the moment of inertia estimator has stabilized.
This alarm is automatically withdrawn after the moment of inertia estimator has stabilized.
```

---

### CR-CAND-V4-109 · A07095

- 来源记录：`SIEMENS_S210_2019_A07095`（序号 None）
- 故障描述：One Button Tuning activated
- 候选原因节点：The One Button Tuning function is active.
- 目标故障实体：`A07095` · One Button Tuning activated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07095:cause:3`，字符位置 `82-123`
- 证据原文：> The One Button Tuning function is active.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07095 Drive: One Button Tuning activated
Reaction: NONE
Acknowledge: NONE
Cause: The One Button Tuning function is active.
One Button Tuning is performed at the next switch-on command.
See also: p5300 (One Button Tuning selection)
Remedy: Not necessary.
The alarm is automatically withdrawn after One Button Tuning has been exited (p5300 = 0).
```

---

### CR-CAND-V4-110 · A07200

- 来源记录：`SIEMENS_S210_2019_A07200`（序号 None）
- 故障描述：Master control ON command present
- 候选原因节点：The ON/OFF1 command is present (no 0 signal).
- 目标故障实体：`A07200` · Master control ON command present
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07200:cause:3`，字符位置 `88-133`
- 证据原文：> The ON/OFF1 command is present (no 0 signal).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07200 Drive: Master control ON command present
Reaction: NONE
Acknowledge: NONE
Cause: The ON/OFF1 command is present (no 0 signal).
The command is either influenced via binector input p0840 (current CDS) or control word bit 0 via the master control.
Remedy: Switch the signal via binector input p0840 (current CDS) or control word bit 0 via the master control to 0.
```

---

### CR-CAND-V4-111 · A07565

- 来源记录：`SIEMENS_S210_2019_A07565`（序号 None）
- 故障描述：Encoder error in PROFIdrive encoder interface 1
- 候选原因节点：An encoder error was signaled for encoder 1 via the PROFIdrive encoder interface (G1_ZSW.15).
- 目标故障实体：`A07565` · Encoder error in PROFIdrive encoder interface 1
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07565:cause:3`，字符位置 `102-195`
- 证据原文：> An encoder error was signaled for encoder 1 via the PROFIdrive encoder interface (G1_ZSW.15).

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07565 Drive: Encoder error in PROFIdrive encoder interface 1
Reaction: NONE
Acknowledge: NONE
Cause: An encoder error was signaled for encoder 1 via the PROFIdrive encoder interface (G1_ZSW.15).
Alarm value (r2124, interpret decimal):
Error code from G1_XIST2.
Remedy: Acknowledge the encoder error using the encoder control word (G1_STW.15 = 1).
```

---

### CR-CAND-V4-112 · A07805

- 来源记录：`SIEMENS_S210_2019_A07805`（序号 None）
- 故障描述：Power unit overload I2t
- 候选原因节点：The alarm threshold for I2t overload (p0294) of the power unit has been exceeded.
- 目标故障实体：`A07805` · Power unit overload I2t
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07805:cause:3`，字符位置 `78-159`
- 证据原文：> The alarm threshold for I2t overload (p0294) of the power unit has been exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A07805 Drive: Power unit overload I2t
Reaction: NONE
Acknowledge: NONE
Cause: The alarm threshold for I2t overload (p0294) of the power unit has been exceeded.
The response parameterized in p0290 becomes active.
Remedy: - reduce the continuous load.
- adapt the load duty cycle.
- check the assignment of the rated currents of the motor and Motor Module.
```

---

### CR-CAND-V4-113 · A08511

- 来源记录：`SIEMENS_S210_2019_A08511`（序号 None）
- 故障描述：Receive configuration data invalid
- 候选原因节点：The drive unit did not accept the receive configuration data.
- 目标故障实体：`A08511` · Receive configuration data invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A08511:cause:3`，字符位置 `97-158`
- 证据原文：> The drive unit did not accept the receive configuration data.

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

### CR-CAND-V4-124 · A08800

- 来源记录：`SIEMENS_S210_2019_A08800`（序号 None）
- 故障描述：PROFIenergy energy-saving mode active
- 候选原因节点：The PROFIenergy energy-saving mode is active
- 目标故障实体：`A08800` · PROFIenergy energy-saving mode active
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A08800:cause:2`，字符位置 `85-129`
- 证据原文：> The PROFIenergy energy-saving mode is active

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A08800 PROFIenergy energy-saving mode active
Reaction: NONE
Acknowledge: NONE
Cause: The PROFIenergy energy-saving mode is active
Alarm value (r2124, interpret decimal):
Mode ID of the active PROFIenergy energy-saving mode.
See also: r5600 (Pe energy-saving mode ID)
Remedy: The alarm is automatically withdrawn when the energy-saving mode is exited.
Note:
The energy-saving mode is exited after the following events:
- the PROFIenergy command end_pause is received from the higher-level control.
- the higher-level control has changed into the STOP operating state.
- the PROFINET connection to the higher-level control has been disconnected.
```

---

### CR-CAND-V4-125 · A09000

- 来源记录：`SIEMENS_S210_2019_A09000`（序号 33）
- 故障描述：Web server user incorrectly configured
- 候选原因节点：An error occurred when configuring the web server user.
- 目标故障实体：`A09000` · Web server user incorrectly configured
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A09000:cause:8`，字符位置 `86-141`
- 证据原文：> An error occurred when configuring the web server user.

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

### CR-CAND-V4-129 · A13001

- 来源记录：`SIEMENS_S210_2019_A13001`（序号 None）
- 故障描述：Error in license checksum
- 候选原因节点：When checking the checksum of the license key, an error was detected.
- 目标故障实体：`A13001` · Error in license checksum
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13001:cause:2`，字符位置 `73-142`
- 证据原文：> When checking the checksum of the license key, an error was detected.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13001 Error in license checksum
Reaction: NONE
Acknowledge: NONE
Cause: When checking the checksum of the license key, an error was detected.
Remedy: Compare the license key (p9920) entered with the license key on the certificate of license.
Re-enter the license key and activate (p9920, p9921).
```

---

### CR-CAND-V4-130 · A13030

- 来源记录：`SIEMENS_S210_2019_A13030`（序号 None）
- 故障描述：Trial License activated
- 候选原因节点：The 'Trial License' function was activated. One of the available periods is expiring.
- 目标故障实体：`A13030` · Trial License activated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13030:cause:2`，字符位置 `71-155`
- 证据原文：> The "Trial License" function was activated. One of the available periods is expiring

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13030 Trial License activated
Reaction: NONE
Acknowledge: NONE
Cause: The "Trial License" function was activated. One of the available periods is expiring.
Remedy: Not necessary.
The alarm is automatically withdrawn after the periods have expired.
```

---

### CR-CAND-V4-131 · A13031

- 来源记录：`SIEMENS_S210_2019_A13031`（序号 None）
- 故障描述：Trial License period expired
- 候选原因节点：One of the available periods of the 'Trial License' function has expired.
- 目标故障实体：`A13031` · Trial License period expired
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13031:cause:3`，字符位置 `76-148`
- 证据原文：> One of the available periods of the "Trial License" function has expired

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13031 Trial License period expired
Reaction: NONE
Acknowledge: NONE
Cause: One of the available periods of the "Trial License" function has expired.
Remedy: - if required, start an additional period (p9918 = 1).
- deactivate functions requiring a license.
- appropriately license the drive unit.
Note:
A license that is not adequate will only become evident after the next time the system runs up.
```

---

### CR-CAND-V4-132 · A13032

- 来源记录：`SIEMENS_S210_2019_A13032`（序号 None）
- 故障描述：Trial License last period activated
- 候选原因节点：The 'Trial License' function was activated. The last of the available periods is expiring.
- 目标故障实体：`A13032` · Trial License last period activated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13032:cause:2`，字符位置 `83-172`
- 证据原文：> The "Trial License" function was activated. The last of the available periods is expiring

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13032 Trial License last period activated
Reaction: NONE
Acknowledge: NONE
Cause: The "Trial License" function was activated. The last of the available periods is expiring.
Remedy: Not necessary.
The alarm is automatically withdrawn after the last period has expired.
```

---

### CR-CAND-V4-133 · A13033

- 来源记录：`SIEMENS_S210_2019_A13033`（序号 None）
- 故障描述：Trial License last period expired
- 候选原因节点：The last period of the 'Trial License' function has expired. No additional periods available.
- 目标故障实体：`A13033` · Trial License last period expired
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A13033:cause:2`，字符位置 `81-173`
- 证据原文：> The last period of the "Trial License" function has expired. No additional periods available

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A13033 Trial License last period expired
Reaction: NONE
Acknowledge: NONE
Cause: The last period of the "Trial License" function has expired. No additional periods available.
Remedy: - deactivate functions requiring a license.
- appropriately license the drive unit.
Note:
A license that is not adequate will only become evident after the next time the system runs up.
```

---

### CR-CAND-V4-134 · A30016

- 来源记录：`SIEMENS_S210_2019_A30016`（序号 None）
- 故障描述：Load supply switched off
- 候选原因节点：The DC link voltage is too low.
- 目标故障实体：`A30016` · Load supply switched off
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30016:cause:3`，字符位置 `84-115`
- 证据原文：> The DC link voltage is too low.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30016 Power unit: Load supply switched off
Reaction: NONE
Acknowledge: NONE
Cause: The DC link voltage is too low.
Alarm value (r2124, interpret decimal):
DC link voltage at the time of the trip [V].
Remedy: - switch on load supply.
- check the line supply if necessary.
```

---

### CR-CAND-V4-135 · A30031

- 来源记录：`SIEMENS_S210_2019_A30031`（序号 None）
- 故障描述：Hardware current limiting in phase U
- 候选原因节点：closed-loop control is incorrectly parameterized.
- 目标故障实体：`A30031` · Hardware current limiting in phase U
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30031:cause:3`，字符位置 `205-254`
- 证据原文：> closed-loop control is incorrectly parameterized.

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

### CR-CAND-V4-140 · A30034

- 来源记录：`SIEMENS_S210_2019_A30034`（序号 None）
- 故障描述：Internal overtemperature
- 候选原因节点：The alarm threshold for internal overtemperature has been reached.
- 目标故障实体：`A30034` · Internal overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30034:cause:3`，字符位置 `137-203`
- 证据原文：> The alarm threshold for internal overtemperature has been reached.

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

### CR-CAND-V4-148 · A30041

- 来源记录：`SIEMENS_S210_2019_A30041`（序号 None）
- 故障描述：Undervolt 24/48 V alarm
- 候选原因节点：For the power unit power supply, the lower threshold has been violated.
- 目标故障实体：`A30041` · Undervolt 24/48 V alarm
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30041:cause:3`，字符位置 `83-154`
- 证据原文：> For the power unit power supply, the lower threshold has been violated.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30041 Power unit: Undervolt 24/48 V alarm
Reaction: NONE
Acknowledge: NONE
Cause: For the power unit power supply, the lower threshold has been violated.
Alarm value (r2124, interpret hexadecimal):
yyxxxx hex: yy = channel, xxxx = voltage [0.1 V]
yy = 0: 24 V power supply
yy = 1: 48 V power supply
Remedy: - check the power supply of the power unit.
- carry out a POWER ON (switch-off/switch-on) for the component.
```

---

### CR-CAND-V4-149 · A30042

- 来源记录：`SIEMENS_S210_2019_A30042`（序号 None）
- 故障描述：Fan has reached the maximum operating hours
- 候选原因节点：The maximum operating time of at least one fan will soon be reached, or has already been exceeded.
- 目标故障实体：`A30042` · Fan has reached the maximum operating hours
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30042:cause:3`，字符位置 `103-201`
- 证据原文：> The maximum operating time of at least one fan will soon be reached, or has already been exceeded.

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

### CR-CAND-V4-155 · A30054

- 来源记录：`SIEMENS_S210_2019_A30054`（序号 None）
- 故障描述：Undervoltage when opening the brake
- 候选原因节点：When the brake is being opened, it is detected that the power supply voltage is less than 21.4 V
- 目标故障实体：`A30054` · Undervoltage when opening the brake
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30054:cause:3`，字符位置 `95-191`
- 证据原文：> When the brake is being opened, it is detected that the power supply voltage is less than 21.4 V

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30054 Power unit: Undervoltage when opening the brake
Reaction: NONE
Acknowledge: NONE
Cause: When the brake is being opened, it is detected that the power supply voltage is less than 21.4 V
Alarm value (r2124, interpret decimal):
Supply voltage fault [0.1 V].
Example:
Alarm value = 195 --> voltage = 19.5 V
Remedy: Check the 24 V voltage for stability and value.
```

---
