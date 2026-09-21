# Domain Router Error Taxonomy v1

更新时间：2026-09-21
适用范围：S210 + FAA SDR 混合域 Router v1 开发/Shadow 评估

## 目的

本轮不增加 Router 规则，也不修改 Generic Retrieval Pipeline。目标是解释 Rule Router v1 为什么有 22 条查询仍保持 `cross_domain`，并区分：

- **A：可能本应 scope，但 Router 没识别到足够信号**；
- **B：确实存在领域歧义，应保持跨域或请求澄清**；
- **C：查询信息不足，应先补充设备、系统、厂商或故障码等上下文**。

分类脚本中的 cue 词表仅用于离线诊断，不能直接作为线上规则。所有逐条标签都标记为需要人工复核，不能当作专家 Gold。

## 首轮结果

输入报告：`evaluation/quality_eval/runs/mixed_domain_router_comparison_v1_2026-09-21.json`

输出报告：`evaluation/quality_eval/runs/domain_router_error_taxonomy_v1_2026-09-21.md` / `.json`

| 项目 | 数量 |
| --- | ---: |
| 总查询 | 79 |
| `scoped` | 57 |
| `cross_domain` | 22 |
| A `missing_router_signal` | 4 |
| B `domain_ambiguous` | 2 |
| C `query_insufficient` | 16 |
| `false_scoped` | 0 |

A 类当前只是 Router v2 候选，例如包含 `STO`、`CU`、`Sensor Module`、`SI Motion` 等技术信号但仍被保留为跨域的查询。B/C 类暂不应通过扩充词表强行缩小 scope。当前 22 条分类来自“基准查询领域标签 + 分析词表”的诊断审计，不能等同于人工确认的错误事实。

## 解释与边界

- `false_cross_domain_candidate` 只表示 A 类候选，不代表已经批准新增规则。
- `false_scoped=0` 表示本轮没有发现错误缩小 scope 的样本；它不构成生产门禁通过。
- Router 仍然是入口控制层，只输出 scope、模式、置信度和可审计信号；它不拥有 RRF、Top-K、Reranker 或领域专用排名逻辑。
- Generic Retrieval Pipeline、S210 生产 API、前端 UI 均未修改。
- 同一批查询在本报告生成后不得用于调词表或调参数；需要新建 Query Sufficiency 评测或新的 Router Final Test。

## 下一步

1. 对 22 条 `cross_domain` 查询补充人工标签：A、B、C，并记录标签依据。
2. 建立 Query Sufficiency 输出：`sufficient`、`partially_sufficient`、`insufficient`。
3. 比较 `No Router`、`Rule Router v1`、`Rule Router + clarification` 的 R@K、MRR、WrongDomain@K 和 abstain rate。
4. 只有 A 类经人工确认且产生可复现收益后，才考虑 Router v2；B/C 优先走跨域召回或澄清，不通过猜测解决。
