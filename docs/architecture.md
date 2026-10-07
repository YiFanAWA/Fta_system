# 当前架构与模块边界

更新时间：2026-09-27  
本文件描述当前代码和接线，不把未来路线图当成已落地系统。

## Decision

single recommended architecture：保留当前各 owner 模块，以 FastAPI 作为协议组合根；正式可持久化的抽取审核建树工作流、S210 RAG 在线链路和离线递归候选 FTA Preview 明确隔离。先以现有代码和证据闭合每条路径，不为了让图看起来统一而提前切换生产。

## 系统分层

```text
Vue frontend
    │ HTTP
    ▼
app.api_server（FastAPI composition root）
    ├── extraction/review/release/build workflow ── SQLite repositories
    ├── AI causal review workflow ───────────────── SQLite snapshot import
    ├── S210 RAG runtime ────────────────────────── Gold context + evidence answer
    └── legacy FTA generation / export endpoints

Separate modules (not wired into the current API path):
    Generic Retrieval / Domain Router / Aerospace Adapter

Offline evidence-bound candidate FTA:
raw text → FaultExtractor → ExtractionResult + evidence
         → CandidateFtaApplicationService
         → CandidateFtaExtractionService
         → candidate / blocked / failed Preview
         （当前无 API route、无正式 DB/Gold 写入）
```

## Owner Layers

| Owner | 唯一职责 | 不应承担的职责 |
| --- | --- | --- |
| `backend-python/app/api_server.py` | HTTP schema 映射、依赖组装、状态码与异常投影 | 不定义抽取、审核、因果或门型语义真相 |
| `backend-python/contracts/` | 跨层数据合同：抽取、审核、放行、通用实体、检索候选、递归 FTA 等 | 不调用模型或执行 I/O |
| `backend-python/extraction/` | 原文抽取应用编排、证据、记录级审核/因果审核、放行和正式建树尝试持久化 | 不由前端或 API handler 直接实现审核规则 |
| `backend-python/domains/` | Siemens/Aerospace 数据映射、组件/数据集注册、可解释领域证据与 Router 规则 | 不拥有通用检索排序算法；Adapter 不通过领域分支改公共检索器 |
| `backend-python/rag/` | 故障上下文、S210 runtime retriever、通用检索编排、关系扩展、回答/边界策略 | 离线通用模块的存在不代表已被生产 API 接线 |
| `backend-python/fta/` | 图/树生成、DOT/导出以及证据约束候选 FTA 服务 | 未经批准的候选不得升级成正式审核树或生产树 |
| `backend-python/workflows/` | 既有端到端工作流和兼容编排 | 新的共享业务语义不应继续堆入旧工作流文件 |
| `evaluation/quality_eval/` | 固定数据集、评测器、运行产物和审计清单 | 运行产物不自动成为 Gold，也不代表 API 当前行为 |

目录概览见[项目模块结构 v2](project-structure-v2.md)。

## 两条 FTA 路径必须分开

### 正式的抽取审核放行工作流

```text
POST /api/fta/extract
  → 抽取并保存完整 ExtractionResult / evidence / 初始审核状态
  → review decisions（新增不可变审核记录）
  → POST /api/fta/release（以最新审核状态决定放行）
  → POST /api/fta/build_released（追加每次建树尝试）
```

此路径由 extraction/application/repository owners 持有，数据库实现位于 SQLite adapter。失败建树保留尝试历史；它是现有正式 API 工作流，不等于自动因果与逻辑门已可靠。

### 证据约束候选 FTA Preview

```text
原文 → FaultExtractor → ExtractionResult
     → 逐记录递归结构/节点/作用域提议
     → 原文唯一引文及 offset 校验
     → 置信策略（provisional）与 blockers
     → candidate / blocked / failed Preview
```

候选层保留提取结果，允许只重试失败记录。节点分解、因果关系和 AND/OR gate 是不同结构；同一列表、多个原因或模型概率都不能自动证明门型。证据重复或位置不唯一时交人工定位；无直接门证据或完整性不足时保持 `unknown`/blocked。事件发生概率一致性校验只能在结构确认后运行，并且不能反向改门。

这条 Preview 路径当前有合同、服务和离线测试，但没有候选 FTA API route、正式数据库写入或正式 Gold 导入。全量门标签/置信度尚未完成校准，故 `fta_ready=false`、`production_ready=false`。

## RAG 与通用检索边界

- 当前 HTTP 入口为 `POST /api/rag/query`，属于 S210 RAG 运行链路，调用 S210 retriever、完整故障上下文加载、证据约束回答和边界策略。
- `GenericFaultRetrievalPipeline` 与 `RuleBasedDomainRouter` 是分离的可测试模块；Router 设计文档明确其未接 API。不可把离线 parity 或混合域指标表述为当前在线路由成绩。
- `AerospaceAdapter` 与 common schema 证明存在第二领域映射实现，不证明多领域在线服务、router isolation 或生产 API 切换已完成。
- RAG 的既有专家回归和 Boundary 回归见 [RAG Baseline v1.1](rag-baseline-v1.1.md)；其中 HTTP 结果是 2026-09-22 的历史运行证据，本轮没有重新运行。

## Forbidden Paths

- Do not 将普通 `/api/fta/generate`、`/api/fta/full_generate` 的成功输出等同为证据约束、专家批准的 FTA。
- 不由模型置信度单独接受 AND/OR，也不把门置信度当事件发生概率。
- 不把 AI 角色复核称为真人专家审核或正式 Gold。
- 不在本阶段把 Generic Retrieval/Router 声称为生产默认，也不因模块存在就进行未经验证的生产切换。
- 不把 RAG 检索/回答的完成度推导为因果图完整或自动建树可信。
