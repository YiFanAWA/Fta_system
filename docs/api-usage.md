# API 使用说明

## 启动

在仓库根目录创建环境并安装锁定依赖：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r backend-python/requirements.txt
Copy-Item backend-python/.env.example backend-python/.env
```

配置 `backend-python/.env` 后启动服务：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn app.api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000 --reload
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

当前健康响应包含 `status=ok` 和构建标识 `2026-04-15-template-parser-v12`。FastAPI 交互文档位于 `http://127.0.0.1:8000/docs`。

## 接口

- `GET /api/health`：健康检查。
- `POST /api/fta/build_dot`：从结构化条目构建 DOT。
- `POST /api/fta/extract`：抽取文本并创建待审核的结构化故障记录，不生成故障树。
- `GET /api/fta/reviews/pending`：按故障记录查询当前处于 `pending` 状态的审核项。
- `POST /api/fta/reviews/approve`：记录人工批准决定。
- `POST /api/fta/reviews/reject`：记录人工拒绝决定，必须提供原因。
- `POST /api/fta/reviews/revision`：记录要求修改决定，必须提供原因。
- `POST /api/fta/release`：按最新审核状态放行可进入 FTA 建树的故障记录。
- `POST /api/fta/build_released`：对一个已保存的放行快照尝试建树，并追加一条建树尝试记录。
- `GET /api/fta/build_attempts/{release_id}`：查询某个放行快照的全部建树尝试历史。
- `POST /api/fta/full_generate`：从文本生成 DOT，支持 `hybrid`、`llm`、`deterministic`。
- `POST /api/fta/generate`：通过 `ai`、`manual` 或 `text` 输入生成完整故障树及导出文件。
- `POST /api/fta/review`：生成分析报告和初稿审查。
- `POST /api/kg/query`：执行 Neo4j 查询。
- `POST /api/chat`：结合本地记录、树上下文和可选图谱进行问答。
- `POST /api/rag/query`：运行 S210 的检索、完整故障上下文加载和证据约束回答链路。
- `POST /api/fta/generate_agent`：执行现有的分阶段生成工作流。
- `POST /api/fta/generate_from_file`：上传单个文档并生成。
- `POST /api/fta/generate_from_files`：合并多个上传文档并生成。

抽取与审核工作流默认使用 SQLite 持久化，数据库文件默认位于
`backend-python/outputs/extraction_workflow.sqlite3`。可以通过环境变量
`EXTRACTION_DB_PATH` 指定其他路径；该配置只影响后端仓储，不改变 API 合同或前端界面。
当前 SQLite schema 版本为 3；默认仓储按单机应用设计，SQLite 的备份由后端仓储提供，
不建议把同一个数据库文件放在网络文件系统上供多个服务实例同时写入。

### S210 RAG 查询

`POST /api/rag/query` 的请求体为：

```json
{
  "question": "控制单元温度过高怎么办？",
  "top_k": 5,
  "debug": false
}
```

该接口固定使用 S210 Retrieval Pipeline v1：BGE-M3 的 description/cause 双路召回、
fault code 和 parameter 精确匹配、Alarm 辅助召回、按 fault code 去重，以及
`bge-reranker-v2-m3` 精排。响应包含 `answer`、`retrieved`、`contexts` 和
`pipeline.evidence_status`。模型回答必须引用上下文中的 evidence citation；缺少引用或
引用未知证据时，后端拒绝该回答。

响应同时包含 `boundary` 和对应的 `pipeline` 状态：

```json
{
  "boundary": {
    "knowledge_status": "supported_with_warning",
    "response_policy": "warning",
    "answer_allowed": true,
    "confidence_level": "medium",
    "need_additional_info": true,
    "warning_required": true,
    "missing_information": ["fault_code_or_device_model"]
  }
}
```

`out_of_domain` 和 `insufficient_evidence` 不会调用回答模型；非 debug 响应也不会把无关的
最近邻故障候选展示为诊断结果。该边界策略只控制回答安全性，不改变检索召回范围。

默认 `debug=false` 时不返回 `raw_text` 和候选的内部 signals；需要诊断检索排名时可临时
使用 `debug=true`。模型按首次请求懒加载，相关配置见 `backend-python/.env.example` 的
`S210_*` 和现有 OpenAI-compatible provider 配置。当前 Workbench 的 AI 对话入口已经接入
该接口；抽取、审核、放行和建树页面仍使用原有接口。

待审核查询以单条故障记录为一个审核项，返回结果 ID、抽取状态、故障记录、证据和当前审核信息：

```json
{
  "items": [
    {
      "result_id": "...",
      "extraction_status": "success",
      "diagnostics": [],
      "record": {},
      "evidence_spans": [],
      "review": {}
    }
  ],
  "count": 1
}
```

