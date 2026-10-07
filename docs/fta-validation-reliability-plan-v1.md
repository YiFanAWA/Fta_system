# FTA 可靠性与验证补强计划 v1

更新时间：2026-10-07  
状态：执行中；当前执行路线以本文件“2026-10-07 当前完成度与下一阶段计划”为准。活动清单为 manifest v52；v51保留内部 locator overlay 接线前的状态，v50保留F30021定位对账前的单例状态，v49保留P2真实来源运行前状态。审核台账的唯一总入口为[当前状态审计](current-state-audit.md)，本文件负责执行依赖与验收条件。P2工程定位合同与离线接线已完成；F30021当前v5真实来源运行仍被阻断，P2语义缺陷关闭、独立 Gold 和范围就绪验收仍未完成。
范围：候选 FTA 生成、事件/门节点审核数据、离线验证和 readiness 声明。  
不在范围：改写 S210 正式 Gold、写入生产数据库、接入生产 FTA API、用模型自报分数冒充现场故障概率。

## 2026-10-07 当前完成度与下一阶段计划

### 当前达到的阶段

项目已有可运行的故障抽取/审核流程、S210 证据型 RAG，以及有递归结构、逐项原因处置、证据约束和阻断门禁的候选 FTA 研究系统。接下来的主任务是证明候选树的语义与泛化质量，并按明确范围验收结构能力。

| 能力 | 已达到的结果 | 当前证据与限制 |
| --- | --- | --- |
| 抽取—审核—放行—传统建树 | 后端流程已接线，保留抽取、审核及建树尝试历史 | 入口见 `backend-python/app/api_server.py`；传统建树合同与递归候选 Preview 不相同，不能用传统 API 成功替代 Preview 语义验收 |
| S210 检索 | 281 条冻结故障实体；39 条历史 Final 查询 R@1=0.9231、MRR=0.9573、候选召回39/39 | [冻结说明](retrieval-platform-v1-freeze.md)；此成绩已参与 parity/后续分析，今后作为历史回归，不当新盲测 |
| S210 RAG与回答边界 | v1.1 范围内30条语义 API 回归、24条边界 API 回归已保存；30条语义请求均 HTTP 200，故障码/引用/回答合同指标1.0；Boundary unsafe/false-reject为0 | [RAG baseline](rag-baseline-v1.1.md)；30条专家初审中5条关系表达问题另经定向复审。API指标与专家语义审核分别引用原报告，不推广为全场景100% |
| 多领域检索 | Common Schema、Adapter、Generic Pipeline、航空40条开发样本与Rule Router已有离线验证 | 当前S210在线RAG仍通过S210服务；Generic/Router尚未切为API默认，真实多领域Shadow和生产迁移未验收 |
| 因果数据 | 具名审核Gold为205条批准关系；296条有决议，91条排除/暂缓，745条尚无具名决议 | [状态分账](current-state-audit.md)；AI审核覆盖281个事件/1041条候选属于另一来源轨迹，不补足真人审核数量 |
| 逻辑门真值 | 具名Gold6个事件：5 OR、1 unknown、0 AND；另有55个AI审核门节点 | 两套集合不能合计成真人Gold，当前不足以证明AND/OR/unknown三类模型可靠性或概率校准 |
| 原因角色/树准入 | 自然语言原因、映射、故障值模式、状态、后果、摘要、处理动作等已由独立role/disposition合同区分 | [合同](../backend-python/contracts/fta_cause_disposition_contract.py)与[服务](../backend-python/fta/cause_disposition_service.py)；64项离线回归通过，模型分类准确率未由此证明 |
| 递归候选FTA | 层级、完整原因账、证据绑定、unknown reason、断开节点、整树阻断合同已实现 | Figure 7 v6结构与10/10引用位置通过，但门证据漏绑、事件身份及复合粒度仍未验收；五条合成smoke中四条整体符合政策预期，一条结构阻断 |
| AI汇总Preview门禁 | 保存汇总中11个事件build_allowed、270个blocked | 是当时AI审核与门禁的范围结果；没有证明最新服务从任意原文生成11棵语义正确树，也不是本轮新成绩 |
| detached observation | 宿主窄规范化和历史响应离线重放已保留两个独立观察节点，无因果边/门，整树blocked | 修订后的真实模型输出尚未在线复验；历史失败响应保持原样 |
| 结构/定量就绪 | 已建立独立的范围评估合同 | 当前两类readiness均blocked；全局`fta_ready=false`、`production_ready=false` |

上轮357/357哈希通过和64项测试通过分别证明工件完整性与离线合同行为。它们不能换算为“357棵树正确”或“FTA准确率100%”。本轮仅设计计划和同步文档版本，没有新增模型运行。

历史原因指标也不能当当前统一成绩：`fta_project_handbook_extraction_baseline_27_final.json`中的causes F1=0.416667来自27条项目手册抽取样本（TP=5、FP=3、FN=11），不是281条S210、55个门节点或最新cause-disposition模型的成绩。后续每份报告必须绑定dataset、population、Gold来源、pipeline版本与指标定义。

### 执行原则与唯一owner

阶段状态由本计划维护，跨数据集/审核轨迹事实由`current-state-audit.md`维护，文件身份/版本/哈希由活动manifest维护；既有Gold与原始模型输出仍是各自的局部事实源。更新已注册文档时派生新manifest，并固定父快照哈希，不覆盖已封存快照。

生产原因角色与树语义属于`backend-python/contracts/`和`backend-python/fta/`；`evaluation/quality_eval/`负责输入/Gold隔离、运行观测和计分。评测器不能为了匹配标签修改生产解析规则、输出节点或门型。API/前端仅在后续接线阶段消费共享合同。

### 执行顺序

| 阶段 | 当前状态 | 目的、输出与结束条件 |
| --- | --- | --- |
| P0 状态与离线合同收口 | 已完成 | v49冻结此前状态与合同审计；FTA实时运行由v50记录，F30021定位来源/范围对账由v51记录，内部定位覆盖层离线接线由v52记录；均不改Gold/数据库/readiness |
| P1 修订观察边界的单次真实验证 | 已完成（仅1个合成非Gold样例） | 请求预算为1且离线验证越界阻断；一次授权在线请求返回两个分别有证据的断开观察，0边/0门、整树blocked，5条引用位置精确唯一。不能据此推断普遍准确率 |
| P2 真实原文开发回归与语义缺陷关闭 | 进行中：内部 occurrence-locator overlay 合同、精确绑定和离线接线已完成；真实模型复验待另行授权 | 显式内部 locator 可解除重复原因证据跨度这一类绑定歧义，但不代表原因语义通过，也不解决顶事件重复、child集合不完整、门置信策略不可用。F30021 v5 原始运行保持不可变、仍 blocked；语义缺陷关闭数仍为0。公开 API、数据库、Gold 与 readiness 未变 |
| P3 独立Gold与来源隔离 | 可与P2并行准备 | 收集完整来源族、审核节点/边/门及证据，冻结开发/回归/最终验证用途；缺少真人审核时明确为AI辅助标签，停止正式可信度结论 |
| P4 冻结配置后一次性Final评测 | 依赖P2/P3 | 在未参与调参的来源上一次运行，报告结构、因果、门型、证据和selective risk/coverage；任何后续调参使此Final转为已见回归 |
| P5 按范围验收FTA-Structure | 依赖P4 | 输出带范围、版本、审核来源、成绩、严重错误与blocker的readiness报告；仅合格范围可以提出结构验收结论 |
| P6 生产候选Shadow与API接线 | 依赖P5及单独设计 | 只读Shadow、资源/失败/回滚验收后再讨论正式接线；现有RAG与传统建树行为保留其独立验收边界 |
| P7 FTA-Quantitative | 后续独立里程碑 | 有真实事件率/失效率、分母、观测时间、单位和依赖模型后评测概率传播；不能用模型门置信度代替设备故障概率 |

### P1：先验证当前窄修正

评测入口为`public_sources/probe_candidate_fta_observation_boundary_v1.py`，业务owner仍是cause disposition和candidate FTA服务。

2026-10-07首次preflight结果：`model_request_performed=false`、新输出路径可用、Gold未加载、SDK/外层重试均0，但`planned_max_model_calls=3`。`--authorize-single-run`表示一次工作流运行，不能直接当作“只发一个模型请求”的保证。历史实际请求数1也不能证明上界1。

1. **离线预算门禁完成**：观察专用runner的`MAX_MODEL_CALLS=1`；第二阶段请求在委托provider之前抛出专用预算异常，报告`model_request_budget_exceeded`并标记`blocked`，首阶段原始响应及SHA-256留存。假provider端到端测试确认`run_once`会保存blocked JSON/Markdown。没有改生产多阶段流程，也没有把重试0当作请求数1。
2. **在线单例完成**：在针对该请求的明确授权下，对合成非Gold输入执行一次 DeepSeek `deepseek-flash` 请求（SDK/外层重试均0）。模型逐条返回`state + detached_observation + descriptive_association`；宿主保留两个分离的观察节点，不将其升级为FTA事件。
3. 运行工件为[原始运行 v3](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json)和[可读报告](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.md)。实际请求1次、成功响应1份、没有失败/重试；节点与处置引用共5条，全部offset精确且唯一，原文与响应SHA-256均通过复核。
4. **窄范围验收通过**：两个观察节点分开保留且均断开；0条relation、0个gate；树整体`blocked`，blockers明确记录`no_fta_event_candidates`及两个断开节点。没有Gold、数据库或生产API写入，`fta_ready=false`、`production_ready=false`。
5. 该结果只证明模型在此合成共现样例上的一次行为与当前政策边界匹配；它不是人类专家审核、不是Gold、不是准确率/校准或泛化成绩，也不证明所有断开观察都能正确分类。
6. P1已关闭；下一步转入P2真实原文开发回归。继续遵循输入与参考Gold分离、每次运行有明确样本/预算、失败保留且不自动修复/重试。任何新的在线请求均须另行明确授权。

