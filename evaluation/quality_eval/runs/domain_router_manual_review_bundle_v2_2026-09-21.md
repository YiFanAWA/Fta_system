# Domain Router / Query Sufficiency 完整人工审核材料包 v1

状态：`awaiting_human_review`；不是 Gold；不会自动修改 Router 或 Retrieval。

## 一、审核范围

这不是片段式提问，而是把当前所有需要人工确认的材料集中到一份包中：

- 注册表中全部领域信号：已确认词、待确认词、正向原文证据；
- 全部 79 条混合域查询：领域、相关实体、Router 决策、充分性机器判断和人工空白栏；
- 重点 22 条 `cross_domain` 查询：要求人工决定应 scope、保持跨域还是先澄清；
- 澄清问题与 Router v2 放行结论。

## 二、材料来源与限制

| 材料 | 用途 | 限制 |
|---|---|---|
| `siemens_s210_public_fault_gold_candidate` | `evaluation\quality_eval\datasets\siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json` | AI-assisted review; explicitly not equivalent to a human domain expert review. |
| `faa_sdr_2024_public_sample` | `evaluation\quality_eval\datasets\aerospace_faa_sdr_public_sample_v1_2026-09-21.json` | Adapter-development sample; not an expert Gold set. |
| `mixed_domain_router_comparison` | `evaluation\quality_eval\runs\mixed_domain_router_comparison_v1_2026-09-21.json` | Router and retrieval diagnostic; not a human label source. |

正向出现证据只能证明该词在领域材料中出现，不能单独证明它对其他领域具有唯一性；“是否可以缩小 scope”仍必须由专家确认。

## 三、全部领域信号确认

