# FTA System 交接文档：结构化抽取与审核放行

更新时间：2026-09-18
项目路径：`C:\Users\爹\Documents\Codex\2026-09-11\ni\work\Fta_system`
当前分支：`refactor/v2-monorepo`

## 1. 当前目标与边界

本项目是以 FTA 为练习场的学习型工程，重点是工程化代码设计、智能体工作流编排、自然语言抽取和后续深度学习评测。FTA 业务只学习完成抽取和建树所需的最小语义。

当前主线是自然语言故障抽取的审核优先流程：

```text
原始文本
  -> FaultExtractor / TextExtractionAdapter
  -> ExtractionResult
  -> 审核准备与持久化
  -> 人工审核决定
  -> FaultRecordReleaseService
  -> ReleasedExtractionResult（放行快照）
  -> FaultTreeBuildAttempt（每次建树尝试追加一条）
```

已经确认的边界：

- 模型调用只能位于适配器和模型客户端层，核心合同不能依赖具体模型厂商。
- `FaultRecord` 是一条抽取事实；`ExtractionResult` 是一次完整抽取任务的结果档案。
- `ExtractionResult` 要保留记录、证据、状态、诊断和结果 ID；失败结果可以为了审计和重试而保存。
- `FAILED`、`EMPTY`、`PARTIAL` 和 `SUCCESS` 不能混为一谈。
- 抽取失败或待审核数据不能进入 FTA 建树。
- 审核决定是新的不可变实体，不修改原始 `FaultRecord`。
- 当前放行策略只有 `APPROVED` 默认可用；`NOT_REQUIRED` 只有显式配置后才可自动放行。
- 旧的 `full_generate` 仍是多职责旧流程，暂时不能直接改造成审核式抽取流程。

## 1.1 已确认的总体目标与阶段门禁

目标是先把 Siemens S210 做成可验证、可演示的故障 RAG/FTA 样板，再从真实验证结果中抽象多领域平台能力。阶段不得跨越未满足的验收门禁：

1. **阶段 A：S210 Retrieval Pipeline v1**
   - 冻结 281 条 Gold 与 42 条开发检索评测集；
   - 固定 D2（description/cause dense + RRF + fault code/parameter exact）和 Alarm 辅助召回；
   - 候选池为 D2 Top20 与 Alarm Top10 的 fault entity 并集，接入 `bge-reranker-v2-m3`；
   - 另有独立 Final Test Query，禁止用 Final Test 反向调参；
   - 门禁：候选召回稳定、Final Test 有独立成绩。
2. **阶段 B：证据约束的 RAG 回答**
   - Retriever、Reranker、完整故障上下文和回答生成解耦；
   - 上下文必须包含故障字段、alarm/remedy 与原始 evidence/source；
   - 检索指标与回答指标分开评估；
   - 门禁：完成回答评测及人工语义复核后，才能宣称回答链路通过。
3. **阶段 C：API 与现有前端接入**
   - 后端保持 query parsing、retrieval、reranking、context loading、answer generation 的边界；
   - 不改变现有前端布局，AI 对话入口通过 `/api/rag/query` 接入；
   - 门禁：API 合同、前端真实路径、错误态和构建测试均通过。
4. **阶段 D-F：Common Fault Schema、Domain Adapter、通用 Retrieval Pipeline**
   - 仅在 A-C 通过后抽象 `entity_id/domain/manufacturer/system/fault_code/.../evidence/raw_text`；
   - Siemens 作为 `SiemensS210Adapter`，通用检索层不写 Siemens 专用判断；
   - 门禁：281 条数据无损映射，检索角色和 entity 聚合合同有测试。
5. **阶段 G-H：第二领域与领域路由**
   - 优先接入航空航天公开故障数据，建立独立查询评测集；
   - 验证公共 Retriever 与领域专用字段/通道的边界，再增加 Domain/System Router；
   - 门禁：S210 与第二领域可在同一后端运行且结果不互相污染。
6. **阶段 I-J：关系、FTA 与平台化**
   - Fault Entity 与 Fault Tree 分离建模，关系保留 source/evidence/review_status；
   - 支持 AND、OR、Voting Gate 等 FTA 结构，不把尚未标注的逻辑门伪装成已知事实；
   - 门禁：不同领域实体可进入统一关系/FTA 引擎，且 API/前端展示仍有真实数据来源。

当前状态以本节和 7.25 之后的记录为准。历史段落中的“阶段 B 未完成、禁止开始 D-J”已失效，不再作为当前门禁。

| 阶段 | 当前状态 | 证据/边界 |
|---|---|---|
| A. S210 Retrieval v1 | ✅ 完成 | 281 Gold、42 条开发集、39 条封存 Final Test；Generic parity gate PASS |
| B. Grounded RAG | ✅ 工程验收完成 | 12 条回答开发/验证集 12/12；不得作为未见生产泛化成绩 |
| C. API / Frontend | ✅ 核心接入完成 | `/api/rag/query` 与现有前端入口已真实 smoke；未改布局 |
| D. Common Fault Schema v1 | ✅ 完成并冻结 | 281/281 无损映射；版本冻结见 `docs/retrieval-platform-v1-freeze.md` |
| E. Domain Adapter v1 | ✅ 完成并冻结 | `DomainAdapter` 与 `SiemensS210Adapter` 契约测试通过 |
| F. Generic Retrieval v1 | ✅ parity gate PASS | 候选召回 39/39；核心指标无回归；生产尚未切换 |
| G. 第二领域 | ← 下一阶段 | 先实现 `AerospaceAdapter`，不改通用核心 |
| H. Domain/System Routing | 未开始 | 等第二领域单域验证完成后再做 |
| I-J. Relations / FTA Platform | 未开始 | 保持 AND/OR 未标注即 unknown 的边界 |

## 2. 已完成的代码

### 抽取合同与适配器

- `backend-python/extraction_contract.py`
  - `FaultRecord`
  - `EvidenceSpan`
  - `ExtractionDiagnostic`
  - `ExtractionResult`
  - `ExtractionStatus`
- `backend-python/model_client.py`
  - `ModelClient` Protocol
  - provider-neutral `ModelClientError`
  - 测试用 `CallableModelClient`
  - 有界重试包装器
- `backend-python/openai_model_client.py`
  - OpenAI-compatible 模型客户端
  - 将认证、超时、限流、网络错误转换为统一模型错误
- `backend-python/fault_extractor.py`
  - JSON 解析、字段校验和 `FaultRecord` 生成
- `backend-python/text_extraction_adapter.py`
  - 文本分块、模型调用、结果聚合、精确去重、诊断归类
- `backend-python/ai_module.py`
  - 提供文本抽取适配器构造入口
  - 保留旧兼容投影，新的结构化链路优先使用新合同

### 应用编排与持久化边界

- `backend-python/extraction_repository.py`
  - `ExtractionRepository`：保存和查询完整 `ExtractionResult`
  - `ExtractionWorkflowRepository`：抽取结果和初始审核记录的整体保存边界
  - 默认应用实现是 SQLite 仓储，内存仓储只用于隔离测试
- `backend-python/extraction_application_service.py`
  - 编排文本抽取、审核准备和整体保存
  - 不负责模型调用、JSON 解析或建树

### 审核与放行

- `backend-python/review_contract.py`
  - `FaultRecordReview`
  - `ReviewableExtractionResult`
  - 审核状态：`PENDING`、`NOT_REQUIRED`、`APPROVED`、`REJECTED`、`REVISION`
- `backend-python/review_preparation_service.py`
  - 根据置信度、证据和抽取状态生成初始审核状态
- `backend-python/review_decision_service.py`
  - 创建批准、拒绝和要求修改的不可变审核记录
- `backend-python/review_repository.py`
  - 保存审核历史并查询当前状态
- `backend-python/release_contract.py`
  - `ReleaseBlock`
  - `ReleasedExtractionResult`
- `backend-python/release_service.py`
  - 只按当前审核状态生成下游安全投影
- `backend-python/build_contract.py`
  - `FaultTreeBuildAttempt`
  - 建树尝试状态：`SUCCEEDED`、`REJECTED`
- `backend-python/fault_tree_build_service.py`
  - 只消费已保存的放行快照
  - 生成节点时保留 `source_record_ids`，重复故障描述合并来源 ID
  - 在保存成功尝试前校验树结构合同
  - 每次调用都追加建树记录
  - 建树失败不修改审核历史或放行快照
- `backend-python/fault_record_tree_mapper.py`
  - 独立负责 `FaultRecord -> tree input` 映射
- `backend-python/fta_tree_contract.py`
  - 独立负责树结构校验和来源 ID 合并
- `backend-python/fault_tree_build_application_service.py`
  - 独立负责按 `release_id` 读取放行快照和查询建树历史
- `backend-python/build_attempt_repository.py`、`backend-python/release_repository.py`
  - 分别定义建树尝试和放行快照的持久化边界
- `backend-python/sqlite_extraction_repository.py`
  - SQLite schema v3，故障记录支持后台 `related_components`
  - 保存放行快照、blocked 原因和建树尝试历史

### API

- `POST /api/fta/extract`
  - 抽取文本并保存待审核结果
  - 返回 `result_id`、记录、证据、诊断和审核状态
  - 不生成 DOT，不建树
- `GET /api/fta/reviews/pending`
  - 按单条 `FaultRecord` 查询当前处于 `PENDING` 的审核项
  - 返回所属结果 ID、抽取状态、故障记录、证据和当前审核信息
  - `REVISION` 保留为后台审核状态，但暂不进入普通待审核列表
  - `APPROVED`、`REJECTED`、`NOT_REQUIRED` 和 `FAILED` 记录不会进入列表
  - 当前实现查询 SQLite 仓储；默认文件位于 `backend-python/outputs/extraction_workflow.sqlite3`
