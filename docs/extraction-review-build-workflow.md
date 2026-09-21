# 抽取—审核—放行—建树后端流程说明

更新时间：2026-09-20

本文说明本次完成的抽取—审核—放行—建树闭环。目标是让一次文本抽取的故障记录、证据、
审核轨迹、放行结果和后续建树尝试都能被单独追踪。前端保留现有页面布局和视觉样式，
只替换接口调用顺序与数据投影。

## 1. 本轮完成的范围

本轮完成后端四个阶段，并把现有前端入口接入这条主线：

```text
抽取结果
  -> 按 FaultRecord 创建审核状态
  -> 人工审核并追加审核历史
  -> 按最新审核状态生成放行快照
  -> 对放行快照尝试建树并追加建树历史
```

本轮没有做以下事情：

- 没有重做 Vue 页面布局、视觉样式或画布交互。
- 没有继续使用旧的 `POST /api/fta/full_generate` 作为抽取入口。
- 没有把前端本地解析结果绕过审核直接当作后端放行结果。
- 没有宣称真实模型抽取质量、证据质量或 FTA 领域质量已经达标。

## 2. 核心对象和职责

### 2.0 公开手册抽取的显式故障码约束

西门子手册常用“行首故障码 + 故障标题”的记录格式，例如 `A01006 Firmware update...`，
不一定出现“故障码”或 `fault code` 关键词。抽取提示词因此允许这种明确的记录头；适配器还提供
一条窄范围确定性兜底：当本次文本只有一个明确的故障记录头、模型只返回一条记录且漏填
`fault_code` 时，回填该行首编号，并通过同一原文位置生成 `fault_code` 证据。

该兜底不会把正文中的 `message F01700` 等内嵌故障消息当作当前记录编号，也不会在多记录或多
故障码场景下按常识猜码。该规则已用行首 A/F/N 编号、正文内嵌编号和证据跨度测试覆盖。

公开手册评估还必须区分三种结果：结构化严格匹配、归一化诊断匹配和正式策略匹配。
当前正式评估版已固定组件规范名，并将双语原值保留为审计别名；description 使用 L3
确定性等价评分，causes 使用 L4 的 coverage × precision。空字段不因模型返回空值而自动算正确，
AND/OR 逻辑门仍然排除在当前字段 F1 外。

为了让多轮模型评估可比较，公开手册评估请求固定 `temperature=0`。当前固定温度基线中，
行首故障码严格 F1 为 1.000，标题主组件归一化 F1 为 0.667；关联组件仍保持保守策略，
不因为正文普通提及自动建立关联关系。英文只有出现 `associated with`、`related to`、
`connected to/with` 或 `linked to` 等明确关系表达时，才保留关联组件；中文显式
`组件为无（关联……）` 仍由组件声明规则处理。该规则先在适配器层过滤，再由提示词约束模型，
因此不会依赖前端判断，也不会改变现有前端布局。

当英文同一分句中同时出现上述明确关系词和受控组件名称，而模型漏填关联组件时，适配器只对
受控词表做窄范围回填；例如 `Control Units are connected with one another` 可回填
`Control Unit`，但 `using the Control Unit`、`to the Control Unit` 不会触发回填。

组件名称的规范化由 `backend-python/component_registry.py` 统一负责。该注册表只维护稳定的
组件别名、标题组件映射和证据别名；它不枚举故障描述或候选原因。未知组件名称保持原值，不能
仅因为词典没有收录就强行映射为已有组件。故障描述和候选原因仍由模型理解，并由证据绑定和
通用审核规则校验；无法确认的结果进入 `pending`，而不是增加一条新的句子规则。

需要注意：公开 S210 专家金标 v1 中仍有少量 `related_components` 把正文上下文中的组件
当作关联组件（例如 “using the Control Unit”）。这与当前保守口径不一致，不能据此直接把
v6 的关联组件 F1 当作模型质量结论；应先由专家确认这些字段是“关联组件”还是“上下文组件”，
再生成与新口径一致的评估金标。当前 v3 正式金标已完成该投影；v11 全量复评的故障码、
主组件和关联组件 F1 均为 1.000，参数 F1 为 0.864，description 为 0.633，causes 为 0.598。

### 2.1 `ExtractionResult`：一次抽取任务的完整档案

`ExtractionResult` 代表一次抽取执行，不等于一条故障。它保留：

- `result_id`：一次抽取任务的 ID；
- `status`：`success`、`partial`、`empty` 或 `failed`；
- `records`：本次抽取出的 `FaultRecord` 列表；
- `evidence_spans`：故障字段对应的原文证据和位置；
- `diagnostics`：解析、模型调用或 fallback 的诊断信息。

每个 `FaultRecord` 的边界以“故障码 + 故障现象”或原文明确的故障记录为单位，
不是以组件为单位。一个故障关联多个组件时，`component` 保留兼容前端的合并展示值，
`related_components` 保留后台组件列表；组件差异不能单独产生新的故障记录。抽取适配器
只归并故障码和故障现象均相同的模型记录，不会把缺少故障码或故障现象不同的记录静默合并。

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