已实际执行的预算门禁离线测试与安全预检（没有模型调用；输出位置未被占用）：

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_probe_candidate_fta_observation_boundary_v1 -v
python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --preflight --output evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json
```

离线测试为7项通过；preflight显示`planned_max_model_calls=1`、`sdk_max_retries=0`、`outer_retries=0`、Gold未加载、model request未执行且输出路径可用。在线行为验证仍需针对该次请求另行明确授权。

### P2：解决真实语义失败，而非只补JSON结构

第一轮仅用已见Dev/回归来源，固定当前cause disposition、结构与门评估版本。每个改动只针对一个可复现失败，不同时调提示、规则、阈值和样本。两个运行面分别记录：原文FaultRecord多阶段候选链路，以及独立单顶事件event-scope评测；不能互相代替完成状态。

| 代表案例 | 需要验证的边界 | 不允许的处理 |
| --- | --- | --- |
| F01681 | 顶事件重述按summary留账，诊断映射不自动连顶事件；限定Cause/Fault value/Remedy来源范围 | 仅因位于Cause段就增加因果边；把处理指令补成当前原因 |
| F30027 | 自然语言可能原因与故障值模式分别处置，局部替代scope独立保留 | 把全局原因列表统一改成OR |
| F30021 | 重复原句必须凭来源scope/明确定位绑定，无法唯一定位时留unresolved并阻断 | 默认选第一个字符串匹配位置 |
| F06000/F35400 | 合法嵌套、完整单子项not_applicable和多原因scope分别成立 | 为符合简单树图而摊平层级 |
| NASA Figure 7 | 关闭门证据漏绑、重复事件身份、复合节点粒度三项语义发现 | 直接改写既有v6输出；把10/10偏移匹配当作因果/门语义通过 |

event-scope v8目前只有政策smoke运行，Figure 7真实输入runner仍需有界接线与新运行记录。输入只传原文、顶事件和定位；图示参考、文本授权门型和人工标签隔离在参考文件中。节点身份和复合粒度必须先有可复核的匹配标准；不靠重复创建节点、强行切句或摘要来消除blocker。

#### P2a：输入/输出合同与已见真实来源案例离线审计（2026-10-07）

只读审计报告：[逐项审计报告](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.md)及[机器可读审计账](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.json)。检查范围为 F01681、F30027、F30021、F06000、F35400 与 NASA Figure 7，逐项覆盖原因角色、事件身份、层级、子项集合和门证据。

审计发现：当前 `CauseDispositionService` 为 v5；五条 SINAMICS 存档运行仍分别使用 v2/v4，NASA Figure 7 存档运行使用独立 event-scope v6。它们是历史开发证据，不是当前实现的回归成绩。本轮没有模型请求，未改 Gold/数据库/生产 API/readiness。离线候选服务35项、原因处置16项、event-scope v8与runner合同8项测试通过；manifest v48 的367个登记工件哈希有效。该结果只关闭 P2 的合同审计和历史案例盘点，不关闭语义缺陷。

#### P2b：当前版本真实来源受控运行（F30021 单例已完成，2026-10-07）

用户针对 F30021 授权最多四次模型请求；运行实际完成四阶段请求，成功响应4份，外层/SDK重试均为0。输入 SHA-256 固定为 `f3178a6c9c46aa2109a44eb118c6a8730ebfdd6d9a6f5660147529f01ce41d31`，当前原因处置提示为 v5；原始响应已保留。逐项审计见[运行语义审计 v2](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.md)及[结构化审计账](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.json)。

结果：抽取1条FaultRecord、5个cause值；3个进入AI候选，1个relation_only，1个因同一句在 Possible causes 与 r0949 故障值释义中出现两次而按既定规则 unresolved。顶事件引文 `ground fault` 在原文出现4次，树证据唯一性检查阻断；Possible causes四项只有三项进入child集合，complete=false；门型unknown且无门证据，符合“不由列表推OR”的规则。整树blocked，未改Gold/数据库/生产API/readiness。

运行后发现并修正评估runner的派生统计口径：模型提议与宿主证据门禁后的最终处置现在分开计数，并单独校验原因处置证据。原始运行文件没有重写；[离线复核副本](../evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.json)保留原始响应并修正派生摘要，没有新模型请求。

#### P2c：occurrence/scope 证据身份问题（历史离线回归与定位对账；当前接线见 P2e）

补充代码审计：候选FTA结果合同会序列化完整 extraction evidence spans，包括每个 CAUSE 命中的原始 quote、start/end、value_index，以及相应 CAUSE_CONTEXT 上下文。因此 F30021 的 Possible causes 与 Fault value 两个候选位置已能从 Preview 工件中并列复核；CauseDisposition 对 unresolved 不附 `evidence`，避免把待选位置记成确认引用。当前未发现必须新增 `pending_locator_candidates` 共享字段的充分证据。固定离线测试现同时覆盖真实 F30021 重复位置、既有重复顶事件阻断和唯一引用正例；合同不放宽。只有当真实审核端无法消费现有 Preview 才提出共享审核/API合同变更，并先确认唯一owner与持久化影响。

先审查 `TextExtractionAdapter._build_evidence_spans` 对重复cause文本的定位与 `EvidenceSpan.value_index` 绑定：当前同一cause索引接收两个不同段落的跨度，`source_id + start/end` 已能区分出现位置，但 span 未记录可机器消费的来源scope；原因处置服务因此正确地停止自动选择。当前未决处置不保留结构化的候选跨度列表，人工审核需要回查同一 extraction result 的 CAUSE/CAUSE_CONTEXT span。已新增 F30021 离线固定回归，验证 Possible causes 与 Fault value 两处原句都精确留存、同属一个值索引且仍判歧义；未放宽门禁、未改共享合同。下一步先决定人工复核契约是否需要在 `unresolved` 项上单列 `evidence_candidates`/scope 元数据，及由哪个审核/API owner 消费；不得把候选跨度误记为已确认证据。禁止默认选择首个字符串命中，也禁止通过放宽唯一性门禁掩盖歧义。若要改核心共享合同，先报告字段/API持久化影响并停下取得确认；在确认前仅维护当前安全行为回归。

**2026-10-07 定位对账补充（当时状态）**：已有 AI 子智能体审核材料选中 `[332,372)`，原文重新计算确认它是唯一位于 `Possible causes` scope `[166,372)` 内的完整引用；第二次出现 `[468,508)` 位于 r0949 故障值说明。离线脚本核对源哈希、scope 唯一性、两处 quote/offset、AI 非真人/非 Gold provenance，以及最新 v5 run 的 unresolved/blocked 状态，7项回归通过。该旧定位决定当时没有应用到最新 run；该历史原始运行仍不可变。后续内部消费合同的状态以 P2e 为准。

#### P2e：内部 occurrence-locator overlay 合同与离线接线

**目标**：允许调用方把经过明确复核的“原文出现位置”作为独立 overlay 传入候选 FTA 内部服务，解决重复文本位置无法唯一绑定的问题；overlay 只证明位置选择，不证明语义、因果、层级或门型。

实现包括：

- `EvidenceOccurrenceLocatorReview` 保存 extraction/record 身份、原文 SHA-256、目标字段与索引、所选跨度、scope、review id、provenance、真人专家标记及理由；`formal_gold` 始终为 false。
- `EvidenceLocatorReviewResolver` 对源哈希、精确 offset、scope 内唯一性、字段/index 匹配和重复 review target 做 fail-closed 校验。
- CauseDisposition 和 Candidate FTA 提示只能使用所选的精确 extraction quote；模型扩写、没有 overlay 的重复引文、scope 内仍重复或过期原文都不能自动修复/猜选。
- 原因处置批次和候选树序列化保存 locator review 元数据，便于后续检查这一选择从何而来。应用服务只透传显式 review 参数；当前没有 HTTP/API 入口或数据库持久化。

**离线验收**：locator 合同/解析器、CauseDisposition、Candidate FTA、应用服务透传及递归树回归均通过。测试只证明代码合同和 fail-closed 行为，不证明在线模型语义或审核判断正确。本轮无模型请求；Gold、数据库、公开 API、原始运行、`fta_ready` 与 `production_ready` 均未改。下一步需另行授权并创建新的受控运行；不得覆写 v5 原始输出。新运行必须分别复查重复原因是否正确绑定、顶事件唯一性、完整 child 集合、因果边、scope 和 gate evidence；任一问题仍存在，整树继续 blocked。

退出条件：至少一个合法嵌套正例和每类关键反例符合合同与语义审核预期；所有观察到的缺陷标为已关闭、有证据的限制或明确待审。仍有断开/未决节点时保留整树blocked；不要通过删除可疑项提高“成功率”。

### P3：建立可用于可靠性证明的真值

先以60～100个门节点作为收集目标，并同步标注事件身份、因果边方向、child集合、output和证据。AND/OR/unknown各类目标至少15个，作为小规模试点的覆盖目标；数量本身不代表统计充分。来源不足就报告缺口，不强填门型。正式结构质量报告必须拥有完整参考结构，仅有Gate标签不足以评价整树。

- 现有已见的55个AI门节点、Figure 7和合成smoke用于Dev/行为回归；不把其中一半改名为Final。
- 来源簇按完整手册/报告族、修订版及近重复文本分组。S120/S150和S210的重合内容保持near-transfer用途；Final使用未参与提示或规则改动的新来源族。
- 开发/回归与Final按来源族隔离。校准如需另设，亦按来源隔离；数据不足时先做Dev与一个盲测Final，不硬拆三个小集合。
- 每个标签保留实际审核者类型、审核者、日期、原始结论、修订链与证据版本。AI扮演专家仍登记为AI角色；具名审核来源按原材料记录，不假定已经独立验证身份。
- `diagram_reference_gate`与`text_authorized_gate`分别标注。模型只看到正文时，不能用仅存在图里的逻辑或更具体子项处罚其合理unknown。
- 对现有40条revise按证据可补性建立队列；补证/修订未确认前保持pending，不并入批准Gold。745条尚无具名审核决议可按风险分批扩展，无需把全量人工完成当作开发运行的前置条件。

退出条件：来源登记、去重/分组、标签schema、审核来源、参考结构、模型输入投影和冻结哈希均通过；Final来源未参与开发。缺真人复核时可以做探索实验，但不报告正式专家真值成绩。

### P4：冻结后评价真实建树质量

冻结provider/model标识、解析器、prompt、cause disposition、输入包、reference、来源分组、token/timeout预算和重试设置；供应商别名不能保证权重不变，报告实际响应标识及时间。Final只跑一次，不按结果修改query、参考树或门标签。失败输出和blocked案例进入分母。

| 指标 | 口径 |
| --- | --- |
| JSON/结构有效率 | 所有尝试中可严格解析、满足图合同的比例；blocked/失败另报，不能删去 |
| 事件节点Precision/Recall | 依据冻结的事件命题/身份匹配标准；同义表达可匹配，错误对象、方向或粒度单独归类 |
| 因果边Precision/Recall/F1 | 同时匹配端点、方向、关系类型；诊断/共现关系不可计为因果边 |
| 门型Macro-F1与混淆矩阵 | AND/OR/unknown逐类报告样本数及分母；精确child/output scope匹配后才比较标签 |
| 门范围完整率 | child集合和output均与参考范围匹配；gate标签相同不能掩盖作用域错误 |
| 证据定位有效率 | quote与原文offset精确往返；这是机械指标 |
| 证据语义支持率 | 独立审核证据是否支持节点、因果边及门关系，单独报告partial/unsupported |
| Coverage / Selective Risk | coverage=被接受的AND/OR范围数/全部可评范围数；risk=被接受但错误的范围数/被接受范围数；接受0项时risk为N/A |
| 弃判与阻断分布 | 按稳定reason code报告unknown/blocked原因；避免把安全弃判与模型漏判合成一个错误类别 |

数值门槛与严重错误条件在Final运行前冻结，经领域审核确认后才用于验收，不能看到成绩再降门槛。模型自报分数仅是待校准信号。缺校准样本或策略未配置时保持unknown及对应reason code，不以高分覆盖证据不足。

### P5～P7：分别验收结构、接线与定量

结构验收报告由既有scoped readiness owner承载，至少包含scope/data/source版本、审核来源、模型版本、错误样本、指标、门槛、remaining blockers。只有限定范围内节点/因果/门与证据均满足要求时，才允许提出`FTA-Structure Ready`范围结论；单棵Preview仍遵守候选合同，全局/生产标志不自动提升。

API和数据库接线在结构范围验收之后单独设计：先只读Shadow，保存输入/候选/判定/耗时/失败及审核历史，验证资源预算、超时、重试、幂等、权限和回滚。传统流程与候选Preview的合同映射必须明确；前端只展示owner状态与证据。Generic多领域RAG的Shadow是另一条发布任务，不能用FTA离线通过替代。

定量FTA依赖实际事件概率或失效率、暴露时长/分母、样本单位、依赖与共因模型。没有设备数据时标为unavailable，不阻断已达标范围的定性结构验收，也不宣布Quantitative Ready。AND/OR的模型置信分布与设备故障概率分别保存。

### 验收命令、文档与Git边界

离线核心回归继续使用既有cause disposition、candidate、recursive candidate及观察边界回放测试；文档清单通过活动manifest的生成`--check`和validator。具体实际运行结果写入[验收清单](acceptance.md)。新runner、模型运行和独立Gold各自另记录命令/结果，不能沿用旧的64 tests作为新阶段验证。

2026-10-07开始本轮文档设计时，分支`refactor/v2-monorepo`、HEAD `deff690`、工作区1312项变更/未跟踪文件、staged为0。后续实现按owner列出明确文件范围；未提交用户内容原样保留。每项模块验收后形成可review的diff，只有在对应授权下才提交/推送。

治理检查的既有债务：`check_project_guardrails.py --truth-dir docs --mode adoption`未通过，根AGENTS缺少脚本要求的四段固定规范片段；现有docs过渡目录已被识别。该问题发生在本轮文档改动前，保留为独立治理任务，本轮不改agent宪法或迁移真源目录。

本轮计划交付完成条件：当前完成度与未来任务明确分开；路线只拥有一个计划文档；所有链接与owner有效；v45/v46/v47历史快照固定、活动v48可确定性重建且工件哈希校验通过；P1只在其单个合成非Gold样例范围内验收通过，Gold/数据库/生产API及全局readiness未变。后续阶段执行完成条件按P2～P7逐项验收，不能把单例通过或计划文档写完视作FTA全部完成。

## 历史工作记录（以下按当时版本解释）

以下保留早期工作项、发现与运行记录用于追溯；涉及“下一步”“当前”等措辞时，以本文件上面的2026-10-07路线及活动manifest为准。

## 2026-09-29：Figure 7 v6 单次模型运行（结构通过，语义待解决）

在针对该次请求的明确授权下，对既定 label-free Development 输入仅调用一次 v6 runner，SDK 重试为 0。输出 7 个节点/3 个 scope，结构合同有效，10/10 个引用位置精确唯一；v5 的重复 scope、单子项 scope 与门字段缺失未重现。原始响应和机械评估保留，见 [v6 运行](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json)、[assessment](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v6_2026-09-29.json) 和[定性复核](../evaluation/quality_eval/runs/fta_event_scope_model_run_v6_dev_comparison_2026-09-29.md)。

本例仍未达到语义验收：S1 的证据句包含显式替代连接词 `or`，预测却为 `unknown` 且无逻辑证据；E2/E4 的重复事件身份、E5/E7 的复合节点粒度也未解决。先把这些情形沉淀为开发回归和明确的语义审查规则，不凭单一 seen-Dev 输出宣布 v6 语义正确，也不立即以同一样本反复调 prompt。此运行没有 Gold 比较、独立 Final、数据库或生产写入；`fta_ready=false`、`production_ready=false`。任何后续模型请求需新的明确授权。

## 2026-09-29：事件范围语义审核政策与回归 v1（离线完成）

新增 [语义审核政策](../evaluation/quality_eval/fta_event_scope_semantic_review_policy_v1.md)及[六条回归案例](../evaluation/quality_eval/datasets/fta_event_scope_semantic_review_cases_v1.json)。明确指向同一输出的替代路径可提出带源句证据的 OR 候选；明确共同必要条件可提出 AND 候选；同一事件上下文中的共现本身不能推出 AND。门候选仍需审核，不自动成为 Gold。共享事件身份以及长复合因果句的拆分边界均保持人工复核，不自动合并、复制或拆分。

该回归保护的是审核结论和边界，不实现基于 `and/or` 字符串的通用规则引擎，不测试模型分数，也不改变 v6 既有输出。测试与 Manifest v34 只覆盖离线评测文件；正式 Gold、数据库、生产 prompt/API 及 readiness 未改变。完成条件为政策案例通过、v6 观察到的问题仍为待审、manifest artifact hashes 全部有效；更广泛的语义验证仍需多来源独立 Gold。

## 2026-09-29：Event-scope prompt v7 离线候选

在 v6 prompt 之上新增证据绑定要求：输出 `AND/OR` 前，逻辑引文必须直接表达当前 scope 的 child 间关系，并将该 child 组合或替代路径连到同一 output。连接词孤立出现、同一事故中共现，或连接词与当前 output 无关，均保留 `unknown`。已见 Figure 7 S1 的完整句是回归目标；三个反例覆盖共现、显式共同条件及范围外连接词。

实现位于 [prompt v7 候选](../evaluation/quality_eval/event_scope_tree_prompt_v7.py)，由 [五项离线测试](../evaluation/quality_eval/test_event_scope_tree_prompt_v7.py)验证。该测试还确认输入只从现有 label-free packet 投影构建，不包含 diagram/text Gold。运行器仍绑定 v6；v7 尚未进行模型推理，不能据此声称语义缺陷已修复。v6 原始输出和失败观察未修改，Gold/数据库/生产行为未变，readiness 保持 false。活动记录见 [manifest v35](../evaluation/quality_eval/fta_baseline_manifest_v35.json)。

## 2026-09-29：Event-scope prompt v8 离线候选

用户指出有些门型不会直接出现 `OR/AND` 字样，需要理解完整语义。v8 因此不把运算符或固定连接词当作识别前提：多个独立替代路径明确指向同一输出时可提出 OR；多个共同必要条件明确共同指向同一输出时可提出 AND。不是看到两个原因就推门型；证据必须直接覆盖各 child 命题、它们的替代/联合逻辑关系及同一 output。列表、事故共现、scope 外的词面 `or`、不连续证据或真实歧义均保持 `unknown`。

实现位于 [prompt v8 候选](../evaluation/quality_eval/event_scope_tree_prompt_v8.py)，由四项离线测试及六条非 Gold 回归覆盖。该验证只检查 prompt 规则、反例和 label-free 输入；v6 原始输出、Gold、数据库、生产行为和 readiness 均不变。活动记录见 [manifest v36](../evaluation/quality_eval/fta_baseline_manifest_v36.json)。

## 2026-09-29：Event-scope prompt v8 语义 smoke 运行准备（v37 历史快照）

为落实“隐含门型需要理解语义，不能靠枚举 OR/AND 字样”，新增 5 条合成行为样例：无显式运算符的替代路径、共同必要条件、原因列表、事件共现、scope 外的词面 `or`。输入与预期标签分离，runner 只读取输入文件；标签为编写者按审核规则给出的预期，不是人类专家 Gold。runner 每次仅运行一个 case，需针对该 case 明确授权，最多发出一次请求，SDK retry=0；保留原始可见输出，失败即标记 blocked/failed，不自动修复或重试。此处记录的是 v37 生成时的预检状态；实际单次输出和离线对照见下节，v37 快照仍保留当时 live request=0 的事实。

## 2026-09-29：SMOKE-001 单次运行与非 Gold 政策对照（定性）

针对 SMOKE-001 获得用户单次授权后，请求 1 次、零重试。模型以隐含语义判断两条不同替代路径均指向 `pump shutdown`，输出 OR；完整决定句被用作 `logic_evidence`。严格 JSON 解析成功，树结构合同有效，5/5 引文位置匹配。请求后离线读取单独保存的编写者政策预期，Observed OR 与 Expected OR 一致。该预期未经人类专家审核，且输入为合成样例，所以仅记录为单例定性匹配，不是模型准确率/校准/泛化证据。原始响应、assessment、attempt receipt、比较结果均保留；没有自动修复、重试、Gold/数据库/生产写入。活动快照见 [manifest v38](../evaluation/quality_eval/fta_baseline_manifest_v38.json)。

## 2026-09-29：SMOKE-002 隐含 AND 单次运行与非 Gold 政策对照（定性）

用户对 SMOKE-002 单独授权后，请求 1 次、零重试。原文没有字面 AND；模型依据“容器壁被腐蚀削弱”与“内部压力超过设计限值”必须同时成立，且单独任一条件均不足，输出 AND，并将完整句绑定为 `logic_evidence`。严格 JSON 解析成功，结构合同有效，5/5 引文位置匹配。请求后离线读取分离的编写者政策预期，Observed AND 与 Expected AND 一致。该样例同样不是专家 Gold 或真实来源；两条匹配结果只构成定性观察，不报准确率、校准或泛化。原始响应、assessment、attempt receipt 和比较结果保留，无自动修复/重试或 Gold/数据库/生产写入。活动快照见 [manifest v39](../evaluation/quality_eval/fta_baseline_manifest_v39.json)。

## 2026-09-29：SMOKE-003 unknown 策略核验与离线比较器合同修正（v40）

针对 SMOKE-003 的单次授权请求已完成：模型将只列出可能因素、但未说明组合逻辑的三个 child 保持为 `unknown`，`logic_evidence=null`，`unknown_reason=no_direct_logic_evidence`；结构合同通过，5/5 引文位置有效。首次使用 v1 比较器时出现 `requires_review`，原因是比较器无差别要求 `logic_evidence` 与预期决定句逐字相同。这一要求与 prompt 明确规定的 unknown 输出合同冲突。

没有修改模型响应、输入或预期标签。新增离线比较器 v2：AND/OR 检查逻辑引文是否与决定句精确匹配；unknown 检查门型为 unknown、逻辑引文为 null、原因码在允许集合内，并验证参考上下文确实在模型输入中。原 v1 比较结果保留为诊断历史，修正后的比较另存 v2 artifact。此修正只修评估口径，不是模型重跑、语义金标或准确率提升；SMOKE-004/005 未调用。该段为 v40 历史状态，当前活动快照以 [manifest v41](../evaluation/quality_eval/fta_baseline_manifest_v41.json) 为准，readiness 继续为 false。

## 2026-09-29：SMOKE-004 事件共现边界单次观察（v41；合成非 Gold）

针对 SMOKE-004 的单次明确授权请求已完成：1 次请求、0 次重试，`finish_reason=stop`，严格 JSON 解析及树结构合同通过，4/4 引文位置有效。模型保留压力升高和温度升高两个候选子事件，但没有把共同出现误判为 AND 或 OR；输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。离线 v2 比较与编写者的非 Gold 政策预期一致，语义正确性没有经过专家评估。四条合成观察不能用于准确率、校准或泛化结论；SMOKE-005 尚未运行，Gold、数据库、生产 API 与 readiness 均未改变。

## 2026-09-29：SMOKE-005 无关词面 OR 与结构阻断（v42；合成非 Gold）

针对 SMOKE-005 的明确单次授权请求已完成：1 次请求、0 次重试，`finish_reason=stop`，严格 JSON 解析成功，3/3 引文位置有效。模型没有把无关显示选择句中的 `red or amber` 当成泵停机的 OR 证据，输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。但模型把“alarms A and B were both logged”合并成一个 child，形成单子项 gate scope；结构合同报 `gate_scope_requires_at_least_two_children`，整份结果为 blocked。离线比较为 `requires_review`：预期/观察门型相符，但结构无效，故不是整体行为通过。遵守不自动修复/重试，保留原始输出。该合成观察不构成专家 Gold、准确率或泛化证据，Gold、数据库、生产 API 和 readiness 均不变。

## 目标

把当前“有证据约束的候选 FTA 研究原型”推进为可复核、可重复评测、能清楚说明适用边界的结构化 FTA 流程。逐项解决：原因语义混杂、真值与来源隔离不足、unknown 原因不可比较、实验版本难追踪，以及定性结构与定量概率门禁混在一起等问题。

完成本计划不自动等于全量 S210 FTA Ready 或生产就绪；每个阶段只对其明示范围作结论。

## 2026-10-07：状态分账、原因角色与 v44 离线回归对账

- 已核验并分开记录具名因果 Gold v7、具名 AND/OR Gold v1、AI 授权 Batch02–Batch99 全量审核、事件范围 v8、Gate-node v6，以及 AI provisional 因果视图；这些集合粒度/交集不同，不相加。可复算数字与边界以[当前状态审计](current-state-audit.md)为唯一总入口。
- 原因角色与建树处置合同现覆盖自然语言因果条件、诊断映射、故障值模式、状态、后果、因果摘要、处理动作、其他及混合未决。只有证据绑定且角色/处置相容的原因/状态候选可进入 Preview；诊断映射不自动连边，描述性共现只能保留为断开 observation，未决项 fail-closed。正式 Gold、数据库和生产 API 未改变。
- 2026-10-07 离线专项回归 60/60 通过；活动快照 v44 的重建检查通过，旧快照 349/349 哈希有效。该结果是代码/合同/历史响应离线重放证据，不是新模型在线语义准确率。
- 新的 detached-observation 在线复验尚未获针对该请求的明确授权，未调用模型；原始输出不修复、不重试。全局 `fta_ready=false`、`production_ready=false` 保持。当前活动清单 v45 仅记录状态分账，不改变 Gold、数据库或生产路径。

## 2026-09-29：单事件树层级合同收口（已实现，离线范围）

本阶段将 gate scopes 定为评测输出中的唯一层级来源。旧 `parent_id` 不再作为第二份层级真相，只能与 gate scope 推导结果比对；一旦冲突，合同返回 blocker，原始模型输出保持不变，不做自动修复、重挂或摊平。正例覆盖嵌套 OR→AND；反例覆盖父子冲突、重复/多父关系、单子项 gate、成环层级、畸形节点标识和 `complete` 状态谎报。当前已保存的 Figure 7 v3 输出被 6 个 blocker 阻断（新版结构状态缺失也单独记录）。该合同只用于离线评测，不接入生产 FTA 服务。停止条件：真实 v3 输出被同一合同稳定拒绝，合法嵌套正例通过，冲突反例确认不改写输入，且活动 manifest/验收文档哈希一致；完成后将样例保留为开发回归，后续改动需用新来源验证。

## 2026-09-29：事件范围提示词/单次请求器 v4（已在线运行一次，结构阻断）

为验证新层级合同是否能改善模型输出，新增独立评测 prompt 与 one-shot runner，不改旧 v3 请求器和历史 artifact。v4 规定 gate scopes 是唯一层级来源、不输出 `parent_id`；节点与 scope 引文必须绑定 `segment_id`；scope 归属证据和 AND/OR 直接逻辑证据分开，`unknown` 不得伪造逻辑引文。runner 固定 DeepSeek 端点/别名、thinking disabled、JSON mode、8192 输出上限、120 秒超时和 0 重试；Gold 不进入模型输入，reasoning 文本不持久化。经单次明确授权，实际完成 1 次请求、0 次重试，返回严格 JSON。离线合同发现 S2 scope 只有 1 个直接子项，结构阻断；9/9 个引文仅通过逐字位置检查，语义蕴含未评估；3 个门标签均为 `unknown`。对照只涉及已见 Development 单样例，AI 角色参考并非人类专家 Gold，也没有经过验证的 scope 一对一映射，因此只记录定性差异，不报准确率/校准/泛化。未改 Gold、数据库、生产 API 或全局 readiness，`fta_ready=false`、`production_ready=false`。

## 建立计划时基线（审计于 2026-09-28）

- 当前候选 FTA 合同/离线工作流以 [证据约束候选 FTA](candidate-fta-generation-v1.md) 为主；它记录递归 Preview、事件级审核 v8、门节点集 v6 和仍未关闭的概率/生产门禁。
- `FaultRecord.causes` 当前是 `tuple[str, ...]`。候选 FTA 要求每个输入 cause index 至少映射到一个有证据的候选节点；无法映射时整棵候选会被阻断。
- 当前文档声明：事件级 v8 为 37 条 AI 角色审核、2 条 `not_applicable`、0 pending；具名专家逻辑 Gold 只有 6 条（5 OR、1 unknown、0 AND）。这些集合的来源身份不同，不合并报告成一份专家 Gold。
- S120/S150 与 S210 有故障码和 Cause 文本重合，只能作为同厂商跨手册/版本 near-transfer，不作为独立跨领域泛化证明。历史 v3 audit 使用 v5 的 54 个门节点；当前 v6 复核为 55 个节点、53 个同码节点，34 个 scope 引文逐字重现，即 34/55 总体、34/53 同码条件。当前口径以 [overlap audit v4](../evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.md) 为准。
- 建立计划时（2026-09-28）的审计记录：项目已有 `evaluation/quality_eval/runs/dataset_registry_v1.json` 和 RAG baseline manifest，但当时尚未发现覆盖 FTA 当前合同、Gold、审核集、split、probe、Preview schema 和 superseded 关系的单一 FTA baseline manifest；后续已建立 FTA baseline manifest v1–v19，当前版本见 `docs/README.md`。
- `CandidateFtaTree` 的 `fta_ready`、`production_ready` 当前都强制为 false。真实事件概率数据链路尚未接入；门概率语义是未校准模型估计。

## 工作项与完成标准

### 1. 冻结 FTA 实验真源与版本清单

问题：合同、数据集、审核结果、切分、模型探针和 Preview 有多个版本，当前权威版本及已废弃版本需要跨文档人工推断。

处理：先审计现有 dataset registry 和各 FTA 当前文档；确认 owner 后建立或扩展唯一 FTA baseline manifest。清单至少记录 artifact 路径、版本、SHA-256、数据角色（Gold/dev/calibration/validation/regression）、review provenance、来源簇 split、模型/提示/合同标识、Preview schema，以及 superseded-by。不要复制第二份职责重叠的通用 registry。

验收：

- 每项活动评测/审核产物能追溯到唯一当前输入和来源哈希。
- 明确区分正式/具名专家标注、AI 角色复核、开发样本、校准候选和最终验证集。
- 历史版本保留但标成 superseded/历史，不能被误读为当前成绩。
- `docs/README.md` 与 `candidate-fta-generation-v1.md` 对当前清单的引用一致。

状态：完成（历史变更记录）。工作项 1 首次建立 manifest v1；工作项 2 建立 manifest v2；工作项 3 将候选树合同升级后建立当时活动的 manifest v3。工作项 4 完成时，manifest v4 是当时活动清单；现由 [FTA baseline manifest v5](../evaluation/quality_eval/fta_baseline_manifest_v5.json) 取代，v1–v4 均保留为历史快照。现有 Dataset Registry 仍只负责数据集生命周期、标签、样本数与 SQLite 导入事实，没有把研究工件版本账混入其中。

### 2. 在 FTA 前增加原因语义角色与处置判定

问题：同一 `causes` 列表可能混有真实原因/条件、诊断映射、故障值模式定义、后果、状态、因果摘要和 Remedy；当前“所有 cause index 都要落为树节点”的约束会把非树原因项也推入树，造成断开节点和整树阻断。

状态：完成（2026-09-28）。用户确认“未决原因保留待人工补证，不自动绑定；重复短语不自动选位置”。实现限定在离线候选 Preview；正式 Gold、数据库和生产 API 未改。

**v3 在线复演发现的追加阻断（2026-09-28）：** 固定 F01681 原文的 15 条 fault-value/parameter 映射均被隔离为 `relation_only`；但 index 0 的 Cause 文本 “The parameter cannot be parameterized with this value.” 被提出为唯一候选，独立 AI 子智能体认为它可能只是顶事件 “Incorrect parameter value” 的释义/重述，未提供独立上游机制。故原因语义分类尚不能视为闭合：需在 disposition 层区分 `causal_condition` 与 `causal_summary`/顶事件释义，避免仅因出现在 Cause 段就自动产生有信息量的因果边。

**追加验收条件：** 对与顶事件仅同义重述、未增加可辨识原因/触发条件的信息，不应自动作为 FTA child/cause edge；保留原始抽取条目和证据，可按合同标为 `causal_summary` + `relation_only` 或 `unresolved`。正例仍须允许包含独立机制的自然语言原因；诊断映射仍不得仅凭映射连边。先加离线正反例测试并通过，再考虑是否另行授权在线复演。该发现不改变用户确认的“明确自然语言可能原因可进入待审候选”主规则，而是补上“内容须提供非循环原因信息”的边界。

### 已实施合同 v1

**问题与边界。** `FaultRecord.causes` 是抽取层保存的原始字符串事实；不能把它改造成 FTA 已确认原因，也不能因 FTA 过滤而丢失。候选 FTA 当前以“所有 source cause index 都要映射到树节点”作为覆盖门禁；F01681/F30027 已证明参数/故障值诊断映射和通用 Cause 摘要会被混入这批输入。修复只改变候选 FTA 的中间解释合同与树输入选择，不改抽取结果、正式 Gold、数据库或生产 API。

**唯一 owner 建议。** 在 `backend-python/contracts/` 新增不可变的 cause disposition contract；在 `backend-python/fta/` 新增逐项解释/校验服务。该服务创建角色与处置，candidate FTA extraction service 只消费经验证的解释批次；API/controller 不实现分类规则，`FaultRecord` 不承载 FTA 业务状态。

**数据流。**

```text
FaultRecord.causes + 原抽取 EvidenceSpan（原样保留）
        ↓