- `POST /api/fta/reviews/approve`
  - 记录人工批准
- `POST /api/fta/reviews/reject`
  - 记录人工拒绝，必须有原因
- `POST /api/fta/reviews/revision`
  - 记录要求修改，必须有原因
- `POST /api/fta/release`
  - 根据 `result_id` 查询最新审核状态
  - 保存并返回本次不可变放行快照
- `POST /api/fta/build_released`
  - 根据 `release_id` 对放行快照尝试建树
  - 返回 `succeeded` 或 `rejected` 业务结果
  - 无论成功或失败都追加一条建树尝试记录
- `GET /api/fta/build_attempts/{release_id}`
  - 查询指定放行快照的全部建树尝试，按发生顺序返回
  - 成功树节点包含来源故障记录 ID，便于回查抽取证据

相关 API 代码在 `backend-python/api_server.py`，使用说明在 `docs/api-usage.md`。

## 3. 当前真实行为

正常链路：

```text
POST /api/fta/extract
  -> ExtractionResult.success
  -> ReviewableExtractionResult.pending

POST /api/fta/release
  -> pending 被拦截

POST /api/fta/reviews/approve
  -> 新增 approved 审核历史

POST /api/fta/release
  -> 返回该 FaultRecord

POST /api/fta/build_released
  -> 只消费 release.records
  -> 成功：追加 succeeded 建树记录
  -> 失败：追加 rejected 建树记录，保留审核和放行结果
  -> 再次重试：追加新的 attempt_id，不覆盖旧记录
```

`FAILED` 结果会保存诊断信息，但不创建审核任务，也不生成可放行记录。`PARTIAL` 结果可以包含故障记录，但会进入人工审核。`ExtractionResult` 中的审核快照不能覆盖仓储中的最新审核决定。

### 3.1 专家审核报告后的抽取与证据修复

针对专家提交的 v3_2 审核报告，当前后端已完成以下修复，并使用重新启动的 API 进程对项目手册 27 条样本重新运行：

- `PH-A01006` 将“驱动对象为无”与组件字段分离，主组件为空，关联组件为 `DRIVE-CLiQ组件、编码器模块`；
- `PH-A01016` 支持跨换行的“关联控制单元存储器”；
- `PH-F01611` 补回“STO状态不一致”的故障处理证据；
- `PH-A01631` 对被参数赋值打断的条件原因绑定多个原文片段；
- `PH-F01641` 补回故障处理段参数 `r9776` 的证据。

最终在线报告为 `evaluation/quality_eval/runs/fta_project_handbook_online_baseline_evidence_binding_v8.json`，
对应专家审核包为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v5.json`，
文本清单为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v6.md`，
HTML 清单为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v5.html`。
最终包 27/27 条证据偏移有效、0 条证据审计警告、主组件与关联组件重复数为 0。在线合法性和
FTA 产出率均为 100%，启发式疑似幻觉率为 1.06%；这些是结构/接口指标，不是专家语义金标。

历史上仍需专家确认的范围包括：候选原因是否是工程原因而非参数值解释、处理段条件是否应作为候选原因、
以及故障树 AND/OR 逻辑。2026-09-20 用户已确认采用统一 57 条审核文件作为本项目的专家审核来源；
AND/OR 逻辑仍保持 `unknown`。未改变前端布局样式，也未把审核数据写入生产数据库的最终 `APPROVED` 状态。

后续专家报告提出三处收口问题。当前已将 `PH-F01600` 的“交叉比较数据编号异常”恢复为原文一致的
“交叉比较数据编号”；将 `PH-A01631` 两条条件原因规范为“不存在电机抱闸且SBC使能”和
“电机抱闸控制，B且SBC使能”，并合并
重复的 `SBC使能` 证据；同时修正 `PH-A01006` 编码器组件证据的优先匹配，使其指向组件声明中的跨换行
文本。三条记录均已通过真实 API 复测。最终审核包为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v8.json`，文本清单为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v9.md`，HTML 清单为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v8.html`。最终包仍为 27/27 条
证据有效、0 条警告。

## 4. Git 状态与提交

本阶段相关提交：

```text
4b438b1  feat: add structured extraction and review workflow
78fad65  feat: add review-first extraction api
48402b0  feat: add review decision and release api
```

交接文档本身将在本次交接中单独提交。未经用户明确要求，不推送远程、不改写历史、不删除旧 API。

## 5. 已执行验证

使用项目虚拟环境执行：

```powershell
.venv\Scripts\python.exe -m unittest discover -s backend-python\tests -v
.venv\Scripts\python.exe -m compileall -q backend-python
python scripts\verify_repo_layout.py
git diff --check
```

当前结果：

- 80 个后端测试全部通过；
- 建树合同测试覆盖来源 ID、重复描述合并、非法树拒绝和运行时失败重试标记；
- Python 编译通过；
- 仓库布局检查通过；
- HTTP 路由实际验证通过：抽取返回 `pending`，未审核时放行记录数为 0，批准后放行记录数为 1；
- 故意传入不匹配的审核记录时，抽取结果和审核记录都没有写入。
- SQLite 仓储重启后能读回抽取结果、证据和审核历史；不匹配的初始审核记录不会留下半成品。
- SQLite schema 版本为 3，仓储支持生成不覆盖已有目标文件的数据库备份；关联组件、放行快照和建树尝试可在仓储重启后读回。

HTTP 测试环境有一个来自 Starlette/httpx 版本组合的弃用警告，暂不影响接口行为，后续需要统一测试依赖版本。

独立的旧 FTA 回归脚本仍有 1 个 AOCS 案例失败（原因数量不足 2），其余 3 个案例通过。该路径属于旧建树逻辑，本阶段没有修改。

## 6. 未闭合风险

- 默认仓储已切换为 SQLite；当前按单机、单文件设计，数据库迁移版本 1 和基础备份能力已具备。
- 多进程部署、网络文件系统和并发容量边界仍未作为支持场景验收。
- 数据库本身不可写时，建树尝试无法追加，接口会返回服务错误；这属于持久化故障，不能伪造审计记录。
- 当前建树重试记录已经落地，但更细的失败分类、任务队列和补偿调度仍属于后续专题。
- 前端两个现有入口已切换到审核优先流程：抽取后读取 pending，审核完成后放行并建树；
  现有布局和样式保持不变，新增状态与动作投影位于原“抽取结果”区域。
- 前端只在 `/api/fta/release` 返回未被拦截的记录后调用 `/api/fta/build_released`，
  建树 JSON 只在展示层转换成现有画布可消费的 DOT。
- 真实在线模型的接口和证据结构已用 27 条样本复测；已根据 `FTA_故障记录_2.txt` 生成独立专家金标 v2。
  故障树 AND/OR 逻辑金标和微调链路仍未完成；字段抽取已有正式 Precision/Recall/F1 回放报告。
- `full_generate`、旧规则路径和新审核式抽取路径仍在后端并存；当前前端主入口不再调用
  `full_generate`，后续删除旧接口仍需单独评估调用方和迁移窗口。

## 7. 下一步最安全动作

推荐顺序：

1. 已根据 v9 项目审核生成中间集：
   `evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v1.json`。
   该文件包含 27 条样本，项目审核结论为 27 条“审核通过”，但其字段与模型输出同源，不能直接计算独立 F1。
2. 已导入独立领域专家报告，生成正式金标：
   `evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v2.json`，并生成字段 F1 回放报告：
   `evaluation/quality_eval/runs/fta_project_handbook_expert_gold_v2_f1.json`。
   当前候选原因 F1=0.5946，是下一阶段语义优化重点；27 条样本继续固定为 `test`，不直接进入训练。
3. `logic_status` 仍为 `unknown`，因为当前审核确认的是抽取字段和证据，不是故障树 AND/OR 逻辑；之后再做浏览器端真实数据验收，覆盖抽取、pending、批准、放行、建树成功和建树拒绝展示。
4. 如果要部署多实例，再单独设计数据库并发、任务队列和备份恢复验收。

### 7.1 公开数据扩展

已从公开的 SINAMICS S210 手册故障章节抽取 281 条未标注公共语料：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl`
- `evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.manifest.json`
- 生成脚本：`evaluation/quality_eval/public_sources/build_siemens_s210_fault_corpus.py`

该语料用于新样本抽取和后续专家抽样审核，不直接当作金标，也不自动写入生产数据库。由于调用云端模型
会产生 API 成本，批量跑 281 条之前需要单独确认批量预算；当前只完成了下载、解析、来源记录和结构校验。
当前已先固定 30 条分层抽样（F=20、A=8、N=2），专家清单为
`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v1.md`，未预填结论。

为扩展数据量，已从剩余 251 条语料中生成第二批不重复的 30 条分层审核候选（F=20、A=8、N=2）：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v2.json`
- `evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v2.md`

第一批与第二批合计覆盖 60 条，仍有 221 条未抽样。第二批当前仍是
`unlabeled_expert_review_sample`，不能直接写入生产数据库或标记为 `approved`；需先完成专家审核，
再导入候选标注集并决定是否进入金标库。

