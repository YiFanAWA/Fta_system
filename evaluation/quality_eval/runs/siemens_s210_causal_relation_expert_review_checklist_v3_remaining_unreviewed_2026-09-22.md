# Siemens S210 因果关系候选专家审核清单 v3

> 本清单是因果关系候选审核包，不是专家金标，也不是可直接建树的数据。本批从 v1/v2 已审核候选之外的原因中生成，并保留现有 Gold 的原文证据；`causes` 字段本身不等于已证明的因果关系。

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

### CR-CAND-V3-001 · A01007

- 来源记录：`SIEMENS_S210_2019_A01007`（序号 None）
- 故障描述：POWER ON for DRIVE-CLiQ component required
- 候选原因节点：firmware update
- 目标故障实体：`A01007` · POWER ON for DRIVE-CLiQ component required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01007:cause:3`，字符位置 `165-180`
- 证据原文：> firmware update

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01007 POWER ON for DRIVE-CLiQ component required
Reaction: NONE
Acknowledge: NONE
Cause: A DRIVE-CLiQ component must be switched on again (POWER ON) (e.g. due to a firmware update).
Alarm value (r2124, interpret decimal):
Component number of the DRIVE-CLiQ component.
Note:
For a component number = 1, a POWER ON of the Control Unit is required.
Remedy: - Switch off the power supply of the specified DRIVE-CLiQ component and switch it on again.
- For SINUMERIK, auto commissioning is prevented. In this case, a POWER ON is required for all components and the auto
commissioning must be restarted.
```

---

### CR-CAND-V3-002 · A01009

- 来源记录：`SIEMENS_S210_2019_A01009`（序号 None）
- 故障描述：Control module overtemperature
- 候选原因节点：The temperature of the control module (Control Unit) has exceeded the specified limit value.
- 目标故障实体：`A01009` · Control module overtemperature
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01009:cause:4`，字符位置 `82-184`
- 证据原文：> The temperature (r0037[0]) of the control module (Control Unit) has exceeded the specified limit value

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01009 CU: Control module overtemperature
Reaction: NONE
Acknowledge: NONE
Cause: The temperature (r0037[0]) of the control module (Control Unit) has exceeded the specified limit value.
Remedy: - check the air intake for the Control Unit.
- check the Control Unit fan.
Note:
The alarm is automatically withdrawn once the limit value has been fallen below.
```

---

### CR-CAND-V3-003 · A01016

- 来源记录：`SIEMENS_S210_2019_A01016`（序号 None）
- 故障描述：Firmware changed
- 候选原因节点：At least one firmware file in the directory was illegally changed on the non-volatile memory (memory card/device memory) with respect to the version when shipped from the factory.
- 目标故障实体：`A01016` · Firmware changed
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01016:cause:2`，字符位置 `64-243`
- 证据原文：> At least one firmware file in the directory was illegally changed on the non-volatile memory (memory card/device memory) with respect to the version when shipped from the factory.

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

### CR-CAND-V3-009 · A01019

- 来源记录：`SIEMENS_S210_2019_A01019`（序号 None）
- 故障描述：Writing to the removable data medium unsuccessful
- 候选原因节点：The write access to the removable data medium was unsuccessful.
- 目标故障实体：`A01019` · Writing to the removable data medium unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01019:cause:2`，字符位置 `97-160`
- 证据原文：> The write access to the removable data medium was unsuccessful.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01019 Writing to the removable data medium unsuccessful
Reaction: NONE
Acknowledge: NONE
Cause: The write access to the removable data medium was unsuccessful.
Remedy: Remove and check the removable data medium. Then run the data backup again.
```

---

### CR-CAND-V3-010 · A01020

- 来源记录：`SIEMENS_S210_2019_A01020`（序号 None）
- 故障描述：Writing to RAM disk unsuccessful
- 候选原因节点：A write access to the internal RAM disk was unsuccessful.
- 目标故障实体：`A01020` · Writing to RAM disk unsuccessful
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01020:cause:2`，字符位置 `80-137`
- 证据原文：> A write access to the internal RAM disk was unsuccessful.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01020 Writing to RAM disk unsuccessful
Reaction: NONE
Acknowledge: NONE
Cause: A write access to the internal RAM disk was unsuccessful.
Remedy: Adapt the file size for the system logbook to the internal RAM disk (p9930).
```

---

### CR-CAND-V3-011 · A01035

- 来源记录：`SIEMENS_S210_2019_A01035`（序号 None）
- 故障描述：Parameter back-up file corrupted
- 候选原因节点：When the Control Unit is booted, no complete data set was found from the parameter back-up files.
- 目标故障实体：`A01035` · Parameter back-up file corrupted
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01035:cause:3`，字符位置 `85-182`
- 证据原文：> When the Control Unit is booted, no complete data set was found from the parameter back-up files.

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

### CR-CAND-V3-014 · A01045

