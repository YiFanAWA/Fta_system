# Siemens S210 RAG 语义预审报告 v1

> 本报告是 AI 辅助预审，不是外部 Siemens 领域专家签字。正式语义 Gold 仍需领域专家确认。

## 运行结果

- 30 条新查询已全部调用本地 `/api/rag/query`，HTTP 200：30/30。
- 故障码命中：1.0000。
- 引用有效性：1.0000。
- 引用归属对齐：1.0000。
- 答案结构合同通过率：1.0000。
- 这些指标只证明结构化回答和证据合同，不等同于原因/处理措施的领域语义正确率。

## AI 辅助预审汇总

- 故障识别初审通过：30/30。
- 原因类查询初审通过：6 条。
- 处理类查询初审通过：5 条。
- 引用语义支持初审未发现明显问题：30/30。
- 初审未发现明显无证据声明：30/30。
- 初审未发现明显跨故障污染：30/30。
- 正式语义指标：未宣称，等待领域专家确认。

## 评测金标修正

RAG-021、RAG-027、RAG-028、RAG-029、RAG-030 原先使用单一故障码作为唯一答案，但实际存在配对故障/消息码或共享参数。已将相关码加入 `expected_fault_codes`，否则会把证据充分的回答误判为失败。

## 逐条结果

| Query | 类型 | 故障识别 | 原因 | 处理措施 | 引用支持 | 无证据声明 | 跨故障污染 | 合同 |
|---|---|---|---|---|---|---|---|---|
| RAG-001 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-002 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-003 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-004 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-005 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-006 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-007 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-008 | fault_code | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-009 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-010 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-011 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-012 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-013 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-014 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-015 | symptom | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-016 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-017 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-018 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-019 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-020 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-021 | cause | correct | correct | not_requested | supported | no | no | pass |
| RAG-022 | remedy | correct | not_requested | correct | supported | no | no | pass |
| RAG-023 | remedy | correct | not_requested | correct | supported | no | no | pass |
| RAG-024 | remedy | correct | not_requested | correct | supported | no | no | pass |
| RAG-025 | remedy | correct | not_requested | correct | supported | no | no | pass |
| RAG-026 | remedy | correct | not_requested | correct | supported | no | no | pass |
| RAG-027 | parameter | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-028 | parameter | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-029 | parameter | correct | not_requested | not_requested | supported | no | no | pass |
| RAG-030 | parameter | correct | not_requested | not_requested | supported | no | no | pass |

## 结论

本轮可以确认：当前 Retrieval/Reranker/RAG 结构合同已经闭环，30 条回答均能命中允许的故障码并提供归属正确的证据。当前不能仅凭这轮 AI 辅助预审宣布‘领域语义完全正确’或生成正式 RAG Gold；下一步应由领域专家复核原因语义、处理措施安全性和引用是否真正支持陈述。