CauseDispositionService（只产生可审计提案）
        ↓
CauseDispositionBatch（逐 source cause 完整覆盖）
        ↓
CandidateFtaExtractionService（只把 fta_event_candidate 送入树结构）
        ↓
拓扑/证据/门型既有 fail-closed 校验
```

**逐项合同。** 每个 cause index 恰有一个记录，包含：

```json
{
  "source_cause_index": 0,
  "source_cause_text": "原始 causes[index]，逐字保留",
  "semantic_role": "causal_condition",
  "fta_disposition": "fta_event_candidate",
  "evidence": [{"source_id":"input_text","quote":"原文连续引文","start":0,"end":12}],
  "reason_code": "direct_causal_or_condition_statement",
  "review_status": "ai_proposed",
  "provenance": "fta_cause_disposition_model"
}
```

V1 采用**单一主角色 + 独立处置**，不允许多角色数组，避免一条原因被多路重复计入；无法将复合短语安全归为一个角色时用 `mixed_unresolved`，处置必须是 `unresolved`，不自动切句、不猜证据位置。逐项记录通过 index 绑定，不以文本相等匹配，避免重复短语串项。

角色枚举候选：

| `semantic_role` | 含义 | 常见处置 |
| --- | --- | --- |
| `causal_condition` | 原文明确描述导致/触发故障的原因或成立条件 | `fta_event_candidate` / `unresolved` |
| `diagnostic_mapping` | 参数、故障码/值、消息码与诊断含义之间的映射 | `relation_only` / `exclude_from_tree` / `unresolved` |
| `fault_value_mode` | 故障值/位字段只映射到状态、编号或诊断索引 | `relation_only` / `exclude_from_tree` / `unresolved` |
| `consequence` | 故障导致的后果，不是该顶事件的上游原因 | `relation_only` / `exclude_from_tree` / `unresolved` |
| `state` | 状态/描述性现象；是否为树事件须按原文因果角色判定 | `fta_event_candidate` / `relation_only` / `unresolved` |
| `causal_summary` | 对故障 Cause 段的概括，不能再当独立叶节点重复计数 | `relation_only` / `exclude_from_tree` / `unresolved` |
| `remedy` | 检查、更换、复位、升级等处理动作 | `exclude_from_tree` / `unresolved` |
| `other` | 不属于以上角色 | `exclude_from_tree` / `unresolved` |
| `mixed_unresolved` | 单个抽取项包含无法安全拆分的不同语义角色 | `unresolved` |

处置枚举：`fta_event_candidate`（可作为候选树事件，仍不等于正式因果事实）、`relation_only`（保留作关系/诊断上下文，不作为布尔门 child）、`exclude_from_tree`（有依据地保留在审计输出但不进入树）、`unresolved`（信息不足或角色/证据不确定，阻断该记录的候选树放行）。`relation_only` 不能自动创建因果边；关系层仍须满足原有方向与证据合同。

**2026-09-28 边界修正（Cause disposition prompt v2）。** 分类按语义而不是“是否位于 fault-value 表格”决定。若条目仅解释编号/状态，仍是 `fault_value_mode`/`diagnostic_mapping`；若表格中的具体条目本身明确写出该故障的参数不相容、配置冲突或故障条件，且处于该故障的原因解释范围内，则可标为 `causal_condition` + `fta_event_candidate`。候选树表示手册列出的可能原因，不表示某台现场设备已经出现该模式；缺少实例读数不能单独作为排除理由。完整因果句即使同时含有中间状态与原因子句，也应先作为一个整体因果命题保留，不因复合句式自动判 `mixed_unresolved` 或拆句。该调整不推导 AND/OR：门型仍须独立的原文逻辑证据，缺少门型依据时保持 `unknown`。

**实现中的关键安全规则。**

1. 每批解释必须覆盖 `0..len(causes)-1`，无缺项、重复项、越界项；原始文本必须与对应 `causes[index]` 完全相同。
2. 每项必须将模型提出的连续原文引文唯一绑定到完整原文；未出现或出现多次时不得猜位置，转 `unresolved`。已有 CAUSE EvidenceSpan 会作为分类上下文提供，但不要求抽取阶段必须先有 CAUSE span。模型 rationale 不能替代原文证据。
3. 只有 `fta_event_candidate` 的 index 需要映射到树节点；`relation_only` / `exclude_from_tree` 不触发“断开原因节点”门禁，但仍出现在解释审计结果中；`unresolved` 触发 blocker。
4. 即使全部原因为 `fta_event_candidate`，仍须满足当前拓扑连通、完整原因集合、唯一证据及门型直接证据要求；本合同不会放宽 AND/OR、`fta_ready=false` 或 `production_ready=false`。
5. 所有分类默认为 `ai_proposed`，不写 Gold/数据库；人工/用户授权 AI 复核须作为不同 provenance 明确记录，不能写成真人专家签署。

**回归与验收提案。** 用 F01681、F30027 覆盖 fault-value/诊断映射与摘要不污染树；再加明确原因、后果、remedy、重复短语、缺/歧义 evidence、混合语义和空 causes。验证原始 `causes` 序列化完全不变、逐项覆盖无静默丢弃、非树处置不建节点、unresolved 阻断、已获准原因仍受原拓扑门禁。先以离线 Preview 及合同测试验收，不接生产 API、不持久化。2026-09-28 第一轮原文开发回归显示：F01681 有15条故障值配置模式被统一降成 relation-only；F30027 有4条完整因果句被判 mixed_unresolved。已据此更新 Cause disposition prompt 至 v2，并按同一原文复跑；现保留有直接因果语义的候选，同时门型仍 unknown、ready 标记仍 false。

**用户确认的核心决定。** 单一主角色 + 独立处置；混合语义不自动拆分而标 `mixed_unresolved`；未决项保留且阻断整棵候选树；证据缺失或重复短语不自动选位置，必须待人工补证/定位。明确的 `relation_only` 或 `exclude_from_tree` 留在审计账中、不进入树节点，也不自动创建因果边。

验收：

- 原始 causes、原文证据和索引身份保持不变且可审计。
- 每个 source cause 恰有可验证的处置结果；缺分类、缺证据或 unresolved 不会被静默忽略，并会阻断整棵候选树放行。
- 仅 `fta_event_candidate`（或经合同批准的等价处置）进入树节点覆盖门禁；诊断映射/参数模式留在逐项审计账，不得仅凭映射自动创建到顶事件的候选边。
- 候选原因不得仅复述顶事件/故障现象；需要正例和“语义同义重述”负例回归，且不能通过硬编码某个 fault code/短语实现。
- 覆盖门禁、失败 blocker、序列化和重试均有正反例测试；F01681、F30027 等已知混合语义案例作为回归样本。
- 正式 Gold 不被此分类器自动重写；AI 分类清楚标为 proposal，需按已批准的审核政策决定是否纳入 Gold。

实现：新增 `FtaCauseDispositionBatch` / `CauseDisposition` 不可变合同与 `CauseDispositionService`；每批按原始 cause index 完整覆盖并绑定 extraction、record、源文 SHA-256。模型给出的引文只在原文唯一出现时生成跨度；缺失/重复引文、漏项、重复索引或角色/处置冲突会保留为显式 `unresolved`，不能自动落点。候选树 artifact v4 序列化完整处置账，只有 `fta_event_candidate` 进入结构阶段；不符合分类的节点映射会使整树 blocked。无任何候选事件时提前返回 blocked 审计 Preview。

**2026-09-28 原因证据映射补强。** `TextExtractionAdapter` 的 cause evidence mapper 可忽略空白差异并统一单双/弯引号形式，同时返回所有匹配位置；对模型省略的括号参数注记及末尾句号，只在严格匹配失败后做 source-only 规范化，最终仍保存原文真实 quote 和 offset。重复短语不再只取首次出现；多处匹配仍需人工定位。FTA `CauseDispositionService` 现要求 cause index 在抽取阶段已有且仅有一个有效 CAUSE span，后续处置模型的引文不能替代缺失/歧义的抽取证据。保存响应离线回放确认 F01681 16/16、F30027 23/23 causes 都唯一映射，其中历史 index 1 缺口已在当前 mapper 回放中补齐；旧 Preview 不回写。该实现不证明语义因果，也不改变通用抽取层允许部分缺证据的合同。

后续验收（Cause disposition v2 历史快照）：CauseDisposition、候选树、递归结构及 mapper 定向测试 78/78；后端完整测试 263/263。以上为固定响应/离线 mapper 的合同与证据位置验证，不是在线模型语义准确率或专家 Gold。v2 对 F01681 诊断映射的因果边界已由 v3 收紧；Remedy cause-scope reconciliation、独立 Final、Gold、数据库、生产 API 与 readiness 仍未闭合/改变。

**2026-09-28 Cause disposition v3：自然语言候选边 / 诊断映射不得自动连边。** 用户确认：原文明确列出的自然语言可能原因可形成待审核候选边；fault/value、参数/位/索引到解释文本的诊断映射不能仅凭映射连到顶事件，即使映射解释句是自然语言或描述配置冲突。除非映射之外另有独立、直接的原文因果证据，并且对应 source cause 获准为候选，否则映射项留在审计账 `relation_only`。F01681 v2 的15条 `r0949` 映射候选连接属于历史策略输出，不被回写或视为 v3 通过结果。提示已升至 v3；正反例合同测试证明自然语言 cause 候选可进入结构、F01681 风格 mapping-only 输入不生成树节点/边。未在线重跑模型，因此尚无 v3 模型语义准确率声明。

边界验收：CauseDisposition 与 Candidate FTA 定向测试、完整后端回归、v10 manifest check/validator；Gold/数据库/生产 API/readiness 不变。活动文件与哈希见 manifest v10。

验收结果：原因处置单测 9/9；候选生成合同测试 13/13；递归结构测试 10/10；应用/重试测试 7/7；后端完整测试 247/247；manifest 校验 52/52，manifest 校验器测试 6/6，S120/S150 重叠审计回归 4/4；核心合同、服务和相关测试文件 `py_compile` 通过。F01681、F30027 的历史抽取输出回归分别确认 Cause 摘要/故障值模式不污染树、Possible causes 与 r0949 位模式获得不同处置。以上是离线合同与 stub 行为验证，不是在线模型准确率或专家 Gold；正式 Gold、数据库、生产 API、`fta_ready` 和 `production_ready` 均未改变。

### 3. 规范化门型 `unknown` 的原因

问题：门值 `unknown` 本身是有效业务结论，但“无直接证据、原因集合不完整、语义歧义、置信策略缺失、模型分数不足”等处境不能只靠自由文本区分。

处理：在保持 `gate=unknown` 的基础上，增加稳定、可枚举的 unknown reason 分类；现有 `blockers` 作为次级细节，`decision_reason` 不作为机器真值。仅将当前代码可观测到的门证据缺失、子项不完整、scope 冲突、置信策略状态列入正式枚举；历史映射不解析自由文本，未命中时显式标为 `legacy_unspecified`。

验收：

- 每个 unknown gate 有且只有一个主 reason code，可有独立次级 blockers；`not_applicable`、`blocked`、`unknown` 语义不混淆。
- reason code 能由合同校验并在报告中按原因统计，不依赖解析自然语言 `decision_reason`。
- 旧 blocker 映射有覆盖测试；不存在映射的旧数据以显式 legacy/unspecified 标出，不猜补。

状态：完成（工作项 3 结束时的实现状态）。工作项 2 冻结逐原因输入身份后，新增合同级 `UnknownGateReasonCode`；每个新生成的 `gate=unknown` 必须且只能带一个主原因码，非 `unknown` 门禁止携带该字段。原因优先级由 `fta/unknown_gate_reason_policy.py` 按结构化 flags/blockers/策略返回值决定；`blockers` 是次级细节，`decision_reason` 仅供人读，不解析。历史 blocker 只按已登记的精确代码/代码前缀映射；未匹配时是 `legacy_unspecified`，不猜测、不改写旧 artifact。

当时的正式原因码为：`no_direct_logic_evidence`、`incomplete_child_set`、`semantic_scope_ambiguity`、`evidence_missing_or_ambiguous`、`confidence_policy_unavailable`、`model_confidence_below_policy`、`model_prefers_unknown_gate`、`unresolved_structure`、`legacy_unspecified`。优先级固定为子项完整性、scope 一致性、门证据存在/定位、置信策略结果、未解析结构；没有独立代码路径支持的其它原因不作为正式标签加入。候选树输出合同升为 v5；工作项 3 当时建立 manifest v3。工作项 4 后的活动清单已升为 manifest v4。

工作项 3 验证记录：策略/legacy 映射单测 7/7，候选抽取集成测试 16/16，递归候选服务测试 10/10，后端完整测试 257/257，FTA manifest 校验器测试 6/6，S120/S150 重叠审计回归 4/4；`py_compile` 通过。工作项 3 结束时 manifest v3 构建器 `--check` 为 current，SHA-256 工件校验 56/56。`git diff --check` 退出码为 0，只有既有工作树文件的 LF/CRLF 提示。`CandidateFtaTree` 对每棵树输出由逐门原因码推导的 `unknown_gate_reason_counts`，报告不需解析 `decision_reason`。

实施前审计（历史记录）：`CandidateFtaGateAssessment` 同时暴露 `gate`、自由文本 `decision_reason` 和字符串 `blockers`，此前没有机器可校验的主因字段。`GateConfidencePolicy` 已产生稳定的策略原因；结构层另有子项完整性、scope 一致性和门证据定位 blockers。一个 scope 可同时出现多类原因，因此本工作项增加确定性主因优先级，并保留其它 blocker 作为次级细节。`blocked` 是整树放行状态，`not_applicable` 是单子项完整 scope 的非布尔门结论，二者都不通过 unknown reason 表示。

### 4. 补强真值、来源独立性与 holdout 声明

问题：现有 Gate Gold 类别不平衡，AI 角色审核不能代替独立领域真值；同厂商手册文本/故障码重叠会高估泛化。

处理：按来源簇锁定 split；分别登记真人专家标注、用户授权 AI 角色审核、争议/未决、不可用标签。补充经授权的 AND、OR、unknown 覆盖；数据不足时只报告描述性结果，不拟合或宣称阈值校准。复现 S120/S150 重叠审计，并核实“34/54 scope anchors”说法的来源、定义和分母。规划独立验证优先选择不同厂商/手册体系；在取得独立来源前，S120/S150 只称 cross-manual/near-transfer，不称跨领域泛化。

验收：

- Gold provenance、标签规则和争议处理写入数据 manifest；AI 标注不冒充真人专家签名。
- calibration 与 validation 按来源簇隔离，同原句/同故障码/同文档来源不得跨集合泄漏。
- AND/OR/unknown 有足以支持预定分析的独立样本；若达不到，指标明确为 `insufficient_evidence`，不选阈值。
- S120/S150 的 holdout 名称与报告结论准确；34/54 数字有可复现脚本/产物，或从活动结论中撤下。

状态：完成（2026-09-28，完成的是来源/切分审计与结论收口，不代表独立外部验证已经取得）。当时活动 manifest v4 将 55 个 v6 门节点明确标为用户授权 AI 角色审核、`reviewer_is_human_expert=false`、`formal_gold=false`；逐节点 provenance 计数也写入清单。数据有 48 个 source cluster；按共享 fault code 将相关来源簇合并后，形成 47 个防泄漏分组。校准/验证分别为 43/12 个节点、38/10 个 source cluster、37/10 个故障码；没有 fault code、source cluster 或防泄漏分组跨 split。F01700 关联两个来源簇，但均位于 calibration。验证组门型只有 AND/OR/unknown = 4/3/5；具名人类逻辑 Gold 仍是 6 条且 AND=0。因此只允许描述性检查，校准状态保持 `insufficient_evidence`，不拟合/宣称概率阈值。

S120/S150 重叠审计已针对当前 gate review v6 重跑，活动报告为 [overlap audit v4 JSON](../evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.json) / [Markdown](../evaluation/quality_eval/runs/siemens_s120_s150_s210_overlap_audit_v4_2026-09-28.md)。旧 `34/54` 来自 v5 的 54 节点总体及其中 52 个同码节点；当前 v6 为 55 节点、53 个同码节点，scope 原句重复仍是 34，故当前分母应报告为 `34/55` 总体及 `34/53` 同码条件。S120/S150 分类为同厂商跨手册/版本 near-transfer，不是独立跨领域 holdout；当前没有可用于独立跨厂商验证的 gate Gold，故此项明确留作后续数据获取，不提升为泛化结论。

重叠审计工具现在默认读取 v6，并按输入审核集记录 artifact 名、版本、hash、真人专家标记及逐节点 provenance；原 v3 报告保留为 v5 历史快照。工作项 4 当时将活动基线升级为 manifest v4；随后工作项 5 由 v5 取代，v1–v4 均不覆盖。

### 5. 将已见 smoke probes 固化为合同/边界回归集，另建冻结验证

问题：重复增加成功 smoke probe 的信息增益有限；若同时用于调提示、再报成绩，会产生评测泄漏。

处理：把 FAA/NASA/technical-manual/S120/S150 等已用案例按用途归为 fixture/合同/证据边界回归、解析回归或开发集；冻结输入、来源哈希、期望的不变量和测试命令。必须区分“离线测试验证提示/合同/弃判不变量”与“当前模型实际推理结果”：前者不能作为模型准确率或行为泛化证据。真正的最终验证另建独立来源簇集合，在模型、提示、规则、解析器冻结后单次评测；选择性风险/覆盖、分类型错误和 abstention 一并报告。

验收：

- 每个回归用例有明确测试不变量（证据精确性、未知门弃判、极性、断开节点阻断等），不把 smoke 通过率称为准确率。
- 最终验证集在模型/提示/规则冻结后才解封，不参与调参；任何重用必须明确降级为 dev/regression。
- 报告同时给出 population、来源簇、provenance、样本数、指标定义、风险/覆盖和失败案例。

状态：部分完成（2026-09-28）。现有 36 条已参与探索的门型案例已冻结为 seen-case contract/boundary regression，按 15 个来源簇记账；**不是训练集、正式 Gold、独立 Dev 或 Final Test，也不代表当前模型准确率**。随后新增一套公开图示开发集：11 个节点来自 DOE、FAA SRM、NASA 三份完整文档（3 个来源簇），与 15 个已见回归簇不重叠；标签由公开图示及原文说明转录、AI 视觉复核，不是项目专家 Gold，不用于独立准确率主张。该批文档全部分配给 Dev，**独立 Final Test 仍为 `not_created`**，之后必须另找与回归和 Dev 均不同的整本文档。禁止在已有文档内部随机拆分样本。

冻结回归集：`fta_gate_behavior_regression_v1`，36 个唯一节点、15 个来源簇，标签 AND=9、OR=15、unknown=12。每例固定来源哈希、证据模式、定位引用和行为不变量；FAA 图示样例按图中逻辑门符号核验，文字证据样例按直接引文核验，证据消融对照必须保持 unknown。新开发集：`fta_gate_diagram_development_v1`，11 个唯一节点、3 个完整来源簇，标签 AND=5、OR=6。来源簇切分规则为：整份来源文档作为不可拆分单位；新 Dev 与 Final 来源互斥，且均不得与这 15 个已见来源簇重叠；Final 标签在实现/提示/策略冻结前保持封存。回归只用于防止已知边界行为退化；Dev 可用于开发和错误分析；二者都不用于独立最终成绩主张。

范围勘误（2026-09-28，优先于本节中较早使用的“行为回归”措辞）：本活动集现命名为 `fta_gate_contract_boundary_regression_v1`，含 36 个已见案例、15 个来源簇；旧 suite id 仅在 v14 历史快照中保留。它验证固定 fixture 的来源/证据、提示输入隔离、响应合同和测试替身下的 probe 汇总，不调用当前模型，所以不报告模型准确率/校准/泛化。活动 manifest v15 对应字段为 `seen_case_regression_suite`。独立 Final 仍未创建。

离线验收入口：

```powershell
python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v5 -v
python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v7 -v
python -m unittest evaluation.quality_eval.public_sources.test_fta_gate_diagram_development_v1 -v
python -m unittest evaluation.quality_eval.public_sources.test_probe_faa_ast_fta_gate_external_v1 evaluation.quality_eval.public_sources.test_probe_multisource_fta_gate_external_v1 evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -v
python evaluation/quality_eval/build_fta_baseline_manifest_v7.py --check --captured-at 2026-09-28
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