随后已生成第三批不重复审核候选：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v3.json`
- `evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v3.md`

三批合计覆盖 90 条，剩余 191 条未抽样；三批均保持 F=20、A=8、N=2 的分层结构，当前仍未标注。

随后已将全部 281 条组织成 10 个互不重复的审核批次（v1–v9 每批 30 条，v10 为 11 条），
全量审核队列清单为：

`evaluation/quality_eval/datasets/siemens_s210_public_fault_review_batches_v1.manifest.json`

当前队列覆盖数为 281/281，重叠数为 0；其中已有 30 条由用户确认的专家结果，
其余 251 条仍待审核。未审核批次不能直接当作金标或写入生产库。

已生成统一审核队列：

`evaluation/quality_eval/datasets/siemens_s210_public_fault_full_review_queue_281_2026-09-20.json`

专家填写用文本清单：

`evaluation/quality_eval/runs/siemens_s210_public_fault_full_review_queue_281_2026-09-20.md`

对 251 条待审核候选已运行只读结构审计：129 条包含缺少候选原因证据、空组件声明证据或需要语义核对的项目，
报告为 `evaluation/quality_eval/runs/siemens_s210_public_fault_pending_structural_audit_2026-09-20.json`。
结构审计不等于语义审核；其中只有 1 条可以依据 Cause 原文提出精确证据补齐建议，报告为
`evaluation/quality_eval/runs/siemens_s210_public_fault_pending_evidence_proposals_2026-09-20.json`，仍需专家接受。

专家提交结论后，使用 `finalize_public_review_decisions.py` 将候选转为最终 `gold_records` 并追加审核历史；
该定稿器要求每条 pending 都有显式结论，任何未解决的证据不足、无法判断或排除记录都会保持 `import_ready=false`，
不会绕过最终数据库导入闸门。

251 条待审核结论的空白模板为 `evaluation/quality_eval/runs/siemens_s210_public_fault_review_decisions_template_251_2026-09-20.json`。

该队列实际区分两种当前状态：30 条 `confirmed_expert`（其中原始 6 条“证据不足”已按专家明确意见补齐原文证据，
原始结论仍保留在审核历史）、251 条 `pending`（模型候选待专家审核）。因此当前仍不是可入库金标，原因是 251 条尚未有最终专家结论。
补证据后的派生专家文件为 `fta_unified_expert_review_57_2026-09-20_evidence_resolved.json`；原始文件不覆盖。
统一队列由 `build_full_public_review_queue.py` 生成，并在合并时校验 281 条覆盖、唯一 ID 和批次不重叠。

已对 v2–v10 共 251 条执行一次真实后端抽取回放：251/251 成功，251/251 的证据位置通过结构匹配校验，
并生成待审核候选文件：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_review_candidate_v2_2026-09-20.json`
- `evaluation/quality_eval/runs/siemens_s210_public_fault_review_candidate_v2_2026-09-20.md`

这些记录仍为 `pending`，没有自动升级为专家结论或 `approved`。批量脚本曾因 `/api/fta/generate`
输入字段错误导致 400，现已改为 `raw_text` 并增加回归测试；修复后的回放结果为 30/30 成功。

为最终全量入库，已增加 `evaluation/quality_eval/project_gold/import_reviewed_dataset_to_sqlite.py`。
该入口默认要求 281 条最终审核数据，校验字段级证据和来源后，在单事务中写入；数据库 schema 已升级到 v4，
新增数据集导入、样本来源原文快照和结果映射表，支持同一数据集版本幂等重跑。当前只完成导入闸门和测试，
尚未导入 281 条，因为后续批次尚未完成最终审核。

### 7.2 用户确认采用的 57 条专家审核结果

2026-09-20，用户明确确认将
`C:\Users\爹\Downloads\FTA_故障记录专家审核清单_57条_专家逐条已审核完整版.md`
作为本项目的专家审核来源。该文件覆盖项目手册 27 条和公开 SINAMICS S210 30 条。
已复制并导入：

- `evaluation/quality_eval/datasets/fta_unified_expert_review_57_2026-09-20.md`
- `evaluation/quality_eval/datasets/fta_unified_expert_review_57_2026-09-20.json`
- `evaluation/quality_eval/project_gold/import_unified_expert_review.py`

结构化结果保留模型原始结果、字段级证据、完整原文、专家结论、修正字段和审核历史，
并将用户确认的审核来源标记为 `user_accepted_expert_reviewed`。当前结论统计为：
42 条审核通过、8 条语义需修改、6 条证据不足、1 条无法判断。由于仍有未决记录，
严格 F1 不自动标记为 ready；AND/OR 逻辑仍保持 `unknown`。该集合仅用于测试/评估，
不直接写入生产数据库，也不混入训练集。

### 7.3 2026-09-20 真实回放结果

用户确认后，已使用最新候选原因语义约束、故障现象边界规则和证据归一化规则，真实重跑全部 57 条：

- 项目手册 27/27 成功；公开 SINAMICS S210 30/30 成功；没有失败或缺失预测。
- 预测与专家金标合并为独立回放文件：
  `evaluation/quality_eval/runs/fta_unified_expert_review_57_after_boundary_policy_2026-09-20.json`。
- 最新报告：
  `evaluation/quality_eval/runs/fta_unified_expert_review_57_f1_after_boundary_policy_2026-09-20.md`。
- `fully_supported_50` 口径：故障码 1.0000、组件 0.9836、关联组件 1.0000、故障现象 0.9900、
  候选原因 0.9503、参数 1.0000。

这证明当前后端抽取、证据绑定和评估流程可以完整跑通，但不证明 57 条之外的语义泛化已经完成。
当前剩余误差是少数原因粒度/漏抽样本；AND/OR 逻辑仍未进入评估。后续应优先补充这类错误样本，
再决定是否做训练或微调，不应把测试集直接用于训练。

禁止的捷径：

- 不把 `ExtractionResult.records` 直接传给建树层；
- 不把 `FAILED` 当作 `EMPTY`；
- 不在 API 层重新实现审核规则；
- 不为了绕过审核在旧 `full_generate` 中加入静默 fallback；
- 不在没有真实训练数据和评测指标时宣称已经完成深度学习微调。

### 7.4 2026-09-20 公开 S210 281 条 AI 辅助审核金标入库

用户明确同意将多轮 AI 审核结果按“AI 辅助专家审核”口径合并为正式评估金标，不能伪称为真人专家审核。
最终文件为：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json`
- 合并决策：`evaluation/quality_eval/runs/siemens_s210_public_fault_ai_expert_review_decisions_251_final_merged_2026-09-20.json`

最终数据集包含 281 个样本和 281 条故障记录，`label_status=ai_assisted_expert_reviewed`、
`training_eligible=false`、`import_ready=true`；逻辑门仍为 `unknown`，不进入本轮 F1 或金标逻辑判断。
数据集保留三轮审核历史、第三轮针对争议记录的复核结果以及字段级证据，金标字段值未因证据修复而改变。

证据入库前新增了可复现的证据修复脚本
`evaluation/quality_eval/public_sources/repair_final_gold_evidence.py`：仅把证据引用投影为原文精确切片，
并为 6 个因换行/编号/参数插入导致无法自动对齐的候选原因补充原文跨度；不凭空生成“组件为无”的证据，
该公共手册数据集使用显式的 `component_evidence_policy` 记录“原文未声明组件”这一情况。

数据库 `backend-python/outputs/extraction_workflow.sqlite3` 已完成原子导入：

- `dataset_imports`：1 个数据集版本，状态 `completed`，记录数 281；
- `dataset_import_records`：281；`extraction_results`：281 条本次关联结果；
- `fault_records`：281；`evidence_spans`：2,847；
- 本次审核历史：281 条 `approved`，51 条 `revision` 后续记录；
- 重复执行导入命令返回 `already_imported`，未产生重复数据。

本轮验收命令已通过：5 个导入/定稿单元测试、Python 编译检查、281 样本导入预检、实际事务导入和幂等重跑。

### 7.5 2026-09-21 Retrieval Evaluation Dataset v1

根据“冻结 Gold、独立评测检索”的方案，已生成第一版中文检索评测集：

`evaluation/quality_eval/datasets/siemens_s210_retrieval_evaluation_v1_2026-09-21.json`

当前包含 42 条分层查询：故障码 6 条、故障现象 9 条、候选原因 9 条、处理动作 5 条、组件 5 条、参数 5 条、
高歧义描述 3 条；同时覆盖 easy/medium/hard，并包含多正确故障码和信息不足样本。

评测口径固定为：以 `fault_code` 为排名单位；一个查询的 `relevant_fault_codes` 中任意一个进入 Top-K 即视为命中；
输出 Recall@1、Recall@3、Recall@5 和 MRR。查询标签由冻结 Gold 派生，标记为
`ai_assisted_benchmark_derived_from_frozen_gold`，不是人工编写的领域专家查询金标。

已增加生成和校验脚本：

`evaluation/quality_eval/public_sources/build_siemens_s210_retrieval_eval_dataset.py`

当前只完成评测集和结构校验，尚未宣称向量检索指标。下一步应实现 Baseline A（整条故障记录）和 Baseline B
（description + causes），再逐步加入故障码/参数精确检索、组件加权、按 fault_code 聚合和 reranker，
每版单独保存 Recall@1/3/5 与 MRR 及错误类型分析。

第一版本地诊断基线已完成：

`evaluation/quality_eval/runs/siemens_s210_retrieval_baseline_diagnostic_2026-09-21.md`

结果为：

| 版本 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| full record 字符 n-gram TF-IDF | 0.2381 | 0.2857 | 0.3333 | 0.4286 | 0.2937 |
| description + causes 字符 n-gram TF-IDF | 0.0714 | 0.0952 | 0.1190 | 0.2143 | 0.1139 |
| description + causes + 精确码/参数/组件加权 | 0.3095 | 0.3810 | 0.4048 | 0.5000 | 0.3729 |

该结果只说明当前中文查询与英文 Gold 的词法基线存在跨语言匹配不足，不能说明 Gold 有问题，也不能代表生产向量模型效果。
下一阶段应在同一评测集上接入真实多语言 embedding；再增加按 `fault_code` 聚合后的候选融合和 reranker，
并对 Top-5/Top-10 未命中样本区分 `insufficient_query_context`、`ambiguous_description` 与真正检索失败；
Recall@10 作为 reranker 候选召回上限指标一并记录。

已确定第一轮本地模型为 `BAAI/bge-m3`，只启用 dense embedding；A/B/C 运行器为
`evaluation/quality_eval/public_sources/run_siemens_s210_bge_dense_ablation.py`，
实验环境版本记录在 `evaluation/quality_eval/public_sources/retrieval_environment.yml`。
当前环境已安装 `torch 2.14.0+cpu`、`sentence-transformers 6.1.0` 和 `transformers 5.17.0`，
本轮使用 Windows 用户代理 `http://127.0.0.1:7897` 作为当前下载/实验进程的临时代理，未修改系统全局代理配置。
BGE-M3 权重已下载到 `tmp/retrieval_models/huggingface`，并在 CPU 上完成 A/B/C dense-only 消融实验。

