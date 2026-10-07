# S210 候选 FTA 重复证据定位确认单 v1

日期：2026-09-27  
用途：把 v3 候选树中无法唯一绑定的短语及其所有原文位置交给审核者定位。  
状态：3 个节点经用户授权的 AI 审核角色定位、主代理按原文回切核实；1 个节点因候选命题丢失否定语义仍为 `pending_semantic_review`。该状态不是真人专家签署或 Gold；没有修改原候选树、Gold 或数据库。

## 定位规则

同一句或短语在原文出现多次时，不由生成器或本确认单自动挑选。审核者需结合该节点的来源原因、所在章节/作用域和完整上下文，确认哪个原文跨度支持该节点；若没有唯一、直接支持的跨度，保留待处理，不绑定证据。下表中的每个 offset 均为原始 `input_text` 的半开区间 `[start,end)`，仅代表候选位置。

## 待定位节点

### F01681 — `SIEMENS_S210_2019_F01681`

来源 artifact：[F01681 v3 候选 Preview](siemens_s210_2019_f01681_candidate_fta_preview_prompt_guard_v3_2026-09-27.json)  
输入文本 SHA-256：`5517c4e678dfa57286a7ae5426e4d40ed7322a4c88241593b6a55d068f0e994b`

| 候选树节点 | 来源 cause index | 待定位短语 | 原文候选位置与上下文 | 审核者确认的 `[start,end)` |
|---|---:|---|---|---|
| `cause:f381f779-cfa2-48eb-88ef-e1a2a6813243:n6_cond_a` | 6 | `motion monitoring functions integrated in the drive (p9601.2 = 1)` | `[841,906)`：位于 Cause 故障值 `xxxx = 9601 and yyyy = 1` 的说明中；`[3102,3167)`：位于 Remedy 配置指引 `Only enable ...` 中。 | `[841,906)`（AI 角色定位；主代理回切核实） |
| `cause:f381f779-cfa2-48eb-88ef-e1a2a6813243:n6_cons_a` | 6 | `PROFIsafe (p9601.3 = 1)` | `[980,1003)`：位于 Cause 的 `...then PROFIsafe ... or onboard F-DI ... is not possible` 中；`[3172,3195)`：位于 Remedy 配置指引中。 | 暂不绑定：该短语本身丢失原句否定结果语义，需先修正候选命题 |

审核结论（每行填写）：`cause_scope / remedy_only / neither / unable_to_determine`。只有确认直接支持当前节点语义的 Cause 证据后，才可写入确认 offset；不得仅因相同字符串可定位就自动认定因果关系成立。

### F30027 — `SIEMENS_S210_2019_F30027`

来源 artifact：[F30027 v3 候选 Preview](siemens_s210_2019_f30027_candidate_fta_preview_prompt_guard_v3_2026-09-27.json)  
输入文本 SHA-256：`fc4d7593653aca73af9c1d8b57bd515b2ed8ff27d9295d1cd75b5232590a00c7`

| 候选树节点 | 来源 cause index | 待定位短语 | 原文候选位置与上下文 | 审核者确认的 `[start,end)` |
|---|---:|---|---|---|
| `cause:cdde4645-6fbf-412d-a78f-44f2df8b4be4:cause9_ground_fault` | 9 | `ground fault` | `[937,949)`：Cause 第9项 `The DC link has either a ground fault or a short-circuit.`；`[3371,3383)`：Remedy 的 `For 9): check the DC link for ground faults ...`。 | `[937,949)`（AI 角色定位；主代理回切核实） |
| `cause:cdde4645-6fbf-412d-a78f-44f2df8b4be4:cause9_short_circuit` | 9 | `short-circuit` | `[955,968)`：Cause 第9项；`[2445,2458)`：故障值位说明 `Armature short-circuit active`；`[2571,2584)`：故障值位说明 `...overcurrent/short-circuit`。 | `[955,968)`（AI 角色定位；主代理回切核实） |

审核结论（每行填写）：`cause_scope / fault_value_explanation / remedy_only / neither / unable_to_determine`。即使 Cause 第9项范围看似最相关，当前策略仍要求由审核者明确确认，不在生成阶段静默选位。

## AI 审核角色定位结论（2026-09-27，追加记录）

审核方式：用户授权的 AI 专家角色独立审查；主代理随后按语料原文和 `[start,end)` 切片复核。它不是 Siemens 真人专家签署，也不是正式 Gold。

