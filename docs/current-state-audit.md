# 项目当前状态审计

## 最新更新（2026-10-07）

当前活动基线为 [manifest v52](../evaluation/quality_eval/fta_baseline_manifest_v52.json)。v52在保留v51历史快照的基础上，加入后端内部的显式 occurrence-locator review overlay：只按原文哈希、记录/字段索引、精确偏移和已审核 scope 绑定证据，并将定位来源信息序列化进原因处置批次及候选树。没有定位时仍 fail-closed；本次只做离线合同/服务回归，没有模型请求。F30021最新真实来源原始运行仍是 v5、仍 blocked，未回写。该实现不是正式 Gold、专家语义验收、准确率或泛化结论；`fta_ready=false`、`production_ready=false`。

### 2026-10-07 P2 真实来源合同与历史案例审计

审计覆盖 F01681、F30027、F30021、F06000、F35400 与 NASA Figure 7，逐项检查原因分类、事件身份、层级、child集合和门证据。完整发现及边界见[审计报告](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.md)和[结构化审计账](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.json)。

关键版本事实：当前 `CauseDispositionService` 提示版本为 `fta-cause-disposition-v6`；本次没有用新提示调用模型。五条 SINAMICS 存档运行是 v2/v4，NASA Figure 7 是独立 event-scope v6；F30021 最新真实来源原始响应仍来自 v5。这些历史响应不能作为当前 v6 真实来源模型结果。F30021仍因重复/缺失证据保持阻断；F06000事件身份/摘要层级仍有语义疑点；F30027/F35400虽保留原文局部替代结构，门仍受未配置置信策略限制而为 `unknown`；Figure 7有引用位置通过但逻辑证据、身份与粒度发现未关闭。

本轮离线结果：候选 FTA 35项、原因处置16项、event-scope v8与v6 runner合同8项通过；该次P2a审计当时检查的v48 manifest 367/367哈希有效。它们证明合同回归与工件完整性，不证明模型遵循提示或语义准确率。P2a只读合同/历史案例审计完成；后续真实来源复跑情况见下节。未改 Gold、数据库、生产 API 或 readiness。

### 2026-10-07 P2b：F30021 当前版本真实来源单例

用户针对样本 `SIEMENS_S210_2019_F30021` 明确授权最多4次模型请求。实际运行4个阶段、成功响应4份，SDK/外层重试均为0，无自动修复/重试。输入文本 SHA-256 为 `f3178a6c9c46aa2109a44eb118c6a8730ebfdd6d9a6f5660147529f01ce41d31`，提示版本为 `fta-cause-disposition-v5`。原始输出保存在[运行 JSON](../evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json)；不修改原始响应的[离线复核副本 v2](../evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.md)另存。

模型曾提议4项 `fta_event_candidate`、1项 `relation_only`；宿主证据门禁最终归一为3项候选、1项relation-only、1项unresolved。第4条候选短语在Possible causes与故障值说明两处出现，抽取证据将两个跨度绑到同一cause索引，故服务拒绝自动消歧。顶事件引文“ground fault”也重复出现4次，唯一性检查失败；可能原因列表4项只确认3项进入子节点，集合不完整。门保持`unknown`，列表本身没有证明AND/OR，置信策略仍不可用。整树状态`blocked`；安全拒绝猜选符合既定规则，但证据身份建模缺陷与语义验收均未关闭（关闭数0）。详见[逐项语义审计 v2](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.md)。

运行器派生统计口径已离线修正为分别报告模型提议与宿主最终处置，并单独核验cause-disposition证据；原始运行文件未覆盖。15项runner测试通过。该单例不是真人专家审核、Gold、准确率或泛化证据；未改数据库、正式Gold、生产API或readiness。下步只做证据 occurrence/scope 身份的离线设计和回归；若需要改共享证据合同，先明确owner/schema影响并停下征求确认。新的模型请求需要另行授权。

2026-10-07 P1 实际验证：在单次明确授权下调用`deepseek-flash`一次，SDK/外层重试均0。模型将两条仅共现、时序在前的报警分别判为`state + detached_observation`；宿主保留两个带唯一原文引文的观察节点，不连边、不建门，整树`blocked`。原文/响应SHA-256与5条引用位置复核通过。原始文件见[运行 JSON](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json)和[报告](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.md)。这只是单个合成非Gold样例，不代表模型准确率、专家审核或泛化。P1窄目标完成，下一步进入P2真实来源开发回归；全局`fta_ready=false`、`production_ready=false`。

### 2026-10-07 P2c：重复证据跨度离线回归与审核出口核对

已新增 F30021 固定用例，真实复现同一 cause 同时出现在 `Possible causes` 与 `Fault value`：抽取保留两条精确 offset、同一 `value_index`；CauseDisposition 继续输出 `unresolved / evidence_missing_or_ambiguous`，不选择任一处。检查 `CandidateFtaGenerationResult` 序列化发现它保留全量 extraction evidence spans，包括 `CAUSE_CONTEXT` 上下文与偏移，因此人工可以在 Preview 工件中看到两个位置；未决项的 `evidence=[]` 仍避免误示为已确认引用。现阶段不改共享证据合同/API。定向后端回归86项通过；无新模型请求，Gold、数据库、生产行为及 readiness 不变。

### 2026-10-07 P2d：F30021 已有定位审核与最新原始运行离线对账