自动准备审核状态时，后端按字段检查证据覆盖，而不是只判断一条记录是否存在任意证据：
`description` 必须有证据；非空的 `fault_code`、`component`、`related_components`、
`causes` 和 `parameters` 必须分别有对应证据；主组件为空但存在关联组件时，还必须有
`component_declaration` 或 `driver_object_declaration` 证据。缺少任一项会创建 `pending`，
并在审核原因中记录缺失字段；候选原因证据缺失使用专门的
`missing_reason_evidence`，其他字段仍使用 `missing_evidence:<field>`，供现有前端展示和专家审核。
候选原因的字段语义定义为“原因、触发条件或故障场景”，证据缺失不等于原因值错误，
二者在评估报告中分别统计。

抽取提示词和后端归一化共同执行两类语义边界：`description` 只保留明确的故障现象/标题，
不把组件前缀、故障类别或 Cause/Remedy 段落拼入；`causes` 允许原因、触发条件和故障场景，
但排除纯诊断编号、处理动作和明确只描述二次故障风险的预防语句。评估器对复合原因拆分、
中文换行和已确认的少量同义表达采用可审计的归一化，不以扩大枚举字典替代模型语义理解。

### 2.4 建树层的职责拆分

建树链路现在分成四个边界：

- `fault_record_tree_mapper.py`：只把已放行的 `FaultRecord` 映射成树生成器输入，不保存数据，也不决定审核状态；
- `fta_tree_contract.py`：定义树的结构校验和来源记录 ID 处理；
- `FaultTreeBuildService`：调用可注入的具体建树器，把成功或失败转换成 `FaultTreeBuildAttempt`；
- `FaultTreeBuildApplicationService`：按 `release_id` 查询放行快照、查询尝试历史，再调用建树服务。

因此，替换规则建树器、模型建树器或测试桩时，不需要修改审核服务、SQLite 仓储或 HTTP 合同。

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

`FaultTreeBuildApplicationService` 先按 `release_id` 读取已保存的放行快照，
`FaultTreeBuildService` 不接收原始 `ExtractionResult`，只接收 `ReleasedExtractionResult`。
因此 `pending`、`revision`、`rejected` 等未放行记录不会直接进入建树层。

建树生成的事件节点会携带 `source_record_ids`。单条故障通常对应一个 ID；如果多条已审核
故障的描述完全相同，树上合并为一个事件节点，但会保留全部来源 ID，不再静默丢失其中一条
审核过的记录。原始证据仍通过 `source_result_id` 回查抽取结果和 `evidence_spans`。

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

建树层在把结果写入尝试记录前会校验树合同：顶事件非空、顶层和子节点逻辑门只能是
`AND`/`OR`、子节点必须是有效对象且树至少包含一个事件。构建器返回非法树时会记录为
不可重试的 `rejected`，不会伪装成成功结果。

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

可通过 `EXTRACTION_DB_PATH` 指定路径。当前 schema 版本为 3：

- v1：抽取结果、故障记录、证据、诊断、审核历史；
- v2：放行快照、放行决策、拦截记录、建树尝试历史。
- v3：故障记录的 `related_components_json`，保存同一故障关联的多个组件。

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

前端沿用现有页面布局和样式，仅在既有“AI 生产输入”和“抽取结果”区域增加状态投影与
审核动作。当前入口统一使用以下调用顺序：

```text
现有抽取页面
  -> 调用 /api/fta/extract
  -> 读取 /api/fta/reviews/pending
  -> 人工动作接口
  -> 调用 /api/fta/release
  -> 调用 /api/fta/build_released
  -> 将成功建树结果转换为现有画布可消费的 DOT
```

前端不重新实现审核规则，也不直接把抽取结果中的全部 `records` 传给建树。前端只展示
后端返回的当前状态；只有 `/api/fta/release` 成功返回放行记录后，才调用建树接口。
后端返回的 JSON 树在前端只做展示层 DOT 转换，不改变后端树合同、放行快照或审计数据。

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

- 前端已接入新流程，但还没有做浏览器端真实模型质量评测；若环境未开启
  `ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE`，规则判定为 `not_required` 的记录仍会由后端拦截。
- 没有做在线模型质量评测、证据准确率评测和领域专家验收。
- SQLite 只按单机单文件边界验证，没有做多实例并发部署验收。
- 当前建树服务已经记录业务拒绝和普通运行时异常，但如果数据库本身不可写，记录无法保存，
  接口会返回服务错误；这属于持久化故障，不应伪造一条成功的审计记录。
- 旧 FTA AOCS 回归路径仍有历史失败案例，本轮没有改动该旧路径。

本轮完成条件是：后端新流程可以独立运行，前端两个现有入口都遵循抽取—审核—放行—建树
顺序，状态和历史可追踪，失败不污染或覆盖既有审核事实。后续模型质量工作仍需单独定义
验收口径。
