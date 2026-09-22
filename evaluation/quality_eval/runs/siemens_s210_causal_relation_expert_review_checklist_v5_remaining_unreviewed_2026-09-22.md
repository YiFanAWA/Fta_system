# Siemens S210 因果关系候选专家审核清单 v5

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。本批从 v1-v4 已审核候选之外的原因中生成，并保留现有 Gold 的原文证据；`causes` 字段本身不等于已证明的因果关系。

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

### CR-CAND-V5-001 · A01016

- 来源记录：`SIEMENS_S210_2019_A01016`（序号 None）
- 故障描述：Firmware changed
- 候选原因节点：File missing.
- 目标故障实体：`A01016` · Firmware changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01016:cause:4`，字符位置 `325-338`
- 证据原文：> File missing.

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

### CR-CAND-V5-005 · A01035

- 来源记录：`SIEMENS_S210_2019_A01035`（序号 None）
- 故障描述：Parameter back-up file corrupted
- 候选原因节点：It is possible that the backup was interrupted by switching off or withdrawing the memory card.
- 目标故障实体：`A01035` · Parameter back-up file corrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01035:cause:5`，字符位置 `269-364`
- 证据原文：> It is possible that the backup was interrupted by switching off or withdrawing the memory card.

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

### CR-CAND-V5-006 · A01654

- 来源记录：`SIEMENS_S210_2019_A01654`（序号 None）
- 故障描述：Deviating PROFIsafe configuration
- 候选原因节点：PROFIsafe is parameterized in the drive; however, a PROFIsafe telegram has not been configured in the higher-level control.
- 目标故障实体：`A01654` · Deviating PROFIsafe configuration
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01654:cause:5`，字符位置 `445-568`
- 证据原文：> PROFIsafe is parameterized in the drive; however, a PROFIsafe telegram has not been configured in the higher-level control.

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

### CR-CAND-V5-007 · A01691

- 来源记录：`SIEMENS_S210_2019_A01691`（序号 None）
- 故障描述：Ti and To unsuitable for PN cycle
- 候选原因节点：No isochronous PROFINET: The PN clock cycle must be at least 4x the current controller clock cycle.
- 目标故障实体：`A01691` · Ti and To unsuitable for PN cycle
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01691:cause:5`，字符位置 `447-546`
- 证据原文：> No isochronous PROFINET: The PN clock cycle must be at least 4x the current controller clock cycle.

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

### CR-CAND-V5-008 · A01711

- 来源记录：`SIEMENS_S210_2019_A01711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：The limit values are based on the actual value (r9713[0/1]). If the safe actual values on the two monitoring channels do not match, the limit values, which have been set at a defined interval, will also be different (i.e. corresponding to message value 3).
- 目标故障实体：`A01711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01711:cause:136`，字符位置 `2240-2494`
- 证据原文：> The limit values are based on the actual value (r9713[0/1]). If the safe actual values on the two monitoring channels do not match, the limit values, which have been set at a defined interval, will also be different (i.e. corresponding to message value 3

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

### CR-CAND-V5-015 · A01714

- 来源记录：`SIEMENS_S210_2019_A01714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：SLS2 exceeded.
- 目标故障实体：`A01714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01714:cause:5`，字符位置 `304-318`
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

### CR-CAND-V5-019 · A01716

- 来源记录：`SIEMENS_S210_2019_A01716`（序号 None）
- 故障描述：Tolerance for safe motion direction exceeded
- 候选原因节点：Tolerance for function 'safe motion direction negative' exceeded.
- 目标故障实体：`A01716` · Tolerance for safe motion direction exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01716:cause:9`，字符位置 `351-415`
- 证据原文：> Tolerance for function "safe motion direction negative" exceeded

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

### CR-CAND-V5-020 · A01781

- 来源记录：`SIEMENS_S210_2019_A01781`（序号 None）
- 故障描述：SBT brake opening time exceeded
- 候选原因节点：Internal brake was not able to be opened.
- 目标故障实体：`A01781` · SBT brake opening time exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01781:cause:5`，字符位置 `336-377`
- 证据原文：> Internal brake was not able to be opened.

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

