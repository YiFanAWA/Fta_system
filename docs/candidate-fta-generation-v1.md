# 证据约束候选 FTA（当前树输出合同 v6）

> 当前活动研究基线是 [manifest v51](../evaluation/quality_eval/fta_baseline_manifest_v51.json)；审核台账见[当前状态审计](current-state-audit.md)，执行计划见[可靠性计划](fta-validation-reliability-plan-v1.md)。2026-10-07 F30021当前cause-disposition v5真实来源单例已运行4个阶段请求、零重试；离线对账确认已有 C04 定位记录与原文唯一 Possible causes scope 相符，但未应用于原始运行，重复跨度仍为unresolved，顶事件引文非唯一、child集合不完整，整树blocked。该结果是开发样例工程审计，不是Gold、准确率或泛化证明；Gold、数据库、生产API、`fta_ready`和`production_ready`均未改变。v50为定位对账前快照，v49为该次运行前快照，下文较早运行摘要属于历史状态。

**Figure 7 单事件历史状态（manifest v42，2026-09-29）**：结构合同通过、10/10 引文位置有效，但语义尚未接受：S1 替代路径证据未绑定为 `logic_evidence`，重复事件身份及复合事件粒度仍待审。prompt v8 按完整语义判断隐含门型，不要求字面 `OR/AND`，但逻辑证据必须支持 child 间关系和同一 output；列表、共现或不连续拼接仍不足。SMOKE-001/002/003/004 已单次授权运行，零重试，门型分别为 OR/AND/unknown/unknown，结构有效且符合隔离的非 Gold 政策预期。SMOKE-005 也完成一次请求，零重试；模型没有把无关显示句中的 `or` 当故障逻辑，输出预期 `unknown`，但只生成一个 gate child，结构合同阻断，整体比较为 `requires_review`。五条证据位置共 22/22；只有前四条整体通过结构合同。五条均为合成定性观察，不是专家审核、准确率或泛化证据。v8 语义接受仍为 false。未改正式 Gold、数据库、生产 API 或 readiness；`fta_ready=false`、`production_ready=false`。没有后续在线请求授权，不会自动重试 SMOKE-005。

历史 manifest v42 是早期验证快照，v1–v43 均不再是活动基线；v15 是范围 readiness 报告所钉定的证据快照。已见门型案例只覆盖 fixture/合同/证据边界，不是统计意义的模型准确率验证；Figure 7 v6 已通过结构合同和引用位置校验，但语义未接受。逻辑门判断按完整语义而非运算符关键词：替代路径可支持 OR，共同必要条件可支持 AND；逻辑引文必须同时支持 child 间门关系及其通向同一 output。unknown 的合同不同：不提供逻辑引文，而需有允许的 `unknown_reason`；v2 离线比较器已覆盖此分支。仅共现、原因罗列、scope 外连接词或不连续拼接仍不够；事件身份及复合句歧义仍需人工审核。SMOKE-001/002/003/004 与隔离的非 Gold 政策预期相符；SMOKE-005 门型也与 unknown 预期相符、且忽略了无关词面 `or`，但因单子项 gate scope 被结构合同阻断，不能算整体通过。五条合成样例证据位置为 22/22，不能用于准确率结论。独立范围 readiness 评估见[报告 v1](../evaluation/quality_eval/runs/fta_scoped_readiness_assessment_v1_2026-09-28.json)，其两条 readiness 均为 `blocked`。候选树仍为离线评估结果，不改变 Gold、数据库、生产 API 或全局 readiness。

#### 2026-09-29：Event-scope prompt v8 离线候选

用户确认：部分原文不会直接写 `OR/AND`，门型需要基于语义理解判断。v8 在 v7 的证据绑定要求上明确区分“语义证据”和“关键词”：完整原文若分别说明多个独立路径都能通向同一 output，可提出 OR；若表达多个条件必须共同成立才发生同一 output，可提出 AND。此处不是枚举词面模板，例句只说明概念。`logic_evidence` 必须直接证明 child 命题、它们的替代/联合关系及共同 output；列表、共现、局部无关 `or`、跨段拼接都不能单独确门，歧义时保持 `unknown`。

本段记录 v37 准备阶段：新增 [prompt v8](../evaluation/quality_eval/event_scope_tree_prompt_v8.py)、六条非 Gold 回归及离线测试，并准备了 5 条语义 smoke 输入、隔离的预期标签和 one-shot runner。当时 runner 仅完成预检、尚无模型输出。随后 SMOKE-001 的单次运行与离线对照见当前状态段落；活动快照为 [manifest v38](../evaluation/quality_eval/fta_baseline_manifest_v38.json)。

状态（2026-09-28）：候选树输出合同当前为 v5。原因处置阶段已接入离线 Preview；`FaultRecord.causes` 原样保留，逐 source cause index 有语义角色/处置审计账。只有明确的 `fta_event_candidate` 会进入结构生成；诊断映射、故障值模式、后果、摘要、Remedy 等明确非树项仅留账、不建节点；`unresolved`、分类缺项、证据缺失/多处匹配以及树结构误映射都会阻断整棵候选树放行。每个最终为 `unknown` 的门另有且只有一个合同校验的 `unknown_reason_code`；次级 blocker 保留细节，自由文本 `decision_reason` 不用于推断主因。证据必须唯一回切原文，不自动猜位置。当前 Cause disposition prompt 为 v4：除区分诊断映射与自然语言原因外，还逐项比较候选命题与顶事件；仅释义/重述而不增加独立上游信息的文本按 `causal_summary + relation_only` 留账，语义不确定的按 `unresolved` 处理。F01681 v4 单样本在线开发复演的 16 条原因均留在树外并导致安全阻断；独立 AI 子智能体复核通过，但非真人专家签署。复演只有两次成功模型请求，不含结构或门型阶段，不构成语义准确率、Gold 或泛化证明。另对同一原文 Remedy `xxxx=9507` 做了只读范围复核：该项是处理指令，不自动补成 cause/FTA 事件；Cause/Fault value 与 Remedy 的范围差异仍使 cause-set completeness 未闭合。处置仍是 `ai_proposed`，不是真人专家结论或 Gold；未改正式 Gold、数据库、生产 API，`fta_ready=false`、`production_ready=false`。

历史状态（截至 2026-09-27；下述早期数字、树覆盖约束和运行快照按其时间点解释）：递归候选 Preview 合同与离线编排已实现并通过后端回归；事件级审核 v8 对39条候选全部给出范围处置（37 reviewed、2 `not_applicable`、0 pending），门标签 AND 0、OR 1、unknown 36。当前门节点审核集为 v6：55个节点、55 reviewed、0 pending；标签 AND 12、OR 17、unknown 26；48个来源簇合为47个故障码/来源切分组，没有同故障码跨 calibration/validation。F30021-C04 已由用户授权的 AI 子智能体按唯一 `Possible causes` scope 定位到 `[332,372)`；同一短语在故障值段还出现一次，但不属于该 cause scope。该定位不改变 F30021 的 `unknown` 门型。v5 的54条 DeepSeek 探索预测仍仅覆盖旧版54条；v6 没有新预测，因此不能把 v5 的54/54作为 v6 成绩或校准结论。真实原文端到端链路已在一条 S120/S150 F06000 上验证嵌套结构与证据绑定：外层10项原因作用域保留为独立 scope，第9项的局部 OR 保留为2子项 scope，17条引用精确且唯一；该 Preview 仍只是一条开发样例，两个门都因无可用置信策略保持 `unknown`。S210 原文验证新增 F30027 与 F01681：F30027 的局部 OR 已获独立 AI 只读复核支持但最终门仍为 `unknown`；F01681 的旧版 Preview 显示46节点中仅2个可回连顶事件、44个断开，且8个节点缺少唯一证据。现已在共享候选合同与生成服务实现断开节点门禁：无法回连顶事件的节点逐个记入 blocker，整棵树转为 `blocked`，所有节点仍保留；`associated_with` 不被当作 FTA 连通边。对应回归已覆盖无边与仅有关联边两种断开情形。真实事件概率链路未完成。不接生产 API/数据库、不写正式 Gold，`tree_generation_authorized=false`、`fta_ready=false`、`production_ready=false`。

历史 v20 记录了单事件包/参考 Gold 的建立阶段；当时的哈希目录快照见[历史 manifest v24](../evaluation/quality_eval/fta_baseline_manifest_v24.json)，当前活动状态以[manifest v26](../evaluation/quality_eval/fta_baseline_manifest_v26.json)为准，验证命令见[manifest validator](../evaluation/quality_eval/validate_fta_baseline_manifest.py)。单事件输入包 Schema 与独立参考 Gold Schema 继续有效：模型输入只含一个顶事件和按页/章节定位的允许原文，不包含来源包络、图示门型或 Gold 标签。v19 的 [NASA XVS 整篇来源筛查](../evaluation/quality_eval/runs/fta_event_scope_xvs_source_screen_v1_2026-09-29.json)记录已扫描40页文本并查看8张 Appendix D 树图；该来源族只能作为已见 Dev/弃判边界候选，不可用于独立盲测 Final。另建立一条 NASA 航天器电池模块 Figure 7 开发样例，输入为 Section 5.0 原文，独立参考文件记录 7 个图示节点、3 个图示门；AI 角色审核修正了重复出现节点被误合并的问题。图示门为 OR/AND/AND，文本授权门为 OR/AND/unknown：第三门的图示叶项“Two module vents clog”比原文“failure of module vents”更具体，精确 scope 标为 `unknown/scope_ambiguity`。AI 角色审核不是人类专家 Gold。来源已被查看，仅 Dev；语义重叠未全审、权利记录不是法律审查。当前 1 个 packet、1 个参考文件；v1/v2 无可用输出、v3 返回可解析结构且8/8引文逐字匹配；v26 离线合同复核发现层级结构 blocker，因此不接受该候选树。独立 Final=0，候选树仍为 Preview，全局 readiness 保持 false。

**Unknown gate reason contract v1（2026-09-28）：**门型仍为 `unknown`，同时输出一个主原因码：`no_direct_logic_evidence`、`incomplete_child_set`、`semantic_scope_ambiguity`、`evidence_missing_or_ambiguous`、`confidence_policy_unavailable`、`model_confidence_below_policy`、`model_prefers_unknown_gate` 或 `unresolved_structure`。优先级固定为：子项集合不完整 → scope/证据范围冲突 → 无直接门证据 → 引文缺失/重复/无法绑定 → 置信策略不可用 → 模型置信未过策略/模型首选 unknown → 其他未解析结构。次级原因保留在 `blockers`；`decision_reason` 仅用于人工说明，禁止解析为机器真值。历史 unknown 若存在已知结构化 blocker 则按同一映射归类，否则只赋 `legacy_unspecified`，不读取自由文本猜测。实现与门禁回归见 `backend-python/fta/unknown_gate_reason_policy.py` 和 `backend-python/tests/test_unknown_gate_reason_policy.py`。

**本轮子目标：关闭 v7 剩余 3 条 pending（已完成）**：逐条复核 F30600、F30650、F30017，重划精确原文作用域，明确完整子项与排除项；没有直接 AND/OR 文本的均保留 `unknown`。验收结果为 v8 的 pending=0、原始证据引用均可精确回切，且不更改正式 Gold/数据库、不宣称 FTA ready。该子目标只关闭事件级候选范围审核，不代表更广泛的 FTA 总目标完成。

**本轮子目标：修正门节点评测边界与切分（v4 已完成）**：保留 v2/v3 历史文件不覆盖；将 `fault_cause_mode_set` 与 `not_applicable` 范围移出逻辑门节点集；对重复出现的 F30021 子项引文不自动选位置，标记 `pending_manual_locator`；切分按相同原文或相同故障码分组，保留旧分配并令新增同故障来源继承该分组。验收只证明数据结构/引用/切分边界，未生成模型概率、不做阈值校准，也不改变 FTA/生产门禁。

**最新事件级 AI 角色审核状态 v8（2026-09-27）**：v8 在 v7 基础上复核了最后3条 pending：F30600限定为两个有文本支持的触发情形，并逐条排除事件摘要、诊断状态及 F30611 后续响应；F30650按完整六个顶层故障值模式审核，1000下级说明留在该模式中；F30017补齐 Infeed 与 Motor Modules 两个适用分支的九项 Cause，并为每项保留分支标签。三者均无直接 AND/OR 门证据，因此记 `unknown`。39条统计为：37条已审核（AND 0、OR 1、unknown 36）、2条 `not_applicable`、0条 pending。详情见[v8审核结果](../evaluation/quality_eval/runs/siemens_s210_event_scope_gate_primary_ai_role_review_v8_2026-09-27.json)及[v3修订依据](../evaluation/quality_eval/datasets/siemens_s210_event_scope_gate_pending_review_amendment_v3_2026-09-27.json)。仍为主代理 AI 角色审核，非真人专家、非独立复核、非正式 Gold，未回查手册 PDF 原件；不写数据库，`fta_ready=false`、`production_ready=false`。

**数据口径纠错（2026-09-26，优先于下文早期节点集/探针数字）**：复核发现 v1 门节点集将 `F01001`、`A01035`、`F01680` 的局部 OR 短语误标为 `event_cause_set / OR`，其事件级原因集合并未完整确认。故 v1 的 57/57 Top-1 一致、Brier、Log-loss、ECE 及相应 validation 数字不得再解释为有效的事件级或跨 scope 门型评测/校准证据；原数据与探针保留作历史审计，不覆盖。新的数据集构建器要求 `event_cause_set` 的 AND/OR 同时通过跨 artifact 的“原因集合完整 + 门标签一致”核验，否则标记 pending 且不计入标签。事件级审核包含 29 个 unknown 对照和 10 个 OR 候选，共 39 条。主代理 AI 角色审核首轮为19条暂判完整、20条pending；v3 以唯一原文跨度补齐6条遗漏后为25条完整、14条pending。v4 将 `F13000` 重划为 Cause 段两条同层原因、将 `F13102` 重审为三个完整 fault-cause 模式；二者均保持 `unknown`。v5 将 `F30895` 和 `A07012` 在限定单子项范围下标记为 `not_applicable`。v6 对6条完整原因/模式范围完成精确引文修订；v7补齐F30003完整Cause列表，v8重新划定并审核最后3条pending。当前事件级统计以“最新事件级 AI 角色审核状态 v8”为准；门节点集合当前以“最新门节点审核集 v6”为准（v1–v5均保留作审计历史）。v2曾因fault-code/case-id错配错误放行F30895，v3后来又发现故障值模式和非适用范围不应混入门型评测、F01700不同来源跨切分及F30021过宽子项证据，均由后续版本修正并保留历史文件。审核为用户授权的AI角色判断，不能等同于真人专家签署；也未回查手册PDF原件，不能报告模型准确率或校准结论。所有材料均非正式Gold、非数据库数据。

**v6审核快照（2026-09-26；历史状态）**：v6对6条pending记录完成精确来源范围复核，完整子项集均保留为 `unknown`，没有从列表或编码推断AND/OR；另4条仍因范围/层级歧义保留pending。v6当时39条统计为：33条可评门型（AND 0、OR 1、unknown 32）、2条 `not_applicable`、4条pending；pending为 `F30600/F30003/F30650/F30017`。v6见[事件级 AI 角色审核](../evaluation/quality_eval/runs/siemens_s210_event_scope_gate_primary_ai_role_review_v6_2026-09-26.json)，修订依据见[pending review amendment](../evaluation/quality_eval/datasets/siemens_s210_event_scope_gate_pending_review_amendment_v1_2026-09-26.json)。以上均为AI角色审核、非真人专家、非正式Gold；未回查手册PDF原件，不写数据库，`fta_ready=false`、`production_ready=false`。

**v7审核快照（2026-09-27；历史状态）**：v7修复F30003遗漏的一项Cause子项后，39条中34条已审核、3条pending、2条not_applicable；pending为F30600/F30650/F30017。详见[v7审核结果](../evaluation/quality_eval/runs/siemens_s210_event_scope_gate_primary_ai_role_review_v7_2026-09-27.json)。状态已由v8更新。

## 当前闭环

```text
原始故障文本
  -> FaultExtractor
  -> ExtractionResult（故障记录 + 原文证据 + 诊断）
  -> CandidateFtaApplicationService（逐条处理）
  -> CandidateFtaExtractionService
      -> 前置阶段：逐原因语义角色/处置提案，唯一绑定原文证据
      -> 结构阶段：只分解获准进入树的原因与局部 gate_scope
      -> 主机校验节点、引用和 scope 结构
      -> 门型阶段：在不可更改的结构上评估各 scope 的门型及独立关系
  -> Candidate Preview（节点证据、门证据、置信策略快照、blockers）
```

`CandidateFtaGenerationResult` 保留完整 `ExtractionResult` 和证据，并为每条记录单独返回 `proposed / blocked / failed`。某条模型调用失败不会丢弃已抽取记录；调用方可以把保留的 extraction、原文和该条 `record_id` 交给 `retry_records()`，不必重新抽取。完整原文不复制进候选 artifact；生成结果和每棵候选树都绑定源文 SHA-256，证据引用保留精确原文片段与 `[start,end)`。

### 当前树输出合同 v5 边界

