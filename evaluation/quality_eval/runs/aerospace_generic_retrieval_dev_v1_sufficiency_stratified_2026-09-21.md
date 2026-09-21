# Aerospace Generic Retrieval Dev v1

本报告运行冻结的 Generic Retrieval Pipeline v1，不代表航空专家金标或最终泛化成绩。查询标签由公开样本确定性派生，错误分类状态保持 `unreviewed`。

## 总体指标

| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Candidate Union | 0.4000 | 0.4000 | 0.4000 | 0.6750 | 0.8500 | 0.4471 |
| Reranked | 0.8000 | 0.8500 | 0.8500 | 0.8500 | 0.8500 | 0.8250 |

## 按查询类型

| 类型 | Candidate R@20 | Reranked R@1 | Reranked MRR |
|---|---:|---:|---:|
| component | 0.7500 | 0.7500 | 0.7500 |
| condition | 0.5000 | 0.2500 | 0.3750 |
| identifier | 1.0000 | 1.0000 | 1.0000 |
| maintenance_action | 1.0000 | 1.0000 | 1.0000 |
| part_number | 1.0000 | 1.0000 | 1.0000 |

## 按查询充分性

| 充分性 | Candidate R@20 | Reranked R@1 | Reranked MRR |
|---|---:|---:|---:|
| insufficient | 0.5000 | 0.1667 | 0.3333 |
| partially_sufficient | 0.7000 | 0.7000 | 0.7000 |
| sufficient | 1.0000 | 1.0000 | 1.0000 |

## 边界

- `candidate_recall` 只说明正确实体是否进入候选池；不能说明查询标签是专家确认的。
- `diagnostic_hint` 只是定位线索，所有错误分类仍需人工/工程复核；本轮不自动把失败归因到 Generic Pipeline。
- 如需改变公共 Schema、Adapter Contract 或 Generic Pipeline，必须先完成错误分类并新增相应回归门禁。