### CR-CAND-V5-021 · A01782

- 来源记录：`SIEMENS_S210_2019_A01782`（序号 None）
- 故障描述：SBT brake test incorrect control
- 候选原因节点：The brake is not configured in p10202. There is a brake test configuration error.
- 目标故障实体：`A01782` · SBT brake test incorrect control
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01782:cause:4`，字符位置 `307-378`
- 证据原文：> The safe brake test was canceled by resetting the brake test selection.

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

### CR-CAND-V5-022 · A01784

- 来源记录：`SIEMENS_S210_2019_A01784`（序号 None）
- 故障描述：SBT brake test canceled with fault
- 候选原因节点：internal software error
- 目标故障实体：`A01784` · SBT brake test canceled with fault
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01784:cause:4`，字符位置 `388-411`
- 证据原文：> internal software error

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

### CR-CAND-V5-037 · A01785

- 来源记录：`SIEMENS_S210_2019_A01785`（序号 None）
- 故障描述：SBT brake test configuration error
- 候选原因节点：No brake was configured
- 目标故障实体：`A01785` · SBT brake test configuration error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01785:cause:4`，字符位置 `365-388`
- 证据原文：> No brake was configured

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

### CR-CAND-V5-040 · A01788

- 来源记录：`SIEMENS_S210_2019_A01788`（序号 31）
- 故障描述：Automatic test stop waits for STO deselection via motion monitoring functions
- 候选原因节点：a safety message is present, that resulted in a STO.
- 目标故障实体：`A01788` · Automatic test stop waits for STO deselection via motion monitoring functions
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01788:cause:8`，字符位置 `319-371`
- 证据原文：> a safety message is present, that resulted in a STO.

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

### CR-CAND-V5-041 · A01900

- 来源记录：`SIEMENS_S210_2019_A01900`（序号 None）
- 故障描述：Configuration telegram error
- 候选原因节点：Too many PZD data words for output or input to a drive object. The number of possible PZD items in a drive object is determined by the number of indices in r2050/p2051.
- 目标故障实体：`A01900` · Configuration telegram error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01900:cause:5`，字符位置 `376-544`
- 证据原文：> Too many PZD data words for output or input to a drive object. The number of possible PZD items in a drive object is determined by the number of indices in r2050/p2051.

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

### CR-CAND-V5-054 · A01902

- 来源记录：`SIEMENS_S210_2019_A01902`（序号 None）
- 故障描述：clock cycle synchronous operation parameterization not permissible
- 候选原因节点：Bus cycle time Tdp > 32 ms.
- 目标故障实体：`A01902` · clock cycle synchronous operation parameterization not permissible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01902:cause:5`，字符位置 `256-283`
- 证据原文：> Bus cycle time Tdp > 32 ms.

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

### CR-CAND-V5-067 · A01940

- 来源记录：`SIEMENS_S210_2019_A01940`（序号 None）
- 故障描述：Clock cycle synchronism not reached
- 候选原因节点：At least one drive object has a pulse enable (also not controlled from PROFINET).
- 目标故障实体：`A01940` · Clock cycle synchronism not reached
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01940:cause:5`，字符位置 `574-655`
- 证据原文：> at least one drive object has a pulse enable (also not controlled from PROFINET).

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

### CR-CAND-V5-068 · A01943

- 来源记录：`SIEMENS_S210_2019_A01943`（序号 None）
- 故障描述：Clock cycle signal error when the bus is being established
- 候选原因节点：the master is sending an irregular global control telegram.
- 目标故障实体：`A01943` · Clock cycle signal error when the bus is being established
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01943:cause:5`，字符位置 `314-373`
- 证据原文：> the master is sending an irregular global control telegram.

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

### CR-CAND-V5-070 · A01944

