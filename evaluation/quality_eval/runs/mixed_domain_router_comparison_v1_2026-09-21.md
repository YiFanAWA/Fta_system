# Siemens S210 + Aerospace Domain Router Comparison v1

本报告在同一 321 个实体、79 条查询和 BGE-M3 下，对比 no-router 与可解释规则 Router；不代表生产上线。

## 路由决策

scoped：57；cross_domain：22。

## 检索指标

| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| No Router | 0.5949 | 0.6582 | 0.6962 | 0.8228 | 0.9241 | 0.6571 |
| Rule Router | 0.5949 | 0.6582 | 0.6709 | 0.8101 | 0.9241 | 0.6515 |
| Oracle Scope | 0.5949 | 0.6582 | 0.6709 | 0.8101 | 0.9241 | 0.6515 |

## 跨域污染

| 方案 | WrongDomain@1 | WrongDomain@3 | WrongDomain@5 | Purity@1 | Purity@3 | Purity@5 |
|---|---:|---:|---:|---:|---:|---:|
| No Router | 0.1772 | 0.3291 | 0.3797 | 0.8228 | 0.7975 | 0.8127 |
| Rule Router | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| Oracle Scope | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |

## 边界

- Rule Router 只在显式信号达到阈值时缩小 scope；低信息查询保持 cross_domain。
- Oracle scope 仍不是分类器，只用于测量 metadata scope 的上限。
- 本轮不修改 Generic Retrieval Pipeline，不切生产 API，不把规则写入前端。