- 来源记录：`SIEMENS_S210_2019_A01045`（序号 None）
- 故障描述：Configuring data invalid
- 候选原因节点：An error was detected when evaluating the parameter files PSxxxyyy.ACX, PTxxxyyy.ACX, CAxxxyyy.ACX, or CCxxxyyy.ACX saved in the non-volatile memory.
- 目标故障实体：`A01045` · Configuring data invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01045:cause:3`，字符位置 `76-225`
- 证据原文：> An error was detected when evaluating the parameter files PSxxxyyy.ACX, PTxxxyyy.ACX, CAxxxyyy.ACX, or CCxxxyyy.ACX saved in the non-volatile memory.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01045 CU: Configuring data invalid
Reaction: NONE
Acknowledge: NONE
Cause: An error was detected when evaluating the parameter files PSxxxyyy.ACX, PTxxxyyy.ACX, CAxxxyyy.ACX, or
CCxxxyyy.ACX saved in the non-volatile memory. Because of this, under certain circumstances, several of the saved
parameter values were not able to be accepted.
Alarm value (r2124, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: - Restore the factory setting using (p0976 = 1) and re-load the project into the drive unit.
Then save the parameterization using the "Copy RAM to ROM" or with p0977 = 1. This overwrites the incorrect parameter
files in the non-volatile memory – and the alarm is withdrawn.
```

---

### CR-CAND-V3-015 · A01049

- 来源记录：`SIEMENS_S210_2019_A01049`（序号 None）
- 故障描述：It is not possible to write to file
- 候选原因节点：It is not possible to write into a write-protected file (PSxxxxxx.acx)
- 目标故障实体：`A01049` · It is not possible to write to file
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01049:cause:3`，字符位置 `87-157`
- 证据原文：> It is not possible to write into a write-protected file (PSxxxxxx.acx)

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01049 CU: It is not possible to write to file
Reaction: NONE
Acknowledge: NONE
Cause: It is not possible to write into a write-protected file (PSxxxxxx.acx). The write request was interrupted.
Alarm value (r2124, interpret decimal):
Drive object number.
Remedy: Check whether the "write protected" attribute has been set for the files in the non-volatile memory under .../USER/
SINAMICS/DATA/...
When required, remove write protection and save again (e.g. set p0977 to 1).
```

---

### CR-CAND-V3-016 · A01064

- 来源记录：`SIEMENS_S210_2019_A01064`（序号 None）
- 故障描述：Internal error (CRC)
- 候选原因节点：A checksum error (CRC error) has occurred in the Control Unit program memory
- 目标故障实体：`A01064` · Internal error (CRC)
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01064:cause:3`，字符位置 `72-148`
- 证据原文：> A checksum error (CRC error) has occurred in the Control Unit program memory

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01064 CU: Internal error (CRC)
Reaction: NONE
Acknowledge: NONE
Cause: A checksum error (CRC error) has occurred in the Control Unit program memory
432 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: - carry out a POWER ON (switch-off/switch-on) for all components.
- upgrade firmware to later version.
- contact Technical Support.
```

---

### CR-CAND-V3-017 · A01073

- 来源记录：`SIEMENS_S210_2019_A01073`（序号 None）
- 故障描述：POWER ON required for backup copy on memory card
- 候选原因节点：The parameter assignment on the visible partition of the memory card has changed.
- 目标故障实体：`A01073` · POWER ON required for backup copy on memory card
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01073:cause:2`，字符位置 `96-177`
- 证据原文：> The parameter assignment on the visible partition of the memory card has changed.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01073 POWER ON required for backup copy on memory card
Reaction: NONE
Acknowledge: NONE
Cause: The parameter assignment on the visible partition of the memory card has changed.
In order that the backup copy on the memory card is updated on the non-visible partition, it is necessary to carry out a
POWER ON or hardware reset (p0972) of the Control Unit.
Note:
It is possible that a new POWER ON is requested via this alarm (e.g. after saving with p0971 = 1).
Remedy: - carry out a POWER ON (switch-off/switch-on) for the Control Unit.
- carry out a hardware reset (RESET button, p0972).
```

---

### CR-CAND-V3-018 · A01099

- 来源记录：`SIEMENS_S210_2019_A01099`（序号 None）
- 故障描述：UTC synchronization tolerance violated
- 候选原因节点：The tolerance (p3109) set for UTC synchronization was violated.
- 目标故障实体：`A01099` · UTC synchronization tolerance violated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01099:cause:2`，字符位置 `86-149`
- 证据原文：> The tolerance (p3109) set for UTC synchronization was violated.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01099 UTC synchronization tolerance violated
Reaction: NONE
Acknowledge: NONE
Cause: The tolerance (p3109) set for UTC synchronization was violated.
Note:
UTC: Universal Time Coordinates
Remedy: Select the synchronization intervals shorter so that the deviation between the time of day master and drive system lies within
the tolerance.
Note:
The deviation when synchronizing is shown in r3107.
```