- 来源记录：`SIEMENS_S210_2019_A01944`（序号 None）
- 故障描述：Sign-of-life synchronism not reached
- 候选原因节点：The sign-of-life is changing differently to how it was configured in the Tmapc time grid.
- 目标故障实体：`A01944` · Sign-of-life synchronism not reached
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01944:cause:4`，字符位置 `309-398`
- 证据原文：> the sign-of-life is changing differently to how it was configured in the Tmapc time grid.

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

### CR-CAND-V5-071 · A07012

- 来源记录：`SIEMENS_S210_2019_A07012`（序号 None）
- 故障描述：Motor temperature model 1/3 overtemperature
- 候选原因节点：Motor temperature model 1 (I2t): temperature too high.
- 目标故障实体：`A07012` · Motor temperature model 1/3 overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07012:cause:4`，字符位置 `239-293`
- 证据原文：> Motor temperature model 1 (I2t): temperature too high.

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

### CR-CAND-V5-073 · A07091

- 来源记录：`SIEMENS_S210_2019_A07091`（序号 None）
- 故障描述：determined current controller dynamic response invalid
- 候选原因节点：incorrectly set current controller
- 目标故障实体：`A07091` · determined current controller dynamic response invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A07091:cause:3`，字符位置 `330-364`
- 证据原文：> incorrectly set current controller

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

### CR-CAND-V5-077 · A08511

- 来源记录：`SIEMENS_S210_2019_A08511`（序号 None）
- 故障描述：Receive configuration data invalid
- 候选原因节点：Connection established to more drive objects than configured in the device.
- 目标故障实体：`A08511` · Receive configuration data invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A08511:cause:4`，字符位置 `256-331`
- 证据原文：> Connection established to more drive objects than configured in the device.

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

### CR-CAND-V5-087 · A09000

- 来源记录：`SIEMENS_S210_2019_A09000`（序号 33）
- 故障描述：Web server user incorrectly configured
- 候选原因节点：No admin password
- 目标故障实体：`A09000` · Web server user incorrectly configured
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A09000:cause:9`，字符位置 `185-202`
- 证据原文：> No admin password

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

### CR-CAND-V5-090 · A30031

- 来源记录：`SIEMENS_S210_2019_A30031`（序号 None）
- 故障描述：Hardware current limiting in phase U
- 候选原因节点：fault in the motor or in the power cables.
- 目标故障实体：`A30031` · Hardware current limiting in phase U
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30031:cause:4`，字符位置 `257-299`
- 证据原文：> fault in the motor or in the power cables.

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

### CR-CAND-V5-094 · A30034

- 来源记录：`SIEMENS_S210_2019_A30034`（序号 None）
- 故障描述：Internal overtemperature
- 候选原因节点：ambient temperature might be too high.
- 目标故障实体：`A30034` · Internal overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30034:cause:4`，字符位置 `316-354`
- 证据原文：> ambient temperature might be too high.

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

### CR-CAND-V5-101 · A30042

- 来源记录：`SIEMENS_S210_2019_A30042`（序号 None）
- 故障描述：Fan has reached the maximum operating hours
- 候选原因节点：The operating hours counter of the heat sink fan will reach the maximum operating time in 500 hours.
- 目标故障实体：`A30042` · Fan has reached the maximum operating hours
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30042:cause:4`，字符位置 `252-352`
- 证据原文：> The operating hours counter of the heat sink fan will reach the maximum operating time in 500 hours.

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

### CR-CAND-V5-106 · A30076