新增[对账报告](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.md)及[结构化结果](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.json)。对账重算原文 SHA 和所有精确跨度，确认 C04 引文在全文出现两次：`[332,372)` 位于唯一 `Possible causes` scope `[166,372)` 内，`[468,508)` 位于后续 r0949 故障值说明。历史定位材料是授权 AI 子智能体审核，不是真人签署或正式 Gold。

该定位决定没有应用到最新 v5 原始运行：其 C04 仍为 `unresolved / evidence_missing_or_ambiguous`、`evidence=[]`；顶事件 `ground fault` 仍有4处匹配，child 集合不完整、门为 `unknown`，整树 `blocked`。本次关闭的是历史定位工件的来源/范围一致性对账；语义缺陷关闭数仍为0。无模型请求、不修改原始运行、Gold、数据库、共享公共 API 或 readiness。自动化对账及回归共7项通过。当时提出的“运行时消费出口需另行设计”由下方 P2e 更新；不得自动回填，也不得默认选择首个匹配。

### 2026-10-07 P2e：内部 occurrence-locator overlay 合同与离线接线

在明确限定为后端内部合同后，新增 `EvidenceOccurrenceLocatorReview` 与 `EvidenceLocatorReviewResolver`。定位决定要求 extraction/result/record/source SHA 一致；所选跨度与 scope 必须精确回切原文；引文在所选 scope 内唯一；且必须恰好覆盖同字段、同 value index 的一个抽取证据跨度。重复定位目标、过期源文、越界/错误偏移、scope 内重复引用均拒绝。原因处置模型只能逐字返回已选中的抽取证据短引文；模型扩写、跨 scope 拼引文或未提供 locator 时仍 unresolved，不自动修复、不自动重试。

Locator review 随 `FtaCauseDispositionBatch` 与 `CandidateFtaTree` 一同序列化，保留 review id、审阅来源、是否真人专家、非 Gold 标记、源文 SHA、scope/selected offsets 与理由。定位只证明“选中了哪处文本”，不证明原因语义、因果边、层级或 AND/OR；它不会解除 F30021 的 child-set、顶事件身份或门策略 blocker。服务仅接受显式内部参数；没有改公开 API、数据库持久化、Gold、原始模型运行或 readiness，也没有发起模型请求。

离线回归覆盖 locator 合同/哈希与偏移校验、scope 内重复拒绝、原因处置 fail-closed/精确引文、候选树证据绑定和元数据保留、应用服务透传。当前 v52 只证明实现合同按预期工作；没有模型语义成绩，正式语义缺陷关闭仍为0，`fta_ready=false`、`production_ready=false`。下一步是在另行授权后，以新运行验证明确 locator 能否解决重复原因证据绑定；必须保留 v5 原始运行不变，并分别检查顶事件唯一性、child 集合完整性及门策略。

### 审核 / Gold / 逻辑门台账对账（2026-10-07）

以下集合使用不同审核者、对象和粒度，**不能相加为一个“总审核数”**。明细来源分别由对应 JSON 与专项状态文档登记；本表只给出当前权威口径。

| 台账 | 范围与计数 | 权威含义与边界 |
| --- | --- | --- |
| 具名审核的因果关系 Gold v7 | 来源全集 281 条故障记录 / 1041 条原因候选；已有决议 296 = 批准 205 + 排除或暂缓 91（`revise` 40、`cannot_determine` 40、`reject` 11）；745 条尚无具名审核决议 | 205 条才是当前正式因果关系 Gold；`expert_validated=true` 的范围仅为 `reviewed_candidates_only`。91 条不是批准关系，40 条 revise 仍未关闭。 |
| 具名审核的 AND/OR Gold v1 | 6 个事件：OR 5、unknown 1、AND 0 | 是独立逻辑门审核集；`logic_gates_complete=false`，不能替代 281 条事件的门型覆盖。 |
| AI 授权的 Batch02–Batch99 汇总审核 | 98 份快照；281/281 个唯一事件、1041/1041 个唯一候选 ID；重复 0。事件门标签 OR 17、`not_applicable` 60、unknown 204。候选类别：causal 707、causal_summary 137、associated_only 175、cannot_determine 18、causal_trigger_condition 1、diagnostic_subtype 1、not_supported 2 | 全覆盖是 AI 角色审阅覆盖，不是真人专家 Gold；不写入正式 Gold/数据库，也不代表 281 条均可建树。11 个事件通过既有 Preview 门禁，270 个未通过。 |
| 事件范围主审核 v8（AI 角色） | 39 个所选 `event_cause_set` 范围：reviewed 37（AND 0、OR 1、unknown 36），`not_applicable` 2，pending 0 | 这是一个窄范围事件级审核集合，不是上行 281 事件汇总，也不是人类专家 Gold。 |
| Gate-node Review v6（AI 角色） | 55 个门节点：reviewed 55、pending 0；AND 12、OR 17、unknown 26；47 个故障码、48 个来源簇；另有 5 个非门范围审核 | AI 角色审核、非正式 Gold、非模型校准集；不可与事件范围 v8 或具名 AND/OR Gold 合并计数。 |
| 因果 Gold v7 AI provisional 派生视图 | 246 个候选范围：165 条关系（其中 163 条既有具名审核关系、2 条 AI provisional）+ 81 条排除/暂缓 | 与正式 Gold 有候选交集且范围较旧，不是额外的互斥样本；不得与 205 条或 Batch02–99 覆盖量相加，也不得升格为专家签署。 |