实验结果已写入：

- `evaluation/quality_eval/runs/siemens_s210_bge_m3_dense_ablation_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_m3_dense_ablation_2026-09-21.md`

| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| A_description_dense | 0.4286 | 0.5476 | 0.6190 | 0.6667 | 0.5224 |
| B_cause_dense | 0.2857 | 0.4286 | 0.4524 | 0.5714 | 0.3883 |
| C_description_cause_rrf | 0.3333 | 0.4762 | 0.6429 | 0.7143 | 0.4649 |

A/B/C 基线本轮未启用 sparse、ColBERT、exact matching 或 reranker。结果表明 description dense 的召回优于 cause dense，
description/cause 的 RRF 融合把 Recall@10 提升到 0.7143，但在 Recall@1 和 MRR 上没有超过 description-only；
不能把当前 42 条、由 Gold 派生的评测结果解释为专家查询集或生产效果。

### 7.6 2026-09-21 Retrieval Experiment D

已在 C 的 `description/cause RRF` 基础上完成 D：

- 故障码命中：强优先级，将 query 中明确出现的 `A/F/N + 5 位数字` 故障码置于前列；
- 参数命中：对 query 中的 `p####`/`r####` 参数做精确匹配和加权，不做唯一过滤；
- 组件命中：使用中英文/中文组件别名做软加权，不做硬过滤；
- 仍以 `fault_code` 为最终排名单位，不启用 sparse、ColBERT 或 reranker。

本轮固定权重记录在结果 JSON 的 `evaluation_info.hybrid_signal_weights`：故障码 100.0、每个参数 0.25、每个组件别名 0.05。
每条查询的 `A_rank`、`B_rank`、`C_rank`、`D_rank` 已写入 `rank_changes`，其中 rank 表示第一个相关故障的排名。

结果文件：

- `evaluation/quality_eval/runs/siemens_s210_bge_m3_dense_ablation_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_m3_dense_ablation_2026-09-21.md`

| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| C_description_cause_rrf | 0.3333 | 0.4762 | 0.6429 | 0.7143 | 0.4649 |
| D_exact_hybrid | 0.5000 | 0.5952 | 0.6905 | 0.7857 | 0.5879 |

D 相比 C：Recall@1 提升 0.1667，Recall@10 提升 0.0714，MRR 提升 0.1230；6 条故障码查询和 5 条参数查询均在 D 中实现 Recall@1=1.0。
组件查询组的表现反而下降，说明当前组件别名/软加权仍需误差分析，不能直接据此增加更强的组件规则。
当前停止条件已满足：D 的 Recall@10 达到 0.7857，可进入 Top-10 未命中样本分析；只有确认候选已召回但排序靠后后，才决定是否进入 E reranker。

### 7.7 2026-09-21 D1/D2/D3 消融与 Hybrid 信号审计

为区分不同结构化信号的作用，已在同一份冻结 Gold 和同一份 42 条评测集上完成：

- C：description/cause dense RRF；
- D1：C + `fault_code` exact；
- D2：D1 + `parameter` exact；
- D3：D2 + `component` soft boost。

运行器：`evaluation/quality_eval/public_sources/run_siemens_s210_bge_hybrid_ablation.py`。
结果与逐查询信号日志：

- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_ablation_d1_d3_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_ablation_d1_d3_2026-09-21.md`

| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| C_description_cause_rrf | 0.3333 | 0.4762 | 0.6429 | 0.7143 | 0.8095 | 0.4649 |
| D1_fault_code | 0.4762 | 0.6190 | 0.7857 | 0.8571 | 0.9286 | 0.6045 |
| D2_fault_code_parameter | 0.5952 | 0.7143 | 0.8571 | 0.9286 | 0.9762 | 0.6980 |
| D3_fault_code_parameter_component | 0.5000 | 0.5952 | 0.6905 | 0.7857 | 0.8810 | 0.5879 |

D2 是当前最优候选：相对 C 的 Recall@10 提升 0.2143，MRR 提升 0.2331；故障码组和参数组均达到 Recall@1=1.0。
D3 反而退化，D3 相比 C 的回归查询为 `Q007/Q021/Q024/Q028/Q030/Q031/Q032/Q034`。
逐条日志已记录 query 命中的故障码/参数/组件、每个 fault 的 bonus、C/D1/D2/D3 rank，以及因 bonus 超过相关 fault 的候选。

初步根因已定位为组件 soft boost 的粒度问题：例如 `编码器` 或 `控制单元` 被映射到大量 fault，单个 0.05 bonus 在 RRF 分数尺度下足以把大量不相关候选推到正确结果之前。
因此暂不把 D3 作为候选融合方案，也不进入 reranker；下一步应以 D2 为主线，设计保留 C/D2 召回结果的 candidate fusion，再重新验证 Top-10 上限。

### 7.8 D2 主基线与 Q023 诊断

已将 `D2_fault_code_parameter` 标记为当前主检索基线：description dense + cause dense + RRF + fault_code exact + parameter exact；component boost 不进入主排名。
`reranker_candidate_pool` 暂定为 Top-20。

D2 的 Recall@20 为 `0.9762`，即 42 条查询中 41 条至少有一个相关 fault 进入 Top-20，满足进入 reranker 阶段的候选池条件。

Q023 是唯一的真正 retrieval miss：

- 查询：`驱动对象之间的交叉比较数据不一致，可能是哪类安全故障？`
- 相关 fault：`F01600/F01611/F30600/F30611`；
- C、D1、D2、D3 均为 rank `69`；
- query 中没有明确 fault_code、parameter 或 component，因此没有任何 exact/boost 信号命中；
- D2 Top-10 为 `F30625/A13001/F01651/F01000/F01625/F13102/A01069/F01015/F01672/F31845`。

对四条相关 fault 的原始 `input_text` 核查表明，Q023 的关键表述主要来自故障值/报警值说明，而不是当前 Gold 的 description、causes 或 parameters：
`F01611/F30611` 的 `Fault value (r0949)` 段落明确写有“Number of the cross-compared data that resulted in this fault”，
`F01600/F30600` 则通过后续响应关联到对应的 monitoring-channel fault。
因此 Q023 不是 D2 排序问题，也不是需要更换 embedding 的证据，而是当前索引字段没有覆盖 `fault_value/alarm_value` 语义。

当前结论：Top-20 可以作为 reranker 候选池；Q023 不能依靠 reranker 补救，因为相关 fault 未进入 Top-20。
下一步若要提升该类查询，应新增独立的 `fault_value` 或 `raw_input_text` 检索通道，再单独做通道消融；在此之前不改 Gold、不改 42 条评测集、不训练模型。

### 7.9 2026-09-21 E0 Alarm-value auxiliary retrieval

已完成独立 Alarm-value dense 通道实验。每条 child chunk 从原始 `input_text` 中截取首个 `Fault value`/`Alarm value` 标题开始，
到下一个 `Remedy` 之前结束；本轮 281 条记录中有 151 条存在该段落。没有把 Remedy 或 Note 单独作为本轮检索通道。

结果文件：

- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_alarm_ablation_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_alarm_ablation_2026-09-21.md`

| 实验 | Recall@1 | Recall@5 | Recall@20 | MRR |
|---|---:|---:|---:|---:|
| E0_alarm_dense | 0.1905 | 0.4762 | 0.6429 | 0.3141 |

Alarm-only 总体指标较低，符合它作为辅助通道而非主检索的预期。但 Q023 在 Alarm-only 中的首个相关 fault 排名为 10，
其中 `F01611` 进入 Alarm Top-10；D2 Top20 与 Alarm Top10 按 `fault_code` 去重后的候选并集包含 Q023 的相关 fault。

| 候选池 | candidate_recall | 命中查询数 | 平均池大小 | 池大小范围 |
|---|---:|---:|---:|---:|
| D2 Top20 ∪ Alarm Top10 | **1.0000** | **42/42** | 27.05 | 22～30 |

因此第一版 Candidate Retrieval 已达到 `42/42` 候选召回。当前推荐链路固定为：
`D2 Retriever Top20` → `Alarm auxiliary Top10` → `fault_code 去重并集` → `Reranker`。
Alarm 通道不进入主排序，只负责补充 D2 漏掉的原文报警值语义。

### 7.10 2026-09-21 Reranker 精排实验

已在固定候选池 `D2 Top20 ∪ Alarm Top10`（按 `fault_code` 去重）上完成本地 Cross-Encoder 精排实验。
本轮没有重新召回候选，没有修改 281 条 Gold、42 条评测集、D2 主基线或 Alarm 辅助通道。