- 来源记录：`SIEMENS_S210_2019_A30076`（序号 None）
- 故障描述：thermal overload internal braking resistor alarm
- 候选原因节点：The energy absorbed by the internal braking resistor has exceeded the alarm threshold of 80 %.
- 目标故障实体：`A30076` · thermal overload internal braking resistor alarm
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30076:cause:3`，字符位置 `108-202`
- 证据原文：> The energy absorbed by the internal braking resistor has exceeded the alarm threshold of 80 %.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30076 Power unit: thermal overload internal braking resistor alarm
Reaction: NONE
Acknowledge: NONE
Cause: The energy absorbed by the internal braking resistor has exceeded the alarm threshold of 80 %. If the power unit is still
operated in the generator mode, then this can reach the shutdown threshold. To avoid overheating of the braking resistor,
use of the braking resistor is inhibited and alarm A30077 is output.
Alarm value (r2124, interpret decimal):
Energy absorbed by the braking resistor [Ws].
Remedy: Reduce the power when generating.
Note:
For a DC link coupling, the generating power of all of the coupled power units must be taken into consideration.
```

---

### CR-CAND-V5-107 · A30077

- 来源记录：`SIEMENS_S210_2019_A30077`（序号 34）
- 故障描述：thermal overload internal braking resistor
- 候选原因节点：The internal braking resistor is thermally overloaded
- 目标故障实体：`A30077` · thermal overload internal braking resistor
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30077:cause:5`，字符位置 `102-155`
- 证据原文：> The internal braking resistor is thermally overloaded

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30077 Power unit: thermal overload internal braking resistor
Reaction: NONE
Acknowledge: NONE
Cause: The internal braking resistor is thermally overloaded. This is the reason that its use was inhibited.
Alarm value (r2124, interpret decimal):
Energy absorbed by the braking resistor [Ws].
504 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: Reduce the power when generating.
Note:
- once the internal braking resistor has thermally recovered, it is enabled for further use.
- for a DC link coupling, the generating power of all the coupled power units must be taken into consideration.
```

---

### CR-CAND-V5-108 · A30502

- 来源记录：`SIEMENS_S210_2019_A30502`（序号 None）
- 故障描述：DC link overvoltage
- 候选原因节点：device supply voltage too high
- 目标故障实体：`A30502` · DC link overvoltage
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30502:cause:3`，字符位置 `156-186`
- 证据原文：> device supply voltage too high

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

### CR-CAND-V5-110 · A30693

- 来源记录：`SIEMENS_S210_2019_A30693`（序号 None）
- 故障描述：Safety parameter settings changed, warm restart/POWER ON required
- 候选原因节点：Safety parameters have been changed
- 目标故障实体：`A30693` · Safety parameter settings changed, warm restart/POWER ON required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30693:cause:3`，字符位置 `120-155`
- 证据原文：> Safety parameters have been changed

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30693 SI P2: Safety parameter settings changed, warm restart/POWER ON required
Reaction: NONE
Acknowledge: NONE
Cause: Safety parameters have been changed; these will only take effect following a warm restart or POWER ON.
Alarm value (r2124, interpret decimal):
Only for internal Siemens diagnostics.
Remedy: - carry out a warm restart.
- carry out a POWER ON (switch-off/switch-on).
Note:
A POWER ON is required before carrying out the acceptance test.
```

---

### CR-CAND-V5-111 · A30706

- 来源记录：`SIEMENS_S210_2019_A30706`（序号 None）
- 故障描述：SAM/SBR limit exceeded
- 候选原因节点：Motion monitoring functions with encoder (SAM): after initiating SS1 or SS2, the speed exceeded the set tolerance.
- 目标故障实体：`A30706` · SAM/SBR limit exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30706:cause:5`，字符位置 `84-210`
- 证据原文：> Motion monitoring functions with encoder (SAM, p9506 = 0): - after initiating SS1 or SS2, the speed exceeded the set tolerance

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

### CR-CAND-V5-113 · A30707

