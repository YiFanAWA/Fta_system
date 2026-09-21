# Query Action Gold v2 实验矩阵

本报告冻结 Generic Retrieval v1，只比较 No Router、Rule Router v1、Rule Router v1 + Query Decision Layer。

## 主要指标

| 方案 | Action Accuracy | Candidate Recall@20 | Candidate Recall Loss | R@1 | MRR | WrongDomain@1 | False Scope@all | Scoped Candidate Miss@scoped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| No Router | 0.1139 | 0.9241 | 0.0000 | 0.5949 | 0.6567 | 0.2152 | 0.0000 | 0.0000 |
| Rule Router v1 | 0.1139 | 0.9241 | 0.0000 | 0.6329 | 0.6947 | 0.0000 | 0.0000 | 0.0877 |
| Rule Router v1 + Query Decision | 0.5190 | 0.5190 | 0.4051 | 0.3797 | 0.4097 | 0.0000 | 0.0000 | 0.0877 |

## Action 分类

Gold action：`retrieve=9`、`retrieve_with_warning=70`、`clarify=0`。

| 方案 | retrieve Precision/Recall | warning Precision/Recall | clarify Precision/Recall | 澄清数 |
|---|---:|---:|---:|---:|
| No Router | 0.1139/1.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0 |
| Rule Router v1 | 0.1139/1.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0 |
| Rule Router v1 + Query Decision | 0.5714/0.8889 | 1.0000/0.4714 | 0.0000/0.0000 | 32 |

## 解释

- `false_scope` 只统计 Router 已缩小到错误领域的情况；cross_domain 不算错误缩小。
- Query Decision Layer 的 `clarify` 会产生空检索结果，因此全量 Recall 会下降；同时报告未澄清查询的条件召回，区分“安全停下”和“检索能力下降”。
- `retrieve_with_warning` 不阻断检索，只影响回答层提示。
- 本轮没有接入生产 API/前端，也没有修改 Generic Retrieval v1、embedding 或 reranker。