活动研究清单为 [FTA baseline manifest v15](../evaluation/quality_eval/fta_baseline_manifest_v15.json)；manifest v1–v14 保留为历史快照。独立 Final Test 状态仍为 `not_created`：已纳入的公开来源均分配给回归或开发，Final 必须使用后续新获取的完整来源文档。

**工作项 5 审计更新（2026-09-28）：**离线测试现被明确界定为 fixture/合同/证据边界回归，未调用当前模型；36 条数据不提供当前模型的准确率、校准或泛化成绩。活动 suite/manifest 已升为 `fta_gate_contract_boundary_regression_v1` / v15。开发集仍为 11 条、3 个整本文档来源簇；独立 Final 仍 `not_created`，需取得与全部回归和开发来源不同的新完整文档。

### 6. 拆分定性结构与定量概率 readiness

问题：候选树的结构、证据与门型审核，和真实故障概率/失效率数据校验属于不同成熟度；共用一个最终门禁会让缺失现场概率数据长期遮蔽已验证的定性结构能力，或反向造成结构能力被误报为定量 ready。

处理：定义两个有范围的里程碑：

- `FTA-Structure Ready`：仅对明示的数据集/来源范围评估事件身份、原因解释处置、关系连通、逻辑门直接证据、人工审核状态、来源切分和结构合同；不能外推到全量/生产。
- `FTA-Quantitative Ready`：在结构就绪基础上，要求同来源、同观测窗口/样本分母的真实事件概率/失效率、依赖性假设与数据质量审计，并单独验证计算与不确定性传播。

