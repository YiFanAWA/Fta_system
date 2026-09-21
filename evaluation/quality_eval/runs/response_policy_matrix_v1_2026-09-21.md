# Response Policy v1 实验矩阵

本报告复用已生成的 Rule Router v1 检索结果，不重新运行 embedding、RRF、Router 或 Reranker。Response Policy 只控制检索后的回答方式。

## 架构合同

```text
Query -> Rule Router v1 -> Retrieval/Reranker -> Response Policy -> RAG
```

`normal` 正常回答；`warning` 继续回答但降低确定性并提示补充信息；`clarify` 可以利用检索结果组织澄清问题，但不输出确定性结论。三者均不改变候选召回。

## 检索指标保持不变

| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR | WrongDomain@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rule Router v1 | 0.6329 | 0.7215 | 0.7722 | 0.8101 | 0.9241 | 0.6947 | 0.0000 |
| Rule Router v1 + Response Policy | 0.6329 | 0.7215 | 0.7722 | 0.8101 | 0.9241 | 0.6947 | 0.0000 |

检索 parity：**通过**。所有检索指标差值均为 0。

## Response Policy 指标

| 指标 | 值 |
|---|---:|
| Policy Accuracy | 0.5190 |
| 预测 normal / warning / clarify | 14 / 33 / 32 |
| Gold normal / warning / clarify | 9 / 70 / 0 |
| 预测澄清率 | 0.4051 |

| Policy | Precision | Recall | Support |
|---|---:|---:|---:|
| normal | 0.5714 | 0.8889 | 9 |
| warning | 1.0000 | 0.4714 | 70 |
| clarify | 0.0000 | N/A | 0 |

## 解释

- 当前机器 Query Analyzer 产生的 `insufficient` 查询会预测为 `clarify`，但这只影响回答策略，不再清空检索结果。
- 当前专家 Gold 没有 `clarify` 样本，因此不能据此宣称“必须澄清后才能回答”的策略已经得到专家验证。
- `unsupported_claim_rate` 和 `citation_support_rate` 当前为 N/A；它们需要下一阶段真实生成答案后的人工语义评测，不能由检索矩阵代替。
- 本轮没有接入生产 API/前端，也没有修改 Generic Retrieval、embedding、reranker 或 Rule Router v1。
