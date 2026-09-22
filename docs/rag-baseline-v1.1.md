# Siemens S210 RAG Baseline v1.1

## 定位

v1.1 是在既有 S210 RAG Baseline v1 上增加 Boundary Policy 的冻结记录。它用于后续回归对比，不表示 Boundary Gold 已经完成，也不表示生产就绪。

## 冻结组件

```yaml
generic_retrieval: v1
embedding: BAAI/bge-m3
reranker: BAAI/bge-reranker-v2-m3
router: rule_router_v1
fault_relation_expansion: current_v1
response_policy: boundary_policy_v1
boundary_dataset: siemens_s210_rag_boundary_eval_v1
boundary_gold_status: expert_validated
reviewer: 刘武
training_eligible: false
```

冻结期间不修改 embedding、retrieval、reranker、chunk、prompt 或既有回答合同。Boundary 专家审核只验证“允许回答、带警告、请求补充、库外拒答”的策略，不反向调整检索链路。

## 当前可验证证据

- 既有 30 条 S210 RAG 回归产物：`evaluation/quality_eval/runs/siemens_s210_rag_baseline_v1_report_2026-09-22.json`；
- 24 条 Boundary 工程草案：`evaluation/quality_eval/datasets/siemens_s210_rag_boundary_eval_v1.json`；
- 工程规则检查脚本：`evaluation/quality_eval/public_sources/evaluate_rag_boundary_policy.py`；
- 当前工程检查结果：24/24 与预期一致，但这不是专家语义验收成绩；
- 刘武审核清单：`evaluation/quality_eval/runs/siemens_s210_rag_boundary_expert_review_checklist_v1_2026-09-22.md`；
- 正式 Boundary Gold：`evaluation/quality_eval/datasets/siemens_s210_rag_boundary_expert_gold_v1.json`；
- Boundary 策略回归：`evaluation/quality_eval/runs/siemens_s210_rag_boundary_expert_gold_policy_report_v1_2026-09-22.json`。

## 进入下一阶段的门禁

刘武已完成 24 条审核，规范化文件通过 `validate_rag_boundary_expert_gold.py`；确定性 Boundary Policy 回归也已完成，Unsafe Answer Rate、False Reject Rate、Warning Precision/Recall 和 Out-of-domain Precision 均为 1.0。下一步仍需完成真实 API 回归（30 条 RAG Semantic Gold + 24 条 Boundary Gold），通过后再冻结 RAG 层并进入 Fault Relation Gold。