现有 `fta_ready=false` 与 `production_ready=false` 保持不变。用户确认 readiness 由独立的范围评估报告/manifest 表达，不加到单棵 Candidate Preview；本工作项只实现评估层合同，不改核心树合同、Gold、数据库、API 或生产 flag。

验收：

- 两个 readiness 有独立范围、输入证据、报告和反例测试；报告必须钉定 manifest、数据文件与来源簇，列出纳入/排除分母、评估 provenance、criteria、evidence refs 与 blockers。
- Structure Ready 不需要真实故障概率，但必须满足结构/证据/审核门槛；Quantitative Ready 不可由模型门型分数代替。
- 全量与生产标志不会因试点范围达标自动变真。

**外部整本文档筛选更新（2026-09-28，manifest v17）：**对 4 份官方 FAA/NASA 文档进行了来源筛选。NASA/CR-2019-220217（200 页）和 DOT/FAA/TC-15/62（296 页）适合后续评测适配开发，但代表性树图页已经被检查，故它们属于已见来源簇，不能作为盲测 Final；NASA CR-108289 仅作为图/图结构补充；NASA-TM-105505 的实际下载 PDF 只有 27 页且没有所述附录树图，因此排除。具体官方链接、下载 PDF SHA-256、筛选理由和限制见[结构化来源筛选记录](../evaluation/quality_eval/runs/fta_independent_final_source_screen_v1_2026-09-28.json)。来源 ID 精确扫描没有发现与仓库现有清单重名，但这不构成语义去重或模型预训练隔离证明。

