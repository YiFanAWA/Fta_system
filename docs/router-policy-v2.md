# Domain Router v2 Policy（专家审核派生，实验版）

> 本策略仅用于 No Router / Rule Router v1 / Expert Router v2 对比，不直接替换生产 Router。
> 只有刘武在审核文件中明确确认的信号和查询标签进入本版本；未审核查询不作为 Gold。

## 输入依据

- 审核文件：`evaluation\quality_eval\runs\domain_router_manual_review_bundle_v2_LiuWu_reviewed_v1.json`。
- 审核信号：16 个。
- 查询 Gold：22 / 79 条，覆盖率 `0.2785`。
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

## Query Sufficiency

- `sufficient`：可以直接检索。
- `partially_sufficient`：可以谨慎检索，但是否先澄清由专家 Gold 的 `gold_action` 决定。
- `insufficient`：原则上输出 `clarify_first`，不强行确定领域。
- `cannot_determine`：保持跨域并记录无法判断原因。
- `clarification precision` 只在专家明确标注的查询 Gold 子集上计算；全量查询的 clarification rate 只是行为统计，不是准确率。

## 三组实验定义

| 方案 | 领域处理 | 澄清判断 |
|---|---|---|
| No Router | 321 个实体混合检索 | 不主动澄清 |
| Rule Router v1 | 使用当前 backend v1 已确认注册表 | 使用当前机器 sufficiency evaluator |
| Expert Router v2 | 使用本策略派生 registry；未命中强条件时保持 cross_domain | 使用同一 sufficiency evaluator；Gold 仅用于评估 |

## 验收指标

- `WrongDomain@1`：Top1 是否出现错误领域实体。
- `Candidate Recall@20`：正确实体是否进入 Top20 候选池。
- `Clarification Precision`：在专家 Gold 子集上，要求澄清的查询中实际应澄清的比例。
- `Clarification Rate`：所有查询中系统要求补充信息的比例。
- 同时保留 `R@1/R@3/R@5/R@10/R@20/MRR`，防止 Router 降低召回。

## 禁止事项

- 不把这份 registry 自动复制到 `backend-python/config`。
- 不把 57 条未审核查询补成 Gold。
- 不用实验结果反向修改 Gold。
- 不因 Router 指标变化直接修改 Generic Retrieval Pipeline。