- `CandidateFtaTree` 使用节点、`CandidateFtaGateAssessment` 与 `CandidateFtaRelation` 三种对象；不再用一个平面 gate 表示整个故障。
- 每个适用门以稳定的 `gate_node_id` 绑定故障身份、源文摘要、`scope_type` 和确切作用域跨度；独立保存 AND/OR/unknown 概率分布、provisional 策略/阈值快照、child IDs、原因集合状态、作用域引文和直接门证据。`not_applicable` 不携带这些门分类概率和策略字段。
- 原因处置完成后，结构分解与门型判断分为两个独立模型阶段。门型阶段只能按 `gate_id` 对结构阶段的 scope 一对一评估，不得新增、删除或重排节点/scope；缺少、重复或多出的 ID 会使候选失败。结构阶段不确定的原因索引会保留 blocker，不准门型阶段补猜结构。
- AND/OR 必须有唯一精确引文、该作用域下完整且归一化的多子项、所有节点出处都落在同一 scope 内，并通过显式置信策略；缺证、重复引文、scope 不覆盖节点或低置信度时门保持 `unknown` 或整棵候选 `blocked`。
- `not_applicable` 与 `unknown` 分开：仅当作用域只有一个 child，且原因集合声明完整并已叶项归一化时，才记录 `not_applicable`；这时不保存门类型概率、门证据或置信策略，也不进入 AND/OR 置信度校准。只有一个已观测 child 但原因集合完整性/归一化不足时仍为 `unknown`，不能把“暂时只找到一个”当作“确定只有一个”。该状态仍是 AI 候选判断，不代表 Gold 或专家批准。
- 未知门可以留在证据完整的 `candidate_ready_for_review` Preview 中；这只表示可供复核，不表示门已接受。结构/证据损坏或原因映射不完整时整棵 Preview 为 `blocked`，保留 blocker。
- `unknown` scope 仍可保留一条精确唯一、位于 scope 内的直接逻辑引文作为审核证据；保留该引文不会自动把门改成 AND/OR。每个 `unknown` 必须有一个主 `unknown_reason_code`，次级 blockers 单独保留；自由文本理由不参与归类。序列化同时输出从 gate assessments 推导的 `unknown_gate_reason_counts`，便于报告按原因汇总。
- `causes / may_cause / associated_with` 是带独立原文证据及两端节点共同覆盖 scope 的有向关系边，与 AND/OR 逻辑门分离。单一配置组可通过 `may_cause` 指向顶事件，而顶层门仍为 unknown。
- 每个生成叶/组节点必须引用至少一个 `fta_event_candidate` 的原始 cause index；只有这类原因要求映射到树节点，一个合格 cause 仍可映射到多个从原文拆出的节点。所有原始原因（包括 `relation_only`、`exclude_from_tree` 和 `unresolved`）都必须完整保留在 `cause_dispositions` 审计账中；未决项阻断整树放行，明确非树项不产生树节点也不自动创建因果边。抽取时没有 CAUSE evidence span 不等于可以无证据建树：分类模型提出的引文必须由 binder 在原文中唯一定位；未出现或重复出现均转 `unresolved`，不得自动选位置。
- `CandidateFtaTree` 序列化版本为 v5，以完整逐项处置账和 unknown 主因码连接抽取原因与树结构；它仍是 `ai_proposed` 离线 Preview，不把模型分类写成专家 Gold。
- 门置信度目前明确是 `uncalibrated_model_estimate`；策略只能是 `provisional`，不得宣称概率已校准。AI 角色 provenance 不等于真人审核、Gold 批准或生产就绪。
- 事件发生概率尚未接入候选应用流程，且当前未找到真实 S210 设备统计样本；门确定/审核前不得运行概率一致性推断，模型门概率不得冒充事件发生概率。

## 门类型与置信度

- 每一层的 AND/OR 必须同时满足：该 scope 的原因集合完整、子项归一化、节点精确证据、作用域内唯一直接逻辑引文、唯一最高类别，以及显式置信度阈值和 margin。分层结构由递归节点表达，不再要求整条故障原因必须被压成同级叶项。
- 程序验证节点证据和门证据的精确唯一位置、源文摘要及同一 scope 锚点；不能仅凭字符串切片证明引文在语义上蕴含 AND/OR，语义是否支持仍需审核。因此 `candidate_ready_for_review` 只表示证据闭合的候选可供复核，不是审核通过。
- 一层原因集合不完整或不适合直接作为同级门输入时，该层保持 `unknown`；其他局部 scope 仍可分别提议门，但若节点证据、scope 或抽取原因映射无法核验，整棵候选会 `blocked`。
- 未配置阈值、分数并列、低于阈值、margin 不足、原因集合不完整、证据缺失/重复或抽取状态非完整时，保持 `gate=unknown` 或 `blocked`；概率分布仍保留作诊断。
- 当前阈值策略仅接受 `provisional`。任何输出都不是 `fta_ready`、`production_ready`，且概率含义标记为未校准模型估计。
- 已审核逻辑 Gold 当前只有 6 条：5 条 OR、1 条 unknown、0 条 AND。2026-09-26 已对这 6 条执行 `deepseek-flash` 置信度探针，产物为 [模型置信度探针](../evaluation/quality_eval/runs/siemens_s210_gate_confidence_probe_named_gold_v1_2026-09-26.json)。模型 Top-1 与 Gold 一致为 1/6：5 条 Gold OR 均被模型判为 unknown，Gold unknown 案例也被判为 unknown；6/6 条均未通过原因叶项规范化检查。该结果说明当前首先受原因集合层级/完整性和直接逻辑证据约束，不能据此调门限或推翻 Gold。
- 探针审计指标为 Top-1 `0.1667`、多类 Brier `1.4833`、log-loss `17.9214`。它们只描述这 6 条小样本上的模型自报分布，不代表校准质量。AND 类仍为 0，且没有独立 calibration/validation 划分，所以校准状态仍是 `insufficient_evidence`，不得选出或宣称任何已校准阈值。离线审计脚本只计算覆盖、Top-1、Brier、log-loss 和显式阈值的 coverage/accepted accuracy；不自动挑阈值。
- 另对照了全量 [AI 授权逻辑门复核](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.json)：它不是正式 Gold，也没有覆盖人类 Gold；但在这 6 条中，与命名专家 Gold 的门标签存在 4 条差异：A01069=`not_applicable`、A01631=`unknown`、A01981=`not_applicable`、A30714=`unknown`，而 Gold v1 将它们都标为 OR；A07094 的 OR 与 F01611 的 unknown 一致。AI 复核对 A01069/A01981 将摘要/诊断项从独立叶项中排除，对 A01631/A30714 因完整性或层级不足保留 unknown。该冲突只作为错误分析，不能覆盖命名专家 Gold；也说明在校准前必须统一“摘要与叶项”“单一原因的 not-applicable 与 unknown”的标注规则。当前校准审计器尚不自动检查跨版本标签冲突，因此本轮分数只能作描述性探针。
- 对同一份 281 事件汇总做了节点级范围审计：找到 15 条明确的 `local_logic_observations`（AND 1、OR 12、unknown 1、unresolved 1），分布在 14 个 fault code；A30031 含两个不同局部作用域，F30625 与 F30655 则重复引用同一句原文。逐条回查原始 corpus 后，14 条引文唯一出现，13 条声明的 `[start,end)` 位置精确切回原文；F30001 缺少 offset，F31405 的引文在 corpus 中找不到。在明确标为 AND/OR 的 13 条中，有 11 条的局部逻辑与事件顶层门不同。因此不能按 `fault_code` 把事件级 Gold 复制给内部节点；节点级校准还必须按原文证据簇分组切分，避免同一故障下节点或重复引文跨入 calibration/validation 两侧。可复核明细见 [节点逻辑原文跨度审计](../evaluation/quality_eval/runs/siemens_s210_local_logic_source_audit_v1_2026-09-26.json)。该汇总不是正式 Gold、没有独立 calibration/validation 划分；它只能作为待审核的节点级校准候选池，不能据此宣布阈值已校准。
- 对全量 [AI 授权逻辑门复核](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.json) 的 281 个事件仍保持原状态：OR 17、not_applicable 60、unknown 204；它不是概率预测数据，也不是人类专家 Gold。历史 [AI 角色门节点审核集 v1](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v1_ai_role_review.json) 和 [来源簇切分 v1](../evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v1.json) 曾统计 57 个 reviewed 节点（AND 11、OR 17、unknown 29）、1 个 pending、50 个来源簇；后续复核确认其中 3 个 event-scope OR 行属于作用域误标，因此该 v1 标签集合及基于它的探针结果已被纠错说明取代，不可用于事件级/跨 scope 性能结论。原29个unknown节点仅说明先前AI审核标注为unknown，不能直接当正式Gold；本轮事件包中的候选需以最新逐条审核结果为准。局部 AND/OR 只能用于各自局部 scope。
- 新的 [AI 角色门节点审核集 v2](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v2_scope_reconciled_ai_role_review.json) 与 [来源簇切分 v2](../evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v2_scope_reconciled.json) 已通过跨 artifact 的事件 scope / cause-set 完整性 / gate-label 对账：58 个节点中 54 reviewed、4 pending；reviewed 标签计数 AND 11、OR 14、unknown 29，47 个已分配来源簇。F01001、A01035、F01680 因事件级范围不完整或门标签不一致被改为 pending，不参与计分。 [事件级审核包 v2](../evaluation/quality_eval/runs/siemens_s210_event_scope_gate_blind_review_bundle_v2_2026-09-26.json) 保留无标签的39条初始输入；[候选修订清单](../evaluation/quality_eval/datasets/siemens_s210_event_scope_gate_candidate_repair_manifest_v1_2026-09-26.json)与修订生成器仅应用唯一精确原文跨度，随后v3–v8按追加式修订推进。当前状态以v8为准：37条已审核门型（AND 0、OR 1、unknown 36）、2条 `not_applicable`、0条pending。该AI角色审核非真人、非独立复核，不作为概率校准Gold；v1–v7仅保留作审计历史。

- **v3（历史/已被 v4 取代）**：[数据集 v3](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v3_v8_scope_reconciled_ai_role_review.json) 以 v2 为底稿对账了 v8 范围，但后续发现它仍将 `fault_cause_mode_set` 放入 unknown 门类、保留 excluded 行在门节点表、只按来源切分而让 F01700 的两个来源跨集合，且 F30021-C04 绑定整段 cause-list。v3 文件与切分保留作审计历史，不应用于新校准或新预测。
- **门节点审核集 v4（历史，已由 v5 取代）**：[逻辑门节点集 v4](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v4_gate_only_ai_role_review.json)包含55个节点（50 reviewed、5 pending；AND 11、OR 14、unknown 25），当时 pending 为 F01001、A01035、F01680、F01659 及 F30021-C04 引文定位。v4 的切分映射见[来源簇切分 v4](../evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v4_fault_and_source_grouped.json)。该版本和3个 `fault_cause_mode_set`、2个 `not_applicable` 范围附件仅保留作审计历史；审核状态随后依次更新到 v5、v6。旧记录曾报告 v4 有266个证据跨度；v4重算为244个，二者口径差异尚未追溯，故不沿用旧总数。v5版本当时统计245个，且纳入字段均通过原文切片校验。

- **当前门节点审核集 v6**：[逻辑门节点集 v6](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v6_locator_reconciled_ai_role_review.json)共55个节点，55 reviewed、0 pending、0 excluded；标签 AND 12、OR 17、unknown 26。v6 只在 v5 基础上关闭 F30021-C04 的证据定位问题：精确短语全文出现两次，但唯一 `Possible causes` scope `[166,372)` 内只有 `[332,372)` 这一处；另一处 `[468,508)` 属于 r0949 故障值说明。子项 evidence 已收窄至 `[332,372)`，该 AI 定位不新增 gate evidence，F30021 门型保持 `unknown`。依据见[定位审核 JSON](../evaluation/quality_eval/runs/siemens_s210_F30021_C04_locator_ai_review_v1_2026-09-27.json)；v5 原始[定位确认单](../evaluation/quality_eval/runs/siemens_s210_F30021_C04_locator_confirmation_v1_2026-09-27.md)保留作历史，不覆盖。新切分映射见[v6来源簇切分](../evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v6.json)：48个来源簇合并47个 fault/source split group，F30021 恢复历史 validation 分配，没有改变其他 v5 分配。v6 审核由用户授权 AI 子智能体执行，并由主代理按原始 corpus 复核；不是真人专家签署、不是正式 Gold，也不是概率校准。

- **历史门节点审核集 v5（被 v6 取代）**：[逻辑门节点集 v5](../evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v5_independent_ai_role_review.json)仍为55个节点，54 reviewed、1 pending、0 excluded；已审核标签 AND 12、OR 17、unknown 25。v5 独立角色复核并以原始语料逐字复核了 v4 的四个门候选：F01001、A01035、F01680 的原文分别支持其局部原因表达为 OR，但这些短语不代表完整事件根因集合，故 scope 改为 `local_cause_expression`，不外推为根节点门；F01659 的 fault value 20 只支持 `enable_attempt_group` 局部 AND，两个子项均绑定共同限定语 `both controlled via F-DI`，不得据此把 F01659 故障根节点标为 AND。F01680 的泛化 child `a fault is present` 不是可执行 FTA 叶节点，因此即使局部门标签为 OR，整树仍标记 blocker。F30021-C04 在 v5 保持待定位，已由 v6 追加修订关闭。

  v5 来源簇切分见[切分映射 v5](../evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v5.json)。唯一待人工定位项有[独立确认单](../evaluation/quality_eval/runs/siemens_s210_F30021_C04_locator_confirmation_v1_2026-09-27.md)。按当前节点合同重新验证了245个 scope/child/gate/explanatory evidence spans，全部精确回切原文；47个来源簇合并为46个 fault/source 切分组，未发现故障码跨 calibration/validation。划分内 calibration 有43个节点/38个来源簇（AND 8、OR 14、unknown 21），validation 有11个节点/9个来源簇（AND 4、OR 3、unknown 4）。

  **v5 探索性概率探针（2026-09-27）**：[原始预测 artifact](../evaluation/quality_eval/runs/siemens_s210_gate_node_confidence_probe_v5_exploratory_2026-09-27.json)，模型 `deepseek-flash`，54/54 请求成功。模型 Top-1 与当前 AI 角色审核标签完全一致：AND 12/12、OR 17/17、unknown 25/25；整体 Top-1 `1.0000`、多类 Brier `0.00203`、Log-loss `0.01455`、Top-label ECE `0.01389`。分组结果：calibration 43/43，Top-1 `1.0000`、Brier `0.00251`、Log-loss `0.01709`；validation 11/11，Top-1 `1.0000`、Brier `0.00013`、Log-loss `0.00459`。validation 的11个节点来自9个来源簇，仍是很小的同一公开手册样本；这些数字只代表本次模型与当前 AI 标签集的一致性，不证明真实工程门型正确，也不证明跨手册泛化。

  29条 AND/OR 预测均提供唯一且位于节点作用域内的原文逻辑引文，探针 proposal blocker 为0；25条 unknown 没有伪造逻辑门引文。离线审计无节点身份、来源、offset 或 evidence mismatch，`calibration_status=ready_for_policy_review`；但 `gate_policy_selected=false`、探针 `threshold_selected=false`，概率校准器和接受阈值均未建立。这里的 `ready_for_policy_review` 只表示预测、审核行和来源切分资料可供策略审查，不等于已校准、已批准或可运行时放行。v5 仍明确保持 `reviewer_is_human_expert=false`、`formal_gold=false`、`database_written=false`、`tree_generation_authorized=false`、`fta_ready=false`、`production_ready=false`。

  本轮调用经用户明确授权；54条提示不包含审核标签和审核理由，F30021-C04 pending 未发送。复核命令（探针会再次调用外部模型并可能产生费用；审计命令为离线）：

  ```powershell
  python evaluation/quality_eval/public_sources/probe_fta_gate_node_confidence_v1.py --dataset evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v5_independent_ai_role_review.json --corpus evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl --output evaluation/quality_eval/runs/siemens_s210_gate_node_confidence_probe_v5_exploratory_2026-09-27.json
  python evaluation/quality_eval/fta_gate_node_confidence_audit.py --gold evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v5_independent_ai_role_review.json --predictions evaluation/quality_eval/runs/siemens_s210_gate_node_confidence_probe_v5_exploratory_2026-09-27.json --split-assignments evaluation/quality_eval/datasets/siemens_s210_gate_node_source_cluster_splits_v5.json --source-corpus evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl
  ```

v5 生成及针对性验收：

```powershell
python -m evaluation.quality_eval.public_sources.reconcile_fta_gate_node_review_dataset_v5
python -m unittest evaluation.quality_eval.test_reconcile_fta_gate_node_review_dataset_v5 evaluation.quality_eval.test_fta_gate_node_confidence_audit -v
python -m compileall -q evaluation/quality_eval/fta_gate_node_confidence_audit.py evaluation/quality_eval/test_fta_gate_node_confidence_audit.py evaluation/quality_eval/public_sources/reconcile_fta_gate_node_review_dataset_v5.py evaluation/quality_eval/test_reconcile_fta_gate_node_review_dataset_v5.py
```