---

### CR-CAND-V3-019 · A01251

- 来源记录：`SIEMENS_S210_2019_A01251`（序号 None）
- 故障描述：CU-EEPROM incorrect read-write data
- 候选原因节点：Error when reading the read-write data of the EEPROM in the Control Unit.
- 目标故障实体：`A01251` · CU-EEPROM incorrect read-write data
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01251:cause:3`，字符位置 `87-160`
- 证据原文：> Error when reading the read-write data of the EEPROM in the Control Unit.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01251 CU: CU-EEPROM incorrect read-write data
Reaction: NONE
Acknowledge: NONE
Cause: Error when reading the read-write data of the EEPROM in the Control Unit.
Alarm value (r2124, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: For alarm value r2124 < 256, the following applies:
- carry out a POWER ON (switch-off/switch-on).
- replace the Control Unit.
For alarm value r2124 >= 256, the following applies:
- for the drive object with this alarm, clear the fault memory (p0952 = 0).
- as an alternative, clear the fault memory of all drive objects (p2147 = 1).
- replace the Control Unit.
```

---

### CR-CAND-V3-020 · A01304

- 来源记录：`SIEMENS_S210_2019_A01304`（序号 None）
- 故障描述：Firmware version of DRIVE-CLiQ component is not up-to-date
- 候选原因节点：The non-volatile memory has a more recent firmware version than the one in the connected DRIVE-CLiQ component.
- 目标故障实体：`A01304` · Firmware version of DRIVE-CLiQ component is not up-to-date
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01304:cause:3`，字符位置 `106-216`
- 证据原文：> The non-volatile memory has a more recent firmware version than the one in the connected DRIVE-CLiQ component.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01304 Firmware version of DRIVE-CLiQ component is not up-to-date
Reaction: NONE
Acknowledge: NONE
Cause: The non-volatile memory has a more recent firmware version than the one in the connected DRIVE-CLiQ component.
Alarm value (r2124, interpret decimal):
Component number of the DRIVE-CLiQ component involved.
Remedy: Update the firmware (p7828, p7829 - or commissioning tool).
```

---

### CR-CAND-V3-021 · A01306

- 来源记录：`SIEMENS_S210_2019_A01306`（序号 29）
- 故障描述：Firmware of the DRIVE-CLiQ component being updated
- 候选原因节点：Firmware update is active for at least one DRIVE-CLiQ component.
- 目标故障实体：`A01306` · Firmware of the DRIVE-CLiQ component being updated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01306:cause:5`，字符位置 `98-162`
- 证据原文：> Firmware update is active for at least one DRIVE-CLiQ component.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01306 Firmware of the DRIVE-CLiQ component being updated
Reaction: NONE
Acknowledge: NONE
Cause: Firmware update is active for at least one DRIVE-CLiQ component.
Alarm value (r2124, interpret decimal):
Component number of the DRIVE-CLiQ component.
Remedy: Not necessary.
This alarm is automatically withdrawn after the firmware update has been completed.
```

---

### CR-CAND-V3-022 · A01330

