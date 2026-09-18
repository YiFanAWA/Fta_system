# 抽取—审核—放行—建树后端流程说明

更新时间：2026-09-18

本文说明本次完成的后端闭环。目标是让一次文本抽取的故障记录、证据、审核轨迹、放行
结果和后续建树尝试都能被单独追踪。前端页面和布局本轮不改，现有前端也不会自动连接
这些新接口。

## 1. 本轮完成的范围

本轮只处理后端四个阶段：

```text
抽取结果
  -> 按 FaultRecord 创建审核状态
  -> 人工审核并追加审核历史
  -> 按最新审核状态生成放行快照
  -> 对放行快照尝试建树并追加建树历史
```

本轮没有做以下事情：

- 没有修改 Vue 页面、布局、样式和现有组件。
- 没有让旧的 `POST /api/fta/full_generate` 自动切换成审核流程。
- 没有新建审核 UI，也没有把新接口接入前端。
- 没有宣称真实模型抽取质量、证据质量或 FTA 领域质量已经达标。

## 2. 核心对象和职责

### 2.1 `ExtractionResult`：一次抽取任务的完整档案

`ExtractionResult` 代表一次抽取执行，不等于一条故障。它保留：

- `result_id`：一次抽取任务的 ID；
- `status`：`success`、`partial`、`empty` 或 `failed`；
- `records`：本次抽取出的 `FaultRecord` 列表；
- `evidence_spans`：故障字段对应的原文证据和位置；
- `diagnostics`：解析、模型调用或 fallback 的诊断信息。

即使抽取失败，也可以保存带诊断的结果，便于排查和重试；失败结果不会生成审核任务。

### 2.2 `FaultRecord`：审核列表的最小业务单位

审核列表以一条 `FaultRecord` 为一个单位，而不是以整个 `ExtractionResult` 为一个单位。
这样一次抽取包含三条故障时，列表最多出现三条审核项；每条记录可以独立批准、拒绝或要求
补充信息，同时仍然通过 `result_id` 找回同一次抽取的证据和诊断。

### 2.3 `FaultRecordReview`：不可变审核动作

审核动作不会直接修改 `FaultRecord`，每次动作都新增一条带 `review_id` 的审核记录：

| 状态 | 含义 | 是否进入普通 pending 列表 | 默认能否放行 |
|---|---|---:|---:|
| `pending` | 等待人工审核 | 是 | 否 |
| `not_required` | 当前规则判断不要求人工审核 | 否 | 否，需显式配置 |
| `approved` | 人工已批准 | 否 | 是 |
| `rejected` | 人工拒绝 | 否 | 否 |
| `revision` | 人工要求补充证据或重新抽取 | 否 | 否 |

`revision` 是一种后台审核历史状态，不是普通待审核队列状态。本轮按已确认边界，
普通审核列表只抽取当前状态恰好为 `pending` 的记录。后续如果要单独做“待补充证据”列表，
应增加独立查询投影，不应把 `revision` 偷换成 `pending`。

## 3. 当前状态如何判断

状态判断以审核历史中最新一条记录为准，而不是以抽取时附带的审核快照为准：

```text
FaultRecord
  -> review_history(record_id)
  -> 按 created_at + 仓储序号取最新审核动作
  -> 当前审核状态
```

例如：

```text
pending -> revision -> approved
```

当前状态是 `approved`，因此可以放行；但三条历史都会保留。审核记录写入失败时，
该审核动作不会成为当前状态，也不会留下半条记录。

## 4. 放行门和 `NOT_REQUIRED` 策略

`FaultRecordReleaseService` 是审核到建树之间的唯一业务放行门。API 层只负责读取请求、
取当前状态并调用它，不重复实现审核规则。

默认策略：

```text
允许：approved
拦截：pending / revision / rejected / not_required / 缺少审核状态
```

`not_required` 是否可以放行是后端策略开关，不是前端传一个字段就能绕过的判断：