| 节点 | AI 角色审核结论 | 主代理回切核验 | 可绑定位置 | 限定含义 |
|---|---|---|---|---|
| F01681 `cause:f381f779-cfa2-48eb-88ef-e1a2a6813243:n6_cond_a` | Cause 故障值1条件；排除 Remedy 中重复短语 | 精确匹配 | `[841,906)` | 只证明手册描述了该条件，不证明本次设备实例中该参数状态已发生，也不建立顶事件因果边 |
| F01681 `cause:f381f779-cfa2-48eb-88ef-e1a2a6813243:n6_cons_a` | 暂不绑定：当前节点文本 `PROFIsafe (p9601.3 = 1)` 丢失原句的否定和结果含义 `...is not possible` | `[980,1003)` 虽精确落在 Cause 句内，但不足以支持当前节点语义；`[3172,3195)` 属 Remedy | **仍 pending** | 先修复节点命题/角色并复核，不得把正向参数短语当作原文结论 |
| F30027 `cause:cdde4645-6fbf-412d-a78f-44f2df8b4be4:cause9_ground_fault` | Cause 第9项；排除 Remedy 的检查动作 | 精确匹配 | `[937,949)` | 支持手册列出的候选故障模式，不证明实例中确实发生接地故障 |
| F30027 `cause:cdde4645-6fbf-412d-a78f-44f2df8b4be4:cause9_short_circuit` | Cause 第9项；排除故障值位说明中的重复术语 | 精确匹配 | `[955,968)` | 支持手册列出的候选故障模式；`either … or` 不在本定位审核中批准为正式逻辑门，也不确定实例的具体模式 |

因此，原确认单中3个位置问题已由 AI 角色审核处理并经原文回切核验；剩余的 F01681 `n6_cons_a` 是**语义表达/结构问题**，不是再挑另一个重复 offset 就能解决。确认单不修改 v3 artifact；需要新 Preview 才能反映节点修正，且现场映射仍需实例参数读数。

## 提示修订后的 F01681 v4 回归

用户确认应保留完整否定结果命题后，已在新提示下生成 [F01681 polarity guard v4 Preview](siemens_s210_2019_f01681_candidate_fta_preview_polarity_guard_v4_2026-09-27.json)。v4 将 Cause index 6 保留为单一完整命题节点，证据 `[838,1050)` 精确覆盖“若两项功能启用，则 PROFIsafe 或 onboard F-DI 不可用”；没有把两个功能选项拆成正向原因叶节点。旧 v3 不修改、不覆盖，旧 `n6_cons_a` 仍保持不绑定。

v4 的独立 AI 角色复核已完成：确认 Cause index 6 完整保留否定命题、没有生成正向 PROFIsafe/onboard F-DI 叶项、引文精确且树仍阻断；同时指出 unknown 门诊断理由可能被误读成 AND 已确认。为修复该表达风险，v5 artifact 已将模型理由标为未接受提议。v5 的独立 AI 角色复核也已完成，确认标签、引文和生产门禁一致；另提醒 Cause index 8 的正向 `Onboard F-DI are enabled` 是父级 “without enabling motion monitoring” 条件组内的局部候选，不应脱离其未知门 scope 单独解释为根因。v5 整树仍为 `blocked`，没有写入 Gold/数据库；两轮单样本输出仅证明本次表达符合预期，不代表模型普遍保证。

## F01681 另需的实例材料（不是手册证据定位）

当前语料是 2019 手册中的通用故障定义和故障值映射，不含某台设备发生 F01681 时的现场读数。若要把某个映射模式从诊断候选连到该实例的顶事件，需另提供可追溯的同一故障时刻材料：

1. 故障记录/时间戳及设备型号、固件版本；
2. 原始 `r0949` 故障值（不要只给人工解释后的文本）；
3. 按手册映射解出的 `xxxx/yyyy`，以及与该映射有关的参数/配置实际读回值（例如对应的 `p9501`、`p9601` 等）；
4. 数据来源（驱动诊断导出、PLC/调试记录或其他可核查来源）。

缺少这些实例读数时，故障值映射只能保留为条件性诊断候选，不能假定该模式在本次故障中发生；局部门型也继续保持 `unknown`。

## 审核记录（待填）

- 审核者/角色：待填
- 审核日期：待填
- 修正说明：待填
- 是否允许绑定任何候选位置：待填

本确认单本身不是专家签署、不是 Gold，也不授权写数据库、生成正式 FTA 或将 `fta_ready` / `production_ready` 改为 true。
