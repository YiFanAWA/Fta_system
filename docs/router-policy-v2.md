# Domain Router v2 Policy（专家审核派生，实验版）

> 本策略仅用于 No Router / Rule Router v1 / Expert Router v2 对比，不直接替换生产 Router。
> 只有刘武在审核文件中明确确认的信号和查询标签进入本版本；Router 规则仍只用于离线实验。

## 输入依据

- 审核文件：`evaluation\quality_eval\runs\domain_router_manual_review_bundle_v2_LiuWu_reviewed_v1.json`。
- 领域信号审核：22 个候选信号，其中 16 个进入 high/medium，6 个明确排除；
- 查询 Gold：[query_sufficiency_gold_v1_LiuWu_expert_review.json](../evaluation/quality_eval/runs/query_sufficiency_gold_v1_LiuWu_expert_review.json)，共 79 条。
- 审核者：刘武。
- 证据要求：每条 Gold 查询保留相关故障实体的原始记录证据；领域词保留原文出现证据或明确标记无直接证据。

## 信号分类

| 信号级别 | 路由含义 | 约束 |
|---|---|---|
| high_signal | 强领域/系统信号 | 单一领域命中且无冲突时可缩小 scope |
| medium_signal | 条件领域信号 | 单独出现不能缩小 scope，需同域 high signal 或明确系统/标识符支持 |
| excluded_signal | 专家明确不加入 | 不参与 Router 打分 |

## 路由决策

1. 先解析显式故障码、参数、JASC/部件号等 identifier；identifier 命中某一 scope 时，可作为强证据。
2. 统计每个 scope 的 high/medium 信号；只命中一个 scope 的 high signal，且没有跨域冲突时，输出 `scope_<domain>`。
3. 只有 medium signal 时，保持 `cross_domain`，除非同时存在同域 high signal 或明确 system/manufacturer/identifier。
4. 多个 scope 同时出现 high signal 时，输出 `cross_domain`，不得猜测。
5. Router 不修改检索实体、Gold、embedding、RRF、reranker 或前端/API。

## Query Sufficiency（仅作回答策略输入）

- `sufficient`：可以直接检索。
- `partially_sufficient`：允许检索，回答使用 `warning` 策略。
- `insufficient`：允许检索，但回答使用 `clarify` 策略，不输出确定性结论。
- `cannot_determine`：保持跨域并记录无法判断原因。
- `clarification` 只控制回答层；不把候选结果从 Retrieval 中删除。

## 三组实验定义

| 方案 | 领域处理 | 澄清判断 |
|---|---|---|
| No Router | 321 个实体混合检索 | 不主动澄清 |
| Rule Router v1 | 使用当前 backend v1 已确认注册表 | 使用当前机器 sufficiency evaluator |
| Expert Router v2 | 使用本策略派生 registry；未命中强条件时保持 `cross_domain` | 使用同一 sufficiency evaluator；Gold 仅用于评估 |
| Sufficiency + Router（历史） | Expert Router v2 + 当前机器 sufficiency gate | 机器判断为 insufficient 时阻断检索；仅用于解释召回损失 |

## 验收指标

- `WrongDomain@1`：Top1 是否出现错误领域实体。
- `Candidate Recall@20`：正确实体是否进入 Top20 候选池。
- `Clarification Precision`：在 79 条专家 Gold 上，要求澄清的查询中实际应澄清的比例。
- `Clarification Rate`：所有查询中系统要求补充信息的比例。
- 同时保留 `R@1/R@3/R@5/R@10/R@20/MRR`，防止 Router 降低召回。

## 全量专家 Gold 评估结果

报告：`evaluation/quality_eval/runs/query_sufficiency_gold_v1_evaluation_2026-09-21.md`

| 方案 | Domain Accuracy | Sufficiency Accuracy | Clarification Precision | Clarification Recall | 澄清比例 | Candidate Recall@20 | WrongDomain@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rule Router v1 | 0.7215 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.9241 | 0.0000 |
| Expert Router v2 | 0.1392 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.9241 | 0.2152 |
| Sufficiency + Router | 0.1392 | 0.5190 | 0.9688 | 0.4429 | 0.4051 | 0.5190 | 0.1646 |

结论：Expert Router v2 尚未证明优于 Rule Router v1；历史 Sufficiency + Router 将 32 条查询置为澄清并阻断检索，Candidate Recall@20 降至 0.5190。当前不再采用这种前置阻断；回答风险控制改由 Response Policy Layer 承担。

## 禁止事项

- 不把这份 registry 自动复制到 `backend-python/config`。
- 不把任何没有明确专家标签的查询补成 Gold；当前新版查询 Gold 已覆盖 79 条。
- 不用实验结果反向修改 Gold。
- 不因 Router 指标变化直接修改 Generic Retrieval Pipeline。