**原因语义角色合同已实现并通过当前离线回归**：`causal_condition`、`diagnostic_mapping`、`fault_value_mode`、`consequence`、`state`、`causal_summary`、`remedy`、`other`、`mixed_unresolved`；处置为 `fta_event_candidate`、`detached_observation`、`relation_only`、`exclude_from_tree`、`unresolved`。合同限制只有有证据、角色兼容的原因/状态候选才能进入树；诊断映射、故障值解释、后果、摘要和处理动作不得被自动当作因果边；共现状态可作为有证据的断开观察节点保留，但不能挂到树或参与逻辑门，未决/断开项继续阻断整树。

2026-10-07 离线验证：v44 前置回归 60 项通过，旧快照 `349/349` 哈希有效；v45 加入状态对账后，扩展回归 **64 项通过**，v45 生成器 `--check` 为 current，活动清单 **357/357** 哈希有效，目标文件 `compileall` 退出码 0。v45 新增状态对账，不是模型语义准确率验证。没有发起新的在线请求；需明确标记为“离线已验、在线待授权/待验证”。

其余 FTA readiness 仍未通过：正式因果 Gold 未覆盖 745 条候选；具名逻辑 Gold 仅 6 个事件且无 AND；独立 Final 验证尚缺；门型概率未校准；真实设备概率链路未接入。不得据 AI 覆盖数、合成 smoke 或 Preview 树宣布全量/生产 FTA Ready。

此前 manifest v42/v43 的运行汇总是历史快照，不代表当前服务合同。SMOKE-001…005 均为合成非 Gold；不能证明真人专家语义正确、准确率/校准或真实手册泛化。FTA Structure/Quantitative readiness 仍未通过，`fta_ready=false`、`production_ready=false`。

#### v41：SMOKE-004 事件共现边界单次观察

针对 SMOKE-004 的明确单次授权请求已完成：1 次请求、0 次重试，`finish_reason=stop`，严格 JSON 解析及树结构合同通过，4/4 引文位置有效。模型把压力升高和温度升高作为候选子事件保留，但因原文只记载二者在储罐破裂前出现、未说明 AND/OR 组合关系，输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。离线 v2 比较与编写者非 Gold 预期一致；语义正确性未由专家评估。v41 记录四条合成非 Gold 观察，SMOKE-005 仍未运行；不报告准确率、校准或泛化，不改变 Gold、数据库、生产 API 或 readiness。

#### v42：SMOKE-005 无关词面 OR 与结构阻断

针对 SMOKE-005 的明确单次授权请求已完成：1 次请求、0 次重试，严格 JSON 解析成功，3/3 引文位置有效。模型识别出“red or amber”属于独立的显示选择，没有将它当作 `pump shutdown` 的 OR 证据，并把故障门标为 `unknown`。但是输出只包含一个 gate child，结构合同报 `gate_scope_requires_at_least_two_children`，因此整份输出保持 blocked。离线 v2 对照结果为 `requires_review`：预期/观察门型相符不等于整例通过。原始输出未修复、未重试；本次只支持合成样例的定性观察，不构成 Gold、准确率或泛化证据。

#### v38：SMOKE-001 单次在线行为观察（非 Gold）

请求 1 次、重试 0 次，`finish_reason=stop`，严格 JSON 解析成功。模型把两个不同故障路径连到同一 `pump shutdown` 顶事件，并输出 OR；`logic_evidence` 与完整决定句相同。合同通过，5/5 引文位置有效。运行后才读取隔离的预期标签做离线对照：预期 OR、观察 OR，匹配。此标签是按政策撰写、未经专家复核；因此结果只能称为“匹配该合成 smoke 的政策预期”，不能称为语义正确率或模型泛化。原始可见响应、机械评估、调用收据和比较 JSON 均保存；没有自动修复/重试，未写 Gold、数据库或生产 API。其余 SMOKE-002…005 未请求。

#### v39：SMOKE-002 单次在线行为观察（非 Gold）

请求 1 次、重试 0 次，`finish_reason=stop`，严格 JSON 解析成功。原文没有字面 AND；模型根据“腐蚀削弱的容器壁”和“超过设计限值的内部压力必须同时成立，单独任一条件均不足”输出 AND，并将完整条件句绑定为 `logic_evidence`。合同通过，5/5 引文位置有效。运行后才离线读取分离的编写者预期，Observed AND = Expected AND。此为第二条合成政策样例的匹配，不是专家语义验收、准确率或泛化证据；SMOKE-003…005 未调用。原始响应、机械评估、调用收据和比较 JSON 已保存，无自动修复/重试或 Gold/数据库/生产写入。

#### v40：SMOKE-003 unknown 门型单次观察与比较器合同修正

