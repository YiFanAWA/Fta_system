# Domain/System Router v1

## 目标

在 Siemens S210 与 Aerospace 共用索引时，先判断查询是否包含足够明确的领域信号；有明确证据时缩小检索 scope，没有足够证据时保留跨域召回，避免错误过滤。

Router 不拥有检索排名、RRF、Top-K 或 Reranker 逻辑。它只输出：

- `selected_scope_ids`：允许检索的领域/system scope；
- `mode`：`scoped` 或 `cross_domain`；
- `confidence`：规则信号形成的可解释置信度；
- `signals` 与 `scores`：用于审计和 shadow mode。

实现：`backend-python/domain_router.py`；领域证据由 [Domain Evidence Registry v1](domain-evidence-registry-v1.md) 集中维护。

## 当前规则

每个领域由 `DomainScopeProfile` 提供：

- 领域、厂商、系统身份；
- 显式强词；
- 可选弱词；
- 领域侧 identifier 正则。

当前已确认规则优先识别：

- Siemens：Siemens、SINAMICS、S210、DRIVE-CLiQ、PROFINET、PROFIsafe、故障码和参数号；
- Aerospace：航空/航空器、FAA、SDR、JASC 及 JASC 编号。

规则没有命中或最高分与次高分不足以拉开差距时，结果为 `cross_domain`。这不是拒答，而是保留完整检索空间。注册表中的 `pending_manual_confirmation` 词不会自动参与 Router v1。

## 混合域对照结果

证据：

`evaluation/quality_eval/runs/mixed_domain_router_comparison_v1_2026-09-21.md`

同一数据、同一 BGE-M3、321 个实体、79 条查询：

| 方案 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR | WrongDomain@1 | WrongDomain@3 | WrongDomain@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No Router | 0.5949 | 0.6582 | 0.6962 | 0.8228 | 0.9241 | 0.6571 | 0.1772 | 0.3291 | 0.3797 |
| Rule Router | 0.5949 | 0.6582 | 0.6709 | 0.8101 | 0.9241 | 0.6515 | 0 | 0 | 0 |
| Oracle Scope | 0.5949 | 0.6582 | 0.6709 | 0.8101 | 0.9241 | 0.6515 | 0 | 0 | 0 |

解释：当前规则 Router 在这批查询上与 oracle scope 的候选指标一致，并把跨域污染降为 0；但 R@5、R@10 和 MRR 相比 no-router 略低。因此它是可审计的开发/Shadow 方案，不是生产默认。

## 当前边界

- 规则 Router 尚未接入 API 或前端；
- 尚未实现 learned Router；
- 当前结果不是跨域泛化结论，因为 Aerospace 查询是开发集模板派生数据；
- 生产切换前必须新增 scope 回归门禁：不能出现错误领域污染，同时不能接受关键领域内 Recall/MRR 的未解释下降；
- 低信息查询仍应保留 `cross_domain`，不能依靠词表强行猜领域。

Router v1 的首轮错误分类见 [Domain Router Error Taxonomy v1](domain-router-error-taxonomy-v1.md)。该分类只用于离线诊断：首轮 22 条 `cross_domain` 查询被标记为 A=4、B=2、C=16，未发现 `false_scoped`；A/B/C 均需要人工复核，不会自动反向修改规则。

Query Sufficiency 首轮诊断已完成，见 `evaluation/quality_eval/runs/mixed_domain_query_sufficiency_v1_2026-09-21.md`；下一步是建立人工 sufficiency Gold 并进行 clarification 对照实验，再决定是否需要调整规则、增加 system 级 scope，或引入 learned Router。之后进入 RAG 人工语义评测。