- 来源记录：`SIEMENS_S210_2019_A01330`（序号 None）
- 故障描述：Commissioning not possible
- 候选原因节点：The actual topology does not fulfill the requirements.
- 目标故障实体：`A01330` · Commissioning not possible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01330:cause:3`，字符位置 `119-173`
- 证据原文：> The actual topology does not fulfill the requirements.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01330 Topology: Commissioning not possible
Reaction: NONE
Acknowledge: NONE
Cause: Unable to carry out commissioning. The actual topology does not fulfill the requirements.
Remedy: - check the OCC cable between the converter and motor.
- carry out a POWER ON (switch-off/switch-on).
- Check that the connected hardware is supported.
Note:
OCC: One Cable Connection (one cable system)
436 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V3-023 · A01489

- 来源记录：`SIEMENS_S210_2019_A01489`（序号 None）
- 故障描述：motor with DRIVE-CLiQ not connected
- 候选原因节点：The topology comparison has detected a motor with DRIVE-CLiQ missing in the actual topology with respect to the target topology.
- 目标故障实体：`A01489` · motor with DRIVE-CLiQ not connected
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01489:cause:3`，字符位置 `93-221`
- 证据原文：> The topology comparison has detected a motor with DRIVE-CLiQ missing in the actual topology with respect to the target topology.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01489 Topology: motor with DRIVE-CLiQ not connected
Reaction: NONE
Acknowledge: NONE
Cause: The topology comparison has detected a motor with DRIVE-CLiQ missing in the actual topology with respect to the target
topology.
Alarm value (r2124, interpret hexadecimal):
ddccbbaa hex:
dd = connection number (%4)
cc = component number (%3)
bb = component class (% 2)
aa = component number of the component that has not been inserted (% 1)
Note:
The component is described in dd, cc and bb, where the component has not been inserted.
Component class and connection number are described in F01375.
Remedy: Adapting topologies:
- insert the components involved at the right connection (correct the actual topology).
- adapt the project/parameterizing in the commissioning tool (correct the target topology).
Check the hardware:
- check the 24 V supply voltage.
- check DRIVE-CLiQ cables for interruption and contact problems.
- check that the component is working properly.
Note:
Under "Topology --> Topology view" the commissioning tool where relevant offers improved diagnostics capability (e.g.
setpoint/actual value comparison).
```

---

### CR-CAND-V3-024 · A01590

- 来源记录：`SIEMENS_S210_2019_A01590`（序号 None）
- 故障描述：Motor maintenance interval expired
- 候选原因节点：The selected service/maintenance interval for this motor was reached.
- 目标故障实体：`A01590` · Motor maintenance interval expired
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01590:cause:3`，字符位置 `89-158`
- 证据原文：> The selected service/maintenance interval for this motor was reached.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01590 Drive: Motor maintenance interval expired
Reaction: NONE
Acknowledge: NONE
Cause: The selected service/maintenance interval for this motor was reached.
Alarm value (r2124, interpret decimal):
Motor data set number.
Remedy: carry out service/maintenance and reset the service/maintenance interval (p0651).
```

---

### CR-CAND-V3-025 · A01637

- 来源记录：`SIEMENS_S210_2019_A01637`（序号 None）
- 故障描述：Safety password not assigned
- 候选原因节点：Safety Integrated is parameterized and enabled. However, a valid safety password has still not been entered.
- 目标故障实体：`A01637` · Safety password not assigned
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01637:cause:3`，字符位置 `80-188`
- 证据原文：> Safety Integrated is parameterized and enabled. However, a valid safety password has still not been entered.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01637 SI: Safety password not assigned
Reaction: NONE
Acknowledge: NONE
Cause: Safety Integrated is parameterized and enabled. However, a valid safety password has still not been entered.
See also: r9767 (SI safety password status)
Remedy: - assign a valid safety password.
- carry out data save.
```

---

### CR-CAND-V3-026 · A01638

- 来源记录：`SIEMENS_S210_2019_A01638`（序号 None）
- 故障描述：Safety password entered
- 候选原因节点：A valid safety password has been entered.
- 目标故障实体：`A01638` · Safety password entered
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01638:cause:3`，字符位置 `75-116`
- 证据原文：> A valid safety password has been entered.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01638 SI: Safety password entered
Reaction: NONE
Acknowledge: NONE
Cause: A valid safety password has been entered. It is possible to change safety parameters in the safety commissioning mode.
See also: r9767 (SI safety password status)
Remedy: Not necessary.
This alarm is automatically withdrawn with "Delete password" (e.g. after exiting the web server - or after a Power on). The
password remains assigned.
```

---

### CR-CAND-V3-027 · A01654

- 来源记录：`SIEMENS_S210_2019_A01654`（序号 None）
- 故障描述：Deviating PROFIsafe configuration
- 候选原因节点：The configuration of a PROFIsafe telegram in the higher-level control (F-PLC) does not match the parameterization in the drive.
- 目标故障实体：`A01654` · Deviating PROFIsafe configuration
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01654:cause:3`，字符位置 `88-215`
- 证据原文：> The configuration of a PROFIsafe telegram in the higher-level control (F-PLC) does not match the parameterization in the drive.

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

### CR-CAND-V3-030 · A01691