**合同适配阻塞（合同部分已由 v18 关闭，来源适配仍未完成）：**当前 Candidate FTA 应用服务对每个 `FaultRecord` 单独生成树，外部来源则是含多个顶事件的系统级报告；不能把整本 PDF 直接输入并声称验证了完整系统级建树。v18 已建立评测专用输入/Gold Schema 与合同校验器：单一顶事件、按页/章节定位的原文、模型输入与参考标签分离，并区分 `diagram_reference_gate` 和 `text_authorized_gate`。但尚未对新的完整文档实际组装 packet，也未验证 PDF 到 packet 的来源适配器；整本 PDF 仍不能直接送入当前生产服务。

**当前状态（manifest v19，2026-09-29）：**v17 筛选的4份来源中，2份仅可作为已见开发候选，0份盲测 Final 合格。NASA XVS 已完成整篇40页文本筛查并查看 Appendix D 的8张树图，来源族标记为 `seen_development_only_not_final`；正文只给高层 failure conditions，不能支持完整图示因果分解。1998 前身与相关 CR #29-C19 尚未内容比对，语义重叠审计未完成；权利结论仅暂定用于内部评估、保留限制声明，不是法律/人工审查。输入 packet=0、reference Gold=0、模型调用=0、Final `not_created`；Structure/Quantitative readiness 仍 `blocked`，`fta_ready=false`、`production_ready=false`。下一步只筛选另一完整来源族的元数据，并在来源簇/配置冻结前不打开其树图。
- `ready_within_scope` 仅描述报告声明范围；AI 角色审核不得声明为真人专家审核；Quantitative Ready 必须以前置同范围 Structure Ready 和真实事件率/失效率及观测窗口、分母、依赖/不确定性验证为条件。