```env
ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE=false
```

只有明确改为 `true` 时，API 才会把 `not_required` 加入放行状态集合。这样保留后台状态
有三个实际用途：

1. 能区分“人工批准”和“规则判断不需要人工审核”；
2. 能在策略改变时重新判断，不必篡改历史审核动作；
3. 能在审计中回答“这条记录为什么没有人工审核”。

## 5. 放行快照

调用 `POST /api/fta/release` 后，会生成 `ReleasedExtractionResult`，并写入 SQLite：

- `release_id`：本次放行快照 ID；
- `source_result_id`：来源抽取任务 ID；
- `records`：允许下游建树的故障记录；
- `review_decisions`：这些放行记录对应的最新审核决定；
- `blocked`：被拦截记录的 ID、状态和原因。

放行快照是历史投影，不会反过来修改抽取结果或审核历史。即使后续审核状态再次变化，
原先已经保存的放行快照仍然能说明当时哪些记录被放行。

一次放行请求会产生一个新的 `release_id`。这保证每次“当时状态下的放行尝试”都能被审计，
代价是重复调用会产生多个快照；如果未来需要幂等放行，应另行设计幂等键，不能依赖覆盖旧快照。

## 6. 建树尝试和失败策略

### 6.1 建树只消费放行快照

`FaultTreeBuildService` 不接收原始 `ExtractionResult`，只接收 `ReleasedExtractionResult`。
因此 `pending`、`revision`、`rejected` 等未放行记录不会直接进入建树层。

### 6.2 每次尝试新增一条记录

调用 `POST /api/fta/build_released` 后，不管建树成功还是业务拒绝，都会创建一条
`FaultTreeBuildAttempt`：

| 字段 | 作用 |
|---|---|
| `attempt_id` | 本次尝试唯一 ID |
| `release_id` | 关联放行快照 |
| `source_result_id` | 关联原始抽取任务 |
| `top_event` | 本次建树使用的顶事件 |
| `status` | `succeeded` 或 `rejected` |
| `reason` | 拒绝原因，成功时为空 |
| `retryable` | 是否可能适合重试 |
| `tree` | 成功生成的树，拒绝时为空 |
| `created_at` | UTC 时间 |

重复调用不会更新上一条记录。例如：

```text
attempt-1: rejected  没有可用于构建故障树的事件
attempt-2: rejected  没有可用于构建故障树的事件
attempt-3: succeeded
```

历史三条都保留，最近一次可以通过 `GET /api/fta/build_attempts/{release_id}` 的最后一项
得到；前两条可用于查明为什么需要重试。

### 6.3 为什么不回滚原审核结果

建树失败发生在审核/放行之后，它说明的是“下游构建尝试失败”，不等于“人工审核失效”。
如果回滚审核状态，会丢失两个事实之间的区别：

- 人工已经批准了什么；
- 建树为什么没有成功。

因此本轮采用：

```text
保留原 FaultRecordReview
保留原 ReleasedExtractionResult
新增一条 status=rejected 的 FaultTreeBuildAttempt
```

这就是“建树拒绝记录”，它不覆盖、不删除、不回滚原审核结果。

## 7. SQLite 持久化和事务边界

默认数据库：

```text
backend-python/outputs/extraction_workflow.sqlite3
```

可通过 `EXTRACTION_DB_PATH` 指定路径。当前 schema 版本为 2：

- v1：抽取结果、故障记录、证据、诊断、审核历史；
- v2：放行快照、放行决策、拦截记录、建树尝试历史。

事务边界如下：

1. 抽取结果和初始审核状态：同一事务写入。任何一方失败，整次写入回滚，避免孤儿抽取或孤儿审核。
2. 人工审核动作：单条追加；写入失败不改变当前状态。
3. 放行快照：快照主记录、放行记录、审核决策和 blocked 原因同一事务写入。
4. 建树尝试：一条尝试单独追加；前一次尝试不会被覆盖。

