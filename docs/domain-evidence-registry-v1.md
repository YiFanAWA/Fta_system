# Domain Evidence Registry v1

更新时间：2026-09-21

## 目的

将领域识别证据集中放在 `backend-python/config/domain_evidence_registry_v1.json`，避免把领域词散落在 Router、评测脚本或前端代码中。

注册表维护：

- `high_signal`：达到 Router scope 门槛的强证据；
- `medium_signal`：只能作为弱证据使用；
- `identifier_patterns`：领域/系统代码或标识符的正则；
- `pending_manual_confirmation`：候选词，不会被线上或 Shadow Router 默认消费。

## 当前状态

当前注册表状态为 `pending_manual_confirmation_for_a_signals`，Router 默认只加载 `confirmed` 项。

待人工确认的 A 类候选词：

- Siemens S210：`STO`、`SI Motion`、`CU`、`Sensor module`；
- 航空领域候选：`ATA`、`LRU`、`flight`、`aircraft`。

本轮不把这些词视为已确认，不修改 Router v1 的决策边界。确认后只需更新注册表的状态，再单独生成 Router v2 对照报告。

## 代码边界

- `domain_evidence_registry.py` 是注册表加载与校验 owner；
- `domain_router.py` 仍然只负责通用路由决策，不拥有领域词表；
- `run_mixed_domain_router_comparison.py` 已改为从注册表加载已确认 profile；
- `include_pending=True` 只允许离线审查测试使用，不能作为生产/Shadow 默认配置。

注册表加载的确定性验证表明：使用已确认词生成的 Router 决策与原 Router v1 逐条一致，仍为 57 条 `scoped`、22 条 `cross_domain`。