- 来源记录：`SIEMENS_S210_2019_A01691`（序号 None）
- 故障描述：Ti and To unsuitable for PN cycle
- 候选原因节点：The configured times for PROFINET communication are not permitted and the PN cycle is used as the actual value acquisition cycle for the safe movement monitoring functions
- 目标故障实体：`A01691` · Ti and To unsuitable for PN cycle
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01691:cause:3`，字符位置 `92-263`
- 证据原文：> The configured times for PROFINET communication are not permitted and the PN cycle is used as the actual value acquisition cycle for the safe movement monitoring functions

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

### CR-CAND-V3-033 · A01693

- 来源记录：`SIEMENS_S210_2019_A01693`（序号 None）
- 故障描述：Safety parameter settings changed, warm restart/POWER ON required
- 候选原因节点：Safety parameters have been changed
- 目标故障实体：`A01693` · Safety parameter settings changed, warm restart/POWER ON required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01693:cause:3`，字符位置 `120-155`
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
A01693 SI P1: Safety parameter settings changed, warm restart/POWER ON required
Reaction: NONE
Acknowledge: NONE
Cause: Safety parameters have been changed; these will only take effect following a warm restart or POWER ON.
Alarm value (r2124, interpret decimal):
Parameter number of the safety parameter which has changed, necessitating a warm restart or POWER ON.
Remedy: - carry out a warm restart.
- carry out a POWER ON (switch-off/switch-on).
Note:
A POWER ON is required before carrying out the acceptance test.
```

---

### CR-CAND-V3-034 · A01695

- 来源记录：`SIEMENS_S210_2019_A01695`（序号 None）
- 故障描述：Sensor Module was replaced
- 候选原因节点：A Sensor Module, which is used for safe motion monitoring functions, was replaced
- 目标故障实体：`A01695` · Sensor Module was replaced
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01695:cause:3`，字符位置 `85-166`
- 证据原文：> A Sensor Module, which is used for safe motion monitoring functions, was replaced

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01695 SI Motion: Sensor Module was replaced
Reaction: NONE
Acknowledge: NONE
Cause: A Sensor Module, which is used for safe motion monitoring functions, was replaced. The hardware replacement must be
acknowledged. An acceptance test must be subsequently performed.
Note:
This message does not result in a safety stop response.
Remedy: - save all parameters
- acknowledge fault.
```

---

### CR-CAND-V3-035 · A01696

- 来源记录：`SIEMENS_S210_2019_A01696`（序号 None）
- 故障描述：Test stop for the motion monitoring functions selected when booting
- 候选原因节点：The forced checking procedure (test stop) for the safe motion monitoring functions is already selected when booting, which is not permissible.
- 目标故障实体：`A01696` · Test stop for the motion monitoring functions selected when booting
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01696:cause:3`，字符位置 `126-268`
- 证据原文：> The forced checking procedure (test stop) for the safe motion monitoring functions is already selected when booting, which is not permissible.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01696 SI Motion: Test stop for the motion monitoring functions selected when booting
Reaction: NONE
Acknowledge: NONE
Cause: The forced checking procedure (test stop) for the safe motion monitoring functions is already selected when booting, which
is not permissible.
This is the reason that the test is only carried out again after first selecting the forced checking procedure.
Note:
This message does not result in a safety stop response.
458 Operating Instructions, 01/2019, A5E41702836B AC
Remedy: Deselect the forced checking procedure (test stop) for the safe motion monitoring functions and then select again.
SI: Safety Integrated
```

---

### CR-CAND-V3-036 · A01697

- 来源记录：`SIEMENS_S210_2019_A01697`（序号 None）
- 故障描述：Test stop for motion monitoring functions required
- 候选原因节点：The time set in p9559 for the forced checking procedure (test stop) for the safe motion monitoring functions has been exceeded.
- 目标故障实体：`A01697` · Test stop for motion monitoring functions required
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01697:cause:3`，字符位置 `109-236`
- 证据原文：> The time set in p9559 for the forced checking procedure (test stop) for the safe motion monitoring functions has been exceeded.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01697 SI Motion: Test stop for motion monitoring functions required
Reaction: NONE
Acknowledge: NONE
Cause: The time set in p9559 for the forced checking procedure (test stop) for the safe motion monitoring functions has been
exceeded. A new forced checking procedure is required.
After the next time the forced checking procedure is selected, the message is withdrawn and the monitoring time is reset.
Note:
- this message does not result in a safety stop response.
- As the switch-off signal paths are not automatically checked during booting, an alarm is always issued once booting is
complete.
- the test must be performed within a defined, maximum time interval (p9559, maximum of 9000 hours) in order to comply
with the requirements as laid down in the standards for timely fault detection and the conditions to calculate the failure rates
of safety functions (PFH value). Operation beyond this maximum time period is permissible if it can be ensured that the
forced checking procedure is performed before persons enter the hazardous area and who are depending on the safety
functions correctly functioning.
See also: p9559 (SI Motion forced checking procedure timer), r9765 (SI Motion forced checking procedure remaining time)
Remedy: Carry out the forced checking procedure (test stop) for the safe motion monitoring functions.
Note:
SI: Safety Integrated
```

---

### CR-CAND-V3-037 · A01698

- 来源记录：`SIEMENS_S210_2019_A01698`（序号 None）
- 故障描述：Commissioning mode active
- 候选原因节点：The commissioning of the 'Safety Integrated' function is selected.
- 目标故障实体：`A01698` · Commissioning mode active
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01698:cause:4`，字符位置 `80-145`
- 证据原文：> The commissioning of the "Safety Integrated" function is selected

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01698 SI P1: Commissioning mode active
Reaction: NONE
Acknowledge: NONE
Cause: The commissioning of the "Safety Integrated" function is selected.
Note:
- this message does not result in a safety stop response.
- in the safety commissioning mode, the "STO" function is internally selected.
See also: p0010 (Drive commissioning parameter filter 2)
Remedy: Not necessary.
This message is automatically withdrawn after the safety functions have been commissioned.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

---

### CR-CAND-V3-038 · A01706

