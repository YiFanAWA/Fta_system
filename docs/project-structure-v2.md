# FTA System 项目模块结构 v2

本文是当前仓库的目录职责真源。此次整理只改变代码归属和导入路径，不改变 API、数据库合同、抽取语义、检索策略或 FTA 业务行为。

## 总体目录

```text
Fta_system/
├─ backend-python/
│  ├─ app/          # FastAPI 与交互式 CLI 的组合入口
│  ├─ core/         # 配置、模型客户端、提示模板、通用工具
│  ├─ contracts/    # 跨模块共享的数据合同和结构模型
│  ├─ extraction/   # 抽取、审核、放行、建树应用服务与持久化
│  ├─ domains/      # Siemens/Aerospace 适配器、组件与领域路由
│  ├─ rag/          # 检索、RAG、证据绑定、响应策略
│  ├─ fta/          # 知识图谱、故障树生成、校验和导出
│  ├─ workflows/    # 旧版完整编排流程与清理工具
│  ├─ tests/        # 后端合同、集成和 API 测试
│  ├─ config/       # 可审计的领域证据注册表等配置数据
│  ├─ examples/     # 可复现的输入样例
│  ├─ outputs/      # 本地运行时输出，不提交 Git
│  ├─ api_server.py # 兼容入口，真实实现位于 app/api_server.py
│  ├─ main.py       # 兼容 CLI 入口，真实实现位于 app/main.py
│  └─ requirements.txt
├─ frontend/        # Vue 3 页面、交互和 API 展示适配
├─ evaluation/      # 离线数据集、评测脚本、金标与运行报告
├─ docs/            # 架构、API、评测、交接和历史文档
└─ scripts/         # 仓库布局与安全边界门禁
```

## 后端模块职责

### `app/`：应用入口

- `api_server.py`：组装 FastAPI 路由、依赖、仓储和服务；不定义底层抽取/检索算法。
- `main.py`：保留原有交互式 FTA 命令行流程。

根目录的 `api_server.py`、`main.py`、`clean_kb.py` 和 `fta_regression_check.py` 是兼容启动包装器，便于旧命令继续工作；新代码应直接引用对应的包路径。

### `core/`：运行时基础设施

- `config.py`：环境变量、模型、数据库和数据集路径配置。
- `model_client.py`、`openai_model_client.py`：模型客户端协议、重试和 OpenAI 兼容实现。
- `prompt_templates.py`：抽取等任务的提示模板。
- `utils.py`：日志、JSON/文本输出等基础工具。

### `contracts/`：共享合同

这里是跨模块共享语义的唯一 owner，包括抽取结果、审核结果、放行快照、建树尝试、RAG 上下文、检索候选、领域实体和 FTA 树结构合同。API、前端和评测脚本只能消费这些结构化合同，不应自行复制业务状态。

### `extraction/`：抽取审核与建树应用层

- `fault_extractor.py`、`text_extraction_adapter.py`、`file_text_extractor.py`：文本解析、模型抽取和证据绑定。
- `extraction_application_service.py`：一次抽取任务的应用编排。
- `review_*`：审核准备、审核决定、审核历史仓储。
- `release_*`：按最新审核状态放行历史快照。
- `fault_tree_build_*`、`fault_record_tree_mapper.py`：从放行快照尝试建树并保留每次尝试。
- `sqlite_extraction_repository.py`、各 repository：事务、幂等和历史持久化。

### `domains/`：领域适配层

- `siemens_s210_adapter.py`：Siemens S210 字段、证据和检索分块映射。
- `aerospace_adapter.py`：航空公开数据到 Common Fault Schema 的映射。
- `common_fault_schema` 已位于 `contracts/`，保证领域适配器不拥有公共实体合同。
- `domain_router.py`、`domain_evidence_registry.py`：领域信号与范围选择策略。
- `component_registry.py`、`dataset_registry.py`：组件规范化和数据集状态治理。

### `rag/`：检索与证据型回答

- `generic_retrieval_pipeline.py`：跨领域通用候选召回、融合、父实体聚合和重排接口。
- `s210_retrieval_adapter.py`：S210 的 D2 + Alarm 辅助召回实现。
- `vector_store.py`：向量存储适配。
- `rag_service.py`：检索、完整上下文加载、证据约束回答编排。
- `fault_relation_expansion.py`：回答前展开已审核的关联故障/消息关系。
- `response_policy.py`、`query_*`：知识边界、响应策略和查询信息量判断。

### `fta/`：知识图谱与故障树输出

- `kg_builder.py`、`kg_reasoner.py`：Neo4j 节点写入和路径查询。
- `fta_generator.py`、`fta_llm_pipeline.py`：故障树生成管线。
- `fta_tree_contract.py` 位于 `contracts/`，负责树结构合法性；`fta_dot_builder.py` 负责确定性 DOT 构建。
- `visualizer.py`、`xml_exporter.py`：PNG/DOT/XML 等结果导出。
- `fta_regression_check.py`：历史 FTA 回归样例检查。

### `workflows/`：兼容编排流程

- `agent_workflow.py`、`ai_module.py`：旧版端到端编排，逐步由新的 application service 和 RAG service 替代。
- `clean_kb.py`：离线知识库清理工具。

该目录不是共享合同 owner；新增功能应优先进入 `contracts/`、`extraction/`、`rag/` 或 `fta/` 的对应 owner。

## 依赖方向

```text
app
 ├─ workflows / extraction / rag / fta
 └─ core / contracts

workflows ─┬─ extraction ─┬─ contracts
           ├─ fta         └─ core
rag ───────┼─ domains ────┘
           └─ contracts / core
domains ───┴─ contracts / core
fta ───────── contracts / core
```

原则：`contracts` 不依赖 `app`；领域适配器不反向依赖 API；评测代码只能调用后端合同，不能成为生产逻辑的第二份实现。

## 启动与兼容策略

推荐使用包入口：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn app.api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000
```

以下旧入口仍保留：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000
& .\.venv\Scripts\python.exe backend-python/fta_regression_check.py
```

兼容入口只做转发，不复制业务实现；因此未来删除兼容层时不会影响模块 owner。