探针默认路径仍指向旧版；复跑必须显式提供 v5 的 `--dataset/--corpus/--output` 并使用全新输出文件，不能覆盖已有预测。当前预测只可用于错误分析和后续策略研究，不能用同一批 validation 数据反复调阈值后再声称独立验证。

v4 针对性回归命令与本轮结果：

```powershell
python -m unittest evaluation.quality_eval.test_reconcile_fta_gate_node_review_dataset_v4 evaluation.quality_eval.test_reconcile_fta_gate_node_review_dataset_v3 evaluation.quality_eval.test_fta_gate_node_review_dataset_builder evaluation.quality_eval.test_fta_gate_node_confidence_audit evaluation.quality_eval.test_apply_fta_event_scope_gate_review_v8 -v
python -m compileall -q evaluation/quality_eval/public_sources/reconcile_fta_gate_node_review_dataset_v4.py evaluation/quality_eval/test_reconcile_fta_gate_node_review_dataset_v4.py
```

本轮 24 项测试通过，相关 Python 文件编译检查通过；未运行模型探针、未修改旧版 v2/v3、正式 Gold 或数据库。

**独立只读复核补充（2026-09-26；其 scope 结论已由后续复核更正）**：早先一次只读复核确认了 58 个节点的字符跨度，但误把 AND/OR 候选包的局部证据交叉确认成事件级 scope 无误；随后逐项对照 consolidated event review 发现 F01001、A01035、F01680 的事件原因集合不完整或顶层标签不一致。故早先“未发现标签错误”的结论仅适用于原文跨度形状，不能用于语义标签/作用域通过声明。F01659 仍 pending；另有 10 个 unknown 子项缺少 `span_origin` / `source_match_count` 元数据，但引文在语料中唯一且偏移准确。本次没有核验原始手册/PDF，也不构成人类专家审核。

**置信评测样本量限制（v1 数字仅作历史）**：v1 把 3 个作用域误标的 event OR 行混入 57 个 reviewed 节点，故此前基于它算出的 validation 10 个独立簇、12/12、25.9% 零错误上界及全体 50 簇 5.8% 上界，均不再作为当前有效样本统计。当前事件级审核v8有37条已审核门型标签（AND 0、OR 1、unknown 36）、2条not_applicable和0条pending；事件级AND正例仍为0，来源仅为同一手册且审核非真人/非独立，因此远不足以进行三分类校准或选门置信阈值。

**同作用域补充候选池（尚未进入评测）**：对全量事件审核结果按 `logic_gate=OR`、`cause_set_complete=true` 且至少两个有证据的合格因果子项盘点，找到 10 个事件级候选：A01780、A07012、A07094、A30788、F01018、F01700、F07414、F30002、F30004、F30068。它们仍须独立复核作用域、完整子项与门证据，主审核标签不能直接当作独立标签。A01780 与 F01700 已各有不同局部门节点，因此来源文本去重后这 10 项最多增加 8 个新来源簇。若审核通过，可扩充 `event_cause_set` 的 OR 对 unknown 对照；但该语料仍无事件级 AND 正例，不能单独支持完整三类门型的事件级校准。来源清单以 [281 条事件审核汇总](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.json) 为准。

**v1 历史冒烟（之后由递归合同固定响应回归扩展，不等于 v3 在线验收）**：2026-09-26 对公开原文样本 `SIEMENS_S210_2019_A01631` 做真实配置模型原文入口冒烟：抽取器返回 `success`、故障码 `A01631`，并把原文压缩成一个原因值 `No motor holding brake available and SBC enabled`；但证据映射没有为该值绑定任何 CAUSE span。旧候选应用层因此以缺证据/原因不足安全阻断，记录见 [真实原文入口冒烟结果](../evaluation/quality_eval/runs/siemens_s210_candidate_fta_real_source_smoke_A01631_2026-09-26.json)。它证明旧版 fail-closed，不是当前递归合同的实时模型端到端成绩。

### A01631 复合条件的原文层级审计

对同一原始语料记录 `SIEMENS_S210_2019_A01631` 做了只读回查。原文先描述配置“不实用”，继而写明“以下配置可能导致此消息”，并列出一条配置：`"No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1).` 该完整引文在记录原文中唯一出现，字符区间为 `[246, 325)`；其中两个条件分别位于 `[248, 294)` 与 `[299, 324)`。原文位置通过对当前 JSONL 输入文本做精确切片核验。

这条样本说明必须区分两个逻辑作用域，不能把“一个抽取 cause”误当成“一个顶层叶事件”，也不能把两个子条件平铺成顶层 OR：

```text
A01631 顶事件（候选门：unknown；原文未直接证明事件级 OR）
└─ 配置条件组（以独立 causes 因果边指向顶事件，不伪装成顶层门输入）
   ├─ 条件：无电机制动器（p1215 = 0）
   └─ 条件：SBC 已使能（p9602 = 1）
      组内逻辑门候选：AND；直接证据为整条配置引文 [246, 325)
```

原文直接支持配置组内 AND；命名专家 Gold 将两个候选标为事件级 OR，但原文是先概括“检测到不实用的配置”，再写“以下配置可导致该消息”并列出一个具体配置，没有直接引文证明这两个候选是彼此独立、可分别导致顶事件的两个 OR 分支。故 Gold 标签仍保留为专家评测标签，但候选生成必须独立遵循直接证据门禁：事件顶层门保持 unknown，配置组到事件用单独的 `causes` 因果关系表示，组内 AND 另作独立 `gate_node_id` / `scope_type`。不能把 Gold 标签当成原文引文，也不能用因果边替代 FTA 门。候选完整性应限定到原文列出的配置集合，并独立审核；不能因为两个叶条件已拆出，就自动宣称原因集合完整。模型置信度可用于已校准决策中的接受/弃判，但不能替代原文证据；事件发生概率只在结构审核确定后用于一致性核验。

历史审计结论：扁平 `FaultRecord.causes` 与旧单层候选合同确实无法保留上述父子层级；已审核用的 `fta_graph_contract` 也不能直接冒充未审核候选合同。该设计缺口已由递归候选合同演进处理：候选自有 nodes/gates/relations 合同，A01631 的局部 AND、`may_cause` 边与顶层 unknown 可以并存；不改变 Gold、数据库或审核状态。

### A01631 证据映射 owner 诊断

历史 v1 owner 诊断（不代表当前 v4 行为）：`TextExtractionAdapter._find_evidence_locations()` 对英文连接词 `and` 的拆分能力不足，单个复合原因无法由旧的“一原因一 span”候选输入表达。该限制仍未改写抽取 owner；递归候选合同在候选边界内按 `source_cause_indices` 保留来源关联，并要求候选节点自己从原始输入绑定唯一原文 quote，因此无需静默改动抽取事实或 `TextExtractionAdapter`。

当前采用的保守修复是在**候选层**表达“配置组 + 叶条件”，叶节点有独立原文证据、组内门有对应 scope/逻辑证据，来源映射仍追溯到原始抽取 cause index；没有为抽取层新增领域特例。公开英文 A01631 原文的固定模型响应回归已覆盖该结构。它验证合同、解析和证据定位，不验证在线模型的语义正确率；AI 输出依旧只是 Preview。

历史 fixture 曾错误断言 A01631 顶层 OR；当前测试已替换为递归表示：配置组内 AND、有向 `may_cause` 关系、顶层 unknown，并检查节点证据与 gate scope。此处是固定模型响应回归，不是在线 LLM 预测，也不是人工专家签署。

### 15 条局部逻辑观察的独立源文复核

2026-09-26 由独立只读子智能体逐条复核 `siemens_s210_local_logic_source_audit_v1_2026-09-26.json`：15 条 observation 均唯一关联到公开语料记录；14 条非空 quote 均在对应原文唯一出现，其中 13 条原有 offset 精确回切。F30001 的 quote 唯一但原 audit 缺 offset，复核定位为 `[176, 229)`；F31405 的 observation 缺 quote/offset，但汇总审核 artifact 的 `[115, 214)` 可在原文精确回切。该复核只确认 source alignment，不把 AI 标签升级为 Gold，也未修改文件、Gold 或数据库。

门型必须按引文所处节点作用域解释：

- **A01631**：`"No motor holding brake available" (p1215 = 0) and "SBC" enabled (p9602 = 1)` 只直接支持配置条件组内部 AND。命名专家 Gold 的事件级 OR 标签仍是评测真值，AI 汇总 `unknown` 不回写 Gold；但原文没有清楚提供两个独立事件级 OR 分支的直接引文。因此用于候选生成时，事件级 gate 仍须 unknown，除非后续获得可直接支持顶层 OR 的原文证据；具体配置组与故障事件可另以有出处的因果边连接。Gold 标签与候选证据准入是两个不同判断，不能混用。
- **事件级 OR 候选**：F01911 的两个时序条件由 `or` 连接；F30655 的唯一原因描述含 `either ... or ...`。它们可作为独立复核候选，但原因分支仍需拆成有证据的节点，且该 source audit 本身不是独立专家 Gold。
- **其余 observation**：只支持局部复合短语、配置/条件组、诊断值映射或未知逻辑；不能从局部连接词、项目符号列表或参数解释提升成整个故障的 AND/OR。F01673 的 `and/or`、F30700 的并列 `Possible causes` 保持 unknown；F07011 缺现场故障值，不能由诊断值说明断定本次发生原因。

因此这 15 条**仍不进入当前门置信度审核集**：它们属于历史局部逻辑 observation，缺少本节审核集所要求的统一节点子项复核；不能与事件级 Gold 混成一个 `fault_code` 标签。AI 汇总记录的 15 个事件 `build_allowed=false`，此状态保持不变。当前另行使用已核验的 29 个 AND/OR 节点候选与 29 个完整原因集 unknown 节点，并保留所有来源范围和 AI provenance；不是把这 15 条直接塞进新数据集。置信度与证据仍是相互独立的准入条件：模型分数不替代引文，直接引文也不替代经过审核样本校准的决策策略。

### 281 条原文扫描得到的 AND/OR 节点审核候选池

按用户授权的 AI 专家角色，由两个独立子任务扫描同一份 281 条公开原文，主 agent 随后逐条以 `input_text[start:end] == quote` 复核引文与所有子分支。两个包都带来源 SHA-256、AI 审核 provenance、`formal_gold=false`、`database_written=false`；不是正式 Gold。

- [OR 节点候选审核包](../evaluation/quality_eval/runs/siemens_s210_gate_node_or_ai_review_candidates_v1_2026-09-26.json)：17 条可进入独立复核、2 条 ambiguous、1 条 reject；51/51 个门/子项跨度精确，原始语料哈希匹配。F01701 文本的 OR 实际针对关联消息 F01700，已单独标注 target，不能误归到 F01701 顶层门。其余局部 cause、检测位置/来源、运行触发条件也按各自 `scope_type` 区分。
- [AND 节点候选审核包](../evaluation/quality_eval/runs/siemens_s210_gate_node_and_ai_review_candidates_v1_2026-09-26.json)：12 条可进入独立复核、3 条 ambiguous、2 条 reject；36/36 个门/子项跨度精确，原始语料哈希匹配，覆盖 9 个故障码；**事件顶层 AND 候选为 0**。其中 A01631 仅是配置组内 AND，F30078 的源文实际含 U+2013 EN DASH 后接 `and if`，不是初始 AI 输出中损坏的 `�C`；主 agent 已依据原文修正分类。
- 两包合计 29 条局部门节点候选（17 OR、12 AND），另有 5 条歧义和 3 条排除；标签只适用于各自显式 scope。不能把它们折叠为 29 个“事件级故障树门”。

### 29 个门节点的独立 AI 复核

2026-09-26 另一子智能体在不修改文件的前提下，重新阅读 29 个候选及对应公开原文，逐条检查 scope、children 的同层性/完整性、门语义与引文跨度。主 agent 再次核验当前语料 SHA-256 与两个候选包一致（`b42535d37ae27b63ba0048c88e947916e846da53e1bf18b3e5825c1853c1f483`），并独立回切门/子项共 87 个跨度，均精确匹配。

- 独立 AI 复核结论：29 个局部门节点都能在其具体 scope 的原文中找到 AND/OR 连接关系支持（OR 17、AND 12）；这只是局部文字逻辑标签，不等于每条故障的完整 FTA 根门，也不表示物理根因已确诊。
- 复核标记的树结构限制：F01680 有一个过宽泛的 `a fault is present` 分支；F07901 的正/负方向短语须继承父句“超过最大允许速度”；F01659 的两个事件须保留共同限定“both controlled via F-DI”；F01043、F31896 的引文是示例而非完整候选集合；F01701 的 OR 归属相关消息 F01700；F30078、F31405 表达监控响应/检测位置，不是已证实的物理原因。这些样例可以验证“节点级文字门识别”，但不能未经补全就进入完整树。
- [独立 AI 复核 artifact](../evaluation/quality_eval/runs/siemens_s210_gate_node_independent_ai_review_v1_2026-09-26.json) 保存了 29 个候选及 5 个歧义项的逐条结果；明确标记非人类专家签署、不可校准、非正式 Gold，且 Gold/数据库/FTA/生产就绪均为 false。

### 5 条 ambiguous observation 的 scope 复核

另一轮只读独立 AI 复核将 5 条 ambiguous observation 按其具体语义范围分类；主 agent 对照同一原文复核 5/5 个 quote/offset，均精确。`ambiguous` 是待查状态，不是 `unknown` 标签的同义词：

- F01672、F01673：在明确的 Cause/原因条件 scope 下，原文分别直接支持 OR（F01672 的逗号部分须合并成一个分支；F01673 的 `and/or` 是 inclusive OR）。当前 OR artifact 缺这两条的 `scope_type`，需先补 scope 与共同谓词/子项结构，不能直接并入节点校准样本。
- F01651：原文 `and` 描述安全同步要求的覆盖范围，未说明其中两种同步链路各自失败如何组合造成故障事件；对此事件级子事件集合应保持 unknown。它是潜在弃判例，但当前 artifact 未列出待判断的两个子事件，故暂不能作为有效的节点级校准行。
- F01682：`only supported in conjunction with PROFIsafe` 在“兼容性要求”节点直接支持 AND；这是要求/配置关系，不是 F01682 顶层故障因果 AND。该样本需与故障事件门任务分开。
- A01940：`and` 连接运行背景条件；原文没有说明这些背景状态是 FTA 子事件或导致关系，故排除出因果门标签，而不是标成 unknown。

因此这 5 条当前给出 **OR 2、AND 1、unknown 1、exclude 1**；但可直接用来做节点级校准的新增样本仍为 0，因为 OR 样本 scope 缺失、F01651 缺子事件集合、F01682 属于不同任务 scope，而 A01940 非因果门样本。Gold/原候选包均未被改写。

这是校准数据准备的进展，不是校准完成。再次独立回切原文后，OR 为 51 条、AND 为 36 条跨度，全部精确匹配（合计 87 条；早先摘要中“54/41”是统计错误，以本轮逐条切片结果和候选包内校验为准）。当前 29 个已提议节点分属 26 条节点-故障关联、25 个唯一故障簇：AND 12 节点/9 个故障簇，OR 17 节点/17 个故障簇；两类标签的故障簇仅在 F30078 重叠。5 条歧义项已按 scope 复核，但没有一条可不经规范化直接作为新的校准行。现有 DeepSeek probe 和 calibration audit 仍以 `fault_code`/单事件 gate 为键，不能消费多层节点；稳定身份须使用 `gate_node_id + scope_type + source digest + exact anchor`，并按故障/重复证据簇整体切分 calibration/validation。要开始节点级概率校准，还需独立节点级审核标签、对应节点级模型预测和不泄漏的分组划分；在此之前不拟合、不选阈值、不宣称 gate confidence 已校准。

校准就绪审计入口：

```powershell
python evaluation/quality_eval/fta_gate_confidence_calibration.py `
  --gold evaluation/quality_eval/datasets/siemens_s210_and_or_logic_gold_v1.json `
  --predictions evaluation/quality_eval/runs/siemens_s210_gate_confidence_probe_named_gold_v1_2026-09-26.json
```

当前这份预测产物覆盖 Gold 6/6 条，离线审计指标为 Top-1 `0.1667`、Brier `1.4833`、Log-loss `17.9214`；这些仅是小样本描述性结果，不是校准通过。当前实际阻塞是 Gold 缺 AND 类和缺独立 calibration/validation 划分。后续新增审核预测仍需提供 `--predictions <artifact.json>` 与不重叠的 `--split-assignments <mapping.json>`；划分映射按 `fault_code` 指定 `calibration` 或 `validation`，不修改 Gold 本体。

当前校准审计脚本以 `fault_code` 为单一标签键，适用于事件顶层门，不适用于同一故障下多个不同层级的局部门。节点层级合同确认后，校准数据键必须改为稳定的 `gate_node_id` 并携带 `scope_type`；不得将同一 `fault_code` 下的局部 AND/OR 合并成一个标签。

### 节点级置信度审计器

