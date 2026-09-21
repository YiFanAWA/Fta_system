# Siemens S210 RAG Baseline v1

## 目标

本基线用于冻结已经通过专家语义审核的 S210 RAG 链路，防止后续 Fault Relation、FTA 和多领域工作继续改动 Retrieval/Reranker/Prompt 后无法判断回归来源。

本基线不是生产就绪声明，也不是新的专家金标。它冻结的是当前回答合同和运行配置。

## 冻结内容

```yaml
Embedding: BAAI/bge-m3
Retriever: D2 + Alarm auxiliary
Reranker: BAAI/bge-reranker-v2-m3
Router: Rule Router v1
Relation: Fault Relation Expansion v1
Generation: deepseek-flash
Device: cpu
```

主召回器保持：`description dense + cause dense + RRF + fault_code exact + parameter exact`；候选池保持 `D2 Top20 ∪ Alarm Top10` 并按 `fault_code` 去重。关系扩展只补充已有候选上下文中的证据支持关系，不改变召回和重排。

## 真实 API 回归

评测集为冻结的 30 条 S210 RAG Semantic Gold v1 查询，接口为 `POST /api/rag/query`，`top_k=5`，`debug=false`。

最终结果：

| 指标 | 结果 |
|---|---:|
| 请求数 | 30 |
| 最终 HTTP 成功数 | 30 |
| 故障码命中 | 1.0000 |
| 引用有效性 | 1.0000 |
| 引用归属对齐 | 1.0000 |
| 答案合同通过率 | 1.0000 |

产物：

- 基线清单：[siemens_s210_rag_baseline_v1_manifest_2026-09-22.json](../evaluation/quality_eval/runs/siemens_s210_rag_baseline_v1_manifest_2026-09-22.json)
- 完整回答：[siemens_s210_rag_baseline_v1_responses_2026-09-22.json](../evaluation/quality_eval/runs/siemens_s210_rag_baseline_v1_responses_2026-09-22.json)
- 合同报告：[siemens_s210_rag_baseline_v1_report_2026-09-22.json](../evaluation/quality_eval/runs/siemens_s210_rag_baseline_v1_report_2026-09-22.json)

## 冷启动说明

第一次完整回归中，RAG-001 因本地模型懒加载超过客户端 180 秒超时，初始状态为 HTTP 0；模型完成加载后单独重试成功，最终 30 条全部 HTTP 200，合同指标均为 1.0000。

因此当前结论是：

- 语义与回答合同：可以冻结；
- 真实服务链路：已完成 30 条回归；
- 首请求耗时：仍是运行风险，不能据此宣称生产就绪；
- 后续应单独处理模型预热、服务启动策略或客户端超时，不应为此修改检索语义。

## 后续边界

冻结后不再修改本基线中的 embedding、retriever、reranker、router 和回答合同。下一阶段进入 Fault Relation Gold、Causal Relation Gold 和 AND/OR Logic Gold；这些是 FTA 推理质量问题，不应通过继续调 RAG 检索来解决。