- 来源记录：`SIEMENS_S210_2019_A30707`（序号 None）
- 故障描述：Tolerance for safe operating stop exceeded
- 候选原因节点：The actual position has moved further away from the target position than the standstill tolerance.
- 目标故障实体：`A30707` · Tolerance for safe operating stop exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30707:cause:3`，字符位置 `104-202`
- 证据原文：> The actual position has moved further away from the target position than the standstill tolerance.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30707 SI Motion P2: Tolerance for safe operating stop exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The actual position has moved further away from the target position than the standstill tolerance.
The drive is stopped by message F30701.
Remedy: - check whether safety faults are present and if required carry out the appropriate diagnostic routines for the particular faults.
- check whether the standstill tolerance matches the accuracy and control dynamic performance of the axis.
- carry out a POWER ON (switch-off/switch-on).
Note:
SI: Safety Integrated
SOS: Safe Operating Stop
See also: p9530 (SI Motion standstill tolerance)
```

---

### CR-CAND-V5-114 · A30709

- 来源记录：`SIEMENS_S210_2019_A30709`（序号 None）
- 故障描述：SS2E initiated
- 候选原因节点：The drive is stopped using SS2E (braking along a path). 'Safe Operating Stop' (SOS) is activated after the parameterized time has expired.
- 目标故障实体：`A30709` · SS2E initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30709:cause:5`，字符位置 `76-213`
- 证据原文：> The drive is stopped using SS2E (braking along a path). "Safe Operating Stop" (SOS) is activated after the parameterized time has expired

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30709 SI Motion P2: SS2E initiated
Reaction: NONE
Acknowledge: NONE
Cause: The drive is stopped using SS2E (braking along a path).
"Safe Operating Stop" (SOS) is activated after the parameterized time has expired.
Possible causes:
Subsequent response, following messages: A30714, A30716
See also: p9553 (SI Motion transition time SS2E to SOS)
Remedy: - remove the cause of the fault at the control.
- carry out diagnostics for the active messages (A30714, A30716).
Note:
SI: Safety Integrated
SOS: Safe Operating Stop
SS2E: Safe Stop 2 External (Safe Stop 2 with external stop)
```

---

### CR-CAND-V5-115 · A30711

- 来源记录：`SIEMENS_S210_2019_A30711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：difference between the input data or results of the monitoring functions
- 目标故障实体：`A30711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30711:cause:3`，字符位置 `172-244`
- 证据原文：> difference between the input data or results of the monitoring functions

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

### CR-CAND-V5-127 · A30716

- 来源记录：`SIEMENS_S210_2019_A30716`（序号 None）
- 故障描述：Tolerance for safe motion direction exceeded
- 候选原因节点：The tolerance for the 'safe motion direction' function was exceeded
- 目标故障实体：`A30716` · Tolerance for safe motion direction exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30716:cause:4`，字符位置 `106-173`
- 证据原文：> The tolerance for the "safe motion direction" function was exceeded

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

### CR-CAND-V5-130 · A30730

- 来源记录：`SIEMENS_S210_2019_A30730`（序号 None）
- 故障描述：Reference block for dynamic Safely-Limited Speed invalid
- 候选原因节点：The reference block transferred via PROFIsafe is negative.
- 目标故障实体：`A30730` · Reference block for dynamic Safely-Limited Speed invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30730:cause:3`，字符位置 `118-176`
- 证据原文：> The reference block transferred via PROFIsafe is negative.

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

### CR-CAND-V5-132 · A30788

- 来源记录：`SIEMENS_S210_2019_A30788`（序号 None）
- 故障描述：wait for STO deselection via SMM
- 候选原因节点：The automatic test stop was not able to be carried out after powering up.
- 目标故障实体：`A30788` · wait for STO deselection via SMM
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30788:cause:2`，字符位置 `101-174`
- 证据原文：> The automatic test stop was not able to be carried out after powering up.

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

### CR-CAND-V5-135 · A30798