新增 `evaluation/quality_eval/fta_gate_node_confidence_audit.py`，供局部门校准资料使用。它以 `gate_node_id` 而不是 `fault_code` 匹配审核标签和模型概率；身份同时核对 `fault_code`、`scope_type`、原文 SHA-256、作用域锚点和 `source_cluster_id`。同一来源/故障下的不同逻辑节点因此可分别计分，但训练/验证划分必须以来源簇为单位，禁止同一簇跨集合。

输入 `fta_gate_node_review_dataset` 必须保留审核来源（包括是否真人审核）、非正式 Gold 状态、完整作用域锚点、每个 child 的原文证据、门证据和完整子项状态。`AND/OR` 标签必须有门证据；`unknown` 仍需要完整且可定位的待判断子项集合。每个证据跨度必须位于该节点的精确作用域锚点中。审计时必须提供原始 JSONL `--source-corpus`，按每条 `input_text` 的 UTF-8 SHA-256 找到原文，并逐条验证作用域、child、门证据的 `[start,end)` 切片；缺原文或任一 quote-offset 不符都会阻断 readiness。预测必须使用相同节点身份及来源锚点，并携带单一模型 ID。待审核和排除项会单独计数，不会被当作已审核标签。

该审计器只报告节点级覆盖、Top-1/Brier/Log-loss 和按来源簇切分结果；**不拟合概率校准器、不选择置信度阈值，也不将 AI 复核升级为真人签署**。`ready_for_policy_review` 仅表示输入、类别和分组预测齐备到可供策略审查，并不表示概率已校准或可用于生产。

生成器 `evaluation/quality_eval/public_sources/build_fta_gate_node_review_dataset_v1.py` 的 v2 输出会将不完整或跨 artifact 门标签冲突的事件级正例留在 pending；此前29个局部AND/OR候选和29个事件级unknown需要按此规则重建。首轮发现20条pending；v3以唯一原文跨度补齐6条后，v4完成2条范围重审，v5将2条单子项完整scope分流为not_applicable，v6对6条完整scope标unknown，v7补齐F30003完整Cause列表，v8对F30600/F30650/F30017逐条重划范围并显式登记排除项；当前39条候选已无pending。修订均以精确唯一原文跨度和fault-code/case-id一致性为门槛，重复引文仍需人工定位。v8为当前AI角色开发审核材料，不是正式Gold；不得沿用v1概率预测/分数。

历史脚本 `evaluation/quality_eval/public_sources/probe_fta_gate_node_confidence_v1.py` 曾对 v1 的57个 reviewed scope 请求模型输出 AND/OR/unknown 概率；其结果保留作审计，但配对标签集存在 scope 污染，不可用于有效准确率/校准结论。脚本当前支持显式 `--dataset/--corpus/--output`，默认值仍指向旧 v2 数据和旧输出，禁止不带参数运行。

**模型探针状态更新（2026-09-27）**：已在用户明确授权后，对54个已审核节点运行一次探索性模型预测；唯一 pending 项未发送。配对审计虽与当前 AI 角色审核标签54/54一致，但 validation 只有4个 AND、3个 OR、4个 unknown，且仅9个来源簇；这不是独立真人 Gold，也不足以证明概率校准、跨来源泛化或生产阈值。预测仅标作 `uncalibrated_model_estimate_not_event_probability`，不可送入运行时放行或自动建树。后续若要再调用模型，必须明确新实验目的并写入全新输出文件；当前优先补充独立来源、边界/困难样本及标签复核，不因本次全对而选择阈值。

审计即使显示 `ready_for_policy_review`，也只说明来源、标签、预测和切分字段齐备；不表示概率已校准、阈值已选定或可用于运行时。当前测试集在 scope type 与 gate 类别间存在混杂，需在报告中分层呈现结果，不得只依据总体 Brier/Top-1 选择生产策略。

#### 首次节点级概率探针结果（2026-09-26）

历史探针：原始 57 个请求都返回结构有效；曾报告模型 Top-1 与 v1 AI 标签 `57/57` 一致，并计算 Brier `0.00084`、Log-loss `0.00817`、ECE `0.00789`。但由于三条 event-scope OR 标签污染，所有这些配对指标均标记为 **superseded / invalid_for_scope_accuracy_or_calibration**，只能保留原始探针供审计，不能对外引用为模型门识别成绩。

即使忽略标签污染，这些历史分数也不是概率校准证明：来源是 AI 角色审核、样本少、scope/class 混杂，探针提示还要求缺少直接门证据时偏向 unknown。现阶段只能说明旧提示在旧样本上的输出形式，不得拟合可泛化校准器、选生产阈值或接受生产树。后续必须先补正候选范围、复核AI角色标签并重建同scope样本，再按来源簇独立验证。

节点级审计需传入评审集、同一版本模型概率、按 `source_cluster_id` 的划分映射和真实原文 corpus；CLI 参数为 `--gold`、`--predictions`、`--split-assignments`、`--source-corpus`。截至 2026-09-27，v5 已有配对探索预测并通过身份/证据审计，但审核集仍是 AI 角色标签、validation 仅9个来源簇，因此只报告描述性指标，不拟合校准器、不报告已校准的概率质量。

节点级审计测试：

```powershell
python -m unittest evaluation.quality_eval.test_fta_gate_node_confidence_audit -v
```

#### A01631 分层证据复核

子智能体独立只读核对原文后，A01631 的候选表示有明确证据边界：配置组内 AND 由 `[246,325)` 直接支持；`The following configurations can result in this message:` `[189,245)` 支持该配置可能导致消息的有向因果关系；单条原文配置不支持事件顶层多个原因集合的 AND/OR，顶层仍是 `unknown`。offset 是解码后 `input_text` 的 Python 字符索引、左闭右开，非字节偏移。这个复核是 AI 结果，不是真人专家签署，也不更改命名专家 Gold。

对子项证据跨度完整覆盖的检查是当前 S210 v1 的保守**位置绑定策略**，不是所有来源都必须满足的普遍语义定律。语义门禁仍要求原文直接表达该 scope 下 child 之间的 AND/OR；精确跨度覆盖本身不能证明语义。A01631 的完整配置句正好同时含两个子项和 `and`，适用于这条样本。遇到分散的子项证据或单独关系句时，v1 可以阻断并留 `unknown`；要放宽需先引入显式 scope/evidence 关系，而不能退回“引文只在整条记录范围内”这种宽松包络绑定。

### 局部门 unknown 样本补充（F30017）

2026-09-26，用户授权的独立 AI 审核角色从公开语料中识别出 F30017 下两个可区分的设备作用域原因组。它们不是两个新故障，也不是正式 Gold；两组来自同一条语料记录和同一段原文，因此统计独立校准簇时只能计为 **1 个 fault/source cluster**。

语料文件 SHA256 为 `b42535d37ae27b63ba0048c88e947916e846da53e1bf18b3e5825c1853c1f483`；下列 11 个 quote 均由主 agent 对当前 JSONL 的 Unicode `[start,end)` 切片重新核验，11/11 精确匹配：

| 局部作用域 | 直接原因子项 | 当前审核判断 |
| --- | --- | --- |
| `For infeed units, the following applies:` `[315,355)` | 控制环参数化不正确 `[358,407)`；进线负载过高 `[410,441)`；线路电抗器缺失/型号错误 `[444,487)`；功率单元故障 `[490,511)` | `unknown`：标题限定设备适用范围，未声明四项原因之间为 AND 或 OR |
| `The following applies to Motor Modules:` `[512,551)` | 控制环参数化不正确 `[554,603)`；电机或功率电缆故障 `[606,648)`；功率电缆长度超限 `[651,706)`；电机负载过高 `[709,728)`；功率单元故障 `[731,752)` | `unknown`：标题限定设备适用范围，未声明五项原因之间为 AND 或 OR |

子项 `fault in the motor or in the power cables` 内的 `or` 只表达该单个子项的内部替代关系，不能据此推断整个同级列表是 OR。当前可记录两个作用域级的保守审核结论，但不能用于拟合或选择置信度阈值：样本只有一个独立故障/原文簇，且尚无与这两个稳定作用域键配对的模型概率。节点级校准还需 `gate_node_id + scope_type + source digest + exact anchor`，并按故障/来源簇整体切分；unknown 类要进入独立验证集，必须再找不同 fault/source cluster 的 unknown 样本。

### 局部门 unknown 样本补充（F30027）

全语料只读筛查另找到 F30027 的“预充电电阻过热”局部原因组。AI 审核判断为 `unknown`：四条分别描述了导致该中间事件的条件，但原文没有说明四项之间是 OR、AND 或其他关系。该作用域与已有 F30027 局部 OR 节点（`The DC link has either a ground fault or a short-circuit.`）不同，也不是事件级门判断。

公开语料 SHA256 仍为 `b42535d37ae27b63ba0048c88e947916e846da53e1bf18b3e5825c1853c1f483`。主 agent 已验证中间事件表述 `[430,470)` 及四条完整原因跨度 `[430,531)`、`[535,615)`、`[619,769)`、`[773,908)` 均精确回切，5/5 匹配。短语 `The precharging resistors are overheated` 在四个原因句中重复出现，因此不能仅凭短语自动定位作用域；审核范围以这四个已定位子项组成的连续原文组为准。该例为一个新的 fault/source cluster。加上 F30017 后，当前局部门 unknown 候选共 3 个 scope node、2 个独立 fault/source cluster（F30017 两节点、F30027 一节点）；尚无配对模型概率，不能用于阈值拟合或独立验证。

### F31120 条件性故障模式负例

用户已明确确认：F31120 的 8 条 r0949 位说明可以保留为文档定义的条件性故障模式，但没有本次设备实际 r0949 读数时，不能据此确认哪种模式命中，也不能因列出多个模式而推出事件门 OR。当前全量 AI 审核 artifact 将该事件门记录为 `unknown`，理由是缺少设备实际故障值且原文没有直接给出八种模式对顶事件的 AND/OR 组合关系。主 agent 对照当前公开语料 SHA256 `b42535d37ae27b63ba0048c88e947916e846da53e1bf18b3e5825c1853c1f483`，将 artifact 中 8 个候选证据跨度逐条回切，8/8 精确匹配。此例是门判定的保守弃判样本，不代表八个枚举文本可以直接当成一组完整、同级、当前已激活的 FTA 叶节点。

六条具名专家 Gold 的历史探针可复跑（会调用配置的模型服务；只读 Gold/公开原文，并拒绝覆盖既有输出）。它与上述 57 节点 AI 审核集探针是两份独立任务，不可混合样本键或来源声称：

```powershell
python evaluation/quality_eval/public_sources/run_fta_gate_confidence_probe.py
```

## 递归候选合同 v3 实施记录（2026-09-26）

本轮在原候选 FTA owner 文件中实施：候选层自有递归合同，不把抽取事实改造成 FTA 层级，也不把审核后 graph contract 冒充未审核候选。用户已确认源码归属；A01631 的层级处理采用原文证据支持的配置组内 AND、`may_cause` 边与事件根 unknown，且仅作为候选 Preview。

- 每个**内部门节点**独立保存稳定 `gate_node_id`、`scope_type`、门型与 `AND/OR/unknown` 概率、策略/阈值快照、该作用域的直接门证据、scope 锚点、child IDs、原因集合完整性及判定理由；`gate_node_id` 由故障身份、原文摘要、scope 类型及位置确定，不依赖模型自选 ID。
- 每个**叶事件**只持有自己的精确原文证据，不拥有 gate/children。复合条件先拆成有层级的组与叶项，不能将一个抽取 cause 字符串强行变成单个 FTA 叶节点。
- **因果边与逻辑门分离**：`causes` 是有方向、带自身关系证据的边；AND/OR 是多个子事件输入同一逻辑节点的关系。A01631 配置组到报警可由因果边表达；配置组内 AND 单独建门，事件顶层 OR 因原文缺少直接门跨度而保持 unknown。
- **unknown 与候选生命周期分离**：门节点可为 unknown；若节点身份、证据、作用域和原因集合可完整审阅，可保留为 review candidate/preview，但绝不把 unknown 转成 AND/OR。若叶证据、scope 或 child set 无法核验，则候选整体 blocked 并保留局部结构与 blocker。合同 v3 增加 `not_applicable`：只接受单一且声明完整、叶项归一化的 child，不要求无意义的 AND/OR 概率；完整性不足时仍保留 `unknown`。该状态用于区分“不适用”和“尚不能判断”，不表示来源完整性已由机器证明。
- **证据绑定**应校验 extraction/record 身份、原文摘要、`source_id`、`[start,end)` 与 quote 精确切片；门证据须与该 node scope 一致，不能仅用当前“最小到最大跨度包络”判定属于记录。模型不能仅凭自行生成的 quote 建立证据；应引用已有证据 ID，或由受控 binder 以精确且无歧义位置绑定。
- 2026-09-26 运行时反例曾证明记录包络不够严格。当前树输出 v4 要求唯一精确 quote，并校验每个 gate 的 scope 同时包含输出节点与 child 节点证据；gate 证据必须位于该 scope 内。重复节点/门/关系引文不会自动定位；节点/作用域错误会让树 blocked，逻辑证据缺失或概率不足会保留该局部 gate unknown。跨度校验仍不能证明语义蕴含，仍需独立审核和置信度校准。
- **校准单位**是 gate node/scope，不是 `fault_code`。样本身份至少含稳定 `gate_node_id`、`scope_type`、source digest 与 scope 锚点；同一 fault 下所有相关层级节点、重复来源证据簇必须整体分配至 calibration 或 validation，防止泄漏。标签冲突需隔离，不自动覆盖 Gold 或多数表决。
- `fta_graph_contract` 只作为审核后投影形状参考：其审核 provenance / 有门要求不能用于未审核候选，且不负责拿原文做精确切片核验。候选经审核后再映射过去。

已通过回归覆盖：A01631 混合层级/顶层 unknown；另一嵌套样例的局部 AND 与根 OR 各自持有独立概率与证据；单一完整归一化 child 的 `not_applicable`；单一但不完整 child 仍为 `unknown` 并保留模型分布；缺失原因映射、重复 node/gate quote、gate quote 越界、置信度不足、无策略及模型合同无效。待补能力：基于正式节点审核集的概率校准与来源簇划分；真实设备发生概率输入和应用层调用；在线模型/真实抽取端到端验证。

## 故障事件发生概率

发生概率与门类型置信度是不同概念。`check_event_probability_consistency()` 只在门结构已有确认 ID、门为 AND/OR、事件概率具备相同来源/观测窗口/样本数、父子观测范围一致，且事件独立性声明带有审核证据 ID 时运行。当前模块只要求该 ID 非空，不负责查询或验证其审批状态；调用方必须保证它确实指向有效审核记录：

- AND：`P(parent) = product(P(children))`
- OR：`P(parent) = 1 - product(1 - P(children))`

结果只报告一致 / 不一致 / 不可评估，并始终 `may_change_gate=false`。相关事件、没有独立性审核引用、不同概率数据源/观测窗口、样本量不匹配或结构未确认时不套用独立公式。概率一致性不能证明 AND/OR，也不能反过来覆盖原文逻辑证据。

截至 2026-09-26 的调用点审计：`backend-python/fta/event_probability_consistency.py` 仅定义该函数，仓库非测试代码没有调用方；当前测试通过显式传入 `gate_structure_confirmed=True` 覆盖计算分支。因此现有证据只证明**函数级**“未确认时不计算”和“结果不改变门型”，尚未证明**应用链路级**只会把已接受/已审核的结构传进来。候选 FTA 应用服务当前也未接入概率核验。后续接线必须由核心应用层从经过门证据与置信度策略接受的具体节点状态生成确认输入，不能由 API、脚本或调用者任意填一个布尔值；在递归节点合同和置信度校准闭合前，不应把概率校验宣称为端到端完成。

另外，对 `evaluation/` 与 `backend-python/` 当前 JSON/JSONL 的字段检索没有找到真实的事件发生概率观测数据；现有概率单测使用的是计算夹具，不是设备统计。故真实 S210 概率一致性试验目前缺少输入数据。不得用候选原因出现次数、模型置信度或手册中的故障值替代事件发生概率；后续需有同来源、同观测窗口/样本数的父子事件观测，以及独立性审核证据，才可运行该检查。

## 旧单层合同的持久化边界审计（历史）

旧单层实现曾以全量后端单测 232 项通过，但其平面 gate 不足以表达 A01631 分层语义；这些数字是历史验收结果，不代表当前 v4。`CandidateFtaApplicationService` 仍只在内存中组合抽取结果与逐记录候选；源码中没有 API 入口或数据库保存调用，失败提议保留抽取结果供重试。

当前结果携带 `reviewer_provenance="user_authorized_ai_expert_role"`，同时强制 `human_reviewed=false`、`confidence_semantics="uncalibrated_model_estimate"`、`fta_ready=false`、`production_ready=false`。AI 提议按用户授权角色可进入内部复核流程，但该 provenance 不代表具名真人审核、Gold 批准或概率校准。

v3 针对性回归命令：

```powershell
python -m unittest backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_recursive_candidate_fta_extraction_service backend-python.tests.test_candidate_fta_application_service -v
python -m unittest discover -s backend-python/tests -q
python -m unittest evaluation.quality_eval.test_fta_gate_confidence_calibration evaluation.quality_eval.test_fta_gate_node_confidence_audit -q
```

