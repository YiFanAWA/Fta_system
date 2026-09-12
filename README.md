# AI FTA System

这是一个面向故障树分析（FTA）的学习型全栈项目：Python/FastAPI 后端负责文本抽取、故障树生成、知识图谱接入和文件导出，Vue 前端负责输入、可视化与交互，`evaluation/` 保存独立的质量评测程序、数据集和历史基线。

本次整理只建立可复现的前后端分离仓库，没有把现有 Python 业务逻辑改写成 Java，也没有把历史评测结果包装成当前质量结论。

## 目录

```text
backend-python/   FastAPI 服务、FTA 核心逻辑和运行示例
frontend/         Vue 3 前端源码
evaluation/       数据修正规则、评测程序、数据集和历史报告
docs/             API、项目说明、设计与历史文档
scripts/          仓库结构门禁
```

运行时生成文件写入 `backend-python/outputs/`；Python 虚拟环境、前端依赖和构建产物均不提交到 Git。

## 本地启动

需要 Python 3.10+、Node.js/npm。Graphviz 是生成 PNG 的可选外部程序；Neo4j 是知识图谱增强所需的可选服务。它们不是 Python 包，因此不能通过 `requirements.txt` 代替安装。

在仓库根目录执行：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r backend-python/requirements.txt
Copy-Item backend-python/.env.example backend-python/.env
```

按需编辑 `backend-python/.env`。调用 AI 路径需要配置有效的 OpenAI 兼容 API；使用 Neo4j 或本地图形工具时，还需要配置对应服务或程序路径。`.env` 已被 Git 忽略。

启动后端：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```powershell
npm ci --prefix frontend
npm run serve --prefix frontend
```

开发服务器默认把 `/api` 代理到 `http://127.0.0.1:8000`。可用 `VUE_APP_API_PROXY_TARGET` 修改开发代理，或用 `VUE_APP_API_BASE_URL` 指定部署环境的 API 根地址；浏览器中已保存的 `api_base_url` 会优先于部署默认值。

## 最小验证

```powershell
python scripts/verify_repo_layout.py
& .\.venv\Scripts\python.exe -m compileall -q backend-python evaluation
$env:PYTHONUTF8='1'
& .\.venv\Scripts\python.exe backend-python/fta_regression_check.py
npm run build --prefix frontend
```

接口和请求示例见 [API 使用说明](docs/api-usage.md)，产品与技术背景见 [项目说明](docs/project-overview.md)，当前已知问题见 [已知问题](docs/known-issues.md)。

## 评测证据边界

仓库保留了 2026-03-31 的[通用指标报告](evaluation/quality_eval/runs/metric_report_20260331_122935.json)和[事件逻辑报告](evaluation/quality_eval/runs/event_logic_report_20260331_134338.json)。它们是历史基线，只说明当时那次运行，不代表当前提交已经重新完成模型、Neo4j 或在线 API 的端到端评测。

## 当前边界

- 当前主线是 Python AI/FTA 后端与 Vue 前端；Java 后端尚未创建。
- 结构迁移后的既有回归基线为 4 个样例中 3 个通过，AOCS 样例仍失败；详见已知问题。
- Docker 文档仅保留为历史材料，当前仓库没有已验证的 Dockerfile 或镜像构建链路。
- 前端包含一个约 22 MB 的背景视频。对外推送前必须确认其版权和公开来源。
