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
  -> ReleasedExtractionResult
  -> 后续 FTA 建树
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
  - 当前实现是内存仓储，重启后数据会丢失
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

### API

- `POST /api/fta/extract`
  - 抽取文本并保存待审核结果
  - 返回 `result_id`、记录、证据、诊断和审核状态
  - 不生成 DOT，不建树
- `POST /api/fta/reviews/approve`
  - 记录人工批准
- `POST /api/fta/reviews/reject`
  - 记录人工拒绝，必须有原因
- `POST /api/fta/reviews/revision`
  - 记录要求修改，必须有原因
- `POST /api/fta/release`
  - 根据 `result_id` 查询最新审核状态
  - 只返回允许下游消费的故障记录

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
```

`FAILED` 结果会保存诊断信息，但不创建审核任务，也不生成可放行记录。`PARTIAL` 结果可以包含故障记录，但会进入人工审核。`ExtractionResult` 中的审核快照不能覆盖仓储中的最新审核决定。

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

- 45 个测试全部通过；
- Python 编译通过；
- 仓库布局检查通过；
- HTTP 路由实际验证通过：抽取返回 `pending`，未审核时放行记录数为 0，批准后放行记录数为 1；
- 故意传入不匹配的审核记录时，抽取结果和审核记录都没有写入。

HTTP 测试环境有一个来自 Starlette/httpx 版本组合的弃用警告，暂不影响接口行为，后续需要统一测试依赖版本。

独立的旧 FTA 回归脚本仍有 1 个 AOCS 案例失败（原因数量不足 2），其余 3 个案例通过。该路径属于旧建树逻辑，本阶段没有修改。

## 6. 未闭合风险

- 当前仓储是 `InMemory` 实现，进程重启会丢失数据。
- 真实数据库事务、失败日志、失败任务、重试和补偿机制尚未设计；这些属于后续专题。
- 前端仍调用旧的 `/api/fta/full_generate`，会直接自动渲染故障树，尚未切换到审核优先流程。
- 目前没有完整的前端人工审核页面和待审核列表查询接口。
- 真实在线模型、证据质量、标注数据、Precision/Recall/F1 和微调链路尚未完成评测。
- `full_generate`、旧规则路径和新审核式抽取路径并存，后续迁移时要明确入口，不要把两种合同混用。

## 7. 下一步最安全动作

推荐顺序：

1. 先读取本交接文档和当前 `git status --short`。
2. 为审核页面增加“查询待审核任务”的只读 API，保证人工可以从持久化数据恢复工作，而不是依赖一次抽取响应。
3. 再增加前端审核列表、批准、拒绝和要求修改操作。
4. 前端只在 `/api/fta/release` 返回记录后，才把记录交给 FTA 建树。
5. 之后再设计真实数据库仓储和事务边界。
6. 最后再进入 NLP 评测、错误分析和微调数据闭环。

禁止的捷径：

- 不把 `ExtractionResult.records` 直接传给建树层；
- 不把 `FAILED` 当作 `EMPTY`；
- 不在 API 层重新实现审核规则；
- 不为了绕过审核在旧 `full_generate` 中加入静默 fallback；
- 不在没有真实训练数据和评测指标时宣称已经完成深度学习微调。
