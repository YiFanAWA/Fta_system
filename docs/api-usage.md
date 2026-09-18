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
& .\.venv\Scripts\python.exe -m uvicorn api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000 --reload
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
- `POST /api/fta/reviews/approve`：记录人工批准决定。
- `POST /api/fta/reviews/reject`：记录人工拒绝决定，必须提供原因。
- `POST /api/fta/reviews/revision`：记录要求修改决定，必须提供原因。
- `POST /api/fta/release`：按最新审核状态放行可进入 FTA 建树的故障记录。
- `POST /api/fta/full_generate`：从文本生成 DOT，支持 `hybrid`、`llm`、`deterministic`。
- `POST /api/fta/generate`：通过 `ai`、`manual` 或 `text` 输入生成完整故障树及导出文件。
- `POST /api/fta/review`：生成分析报告和初稿审查。
- `POST /api/kg/query`：执行 Neo4j 查询。
- `POST /api/chat`：结合本地记录、树上下文和可选图谱进行问答。
- `POST /api/fta/generate_agent`：执行现有的分阶段生成工作流。
- `POST /api/fta/generate_from_file`：上传单个文档并生成。
- `POST /api/fta/generate_from_files`：合并多个上传文档并生成。

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