| Scope | 组别 | 词 | 注册状态 | 原文证据 | 专家判断 | Router 角色 | 备注 |
|---|---|---|---|---|---|---|---|
| siemens_s210 | high_signal | `siemens` | confirmed | ked. It is recommended that the parameterization is downloaded again. dd, cc, bb: Only for internal Siemens troubleshooting. See also: p0977 (Save all parameters) Remedy: - download the project again using the commissioning tool. - save all parameters (p0977 = 1 or "copy RAM to ROM"). S |  |  |  |
| siemens_s210 | high_signal | `sinamics` | confirmed | e "write protected" attribute has been set for the files in the non-volatile memory under .../USER/ SINAMICS/DATA/... When required, remove write protection and save again (e.g. set p0977 to 1). |  |  |  |
| siemens_s210 | high_signal | `s210` | confirmed | 未在当前样本中找到直接出现证据 |  |  |  |
| siemens_s210 | high_signal | `drive-cliq` | confirmed | A01006 Firmware update for DRIVE-CLiQ component required Reaction: NONE Acknowledge: NONE Cause: The firmware of a DRIVE-CLiQ component must be updated as there is no suitable firmware or firmware version in the compo |  |  |  |
| siemens_s210 | high_signal | `profinet` | confirmed |  Ti and To unsuitable for PN cycle Reaction: NONE Acknowledge: NONE Cause: The configured times for PROFINET communication are not permitted and the PN cycle is used as the actual value acquisition cycle for the safe movement monitoring functions: Isochronous PROFINET: The sum of Ti and  |  |  |  |
| siemens_s210 | high_signal | `profisafe` | confirmed | A01654 SI P1: Deviating PROFIsafe configuration Reaction: NONE Acknowledge: NONE Cause: The configuration of a PROFIsafe telegram in the higher-level control (F-PLC) does not match the parameterization in the driv |  |  |  |
| siemens_s210 | high_signal | `STO` | pending_manual_confirmation |  - this message does not result in a safety stop response. - in the safety commissioning mode, the "STO" function is internally selected. See also: p0010 (Drive commissioning parameter filter 2) Remedy: Not necessary. This message is automatically withdrawn after the safety function |  |  |  |
| siemens_s210 | high_signal | `SI Motion` | pending_manual_confirmation | A01691 SI Motion: Ti and To unsuitable for PN cycle Reaction: NONE Acknowledge: NONE Cause: The configured times for PROFINET communication are not permitted and the PN cycle is used as the actual |  |  |  |
| siemens_s210 | high_signal | `CU` | pending_manual_confirmation | A01009 CU: Control module overtemperature Reaction: NONE Acknowledge: NONE Cause: The temperature (r0037[0]) of the control module (Control Unit) has exceeded the specified limit value. Rem |  |  |  |
| siemens_s210 | high_signal | `Sensor module` | pending_manual_confirmation | A01695 SI Motion: Sensor Module was replaced Reaction: NONE Acknowledge: NONE Cause: A Sensor Module, which is used for safe motion monitoring functions, was replaced. The hardware replacement must be acknowledg |  |  |  |
| siemens_s210 | medium_signal | `drive` | pending_manual_confirmation | A01006 Firmware update for DRIVE-CLiQ component required Reaction: NONE Acknowledge: NONE Cause: The firmware of a DRIVE-CLiQ component must be updated as there is no suitable firmware or firmware version in the  |  |  |  |
| siemens_s210 | medium_signal | `servo` | pending_manual_confirmation |  no clock synchronization or clock synchronous sign of life and DSC is selected. Note: DSC: Dynamic Servo Control See also: r0922 (PROFIdrive PZD telegram selection) Remedy: Set clock synchronization across the bus configuration and transfer clock synchronous sign-of-life. |  |  |  |
| faa_sdr | high_signal | `航空器` | confirmed | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `航空` | confirmed | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `faa` | confirmed | TACH LUGS. ACCOMPLISHED TEXTRON AVIATION FIELD REPAIR FR-680-0149-12564 REV A DATED 25 OCT 2023 AND FAA FORM 8100-9 DATED 25 OCT 2023; FIELD REPAIR - CORROSION, RH MLG, TRUNNION, TRAILING LINK ATTACH LUGS. |  |  |  |
| faa_sdr | high_signal | `jasc` | confirmed | OperatorControlNumber: DALA2024010200007 JASCCode: 3350 AircraftMake: AIRBUS AircraftModel: A320211 PartName: UNKNOWN PartNumber: UNKNOWN PartCondition: UNKNOWN Discrepancy: SHIP 3229 DISC: FOUND BROKEN GROUND WIRE FOR EMERGENCY  |  |  |  |
| faa_sdr | high_signal | `sdr` | confirmed | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `飞机` | confirmed | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `ATA` | pending_manual_confirmation | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `LRU` | pending_manual_confirmation | 未在当前样本中找到直接出现证据 |  |  |  |
| faa_sdr | high_signal | `flight` | pending_manual_confirmation | URNING RUBBER SMELL AROUND SEATS 20-22. SMELL STARTED IN CLIMB. CONTINUED ON AND OFF THROUGHOUT THE FLIGHT. NO FLIGHT DECK SMELL. C/A: C/W ODI WORK CARD 0550-2002 UP TO STEP 3. ALSO, C/W FIG 3 ( ELECTRICAL, SMOKE/ODOR IN THE MID CABIN- TYPE 9 MISC). ODI CONF CALL W/ MCC COMPLETED. (BV8 |  |  |  |
| faa_sdr | high_signal | `aircraft` | pending_manual_confirmation |  PartCondition: DISCONNECTED ComponentName: SHUTOFF VALVE ComponentPartNumber: UNKNOWN Discrepancy: AIRCRAFT ARRIVED ON LFBF AIRPORT ON 20 DEC 2023 FROM UNITED STATES.  THE LEADING EDGE STANDBY SHUTOFF VALVE WAS FOUND DISCONNECTED AT THE ARRIVAL OF THE AIRCRAFT (ELECTRICAL CONNECTOR DISC |  |  |  |

专家填写：
- 判断：`是 / 条件是 / 否 / 无法判断`；
- Router 角色：`high_signal / medium_signal / 不加入`；
- 必须说明是否需要与厂商、系统或故障码联合出现。

## 四、22 条 cross-domain 重点确认

| Query | 查询 | 机器领域标签 | 机器充分性 | 相关实体/故障 | 材料记录 | 人工领域结论 | 人工充分性 | 最终动作 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| S210-FT007 | CU 温度超过允许上限时会出现哪条报警？ | A_missing_router_signal | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01009 | SIEMENS_S210_2019_A01009 |  |  |  |
| S210-FT008 | 向可移动存储介质写数据失败，应该查哪条报警？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01019 | SIEMENS_S210_2019_A01019 |  |  |  |
| S210-FT009 | 驱动器内部 RAM 磁盘无法写入对应什么报警？ | B_domain_ambiguous | insufficient (0.28) | industrial-drive:siemens:s210:A01020 | SIEMENS_S210_2019_A01020 |  |  |  |
| S210-FT010 | 启动时发现参数备份文件不完整，会报告什么故障？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01035 | SIEMENS_S210_2019_A01035 |  |  |  |
| S210-FT011 | 控制单元程序存储区发生 CRC 校验错误时是什么故障？ | C_query_insufficient | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01064 | SIEMENS_S210_2019_A01064 |  |  |  |
| S210-FT013 | 交流变频器散热器过热会触发哪些报警？ | C_query_insufficient | partially_sufficient (0.52) | industrial-drive:siemens:s210:A05000 | SIEMENS_S210_2019_A05000 |  |  |  |
| S210-FT014 | 24/48 V 供电电压低于下限时会产生什么报警？ | B_domain_ambiguous | insufficient (0.28) | industrial-drive:siemens:s210:A30041 | SIEMENS_S210_2019_A30041 |  |  |  |
| S210-FT015 | 用于安全运动监控的编码器报告硬件故障，对应哪条报警？ | C_query_insufficient | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01750 | SIEMENS_S210_2019_A01750 |  |  |  |
| S210-FT016 | 存储卡中的参数备份和当前驱动不匹配，可能是什么原因？ | C_query_insufficient | insufficient (0.1) | industrial-drive:siemens:s210:A01069 | SIEMENS_S210_2019_A01069 |  |  |  |
| S210-FT017 | 安全集成功能已经参数化并启用，但没有有效安全密码，会出现什么报警？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01637 | SIEMENS_S210_2019_A01637 |  |  |  |
| S210-FT019 | 安全参数被改动后要求暖启动或重新上电，这是哪个报警的触发场景？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01693 | SIEMENS_S210_2019_A01693 |  |  |  |
| S210-FT020 | 开始制动测试时制动器没有打开，会对应什么报警？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01780 | SIEMENS_S210_2019_A01780 |  |  |  |
| S210-FT021 | 制动测试中打开制动器超过 11 秒仍未完成，是什么报警？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A01781 | SIEMENS_S210_2019_A01781 |  |  |  |
| S210-FT022 | 电机输出相序接错会造成哪种换向角错误？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:F07412 | SIEMENS_S210_2019_F07412 |  |  |  |
| S210-FT023 | 电机回馈能量过大时会导致哪种直流母线问题？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:F30002 | SIEMENS_S210_2019_F30002 |  |  |  |
| S210-FT027 | 安全运动监控使用的 Sensor Module 更换后，需要关注什么报警？ | A_missing_router_signal | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01695 | SIEMENS_S210_2019_A01695 |  |  |  |
| S210-FT029 | 功率单元的 I2t 过载报警是哪一条？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:A07805 | SIEMENS_S210_2019_A07805 |  |  |  |
| S210-FT030 | PN 组件的周期连接中断对应什么故障？ | C_query_insufficient | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01980 | SIEMENS_S210_2019_A01980 |  |  |  |
| S210-FT031 | SI Motion 中安全编码器的硬件故障是什么报警？ | A_missing_router_signal | partially_sufficient (0.52) | industrial-drive:siemens:s210:A01750 | SIEMENS_S210_2019_A01750 |  |  |  |
| S210-FT032 | Drive 侧电机换向角不正确对应哪些故障码？ | C_query_insufficient | partially_sufficient (0.52) | industrial-drive:siemens:s210:F07412 | SIEMENS_S210_2019_F07412 |  |  |  |
| S210-FT038 | 故障值中的 cross-compared data number 指向哪些监控通道故障？ | C_query_insufficient | insufficient (0.28) | industrial-drive:siemens:s210:F01611, industrial-drive:siemens:s210:F30611 | SIEMENS_S210_2019_F01611, SIEMENS_S210_2019_F30611 |  |  |  |
| S210-FT039 | 只知道驱动报告 STO 或监控通道问题，哪些安全故障需要一起排查？ | A_missing_router_signal | insufficient (0.28) | industrial-drive:siemens:s210:F01600, industrial-drive:siemens:s210:F01611, industrial-drive:siemens:s210:F30600, industrial-drive:siemens:s210:F30611 | SIEMENS_S210_2019_F01600, SIEMENS_S210_2019_F01611, SIEMENS_S210_2019_F30600, SIEMENS_S210_2019_F30611 |  |  |  |

人工领域结论：`industrial_drive / aerospace / both_or_ambiguous / cannot_determine`。
人工充分性：`sufficient / partially_sufficient / insufficient / cannot_determine`。
最终动作：`scope_industrial_drive / scope_aerospace / cross_domain / clarify_first`。

## 五、全部 79 条查询充分性确认

以下不是只列异常项，而是完整保留所有查询，供专家确认机器充分性判断是否合理。

| Query | 查询 | 基准领域 | Router 模式 | 机器充分性 | 分数 | 是否澄清 | 人工充分性 | 最终动作 | 备注 |
|---|---|---|---|---|---:|---|---|---|---|
| S210-FT001 | 请给出 A01009 的故障定义。 | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT002 | 故障码 F01001 的含义是什么？ | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT003 | A01637 对应哪一种安全报警？ | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT004 | 查询 PN 故障码 A01900。 | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT005 | A30054 是什么类型的电源报警？ | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT006 | F01023 的故障现象和含义是什么？ | industrial_drive | scoped | sufficient | 0.99 | False |  |  |  |
| S210-FT007 | CU 温度超过允许上限时会出现哪条报警？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT008 | 向可移动存储介质写数据失败，应该查哪条报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT009 | 驱动器内部 RAM 磁盘无法写入对应什么报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT010 | 启动时发现参数备份文件不完整，会报告什么故障？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT011 | 控制单元程序存储区发生 CRC 校验错误时是什么故障？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT012 | PROFINET 控制器的周期连接断开后对应哪条报警？ | industrial_drive | scoped | insufficient | 0.28 | True |  |  |  |
| S210-FT013 | 交流变频器散热器过热会触发哪些报警？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT014 | 24/48 V 供电电压低于下限时会产生什么报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT015 | 用于安全运动监控的编码器报告硬件故障，对应哪条报警？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT016 | 存储卡中的参数备份和当前驱动不匹配，可能是什么原因？ | industrial_drive | cross_domain | insufficient | 0.1 | True |  |  |  |
| S210-FT017 | 安全集成功能已经参数化并启用，但没有有效安全密码，会出现什么报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT018 | 上位 F-PLC 的 PROFIsafe 配置和驱动侧参数化不一致，会触发哪条报警？ | industrial_drive | scoped | insufficient | 0.28 | True |  |  |  |
| S210-FT019 | 安全参数被改动后要求暖启动或重新上电，这是哪个报警的触发场景？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT020 | 开始制动测试时制动器没有打开，会对应什么报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT021 | 制动测试中打开制动器超过 11 秒仍未完成，是什么报警？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT022 | 电机输出相序接错会造成哪种换向角错误？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT023 | 电机回馈能量过大时会导致哪种直流母线问题？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT024 | 调整 p3109 的 UTC 同步容差后，应查看哪条报警？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT025 | 排查 p9559 设置并执行安全运动监控测试停止，针对哪个报警？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT026 | 处理 STO 测试停止超时并检查 p9659，应该定位哪条报警？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT027 | 安全运动监控使用的 Sensor Module 更换后，需要关注什么报警？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT028 | 修改 p9930 仍不能写入内部 RAM 盘时，应该复核哪个故障？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT029 | 功率单元的 I2t 过载报警是哪一条？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT030 | PN 组件的周期连接中断对应什么故障？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT031 | SI Motion 中安全编码器的硬件故障是什么报警？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT032 | Drive 侧电机换向角不正确对应哪些故障码？ | industrial_drive | cross_domain | partially_sufficient | 0.52 | False |  |  |  |
| S210-FT033 | r9767 是哪条安全密码报警的关联参数？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT034 | p0294 用于哪个功率单元过载报警的诊断？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT035 | 配置电报错误可能涉及 p8969，这对应哪条故障？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT036 | r8936 与哪条 PROFINET 周期连接报警有关？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT037 | p10202 涉及哪些制动测试报警？ | industrial_drive | scoped | partially_sufficient | 0.82 | False |  |  |  |
| S210-FT038 | 故障值中的 cross-compared data number 指向哪些监控通道故障？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| S210-FT039 | 只知道驱动报告 STO 或监控通道问题，哪些安全故障需要一起排查？ | industrial_drive | cross_domain | insufficient | 0.28 | True |  |  |  |
| AERO-Q001 | JASC 2100 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q002 | JASC 2120 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q003 | JASC 2421 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q004 | JASC 2435 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q005 | JASC 2565 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q006 | JASC 2612 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q007 | JASC 2697 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q008 | JASC 2740 对应哪些航空故障报告？ | aerospace | scoped | sufficient | 0.95 | False |  |  |  |
| AERO-Q009 | 航空维修记录中涉及部件号 L856M3001881 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q010 | 航空维修记录中涉及部件号 356200575 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q011 | 航空维修记录中涉及部件号 23085029 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q012 | 航空维修记录中涉及部件号 G4710A19 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q013 | 航空维修记录中涉及部件号 310A204110 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q014 | 航空维修记录中涉及部件号 SL36006WA20P 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q015 | 航空维修记录中涉及部件号 03018200 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q016 | 航空维修记录中涉及部件号 64404303416 的是哪条记录？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q017 | 哪条航空故障记录涉及 LIGHT？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q018 | 哪条航空故障记录涉及 SHUTOFF VALVE？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q019 | 哪条航空故障记录涉及 FIRE LOOP CABLE？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q020 | 哪条航空故障记录涉及 STARTER GEN？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q021 | 哪条航空故障记录涉及 TAXI LIGHT？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q022 | 哪条航空故障记录涉及 THRUST LINK？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q023 | 哪条航空故障记录涉及 ENGINE CYLINDER？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q024 | 哪条航空故障记录涉及 CYLINDER？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q025 | 航空部件状态为 LOOSE 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q026 | 航空部件状态为 DISCONNECTED 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q027 | 航空部件状态为 CHAFED 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q028 | 航空部件状态为 FAILED 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q029 | 航空部件状态为 FAILED 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q030 | 航空部件状态为 MAKING METAL 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q031 | 航空部件状态为 BROKEN 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q032 | 航空部件状态为 FAILED 的故障记录是哪条？ | aerospace | scoped | partially_sufficient | 0.72 | False |  |  |  |
| AERO-Q033 | 哪条航空维修报告包含处置记录：REPAIRED WIRE AND OPS CHECKED THE CABIN MERGENCY PATHWAY LIGHTS IAW A320？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q034 | 哪条航空维修报告包含处置记录：REF. LOG 0134554 FOR 2L SLIDE REPLACEMENT, REMOVAL, REMOVED 2L DAMPER PER？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q035 | 哪条航空维修报告包含处置记录：PERFORMED ER/A 614433-14AD REV: ORIGINAL AS PER PRI REV 0 OF ER/？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q036 | 哪条航空维修报告包含处置记录：C/W ODI WORK CARD 0550-2002 UP TO STEP 3. ALSO, C/W FIG？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q037 | 哪条航空维修报告包含处置记录：OPS CKD AFT LEFT PASSENGER DOOR SLIDE ARM PER A320 AMM 52-73,？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q038 | 哪条航空维修报告包含处置记录：PERFORMED REPAIR IN HOLE #4, LOCATED ON INBOARD LOWER POSITION, DOOR STOP？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q039 | 哪条航空维修报告包含处置记录：REVISE AND UPDATE ERA 550224-14AD WITH DTE RESULTS PRIOR TO 101,081 TOTAL？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |
| AERO-Q040 | 哪条航空维修报告包含处置记录：ACCOMPLISH INSPECTIONS PER ERA 550225-14AD SECTION IV PRIOR TO 47,581 TOTAL FLIGHT？ | aerospace | scoped | insufficient | 0.1 | True |  |  |  |

## 六、系统澄清行为确认

请专家确认下列问题是否足够、是否需要增删：

1. 请补充设备型号、系统名称或厂商。
2. 如果有，请提供完整故障码、报警码或参数号。
3. 请说明涉及的组件、模块或部件。
4. 请补充故障现象、触发条件或报警值。
5. 如果信息仍不足，是否允许返回多个候选故障，而不是强行给出唯一答案？

专家结论：____________________________________________________________

## 七、最终签字结论

- [ ] A 类领域词已完成审核；
- [ ] 全部 22 条 cross-domain 查询已完成审核；
- [ ] 全部查询充分性已完成审核；
- [ ] 可以形成 `query_sufficiency_gold_v1`；
- [ ] 允许生成 Router v2；
- [ ] 暂不允许 Router v2，继续使用 Router v1。

审核人：____________________    日期：____________________

## 版本边界

本材料包不把 AI 辅助审核、公开样本或机器诊断直接升级为真人专家金标。专家填写后应生成新的版本化审核结果，不覆盖本材料包。
