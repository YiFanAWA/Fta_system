# RAG Semantic Evaluation v1

## 定位

这是回答语义质量评测，不是 Retrieval 评测，也不是 Siemens 领域事实的新金标。检索、Reranker 和 Rule Router v1 保持冻结。

流程：

```text
冻结 281 条 Gold
  ↓
生成新的 30 条中文问题
  ↓
RAG 生成回答
  ↓
自动合同检查
  ↓
人工语义审核
```

## 当前数据

草案：`evaluation/quality_eval/datasets/siemens_s210_rag_semantic_gold_v1_2026-09-21.json`。

该草案从冻结 281 条故障 Gold 中选择未出现在既有 12 条回答评测中的故障码，并生成新的问题表述。当前状态为 `pending_human_semantic_review`，不属于专家金标，也不能据此宣布 RAG 正确率。

人工审核模板：`evaluation/quality_eval/runs/siemens_s210_rag_semantic_review_template_v1_2026-09-21.json`。

## 审核字段

每条回答至少审核：

- `fault_identification`：正确 / 部分正确 / 错误；
- `cause_correctness`：正确 / 部分正确 / 错误 / 不适用；
- `remedy_correctness`：正确 / 部分正确 / 错误 / 不适用；
- `citation_support`：supported / partial / unsupported；
- `unsupported_claims`：yes / no；
- `cross_fault_contamination`：yes / no；
- 备注与审核者。

## 通过条件

本轮只在人工审核完成后报告语义指标。自动 citation 存在、citation 对齐和答案合同通过，只能证明结构合同，不能替代原因/处理措施语义正确性。

已有 12 条回答复核属于历史 AI 辅助参考，不并入本轮 30 条新评测，也不把“AI 辅助复核”表述成外部 Siemens 专家签字。
