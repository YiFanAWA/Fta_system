# S210 RAG 边界与安全回答策略 v1

## 目的

本层处理“用户问题是否有足够证据由 S210 RAG 回答”的边界，不改变
Embedding、Retrieval、Reranker、Fault Relation 或前端布局。

当前 owner 是 `backend-python/response_policy.py` 的
`ResponsePolicyLayer.assess_boundary()`。

## 运行位置

```text
Query
  ↓
Rule Router / Retrieval / Reranker
  ↓
Evidence Context
  ↓
RAG Boundary Policy
  ↓
Answer 或安全拒答
```

明确的外部领域问题可以在检索前快速拒答；其余问题在候选故障和完整上下文加载后
执行边界判断。这样不会为了“信息不足”而直接损失候选召回，同时也不会为明显的
库外问题加载重型检索模型。

## 状态合同

| `knowledge_status` | 行为 |
|---|---|
| `supported` | 有 S210 标识、故障码或参数，允许正常回答 |
| `supported_with_warning` | 有技术故障描述但缺少明确身份，允许回答并提示补充 |
| `insufficient_evidence` | 信息过少，不生成确定诊断，请求补充 |
| `out_of_domain` | 明确属于当前知识库之外，不生成故障诊断 |

接口同时返回：`answer_allowed`、`confidence_level`、`warning_required`、
`need_additional_info`、`reason` 和 `missing_information`。

## 当前判定原则

- 明确 S210/Siemens/SINAMICS/DRIVE-CLiQ、故障码或参数：允许正常回答；
- 仅有“温度异常、通信失败”等技术描述：允许检索和回答，但必须降级为 warning；
- “设备坏了、报警了”等低信息问题：返回补充信息要求，不给确定故障；
- 天气、股票、航空器等明确外部领域：返回超出当前知识库范围；
- 不用单一向量相似度作为“有依据”的证明；最终回答仍必须通过 evidence citation 合同。

## 测试集与当前边界

工程测试集：
`evaluation/quality_eval/datasets/siemens_s210_rag_boundary_eval_v1.json`。

该文件当前是 24 条工程草案，不是专家金标，状态为
`engineering_draft_pending_expert_review`。规则检查报告：
`evaluation/quality_eval/runs/siemens_s210_rag_boundary_policy_v1_report_2026-09-22.json`。

在正式接入生产前，需要由领域专家审核边界样本，特别是：

- 哪些“技术描述”可以 warning 后直接回答；
- 哪些问题必须先补充故障码或设备型号；
- 哪些词确实代表 Siemens S210 领域，而不是通用工业词；
- 哪些外部领域应直接拒答。

## 验收门槛

1. 原有 30 条 S210 RAG 回归结果不下降；
2. `out_of_domain` 不调用回答模型；
3. `insufficient_evidence` 不产生确定诊断；
4. 所有正常回答仍满足 evidence citation 合同；
5. 边界测试集经专家审核后，再报告安全拒答和误拒答指标。

本阶段只完成工程边界机制和草案测试，不宣称已经完成专家语义验收。
