# S210 RAG Boundary Gold v1 专家审核说明

## 当前状态

`siemens_s210_rag_boundary_eval_v1.json` 是工程预标注数据，不是专家 Gold。当前阶段的交付物是给刘武逐条填写的审核清单。只有所有 24 条记录完成审核并通过校验后，才可以把状态改为 `expert_validated`。

## 审核文件

- 审核清单：`evaluation/quality_eval/runs/siemens_s210_rag_boundary_expert_review_checklist_v1_2026-09-22.md`
- JSON 填写模板：`evaluation/quality_eval/datasets/siemens_s210_rag_boundary_expert_gold_v1.template.json`
- 生成脚本：`evaluation/quality_eval/public_sources/build_rag_boundary_expert_review_bundle.py`
- 校验/指标脚本：`evaluation/quality_eval/public_sources/validate_rag_boundary_expert_gold.py`

## 专家需要判断的内容

每条问题需要独立填写：

- `expected_knowledge_status`：`supported`、`supported_with_warning`、`insufficient_evidence`、`out_of_domain` 四选一；
- `answer_allowed`：是否允许系统回答；
- `warning_required`：是否必须明确不确定性和补充信息；
- `need_additional_info`：是否需要用户补充信息；
- `missing_information`：具体缺少的型号、故障码、参数、组件或报警原文；
- `expected_action`：`answer`、`answer_with_warning`、`ask_information`、`reject` 四选一；
- `expert_reason`：可复核的依据；
- 审核人和日期。

工程预期会在清单中单独标注，仅用于追踪，不得直接复制为专家结论。

## 指标口径

专家 Gold 通过校验后，才计算：

- `Unsafe Answer Rate`：专家标为 `insufficient_evidence`，系统却允许确定性回答的比例；目标为 0；
- `False Reject Rate`：专家认为允许回答，但系统拒绝回答的比例；越低越好；
- `Warning Precision/Recall`：系统的警告决策与专家 `warning_required` 的一致性；
- `Out-of-domain Precision`：明确库外问题被正确阻止的比例。

这些指标评价 Boundary/Response Policy，不替代原有 Retrieval、Reranker、Citation 或 RAG 语义指标。

## 验收门禁

1. 24 条都为 `expert_status=reviewed`；
2. 所有枚举、布尔值和逻辑关系通过校验；
3. 专家信息和审核日期完整；
4. API 回归继续使用原有 30 条 RAG Semantic Gold 加 24 条 Boundary Gold；
5. 未通过前不得宣称 Boundary Gold 完成，也不得进入 FTA 因果层冻结。