历史验证快照：当时完整后端回归为 228 项通过，门置信度评估器另有 12 项通过。该数字只记录旧单层合同审计阶段，不代表当前代码状态；当前全后端回归数字以文末最新 F06000 两阶段复核记录为准。上述测试验证合同与离线编排，不代表概率校准或生产就绪。

本次通过的命令：

```powershell
python -m unittest backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_candidate_fta_application_service backend-python.tests.test_event_probability_consistency -v
```

API 调用点检索：

```powershell
rg -n "CandidateFtaApplicationService|CandidateFtaExtractionService|candidate_fta_generation_result|event_probability_consistency" backend-python/app backend-python/fta backend-python/tests
```

结果仅在候选服务、概率函数和测试中发现定义/调用；`backend-python/app` 未发现候选 API 接线。此处是基于仓库当前检索结果的静态审计，不等价于端到端部署证明。

## 范围与停止条件

- 不改 Gold、不写数据库、不接 API、不自动将候选树标记为正式树。
- v2 已可递归表达节点层级，但仍是候选生成器：不是正式 Gold，也未接生产 API/数据库。
- 本阶段闭环验收还需：基于规范化 gate-node Gold 取得配对模型概率，按 source cluster 做独立 calibration/validation；确认 `not_applicable` 与 `unknown` 的标注定义；用独立样本评估置信策略的风险/覆盖，而非手设生产阈值；之后才可将已审核结构与真实事件概率接入一致性核验。真实模型与 `FaultExtractor` 已在 F06000 单条样例完成在线候选 Preview（含保守弃判），但仍需独立样本覆盖、经验证策略下的正向门接受路径及更广的端到端回归。真实设备事件概率观测数据当前缺失。
- 只有证据、完整原因集合和经审核置信度策略都满足时才提出 AND/OR；否则弃判。概率核验不改变门。

### 目标完成门禁

只有以下条件全部有当前证据，才可结束本阶段目标：

1. 真实原文经 `FaultExtractor` 生成的原因结构保留逻辑作用域/必要层级；每个建树叶节点都有可回切的原文出处。原文压缩、位置不唯一或证据不能支持该节点时必须阻断或保持 `unknown`。
2. 门判断按具体逻辑节点输出 AND/OR/unknown 及模型置信度；AND/OR 必须有该节点作用域内的直接原文依据。模型分数经审核样本校准，并有独立验证数据和经审定的错误风险/接受覆盖目标；样本不足时不选择阈值。
3. 至少一条真实原文路径通过“抽取 → 证据绑定 → 节点门判断/弃判 → 候选 Preview合同验证”，同时覆盖正向门和保守弃判；Preview 保留门证据、原因集合状态和来源，不转正式 Gold。
4. 事件发生概率只对已确认结构做同来源/同观测条件下的一致性检查；依赖性或证据未核实时不套独立公式；不一致只能报告，绝不改写门型。
5. 回归测试覆盖缺证、原因集合不全、层级不明、置信度不足、重复引文和概率数据不匹配；最终状态仍明确 `formal_gold_mutated=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`。

当前整体目标仍未通过门禁。递归候选合同、A01631 的固定响应端到端编排回归、A01631 组内 AND + `may_cause` + 顶层 unknown、节点级独立概率/证据回归，以及 v8 范围对账后的事件级审核材料均已生成。事件级 v8 为37条已审核门型（AND 0、OR 1、unknown 36）、2条 `not_applicable`、0条 pending；当前门节点 v6 为55个节点（55 reviewed、0 pending），标签 AND 12、OR 17、unknown 26；另有3个故障值模式集合和2个不适用范围留在非门节点附件。审核为用户授权 AI 角色复核，不是真人专家签署、非正式 Gold，且未回查手册原件。v6 仅将 F30021-C04 证据定位绑定到 `[332,372)`，门型保持 unknown；此前 v5 的54条配对 DeepSeek 探索预测仅覆盖旧版节点，不能冒充 v6 的55条预测成绩。validation 当前增加至12个节点，仍是少量同一公开手册样本；没有选门策略或已校准阈值，不能作为校准或泛化结论。剩余工作为扩充独立来源且有充分 AND/OR/unknown 覆盖的审核/验证样本；分 scope 做重复独立评估并评估风险/覆盖；在样本充分后才拟合/验证校准策略；扩大真实模型与 `FaultExtractor` 联合 Preview 覆盖，并验证策略通过后的正向门接受路径；打通真实设备事件发生概率链路。F06000 单条真实原文在线 Preview 已验证嵌套 scope、精确证据和保守弃判，不等于上述覆盖门禁完成。事件概率输入仍未接入候选应用服务。所有候选只在内存生成，正式 Gold/数据库未改，`tree_generation_authorized=false`、`fta_ready=false`、`production_ready=false`。

### 2026-10-07：内部 occurrence-locator review overlay（P2e）

后端现提供显式 `EvidenceOccurrenceLocatorReview` 与 `EvidenceLocatorReviewResolver`，允许审核者把重复短语定位到经原文 SHA、record/field/index、精确偏移和唯一 scope 校验的 occurrence。该 overlay 随 CauseDispositionBatch 和 CandidateFtaTree 序列化，保存 review id、provenance、真人/非真人标记、`formal_gold=false` 与理由。它只证明位置绑定，不证明原因是独立上游事件、不证明事件身份/层级/完整 child 集合，也不提供 AND/OR 证据。

模型必须逐字使用 locator 对应的原始抽取 evidence quote；没有 locator 时，重复引用仍 unresolved；过期/越界/非唯一定位、扩写引文都 fail-closed。locator 不会自动回填历史响应或数据库。该入口目前只存在于后端内部服务参数中，未接公开 API 或持久化数据库，也不改变模型请求数。详见[当前状态审计 P2e](current-state-audit.md)和[manifest v52](../evaluation/quality_eval/fta_baseline_manifest_v52.json)。F30021 原始 v5 运行仍 blocked；要证明新运行的语义行为须另行授权，且不得覆盖历史运行。`fta_ready=false`、`production_ready=false` 保持。

## 验证命令

```powershell
python -m unittest backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_candidate_fta_application_service backend-python.tests.test_event_probability_consistency evaluation.quality_eval.test_fta_gate_confidence_calibration evaluation.quality_eval.test_fta_gate_node_confidence_audit -v
```

## S120/S150 整本来源留出（2026-09-27，进行中）

