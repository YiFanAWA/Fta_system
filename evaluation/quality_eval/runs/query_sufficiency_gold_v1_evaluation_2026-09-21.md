# Query Sufficiency Gold v1 专家评估

本报告使用刘武审核的 79 条查询 Gold，比较 Rule Router v1、Expert Router v2 和 Sufficiency + Router。报告不代表生产切换。

## Gold 分布

领域：`{'aerospace': 40, 'industrial_drive': 39}`；充分性：`{'partially_sufficient': 70, 'sufficient': 9}`；应澄清：`{'False': 9, 'True': 70}`。

## 主要指标

| 方案 | Domain Accuracy | Sufficiency Accuracy | Clarification Precision | Clarification Recall | 澄清比例 | Candidate Recall@20 | Ranked R@1 | WrongDomain@1（候选） |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Rule Router v1 | 0.7215 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.9241 | 0.6329 | 0.0000 |
| Expert Router v2 | 0.1392 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.9241 | 0.5949 | 0.2152 |
| Sufficiency + Router | 0.1392 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.5190 | 0.3544 | 0.1646 |

## 澄清门对检索的影响

| 方案 | 澄清数 | 全量 Candidate Recall@20 | 未澄清查询 Candidate Recall@20 | 全量 Ranked R@1 | 未澄清查询 Ranked R@1 |
|---|---:|---:|---:|---:|---:|
| Rule Router v1 | 0 | 0.9241 | 0.9241 | 0.6329 | 0.6329 |
| Expert Router v2 | 0 | 0.9241 | 0.9241 | 0.5949 | 0.5949 |
| Sufficiency + Router | 32 | 0.5190 | 0.8723 | 0.3544 | 0.5957 |

## 解释边界

- Domain Accuracy 将 `cross_domain` 视为未提交具体领域，因此不会算作命中单领域 Gold。
- Sufficiency + Router 使用机器 sufficiency gate，不把专家 Gold 直接写成运行时规则，避免评测泄漏。
- Clarification 指标现在覆盖 79 条专家 Gold；与上一份 22 条 Gold 的结果不可直接混比。
- WrongDomain@1 与其他检索明细保留在输入 comparison JSON 的逐查询结果中；本报告重点新增领域、充分性和澄清指标。