- 模型：`BAAI/bge-reranker-v2-m3`；设备：CPU；
- 候选池平均大小：`27.05`，范围 `22～30`；
- 候选召回保持 `1.0000`（42/42）；
- `E_reranker_raw`：只使用 Cross-Encoder 分数排序；
- `E_reranker_guarded`：在 raw 排序基础上，对用户明确输入的故障码执行确定性置顶；不带故障码的查询不改变 raw 排序。

结果文件：

- `evaluation/quality_eval/runs/siemens_s210_bge_reranker_v2_m3_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_reranker_v2_m3_2026-09-21.md`

| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| E_reranker_raw | 0.8810 | 0.9524 | 0.9762 | 1.0000 | 1.0000 | 0.9253 |
| E_reranker_guarded | 0.8810 | 0.9524 | 0.9762 | 1.0000 | 1.0000 | 0.9253 |

Q023 从 D2 的第 `69` 名提升到 reranker 的第 `9` 名，说明它在候选池中但原始 D2 排序靠后；Alarm 通道先将 `F01611` 补入候选池，reranker 再完成排序。原始与 guarded 指标相同，说明本轮 42 条查询中故障码保护没有额外改变最终指标，但两组结果仍保留用于生产策略审计。

按查询类型的 raw 结果显示：fault_code 与 parameter 查询 Recall@1 均为 `1.0000`；cause 为 `0.8889`，symptom 为 `0.7778`，component 为 `0.8000`，ambiguous_description 为 `0.6667`。因此当前主要剩余风险是信息不足或描述高度相似时的 Top-1 排序，而不是候选召回不足。

当前检索闭环可进入下一步系统设计：
`D2 Top20` → `Alarm auxiliary Top10` → `fault_code 去重并集` → `bge-reranker-v2-m3` → Top-K fault。
但 42 条查询仍属于开发/验证集，不应据此宣称生产泛化能力；下一阶段应保留一份不参与调参的最终检索测试集，并对 raw/guarded 策略做回归。

### 7.11 2026-09-21 Retrieval Final Test v1 与阶段 A 验收

已建立独立 Final Test Query 数据集：

- `evaluation/quality_eval/datasets/siemens_s210_retrieval_final_test_v1_2026-09-21.json`
- 共 `39` 条全新中文查询，查询文本与原 `Retrieval Evaluation v1` 的 `42` 条查询零重复；
- 覆盖 `fault_code`、`symptom`、`cause`、`remedy`、`component`、`parameter`、`alarm_value`、`ambiguous_description`；
- 相关性标签仍来自冻结的 281 条 Gold，明确标注为工程 holdout，不冒充人工专家查询标注；
- 该集合不参与参数、模型、chunk、bonus 或 reranker 调整。

Final Test 使用与开发阶段完全相同的 Retrieval Pipeline v1：
`BGE-M3 description/cause RRF` → `fault_code/parameter exact` → `Alarm Dense auxiliary` →
`D2 Top20 ∪ Alarm Top10` → `fault_code 去重` → `bge-reranker-v2-m3`。

候选召回结果：

- `candidate_recall = 1.0000`（39/39）；
- 候选池平均大小 `27.08`，范围 `22～30`；
- D2 的 Final Test：Recall@1 `0.7949`、Recall@3 `0.9231`、Recall@5 `0.9487`、Recall@20 `1.0000`、MRR `0.8611`。

Final Reranker 结果文件：

- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_final_test_v1_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_m3_hybrid_final_test_v1_2026-09-21.md`
- `evaluation/quality_eval/runs/siemens_s210_bge_reranker_final_test_v1_2026-09-21.json`
- `evaluation/quality_eval/runs/siemens_s210_bge_reranker_final_test_v1_2026-09-21.md`

| 实验 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| E_reranker_raw | 0.9231 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9573 |
| E_reranker_guarded | 0.9231 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9573 |

Final Test 上 raw 与 guarded 指标一致；故障码显式保护仍保留为生产安全策略，但没有把保护策略收益误报为模型收益。当前阶段 A 的停止条件已满足：S210 Retrieval Pipeline v1 有固定配置、独立最终测试集和可复现成绩。后续不得用 Final Test 反向调参；若新增测试查询，应建立 v2，而不是覆盖 v1。

### 7.12 2026-09-21 Phase B RAG 核心链路

已开始阶段 B，但本轮只落地后端核心合同，不提前接 API 或前端。新增：

- `backend-python/rag_contract.py`：定义 `FaultRetriever`、`FaultContextLoader`、`AnswerGenerator` 三个可替换端口，以及 `RetrievedFault`、`FaultContext`、`EvidenceCitation`、`RagResponse` 数据合同；
- `backend-python/rag_service.py`：实现检索结果去重、完整故障上下文加载、Alarm value/Remedy 原文分段、Evidence spans 装载、证据约束提示词和回答引用校验；
- `backend-python/tests/test_rag_service.py`：覆盖上下文完整性、证据引用、候选去重、缺失引用拒绝和未知引用拒绝。

`GoldFaultContextStore` 已对冻结 Gold 实际加载验证：281/281 条故障上下文成功，281/281 条有 Remedy，281/281 条有 evidence，151 条有 Alarm/Fault value 段落，共保留 2653 条去重后的 evidence span。

当前阶段 B 的边界：

- RAG 核心编排和证据安全合同已完成；
- `PromptAnswerGenerator` 已通过 provider-neutral `ModelClient` 接入点支持 DeepSeek/Qwen 等 OpenAI-compatible 模型；
- 真实 BGE/Reranker runtime adapter、HTTP API 和前端尚未接入，属于阶段 C 的接线工作；
- 在模型没有返回合法 evidence citation 时，服务会拒绝该回答，不返回无证据的“看似完整”结论。

阶段 B 下一步是用真实 Retrieval Pipeline 注入 `FaultRagService`，构造回答评测集，分别评估 fault_code、cause、remedy、evidence citation 和 hallucination，再进入 API 接线。

### 7.13 2026-09-21 S210 运行检索适配器 smoke test

已新增 `backend-python/s210_retrieval_adapter.py`，把阶段 A 已验证的策略封装为 `FaultRetriever` 实现：

- BGE-M3 description dense + cause dense；
- RRF 融合；
- fault_code exact + parameter exact；
- Alarm/Fault value auxiliary Top-10；
- D2 Top-20 与 Alarm Top-10 按 fault_code 去重并集；
- bge-reranker-v2-m3 精排；
- 明确 fault_code 时 deterministic pin；
- 返回 rank、score、D2/Alarm 来源排名和命中的 exact signals，供 debug/API 使用。

运行适配器不把检索细节泄漏到 `FaultRagService` 或未来 HTTP API。适配器通过 `GoldFaultContextStore` 读取完整故障上下文，RAG 服务只消费 `RetrievedFault` 和 `FaultContext` 合同。

验证证据：

- `backend-python/tests/test_s210_retrieval_adapter.py`：3 个纯逻辑测试通过；
- 真实本地 smoke test：使用冻结 281 条 Gold、BGE-M3 和 bge-reranker-v2-m3，查询“控制单元温度过高，是什么报警？”成功返回 `A01009` 第 1 名、`A30034` 第 2 名、`F30036` 第 3 名；
- backend 全量测试 `113/113` 通过，retrieval 相关测试 `16/16` 通过。

阶段 B 仍未宣称全部完成：回答模型调用和回答评测集尚未落地，HTTP/API 接线仍属于阶段 C。当前已经具备可实例化的 `Retriever → ContextLoader → AnswerGenerator` 核心闭环。

### 7.14 2026-09-21 S210 RAG API 接线与合同验收

已将阶段 B 的核心闭环接入后端 HTTP API，但暂不改动现有前端布局和页面行为：

- `POST /api/rag/query` 接收 `question`、`top_k`、`debug`；
- 首次请求时才懒加载 BGE-M3、bge-reranker-v2-m3 和冻结 Gold，避免服务启动时强制加载大模型；
- 接口内部固定使用 `S210BgeRetriever → GoldFaultContextStore → PromptAnswerGenerator`；
- 默认响应隐藏 `raw_text` 和检索内部 signals，`debug=true` 才返回调试信息；
- 返回中附带 pipeline 名称、召回组合、候选池和 evidence status；
- RAG 服务错误返回结构化 422，模型供应商错误返回结构化 502，未知运行错误不泄漏内部异常。

验证证据：

- `backend-python/tests/test_rag_api.py`：验证正常响应、证据状态、默认脱敏和 debug 信息开关；
- `backend-python/.venv\Scripts\python.exe -m unittest discover -s backend-python/tests -p 'test_*.py'`：`118/118` 通过；
- `py_compile` 和 API 模块导入检查通过。

当前阶段边界：

- API 已具备后端合同和真实检索适配器接线，但尚未用真实外部模型凭证完成一次线上回答验收；
- 在本节记录的 API 接线时点，现有前端尚未调用 `/api/rag/query`；后续 7.16 已完成 Workbench AI 对话入口接入；
- 仍需新增回答质量评测集，单独评估故障码、原因、处理建议、证据引用和幻觉率，不能用检索 Recall 代替回答质量。

### 7.15 2026-09-21 RAG 回答评测合同与证据补全

为进入阶段 B 的回答质量评估，新增：

- `evaluation/quality_eval/datasets/siemens_s210_rag_answer_evaluation_v1_2026-09-21.json`：12 条独立的回答评测问题，覆盖症状、原因、处理、参数、告警值、歧义和多答案场景；该集合不修改检索评测集，也不用于调参；
- `evaluation/quality_eval/public_sources/evaluate_siemens_s210_rag_answers.py`：只评估回答合同，不把检索 Recall 冒充为回答质量；机械检查故障码命中、citation 有效性、citation 所属故障和必需证据字段覆盖；原因/处理语义、越界陈述和跨故障污染保留为人工复核项；
- `evaluation/quality_eval/public_sources/build_siemens_s210_rag_manual_review_template.py`：根据同一冻结数据集生成逐条人工复核模板，预留回答、证据、原因、处理建议、越界陈述和跨故障污染结论；
- `evaluation/quality_eval/public_sources/test_evaluate_siemens_s210_rag_answers.py`：覆盖通过、错误故障证据和缺少响应场景。

同时修正了 `GoldFaultContextStore` 的证据装载边界：冻结 Gold 内容不变，但从每条原文的 `Alarm value/Fault value` 和 `Remedy` 段落生成带 offset 的派生 evidence citation。这样回答处理建议时必须引用具体原文段落，而不是只依赖上下文中未绑定证据的文本。

当前 281 条故障上下文实际验证结果：

- 281/281 有 `remedy` evidence；
- 151/281 有 `alarm_value` evidence；
- 去重 evidence 总数从 2653 增加到 3085；
- RAG 服务、API 合同和回答评测器相关测试通过。

回答评测尚未宣称最终通过：12 条集合目前是开发评测集，真实模型回答文件和人工语义审核仍需下一步生成；在此之前不能声称 RAG 已达到生产质量。

### 7.16 2026-09-21 现有前端 AI 对话入口接入 S210 RAG

保持现有 Workbench 布局和审核/建树页面不变，只替换 AI 对话侧栏的请求和提示内容：

- `frontend/src/components/Workbench.vue` 的 `requestAiChatAnswer()` 现在调用 `/api/rag/query`；
- 现有对话气泡继续显示 `answer.text`，证据 citation 会随回答文本展示，不新增 UI 组件；
- 快捷问题改为控制单元过热、固件下载失败、p7829 参数和直流母线过压，避免旧快捷问题继续调用已不匹配的树分析语义；
- 后端不可用时，现有侧栏新增明确错误提示，不再把空错误对象显示成 `{}`；
- 原有抽取、审核、放行和建树入口未改动。

真实页面验证：

- 本地开发服务 `http://127.0.0.1:8081/` 生产构建和开发编译均成功；
- Workbench 页面可加载，AI 侧栏显示“随时询问 S210 故障记录”和新的快捷问题；
- 后端不可用时页面显示“请求失败：500”，布局未破坏。