状态：评估层合同与 v1 范围报告已实现；当前范围结论为 Structure `blocked`、Quantitative `blocked`。该工作项的“报告/合同交付”已完成，但任何 readiness 状态均未达成；全局与生产标志继续为 false。当前报告仅覆盖 v15 的 36 条合同/边界回归和 11 条公开图示开发案例（47 条、18 来源簇），不代表完整因果结构、模型准确率或独立泛化。

## 执行顺序与依赖

```text
1. 基线/来源清单审计与冻结（工作项1）
   ↓
2. Cause role + disposition 合同设计和逐项原因解释层（工作项2）
   ↓
3. Unknown reason code 规范化（工作项3，可依赖工作项2的统一身份）
   ↓
4. Gold provenance、来源簇隔离与独立验证集（工作项4）
   ↓
5. 回归集冻结 + 独立验证（工作项5）
   ↓
6. Structure / Quantitative readiness 分离并逐范围验收（工作项6）
```

每个工作项必须有单独的变更边界、测试/报告和完成记录。工作项 2 的原因边界已获用户确认；工作项 6 已获用户确认由评估报告承载，并按该边界完成评估层实现；本计划不是对任意 API 或生产迁移的预先授权。

## 全局停止条件与安全边界

- 不覆盖、不重写现有用户改动；当前工作树存在大量未提交及未跟踪文件，本计划仅拥有明确列出的计划/index 改动及后续逐项授权改动。
- 不以 AI 角色复核宣称真人领域专家签署；样本不足时如实报告 `insufficient_evidence`。
- 不从列举项、故障码数值或模型概率自动推断 AND/OR；门型直接证据缺失仍为 unknown。
- 不将候选 Preview 升级成正式 Gold/数据库/生产树；任何生产开关单独审核。
- 不在同一轮同时调 prompt、规则、阈值和测试集；每项变化可追溯、可复现。

## 本计划完成标准

六个工作项均已按各自标准完成，活动基线清单可复现，回归与独立验证的用途和 provenance 分明，结构/定量 readiness 独立报告；未满足的项必须保留明确 blocker。即使本计划完成，也不自动表示 S210 全量 FTA 或生产部署 ready。

## 变更记录

