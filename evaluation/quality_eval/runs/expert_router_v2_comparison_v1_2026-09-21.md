# No Router / Rule Router v1 / Expert Router v2 对比

本报告只验证审核派生的 Router v2，不代表生产切换。Generic Retrieval Pipeline 未修改。

## 检索指标

| 方案 | Candidate Recall@20 | Ranked R@1 | Ranked R@3 | Ranked R@5 | Ranked R@10 | MRR | WrongDomain@1（候选） |
|---|---:|---:|---:|---:|---:|---:|---:|
| No Router | 0.9241 | 0.5949 | 0.6582 | 0.6835 | 0.8481 | 0.6567 | 0.2152 |
| Rule Router v1 | 0.9241 | 0.6329 | 0.7215 | 0.7722 | 0.8101 | 0.6947 | 0.0000 |
| Expert Router v2 | 0.9241 | 0.5949 | 0.6582 | 0.6835 | 0.8481 | 0.6567 | 0.2152 |

## 澄清行为

| 方案 | 专家 Gold 数 | Gold 中应澄清 | Clarification Precision | Clarification Recall | 全量澄清比例 |
|---|---:|---:|---:|---:|---:|
| No Router | 22 | 19 | N/A | 0.0000 | 0.0000 |
| Rule Router v1 | 22 | 19 | 1.0000 | 0.7368 | 0.4051 |
| Expert Router v2 | 22 | 19 | 1.0000 | 0.7368 | 0.4051 |

## 口径与限制

- Candidate Recall@20 看正确实体是否进入候选池；Ranked 指标看最终排序。
- Clarification Precision/Recall 只在刘武明确审核的 22 条查询上计算；57 条未审核查询不参与 Gold 准确率。
- 全量 79 条的澄清比例是系统行为统计，不能解释成“需要补充信息的真实比例”。
- Expert Router v2 registry 为实验文件，未写入 `backend-python/config`，未接生产 API/前端。

## 逐条结果

结果明细见同名 JSON 的 `queries` 字段，包括每个方案的路由、sufficiency、候选池、排名和跨域污染。