当前限制：真实回答需要后端服务、BGE/Reranker 本地模型和 OpenAI-compatible provider 凭证同时可用；本次尚未向外部模型发送真实用户问题，因此不能把前端页面加载成功等同于 RAG 回答质量通过。

### 7.17 2026-09-21 真实运行 smoke test 结论

已启动真实后端并验证：

- `GET /api/health` 返回 `status=ok`；
- 空问题请求被 FastAPI 合同拒绝并返回 HTTP 422；
- 首次有效请求成功触发本地 BGE-M3/Reranker 加载和候选精排，但在等待外部 DeepSeek-compatible provider 响应时未在观察窗口内完成，因此主动终止该次请求，避免后台无限等待；
- 没有把该次未完成请求计入 RAG 回答质量成绩，也没有生成虚假的成功报告。

这暴露出一个后续运行风险：CPU 首次加载/向量预计算和外部 provider 超时需要独立的 warm-up、超时、状态提示和可观测性设计。该次运行本身不能宣称真实端到端回答已通过；后续 7.18 已用修正后的 provider 配置重新完成成功 smoke。

### 7.18 2026-09-21 端到端 RAG smoke test 成功

修正 provider 配置后，真实端到端请求已成功：

- DeepSeek `/models` 返回的可用模型为 `deepseek-flash`、`deepseek-v4-pro`；原配置中的 `deepseek-v4-flash` 不存在；
- `backend-python/.env`、`.env.example` 和 `config.py` 已统一为 `deepseek-flash`，API key 未修改；
- provider 最小调用返回 `OK`；
- `POST /api/rag/query` 对公开问题“控制单元温度过高是什么报警？”返回 HTTP 200；
- `A01009` 被检索/精排到第 1 名，回答包含 6 条有效 evidence citation，`evidence_status=cited`；
- 运行摘要保存于 `evaluation/quality_eval/runs/siemens_s210_rag_answer_smoke_2026-09-21.json`。

这证明了当前一条真实的 `前端入口 → 后端 API → BGE-M3/Reranker → Gold 上下文 → DeepSeek → 证据约束回答` 链路可以闭合。该 smoke 只验证单条公开问题，仍不能替代 12 条回答评测集的语义质量评估。

### 7.19 2026-09-21 RAG 回答评测批量运行器已准备

已新增批量运行器：

- `evaluation/quality_eval/public_sources/run_siemens_s210_rag_answer_evaluation.py`：读取冻结的 12 条回答评测集，逐条调用本地 `/api/rag/query`，保存原始响应批次和机械评测报告；支持 `--query-id` 单条运行、`--dry-run` 离线生成查询计划、超时和输出路径参数；
- 运行器会复用 `evaluate_siemens_s210_rag_answers.py`，不会把检索指标冒充回答指标；
- 新运行器已通过 `py_compile`，既有后端测试 118/118 通过，回答评测器测试 3/3 通过。
- `--dry-run` 已实际运行，确认 12 条查询会被选中且未访问 API；计划输出位于 `tmp/siemens_s210_rag_answer_eval_plan.json`，仅为临时验证产物。
- 人工复核模板已生成：`evaluation/quality_eval/runs/siemens_s210_rag_answer_manual_review_template_v1_2026-09-21.json`，共 12 条空白复核记录。

当前尚未执行 12 条批量调用。原因是该运行器会使用 `backend-python/.env` 中配置的 DeepSeek provider，批量运行属于外部 API 用量，需用户明确允许后再执行。当前可确认的证据仍是 7.18 的单条真实 smoke；在批量响应和人工语义复核完成前，不得宣称阶段 B 的回答质量已通过。

### 7.20 2026-09-21 阶段 B 回答评测与上下文隔离修复

用户授权后已正式运行 12 条回答评测。首轮结果显示故障码命中率和 citation 有效性均为 100%，但回答模型把 Top-5 候选故障全部展开，导致 citation 混入非主故障，回答合同通过率只有 16.67%。这不是检索召回失败，而是生成上下文范围过宽。

已在 `backend-python/rag_service.py` 增加生成范围策略：

- 默认只把首位候选故障交给回答模型；
- 用户明确询问多个故障，且候选排名接近时，才保留多个上下文；
- 对“同一描述、分数接近”的候选保留并列回答，例如 F01611/F30611、F30002/A30502；
- 检索结果仍完整保留在 API 响应中，用于候选展示和 debug，但不会强迫回答模型逐个解释所有候选；
- prompt 要求结论第一行同时引用故障码和故障现象证据。

验证结果：

- 后端测试从 118 项增加到 120 项，全部通过；
- 修复后完整重跑 12 条中的 11 条，RA012 单独增量重跑并合并；
- 最终响应数 12/12，缺失响应 0；
- `fault_code_accuracy=1.0`；`citation_validity=1.0`；`citation_alignment=1.0`；`answer_contract_pass_rate=1.0`；
- 最终响应批次：`evaluation/quality_eval/runs/siemens_s210_rag_answer_responses_final_v1_2026-09-21.json`；
- 最终自动报告：`evaluation/quality_eval/runs/siemens_s210_rag_answer_report_final_v1_2026-09-21.json`；
- AI 辅助逐条语义复核：`evaluation/quality_eval/runs/siemens_s210_rag_answer_manual_review_v1_2026-09-21.md`。

当前阶段 B 的工程验收条件已满足：回答链路、证据约束、检索/回答分离评测和 12 条独立回答评测均有结果。该结论证明系统忠实于冻结 Gold/evidence，不等同于外部 Siemens 领域专家对事实本身的签字；若进入生产，仍应保留专家抽查入口。

### 7.21 2026-09-21 阶段 D Common Fault Schema 第一版

阶段 B/C 验收完成后，开始阶段 D，但暂不改动现有 API、前端和 S210 生产检索器。新增：

- `backend-python/common_fault_schema.py`：定义通用 `FaultEntity`、`FaultEvidence`、`FaultRelation`，并以 `domain + manufacturer + system + fault_code` 生成稳定 `entity_id`；
- `backend-python/siemens_s210_adapter.py`：将冻结 Gold 映射为 Common Fault Schema，保留 S210 特有字段在 `domain_specific`，包括主/关联组件、alarm value、logic status、gold relations 和审核状态；
- Adapter 同时提供父实体范围内的 description/cause/alarm/full child chunks，以及 fault code/parameter exact 字段抽取接口；
- `backend-python/tests/test_common_fault_schema.py`：验证 281 条 Gold 无损映射、281 个唯一 fault code、281 个唯一 entity id、核心字段和 evidence 保留。

阶段 D 当前验收证据：

- Common Schema 测试 3/3 通过；
- 后端全量测试 123/123 通过；
- `py_compile` 通过，`git diff --check` 通过；
- 281/281 条 Gold 已映射，未修改 Gold 文件，未接入新 API。

下一步进入阶段 E：把 Adapter 接口从 Siemens 实现中抽成可替换协议，并为通用 Retrieval Pipeline 定义 entity 聚合合同；在此之前不接入第二领域数据。

### 7.22 2026-09-21 阶段 E Adapter 协议第一版

已新增 `backend-python/domain_adapter_contract.py`：