- 来源记录：`SIEMENS_S210_2019_A01706`（序号 30）
- 故障描述：SAM/SBR limit exceeded
- 候选原因节点：Motion monitoring functions with SAM: after initiating SS1 or SS2, the speed exceeded the set tolerance
- 目标故障实体：`A01706` · SAM/SBR limit exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01706:cause:3`，字符位置 `84-202`
- 证据原文：> Motion monitoring functions with SAM (p9506 = 0): - after initiating SS1 or SS2, the speed exceeded the set tolerance.

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

### CR-CAND-V3-040 · A01707

- 来源记录：`SIEMENS_S210_2019_A01707`（序号 None）
- 故障描述：Tolerance for safe operating stop exceeded
- 候选原因节点：The actual position has moved further away from the target position than the standstill tolerance.
- 目标故障实体：`A01707` · Tolerance for safe operating stop exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01707:cause:3`，字符位置 `104-202`
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
A01707 SI Motion P1: Tolerance for safe operating stop exceeded
Reaction: NONE
Acknowledge: NONE
Cause: The actual position has moved further away from the target position than the standstill tolerance.
The drive is stopped by message F01701.
Remedy: - check whether safety faults are present and if required carry out the appropriate diagnostic routines for the particular faults.
- check whether the standstill tolerance matches the accuracy and control dynamic performance of the axis.
- carry out a POWER ON (switch-off/switch-on).
Note:
SI: Safety Integrated
SOS: Safe Operating Stop
See also: p9530 (SI Motion standstill tolerance)
```

---

### CR-CAND-V3-041 · A01709

- 来源记录：`SIEMENS_S210_2019_A01709`（序号 None）
- 故障描述：SS2E initiated
- 候选原因节点：The drive is stopped using SS2E (braking along a path).
- 目标故障实体：`A01709` · SS2E initiated
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01709:cause:3`，字符位置 `76-131`
- 证据原文：> The drive is stopped using SS2E (braking along a path).

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

### CR-CAND-V3-043 · A01711

- 来源记录：`SIEMENS_S210_2019_A01711`（序号 None）
- 故障描述：Defect in a monitoring channel
- 候选原因节点：The drive has identified a difference between the input data or results of the monitoring functions and initiated A01711. Safe operation is no longer possible.
- 目标故障实体：`A01711` · Defect in a monitoring channel
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01711:cause:3`，字符位置 `145-244`
- 证据原文：> The drive has identified a difference between the input data or results of the monitoring functions

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

### CR-CAND-V3-052 · A01714

- 来源记录：`SIEMENS_S210_2019_A01714`（序号 None）
- 故障描述：Safely-Limited Speed exceeded
- 候选原因节点：The drive has moved faster than that specified by the velocity limit value (p9531).
- 目标故障实体：`A01714` · Safely-Limited Speed exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01714:cause:3`，字符位置 `91-174`
- 证据原文：> The drive has moved faster than that specified by the velocity limit value (p9531).

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

### CR-CAND-V3-058 · A01716

- 来源记录：`SIEMENS_S210_2019_A01716`（序号 None）
- 故障描述：Tolerance for safe motion direction exceeded
- 候选原因节点：The tolerance for the 'safe motion direction' function was exceeded.
- 目标故障实体：`A01716` · Tolerance for safe motion direction exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01716:cause:7`，字符位置 `106-173`
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

### CR-CAND-V3-061 · A01730

- 来源记录：`SIEMENS_S210_2019_A01730`（序号 None）
- 故障描述：Reference block for dynamic Safely-Limited Speed invalid
- 候选原因节点：The reference block transferred via PROFIsafe is negative
- 目标故障实体：`A01730` · Reference block for dynamic Safely-Limited Speed invalid
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01730:cause:3`，字符位置 `118-175`
- 证据原文：> The reference block transferred via PROFIsafe is negative

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

### CR-CAND-V3-063 · A01750

- 来源记录：`SIEMENS_S210_2019_A01750`（序号 None）
- 故障描述：Hardware fault safety-relevant encoder
- 候选原因节点：The encoder that is used for the safety-relevant motion monitoring functions signals a hardware fault.
- 目标故障实体：`A01750` · Hardware fault safety-relevant encoder
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01750:cause:3`，字符位置 `100-202`
- 证据原文：> The encoder that is used for the safety-relevant motion monitoring functions signals a hardware fault.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01750 SI Motion P1: Hardware fault safety-relevant encoder
Reaction: NONE
Acknowledge: NONE
Cause: The encoder that is used for the safety-relevant motion monitoring functions signals a hardware fault.
Message value (r2124, interpret decimal):
Encoder status word 1, encoder status word 2 that resulted in the message.
Remedy: - check the encoder connection.
- replace encoder.
```

---

### CR-CAND-V3-064 · A01751