请求 1 次、重试 0 次，严格 JSON 解析成功。模型输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`，符合输入仅列可能因素、未说明因素如何组合的情形。结构合同通过，5/5 引文位置有效。旧 v1 比较器的“决定句必须与 logic_evidence 完全相同”只适用于已知 AND/OR；套用 unknown 时造成假阴性。v2 比较器依据既有 prompt 合同，对 AND/OR 检查直接逻辑引文，对 unknown 检查空逻辑引文及允许的原因码；复核结果与非 Gold 编写者预期相符。原始运行和首次 v1 比较结果保留不改，v2 另存修正后的比较记录。该修正是评估器合同纠错，不是模型重跑或准确率证据；SMOKE-004/005 未调用。

#### v37 语义门型 smoke 运行准备（2026-09-29；预检就绪、未运行模型）

样例覆盖：无显式运算符但语义明确的替代路径（候选 OR）、共同必要条件（候选 AND）、只列可能因素、只记录事件共现、以及 scope 外出现字面 `or` 的反例（后三类预期均为 unknown）。模型输入与预期标签分属两个文件；runner 只读输入文件，每次只接收一个 case，必须为该条请求单独明确授权，SDK 重试为 0，原始可见响应保留，失败标记 blocked/failed，不修补、不重试。预期标签由政策规则编写，未经专家审核，不可用于准确率或校准结论。在线运行后也只能做定性行为观察，不能代替基于真实手册、独立 Gold 的验证。

#### 语义审核政策与开发回归 v1（2026-09-29；离线完成）

[审核政策](../evaluation/quality_eval/fta_event_scope_semantic_review_policy_v1.md)规定：明确指向同一输出事件的替代路径可提出带原文逻辑证据的 OR 候选；明确共同必要条件可提出 AND 候选；仅共现不能推出 AND；候选门仍不是专家批准。共享/重复事件身份及长复合因果句的节点粒度不能由脚本自动合并、复制或拆分，需保留为人工复核项。六条[回归案例](../evaluation/quality_eval/datasets/fta_event_scope_semantic_review_cases_v1.json)包括三个政策示例和三个 v6 已观察风险；全部明确非 Gold、无模型准确率含义。

测试只验证政策案例的预期处置、v6 S1 的 `unknown + 无 logic_evidence` 仍被标记为待审，以及 E2/E4、E5/E7 不被自动修补；它不实现自然语言通用门型解析器。未改 v6 输出、提示词、生产服务或 Gold；无模型请求。

#### v6 单次受控模型运行（2026-09-29；结构/引文通过，语义未接受）

原始响应、尝试收据、机械评估与[定性复核](../evaluation/quality_eval/runs/fta_event_scope_model_run_v6_dev_comparison_2026-09-29.md)均已保存。请求 1 次、重试 0 次，`finish_reason=stop`，JSON 严格解析成功，模型 7 个节点、3 个 scope，均为 `unknown`；树层级合同通过，证据位置 10/10。v5 的三个结构问题在该单例中未重现。另一方面，S1 引文自身含两条候选路径间的显式 “or”，但模型输出 `logic_evidence=null`、`gate=unknown`；这显示逻辑线索绑定存在漏项。输出还分别建立语义相近的 E2/E4 电芯爆炸节点，并将一段长因果过程压成 E5/E7 复合节点，事件身份与粒度需进一步审查。位置校验只证明引文能回切，不证明其支持事件切分、因果边或门型。没有与真人专家 Gold 比较，不报准确率、F1、校准或泛化；不接受为已批准 FTA Preview，不写 Gold/数据库/生产 API，`fta_ready=false`、`production_ready=false`。任何后续在线请求需新的明确授权。

#### v6 单次请求器接线（2026-09-29；历史：运行前状态）

[v6 请求器](../evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py)使用 v6 提示词和通过合同校验的 label-free 输入投影；本节记录的是在线调用前状态：真实请求需显式 `--authorize-single-request`，最多一次、SDK 重试为 0。实际单次结果见上节；授权已使用，若需再次在线调用，必须重新取得针对该次请求的明确授权。若响应被合同阻断，原始输出保存并标记 blocked，不自动修复或重试。

#### v6 提示词离线准备（2026-09-29；未运行模型）

[v6 提示词](../evaluation/quality_eval/event_scope_tree_prompt_v6.py)针对 v5 的三个结构问题增加了单一层级来源、每个输出节点最多一个 scope、复合替代路径嵌套表达、避免单子项 scope，以及已知门必须显式提供 `unknown_reason: null` 等要求。五项本地回归覆盖方向表达、结构约束、字段完整性、嵌套结构 fixture 和 label-free 输入投影，全部通过。此证据只覆盖提示词文本与本地结构合同；没有模型响应，不证明模型遵循或语义准确。任何后续在线请求须另行明确授权。

#### v5 单次模型运行与离线合同复核（2026-09-29）

原始运行、尝试收据、合同评估及[定性报告](../evaluation/quality_eval/runs/fta_event_scope_model_run_v5_dev_comparison_2026-09-29.md)均已保存。请求一次、重试 0 次、`finish_reason=stop`，严格 JSON 成功。15/15 条引文在引用段落中唯一定位；这只证明可定位，不证明语义蕴含。模型把电芯爆炸和模块容器失效列为 T 的同级子项，但同时把四个 scope 都指向 E1，S2 只有一个子项，S4 又缺少必需字段，因此整树合同 blocked。该单一样例只是提示词局部遵循的定性观察；不与 AI 角色审核标签计算准确率/校准，也不作为 FTA Preview、Gold 或泛化证据。无第二次请求，后续在线调用须重新明确授权。

#### v4 单次受控运行结果（2026-09-29）

原始响应、合同评估、尝试收据和[离线定性对照](../evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md)均已归档。模型输出节点与门作用域通过 JSON 解析，证据引用位置 9/9 唯一匹配；但 S2 仅有一个直接子项，结构合同 fail-closed 阻断，未修改原输出。预测门型为 AND 0、OR 0、unknown 3。AI 角色复核文本的根 OR 只能作为定性参照；它不是人类专家 Gold，且 scope 对应关系未建立，因此无准确率、F1、校准或泛化结论。此次 API 运行只用一次授权、零重试；后续在线调用须重新取得用户明确授权。`fta_ready=false`、`production_ready=false` 保持。

#### thinking-disabled 单次受控对照（2026-09-29；已完成）

用户报告本地凭证已更新后，按已授权方案调用 [v3 请求器](../evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py) 一次：沿用 v2 的同一输入投影、提示、`deepseek-flash`、temperature、8192 token 上限和 JSON mode，只增加显式 `thinking=disabled`。响应为 `finish_reason=stop`，JSON 可解析，得到 5 个节点与 3 个门范围；离线检查 8 条引文均在输入原文匹配，结构错误为空。供应商未提供 reasoning token 数，`reasoning_content` 不存在；请求器不会持久化推理文本。单次对照观察与“thinking disabled”相关，但样本只有一个，不能据此认定普遍根因或性能提升。

安全记录：先前旧 provider 密钥曾意外出现在本地诊断工具输出；用户随后报告已更新凭证。本次只记录 API 请求成功与响应元数据，不读取、输出或保存密钥。v3 单测 8 项、v2 回归 4 项、Figure 7 输入合同回归 4 项及后续离线对照测试通过；v3 preflight 与线上单次请求均成功。正式 Gold、数据库、生产 API 未改变；只有一条已见 Dev 样例的定性比较，独立 Final 仍未创建，readiness 状态不变。

### 模型运行前状态快照（manifest v19 历史）

活动 FTA 研究基线为 [manifest v19](../evaluation/quality_eval/fta_baseline_manifest_v19.json)。评测层已定义“单顶事件模型输入包”和“独立参考 Gold”两套 Schema，并实现来源/引文/图连通/门标签分离校验；12 项合成合同测试通过。NASA XVS 报告已完成整篇40页文本筛查，并视觉检查 Appendix D 的8张树图；因图示已被查看且正文不足以支持完整下层分解，该来源族仅为已见 Dev/弃判边界候选，不符合独立 Final。权利只作暂定内部评估判断，且1998前身及相关 XVS 文档的语义重叠尚未完成核对。当前真实 packet 与 Gold 均为0，模型未运行，无建树准确率结果；生产 API、数据库、正式 Gold 未改，Structure/Quantitative readiness 仍 `blocked`，`fta_ready=false`、`production_ready=false`。

审计日期：2026-09-29（Asia/Shanghai）  
仓库：`Fta_system`，分支 `refactor/v2-monorepo`。  
性质：基于当前工作区源码、文档、测试和可见运行产物的静态/针对性审计；不是生产环境验收。

## Existing Truth Inventory

当前 truth sources：

- 可运行行为与路由：`backend-python/app/api_server.py`；
- 数据语义和跨模块合同：`backend-python/contracts/`；
- 模块职责：`docs/project-structure-v2.md`；
- 正式抽取审核工作流：`docs/extraction-review-build-workflow.md`；
- 候选 FTA 最新范围、指标与限制：`docs/candidate-fta-generation-v1.md`；
- RAG 冻结与运行证据：`docs/rag-baseline-v1.1.md` 及其指向的 dated artifacts；
- 仓库布局检查：`scripts/verify_repo_layout.py`；
- 本次实际执行的测试命令：见本文件“本次实际验证”和 [验收清单](acceptance.md)。

此处的 current truth 是对当前代码与报告的汇总；若摘要与源文件冲突，回到源文件、测试和实际接线路径核验。

## Product Boundary

当前项目提供故障文本抽取、审核/放行/传统建树 API、S210 RAG，以及离线通用检索/Router/候选 FTA 模块。当前范围不包含已校准的自动 AND/OR 判定、全量自动建树就绪、Generic/Router 已切换到 S210 API，或候选 Preview 的正式持久化与 Gold 导入。

## Current Call Chains

```text
POST /api/fta/extract → extraction + evidence + initial review persistence
    → review decisions → /api/fta/release → /api/fta/build_released