为验证门节点处理能否迁移到另一份 Siemens 手册，已下载官方《SINAMICS S120/S150 List Manual, 11/2023》，本地文件为 `C:\Users\爹\Downloads\SINAMICS_S120_S150_List_Manual_11-2023_EN.pdf`，PDF SHA-256=`f7684038621ae9faaedbed1780e23c48775c19d76ae0fbd0adce268d69f489f4`；来源：[Siemens 官方缓存 PDF](https://cache.industry.siemens.com/dl/files/046/109827046/att_1164654/v1/S120_S150_list_man_1123_en-US.pdf?download=true)，[官方支持条目](https://support.industry.siemens.com/cs/ww/en/view/109827046)。仅处理 PDF 第 2579–3352 页的“4.2 List of faults and alarms”。原 PDF 保留在本机，不随代码提交或分发；复用/再分发需另行核对 Siemens 条款。

当前权威抽取产物：

- [整本来源留出语料 v2](../evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.jsonl)
- [语料清单 v2](../evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.manifest.json)
- [PDF 抽取器](../evaluation/quality_eval/public_sources/build_siemens_s120_s150_fault_corpus_holdout_v1.py)
- [抽取器测试](../evaluation/quality_eval/test_build_siemens_s120_s150_fault_corpus_holdout_v1.py)

v2 有 1,532 条记录、1,443 个唯一故障码（F 884、A 628、N 20）和 1,575 段 parser 提取的 Cause 区间。记录身份会区分同一故障码在不同页或同页重复出现的条目。逐条以源 PDF 重建抽取文本后，1,532 个记录区间、PDF 页码映射和 cause quote 字符偏移均通过精确回切检查；测试 3 项通过。v1 是早期抽取快照，Cause 字段边界没有保留 `Cause` 下嵌套的 `Fault value` 子段；**所有后续工作只使用 v2**。

这份 S120/S150 手册作为一个完整外部来源簇留出：不与 S210 混合切分，不用于提示词/模型/阈值选择。它是另一产品系列/版本和另一份文档，不是跨行业验证；1,532 条记录不能冒充 1,532 个独立来源簇。语法线索计数（`either/or` 34、`both/and` 13、`if/and` 36、“one of following”17、至少两条列表 241）有交叠且会包含诊断值、状态描述或普通连接词，只能筛候选，**不是 AND/OR 标签**；列表、多原因、工程常识或单词 `and/or` 本身都不能自动定门型。

当前已完成官方来源下载、章节语料抽取、位置审计、S210 重叠审计、首批 4 条候选的 AI 角色只读范围审核，以及 `deepseek-flash` 固定门节点概率探针。探针仅调用 5 次，5/5 成功；Top gate 与 AI 角色标签描述性一致 5/5，5/5 个模型提出的 AND/OR 门引文均精确且唯一地落在固定作用域内。样本仅 4 个故障码、1 个手册来源簇，且 F35400 曾在此前过程材料中出现；这不是盲测准确率、跨来源泛化成绩或概率校准。未选择阈值、未做概率校准，未修改 Gold、数据库或生产流程。AI 角色审核须明确标为 AI、非真人专家签署。仍保持 `formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`。没有直接门证据或作用域不完整时保持 `unknown`。

### S120/S150 与 S210 重叠审计（2026-09-27）

在建立第二手册的门节点审核集前，先将 S120/S150 v2 与既有 S210 原始公开语料及 S210 v5 AI 角色门节点审核集做只读重叠审计：[审计说明](../evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v3_2026-09-27.md)、[逐条 JSON 明细](../evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v3_2026-09-27.json)、[可复跑审计器](../evaluation/quality_eval/public_sources/audit_siemens_s120_s150_holdout_overlap_v1.py)。

核对结果：S120/S150 的 1,443 个唯一故障码中有 **250 个**也出现在 S210；1,532 条 S120/S150 记录中有 **290 条**同码。按完整解析 `causes_text`（仅 NFKC、大小写和空白归一，保留标点）分层：70 条同码且文本完全重合，144 条同码且存在至少 32 字符的包含重合，另有 76 条同码但未发现上述整段文本重合；另外 4 条虽然故障码未在 S210 出现，但完整解析文本与其他 S210 故障码重合。剩余 1,238 条没有同码或完整文本精确重合；这只是筛查分层，不等于语义独立样本。

再按完整 causes_text 做跨所有故障码的局部包含筛查（较短字符串至少 32 字符），共 **219 条**记录出现可能的局部文本重合；这是词面筛查，不等同于语义重复判定。S210 v5 中 54 个已审核门节点有 52 个节点的故障码也出现在 S120/S150；其中 **34 个节点的 scope 锚点原句在 S120/S150 同码记录中逐字重现**。这是明确的潜在标签/文本泄漏风险，不能把对应记录计入未见门证据泛化成绩；同码本身是身份重叠警告，锚点重现才是直接文本重叠信号。该审计没有生成标签，也没有证明剩余样本已语义去重。

因此，S120/S150 仍可作为“另一手册/版本来源留出”检查解析和证据定位，但**不能把 1,532 条当成独立泛化样本**。后续任何门节点开发/评测都必须保留 `source_cluster_id` 整本分组，并将以下用途分开报告：同码/同文本一致性压力测试；未见故障码探索子集；真正独立校准/验证（当前尚无足够独立来源簇，不能宣称）。不得按记录随机切分，也不以本审计拟合模型或阈值。门型依旧只由作用域内直接证据支持；证据不够则 `unknown`。

首批 4 条 AI 角色盲审候选包：[候选包 v2](../evaluation/quality_eval/runs/siemens_s120_s150_gate_review_candidate_bundle_v2_2026-09-27.json)、[候选包生成器](../evaluation/quality_eval/public_sources/build_siemens_s120_s150_gate_review_candidate_bundle_v1.py)，已完成只读范围审核；结果见[AI 角色审核试点 v1](../evaluation/quality_eval/runs/siemens_s120_s150_gate_node_ai_role_review_pilot_v1_2026-09-27.json)及[校验测试](../evaluation/quality_eval/public_sources/test_siemens_s120_s150_gate_node_ai_role_review_pilot_v1.py)。4 个故障记录共 5 个门节点：1 个 AND、4 个 OR（其中 F06000 的一个 OR 是嵌套在第 9 项原因内的局部门）；引用位置均已精确回切且唯一。F06000 的嵌套门没有被摊平成同层原因，F08702 的“See also”诊断信息没有混入门作用域。该审核明确是 AI 角色试点，不是真人专家签署、正式 Gold、独立来源簇验证或概率校准；候选包仍属于单一 S120/S150 手册来源簇，且 F35400 曾在此前过程材料中出现，不能视为完全盲审。重叠审计、候选包生成器、审核结果校验及语料抽取相关测试共 13 项通过；PDF 复抽和 1,575 个 cause 跨度回切通过。未调用外部模型 API、未写 Gold/数据库，也未改变 FTA/生产门禁。若后续要使用冻结的 DeepSeek 探针，仍须另行取得该 API 调用授权。

### 固定模型探针结果补记（2026-09-27）

本段取代本节早先“尚未运行固定模型探针 / 未调用外部模型 API / 仍待授权”的过期状态描述。用户授权后，已用 `deepseek-flash`、`temperature=0` 对 5 个已审核 scope 各调用一次；5/5 请求成功。Top gate 与 AI 角色审核标签描述性一致 5/5；模型所提 AND/OR 引文 5/5 均精确且唯一地位于作用域内。逐项预测见[探针原始结果](../evaluation/quality_eval/runs/siemens_s120_s150_gate_node_confidence_probe_v1_2026-09-27.json)，配对与证据对账见[试点对照报告](../evaluation/quality_eval/runs/siemens_s120_s150_gate_probe_pilot_audit_v1_2026-09-27.json)。

该结果只有 5 个门节点、4 个故障码、1 个 S120/S150 来源簇，且 F35400 曾在先前过程材料出现；它不是盲测准确率、独立来源泛化或概率校准。没有选阈值，没有写正式 Gold/数据库，也没有改变 `fta_ready=false`、`production_ready=false`。仅此探针调用了 5 次外部模型请求；本轮关联的 6 个测试模块共 21 项测试通过。

### FAA 外部图示门型分类探针（2026-09-27）

用户要求实测并检查当前缺陷后，使用本机留存的 FAA《Guide to Reusable Launch and Reentry Vehicle Reliability Analysis》官方 PDF，对图 A.4-1、B.1-3、B.2-2 中人工转录的 13 个显式门节点运行独立分类探针。模型输入仅含父事件和直接子事件描述，不含图号、PDF 页码或 Gold 门标签；来源和数据范围见[测试夹具](../evaluation/quality_eval/datasets/faa_ast_gate_diagram_external_test_v1.json)，原始逐条输出见[模型测试结果](../evaluation/quality_eval/runs/faa_ast_fta_gate_external_probe_v1_2026-09-27.json)。

结果：`deepseek-flash`、`temperature=0`，13/13 请求成功；13/13 门型正确（Accuracy=1.000、Balanced Accuracy=1.000、Macro-F1=1.000），AND 3/3、OR 10/10；没有弃判，decisive coverage=1.000。Always-OR 基线为 10/13=0.769，因此本样本上模型高 23.1 个百分点。模型自报概率的描述性 multiclass Brier=0.0268，但它**不是校准结果**，不得将自报 0.80–0.97 解释成真实正确概率或生产阈值。

测试过程中发现并修复了评测器字段合同缺陷：预测行原先写 `expected_gate_from_figure`，汇总器读取 `expected_gate`，造成首轮完整调用后在汇总阶段抛出 `KeyError`、没有保存评分文件。加入端到端汇总回归测试后重跑；首轮 13 次请求未形成可用报告，修复后再次运行 13 次并完成保存。当前探针 5 项单测与候选 FTA/置信度相关 44 项项目回归均通过。

**缺陷与证据边界：**

- 13 个节点都来自同一份 FAA 指南（一个来源簇），而且只有 3 个 AND；虽然报告同时给出类别均衡指标，样本仍不足以证明跨来源泛化。
- 样本是从已画出的 FTA 图中转录的父子节点分类任务，不是从原始维修文本抽取因果关系、绑定证据、确定完整原因集合并自动建树的端到端测试。
- 没有 `unknown`、`not_applicable` 或缺证据样本；因此这轮不能验证模型何时应弃判，也不能验证缺证时的保守性。
- 门标签是按公开图示人工转录的外部测试标签，不是项目正式 Gold，也未经本项目领域专家签署；此处只适合作为小规模结构分类 smoke test。
- 虽然 13/13 命中，不能据此设置信心阈值、宣称概率已校准、合并 Gold、写数据库或打开自动/生产建树。

因此，这轮证明的仅是：**当前 DeepSeek 模型在一个极小、单来源、图示已给定的 AND/OR 分类探针上能够全命中；测试器回归正常。** 尚未解决的主要问题仍是独立来源样本不足、unknown/缺证据决策覆盖不足、置信度未校准，以及真实原文到证据化 FTA Preview 的端到端验证缺口。`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false` 均保持。

### S120/S150 原始故障文本到候选 FTA 在线冒烟（2026-09-27）

为检查真实文本链路，而不是再次只测图示分类，使用项目现有 `build_text_extraction_adapter()`、`CandidateFtaApplicationService.generate()` 和 `CandidateFtaExtractionService.propose()`，以 `deepseek-flash`、`temperature=0` 对 S120/S150 2023 List Manual 的 4 条原始记录运行在线开发冒烟：A30079、F06000、F08702、F35400。输入来自本地外部留出语料；本次不输入既有审核标签，也不计正式准确率。逐样本提取、节点、门提议与引用数据见[原始运行产物](../evaluation/quality_eval/runs/siemens_s120_s150_real_source_candidate_fta_smoke_v1_2026-09-27.json)。

本次 4/4 抽取成功、4/4 产生可复核的候选 Preview；抽取 span 及树节点/作用域引用均能按原文 offset 精确回切且引用唯一。A30079 的“simultaneously satisfied”被拆为两个有原文证据的条件；F35400 的“at least one/or”和 F08702 的“either/or”也分别拆出候选子节点。对已有 S120/S150 AI 角色审核的 4 个同作用域参考标签，模型 Top-probability 类别描述性匹配 4/4；该参考不是人类专家 Gold，且本次记录来自单一 S120/S150 文档来源簇，因此不能声称独立准确率。

**首轮发现的缺陷/限制：**

1. F06000 第 9 项原文“either a ground fault or a short-circuit”在首轮候选中仍作为一个叶原因，没有生成其内部局部 OR 节点。此问题随后作为嵌套结构回归样例修复，详情见下方“F06000 两阶段结构复核”。
2. A30079、F06000 外层 OR、F08702 与 F35400 的模型概率偏向均很明确，但所有对应 AND/OR `gate` 最终保持 `unknown`，阻断理由为 `gate_confidence_policy_unavailable`。这符合当前“无校准策略不接受门型”的 fail-closed 合同；也说明现在没有可用策略把模型概率转成接受决策，不能宣称在线门型决策闭环完成。
3. F06000 顶事件只有一个直接 Cause 子事件，系统保留根门 `unknown`，未把中间层 10 项 OR 错升为顶层门。这个弃判是正确的保守行为，不是漏掉顶层 OR 的证据。

本次在线调用共 4 次抽取、4 次候选提议；所有候选均保持待复核状态。该报告及语料只保存在本地，未改正式 Gold、数据库或生产配置；`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false` 不变。

### F06000 两阶段结构复核（2026-09-27）

针对上一轮发现的嵌套 scope 丢失，候选服务改成两个相互独立的模型职责：第一阶段只分解原文事件层级和作用域；第二阶段只对固定的 scope 评估门型及额外关系。宿主验证 cause 索引覆盖、scope ID 一对一、节点/门/关系引文的唯一原文跨度及父子引用；重复或越界证据仍阻断，不以模型自报概率绕过。

对同一条 S120/S150 公开原文 F06000 做了三次有版本记录的开发尝试：

| 运行 | 结果 | 发现 |
| --- | --- | --- |
| [v1](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_nested_scope_candidate_fta_v1_2026-09-27.json) | `blocked` | 结构阶段把第9项留成单一原因叶；另有不精确节点/作用域引用。 |
| [v2](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_nested_scope_candidate_fta_v2_2026-09-27.json) | `blocked` | 在结构提示增加逐项检查与嵌套示例后，已正确输出外层10项 scope 和第9项内部2子项 OR scope；17条引用精确且唯一。但门评估阶段把外层列表的每个 child 又重复输出成独立 `causes` 边，关系 scope 未同时覆盖端点，主机按合同阻断。 |
| [v3](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_nested_scope_candidate_fta_v3_2026-09-27.json) | `proposed` / `candidate_ready_for_review` | 第二阶段调整为不复制已由 gate 父子结构表达的原因边后，树级 blocker=0、额外 relation=0。外层10个直接原因中，第9项是中间组；该组的两个直接子项为 ground fault 和 short-circuit。17条节点/作用域/门证据全部精确且唯一回切原文。 |

v3 的两个作用域门标签仍为 `unknown`：外层模型分布为 OR `0.98`，内层为 OR `0.99`，但没有已验证的置信策略可将概率接受为确定门型。**不得把这两个分数解释为校准概率、工程故障概率或专家审核结论。** 因此这次只证明单条输入上的嵌套结构分解、关系克制和证据绑定可以跑通，不证明抽取/建树泛化准确，也不改变 `fta_ready=false`、`production_ready=false`。

本次三轮共进行7次模型请求：v1、v2 各为抽取+结构+评估3次；v3复用了v2的抽取结果与结构响应，仅重新评估关系/门型1次。未写入 Gold、数据库或生产树。针对性候选服务测试24项通过；全后端 `python -m unittest discover -s backend-python/tests -v` 共232项通过。

### v5 门节点现有分数的阈值敏感性检查（2026-09-27，只读）

为判断现有样本能否支持下一步门接受策略，按来源簇固定切分，对 v5 的 54 个已审核节点及配对模型预测运行离线风险/覆盖审计。仅将 Top 类别为 AND/OR、Top 概率达到诊断阈值且 Top-1 与次高类 margin ≥0.50 的节点视为“假设接受”；unknown 预测始终弃判。`empirical_risk` 定义为已接受节点中门标签与审核标签不一致的比例；标签为 unknown、但被预测为 AND/OR 的情况计作错误接受。阈值仅用于敏感性报告，不自动选策略。

| 最低 Top 概率 | calibration：接受/覆盖（43节点，38簇） | calibration：错误接受 | validation：接受/覆盖（11节点，9簇） | validation：错误接受 |
| ---: | ---: | ---: | ---: | ---: |
| 0.80 | 22 / 51.2% | 0/22 | 7 / 63.6% | 0/7 |
| 0.90 | 21 / 48.8% | 0/21 | 7 / 63.6% | 0/7 |
| 0.95 | 18 / 41.9% | 0/18 | 7 / 63.6% | 0/7 |
| 0.98 | 13 / 30.2% | 0/13 | 7 / 63.6% | 0/7 |
| 0.99 | 13 / 30.2% | 0/13 | 5 / 45.5% | 0/5 |

审计实现还收紧了一处计分边界：split 指标与风险/覆盖只使用身份字段完全匹配的 Gold—预测配对；身份不匹配的预测不进入分数，并继续列为 blocker。

这只是阈值敏感性，不是校准结果；表中 0 个观察到的错误不代表真实错误风险为 0。验证组仅11个节点/9个来源簇，且标签来自用户授权的 AI 专家角色审核，不能据此证明真实门型、估计足够低的错误风险或选出生产阈值。特别是 F06000 外层 OR 估计 0.98、内层 OR 估计 0.99；不能因为某个候选阈值恰好放行内层而把该阈值写入策略。当前仍需扩充独立来源/场景的审核样本并先审定可接受风险与覆盖目标；两层仍按现行 fail-closed 规则为 `unknown`。风险/覆盖指标由 `fta_gate_node_confidence_audit.py` 离线生成，命令见“验证命令”及节点级置信度审计命令；策略仍为 `gate_policy_selected=false`。

### 多来源公开图示门型探针 v1（2026-09-27）

为避免仅有 FAA 单来源结果，新增 NASA《Fault Tree Handbook with Aerospace Applications》、NRC NUREG-0492、以及 NASA SSRI 托管的 HERMES CubeSat 大学项目论文三个文档簇的 5 个明确 AND/OR 图示样本。DeepSeek Flash temperature=0，5/5 请求成功、5/5 与图示门标签一致（AND 2、OR 3）；模型未弃判。离线测试复跑包含 FAA 既有探针后共 9 项通过，三份 PDF SHA-256 与夹具一致。原始结果见[多来源运行报告](../evaluation/quality_eval/runs/fta_gate_multisource_external_probe_v1_2026-09-27.md)、[JSON 结果](../evaluation/quality_eval/runs/fta_gate_multisource_external_probe_v1_2026-09-27.json)、[样本夹具](../evaluation/quality_eval/datasets/fta_gate_multisource_diagram_external_test_v1.json)及[探针脚本](../evaluation/quality_eval/public_sources/probe_multisource_fta_gate_external_v1.py)。

该成绩仅是 5 个节点、3 份文档的小规模图示分类 smoke test，不是独立校准/泛化估计；HERMES 引用 NASA 手册，且同树的两个节点相关。样本都已知为 AND/OR，没有 `unknown` 或证据不足标签。**图示真值不等同于源故障文本足以直接证明门型**，因此本轮不能验收证据约束建树、弃判能力或自动阈值；模型自报概率也不可用于生产放行。排除的抽象门型、文字标签泄漏和重复示例已记录在夹具中。没有改变正式 Gold、数据库、`gate_policy_selected=false`、`fta_ready=false` 或 `production_ready=false`。

### S210 门节点盲化提示消融（2026-09-27）

针对 v5 结果中的类别/作用域混淆，使用来源簇 validation split 重新调用 `deepseek-flash` 11 个节点。验证组为 11 节点、9 个来源簇（AND 4、OR 3、unknown 4）。本轮提示移除了 `fault_code`、`scope_type` 与原 child ID，仅保留固定原文作用域、子项文本、精确子项证据及既有 evidence-first 判断要求；审核标签从未传给模型。逐条结果见[盲化消融运行 artifact](../evaluation/quality_eval/runs/siemens_s210_gate_blind_scope_ablation_validation_v1_2026-09-27.json)。

盲化后 Top-1 标签为 11/11 匹配；4/4 `unknown` 仍判为 `unknown`，unknown 平均自报分数为 1.0；7 个 AND/OR 预测的门证据均可唯一定位在各自 scope 内，4 个 unknown 均未返回门证据。该结果降低了“仅凭 `scope_type` 元数据猜类别”的担忧，但由于只有 11 个节点/9 个来源簇、标签仍由 AI 角色审核、且每节点只做单次模型请求，不能据此宣称专家准确率、概率校准或生产阈值。`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 保持不变。

### 外部原文门证据与 unknown 弃判探针 v1（2026-09-27）

为补上既有公开图示分类测试缺少 `unknown` 的缺口，新增四个跨来源文本样本：NASA 调查摘要、TM 8-630、TM 9-803 各一条“只列可能原因、未明示逻辑门”的 unknown，以及 FAA 历史手册中一条原因短语直接写明 `or` 的 OR 阳性对照。独立 AI 角色复核在模型调用前将三条原因清单定为 `unknown`、将 FAA 原因对定为 OR；此标签不是人类专家签署或正式 Gold。完整的范围、来源哈希、排除理由、逐条结果与限制见[运行报告](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_probe_v1_2026-09-27.md)、[运行 JSON](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_probe_v1_2026-09-27.json)、[输入夹具](../evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_external_test_v1.json)及[探针/测试](../evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py)。

`deepseek-flash`、temperature=0，4/4 请求成功；Top-1 4/4 与 AI 角色审核标签描述性一致。3/3 unknown 均被保留，错误强判为 AND/OR 为 0；唯一 OR 阳性对照正确判 OR，模型引用的门证据精确落在原因作用域中。命中率不能代表可靠泛化：样本仅 4 个文档簇、1 个 OR 阳性、没有 AND 阳性；自报概率未校准，标签不是人类专家 Gold。该探针只证明当前提示对这四条材料表现符合预期，不能证明unknown能力已充分验证。

候选 C（TM 9-808）因独立 AI 复核发现原文父子范围/表格上下文未充分提供而在模型调用前排除。FAA AC 65-15A 已撤销/被新版取代，仅用作历史文本分类对照，不作当前维护建议。此轮没有改 FTA 策略、置信阈值、Gold、数据库或生产 API；`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 保持。针对性 5 项测试及编译检查通过。

来源元数据更正：TM 8-630 的出版月份在本次模型调用后根据美国国会图书馆目录核实为 1944-11。运行 JSON 保留原始夹具摘要；重建原摘要后完全匹配，且修正前后四条模型提示摘要一致，预测结果与来源日期更正无关。详情见运行报告的审计说明。

### 外部原文门证据与 unknown 弃判探针扩展 v2（2026-09-27）

在 v1 的 3 条 unknown + 1 条 OR 文本样例上，新增 NASA TP-2000-209902 图 28 说明中的明确 AND 正例，以及 NASA-TM-104382 “possible causes” 清单（含语法 and）的 unknown 样例。新增范围、逐字引文和 PDF SHA-256 见[扩展夹具](../evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v1.json)；运行详情见[扩展报告](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_probe_v2_2026-09-27.md)和[两条原始模型输出](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v1_2026-09-27.json)。

原文 AND 句明确要求 critical pump failure 与 safety system failure to mitigate 同时发生；unknown 样例仅将电极变化列为 possible causes，and 仅承担列表连接。`deepseek-flash`、temperature=0，本轮对两个新增样例各调用一次，2/2 成功：AND 正例正确、unknown 未被强判；其 decisive quote 精确落在输入证据子串中。与 v1 的四条既有结果合并描述为 6/6 标签一致、4/4 unknown 保留、2/2 已知门型正确、decisive coverage 2/6。这里的合并数是小样本描述性统计，不是可靠准确率估计。

标签由主 AI agent 在模型推理前依据文本直接证据规则给出；不是人类专家 Gold，也没有独立第二审阅者确认。样本仍只有一个 AND 阳性、一个 OR 阳性；模型自报概率未校准。未改变正式 Gold、数据库、门型策略/阈值或 `fta_ready=false` / `production_ready=false`。针对性测试 6 项通过。下一步应增加不同措辞的独立 AND 文本、只在列表语法中出现 and 的 unknown 近邻样例，并继续按原文证据范围核验，而不是据当前小样本打开自动建树。

### 外部原文门证据与 unknown 弃判探针扩展 v3（2026-09-27）

按上一轮的测试方向，新增不同措辞的直接 AND（“必须共同发生”“所有输入均须发生”“所有输入共存”）、明确“任一输入即可”的 OR，以及两个不能从语法 and 或时序共现推断门型的 unknown 近邻样本。输入与来源哈希见[扩展夹具 v2](../evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v2.json)，逐条输出见[运行 JSON](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v2_2026-09-27.json)，完整汇总与限制见[探针报告 v3](../evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_probe_v3_2026-09-27.md)。

`deepseek-flash`、temperature=0，新增样本 6/6 成功且与推理前 AI 角色标签一致：AND 3/3、OR 1/1，unknown 2/2 保留；明确门型引文均精确命中输入证据 4/4，未发生 unknown 强判。合并 v1、扩展 v1 和本轮，共 12/12 标签一致，AND 4/4、OR 2/2、unknown 6/6 保留，6/6 决定性引文精确。累计描述性结果仍是单模型小规模探针，不是人类专家 Gold、独立泛化评估或概率校准。所有自报 Top probability 为 1.0，不能用作门型放行阈值。

本轮未改变正式 Gold、数据库、门型政策、API 或生产状态；`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 均保持。

用户复核确认：Apollo 13 样本中的压力与温度共现不等同于 FTA AND 门，故 `unknown` 标签保持不变；该确认只澄清标注语义，不作为领域专家机理审核或正式 Gold。

### 门型证据消融探针 v1（2026-09-27）

为反向验证模型是否依赖可见逻辑证据，取6个此前已判对的 AND/OR 样本，保持父事件、直接子事件及父事件上下文，移除决定性门型语句与候选集标题后重新请求模型。夹具见[证据消融测试集](../evaluation/quality_eval/datasets/fta_gate_text_evidence_ablation_v1.json)，逐条结果见[运行 JSON](../evaluation/quality_eval/runs/fta_gate_text_evidence_ablation_v1_2026-09-27.json)，范围与限制见[探针报告](../evaluation/quality_eval/runs/fta_gate_text_evidence_ablation_v1_2026-09-27.md)。

`deepseek-flash`、temperature=0，6/6 输出 `unknown`，缺证据时错误强判 AND/OR 为0/6，也均未输出门型引文。与配对原始正例对照，原文门证据存在时的6条正例均正确；移除门证据后6/6弃判。该结果仅说明模型在小规模构造的配对提示下遵守了直接证据要求；不能排除预训练污染，也不是自然分布准确率或专家 Gold。所有自报 Top probability 为1.0，未校准，不用于门策略。

该探针不测试原文抽取、原因集合完整性、递归建树、概率校准或生产接口。未修改 Gold、数据库、门策略及 API，`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 继续保持。

### S210 F30021 原文到候选 FTA Preview（2026-09-27）

使用公开语料 `SIEMENS_S210_2019_F30021` 的原始故障文本，调用当前抽取器与递归候选服务完整运行一次。可复现探针为[脚本](../evaluation/quality_eval/public_sources/probe_s210_f30021_candidate_fta_v1.py)，首次模型输出为[运行 artifact v1](../evaluation/quality_eval/runs/siemens_s210_f30021_candidate_fta_preview_v1_2026-09-27.json)。对 v1 的引文审计发现初版审计器把继承自抽取结果、已有精确 offset 的顶事件引文也要求全局唯一；未重新调用模型，保留 v1 并另生成[更正审计 artifact v1.1](../evaluation/quality_eval/runs/siemens_s210_f30021_candidate_fta_preview_v1_1_2026-09-27.json)。

DeepSeek Flash 共进行3次请求：原文抽取、结构分解、门型评估；请求中没有传入审核标签。抽取器得到1条 F30021 记录和5条 cause 候选，14条抽取证据均能按 offset 精确回切。结构模型建立了两个局部 scope：顶层 `Possible causes` 的4项，以及 `Fault value r0949=0` 下的2项。两个 scope 的最终门都保持 `unknown`，决策原因是没有可用的门型置信策略；模型把 `Possible causes` 列表解释为 OR 的文字只是模型判断，不构成被接受的门标签，也不能据此把列表语法直接当作 OR。

该树最终为 `blocked`，而不是可审核候选：cause index 4（“the hardware DC current monitoring has responded”）仅出现在故障值0解释中，原文没有确认它是顶事件的独立原因，结构阶段将其列为未解决；“short-circuit at the braking resistor”在原文出现两次，分别位于 `[334,371)` 的 Possible causes 项与 `[470,507)` 的故障值0说明。模型为两个节点重复引用了同一短语，宿主没有猜选位置，因此两个节点缺少证据并阻断整棵树。先前 F30021-C04 定位复核只确认了第一处属于 Possible causes scope，不会自动授权把第二处当成另一条 FTA 原因证据。

更正后的审计确认所有已绑定引用 offset 精确；8条模型绑定引文唯一；2个重复短语节点仍明确列为 `nodes_missing_evidence`。因此本次验证证明了“原文→抽取→递归结构候选→保守阻断/证据审计”链路可运行，也暴露了需要由显式定位/原因范围审核解决的真实阻断；它**没有**生成一棵可审核完成的 F30021 树。未修改正式 Gold、数据库、生产 API 或门策略；`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 保持。

独立 AI 子智能体只读复核支持上述阻断：故障值0下的监测响应不应未经关系证据提升为顶事件独立原因；两处相同短路描述是重复提及，不是两个独立原因；顶层 `Possible causes` 列表不等于明确 OR。该复核仅为 AI 角色审查，不是 Siemens 人类专家签署或 Gold。

### S210 F30027 局部明确 OR 的原文 Preview 对照（2026-09-27）

在 F30021 保守阻断样例之外，使用同一公开 S210 语料中的 `SIEMENS_S210_2019_F30027` 运行原文抽取与递归 Preview。复用探针命令：`python evaluation/quality_eval/public_sources/probe_s210_f30021_candidate_fta_v1.py --sample-id SIEMENS_S210_2019_F30027`；原始结果见[运行 artifact](../evaluation/quality_eval/runs/siemens_s210_2019_f30027_candidate_fta_preview_v1_2026-09-27.json)。

模型抽取1条记录、9条原因及参数；候选树有13个节点、3个局部 scope。17条树引用均精确回切原文且模型绑定引文唯一，树级 blocker=0，状态为 `candidate_ready_for_review`。其中：顶事件到“DC link 未能在预期时间内预充电”只有一个 child，故标 `not_applicable`；Cause 下编号列出的9项保持 `unknown`（原因集合完整性为 false，不能按列表推 OR）；第9项“either a ground fault or a short-circuit”正确拆成两个局部 child，并绑定原文 `[912,969)` 的 scope 与 `[928,968)` 的直接逻辑证据。该局部门仍是 `unknown`，因为当前没有可用的门型置信/放行策略；模型提议不等于门型批准。候选没有额外输出原文未明确的关系边。

这是单条公开文本上的结构/证据 Preview，不是准确率评估或正式 Gold。`candidate_ready_for_review` 仅表示候选合同可供审核，不代表人类已审、正式树已接受或生产可用；没有改正式 Gold、数据库、门策略或 API，`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 继续保持。本轮安排的独立 AI 子智能体复核未及时返回，已停止且未将其结果用于判定；因此 F30027 目前只有生成器输出及宿主合同/证据校验，语义审核仍未完成。即使后续 AI 复核完成，也不能替代 Siemens 人类专家签署。

### S210 F30027 独立 AI 复核补记（2026-09-27）

独立 AI 子智能体只读复核现有 F30027 artifact 与公开语料，确认 corpus/source hash 一致，逐项检查的40条抽取与树证据引用/offset 均精确。其结论与本节一致：外层9项编号原因不得凭并列列表推成 OR；末项原文 `either ... or` 在该局部文本范围支持 OR 语义，但门策略未启用，最终 `gate` 仍须保持 `unknown`。单子项连接不构成布尔门，也不等同于已验证的因果关系。

该复核只是 AI 独立角色审查，不是 Siemens 领域专家签署或 Gold。`candidate_ready_for_review` 与“最终门未知”可以同时成立：前者表示候选材料结构上可供人工/审核流程检查，不表示所有局部门已接受。审查也提示 `scope_type` 的局部文本描述可能被误读成已接受的 `gate` 标签；消费方应以最终 `gate` 字段及其 blocker 为准。本轮未更改合同或门策略。

### S210 F01681 多个显式局部门语义 Preview（2026-09-27）

使用公开语料 `SIEMENS_S210_2019_F01681` 原文调用同一探针，结果见[运行 artifact](../evaluation/quality_eval/runs/siemens_s210_2019_f01681_candidate_fta_preview_v1_2026-09-27.json)。原文的一个清晰局部 AND 范围是 `[540,625)`：`Referencing via SCC (p9501.27 = 1) and epos (r0108.4 = 1) are simultaneously enabled.` 这直接说明该 fault-value 子场景要求两项同时成立；它**只支持这个局部配置条件**，不支持将整个 F01681、所有 fault-value 模式或整棵故障树标为 AND。其他故障值段还包含不同的局部 AND/OR/组合限制表述，亦不得彼此合并为顶事件总门。

本次模型调用3次，抽取1条记录和16个 cause 候选，生成46个节点、13个局部逻辑作用域。模型输出的若干门概率为0.95，但没有已选择的接受策略，因此所有最终门仍为 `unknown`；分数不是校准概率或 Gold。证据审计显示候选树68条引用中，67条模型绑定引文可精确且唯一定位；另有8个拆分节点因原文短语重复/定位不唯一而没有证据，宿主没有猜选位置，整棵候选标记 `blocked`。这证明“显式逻辑词可形成局部门候选”与“证据不唯一时阻断”都在工作，但没有批准任何门型。

另做了只读图可达性核算：以顶事件为根，沿候选门 child→output 及因果 source→target 的反向追溯，46个节点中仅2个能到达顶事件，44个处于未连接子图。现有 `CandidateFtaTree` 合同和生成服务已将该情况变为整树阻断条件，并为每个断开节点生成 `node_disconnected_from_top_event:<node_id>`；断开节点不会被删掉。`associated_with` 仅是描述性关联，不算通往顶事件的结构路径。已有 F01681 artifact 是这项代码修复前生成的快照，所以其中尚未呈现新增拓扑 blocker；本轮未为刷新该 artifact 再次调用模型。使用当前共享可达性函数对旧 artifact 做了只读复核，确认应增加44条断开节点 blocker，原 artifact 保持不变。8个节点缺少唯一证据；这与44个断开节点可能重叠，不应相加当作节点总数。原因范围仍需复核：抽取结果把 `Fault value (r0949)` 下的多条诊断/参数模式一并当作 cause 候选，但原文没有把它们逐项连接到顶事件。故该样本仍不能视为完整故障树，fault-value 说明与顶事件原因的范围边界问题仍未解决。

下一步应处理 F01681 的 Cause 与 Fault value 诊断模式作用域，确保无原文依据的原因节点不会被误连；再用新合同重新生成/核对 F01681，并重跑 F30021/F30027 回归。保持置信放行策略未选定，不据模型分数升级门型。该 artifact 只是单样本开发 Preview；未写 Gold、数据库或生产 API，`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 保持。本轮针对性候选 FTA 测试25项通过，完整后端回归233项通过。F01681 的额外子智能体复核未能及时返回且已停止；以上由主代理按原文和 artifact 做的核验不冒充独立或真人专家签署。

### F01681 Cause 摘要与 Fault value 范围保护（2026-09-27）

继续核对原文和 Batch73 后确认：16 个 cause 候选包含一条通用 `Cause` 摘要及 15 条故障值到参数/配置状态的条件映射；映射不等于现场设备实例读数。通用摘要不应仅凭 `Cause` 标题被连成顶事件的独立基本原因，配置映射也不能单独证明某一状态在本次设备实例中发生。此前 Preview 的 `n_c0 -> top_event` 因此属于需要新模型输出复核的可疑关系；不能因为它有原文引文就认为语义关系已成立。

候选 FTA 共享结构/关系提示已增加上述通用约束：抽取到的 cause 是未确认输入；故障值/参数查表是条件映射；摘要或故障释义不能自动成为顶事件原因边。回归测试检查服务生成的两阶段提示确实包含这些约束。此改动只约束模型提示，不能证明在线模型必然遵从。

以上记录的是 v2 提示调整完成、尚未在线复跑时的历史状态；对应旧 artifact 不覆盖。其后在用户授权在线推理后，使用同一探针生成了新的 v3 结果，当前状态以如下“提示保护 v3 回归”小节为准。

### F01681/F30021/F30027 提示保护 v3 回归（2026-09-27）

**候选状态边界确认（2026-09-27）：**用户确认，门型 `unknown` 时可以保留只读 `candidate_ready_for_review` Preview，供检查候选和排障；这不等于接受建树。正式/可用树仍必须拒绝 unknown/不完整 scope，`fta_ready=false`、`production_ready=false`，不写 Gold 或数据库。该定义与当前候选合同中“reviewable candidate ≠ accepted/ready tree”一致，本次无需修改状态机或服务代码。

在用户授权后，使用 DeepSeek Flash 对三个原始 S210 故障样本分别运行同一探针；每个样本执行抽取、结构分解、门型评估共3次请求，合计9次，无重试。没有把审核标签传给模型，也没有覆盖旧快照。结果分别见 [F01681 v3](../evaluation/quality_eval/runs/siemens_s210_2019_f01681_candidate_fta_preview_prompt_guard_v3_2026-09-27.json)、[F30021 v3](../evaluation/quality_eval/runs/siemens_s210_2019_f30021_candidate_fta_preview_prompt_guard_v3_2026-09-27.json) 和 [F30027 v3](../evaluation/quality_eval/runs/siemens_s210_2019_f30027_candidate_fta_preview_prompt_guard_v3_2026-09-27.json)。

- **F01681：**抽取到16条候选原因，树含25个节点、3个局部门 scope、1条局部因果关系。因果边只连接局部条件事件与局部结果事件，不指向顶事件；`topGates=0`。15条 fault-value/参数状态映射没有被挂到顶事件，保留为断开候选；除顶事件外24个节点未连通，因此整树 `blocked`。所有现存引用的 offset 均精确、模型绑定引文唯一；仍有2个拆分节点缺少唯一证据位置，必须人工定位。3个局部门型均为 `unknown`，原因集合也未确认完整。该轮成功验证了“禁止把查表映射伪连到顶事件”和“断开任一节点即整树阻断”；**没有生成可用故障树**。
- **F30021：**树含6个节点、1个局部门 scope、0条关系；scope 有1个 child，不构成可接受的多输入逻辑门。另有1个原因候选断开，整树 `blocked`。证据位置精确且唯一。故障值映射没有被误连，但该样本仍未达到可审核完整树状态。
- **F30027：**本轮抽取输出23条 cause（故障摘要、9条 `Possible causes` 项及13条 `r0949` 故障值位说明），树含26个节点、3个 scope、0条关系。新增识别到的13条故障值映射全部保持断开；13个原因候选 unresolved、2个重复短语节点缺少唯一证据，因此整树 `blocked`。offset 精确，已有模型绑定引文唯一。v1/v2 曾因模型抽取只返回9条 `Possible causes` 而得到 `candidate_ready_for_review`；v3 抽取范围更广后触发整树阻断。这个变化体现了当前门禁对新增未连接内容的保守处理，**不能据此声称抽取质量提高或退化，也不能把旧版较宽松状态当作通过基线**。

三个 v3 artifact 均保持 `formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`；没有改 Gold、数据库、生产 API 或门置信策略。该回归只验证提示约束、证据绑定和拓扑阻断，不构成真人领域专家审核、模型准确率或概率校准结论。F01681 要继续形成正式树，至少需取得具体设备实例的参数/故障值读数，并对完整原因集合、各局部关系和逻辑门进行审核。F01681 两个和 F30027 两个重复短语节点的原文位置已整理到[重复证据定位确认单](../evaluation/quality_eval/runs/siemens_s210_candidate_fta_manual_locator_bundle_v1_2026-09-27.md)：3处由用户授权的 AI 审核角色定位、主代理按原文回切核实；v3 中 `n6_cons_a` 因节点文本丢失原句否定语义，不能靠绑定正向短语解决。AI 角色审核不是真人专家签署或正式 Gold。缺少实例数据时，故障值映射保持为诊断候选，不进入正式 FTA 树。

### F01681 否定命题保真提示 v4 回归（2026-09-27）

用户确认：当原文是“若 A、B 条件成立，则 C/D 不可用”时，结果节点应保留完整否定命题，不把 C、D 当作正向原因拆叶。结构分解提示据此新增极性/条件/情态保真要求：若拆分无法保留语义，就保留完整命题并标记 unresolved，不据示例推出 AND/OR。相关回归断言位于 `backend-python/tests/test_candidate_fta_extraction_service.py`。

使用同一公开样本探针，仅对 `SIEMENS_S210_2019_F01681` 新跑一次，输出为[极性保护 v4 Preview artifact](../evaluation/quality_eval/runs/siemens_s210_2019_f01681_candidate_fta_preview_polarity_guard_v4_2026-09-27.json)；3 次在线请求、0 重试。文件内 `artifact_version=v1` 是该运行产物的结构版本，文件名中的 v4 指本次提示修订，不覆盖 v3。

- Cause index 6 被保留为单一完整节点：“If motion monitoring functions ... and extended functions ... are enabled, then PROFIsafe ... or onboard F-DI ... is not possible.” 证据 `[838,1050)` 精确回切原文；没有再生成把 `PROFIsafe` 或 `onboard F-DI` 作为正向叶节点的拆分。
- 树仍为 `blocked`：19 个节点、34 个 blockers；cause 结构仍 unresolved、候选节点未连接到顶事件。仅另一个 SCC/epos 局部同时使能 scope 输出 `unknown`，且保留 `gate_confidence_policy_unavailable` blocker。证据审计 21 个引用全部 offset 精确、模型绑定引文唯一、无缺证据节点。
- 产物继续保持 `formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`。该单样本结果不证明模型普遍遵循，也不替代 Siemens 真人专家签署。实例级参数读数、完整原因集合及因果/门型审核仍未具备，因此不生成正式树。独立 AI 角色复核确认 v4 的命题保真、offset 和阻断状态符合预期；同时指出 `decision_reason` 虽然最终门是 `unknown`，仍直接拼接“supports an AND gate”一类模型理由，可能被误读成已确认门型。

### F01681 unknown 门提议文案防误读 v5 回归（2026-09-27）

为处理 v4 独立复核指出的表达风险，候选服务现将任何最终为 `unknown` 的 scope 明确标成 `model gate proposal is not accepted`，并把原模型理由放入 `model rationale:` 字段；模型概率仍保留用于审计，不会因此将门改成 AND/OR。新增测试覆盖“模型理由声称 supports AND、但最终门 unknown”的状态标签与顺序。

对同一 F01681 原文再运行一次，产物为[v5 Preview](../evaluation/quality_eval/runs/siemens_s210_2019_f01681_candidate_fta_polarity_and_gate_disclaimer_v5_2026-09-27.json)，共3次请求、0重试：

- Cause index 6 仍是一个带完整条件、`not possible` 否定结果的单一节点，offset `[838,1050)`；没有拆出 PROFIsafe/onboard F-DI 正向原因节点。16 条输入 cause 结构仍 unresolved，且相关节点没有连到顶事件。
- 树状态 `blocked`，35 节点、9 个局部门、0 条关系，50 个 blockers。每个局部门最终均为 `unknown`；诊断先说明模型门型提议未被接受，再显示模型理由。`AND/OR` 数值仍是未经校准的模型提议分布，不是确认结论或设备故障概率。
- 证据审计 53 条引用全部精确回切、52 条模型绑定引文唯一、缺证据节点为0。`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`。

独立 AI 角色复核确认：Cause index 6 的完整否定命题、unknown 门提议未接受标签、offset 和正式门禁均符合要求；同时提醒 Cause index 8 仍有一个正向局部节点 `Onboard F-DI are enabled.`。它属于父级完整条件 “Onboard F-DI are enabled without enabling motion monitoring...” 的局部 child，父 scope 门为 `unknown`，且没有连到顶事件；不得脱离父 scope 当作独立根因。此单样本结果只证明本次输出和状态标签符合预期，不证明模型普遍遵从，也不构成 Gold 或 Siemens 真人专家审核。

为检查提示变更不是只适配 F01681，又用同一探针分别对 F30021 与 F30027 做 v5 回归，产物为 [F30021 v5](../evaluation/quality_eval/runs/siemens_s210_2019_f30021_candidate_fta_polarity_and_gate_disclaimer_v5_2026-09-27.json) 和 [F30027 v5](../evaluation/quality_eval/runs/siemens_s210_2019_f30027_candidate_fta_polarity_and_gate_disclaimer_v5_2026-09-27.json)，各3次请求、0重试：

- **F30021：**6 个节点、1 个 unknown scope、0 条关系，整树 `blocked`（2 个 blockers）。unknown 理由明确标记模型门型提议未接受；7 条候选树引用精确且唯一。
- **F30027：**12 个节点、2 个 unknown scope、0 条关系，结构状态为 `candidate_ready_for_review`（0 blockers）。按已确认边界，这只允许只读送审，**不等于正式树获批**；15 条候选树引用精确且唯一，且 `human_reviewed=false`、`fta_ready=false`、`production_ready=false`。
- 三个 v5 样本均保持 `formal_gold=false`、`database_written=false`；门提议不会因提示变更自动变成已选 AND/OR。各样本均为单次模型样本回归，不能当作统计泛化证明。

独立 AI 角色复核确认两份回归均符合候选边界：F30021 保持阻断；F30027 虽为 `candidate_ready_for_review`，仍 `human_reviewed=false`，两个门均 unknown，尤其局部 `either ... or ...` 只是模型提议（`OR=1.0`），语义为 `uncalibrated_model_estimate`，不得视为已接受 OR。复核未发现越权关系；两个 artifact 的语料文件/原文哈希匹配，F30021 的7条与 F30027 的15条候选引用均精确回切。Preview 探针调用的是不持久化的候选应用服务并只写运行 artifact；两个产物均未写 Gold/数据库且 `fta_ready=false`、`production_ready=false`。AI 角色审核不是真人 Siemens 专家签署或 Gold。

### 闭合枚举完整性与完整原文双样例回归（2026-09-28，Cause disposition v2 前快照）

F35400 与 F06000 的原文运行揭示：结构提示曾把“没有现场参数读数”错误泛化成“定性触发条件不能连接顶事件”，并且没有明确说明 `cause_set_complete` 是来源限定 scope 内的枚举完整性，而不是具体设备实例发生状态。另一个旧探针按响应序号猜测阶段，导致结构服务把已在处置账中排除的原因摘要重复列入结构 unresolved。当前探针改为按输出合同识别阶段；结构提示明确：定性因果条件可在没有实例读数时作为候选连边；闭合枚举覆盖全部直接子项时可标完整；处置账非树项由宿主单独留账、不重复返回结构未决索引。

使用当前 CandidateFtaApplicationService 与 DeepSeek Flash 对同两条完整 S120/S150 原文分别运行四阶段，每条无重试：

| 样本 | 当前输出 | 边界 |
| --- | --- | --- |
| F35400 | 3 节点；2 条阈值条件连接顶事件；枚举完整、叶子已规范化；树证据 5/5 精确且唯一 | 1 个 OR 作用域最终为 `unknown`，唯一 blocker 为 `gate_confidence_policy_unavailable` |
| F06000 | 13 节点；10 条原因候选、1 条 Cause 摘要排除；10 子项外层作用域及 2 子项局部 either-or 作用域均完整；树证据 17/17 精确且唯一 | 两个作用域最终均为 `unknown`，唯一 blocker 均为 `gate_confidence_policy_unavailable` |

运行文件：[F35400 JSON](../evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.json)、[F35400 报告](../evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.md)、[F06000 JSON](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.json)、[F06000 报告](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.md)。

这两条仅作为开发回归，不是准确率、专家 Gold 或独立 Final；不修改 Gold、数据库、生产 API、门置信策略或 readiness。门概率仍是未校准提议，`fta_ready=false`、`production_ready=false`。v7 是该段运行当时的活动版本；后续 Cause disposition v2 运行登记在 [FTA baseline manifest v8](../evaluation/quality_eval/fta_baseline_manifest_v8.json)。

### Cause disposition v2：可能原因与实例诊断分开（2026-09-28，历史策略快照）

第一轮原文回归暴露两处系统性过度排除：F01681 的15条故障值配置冲突均被一律归为“缺少实例读数”；F30027 的完整“过热，因为……”因果句仅因同句包含状态和原因而成为 unresolved。此做法混淆了“手册列出的通用可能原因”与“现场某台设备是否实际发生”。

当时 Cause disposition prompt 升为 `fta-cause-disposition-v2`：

- 纯编号/状态映射仍是 `fault_value_mode` 或 `diagnostic_mapping`，不入树；
- 故障值条目若直接陈述该故障的参数冲突/不相容等原因条件，按命题语义归为 `causal_condition` 候选；无需现场读数来证明它属于手册列出的通用可能原因，但不得声称该现场实例已发生；
- 单一完整因果句保留为一个候选，不因包含中间状态和“as/because”因果子句而自动标为 mixed，也不自动拆句；
- 这只影响原因候选准入，不推断门型。无独立逻辑证据或置信策略时仍为 `unknown`；证据/完整性阻断仍保留。

同一输入语料 `siemens_s210_public_fault_corpus_v1` 的完整四阶段开发回归：

| 样本 | 结果 | 保留的安全边界 |
| --- | --- | --- |
| F01681 | 原因处置：15条 `fta_event_candidate`、1条摘要排除；38节点、12个局部门；树证据60/60精确且唯一；候选状态可供审核 | 所有门仍 `unknown`；故障值替代集合完整性仍不足，局部条件完整性/置信策略 blocker 保留；`fta_ready=false` |
| F30027 | 9条原因候选；12节点、2个门作用域；树证据15/15精确且唯一；候选状态可供审核 | 9项原因集与局部 either-or scope 完整，但门均 `unknown`；门策略不可用；`fta_ready=false` |

第一轮 prompt v1 阻断产物保留为诊断证据，没有被覆盖。v2 原始模型响应文件保留了全部四阶段回复；之后另生成仅补全来源元数据的离线审计副本（没有模型调用）：[F01681 核验 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json)、[F01681 核验报告](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.md)、[F30027 核验 JSON](../evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json)、[F30027 核验报告](../evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.md)。核验副本记录手册 PDF 文件名/SHA-256、章节、页码、corpus source offset 及输入文本 SHA-256。两例仍只是开发回归，不是专家审核、Gold、Final 或准确率结论；不写数据库、不改正式 Gold/门策略/生产 API/readiness。该 v2 对 F01681 故障值解释的候选边界已由 v3 收紧，详见下节；历史运行保持原样。v2 阶段的活动基线曾为 manifest v12，当前活动基线见 [manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)。

### Cause disposition v2 扩展原文回归与 F01681 独立 AI 复核（2026-09-28，历史活动 v9）

新增三条四阶段完整原文开发回归；来源、PDF 哈希、页码、语料 offset 和 input-text SHA-256 保存在 JSON 运行 artifact 中。三例不是正式 Gold、独立验证或准确率证据：

| 样本 | 候选结构与状态 | 保留边界 |
| --- | --- | --- |
| F30021（S210） | 5 节点，4 个 `fta_event_candidate`；候选树 blocked | cause-3 与原文其他位置重复，故不自动定位；顶事件引用也非全局唯一。运行早于顶事件守卫，旧 artifact 未覆盖；守卫由代码单测验证。门仍 unknown，模型 OR 概率未经校准 |
| F35400（S120/S150） | 3 节点，2 个 `fta_event_candidate`；`candidate_ready_for_review`；5/5 引文精确且唯一 | 模型 OR 提议被 fail-closed 策略拒绝，逻辑门保持 unknown |
| F06000（S120/S150） | 15 节点，11 个 `fta_event_candidate`；4 个 scopes；21/21 引文精确且唯一 | 两个布尔门 scope 为 unknown，两个单子项 scope 为 `not_applicable`。首个“READY 未出现”事件与顶事件语义重叠、多层列表的拓扑表达均需人工语义复核 |

F01681 独立 AI 角色复核发现更深的语义/证据问题：[结构化复核记录](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json) · [复核说明](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md)。15 条 `r0949` 故障值解释可与故障记录建立诊断关联，但不因此逐项证明到顶事件的因果方向；`source_cause_index=1` 在抽取层缺 evidence span；Remedy 提到的 `xxxx=9507` 尚未与顶层 cause scope 对账，所以完整性未闭合，也不能自动将其作为 causal child。原始 v2 run 的 `source_document_sha256` 为空，PDF 哈希来自后续既有 provenance audit 并与语料元数据匹配；输入文本 SHA-256 与原始运行/语料一致。因而现有 top-event children 连接不可被当作已证实因果边；来源/offset 可追溯也不等于语义因果已证明。

### 抽取原因证据必须先于 FTA 处置（2026-09-28，离线回归）

候选 FTA 的原因处置现在要求每个 cause index 在抽取结果中已有且仅有一个可回切原文的 `CAUSE` span。处置模型后来给出的 `evidence_quote` 不能补造或替代缺失的抽取证据；零条或多条跨度都会将该项置为 unresolved 并阻断整棵候选树，保留审计信息供补证。通用抽取合同仍允许部分字段/原因没有证据；这个更严格的规则只属于 FTA CauseDisposition 层。

### Cause disposition v3：自然语言候选边与诊断映射分离（2026-09-28，历史策略）

用户确认的当前规则：**原文在 Cause/Possible causes 等明确范围内列出的自然语言原因，可成为待审核的候选因果边；fault code/value、参数号、位号或索引到解释文本的诊断映射，不得仅凭映射本身连接到顶事件。** 映射行的解释即使是流畅自然语言、写有配置冲突/参数不相容，也不改变它作为诊断映射的交际功能。最新 F01681 复演暴露了需补严的子边界：位于 Cause 段不代表一定提供独立原因信息；仅把顶事件换句话说的摘要/释义不能形成有信息量的因果边。

具体执行边界：

- Cause disposition prompt 升为 `fta-cause-disposition-v3`。明确原因范围内的自然语言原因可以是 `causal_condition + fta_event_candidate`；诊断映射默认为 `diagnostic_mapping/fault_value_mode + relation_only`，完整留在逐项审计账。
- 仅当诊断映射之外存在独立、直接原文证据，把对应自然语言条件明确列为该故障的原因/触发条件，且 cause index 获准进入候选时，才允许生成候选连接。不能把映射行自己循环当作独立因果证据。
- 候选边仍是 `ai_proposed`，不是已确认因果关系；AND/OR 仍需独立逻辑证据与审核。原因证据缺失/歧义、映射范围不清或候选无法闭合时仍阻断整棵 Preview；Gold、数据库、生产 API 与 readiness 不变。
- F01681 v2 历史运行曾把 15 条 `r0949` 故障值解释提升为候选并接入树层级；AI 复核已指出这不等于逐项因果证据。该历史 JSON/Markdown 不回写，视为 v2 诊断快照，不再作为当前边界的通过证据。之后用 DeepSeek Flash 对 F01681 做了单次 v3 在线开发复演（4 阶段 4/4 成功、重试 0）：15 条故障值/参数映射均为 `relation_only`、没有进入树；Cause index 0 被提出为唯一待审候选，结果为 2 个节点、1 个单 child `not_applicable` scope，树证据 3/3 精确且唯一。独立 AI 子智能体复核认为 index 0 可能只是对 `Incorrect parameter value` 的重述，给出 `NEEDS_REVISION`。此结果说明映射隔离在该单样本的模型输出中生效，但不能证明候选语义正确；原运行与复核产物均保留，不自动改写、入 Gold 或数据库。此前 `xxxx=9507` Remedy 对 Cause 范围完整性的疑问仍待独立语义对账。

相关 v3 实现、正反例回归、在线运行和复核产物哈希见 [FTA baseline manifest v11](../evaluation/quality_eval/fta_baseline_manifest_v11.json)；v3 阶段后续基线曾升至 v12/v13，当前活动策略与证据见 manifest v14。

### Cause disposition v4：顶事件释义不能作为独立原因边（2026-09-28）

v3 的 F01681 在线开发复演把 `The parameter cannot be parameterized with this value.` 作为唯一 Cause 候选；独立 AI 子智能体指出它可能只是顶事件 `Incorrect parameter value` 的释义，没有提供独立上游机制。该运行保持不变，不回写历史输出。v4 只收紧语义判定：必须将每条原因命题与 `top_event` 对照；只有来源直接支持且提出语义上独立的上游事件、条件、机制或触发过程时，才可成为候选。纯定义/同义改写/重述且没有新增前因信息的内容标为 `causal_summary + relation_only`，意义不清则 `unresolved + semantic_role_uncertain`。这不改变“明确自然语言可能原因可作为待审核候选”的主规则，也不影响诊断映射边界。

离线测试覆盖顶事件重述留账、摘要误标候选时宿主降级、现有明确原因候选、证据与映射边界。**在本小节记录时**未调用在线模型，且不重写 F01681 v3 结果、不更改 Gold/数据库/生产 API/readiness；后续 v4 在线复演见下节。该离线阶段只证明提示词与合同回归可表达边界，不证明模型一定能稳定识别语义等价，也不是准确率或专家验收。

`TextExtractionAdapter` 的离线 mapper 回归现覆盖空白/单双及弯引号差异、抽取文本省略括号内参数注记、末尾句号差异，并保存原文真实 quote 与 offset。重复短语仍返回所有位置；下游不得择一，须人工定位。使用保存的 F01681 抽取响应对原文离线回放后，16/16 causes 都得到唯一、带 index 的原文跨度，包括历史复核指出缺失的 index 1；历史 v2 Preview 不回写。F30027 保存响应离线回放亦覆盖 23/23 causes。以上只证明确定性 mapper 与证据门禁回归，不证明 cause 的因果语义，也不是在线模型结果、专家 Gold 或准确率结论。

在 v9 阶段，全后端测试为 263/263；其中候选 FTA、递归结构、CauseDisposition 和证据 mapper 定向测试为 78/78。v9 manifest 当时登记了相关代码/测试及 SHA-256；这些是历史验收数字，不代表当前测试快照。未改 Gold、数据库或生产 API，FTA 与生产 readiness 均保持 false。

根 artifact 的 `live_model_development_probe_not_expert_review` 与树对象的 `user_authorized_ai_expert_role` 描述不同 provenance 层级：前者标识模型开发运行，后者表示流程使用受授权 AI 角色；它们均不表示真人审核，`human_reviewed=false`。处置边界：保持门型 unknown、候选/Preview 状态；不写 Gold、数据库或生产 API，`fta_ready=false`、`production_ready=false`。上述是历史 v9 运行；当前活动基线见 [manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)。

### Cause disposition v4：F01681 单样本在线开发复演（2026-09-28）

在用户明确授权的一次在线调用范围内，固定原文 `SIEMENS_S210_2019_F01681` 使用 DeepSeek Flash 运行 v4，关闭重试。由于原因处置后没有任何 `fta_event_candidate`，流程仅执行 Fault Extraction 与 Cause Disposition 两阶段（2/2 请求成功），随后按合同提前阻断，没有调用 Structure Decomposition 或 Gate Assessment。

16 条原因全部保留为 `relation_only`：index 0 是对 `Incorrect parameter value` 的摘要/释义，15 条为 fault-value/参数诊断映射。树状态为 `blocked / no_fta_event_candidates`，只保留顶事件节点，无因果关系、无逻辑门。原语料输入 SHA 匹配；抽取引用 54 条、处置条目 16 条、候选树引用 1 条，共 71 个位置均精确。

一个独立 AI 子智能体进行了只读复核并给出 `PASS`：它同意 index 0 不构成独立前因，诊断映射不自动进树，且在零候选时阻断正确。此为 AI 角色审核，不是真人刘武签署、不构成正式 Gold，也不能据单一样本声称模型总体准确。运行和复核 artifact 见[运行 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.json)、[运行报告](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.md)、[AI 复核 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.json)、[AI 复核报告](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.md)。

该样本验证的是 v4 的一个目标边界在一次在线运行中得到符合预期的保守行为，不是完整 FTA 树通过；原因集完整性、其他故障泛化、门型真值和独立 Final 仍未闭合。Gold、数据库、生产 API 与 readiness 不变，`fta_ready=false`、`production_ready=false`。当前活动研究清单为 [manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)。

### F01681 Remedy `xxxx=9507` 范围复核（2026-09-28）

固定原文唯一出现 `If xxxx = 9507: Set synchronous motor.`，位置 `[2526,2564)`；该句属于 `Remedy: Correct parameters`，在此前 Cause/Fault value 映射区段未出现。直接证据支持的只是“xxxx=9507 时，手册要求设置同步电机”。它不是现场状态证据，也未直接说明“未设置同步电机”是 `Incorrect parameter value` 的上游因果条件。

据此不修改 `FaultRecord.causes`，不把该 Remedy 分支纳入原因处置 ledger，也不创建 FTA 节点/边；保留其 Remedy 身份，并将 Cause/Fault value/Remedy 范围完整性维持为 `unresolved`。只读 AI 子智能体复核意见一致，但非真人专家签署。范围审计 JSON/报告见[复核 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.json)与[复核说明](../evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.md)。不改 Gold、数据库、生产 API 或 readiness；活动基线见 [manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)。
