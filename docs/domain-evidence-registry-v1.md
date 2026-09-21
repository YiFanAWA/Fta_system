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

上一版简要填写入口见 [Domain Router / Query Sufficiency 人工确认清单 v1](../evaluation/quality_eval/runs/domain_router_manual_confirmation_checklist_v1_2026-09-21.md)；完整材料包见 [Domain Router / Query Sufficiency 完整人工审核材料包 v2](../evaluation/quality_eval/runs/domain_router_manual_review_bundle_v2_2026-09-21.md)。完整包包含原文证据、来源记录、全部 79 条查询和 22 条重点 cross-domain 查询。

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

## 刘武审核后的 Expert Router v2 输入

刘武审核后的完整输入快照为
`evaluation/quality_eval/runs/domain_router_manual_review_bundle_v2_LiuWu_reviewed_v1.json`。
基于该快照生成的实验文件为：

- `evaluation/quality_eval/runs/domain_signal_registry_v1.json`；
- `evaluation/quality_eval/runs/query_sufficiency_gold_v1.json`；
- [Router v2 Policy（实验版）](router-policy-v2.md)。

原始领域信号审核材料中的 22 条重点查询仅是第一版草案；随后刘武提供了覆盖全部 79 条查询的 [query_sufficiency_gold_v1_LiuWu_expert_review.json](../evaluation/quality_eval/runs/query_sufficiency_gold_v1_LiuWu_expert_review.json)。Expert Router v2 registry 仍只用于离线对照，`production_enabled=false`，未替换本文件中的 v1 配置。

## Expert Router v2 对照结果

三组对照报告：

`evaluation/quality_eval/runs/expert_router_v2_comparison_v1_2026-09-21.md`

| 方案 | Candidate Recall@20 | Ranked R@1 | WrongDomain@1（候选） | Clarification Precision（22 条 Gold） | 全量澄清比例 |
| --- | ---: | ---: | ---: | ---: | ---: |
| No Router | 0.9241 | 0.5949 | 0.2152 | N/A | 0.0000 |
| Rule Router v1 | 0.9241 | 0.6329 | 0 | 1.0000 | 0.4051 |
| Expert Router v2 | 0.9241 | 0.5949 | 0.2152 | 1.0000 | 0.4051 |

本结果说明：专家词表没有破坏候选召回，但在当前 79 条查询上尚未减少错误领域 Top1；不能据此直接上线 v2。Rule Router v1 的领域隔离效果更好，但其优势来自现有 identifier/领域词覆盖，仍需保持 shadow mode 并继续做查询充分性分析。全量专家 Gold 的复评见 `query_sufficiency_gold_v1_evaluation_2026-09-21.md`。
