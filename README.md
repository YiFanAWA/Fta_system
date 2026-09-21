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

后端内部职责已经进一步拆分为 `app/`、`core/`、`contracts/`、`extraction/`、`domains/`、`rag/`、`fta/` 和 `workflows/`；详见[项目模块结构 v2](docs/project-structure-v2.md)。根目录的少量 Python 文件仅作为旧命令兼容入口，不再承载业务实现。

运行时生成文件写入 `backend-python/outputs/`；Python 虚拟环境、前端依赖和构建产物均不提交到 Git。

## 本地启动

需要 Python 3.10+、Node.js/npm。Graphviz 是生成 PNG 的可选外部程序；Neo4j 是知识图谱增强所需的可选服务。它们不是 Python 包，因此不能通过 `requirements.txt` 代替安装。

在仓库根目录执行：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r backend-python/requirements.txt
Copy-Item backend-python/.env.example backend-python/.env
```

按需编辑 `backend-python/.env`。调用 AI 路径需要配置有效的 OpenAI 兼容 API；当前模板默认按 DeepSeek 配置，填写 `DEEPSEEK_API_KEY` 即可，也可以继续使用 `OPENAI_API_KEY` 或 `QWEN_API_KEY`。使用 Neo4j 或本地图形工具时，还需要配置对应服务或程序路径。`.env` 已被 Git 忽略。

启动后端：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn app.api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000
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
数据集生命周期、实际 SQLite 导入状态和评测口径见 [数据集状态注册表 v1](docs/dataset-registry.md)。

## 评测证据边界

仓库保留了 2026-03-31 的[通用指标报告](evaluation/quality_eval/runs/metric_report_20260331_122935.json)和[事件逻辑报告](evaluation/quality_eval/runs/event_logic_report_20260331_134338.json)。它们是历史基线，只说明当时那次运行，不代表当前提交已经重新完成模型、Neo4j 或在线 API 的端到端评测。

公开资料证据评测集的生成器和边界见 [公开资料证据标注集](evaluation/quality_eval/public_evidence/README.md)。该评测集保留来源、原文位置和 `unknown` 状态，属于来源标注的临时数据，不等同于专家确认的 FTA 金标数据。

软逻辑训练中间格式、来源清单和“模型软判断 + 后端硬约束”边界见 [软逻辑训练数据合同](evaluation/quality_eval/soft_logic_training/README.md)。它统一公开维修日志、OMIn 与项目手册样本；车辆故障候选数据在原始归档和列合同完成核验前保持 `pending`，不生成假样本。

项目自身手册的证据集见 [项目手册证据集](evaluation/quality_eval/project_gold/README.md)，当前从手册中生成 27 条带原文证据的样本，仍不是专家确认的工程金标。

当前抽取器的修复后只读基线报告为 [项目抽取基线](evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline_after_evidence.json)：8 条均返回成功，证据跨度为 56/56 且全部通过原文偏移校验；这只证明证据绑定链路可用，不代表工程因果或逻辑门已经得到专家确认。

针对记录边界、A 类故障码和 r 类参数规则修正后，最新 [27 条项目抽取基线](evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline_semantic_v2.json) 中 27 条请求均成功，且每条样本均归并为一条故障记录。预测证据跨度 196/196 在结构上可回指输入文本；当前临时标注期望 154 条，差异部分来自多组件字段的后台证据。故障码 F1=1.0000、故障现象 F1=0.9630、组件 F1=0.9167、故障值场景候选 F1=0.4167、参数 F1=0.9931。该报告用于验证抽取规则改善，不代表专家语义金标。

2026-09-19 的 [在线基线报告](evaluation/quality_eval/runs/fta_project_handbook_online_baseline_after_fallback_merge.json) 在当前 DeepSeek API 配置下重新运行了 27 条样本；修复兜底归并后每条只保留 1 条记录，196 个证据跨度均能回指原文。结构合法率和 FTA 文件产出率均为 100%，但这仍不是专家语义金标，且疑似幻觉率只是字符串启发式指标。

## 当前边界

- 当前主线是 Python AI/FTA 后端与 Vue 前端；Java 后端尚未创建。
- 结构迁移后的既有回归基线为 4 个样例中 3 个通过，AOCS 样例仍失败；详见已知问题。
- Docker 文档仅保留为历史材料，当前仓库没有已验证的 Dockerfile 或镜像构建链路。
- 前端包含一个约 22 MB 的背景视频。对外推送前必须确认其版权和公开来源。