- 来源记录：`SIEMENS_S210_2019_A01751`（序号 None）
- 故障描述：Effectivity test fault safety-relevant encoder
- 候选原因节点：The DRIVE-CLiQ encoder for safe motion monitoring signals an error for the effectivity tests.
- 目标故障实体：`A01751` · Effectivity test fault safety-relevant encoder
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01751:cause:3`，字符位置 `108-201`
- 证据原文：> The DRIVE-CLiQ encoder for safe motion monitoring signals an error for the effectivity tests.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01751 SI Motion P1: Effectivity test fault safety-relevant encoder
Reaction: NONE
Acknowledge: NONE
Cause: The DRIVE-CLiQ encoder for safe motion monitoring signals an error for the effectivity tests.
Message value (r2124, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: - check the encoder connection.
- replace encoder.
Note:
This message can be acknowledged via PROFIsafe (safe acknowledgment).
468 Operating Instructions, 01/2019, A5E41702836B AC
```

---

### CR-CAND-V3-065 · A01781

- 来源记录：`SIEMENS_S210_2019_A01781`（序号 None）
- 故障描述：SBT brake opening time exceeded
- 候选原因节点：The maximum time (11 s) to open the brake during the brake test was exceeded.
- 目标故障实体：`A01781` · SBT brake opening time exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01781:cause:3`，字符位置 `79-156`
- 证据原文：> The maximum time (11 s) to open the brake during the brake test was exceeded.

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

### CR-CAND-V3-068 · A01782

- 来源记录：`SIEMENS_S210_2019_A01782`（序号 None）
- 故障描述：SBT brake test incorrect control
- 候选原因节点：The brake test was canceled as a result of incorrect control.
- 目标故障实体：`A01782` · SBT brake test incorrect control
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01782:cause:2`，字符位置 `80-141`
- 证据原文：> The brake test was canceled as a result of incorrect control.

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

### CR-CAND-V3-071 · A01783

- 来源记录：`SIEMENS_S210_2019_A01783`（序号 None）
- 故障描述：SBT brake closing time exceeded
- 候选原因节点：The maximum time (11 s) to close the brake during the brake test was exceeded.
- 目标故障实体：`A01783` · SBT brake closing time exceeded
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01783:cause:3`，字符位置 `79-157`
- 证据原文：> The maximum time (11 s) to close the brake during the brake test was exceeded.

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

### CR-CAND-V3-073 · A01784

- 来源记录：`SIEMENS_S210_2019_A01784`（序号 None）
- 故障描述：SBT brake test canceled with fault
- 候选原因节点：the brake is not opened
- 目标故障实体：`A01784` · SBT brake test canceled with fault
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01784:cause:2`，字符位置 `263-286`
- 证据原文：> the brake is not opened

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

### CR-CAND-V3-090 · A01785

- 来源记录：`SIEMENS_S210_2019_A01785`（序号 None）
- 故障描述：SBT brake test configuration error
- 候选原因节点：Error when parameterizing the brake test
- 目标故障实体：`A01785` · SBT brake test configuration error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01785:cause:2`，字符位置 `135-175`
- 证据原文：> Error when parameterizing the brake test

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

### CR-CAND-V3-095 · A01788

- 来源记录：`SIEMENS_S210_2019_A01788`（序号 31）
- 故障描述：Automatic test stop waits for STO deselection via motion monitoring functions
- 候选原因节点：The automatic test stop (forced checking procedure) was not able to be carried out after powering up.
- 目标故障实体：`A01788` · Automatic test stop waits for STO deselection via motion monitoring functions
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01788:cause:6`，字符位置 `129-230`
- 证据原文：> The automatic test stop (forced checking procedure) was not able to be carried out after powering up.

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

### CR-CAND-V3-098 · A01796

