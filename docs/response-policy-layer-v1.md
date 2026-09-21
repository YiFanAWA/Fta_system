# Response Policy Layer v1

## 当前定位

Response Policy Layer 是检索后的回答风险控制层，不是检索准入层，也不拥有领域路由、候选召回、RRF 或 Reranker。

```text
Query
  ↓
Rule Router v1
  ↓
Generic Retrieval / Reranker
  ↓
Response Policy Layer
  ↓
Evidence-grounded RAG
```

唯一 owner：`backend-python/response_policy.py`。

## 行为合同

| response_policy | 含义 | 是否允许检索 |
|---|---|---:|
| `normal` | 信息足够，正常生成有证据回答 | 是 |
| `warning` | 继续回答，但降低确定性并提示补充型号、系统、故障码或组件 | 是 |
| `clarify` | 可以利用检索结果组织澄清问题，但不输出确定性结论 | 是 |

三种策略都允许检索。`clarify` 不等于删除候选结果；它只约束回答层不得把低信息查询解释成确定诊断。

## Gold v1

来源：`evaluation/quality_eval/runs/query_sufficiency_gold_v1_LiuWu_expert_review.json`，经规范化生成：
`evaluation/quality_eval/runs/response_policy_gold_v1.json`。

当前 79 条专家审核查询的分布：

- `normal`：9 条；
- `warning`：70 条；
- `clarify`：0 条；
- `retrieval_policy=allow`：79 条。

这说明当前专家材料支持“检索后谨慎回答”，但还没有提供真正的 `clarify` 正例，不能宣称阻断式澄清已经被专家验证。

## 当前实验结果

报告：`evaluation/quality_eval/runs/response_policy_matrix_v1_2026-09-21.md`。

| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR | WrongDomain@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rule Router v1 | 0.6329 | 0.7215 | 0.7722 | 0.8101 | 0.9241 | 0.6947 | 0.0000 |
| Rule Router v1 + Response Policy | 0.6329 | 0.7215 | 0.7722 | 0.8101 | 0.9241 | 0.6947 | 0.0000 |

检索 parity 通过：Response Policy 没有改变召回或排序。

当前机器 Query Analyzer 映射出的回答策略为 `normal=14、warning=33、clarify=32`，与专家 Gold 的 `9/70/0` 仍有偏差。这是回答策略校准问题，不是检索回归；尤其 `clarify` 当前没有 Gold 正例，不能据此调整检索器。

`unsupported_claim_rate`、`citation_support_rate` 目前为 N/A。它们必须在真实 RAG 答案生成后，用独立的 20～30 条人工语义评测集确认。

## 当前边界

- Rule Router v1 保持当前候选/Shadow 基线；Expert Router v2 不晋升为生产实现。
- 不修改 Generic Retrieval、embedding、reranker、Gold 故障数据或前端/API。
- 后续结构化合同见 [Response Policy v2](response-policy-v2.md)，将策略展开为 `answer_allowed`、`confidence_level`、`need_additional_info` 和 `warning_required`。
- `query-decision-layer-v1.md` 保留为历史的前置决策实验，不作为当前检索架构。
- 下一阶段进入 [RAG Semantic Evaluation v1](rag-semantic-evaluation-v1.md)：故障识别、原因正确性、处理措施正确性、证据支持、无依据陈述和跨故障混淆。