- 来源记录：`SIEMENS_S210_2019_A30798`（序号 None）
- 故障描述：Test stop for motion monitoring functions running
- 候选原因节点：The forced checking procedure (test stop) for the safe motion monitoring functions is currently in progress.
- 目标故障实体：`A30798` · Test stop for motion monitoring functions running
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30798:cause:3`，字符位置 `111-219`
- 证据原文：> The forced checking procedure (test stop) for the safe motion monitoring functions is currently in progress.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A30798 SI Motion P2: Test stop for motion monitoring functions running
Reaction: NONE
Acknowledge: NONE
Cause: The forced checking procedure (test stop) for the safe motion monitoring functions is currently in progress.
Remedy: Not necessary.
The message is automatically withdrawn when the test stop has been completed.
Note:
SI: Safety Integrated
```

---

### CR-CAND-V5-136 · A30799

- 来源记录：`SIEMENS_S210_2019_A30799`（序号 None）
- 故障描述：Acceptance test mode active
- 候选原因节点：The acceptance test mode is active
- 目标故障实体：`A30799` · Acceptance test mode active
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30799:cause:3`，字符位置 `89-123`
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
A30799 SI Motion P2: Acceptance test mode active
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

### CR-CAND-V5-137 · A30999

- 来源记录：`SIEMENS_S210_2019_A30999`（序号 None）
- 故障描述：Unknown alarm
- 候选原因节点：An alarm occurred on the power unit that cannot be interpreted by the Control Unit firmware
- 目标故障实体：`A30999` · Unknown alarm
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A30999:cause:3`，字符位置 `73-164`
- 证据原文：> An alarm occurred on the power unit that cannot be interpreted by the Control Unit firmware

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

### CR-CAND-V5-139 · A31700

- 来源记录：`SIEMENS_S210_2019_A31700`（序号 None）
- 故障描述：Functional safety monitoring initiated
- 候选原因节点：Functional safety was activated
- 目标故障实体：`A31700` · Functional safety monitoring initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A31700:cause:3`，字符位置 `97-128`
- 证据原文：> Functional safety was activated

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

### CR-CAND-V5-142 · A40100

- 来源记录：`SIEMENS_S210_2019_A40100`（序号 35）
- 故障描述：Alarm at DRIVE-CLiQ socket X100
- 候选原因节点：An alarm has occurred at the drive object at the DRIVE-CLiQ socket X100.
- 目标故障实体：`A40100` · Alarm at DRIVE-CLiQ socket X100
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A40100:cause:5`，字符位置 `79-151`
- 证据原文：> An alarm has occurred at the drive object at the DRIVE-CLiQ socket X100.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A40100 Alarm at DRIVE-CLiQ socket X100
Reaction: NONE
Acknowledge: NONE
Cause: An alarm has occurred at the drive object at the DRIVE-CLiQ socket X100.
Alarm value (r2124, interpret decimal):
First alarm that has occurred for this drive object.
Remedy: Evaluate the alarm buffer of the specified object.
```

---

### CR-CAND-V5-143 · F01001

- 来源记录：`SIEMENS_S210_2019_F01001`（序号 None）
- 故障描述：FloatingPoint exception
- 候选原因节点：An exception occurred during an operation with the FloatingPoint data type.
- 目标故障实体：`F01001` · FloatingPoint exception
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01001:cause:2`，字符位置 `75-150`
- 证据原文：> An exception occurred during an operation with the FloatingPoint data type.

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

### CR-CAND-V5-150 · F01002

- 来源记录：`SIEMENS_S210_2019_F01002`（序号 None）
- 故障描述：Internal software error
- 候选原因节点：An internal software error has occurred.
- 目标故障实体：`F01002` · Internal software error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01002:cause:3`，字符位置 `78-118`
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
F01002 Internal software error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: An internal software error has occurred.
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade firmware to later version.
- contact Technical Support.
```

---

### CR-CAND-V5-151 · F01003

- 来源记录：`SIEMENS_S210_2019_F01003`（序号 None）
- 故障描述：Acknowledgment delay when accessing the memory
- 候选原因节点：A memory area was accessed that does not return a 'READY'.
- 目标故障实体：`F01003` · Acknowledgment delay when accessing the memory
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01003:cause:3`，字符位置 `101-157`
- 证据原文：> A memory area was accessed that does not return a "READY

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01003 Acknowledgment delay when accessing the memory
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: A memory area was accessed that does not return a "READY".
Fault value (r0949, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- contact Technical Support.
```

