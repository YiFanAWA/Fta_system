# Mixed-Domain Query Sufficiency v1

查询数：79。本报告只做可解释诊断，不修改 Router 或 Retrieval。

## 结果

| 指标 | 结果 |
|---|---:|
| sufficient | 14 |
| partially_sufficient | 33 |
| insufficient | 32 |
| Clarification Rate | 0.4051 |
| Abstain Accuracy | N/A（缺少人工充分性金标） |

## 边界

- 当前等级来自规则化信息量审计，不是人工标签，不代表澄清请求一定正确。
- `Clarification Rate` 是系统建议澄清的比例；`Abstain Accuracy` 必须等 Query Sufficiency Gold 建立后才能计算。
- 下一步应对 low-information 查询人工确认 `sufficient / partially_sufficient / insufficient`，再比较 No Router、Rule Router v1 和 clarification 方案。