POST /api/fta/extract/causal-review
    → extraction → AI causal review → validated snapshot import
    → failure retry by saved extraction result_id

POST /api/rag/query → S210 retrieval/context/evidence/boundary answer

Offline only: raw text → ExtractionResult → Candidate FTA Preview
```

## Dangerous Adoption Actions

不要在当前接管审计中切生产检索器、改数据库 schema、导入候选 Gold、放宽 FTA 门型策略或改写审核历史。不要把 AI 角色审核、模型概率或图示 smoke test升级为真人专家签署/生产准入。任何 API/数据库接线都需要单独设计、迁移与回滚验收。

## Handoff State

截至 2026-09-28，活动 Cause disposition prompt 为 v4：明确列出的自然语言可能原因仍可成为待审核候选边，但每项须与 `top_event` 作语义比较；只释义/同义重述顶事件且没有新增独立上游信息的项按 `causal_summary + relation_only` 留账，语义不清按 `unresolved`；fault/value、参数/位/索引诊断映射仍不得仅凭映射自动连接顶事件。F01681 v4 在线开发复演只执行两阶段（抽取、原因处置），两次请求成功、重试为 0；16 条原因全部 `relation_only`（1 条顶事件释义、15 条诊断映射），候选树 `blocked / no_fta_event_candidates`，没有运行结构/门型阶段。原语料 SHA 匹配，71 条证据引用偏移精确。独立 AI 子智能体只读复核为 `PASS`，非真人专家签署；这是单样本开发证据，不是准确率或 Gold。后续对 Remedy `xxxx=9507` 做了固定原文范围核对：指令只作为 Remedy 保留，不自动新增原因事件/边；Cause/Fault value 与 Remedy 范围差异使 cause-set completeness 保持 `unresolved`。v4 定向测试 14/14、候选树测试 17/17、原文探针测试 10/10、完整后端测试 266/266 已通过；活动 manifest v14 收录当前来源复核及哈希。未改正式 Gold、数据库、生产 API 或 readiness。独立 Final、足够门型真值与有证据的置信策略仍未闭合。

历史审计状态（截至 2026-09-28，manifest v17）：当时活动研究基线为 [FTA baseline manifest v17](../evaluation/quality_eval/fta_baseline_manifest_v17.json)；v16 作为不可变快照，v15 仍是范围 readiness 报告所钉定的证据基线。36 个已见案例仅属 fixture/合同/证据边界回归，相关离线测试不调用当前模型；另有 11 条公开图示门型开发案例。独立范围报告覆盖 47 条、18 个来源簇，结论为 `FTA-Structure=blocked`、`FTA-Quantitative=blocked`。随后筛选了 4 份 FAA/NASA 整本文档：NASA/FAA 两份适合后续开发/评测适配，但代表性树图页已被检查，因此不可作为盲测 Final；NASA CR-108289 仅适合图结构补充；NASA-TM-105505 因实际 PDF 缺少所述附录而排除。当前服务按单条 `FaultRecord` 生成候选树，不能直接把系统级报告作为一棵完整树评测；需要评测专用的有页码来源范围包，并把图示门型参考值与原文证据授权的门型标签分开。独立 Final 仍为 `not_created`；该轮没有模型推理。上述为工程证据审计，非真人专家评审或模型准确率测试；全局 `fta_ready=false`、`production_ready=false`。

2026-09-28 当轮补上了 `fta_ready=true` 的直接合同拒绝测试，Preview 合同测试为 9 项通过；这只证明状态字段守卫，不是建树效果评测。随后建立了候选评测配置锁 v1，精确记录当时解析到的模型别名、调用参数和提示/解析/合同源码哈希；但供应商别名不保证权重不可变，且完整树生成尚未在独立 Final 上执行。因此当时只能证明合同/证据边界可测试，不能报告真实建树准确率；独立来源和完整因果结构/门型 Gold 仍是效果评测前置条件。

后续已建立[建树评测配置锁 v1](../evaluation/quality_eval/fta_generation_eval_lock_v1.json)：它仍描述完整 raw-FaultRecord 多阶段 Candidate FTA runner 的 `deepseek-flash` / `api.deepseek.com`、温度 0、120 秒超时、最多 2 次重试，以及 14 个抽取/处置/结构/门型/解析/合同源码文件 SHA-256；API 密钥未写入。该配置锁不覆盖两次专用 event-scope 单次调用（独立 prompt、重试 0），不能把这两次调用说成完整候选建树流程已运行。两者都是评测配置/记录，DeepSeek 别名不是权重不可变快照。独立完整树 Final 仍为 0 条，故建树效果评测仍 blocked。

## 结论摘要

项目包含多条成熟度不同的链路，不能合并成一个“FTA 已完成”结论：

| 子系统 | 当前判断 | 依据与边界 |
| --- | --- | --- |
| 故障抽取—人工审核—放行—建树 | 后端正式工作流和 API 已实现 | `POST /api/fta/extract`、审核决策、`/release`、`/build_released`；详见 [工作流文档](extraction-review-build-workflow.md)。当前审计未对运行数据库做写入或端到端操作 |
| AI 因果审核 | 已有 API 与可重试持久化流程 | `/api/fta/extract/causal-review` 与基于 `result_id` 的重试接口；接口明确 `human_reviewed=false`、`fta_ready=false` |
| S210 RAG | 当前 S210 API 与证据回答链路已实现；有既有审核/回归记录 | `/api/rag/query`；[RAG Baseline v1.1](rag-baseline-v1.1.md)记录了 30 条语义与 24 条边界 API 回归。报告日期为 2026-09-22，本轮未重新调用外部模型或真实 API |
| Generic Retrieval / Domain Router / Aerospace | 模块与离线实验存在；生产接线未证实 | `generic_retrieval_pipeline.py`、`domain_router.py` 与 adapter 合同可单独测试；[冻结说明](retrieval-platform-v1-freeze.md)和[Router 文档](domain-router-v1.md)明确 S210 API 尚未切换、Router 未接 API |
| 递归证据约束候选 FTA | Preview 服务、合同、离线测试已实现；不具备生产建树资格 | 有 extraction/candidate services 和递归节点合同；尚无对应 `api_server.py` 路由、正式数据库持久化或 Gold 导入 |
| 门型与置信度 | 仍未校准；逻辑门不能由概率单独确定 | 事件级 AI 角色审核 v8：39 项范围处置（37 reviewed、2 `not_applicable`、0 pending），标签 AND 0、OR 1、unknown 36；当前门节点 v6 为 55 个节点、55 reviewed、0 pending，标签 AND 12、OR 17、unknown 26。F30021-C04 定位由 AI 子智能体按唯一 cause scope 解决为 `[332,372)`，其门仍是 `unknown`；这是 AI 审核材料，不是真人专家 Gold。2026-09-28 两条 S120/S150 原文探针验证闭合枚举原因集与嵌套结构可进入 Preview，但门仍因无置信策略为 `unknown`。来源与限制见[候选 FTA 文档](candidate-fta-generation-v1.md) |
| 全量/生产 FTA | 未完成 | `gate_policy_selected=false`、`fta_ready=false`、`production_ready=false`；真实事件概率链路未接入 |

## FTA 候选层的关键语义

当前候选服务从原始文本经 `FaultExtractor` 取得完整 `ExtractionResult`，再逐条提出递归节点、作用域门和关系边。模型失败不会丢弃已抽取结果，可对失败记录重试。候选证据要求精确、唯一定位；重复引文不自动挑选位置。结构或证据不满足条件时结果保持 `blocked` / `unknown`，而不是强行生成可接受的门。

候选服务中的概率是模型对 AND/OR/unknown 的自报判断，不是事件发生概率，也不是经校准的置信概率。只有直接原文逻辑证据、完整原因集合、同一 scope 与显式策略等条件均满足，候选才可进入内部审核状态；这不等于审核批准或生产建树。

截至本审计日，递归候选流程仍是离线/内存 Preview：不通过正式 API 调用，不写数据库，不修改正式 Gold。S120/S150 的 F06000、F35400 和 S210 的 F01681、F30027、F30021 已有完整原文历史开发运行，只证明当时固定提示下结构和引文可被表达与校验，不证明整体准确率或泛化。当前源代码的 Cause disposition prompt 为 v5；上述五个存档运行分别是 v2/v4，不能视为 v5 结果。v5继续要求来源明确、语义独立于顶事件的自然语言原因才可成为候选；摘要留在 `relation_only`，语义不清则 unresolved，故障值/参数诊断映射本身不自动连接顶事件。门型仍独立 fail-closed。F06000 的顶事件重叠/摘要层级、F30021 的重复和缺失证据、F01681 的 `xxxx=9507` Cause/Fault value/Remedy边界均未由当前版本真实运行关闭。NASA Figure 7 v6 是另一套 event-scope runner，10/10 引文位置不能替代身份、粒度、child集或门证据语义验收。所有候选连接仍不得视作已确认因果。

## 当前运行接线与模块存在的区别

- `backend-python/app/api_server.py` 组合了当前 API；S210 RAG 路由使用 S210 runtime retriever 和完整故障上下文加载。
- `GenericFaultRetrievalPipeline`、`RuleBasedDomainRouter` 与 Aerospace Adapter 是独立模块；单元测试通过只证明其合同/离线行为，不代表 API 已使用它们。
- 递归候选 FTA 的 `CandidateFtaApplicationService` 与 `CandidateFtaExtractionService` 被测试覆盖，但当前 API 文件没有候选 FTA 路由；正式 `/api/fta/*` 工作流中的 `build_released` 与该 Preview 不能混称。
- 老的 `/api/fta/full_generate`、`/api/fta/generate` 等生成入口仍然存在。其 DOT/FTA 输出不能被当成证据约束候选流程的审核通过结果。

## 本次实际验证

2026-09-27 在当前工作区执行并通过：

| 命令 | 结果 |
| --- | --- |
| `python scripts/verify_repo_layout.py` | 通过：`repository layout verified` |
| `python -m unittest discover -s backend-python/tests -p "test_*candidate_fta*.py" -q` | 24 tests，OK |
| `python -m unittest discover -s backend-python/tests -p "test_generic_retrieval_pipeline.py" -q` | 3 tests，OK |
| `python -m unittest discover -s backend-python/tests -p "test_domain_router.py" -q` | 4 tests，OK |
| `python -m unittest discover -s backend-python/tests -p "test_rag_api.py" -q` | 4 tests，OK |

这些是当前代码的针对性固定测试，不是完整后端套件、实时 API、线上模型、GPU/向量索引或真实设备测试。本轮未执行全量构建、生产数据库迁移、HTTP 在线回归或生产部署。

### 2026-09-28 外部原文门评估探针

本轮新增隔离评测脚本、测试和运行 artifact，复用 Candidate FTA 的门评估 prompt builder 对 11 个公开图示节点进行文本证据判门；输入使用已核对 PDF 来源页的摘录，模型没有看到 `text_only_gate`、审核理由或 `supports` 字段。DeepSeek Flash 一节点一请求，11/11 请求成功；与 AI 原文证据复核标签描述性一致 11/11（已知门型 9/9、unknown 2/2），9 个决定性引文均唯一绑定在所给文本 scope。执行命令、逐条结果与限制见 [验收清单](acceptance.md)、[Markdown 运行报告](../evaluation/quality_eval/runs/candidate_fta_gate_text_evidence_probe_v1_2026-09-28.md) 与 [JSON artifact](../evaluation/quality_eval/runs/candidate_fta_gate_text_evidence_probe_v1_2026-09-28.json)。

该探针只覆盖候选门评估提示及证据引用校验，不覆盖 raw-text 抽取、原因筛选、递归树结构/连通性或完整应用服务；标签由 AI 依据原文复核，不是真人专家 Gold，且只有 3 个来源簇。当前默认未注入置信策略时服务仍 fail-closed 为 `unknown`。本次候选 FTA 固定测试 33 项与探针合同测试 5 项均通过；冻结 manifest v6 检查 `current`，validator 验证 84/84。pypdf 对 DOE PDF 重复 `/Length` 字典键发出警告，但 PDF 哈希及引文定位检查通过，警告作为评测来源限制记录。没有改 Gold、数据库、生产策略、manifest 或 readiness。

## 治理与工作区风险

- 本审计时工作区存在大量已修改及未跟踪文件，涉及代码、测试、数据集和运行报告；本次只新增/更新真源文档和根 README 索引入口，不清理、不覆盖、不提交其他工作。
- 仓库根目录 `AGENTS.md` 存在，但 `check_project_guardrails.py --mode adoption --truth-dir docs` 仍指出其未包含工具要求的若干治理片段。当前用户提供的 Agent 宪法是会话级指令，不自动等同于仓库本地真源；本次不擅自改写 `AGENTS.md`。
- 根 README 中有 2026-03/09 的历史指标，应按其“仅说明当时运行”的说明解读；不得把这些数字当作当前版本实时指标。

## 当前禁止结论

目前不能声称：`FTA ready`、已完成全量因果/逻辑门 Gold、门置信度已校准、通用检索/Router 已切生产、AI 角色审核等同领域专家签署，或现有回归覆盖真实工业运行风险。

### 2026-09-29 单事件 FTA 开发包（v20）

已从 NASA NTRS 19880001643 建立一个事件范围开发样例：模型输入文件仅包含一个顶事件及 Section 5.0 的带页码/章节定位原文；单独参考文件保留 Figure 7 六节点、三个图示门与文本证据门标签。两文件通过跨 artifact 合同校验，且模型输入投影不包含树图、图示门型或参考 Gold。来源报告记录 SHA-256、公开元数据、已查看状态和未完成的来源族语义重叠审计。

该来源/图示已被评估者打开，故只能算 Dev，不是盲测 Final；独立 AI 角色审核指出两个“Single cell explodes”图示出现是不同节点并修正其误合并。图示门为 OR/AND/AND；文本授权门为 OR/AND/unknown。第三门原文确有宽泛的“单体爆炸 AND 排气口故障”，但没有支持图示精确子项“Two module vents clog”，故按 `scope_ambiguity` 弃判。图示根标签“Module failure”与原文顶事件也不宣称为同义。审核者为 AI 子智能体，不是人类专家。模型尚未推理，不能声称预测效果或专家金标。packet=1、参考 Gold 文件=1，独立 Final=0；正式 Gold、数据库、生产 API 未更改，`fta_ready=false`、`production_ready=false`。

### 2026-09-28 原文候选树完整性复核（Cause disposition v2 前快照）

结构提示现明确区分：`cause_set_complete` 衡量来源限定 scope 中闭合枚举的直接子项是否全部进入结构，不代表某台设备实例已发生，也不要求现场读数；处置为非树项的 cause index 由宿主审计账单独保留，不重复塞入结构未决索引。

- **F35400：**4 个模型阶段均成功；3 节点，2/2 定性阈值条件连接到顶事件；闭合“at least one of the following”列表判完整，叶子已规范化；5/5 候选树引文精确且唯一。
- **F06000：**4 个模型阶段均成功；13 节点，10 个 `fta_event_candidate`，1 项通用摘要留在 exclude 审计账；顶层十项原因和局部两项 either-or 均为完整 scope；17/17 候选树引文精确且唯一。

两条样本的所有门仍为 `unknown`，唯一 blocker 是 `gate_confidence_policy_unavailable`。完整运行产物与命令见[验收清单](acceptance.md)及[候选 FTA 文档](candidate-fta-generation-v1.md)。此处是两个外部手册开发样例，不是独立测试、Gold、真人专家审核或泛化成绩；Gold、数据库和生产路径未变，`fta_ready=false`、`production_ready=false`。

下一阶段不再有门节点定位 pending；应继续补充独立来源和节点级标签评估，再讨论门策略校准、正向接受路径、候选 API/持久化和生产门禁。v6 尚无对应的新模型预测，v5 的 54 条预测不能直接当作 55 条 v6 的成绩。具体命令与门槛见[验收清单](acceptance.md)。

### 2026-09-28 Cause disposition v2 复核（历史策略快照，已被 v3 收紧）

v1 原文回归中的两个问题当时通过 prompt v2 做有界修正并重跑：F01681 的15条故障值解释被提升为通用事件候选，但其“故障值替代集合是否完整”仍 unknown；F30027 的9条原因保留，包含中间状态与成因的完整因果句不再仅因复合句式 unresolved。后续 AI 语义复核指出 F01681 故障值映射不单独证明到顶事件的因果边；因此 v2 的 F01681 映射候选做法已由用户确认的 v3 规则收紧，不再作为当前政策通过证据。两例历史输出中的75条引用仍仅证明位置绑定精确唯一，不证明因果边语义。

这不是门型正确率或泛化结果：F01681 的12个 scopes、F30027 的2个 scopes 仍全为 `unknown`；没有标定门策略、Gold 合并、数据库写入或生产接线。见[候选 FTA 文档](candidate-fta-generation-v1.md)；这段为 v2 历史状态，当前活动清单为 [manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)，v1–v13 保留为历史快照。
