# Query Decision Layer v1

## 定位

Query Decision Layer 位于 Query Analyzer 与 Retrieval 之间，负责决定系统行为，不拥有 embedding、RRF、reranker 或实体检索逻辑。

```text
Query
  ↓
Domain Router v1 + Query Sufficiency Analyzer
  ↓
Query Decision Layer
  ├─ retrieve
  ├─ retrieve_with_warning
  └─ clarify
  ↓
Generic Retrieval v1
```

当前实现：`backend-python/query_decision.py`。

## 行为合同

| action | 含义 | 是否检索 |
|---|---|---:|
| `retrieve` | 信息充分且已有明确 scope，直接检索 | 是 |
| `retrieve_with_warning` | 信息不完整但仍有检索价值，检索并提示用户补充型号/故障码 | 是 |
| `clarify` | 信息不足以安全检索，先请求补充信息 | 否 |

当前策略：

- `insufficient` → `clarify`；
- `sufficient + scoped` → `retrieve`；
- 其他情况 → `retrieve_with_warning`。

该策略只在离线实验中使用，没有接入 API、前端或生产 Router。

## Action Gold v2

来源：`evaluation/quality_eval/runs/query_sufficiency_gold_v1_LiuWu_expert_review.json`。

规范化结果：`evaluation/quality_eval/runs/query_action_gold_v2.json`。

当前 79 条分布：

- `retrieve`：9 条；
- `retrieve_with_warning`：70 条；
- `clarify`：0 条。

注意：原始文件中的 `should_clarify=true` 与 `recommended_action=retrieve_with_warning` 同时存在。系统行为以 `action` 为准，`should_clarify` 只保留为专家原始元数据，不能直接当作阻断信号。

## 实验结果

报告：`evaluation/quality_eval/runs/query_action_matrix_v2_2026-09-21.md`。

| 方案 | Action Accuracy | Candidate Recall@20 | Candidate Recall Loss | R@1 | MRR | WrongDomain@1 | False Scope@all |
|---|---:|---:|---:|---:|---:|---:|---:|
| No Router | 0.1139 | 0.9241 | 0.0000 | 0.5949 | 0.6567 | 0.2152 | 0.0000 |
| Rule Router v1 | 0.1139 | 0.9241 | 0.0000 | 0.6329 | 0.6947 | 0.0000 | 0.0000 |
| Rule Router v1 + Query Decision | 0.5190 | 0.5190 | 0.4051 | 0.3797 | 0.4097 | 0.0000 | 0.0000 |

## 当前结论

1. Rule Router v1 仍然是安全基线：没有错误缩小领域，Candidate Recall@20 不下降。
2. Query Decision Layer 的方向正确，但当前 `insufficient → clarify` 规则过于激进；32 条查询被阻断，造成召回损失。
3. 不能把 `partially_sufficient` 直接映射成 `clarify`；它应默认映射为 `retrieve_with_warning`。
4. 当前 Gold 没有真正的 `clarify` 样本，不能宣称阻断澄清策略已经得到专家验证。

## 下一步边界

- 保持 Generic Retrieval v1、Rule Router v1、embedding、reranker 不变；
- 增加真实低信息查询并由专家标注 `clarify`；
- 只有 `clarify` 样本形成足够覆盖后，才评估阻断式 Query Decision；
- Query Decision Layer 暂不接生产 API/前端。