---

### CR-CAND-V5-152 · F01005

- 来源记录：`SIEMENS_S210_2019_F01005`（序号 None）
- 故障描述：Firmware download for DRIVE-CLiQ component unsuccessful
- 候选原因节点：It was not possible to download the firmware to a DRIVE-CLiQ component.
- 目标故障实体：`F01005` · Firmware download for DRIVE-CLiQ component unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01005:cause:3`，字符位置 `163-234`
- 证据原文：> It was not possible to download the firmware to a DRIVE-CLiQ component.

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

### CR-CAND-V5-165 · F01011

- 来源记录：`SIEMENS_S210_2019_F01011`（序号 None）
- 故障描述：Download interrupted
- 候选原因节点：The project download was interrupted.
- 目标故障实体：`F01011` · Download interrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01011:cause:2`，字符位置 `75-112`
- 证据原文：> The project download was interrupted.

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

### CR-CAND-V5-170 · F01012

- 来源记录：`SIEMENS_S210_2019_F01012`（序号 None）
- 故障描述：Project conversion error
- 候选原因节点：When converting the project of an older firmware version, an error occurred.
- 目标故障实体：`F01012` · Project conversion error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01012:cause:2`，字符位置 `79-155`
- 证据原文：> When converting the project of an older firmware version, an error occurred.

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

### CR-CAND-V5-172 · F01015

- 来源记录：`SIEMENS_S210_2019_F01015`（序号 None）
- 故障描述：Internal software error
- 候选原因节点：An internal software error has occurred.
- 目标故障实体：`F01015` · Internal software error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01015:cause:3`，字符位置 `75-115`
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
F01015 Internal software error
Reaction: OFF2
Acknowledge: POWER ON
Cause: An internal software error has occurred.
Fault value (r0949, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade firmware to later version.
- contact Technical Support.
```

---

### CR-CAND-V5-173 · F01018

- 来源记录：`SIEMENS_S210_2019_F01018`（序号 None）
- 故障描述：Booting has been interrupted several times
- 候选原因节点：power supply interrupted
- 目标故障实体：`F01018` · Booting has been interrupted several times
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01018:cause:3`，字符位置 `251-275`
- 证据原文：> power supply interrupted

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

### CR-CAND-V5-176 · F01023

- 来源记录：`SIEMENS_S210_2019_F01023`（序号 37）
- 故障描述：Software timeout (internal)
- 候选原因节点：An internal software timeout has occurred.
- 目标故障实体：`F01023` · Software timeout (internal)
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01023:cause:6`，字符位置 `82-124`
- 证据原文：> An internal software timeout has occurred.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01023 Software timeout (internal)
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: An internal software timeout has occurred.
Fault value (r0949, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade firmware to later version.
- contact Technical Support.
```

---

### CR-CAND-V5-177 · F01031

- 来源记录：`SIEMENS_S210_2019_F01031`（序号 None）
- 故障描述：Sign-of-life failure for OFF in REMOTE
- 候选原因节点：With the 'OFF in REMOTE' mode active, no sign-of-life was received within 3 seconds.
- 目标故障实体：`F01031` · Sign-of-life failure for OFF in REMOTE
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_F01031:cause:2`，字符位置 `93-176`
- 证据原文：> With the "OFF in REMOTE" mode active, no sign-of-life was received within 3 seconds

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
F01031 Sign-of-life failure for OFF in REMOTE
Reaction: OFF3
Acknowledge: IMMEDIATELY
Cause: With the "OFF in REMOTE" mode active, no sign-of-life was received within 3 seconds.
Remedy: - check the data cable connection at the serial interface for the Control Unit (CU) and operator panel.
- check the data cable between the Control Unit and operator panel.
426 Operating Instructions, 01/2019, A5E41702836B AC
```

---
