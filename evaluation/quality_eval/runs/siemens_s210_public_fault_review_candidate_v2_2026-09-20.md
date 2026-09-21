# SINAMICS S210 第二批模型抽取待审核清单

> 本文件包含模型候选结果和证据，不是专家金标，不提供预审通过结论。
> 专家必须以每条记录的原文为依据，独立填写最终字段、证据和审核结论。

- 样本数：30
- 模型抽取成功：30
- 证据位置通过结构校验：30
- 待审核：30

## 01. SIEMENS_S210_2019_A01007

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "4cddf60a-6b85-4083-a6b8-6f0b1dfde484",
    "fault_code": "A01007",
    "component": "DRIVE-CLiQ component",
    "related_components": [],
    "description": "POWER ON for DRIVE-CLiQ component required",
    "causes": [
      "firmware update"
    ],
    "parameters": [
      "r2124"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 02. SIEMENS_S210_2019_A01330

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "f3232a22-6f50-4a83-b954-b18ed7f1b2f2",
    "fault_code": "A01330",
    "component": "Topology",
    "related_components": [],
    "description": "Commissioning not possible",
    "causes": [
      "The actual topology does not fulfill the requirements."
    ],
    "parameters": []
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 03. SIEMENS_S210_2019_A01707

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "db2f5870-95e8-4261-a69a-556aeedcb2ea",
    "fault_code": "A01707",
    "component": "SI Motion",
    "related_components": [],
    "description": "Tolerance for safe operating stop exceeded",
    "causes": [
      "The actual position has moved further away from the target position than the standstill tolerance."
    ],
    "parameters": [
      "p9530"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 04. SIEMENS_S210_2019_A01796

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "6be1808a-f621-4e9c-b800-193991680f02",
    "fault_code": "A01796",
    "component": "Safety Integrated",
    "related_components": [],
    "description": "Wait for communication",
    "causes": [
      "The drive waits for communication to be established to execute the safety-relevant motion monitoring functions.",
      "Wait for communication to be established to PROFIsafe F-Host."
    ],
    "parameters": [
      "r2124",
      "p9601"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 05. SIEMENS_S210_2019_A01989

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "e30d58a5-67ab-471a-8a0f-48c292712b81",
    "fault_code": "A01989",
    "component": "PN",
    "related_components": [],
    "description": "internal cyclic data transfer error",
    "causes": [
      "The cyclic actual values and/or setpoints were not transferred within the specified times."
    ],
    "parameters": [
      "r2124"
    ]
  }
]
```

### 原文

```text
A01989 PN: internal cyclic data transfer error
Reaction: NONE
Acknowledge: NONE
Cause: The cyclic actual values and/or setpoints were not transferred within the specified times.
Alarm value (r2124, interpret hexadecimal):
Only for internal Siemens troubleshooting.
Remedy: Correctly set T_io_input or T_io_output.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 06. SIEMENS_S210_2019_A08800

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "f680f05d-68ac-4ab0-bf22-79ceb3f99719",
    "fault_code": "A08800",
    "component": "",
    "related_components": [],
    "description": "PROFIenergy energy-saving mode active",
    "causes": [
      "The PROFIenergy energy-saving mode is active"
    ],
    "parameters": [
      "r2124",
      "r5600"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 07. SIEMENS_S210_2019_A30076

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "3ed16dc2-3898-435c-892a-6a3a763e5215",
    "fault_code": "A30076",
    "component": "Power unit",
    "related_components": [],
    "description": "thermal overload internal braking resistor alarm",
    "causes": [
      "The energy absorbed by the internal braking resistor has exceeded the alarm threshold of 80 %."
    ],
    "parameters": [
      "r2124"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 08. SIEMENS_S210_2019_A31700

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "4810b4e0-c058-4dee-a61f-7f6bbb718d47",
    "fault_code": "A31700",
    "component": "Encoder 1",
    "related_components": [],
    "description": "Functional safety monitoring initiated",
    "causes": [
      "Functional safety was activated",
      "Self-test of the DRIVE-CLiQ encoder has detected a fault",
      "Effectivity test x unsuccessful"
    ],
    "parameters": [
      "r2124"
    ]
  }
]
```

### 原文

```text
A31700 Encoder 1: Functional safety monitoring initiated
Reaction: NONE
Acknowledge: NONE
Cause: Functional safety was activated. Self-test of the DRIVE-CLiQ encoder has detected a fault.
Alarm value (r2124, interpret binary):
Bit x = 1: Effectivity test x unsuccessful.
Remedy: Replace encoder.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 09. SIEMENS_S210_2019_F01001

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "dcf9c715-c7e8-4b61-afc9-2b54c0e0bc78",
    "fault_code": "F01001",
    "component": "",
    "related_components": [],
    "description": "FloatingPoint exception",
    "causes": [
      "An exception occurred during an operation with the FloatingPoint data type.",
      "The error may be caused by the basic system or a technology function (e.g. FBLOCKS, DCC, TEC).",
      "Operation invalid",
      "Division by zero",
      "Overflow",
      "Underflow",
      "Inaccurate result"
    ],
    "parameters": [
      "r0949",
      "r9999"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 10. SIEMENS_S210_2019_F01030

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "5f0b443f-9643-4e18-85d4-05333908eb58",
    "fault_code": "F01030",
    "component": "master control",
    "related_components": [],
    "description": "Sign-of-life failure for master control",
    "causes": [
      "For active PC master control, no sign-of-life was received within the monitoring time."
    ],
    "parameters": []
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 11. SIEMENS_S210_2019_F01043

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "74f23289-0b27-4bd6-842b-d412f3e2c341",
    "fault_code": "F01043",
    "component": "",
    "related_components": [],
    "description": "Fatal error at project download",
    "causes": [
      "A fatal error was detected when downloading a project using the commissioning tool.",
      "Device status cannot be changed to Device Download (drive object ON?).",
      "Incorrect drive object number.",
      "A drive object that has already been deleted is deleted again.",
      "Deleting of a drive object that has already been registered for generation.",
      "Deleting a drive object that does not exist.",
      "Generating an undeleted drive object that already existed.",
      "Regenerating a drive object already registered for generation.",
      "Maximum number of drive objects that can be generated exceeded.",
      "Error while generating a device drive object.",
      "Error while generating target topology parameters (p9902 and p9903).",
      "Error while generating a drive object (global component).",
      "Error while generating a drive object (drive component).",
      "Unknown drive object type.",
      "Drive status cannot be changed to 'ready for operation' (r0947 and r0949).",
      "Drive status cannot be changed to drive download.",
      "Device status cannot be changed to 'ready for operation'.",
      "It is not possible to download the topology.",
      "A new download is only possible if the factory settings are restored for the drive unit.",
      "The slot for the option module has been configured several times (e.g. CAN and COMM BOARD)",
      "The configuration is inconsistent (e.g. CAN for Control Unit, however no CAN configured for drive objects A_INF, SERVO or VECTOR).",
      "Error when accepting the download parameters.",
      "Software-internal download error.",
      "download not possible when know-how protection is activated.",
      "download not possible during a partial power up after inserting a component.",
      "The configuration is inconsistent. Know-how protection is either not activated or only partially."
    ],
    "parameters": [
      "r0949",
      "p9902",
      "p9903",
      "r0947",
      "p0340",
      "p0010",
      "p0976"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 12. SIEMENS_S210_2019_F01250

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "51a90340-8872-458a-a249-b53ab033b465",
    "fault_code": "F01250",
    "component": "CU",
    "related_components": [],
    "description": "CU-EEPROM incorrect read-only data",
    "causes": [
      "Error when reading the read-only data of the EEPROM in the Control Unit."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

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

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 13. SIEMENS_S210_2019_F01651

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "59639840-5a55-40b5-8db5-c4e644c20dc8",
    "fault_code": "F01651",
    "component": "Safety Integrated",
    "related_components": [],
    "description": "Synchronization safety time slices unsuccessful",
    "causes": [
      "The 'Safety Integrated' function requires a synchronization of the safety time slices between the two monitoring channels and between the drive and the higher-level control. This synchronization routine was unsuccessful."
    ],
    "parameters": []
  }
]
```

### 原文

```text
F01651 SI P1: Synchronization safety time slices unsuccessful
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function requires a synchronization of the safety time slices between the two monitoring channels
and between the drive and the higher-level control. This synchronization routine was unsuccessful.
Note:
This fault results in an STO that cannot be acknowledged.
Remedy: - carry out a POWER ON (switch-off/switch-on).
- upgrade the drive software.
- upgrade the software of the higher-level control.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 14. SIEMENS_S210_2019_F01671

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "00e23f05-9309-45c8-90ad-d5e689a93569",
    "fault_code": "F01671",
    "component": "SI Motion",
    "related_components": [],
    "description": "Parameterization encoder error",
    "causes": [
      "The parameterization of the encoder used by Safety Integrated is different to the parameterization of the standard encoder."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F01671 SI Motion: Parameterization encoder error
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The parameterization of the encoder used by Safety Integrated is different to the parameterization of the standard encoder.
Note:
This fault does not result in a safety stop response.
Fault value (r0949, interpret decimal):
Parameter number of the non-corresponding safety parameter.
Remedy: Align the encoder parameterization between the safety encoder and the standard encoder.
Note:
SI: Safety Integrated
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 15. SIEMENS_S210_2019_F01683

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "cb66fc2a-edf5-468d-9832-0977065e4151",
    "fault_code": "F01683",
    "component": "SI Motion",
    "related_components": [],
    "description": "SOS/SLS enable missing",
    "causes": [
      "The safety-relevant basic function 'SOS/SLS' is not enabled in p9501 although other safety-relevant monitoring functions are enabled."
    ],
    "parameters": [
      "p9501",
      "p9501.0"
    ]
  }
]
```

### 原文

```text
F01683 SI Motion P1: SOS/SLS enable missing
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The safety-relevant basic function "SOS/SLS" is not enabled in p9501 although other safety-relevant monitoring functions
are enabled.
Note:
This fault does not result in a safety stop response.
Remedy: Enable the function "SOS/SLS" (p9501.0) and carry out a POWER ON.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
SOS: Safe Operating Stop
See also: p9501 (SI Motion enable safety functions)
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 16. SIEMENS_S210_2019_F01910

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "6cc01076-8e31-4a39-a6d3-a65a367ee696",
    "fault_code": "F01910",
    "component": "Fieldbus",
    "related_components": [],
    "description": "setpoint timeout",
    "causes": [
      "The reception of setpoints from the fieldbus interface (onboard, PROFIBUS/PROFINET/USS) has been interrupted.",
      "bus connection interrupted.",
      "controller switched off.",
      "controller set into the STOP state."
    ],
    "parameters": []
  }
]
```

### 原文

```text
F01910 Fieldbus: setpoint timeout
Reaction: OFF3
Acknowledge: IMMEDIATELY
474 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The reception of setpoints from the fieldbus interface (onboard, PROFIBUS/PROFINET/USS) has been interrupted.
- bus connection interrupted.
- controller switched off.
- controller set into the STOP state.
Remedy: Restore the bus connection and set the controller to RUN.
Note regarding PROFIBUS slave redundancy:
For operation on a Y link, it must be ensured that "DP alarm mode = DPV1" is set in the slave parameterization.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 17. SIEMENS_S210_2019_F07085

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "8169bd99-1d60-4681-b9c2-2ebc4236f306",
    "fault_code": "F07085",
    "component": "Drive",
    "related_components": [],
    "description": "Open-loop/closed-loop control parameters changed",
    "causes": [
      "Open-loop/closed-loop control parameters have had to be changed.",
      "As a result of other parameters, they have exceeded the dynamic limits.",
      "They cannot be used due to the fact that the hardware detected not having certain features.",
      "The value is estimated as the thermal time constant is missing.",
      "Motor temperature model 1 is activated as thermal motor protection is missing."
    ],
    "parameters": [
      "p1082"
    ]
  }
]
```

### 原文

```text
F07085 Drive: Open-loop/closed-loop control parameters changed
Reaction: NONE
Acknowledge: IMMEDIATELY
Cause: Open-loop/closed-loop control parameters have had to be changed.
Possible causes:
1. As a result of other parameters, they have exceeded the dynamic limits.
2. They cannot be used due to the fact that the hardware detected not having certain features.
3. The value is estimated as the thermal time constant is missing.
4. Motor temperature model 1 is activated as thermal motor protection is missing.
See also: p1082 (Maximum speed)
Remedy: Not necessary.
It is not necessary to change the parameters as they have already been correctly limited.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 18. SIEMENS_S210_2019_F07575

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "9f26235f-5066-4ce6-8154-0e6835eb18c5",
    "fault_code": "F07575",
    "component": "Drive",
    "related_components": [],
    "description": "Motor encoder not ready",
    "causes": [
      "The motor encoder signals that it is not ready.",
      "initialization of encoder 1 (motor encoder) was unsuccessful.",
      "the function 'parking encoder' is active (encoder control word G1_STW.14 = 1).",
      "the encoder interface (Sensor Module) is deactivated (p0145).",
      "the Sensor Module is defective."
    ],
    "parameters": [
      "p0145"
    ]
  }
]
```

### 原文

```text
F07575 Drive: Motor encoder not ready
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The motor encoder signals that it is not ready.
- initialization of encoder 1 (motor encoder) was unsuccessful.
- the function "parking encoder" is active (encoder control word G1_STW.14 = 1).
- the encoder interface (Sensor Module) is deactivated (p0145).
- the Sensor Module is defective.
Remedy: Evaluate other queued faults via encoder 1.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 19. SIEMENS_S210_2019_F13000

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "8328abdc-301c-4270-9fea-cc8e7cbcb7c6",
    "fault_code": "F13000",
    "component": "",
    "related_components": [],
    "description": "License not adequate",
    "causes": [
      "for the drive unit, the options that require a license are being used but the licenses are not sufficient",
      "an error occurred when checking the existing licenses",
      "The existing license is not sufficient",
      "An adequate license was not able to be determined as the memory card with the required licensing data was withdrawn in operation",
      "An adequate license was not able to be determined as there is no licensing data available on the memory card",
      "An adequate license was not able to be determined as there is a checksum error in the license key",
      "An internal error occurred when checking the license"
    ],
    "parameters": [
      "r0949",
      "p9920",
      "p9921"
    ]
  }
]
```

### 原文

```text
F13000 License not adequate
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: - for the drive unit, the options that require a license are being used but the licenses are not sufficient.
- an error occurred when checking the existing licenses.
Fault value (r0949, decimal interpretation):
0:
The existing license is not sufficient.
1:
An adequate license was not able to be determined as the memory card with the required licensing data was withdrawn in
operation.
2:
An adequate license was not able to be determined as there is no licensing data available on the memory card.
3:
An adequate license was not able to be determined as there is a checksum error in the license key.
4:
An internal error occurred when checking the license.
Remedy: For fault value = 0:
Additional licenses are required and these must be activated (p9920, p9921).
For fault value = 1:
With the system powered down, re-insert the memory card that matches the system.
For fault value = 2:
Enter and activate the license key (p9920, p9921).
For fault value = 3:
Compare the license key (p9920) entered with the license key on the certificate of license.
Re-enter the license key and activate (p9920, p9921).
For fault value = 4:
- carry out a POWER ON.
- upgrade firmware to later version.
- contact Technical Support.
Note:
An overview of the drive device functions requiring a license can be displayed using a commissioning tool in the online
mode. Depending on the commissioning tool, you can obtain the necessary licenses (serial number, license Key, Trial
License Mode).
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 20. SIEMENS_S210_2019_F30004

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "77347ccc-f750-40ca-bc1e-8740ebf5ce1b",
    "fault_code": "F30004",
    "component": "Power unit",
    "related_components": [],
    "description": "Overtemperature heat sink AC inverter",
    "causes": [
      "The temperature of the power unit heat sink has exceeded the permissible limit value.",
      "insufficient cooling, fan failure",
      "overload",
      "ambient temperature too high",
      "pulse frequency too high"
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F30004 Power unit: Overtemperature heat sink AC inverter
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The temperature of the power unit heat sink has exceeded the permissible limit value.
- insufficient cooling, fan failure.
- overload.
- ambient temperature too high.
- pulse frequency too high.
Fault value (r0949, interpret decimal):
Temperature [0.01 °C].
Remedy: - check whether the fan is running.
- check the fan elements.
- check whether the ambient temperature is in the permissible range.
- check the motor load.
- reduce the pulse frequency if this is higher than the rated pulse frequency.
Notice:
This fault can only be acknowledged after the alarm threshold for alarm A05000 has been undershot.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 21. SIEMENS_S210_2019_F30025

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "56ab7114-670f-4159-903e-0b13d54679db",
    "fault_code": "F30025",
    "component": "Power unit",
    "related_components": [],
    "description": "Chip overtemperature",
    "causes": [
      "The chip temperature of the semiconductor has exceeded the permissible limit value.",
      "the permissible load duty cycle was not maintained",
      "insufficient cooling, fan failure",
      "overload",
      "ambient temperature too high",
      "pulse frequency too high"
    ],
    "parameters": [
      "r0949",
      "r0037"
    ]
  }
]
```

### 原文

```text
F30025 Power unit: Chip overtemperature
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The chip temperature of the semiconductor has exceeded the permissible limit value.
- the permissible load duty cycle was not maintained.
- insufficient cooling, fan failure.
- overload.
- ambient temperature too high.
- pulse frequency too high.
Fault value (r0949, interpret decimal):
Temperature difference between the heat sink and chip [0.01 °C].
Remedy: - adapt the load duty cycle.
- check whether the fan is running.
- check the fan elements.
- check whether the ambient temperature is in the permissible range.
- check the motor load.
- reduce the pulse frequency if this is higher than the rated pulse frequency.
Notice:
This fault can only be acknowledged after the alarm threshold for alarm A05001 has been undershot.
See also: r0037 (Drive temperatures)
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 22. SIEMENS_S210_2019_F30068

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "3571cd9a-a661-441a-b8a2-6027b48a1417",
    "fault_code": "F30068",
    "component": "Power unit",
    "related_components": [],
    "description": "undertemperature inverter heat sink",
    "causes": [
      "The actual inverter heat sink temperature is below the permissible minimum value.",
      "the power unit is being operated at an ambient temperature that lies below the permissible range.",
      "the temperature sensor evaluation is defective."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F30068 Power unit: undertemperature inverter heat sink
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The actual inverter heat sink temperature is below the permissible minimum value.
Possible causes:
- the power unit is being operated at an ambient temperature that lies below the permissible range.
- the temperature sensor evaluation is defective.
Fault value (r0949, interpret decimal):
Inverter heat sink temperature [0.1 °C].
Remedy: - ensure that higher ambient temperatures prevail.
- replace the power unit.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 23. SIEMENS_S210_2019_F30651

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "f1f9238a-f3dc-41f7-b9a9-04fc03553867",
    "fault_code": "F30651",
    "component": "Safety Integrated",
    "related_components": [],
    "description": "synchronization with monitoring channel 1 unsuccessful",
    "causes": [
      "The 'Safety Integrated' function requires synchronization of the safety time slices in both monitoring channels. This synchronization routine was unsuccessful."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F30651 SI P2: synchronization with monitoring channel 1 unsuccessful
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The "Safety Integrated" function requires synchronization of the safety time slices in both monitoring channels. This
synchronization routine was unsuccessful.
Note:
This fault results in an STO that cannot be acknowledged.
Fault value (r0949, interpret decimal):
Only for internal Siemens troubleshooting.
Remedy: - carry out a POWER ON (switch-off/switch-on).
- upgrade the drive software.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 24. SIEMENS_S210_2019_F30683

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "2a514287-9b74-4130-a46e-0dc64692253f",
    "fault_code": "F30683",
    "component": "SI Motion",
    "related_components": [],
    "description": "SOS/SLS enable missing",
    "causes": [
      "The safety-relevant basic function 'SOS/SLS' is not enabled, although other safety-relevant monitoring functions are enabled."
    ],
    "parameters": []
  }
]
```

### 原文

```text
F30683 SI Motion P2: SOS/SLS enable missing
Reaction: OFF2
Acknowledge: IMMEDIATELY
Cause: The safety-relevant basic function "SOS/SLS" is not enabled, although other safety-relevant monitoring functions are
enabled.
Note:
This message does not result in a safety stop response.
Remedy: Using the commissioning tool, copy the safety parameters, confirm the data change and carry out a power on.
Note:
SI: Safety Integrated
SLS: Safely-Limited Speed
SOS: Safe Operating Stop
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 25. SIEMENS_S210_2019_F31135

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "2f729c2c-1079-44ec-b20a-7fb41b1090ce",
    "fault_code": "F31135",
    "component": "Encoder 1",
    "related_components": [],
    "description": "Fault when determining the position (single turn)",
    "causes": [
      "position determination fault (singleturn)",
      "hardware fault EnDat supply",
      "EnDat encoder withdrawn when not in the parked state",
      "overcurrent EnDat supply",
      "overvoltage EnDat supply",
      "internal communication error",
      "Lighting",
      "Signal amplitude",
      "Singleturn position 1",
      "Overvoltage",
      "Undervoltage",
      "Overcurrent",
      "Temperature exceeded",
      "Singleturn system",
      "Singleturn power down",
      "Multiturn position 1",
      "Multiturn position 2",
      "Multiturn system",
      "Multiturn power down",
      "Multiturn overflow/underflow"
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F31135 Encoder 1: Fault when determining the position (single turn)
Reaction: ENCODER
Acknowledge: PULSE INHIBIT
522 Operating Instructions, 01/2019, A5E41702836B AC
Cause: The encoder has identified a position determination fault (singleturn) and supplies status information bit by bit in an internal
status/fault word.
Some of these bits cause this fault to be triggered. Other bits are status displays. The status/fault word is displayed in the
fault value.
Note regarding the bit designation:
The first designation is valid for DRIVE-CLiQ encoders, the second for EnDat 2.2 encoders.
Fault value (r0949, interpret binary):
Bit 0: F1 (safety status display).
Bit 1: F2 (safety status display).
Bit 2: Reserved (lighting).
Bit 3: Reserved (signal amplitude).
Bit 4: Reserved (position value).
Bit 5: Reserved (overvoltage).
Bit 6: Reserved (undervoltage)/hardware fault EnDat supply (--> F3x110, x = 1, 2, 3).
Bit 7: Reserved (overcurrent)/EnDat encoder withdrawn when not in the parked state (--> F3x110, x = 1, 2, 3).
Bit 8: Reserved (battery)/overcurrent EnDat supply (--> F3x110, x = 1, 2, 3).
Bit 9: Reserved/overvoltage EnDat supply (--> F3x110, x = 1, 2, 3).
Bit 11: Reserved/internal communication error (--> F3x110, x = 1, 2, 3).
Bit 12: Reserved/internal communication error (--> F3x110, x = 1, 2, 3).
Bit 13: Reserved/internal communication error (--> F3x110, x = 1, 2, 3).
Bit 14: Reserved/internal communication error (--> F3x110, x = 1, 2, 3).
Bit 15: Internal communication error (--> F3x110, x = 1, 2, 3).
Bit 16: Lighting (--> F3x135, x = 1, 2, 3).
Bit 17: Signal amplitude (--> F3x135, x = 1, 2, 3).
Bit 18: Singleturn position 1 (--> F3x135, x = 1, 2, 3).
Bit 19: Overvoltage (--> F3x135, x = 1, 2, 3).
Bit 20: Undervoltage (--> F3x135, x = 1, 2, 3).
Bit 21: Overcurrent (--> F3x135, x = 1, 2, 3).
Bit 22: Temperature exceeded (--> F3x405, x = 1, 2, 3).
Bit 23: Singleturn position 2 (safety status display).
Bit 24: Singleturn system (--> F3x135, x = 1, 2, 3).
Bit 25: Singleturn power down (--> F3x135, x = 1, 2, 3)
Bit 26: Multiturn position 1 (--> F3x136, x = 1, 2, 3).
Bit 27: Multiturn position 2 (--> F3x136, x = 1, 2, 3).
Bit 28: Multiturn system (--> F3x136, x = 1, 2, 3).
Bit 29: Multiturn power down (--> F3x136, x = 1, 2, 3).
Bit 30: Multiturn overflow/underflow (--> F3x136, x = 1, 2, 3).
Bit 31: Multiturn battery (reserved).
Remedy: - determine the detailed cause of the fault using the fault value.
- replace the encoder if necessary.
Note:
An EnDat 2.2 encoder may only be removed and inserted in the "Park" state.
If an EnDat 2.2 encoder was removed when not in the "Park" state, then after inserting the encoder, a POWER ON (switch-
off/switch-on) is necessary to acknowledge the fault.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 26. SIEMENS_S210_2019_F31804

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "9d3c68d4-f567-4a63-a1c5-a35ccb5d8f41",
    "fault_code": "F31804",
    "component": "Encoder 1",
    "related_components": [],
    "description": "Sensor Module checksum error",
    "causes": [
      "A checksum error has occurred when reading-out the program memory on the Sensor Module."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F31804 Encoder 1: Sensor Module checksum error
Reaction: ENCODER
Acknowledge: POWER ON
Cause: A checksum error has occurred when reading-out the program memory on the Sensor Module.
Fault value (r0949, interpret hexadecimal):
yyyyxxxx hex
yyyy: Memory area involved.
xxxx: Difference between the checksum at POWER ON and the actual checksum.
Remedy: - carry out a POWER ON (switch-off/switch-on).
- upgrade firmware to later version (>= V2.6 HF3, >= V4.3 SP2, >= V4.4).
- check whether the permissible ambient temperature for the component is maintained.
- replace the Sensor Module.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 27. SIEMENS_S210_2019_F31850

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "c1828d48-182c-416c-93b5-0cba8da20c15",
    "fault_code": "F31850",
    "component": "Control system (internal software)",
    "related_components": [],
    "description": "Encoder evaluation internal software error",
    "causes": [
      "An internal software error has occurred in the Sensor Module of encoder 1.",
      "Background time slice is blocked.",
      "Checksum over the code memory is not OK.",
      "OEM memory of the EnDat encoder contains data that cannot be interpreted.",
      "Descriptive data from EEPROM incorrect.",
      "Calibration data from EEPROM incorrect.",
      "Configuration data from EEPROM incorrect.",
      "communication with analog/digital converter faulted.",
      "DRIVE-CLiQ encoder initialization application error.",
      "DRIVE-CLiQ encoder initialization ALU error.",
      "DRIVE-CLiQ encoder HISI / SISI initialization error.",
      "DRIVE-CLiQ encoder safety initialization error.",
      "DRIVE-CLiQ encoder internal system error."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F31850 Encoder 1: Encoder evaluation internal software error
Reaction: ENCODER
Acknowledge: POWER ON
532 Operating Instructions, 01/2019, A5E41702836B AC
Cause: An internal software error has occurred in the Sensor Module of encoder 1.
Fault value (r0949, interpret decimal):
1: Background time slice is blocked.
2: Checksum over the code memory is not OK.
10000: OEM memory of the EnDat encoder contains data that cannot be interpreted.
11000 ... 11499: Descriptive data from EEPROM incorrect.
11500 ... 11899: Calibration data from EEPROM incorrect.
11900 ... 11999: Configuration data from EEPROM incorrect.
12000 ... 12008: communication with analog/digital converter faulted.
16000: DRIVE-CLiQ encoder initialization application error.
16001: DRIVE-CLiQ encoder initialization ALU error.
16002: DRIVE-CLiQ encoder HISI / SISI initialization error.
16003: DRIVE-CLiQ encoder safety initialization error.
16004: DRIVE-CLiQ encoder internal system error.
Remedy: - replace the Sensor Module.
- if required, upgrade the firmware in the Sensor Module.
- contact Technical Support.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 28. SIEMENS_S210_2019_F31950

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "b9d0f961-b517-44de-8ed0-22eb7d31babb",
    "fault_code": "F31950",
    "component": "Control system (internal software)",
    "related_components": [],
    "description": "Internal software error",
    "causes": [
      "An internal software error has occurred."
    ],
    "parameters": [
      "r0949"
    ]
  }
]
```

### 原文

```text
F31950 Encoder 1: Internal software error
Reaction: ENCODER
Acknowledge: POWER ON
536 Operating Instructions, 01/2019, A5E41702836B AC
Cause: An internal software error has occurred.
Fault value (r0949, interpret decimal):
The fault value contains information regarding the fault source.
Only for internal Siemens troubleshooting.
Remedy: - if necessary, upgrade the firmware in the Sensor Module to a later version.
- contact Technical Support.
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 29. SIEMENS_S210_2019_N01620

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "d0a55dac-273a-4deb-aa51-9ce05f5552df",
    "fault_code": "N01620",
    "component": "Safety Integrated",
    "related_components": [],
    "description": "Safe Torque Off active",
    "causes": [
      "The 'Safe Torque Off' (STO) function of the basic functions has been selected in monitoring channel 1 using the input terminal and is active."
    ],
    "parameters": []
  }
]
```

### 原文

```text
N01620 SI P1: Safe Torque Off active
Reaction: NONE
Acknowledge: NONE
Cause: The "Safe Torque Off" (STO) function of the basic functions has been selected in monitoring channel 1 using the input
terminal and is active.
Note:
- this message does not result in a safety stop response.
- this message is not output when STO is selected using the Extended Functions.
Remedy: Not necessary.
Note:
SI: Safety Integrated
STO: Safe Torque Off
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---

## 30. SIEMENS_S210_2019_N30621

- 模型状态：success
- 模型记录数：1

### 模型抽取结果

```json
[
  {
    "record_id": "08dd6a9f-25d1-4016-86c5-98aa7d2885fa",
    "fault_code": "N30621",
    "component": "Safety Integrated",
    "related_components": [],
    "description": "Safe Stop 1 active",
    "causes": [
      "The 'Safe Stop 1' function (SS1) was selected in monitoring channel 2 and is active."
    ],
    "parameters": []
  }
]
```

### 原文

```text
N30621 SI P2: Safe Stop 1 active
Reaction: NONE
Acknowledge: NONE
Cause: The "Safe Stop 1" function (SS1) was selected in monitoring channel 2 and is active.
Note:
This message does not result in a safety stop response.
Remedy: Not necessary.
Note:
SI: Safety Integrated
SS1: Safe Stop 1
```

### 专家审核

审核结论：待填写（审核通过 / 证据不足 / 语义需修改 / 无法判断）

审核意见：

---
