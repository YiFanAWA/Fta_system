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

## 2026-09-21 实际运行结果

本轮 30 条新查询已调用本地 `/api/rag/query`，30/30 返回 HTTP 200。自动答案合同复核结果：

| 指标 | 结果 |
|---|---:|
| 故障码命中 | 1.0000 |
| 引用有效性 | 1.0000 |
| 引用归属对齐 | 1.0000 |
| 答案合同通过率 | 1.0000 |

运行产物：

- 回答：[siemens_s210_rag_semantic_responses_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_responses_v1_2026-09-21.json)
- 合同报告：[siemens_s210_rag_semantic_contract_report_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_contract_report_v1_2026-09-21.json)
- AI 辅助预审：[siemens_s210_rag_semantic_ai_review_v1_2026-09-21.md](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_ai_review_v1_2026-09-21.md)
- 专家审核清单：[siemens_s210_rag_semantic_expert_review_checklist_v1_2026-09-21.md](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_expert_review_checklist_v1_2026-09-21.md)
- 专家 JSON 标注模板：[siemens_s210_rag_semantic_expert_review_template_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_expert_review_template_v1_2026-09-21.json)

运行后发现，RAG-021、RAG-027、RAG-028、RAG-029、RAG-030 的原始单答案码标注过窄：它们分别涉及配对故障/消息码或共享参数。已把相关代码补入 `expected_fault_codes` 后重新离线评估，避免将证据充分的配对码回答误判为失败。这是评测 Gold 的口径修正，不是修改生产检索器。

AI 辅助预审初步未发现故障识别、引用支持、无证据声明或跨故障污染问题；但这不等于正式领域语义通过。原因正确性、处理措施安全性和引用是否真正支持陈述，仍需 Siemens 领域专家逐条确认。

## 2026-09-21 专家标注结果

刘武专家已完成 RAG-001～RAG-030 的逐条标注。结构化结果与报告：

- 专家标注 JSON：[siemens_s210_rag_semantic_expert_annotated_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_expert_annotated_v1_2026-09-21.json)
- 专家审核报告：[siemens_s210_rag_semantic_expert_validation_report_v1_2026-09-21.md](../evaluation/quality_eval/runs/siemens_s210_rag_semantic_expert_validation_report_v1_2026-09-21.md)

结果：25 条通过、5 条需要修改（RAG-021、RAG-027、RAG-028、RAG-029、RAG-030），无明显错误、无无法判断记录。原因正确 30/30，处理措施正确 30/30，引用完全支持 29/30，部分支持 1/30，无证据声明和跨故障污染均为 0/30。

这 5 条不是原因或处理措施错误，而是配对故障码/消息码展示不完整，以及参数查询没有完整解释关联关系。修正回答展示策略后，只需复审这 5 条，再冻结正式 RAG Semantic Gold v1。

## 2026-09-21 关系扩展定向回归

针对上述 5 条记录，已新增独立的 Fault Relation Expansion v1。该层位于 Retrieval/Reranker 之后，只负责在已有候选故障上下文中补充有证据支持的配对故障/消息码或共享参数关系，不改变检索、重排和 Router。

定向回归复用了原 30 条评测的检索结果，只重新生成 RAG-021、RAG-027、RAG-028、RAG-029、RAG-030。5 条的故障码合同、引用有效性、引用归属对齐和答案合同通过率均为 1.0000。该结果仍是工程合同回归，不等于专家已经通过修正后的关系表达。

关系扩展设计、注册表、定向回归和专家复审清单见：[Fault Relation Expansion v1](fault-relation-expansion-v1.md)。在专家填写 5 条定向复审前，RAG Semantic Gold v1 不冻结为最终关系金标。
