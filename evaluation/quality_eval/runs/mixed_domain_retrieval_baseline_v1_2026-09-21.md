# Siemens S210 + Aerospace Mixed-Domain Baseline v1

实体数：321；查询数：79；Router：`none`。本报告是无 Router 诊断，不是生产结论。

## 检索指标

| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| candidate_recall | 0.6076 | 0.6709 | 0.6962 | 0.8354 | 0.9241 | 0.6674 |
| ranked | 0.6076 | 0.6709 | 0.6962 | 0.8354 | 0.9241 | 0.6674 |

## 跨域污染

WrongDomain@K 表示 Top-K 中是否出现至少一个错误领域实体的查询比例；DomainPurity@K 表示 Top-K 中属于期望领域的实体比例。

| 阶段 | WrongDomain@1 | WrongDomain@3 | WrongDomain@5 | Purity@1 | Purity@3 | Purity@5 |
|---|---:|---:|---:|---:|---:|---:|
| candidate_recall | 0.1772 | 0.3418 | 0.3797 | 0.8228 | 0.7932 | 0.8127 |
| ranked | 0.1772 | 0.3418 | 0.3797 | 0.8228 | 0.7932 | 0.8127 |

## 解释边界

- 当前没有 Router，混合 Adapter 只存在于评测脚本中；Generic Pipeline 未添加领域分支。
- S210 查询来自冻结 Final Test v1；航空查询来自非专家模板派生 Dev v1，不能把两者合并分数当作对称领域质量。
- 若发现污染，先定位 query 信息量、Adapter 字段角色和候选池，再决定是否设计 Router；本报告不会自动触发 Router 实现。