- 2026-09-28：建立计划。当前为基线审计后、实现前状态；只核对仓库与现有文档，没有修改抽取/FTA 合同、Gold 或数据库。
- 2026-09-28：工作项 1 完成 owner 审计：现有 Dataset Registry 只负责数据集生命周期事实；未发现负责 FTA 合同、审核集、来源切分、probe 和 Preview schema 的 FTA 基线清单。下一步按计划建立独立 FTA baseline manifest，并对其活动条目计算/核对文件哈希。找到 S120/S150 重叠审计 v3，核实“34个 scope 引文重现”成立，但应报告 34/54 总体及 34/52 同码条件分母。
- 2026-09-28：工作项 1 完成：新增 baseline manifest、SHA-256 校验器及测试；manifest 校验 44/44，校验器单测 6/6，S120/S150 重叠审计测试 4/4。其余五项未因本次完成而自动改变状态。
- 2026-09-28：工作项 2 完成现状审计并形成合同提案；确认保持 `FaultRecord.causes` 原样，以逐 source index 的单角色/独立处置解释合同隔离诊断映射与树事件。因涉及核心合同语义，待用户审核后方可编码。
- 2026-09-28：工作项 3 完成只读 blocker/reason 盘点：发现策略原因码已稳定存在，但它与结构/证据 blockers 并列且可同时发生；reason 合同须在工作项 2 的原因输入身份冻结后再实现，避免重复表达或错误合并。
- 2026-09-28：用户确认工作项 2 的安全边界：证据无法唯一定位时待人工补证，不自动绑定；重复短语不自动选择位置。随后完成离线原因角色/处置合同、候选 FTA v4 审计账、fail-closed 接线及回归；正式 Gold、数据库、生产 API 和 readiness 标志未改。工作项 3 现可按依赖顺序进入实施。
- 2026-09-28：工作项 3 完成实现与离线回归：候选树合同升为 v5，每个 `unknown` 门强制且仅强制一个主 reason code；旧 blocker 按结构化代码映射，未识别旧值为 `legacy_unspecified`；正式 Gold、数据库、生产 API 与 readiness 标志未改。
- 2026-09-28：工作项 4 完成来源与 split 审计：当前 v6 的 55 个节点 provenance、48 个 source cluster 及合并共享 fault code 后的 47 个防泄漏分组均已重算并登记；calibration/validation 无故障码、来源簇或分组跨集合。重叠报告更新到 v6 分母 `34/55` 与 `34/53`。S120/S150 仅作同厂商近迁移；独立跨厂商 Gate Gold 尚无，校准结论保持 `insufficient_evidence`。新增活动 manifest v4，保留 v1–v3 历史快照；不改 Gold 标签、数据库、生产 API 或 readiness。
- 2026-09-28：工作项 5 部分完成：盘点此前已参与探索的 36 条门型案例，按 15 个来源簇冻结为 source-pinned 行为回归（AND=9、OR=15、unknown=12），并明确非训练集、非正式 Gold、非独立验证集；独立 Final Test 保持 `not_created`。核对发现来源数为 15（FAA reusable-launch/reentry guide 与 FAA AC 65-15A 是不同文件），不沿用早先误报的 14。新增活动 manifest v5 和离线回归校验；不做随机拆分、不改 Gold 标签、数据库、生产 API 或 readiness。
- 2026-09-28：工作项 6 报告/合同交付完成（不代表 Ready）：用户确认 readiness 使用独立范围报告/manifest，不挂到单棵 Preview。新增 scoped readiness report v1、可复现 builder 与 validator，并基于不可变 v15 manifest 对 36 条合同/边界回归 + 11 条公开图示开发样本（47 条、18 来源簇）作证据审计。结果 Structure 与 Quantitative 均 `blocked`；Final 未创建、当前模型行为未运行、AI 审核非真人 Gold、真实设备概率/分母/观测窗缺失均显式记录。全局 `fta_ready=false`、`production_ready=false`，Candidate Preview、Gold、数据库及 API 合同未改；活动基线升为 v16。
- 2026-09-28：工作项 5 再推进一阶段：新增 DOE、FAA SRM、NASA 三份完整公开来源，共 11 个图示门型开发样本（AND=5、OR=6，3 个来源簇），全部分配到 Dev，且与 15 个已见回归来源簇隔离；来源 PDF 哈希、页码、证据引文和提示输入隔离均有离线测试。由于新来源已参与开发，独立 Final 仍 `not_created`，须另找全新文档；没有调用生成模型、修改正式 Gold/数据库/生产 API 或 readiness。活动清单升为 manifest v6。
- 2026-09-28：原文 Preview 回归发现并修正两个结构提示边界：定性触发条件的建树连接不应错误要求现场读数；`cause_set_complete` 应表示限定原文 scope 内的闭合枚举是否完整，而非设备实例是否观测到。结构未决索引也不得重复记录处置账中已排除/待定的非建树项。F35400、F06000 当前应用服务四阶段原文重跑均成功，结构与引文进入可审核 Preview；门仍 fail-closed 为 `unknown`（置信策略不可用）。相应本地回归 33+9+8 通过。创建活动 manifest v7；没有改 Gold、数据库、生产 API、门策略或 readiness。该两例是开发回归，不是独立准确率验证。
- 2026-09-28：F01681/F30027 原文回归发现 Cause disposition v1 将明确故障值配置原因过度降级，并把包含状态+明确成因的完整句误判为 mixed unresolved。更新为 prompt v2：按命题语义区分通用可能原因与现场实例状态，完整因果句保留为一个候选，不因此推导 AND/OR。相同 S210 原文四阶段复跑后，F01681 有15条原因候选（故障值替代 scope 仍不完整）、F30027 有9条原因候选；共75条树证据精确且唯一，14个门 scope 均 unknown。原始 v1 失败 artifact 保留为诊断。补充探针语料标识、prompt 版本及 PDF/章节/页码/source offset 元数据；对两份 v2 输出只做离线来源元数据重核、不调用模型，创建活动 manifest v8；未改 Gold、数据库、生产 API、门策略或 readiness。
- 2026-09-28：Cause disposition v2 扩展回归完成（历史）：S210 F30021 与同厂商 S120/S150 F35400、F06000 各完成一次四阶段原文开发运行；F30021 因重复 cause 引文 blocked，另外两条进入只读 review Preview、所有布尔门仍 unknown。F06000 的顶事件/首个原因语义重叠与嵌套层级留作人工语义检查，不宣称树正确。修复候选服务：顶事件精确引文在源文本中重复时新增 `top_event_evidence_ambiguous` blocker，禁止自动择位；旧 F30021 artifact 早于该守卫且保留原样。F01681 独立 AI 复核进一步指出故障值映射不等于到顶事件的因果证据、cause index 1 缺少抽取层 evidence span、Remedy 中 `xxxx=9507` 导致原因集完整性未闭合。上述内容作为审计记录加入 v9；没有改 Gold、数据库、生产 API、门置信策略或 readiness，独立 Final 仍 `not_created`。
- 2026-09-28：用户确认 Cause disposition 边界：自然语言原因可以成为待审核候选边，诊断映射不自动连接顶事件。Cause disposition / 结构 / 门评估提示升至 v3 并补正反例测试；F01681 v2 的15条故障值解释不再作为当前因果边通过证据，历史产物不回写。随后在 F01681 单样本上完成 v3 在线开发复演：15 条映射均为 `relation_only`，Cause index 0 成为唯一候选；独立 AI 子智能体指出该候选可能重述顶事件，结论 `needs_revision`。此结果不是专家 Gold/准确率；Gold、数据库、生产 API 与 readiness 不变，活动基线升为 manifest v11。
- 2026-09-28：Cause disposition v4 离线修正：因 F01681 v3 的唯一 Cause 候选可能只是顶事件释义，提示词现在要求逐项对照 `top_event`；纯重述且无新增上游信息时用 `causal_summary + relation_only`，语义不明时 fail-closed 为 `unresolved`。新增提示词回归、重述处置回归、宿主误标降级回归；保留独立自然语言原因候选正例及既有诊断映射保护。未在线重跑模型，v3 运行与复核原样保留；Gold、数据库、生产 API、门策略与 readiness 均未改变。活动清单升为 manifest v12；v12 manifest/validator/定向测试结果见验收清单。
- 2026-09-28：Cause disposition v4 单样本在线开发复演完成：在 `OPENAI_MAX_RETRIES=0` 下对固定 F01681 来源运行两阶段、2/2 请求成功；16/16 原因均为 `relation_only`（1 条顶事件摘要、15 条诊断映射），因此候选树按 `no_fta_event_candidates` 阻断，未调用结构/门型阶段。源文本 SHA 匹配，71 个复核引用位置精确。独立 AI 子智能体只读复核 PASS，但不是真人专家签署、Gold 或准确率证据。Gold、数据库、生产 API 和 readiness 未变；新增 v13 manifest，v12 保留为不可变历史快照。具体验收命令和本轮执行结果见 [验收清单](acceptance.md)。
- 2026-09-28：完成 F01681 Remedy `xxxx=9507` 来源范围复核：固定文本唯一命中在 Remedy，精确偏移 `[2526,2564)`；条件式“Set synchronous motor”不直接证明现场状态或到顶事件的因果边，因此不补 Cause/树节点，cause-set completeness 保持 `unresolved`。只读 AI 子智能体意见与来源边界一致但非真人专家签署。新建复核 artifact 与 v14 manifest；Gold、数据库、生产 API/readiness 不变，v13 历史 snapshot 不覆盖。
- 2026-09-28：补齐 Preview 合同的 `fta_ready=true` 直接拒绝回归测试；运行逻辑未变。测试只验证合同拒绝，不代表 FTA 建树语义评估已完成；独立 Final、当前模型生成效果评测及真人专家 Gold 仍未具备，Structure/Quantitative readiness 与全局生产标志保持 blocked/false。
- 2026-09-28：建树评测可行性复核：现有 47 案例不足以计算端到端树生成质量（36 条不调用当前模型的合同/边界回归，11 条为公开图示开发样本）；独立 Final 为 0。Cause disposition 有 v4 标记，但未联合封存 provider/model、提示策略和解析器版本的模型评测配置；因此本轮不运行模型、不伪报准确率。下一步进入效果评测前，先形成可复现冻结清单，再准备来源簇隔离的完整原文—完整结构 Gold Final。
- 2026-09-28：建立建树评测配置锁 v1，快照当前本机解析到的 `deepseek-flash`/`api.deepseek.com`、temperature=0、timeout=120 秒、max retries=2、运行时版本及 14 个提示/解析/合同源码哈希；无密钥落盘、无模型请求。供应商模型别名仍可能映射到变化的权重，因此记录此限制。该动作只完成配置快照；独立完整树 Final 仍为 0，模型生成准确率仍未评估。
- 2026-09-29：评测专用单事件包合同阶段完成（manifest v18）：新增严格模型输入 Schema、独立图示/文本授权参考 Gold Schema、证据/来源簇/图连通性校验器与 12 项合成测试；模型输入投影不暴露来源溯源包络或门型 Gold。实际评测包与 Gold 均为 0，未调用模型，未改变生产服务、数据库、正式 Gold 或 readiness。NASA XVS 仅登记为官方元数据线索，未下载或查看 PDF/树图，未通过权利与来源重叠审计，不计盲测 Final。该子目标停止条件为：输入/Gold 分离、跨 artifact 核验、未知门型/直接证据 fail-closed、无生产接线，并经合同测试通过；后续应先完成全新来源整本筛查，再考虑生成任何 Final 标签。
- 2026-09-29：完成 NASA XVS 整篇来源筛查并建立活动 manifest v19：扫描40页文本、查看8张 Appendix D 树图；该来源族限定为已见 Dev/弃判边界候选，不进入独立 Final。权利暂定内部评估、保留限制声明，非法律/人工审查；1998 前身与关联 CR #29-C19 的语义重叠未闭合。输入/GOLD 分离合同保持有效；packet=0、Gold=0、未调用模型，Structure/Quantitative 仍 blocked，全局 readiness false。验收测试与哈希验证记录见 `docs/acceptance.md`。
- 2026-09-29：完成一个有界单事件 Dev 样例：NASA NTRS 19880001643 Figure 7。模型输入只含顶事件与 Section 5.0 原文，参考图节点/图示门型独立存放。独立 AI 角色审核观察到图中三门对应的原文均出现 AND/OR 运算符，但精确文本授权标签为 OR/AND/unknown：第三门的图示叶项“Two module vents clog”比原文“failure of module vents”更具体，故按 `scope_ambiguity` 保守弃判；同时修正重复事件出现被合并的问题。图示根标签与文本顶事件用语不同。该审核不是真人专家签署；样例已标记 seen-development-only，模型未运行、独立 Final=0。v20 只更新评测资产与研究基线，不修改生产合同、正式 Gold、数据库或 readiness。
- 2026-09-29（v21）：在隔离的 `model_input` 投影上执行一次专用 event-scope DeepSeek 请求，重试为0。provider 返回 `finish_reason=length`，completion tokens 达3000上限，message content 为空，故无 JSON、无结构预测、未与 Gold 比较；没有准确率/校准指标，也没有追加调用。完整 raw-response 元数据及评估见 manifest v21 登记的运行文件。没有改正式 Gold、数据库、生产 API 或 readiness。完整 raw-FaultRecord Candidate FTA 流程的 eval lock v1 仍是独立未运行配置。
- 2026-09-29（v22）：用户另行授权一次重跑；使用压缩 JSON 输出格式、`response_format=json_object` 和 8192 `max_tokens`，SDK 重试仍为0。completion tokens 达8192、`finish_reason=length`、最终 content 为空，未解析出模型输出；未进行 Gold 比较或准确率评估。v1/v2 两次尝试分别记录，不作第三次调用。DeepSeek 官方文档提示 JSON mode 仍可能返回空 content，故不能把某一原因断言为根因。Gold、数据库、生产 API、Final 和 readiness 未改变。
- 2026-09-29：经用户确认优先补响应元数据，再做仅改变 thinking mode 的单次对照。v3 保持 v2 模型、输入、prompt、8192 token、JSON mode 不变，显式 `thinking=disabled`；记录 reasoning 元数据但不保存推理文本。用户报告本地凭证已更新后，执行且仅执行 1 次请求、0 重试；响应 `finish_reason=stop`，strict JSON 可解析，5 个节点、3 个门范围、8/8 引文校验通过、无结构错误。此结果仅证明本次输出可解析且证据可回指输入；未与参考 Gold 比较，不是语义准确率/逻辑门正确性结论。v3/v2/Figure 7 回归共 16 项通过，preflight 通过。已建立活动 manifest v24；Gold、数据库、生产 API、独立 Final 与 readiness 未改变，`fta_ready=false`、`production_ready=false`。
- 2026-09-29：对保存的 v3 输出做离线、非计分定性比较并建立活动 manifest v25。根顶事件文本及根 OR 标签对齐，但直接子项未表示两个复合分支，且 E3 同时属于 E2 的 `parent_id` 子节点和根 OR 直接 child；文本授权为 AND 的次生爆炸范围被模型标成 unknown，独立“模块正常运行”节点缺失；结构分支 Gold 为 `unknown/scope_ambiguity`，模型虽也给 unknown，却绑定到“单体爆炸”而非相同作用域。8 条引文仍逐字匹配输入，但这不是语义蕴含。报告只作为一个已见 Dev 样例的定性错误分析：不计算准确率、不改 AI 角色审核 Gold、不声称真人专家/泛化结论，不改数据库、生产 API 或 readiness；候选树不接受为有效 Preview 树，`fta_ready=false`、`production_ready=false`。