- `DomainAdapter`：统一 `parse_source()`、`normalize_entity()`、`build_retrieval_chunks()`、`extract_exact_fields()`；
- `RetrievalChunk`：每个子检索块必须保留唯一 `entity_id`，避免多个 child 被误当成多个故障；
- `ExactFieldMatches`：统一承载 fault code、parameter、component 等结构化查询匹配结果。

`SiemensS210Adapter` 已实现该协议的第一版，当前现有 S210 检索器仍通过原有适配器运行，未被强行迁移。阶段 E 的当前门禁证据为后端 123/123 测试通过，S210 281 条无损映射测试仍通过。下一步才是阶段 F：将 Candidate Union、按 `entity_id` 聚合和 Reranker 输入抽成通用 Retrieval Pipeline；不接入第二领域，直到该合同稳定。

### 7.23 2026-09-21 阶段 F Candidate Union 合同第一版

已新增 `backend-python/retrieval_pipeline_contract.py`：

- `CandidateHit` 表示任一路 child retriever 的命中；
- `EntityCandidate` 表示按父 `entity_id` 聚合后的候选；
- `CandidateUnion` 支持按通道限制 Top-K、跨 description/cause/alarm 等通道合并、去重，并保留命中通道、child chunk、分数和 rank 信号；
- 该合同不包含 Siemens fault code 判断，也不决定最终 Reranker 排序，后续 Adapter 和 Reranker 可独立替换。

阶段 F 当前验收证据：Candidate Union 测试 2/2 通过，后端全量测试 125/125 通过，现有 S210 API/前端链路未改动。下一步是为通用 Pipeline 增加 Reranker 输入的 parent entity loader 合同，再考虑将 S210 现有运行适配器逐步接入，而不是一次性替换生产路径。
### 7.24 2026-09-21 通用 Retrieval Pipeline 第一轮接入与 parity 回归

已按“先 Siemens parity、后跨领域扩展”的路线新增通用核心，仍未替换生产 API 或前端：

- `backend-python/generic_retrieval_pipeline.py`：新增通用 `ParentEntityLoader`、`GenericRerankerDocumentBuilder`、角色化检索字段、D2 exact 融合、辅助通道并集和 deterministic identifier guard；
- `backend-python/domain_adapter_contract.py`：新增 `RetrievalFieldValues`，Adapter 只提供 `semantic_primary`、`semantic_cause`、`semantic_auxiliary`、`exact_identifier`、`exact_parameters` 和重排展示字段；
- `backend-python/siemens_s210_adapter.py`：通过 `RetrievalFieldValues` 提供 S210 description/cause/alarm/fault-code/parameter，不把 Siemens 字段判断写进通用 Pipeline；同时修正 Alarm/Fault value 到 Remedy 的边界，使 281/281 条与旧版辅助文本完全一致；
- `evaluation/quality_eval/public_sources/run_siemens_s210_generic_parity.py`：对冻结 Gold、39 条 Final Test、旧 candidate/reranker 报告执行通用管线 parity，并保留每条 query 的候选集合、排名差异和重排信号；
- `backend-python/tests/test_generic_retrieval_pipeline.py`：覆盖父实体加载、重排文档身份、exact identifier guard 和 parameter signal。

Parity 输出：

- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_v1_2026-09-21.json`；
- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_v1_2026-09-21.md`。

当前结果：

| 项目 | 结果 |
|---|---:|
| Gold 父实体映射 | 281/281 |
| 候选集合与旧版完全一致 | 36/39（0.9231） |
| 候选顺序与旧版完全一致 | 28/39（0.7179） |
| 通用 Reranker R@1 | 0.9231 |
| 通用 Reranker R@3/R@5/R@10/R@20 | 1.0000 |
| 通用 Reranker MRR | 0.9573 |

解释：通用管线的最终检索指标与旧版完全一致，候选集合剩余 3 条差异集中在边界排序：`FT022` 的两个相近 D2 候选交换了 Top-20 边界，`FT023/FT030` 涉及无 Alarm value 文本的 `N30800` 空通道排序差异。当前不能把这轮结果写成“100% parity”或直接替换生产实现；它已经证明父实体加载、字段角色映射、候选召回和 Reranker 质量没有下降，但还需要对这 3 条边界差异做可解释的 tie/empty-channel 处理，或正式记录为允许的数值漂移门槛。

本轮测试证据：

- 项目 `.venv` 全量 backend 测试 `128/128` 通过；
- 通用 Pipeline 单元测试 `3/3` 通过；
- `py_compile` 和 `git diff --check` 通过；
- 生产 API、前端、冻结 Gold 和 39 条 Final Test 均未被切换或改写。

下一步停止条件：先处理并复验 `FT022/FT023/FT030` 的候选边界日志；只有候选集合 parity 达到约定门槛且通用指标不下降，才允许把 S210 生产检索器改为通用 Pipeline 的薄适配实现。航空航天数据仍然禁止在该门禁之前接入。

### 7.25 2026-09-21 parity 修复边界诊断与自动门禁

按 parity 修复方案，先将上一轮结果固化为不可覆盖的基线：

- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_baseline_v1_2026-09-21.json`；
- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_baseline_v1_2026-09-21.md`。

本轮只增加诊断和门禁能力，没有改 Gold、39 条 Final Test、模型、权重、RRF/Exact/候选池排名规则，也没有切换生产 API/前端。通用输出新增 `rrf_rank`，并在 parity 报告中保存 description dense、cause dense、RRF、D2 Top20、Alarm Top10、exact 命中和参数 bonus 日志。

新增/更新文件：