这里的“回滚”只用于同一个事务中的原子性错误，例如抽取保存和初始审核记录不匹配；
不用于撤销已经成功完成的审核结果。下游建树失败采用追加拒绝记录，以保留真实历程。

SQLite 仓储支持 `backup_to()` 做不覆盖目标的数据库备份。当前支持边界仍是单机、单文件；
不把同一个 SQLite 文件放在网络文件系统中供多个服务实例同时写入。

## 8. 后端接口顺序

### 8.1 抽取

```http
POST /api/fta/extract
```

返回 `result_id`、`records`、`evidence_spans`、`diagnostics` 和初始审核状态。

### 8.2 查询待审核故障

```http
GET /api/fta/reviews/pending
```

返回一个 `FaultRecord` 一条 item，只返回当前状态为 `pending` 的记录；`revision` 不会混进来。

### 8.3 提交审核决定

```http
POST /api/fta/reviews/approve
POST /api/fta/reviews/reject
POST /api/fta/reviews/revision
```

`approve` 需要审核人；`reject` 和 `revision` 还需要原因。

### 8.4 生成放行快照

```http
POST /api/fta/release
```

请求：

```json
{"result_id": "<extraction-result-id>"}
```

### 8.5 尝试建树

```http
POST /api/fta/build_released
```

请求：

```json
{
  "release_id": "<release-id>",
  "top_event": "system failure"
}
```

### 8.6 查询建树历史

```http
GET /api/fta/build_attempts/{release_id}
```

如果 `release_id` 不存在，返回 404；如果存在但尚未尝试建树，返回空 `items` 和 `count=0`。

## 9. 前端接入边界

本轮故意不改前端。未来接入时推荐沿用现有页面布局，只增加调用顺序和数据投影：

```text
现有抽取页面
  -> 调用 /api/fta/extract
  -> 读取 /api/fta/reviews/pending
  -> 人工动作接口
  -> 调用 /api/fta/release
  -> 仅将 response.records 交给现有建树展示
```

前端不应自行判断 `approved`、`pending` 或 `revision`，也不应直接把抽取结果中的全部
`records` 传给建树。后端接口已经为将来接入保留了合同，但当前不会因此新增隐藏 UI 组件。

## 10. 验收证据

本轮执行过：

```powershell
.venv\Scripts\python.exe -m unittest discover -s backend-python\tests -v
.venv\Scripts\python.exe -m compileall -q backend-python
python scripts\verify_repo_layout.py
git diff --check
```

核心流程测试覆盖：

- 单条 `FaultRecord` 待审核查询；
- `revision` 不进入普通 pending 列表；
- 最新审核状态覆盖抽取时的审核快照；
- `not_required` 默认拦截、显式配置后才可放行；
- 放行快照持久化并可重启读取；
- 建树成功追加一条 `succeeded`；
- 建树失败追加一条 `rejected`，不删除放行快照；
- 每次重试产生新的 `attempt_id`；
- SQLite 事务失败不会留下抽取/审核半成品。

## 11. 当前剩余风险

- 前端尚未接入新流程，现有 `/api/fta/full_generate` 仍然是旧的多职责路径。
- 没有做在线模型质量评测、证据准确率评测和领域专家验收。
- SQLite 只按单机单文件边界验证，没有做多实例并发部署验收。
- 当前建树服务已经记录业务拒绝和普通运行时异常，但如果数据库本身不可写，记录无法保存，
  接口会返回服务错误；这属于持久化故障，不应伪造一条成功的审计记录。
- 旧 FTA AOCS 回归路径仍有历史失败案例，本轮没有改动该旧路径。

本轮完成条件是：后端新流程可以独立运行、状态和历史可追踪、失败不污染或覆盖既有审核事实，
并且不要求前端立即修改。后续若进入前端接入或模型质量工作，应另开任务并单独定义验收口径。