故障记录的 `component` 仍是现有前端可直接展示的合并组件文本；当一个故障关联多个组件时，
后端同时返回 `related_components` 列表用于后续建模和审计，当前前端无需新增 UI 组件。

只有当前审核状态为 `pending` 的故障记录会出现在列表中；`revision` 保留在后台审核历史中，但暂不进入普通待审核列表。批准、拒绝或没有人工审核要求的记录不会出现在列表中。失败抽取结果会保留在仓储中，但不会创建审核任务。

`pending` 的自动原因按字段记录证据缺口，例如 `missing_evidence:description`、
`missing_reason_evidence`、`missing_evidence:causes` 或 `missing_evidence:component_declaration`。
其中 `missing_reason_evidence` 专门表示候选原因已有值但缺少直接原文证据；这只补充审核原因，
不改变现有审核接口和前端布局。

## 放行与建树

审核列表完成后，调用放行接口。放行接口每次都会创建一个新的 `release_id`，将当时的
最新审核结果保存成不可变的放行快照。默认只有 `approved` 可以进入快照的 `records`；
`pending`、`revision`、`rejected` 和缺少审核状态的记录进入 `blocked`。`not_required`
默认也会被拦截，只有后端配置 `ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE=true` 时才允许
自动放行，不需要改前端布局或增加 UI 组件。

```json
POST /api/fta/release
{
  "result_id": "<extraction-result-id>"
}
```

典型响应：

```json
{
  "release_id": "<release-id>",
  "source_result_id": "<extraction-result-id>",
  "records": [{"record_id": "...", "description": "pump stopped"}],
  "review_decisions": [{"status": "approved", "reviewer": "reviewer-1"}],
  "blocked": []
}
```

只有 `records` 会交给建树层；`blocked` 只用于解释为什么某条记录没有进入本次快照。
原始抽取结果、证据和审核历史不会被删除或覆盖。

对放行快照尝试建树：

```json
POST /api/fta/build_released
{
  "release_id": "<release-id>",
  "top_event": "system failure"
}
```

成功时返回 `status=succeeded` 和 `tree`；输入不适合建树或构建器拒绝时返回
`status=rejected`、`reason` 和 `retryable`。这两种结果都是 HTTP 成功响应中的业务结果，
因为“建树被拒绝”本身需要进入审计历史，而不是被当成没有记录的接口异常。

成功树的事件节点包含 `source_record_ids`，用于回指本次放行快照中的审核记录；重复描述
被合并时，该数组会保留所有来源记录 ID。原文证据可通过 `source_result_id` 回到抽取结果
和 `evidence_spans` 查询。

每次调用都会新增一个 `attempt_id`，不会覆盖上一次结果：

```json
GET /api/fta/build_attempts/<release-id>
{
  "items": [
    {"attempt_id": "...", "status": "rejected", "reason": "..."},
    {"attempt_id": "...", "status": "succeeded", "tree": {}}
  ],
  "count": 2
}
```

因此，建树失败时保留原审核结果和放行快照，只新增一条拒绝的建树记录；下一次重试
再新增一条记录。查询结果按尝试发生顺序返回，最后一条可作为当前最近一次建树结果，
但前面的失败记录仍然可用于排查和审计。

## 完整生成示例

```json
{
  "system": "Drone",
  "top_event": "Drone Crash",
  "source": "manual",
  "manual_failures": [
    {
      "name": "动力系统失效",
      "probability": 0.12,
      "gate": "OR",
      "causes": [
        {"name": "电机过热停转", "probability": 0.07, "gate": "OR", "causes": []},
        {"name": "电调故障", "probability": 0.03, "gate": "OR", "causes": []}
      ]
    }
  ],
  "use_knowledge_graph": false,
  "run_analysis_report": false,
  "run_draft_review": false,
  "output_prefix": "demo_run"
}
```

该请求可在没有模型密钥和 Neo4j 的情况下检查基础生成链路。`source=ai` 会调用模型；`source=text` 需要提供 `raw_text`，并可通过 `text_chunk_size_chars` 和 `text_chunk_overlap_chars` 调整分块。

返回值根据接口包含 `tree`、`events`、`dot_content`、`extracted_faults`、`analysis_report`、`draft_review` 和 `files` 等字段。运行时文件统一写入 `backend-python/outputs/`。

## 前端连接

开发模式默认通过 Vue 代理请求 `/api`，不需要在前端硬编码主机地址：

```javascript
const response = await fetch('/api/health')
const data = await response.json()
```

可用环境变量覆盖：

- `VUE_APP_API_PROXY_TARGET`：Vue 开发服务器的代理目标。
- `VUE_APP_API_BASE_URL`：构建时写入的 API 根地址。