- `backend-python/generic_retrieval_pipeline.py`：暴露不可变检索配置和 RRF 中间排名，供诊断使用；
- `evaluation/quality_eval/public_sources/run_siemens_s210_generic_parity.py`：输出 3 条候选集合差异的 `stage_diagnostics`；旧版未持久化的阶段明确标为不可用，不伪造对比；
- `evaluation/quality_eval/public_sources/check_siemens_s210_generic_parity_gate.py`：可重复执行的 parity 门禁。候选集合精确一致率和 Top-K 顺序仅记录，不作为失败条件；候选召回、Top-1 相关性和核心指标作为门禁条件；
- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_v2_2026-09-21.json` / `.md`：本轮诊断结果；
- `evaluation/quality_eval/runs/siemens_s210_generic_retrieval_parity_gate_v1_2026-09-21.json`：门禁结果。

门禁结果：`PASS`。

| 门禁项 | 结果 |
|---|---:|
| Gold 父实体数 | 281/281 |
| Final Test 查询数 | 39/39 |
| 通用候选召回 | 39/39 = 1.0000 |
| Top-1 相关性保持 | 39/39 = 1.0000 |
| R@1 / R@3 / R@5 / R@10 / R@20 | 0.9231 / 1 / 1 / 1 / 1 |
| MRR | 0.9573 |
| 候选集合精确一致 | 36/39 = 0.9231（诊断项） |
| Top-1 序列精确一致 | 39/39 = 1.0000（诊断项） |

3 条差异的阶段定位：

- `FT022`：旧/新 Alarm Top10 完全一致；D2 第 20 位为 `F01002`/`F01000` 边界交换；
- `FT023`：D2 Top20 完全一致；Alarm 第 1 位旧版为无 Alarm 文本的 `N30800`，新版从有文本的 `A01009` 开始；
- `FT030`：D2 第 13 位附近发生 `F01000`/`F01002` 及尾部候选边界漂移，同时旧 Alarm 通道包含无 Alarm 文本的 `N30800`；
- 3 条均未造成相关故障丢失，未造成 Top-1 相关性回归，且核心指标与冻结基线完全一致。

本轮结论：通用 Retrieval Pipeline 已通过“语义行为不回归”门禁；候选集合精确一致率和 Top-K 顺序保留为可观测漂移，不再阻断架构冻结。仍未切换 S210 生产检索器，下一阶段应先冻结 Common Fault Schema v1、Adapter Contract v1、Generic Retrieval Pipeline v1 的文档/契约，再单独启动 `AerospaceAdapter`，不得在通用核心写 `if domain == aerospace`。

本轮验收命令与结果：

- `.venv\\Scripts\\python.exe -m unittest discover -s backend-python/tests -p 'test_*.py'`：128/128 通过；
- `.venv\\Scripts\\python.exe -m py_compile backend-python/generic_retrieval_pipeline.py evaluation/quality_eval/public_sources/run_siemens_s210_generic_parity.py evaluation/quality_eval/public_sources/check_siemens_s210_generic_parity_gate.py`：通过；
- `check_siemens_s210_generic_parity_gate.py --baseline ...baseline_v1... --current ...parity_v2...`：`PASS`；
- `git diff --check -- <本轮触达源码/测试/脚本/交接文档>`：通过；仅有 Git 的 LF/CRLF 提示，不能用生成报告中的换行差异替代源码检查。

### 7.26 2026-09-21 v1 冻结、评测生命周期与生产切换边界

根据 parity 复核，已完成当前架构收口：

- 顶部当前状态已更新为 A/B/C/D/E/F 已完成，G 为下一阶段；旧的“B 未完成、禁止 D-J”只保留在历史上下文，不再是当前真源；
- 新增 `docs/retrieval-platform-v1-freeze.md`，正式冻结 Common Fault Schema v1、Domain Adapter Contract v1、Generic Retrieval Pipeline v1；
- Schema 文档预留 `SourceRecord / KnowledgeVersion` 方向，用于未来区分 `source_version/manual_revision/effective_date/software_version/configuration`，本版不改变 `entity_id` 合同；
- 明确 Adapter 只能声明字段角色，不能决定通用排名算法；Generic 核心禁止出现 `if domain == aerospace`；
- 组件只保留为 metadata/reranker context/显式 scoped filter 候选，不重新启用已被消融实验证明有害的默认 component boost；
- 12 条回答评测集已在数据元信息中正式标记为 `RAG Answer Development / Validation v1`，`eligible_for_final_generalization_claim=false`；12/12 是工程验收，不是生产泛化率；
- 39 条 Retrieval Final Test v1 已标记为 `sealed_historical_final_v1`，后续算法、chunk、router、reranker 或生产切换均新建 v2，不覆盖 v1；
- 记录了 Legacy/Generic shadow mode 与 rollback 设计，当前仍不切生产、不改前端布局。

本轮未启动航空数据；下一步是先用冻结的三个 v1 合同实现小规模 `AerospaceAdapter`，独立建立航空 Dev Set，验证公共检索核心与领域映射的边界，再决定是否需要扩展公共契约。Domain Router、混合领域测试、Relations/FTA 层继续保持未开始。

### 7.27 2026-09-21 Phase G1-G3 FAA SDR 航空适配与 Schema Fit

根据 v1 冻结边界，已开始第二领域最小验证；本轮不要求 S210 production API 先切 Generic，也不修改 Generic Pipeline。

数据源与样本：

- 选用 FAA Service Difficulty Reports 2024 官方 CSV。FAA 下载说明提供按年度的 SDR CSV；该类记录来自运营方/维修站提交的航空器故障、失效和缺陷报告。来源：<https://www.faa.gov/av-info/download_SDR>；2024 文件：<https://external.apic4e.faa.gov/sdrs/retrieve/SDR-2024.csv>；
- 本地原始下载暂存于 `tmp/SDR-2024.csv`，共 66,079 条记录；
- 已生成 40 条确定性开发样本：`evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json`；该文件标记为 adapter development only，不是专家 Gold、不是 Final Test；
- 样本保留原始选中行，选择规则是按结构桶确定性首选再按稳定记录编号补齐，不进行语义标注。

Adapter 与 Fit Report：

- 新增 `backend-python/aerospace_adapter.py`：实现 `FaaSdrAerospaceAdapter`，提供 `parse_source()`、`normalize_entity()`、`build_retrieval_chunks()`、`extract_exact_fields()` 和 `retrieval_field_values()`；
- `OperatorControlNumber` 作为当前 Common Schema 要求的唯一记录身份，并在 `domain_specific.identifier_kind` 标明它不是 native fault code；`JASCCode` 保留为 `domain_specific.jasc_code` 和 exact identifier；
- `Discrepancy` 映射到 description/raw/evidence，只有原文明确出现的 `C/A:` 尾部才进入 remedies；部件状态进入 symptoms，不冒充 causes；BIT、ATA、标准化 flight phase、专家 cause 和 AND/OR 关系均保持缺失；
- 新增 `evaluation/quality_eval/runs/aerospace_schema_fit_report_v1_2026-09-21.md/.json`，结论为 `fit_with_explicit_adaptations`；
- Fit 统计：40/40 entity、40/40 唯一 entity_id、40/40 有字符证据、118 个 parent-scoped RetrievalChunk，raw source row 全量保存在 `domain_specific.raw_record`；
- 新增 `backend-python/tests/test_aerospace_adapter.py`，5 项通过；相关脚本已 `py_compile`。

当前停止条件与下一步：

- 本轮尚未把航空实体跑进 Generic Retrieval Pipeline；
- 下一步 G4 是基于真实采样字段生成 `Aerospace Retrieval Dev v1`，再运行冻结 Generic Pipeline；
- 评测首先按 `adapter_mapping`、`schema_gap`、`retrieval_role`、`chunk`、`generic_contract` 分类错误，不因一次 Dev 指标下降就修改公共核心；
- Domain Router、混合领域 contamination、Relations/FTA/AND-OR 继续未开始。

### 7.28 2026-09-21 Phase G4-G5 航空开发集与 Generic Pipeline 单域评测

G4/G5 已完成第一轮，仍未改动通用核心或生产 API：

- 新增 `evaluation/quality_eval/datasets/aerospace_retrieval_dev_v1_2026-09-21.json`；共 40 条确定性模板派生查询，覆盖 `identifier`、`part_number`、`component`、`condition`、`maintenance_action`，并增加 `sufficient / partially_sufficient / insufficient` 标签；数据元信息明确为 `sealed_development_only`，不是专家查询金标、不是 Final Test；
- 新增 `evaluation/quality_eval/public_sources/run_aerospace_generic_retrieval_dev.py`，调用冻结的 `GenericFaultRetrievalPipeline v1`，使用本地 `BAAI/bge-m3` 和 `BAAI/bge-reranker-v2-m3`，候选池仍为 D2 Top20 + auxiliary Top10，按 `entity_id` 聚合；
- 评测结果保存于 `evaluation/quality_eval/runs/aerospace_generic_retrieval_dev_v1_sufficiency_stratified_2026-09-21.json/.md`；模型排名复用已完成的 40 条运行，后续只增加充分性标签和分层统计：

| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Candidate Union | 0.4000 | 0.4000 | 0.4000 | 0.6750 | 0.8500 | 0.4471 |
| Reranked | 0.8000 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.8250 |

- 分层结果：`sufficient` 24 条的 Candidate R@20/Reranked R@1 均为 1.0000；`partially_sufficient` 10 条的两项均为 0.7000；`insufficient` 6 条的 Candidate R@20 为 0.5000、Reranked R@1 为 0.1667；
- 6 条候选池漏召回、2 条候选内排序未到 Top1；新增 `evaluation/quality_eval/runs/aerospace_generic_retrieval_error_taxonomy_v2_2026-09-21.json/.md`，暂归组件/状态字段为 `retrieval_role`，重复低信息状态词为 `query_ambiguity`；
- 当前判断：明确查询上的第一轮结果稳定，低信息查询是主要风险；不能据此宣称航空领域泛化或专家正确率，也不因此修改 Generic Pipeline。

下一步停止条件：先增加带有机型/JASC/部件号上下文的航空 Dev Query，验证三条暂定问题是否仍存在；只有发现稳定的公共契约缺口，才进入 Generic Pipeline v2 设计。混合领域 contamination、Domain Router、Relations/FTA 仍未开始。

### 7.29 2026-09-21 航空查询充分性对照实验

为区分“模型/公共检索能力不足”和“用户查询信息量不足”，新增：

- `evaluation/quality_eval/datasets/aerospace_query_sufficiency_experiment_v1_2026-09-21.json`：16 条 component/condition 基础查询与对应 16 条 enriched 查询；enriched 只补充目标记录的机型、JASC、组件/部件号，不改变实体、模型或排名参数；
- `evaluation/quality_eval/public_sources/build_aerospace_query_sufficiency_experiment.py`；
- `evaluation/quality_eval/runs/aerospace_query_sufficiency_experiment_v1_2026-09-21.json/.md`。

结果：

| 查询版本 | Candidate R@20 | Reranked R@1 | Reranked MRR |
|---|---:|---:|---:|
| base | 0.6250 | 0.5000 | 0.5625 |
| enriched | **1.0000** | **1.0000** | **1.0000** |

这支持“查询充分性是主要变量”的判断：补充区分实体的上下文后，候选召回和 Top1 都恢复。该实验是受控开发实验，不是生产查询重写规则。

### 7.30 2026-09-21 Siemens + Aerospace 无 Router 混合基线

在评测脚本内用组合 Adapter 将 281 条 S210 与 40 条航空实体放进同一个索引；Generic Pipeline、Common Schema、生产 API 和前端均未修改。本轮不使用 reranker，先隔离混合 Candidate Union 和跨域污染：

- 输出：`evaluation/quality_eval/runs/mixed_domain_retrieval_baseline_v1_2026-09-21.json/.md`；
- 实体 321 条，查询 79 条；
- Candidate Recall@20：`0.9241`；
- WrongDomain@1：`0.1772`；WrongDomain@3：`0.3418`；WrongDomain@5：`0.3797`；
- DomainPurity@1：`0.8228`；DomainPurity@3：`0.7932`；DomainPurity@5：`0.8127`；
- S210 Candidate R@20=`1.0000`，航空 Candidate R@20=`0.8500`。

新增 `evaluation/quality_eval/runs/mixed_domain_error_taxonomy_v1_2026-09-21.json/.md`。结论：无 Router 混合索引存在真实跨域污染，下一步应在同一数据/查询/模型下对照 `no-router` 与 `metadata scope`；仍不直接实现 Router，也不修改 Generic Pipeline。

### 7.31 2026-09-21 Oracle Metadata Scope 对照

在相同 321 个实体、79 条查询和 BGE-M3 下，新增评测脚本 `evaluation/quality_eval/public_sources/run_mixed_domain_scope_comparison.py`，分别建立 Siemens/Aerospace 子索引；查询领域直接使用评测集标签，因此这是 oracle scope 上限，不是生产 Router。

输出：`evaluation/quality_eval/runs/mixed_domain_metadata_scope_comparison_v1_2026-09-21.json/.md`。

结果：

- WrongDomain@1/@3/@5：`0.0000 / 0.0000 / 0.0000`；
- Candidate Recall@20：`0.9241`，与无 Router 混合基线相同；
- S210 Candidate R@20：`1.0000`；航空 Candidate R@20：`0.8500`。

解释：显式领域 scope 能消除跨域污染，但不能修复航空域内部的查询/字段召回问题。因此下一步不是直接把 oracle scope 做成生产 Router，而是构造不含“航空/JASC/Siemens”等显式领域提示的跨域查询，评估 Query → Domain/System 识别是否真实可行；在该实验前继续不改公共核心和生产 API。