- 来源记录：`SIEMENS_S210_2019_A01796`（序号 None）
- 故障描述：Wait for communication
- 候选原因节点：The drive waits for communication to be established to execute the safety-relevant motion monitoring functions.
- 目标故障实体：`A01796` · Wait for communication
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01796:cause:3`，字符位置 `77-188`
- 证据原文：> The drive waits for communication to be established to execute the safety-relevant motion monitoring functions.

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

### CR-CAND-V3-100 · A01798

- 来源记录：`SIEMENS_S210_2019_A01798`（序号 None）
- 故障描述：Test stop for motion monitoring functions running
- 候选原因节点：The forced checking procedure (test stop) for the safe motion monitoring functions is currently in progress.
- 目标故障实体：`A01798` · Test stop for motion monitoring functions running
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01798:cause:3`，字符位置 `111-219`
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
A01798 SI Motion P1: Test stop for motion monitoring functions running
Reaction: NONE
Acknowledge: NONE
Cause: The forced checking procedure (test stop) for the safe motion monitoring functions is currently in progress.
Remedy: Not necessary.
The message is automatically withdrawn when the test stop has been completed.
Note:
SI: Safety Integrated
```

---

### CR-CAND-V3-101 · A01839

- 来源记录：`SIEMENS_S210_2019_A01839`（序号 None）
- 故障描述：cable fault to the component
- 候选原因节点：The fault counter (r9936[0...199]) to monitor the DRIVE-CLiQ connections/cables has been incremented.
- 目标故障实体：`A01839` · cable fault to the component
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01839:cause:2`，字符位置 `153-254`
- 证据原文：> The fault counter (r9936[0...199]) to monitor the DRIVE-CLiQ connections/cables has been incremented.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01839 DRIVE-CLiQ diagnostics: cable fault to the component
Reaction: NONE
Acknowledge: NONE
472 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The fault counter (r9936[0...199]) to monitor the DRIVE-CLiQ connections/cables has been incremented.
Alarm value (r2124, interpret decimal):
Component number.
Note:
The component number specifies the component whose feeder cable from the direction of the Control Unit is faulted.
The alarm is automatically withdrawn after 5 seconds, assuming that no other data transfer error has occurred.
Remedy: - check the corresponding DRIVE-CLiQ cables.
- check the electrical cabinet design and cable routing for EMC compliance
```

---

### CR-CAND-V3-102 · A01900

- 来源记录：`SIEMENS_S210_2019_A01900`（序号 None）
- 故障描述：Configuration telegram error
- 候选原因节点：A controller attempts to establish a connection using an incorrect configuring telegram.
- 目标故障实体：`A01900` · Configuration telegram error
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01900:cause:3`，字符位置 `80-168`
- 证据原文：> A controller attempts to establish a connection using an incorrect configuring telegram.

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

### CR-CAND-V3-117 · A01902

- 来源记录：`SIEMENS_S210_2019_A01902`（序号 None）
- 故障描述：clock cycle synchronous operation parameterization not permissible
- 候选原因节点：Parameterization for isochronous operation is not permissible.
- 目标故障实体：`A01902` · clock cycle synchronous operation parameterization not permissible
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01902:cause:3`，字符位置 `118-180`
- 证据原文：> Parameterization for isochronous operation is not permissible.

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

### CR-CAND-V3-132 · A01932

- 来源记录：`SIEMENS_S210_2019_A01932`（序号 None）
- 故障描述：clock cycle synchronization missing for DSC
- 候选原因节点：There is no clock synchronization or clock synchronous sign of life and DSC is selected.
- 目标故障实体：`A01932` · clock cycle synchronization missing for DSC
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01932:cause:3`，字符位置 `95-183`
- 证据原文：> There is no clock synchronization or clock synchronous sign of life and DSC is selected.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01932 PN: clock cycle synchronization missing for DSC
Reaction: NONE
Acknowledge: NONE
Cause: There is no clock synchronization or clock synchronous sign of life and DSC is selected.
Note:
DSC: Dynamic Servo Control
See also: r0922 (PROFIdrive PZD telegram selection)
Remedy: Set clock synchronization across the bus configuration and transfer clock synchronous sign-of-life.
```

---

### CR-CAND-V3-133 · A01940

- 来源记录：`SIEMENS_S210_2019_A01940`（序号 None）
- 故障描述：Clock cycle synchronism not reached
- 候选原因节点：The master does not send a clock synchronous global control telegram although clock synchronous operation was selected when configuring the bus.
- 目标故障实体：`A01940` · Clock cycle synchronism not reached
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01940:cause:3`，字符位置 `291-435`
- 证据原文：> the master does not send a clock synchronous global control telegram although clock synchronous operation was selected when configuring the bus.

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

### CR-CAND-V3-136 · A01941

- 来源记录：`SIEMENS_S210_2019_A01941`（序号 None）
- 故障描述：Clock cycle signal missing when the bus is being established
- 候选原因节点：The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing telegram. The global control telegram for synchronization is not being received.
- 目标故障实体：`A01941` · Clock cycle signal missing when the bus is being established
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01941:cause:3`，字符位置 `112-305`
- 证据原文：> The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing telegram. The global control telegram for synchronization is not being received.

**专家填写：**

- causal_status：
- direction：
- relation_type：
- fta_eligible：
- overall_decision：
- 审核意见：

**完整原文：**

```text
A01941 PN: Clock cycle signal missing when the bus is being established
Reaction: NONE
Acknowledge: NONE
Cause: The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing
telegram. The global control telegram for synchronization is not being received.
Remedy: Check the master application and bus configuration.
Note:
PN: PROFINET
```

---

### CR-CAND-V3-137 · A01943

- 来源记录：`SIEMENS_S210_2019_A01943`（序号 None）
- 故障描述：Clock cycle signal error when the bus is being established
- 候选原因节点：The bus is in the data exchange state and clock synchronous operation has been selected using the parameterizing telegram.
- 目标故障实体：`A01943` · Clock cycle signal error when the bus is being established
- 系统提出的关系假设：`cause_node --causes--> fault_entity`（仅供审核，不是结论）
- 证据引用：`SIEMENS_S210_2019_A01943:cause:3`，字符位置 `110-232`
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
