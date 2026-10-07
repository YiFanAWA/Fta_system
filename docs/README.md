# 项目内部真源索引

更新时间：2026-10-07  
适用范围：FTA System 当前代码、架构边界、验收状态和阶段记录。

本文件是内部工程文档入口，不是产品介绍，也不代替源码或测试。当前仓库已采用 `docs/` 作为工程文档目录；本项目以此处建立过渡期真源索引，不另建第二套 `dev-docs/`。

## 冲突时的事实优先级

1. 当前源码、合同/schema、测试、脚本、运行结果和真实 API 行为；
2. 仓库根目录 `AGENTS.md` 与其他项目级规则；本次审计发现根目录已有 `AGENTS.md`，但当前仓库治理检查要求的若干规范片段尚未满足；
3. 本索引及其链接的当前架构、状态和验收文档；
4. 当前有效的专项合同、冻结说明和审核材料；
5. 历史报告、旧版本、聊天记录。历史材料只说明当时状态，不覆盖当前实现。

若运行产物、文档和源码不一致，先以源码/测试/当前实际运行行为为准，并在本索引所指向的状态审计中记下差异；不得把历史指标描述成当前 API 的实时成绩。

## 当前真源

| 文档 | 职责 |
| --- | --- |
| [当前状态审计](current-state-audit.md) | 记录已实现、已接线、离线实验、未验收和明确禁止推断的事项 |
| [架构与模块边界](architecture.md) | 说明运行路径、唯一 owner、模块调用关系及生产/Preview 边界 |
| [验收与验证清单](acceptance.md) | 给出可重复的本地命令、已执行结果和阶段门禁 |
| [项目模块结构 v2](project-structure-v2.md) | 目录职责和包结构入口 |
| [抽取—审核—放行—建树工作流](extraction-review-build-workflow.md) | 正式持久化工作流合同及边界 |
| [证据约束候选 FTA v1](candidate-fta-generation-v1.md) | 递归候选树、证据/逻辑门策略、Preview 实验与剩余门禁 |
| [FTA 可靠性与验证补强计划 v1](fta-validation-reliability-plan-v1.md) | 2026-10-07 当前完成度与P1～P7路线：真实边界复验、原文语义回归、来源隔离Gold、独立Final、结构验收、Shadow、定量FTA；早期过程标为历史 |
| [FTA baseline manifest v52](../evaluation/quality_eval/fta_baseline_manifest_v52.json) | 当前活动研究基线；登记后端内部 occurrence-locator overlay 合同与离线回归。无新模型调用；F30021 v5原始运行仍blocked且未回写；未改公开API、数据库、Gold或readiness |
| [FTA baseline manifest v51](../evaluation/quality_eval/fta_baseline_manifest_v51.json) | 历史快照：定位overlay内部接线前的状态；登记 F30021 cause-disposition v5 的单次真实来源运行及历史定位审核离线对账；v50保留对账前状态 |
| [F30021 重复证据定位离线对账 v1](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.md) · [JSON](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.json) | 核验既有 AI 定位选择与来源唯一 scope/偏移一致；不是真人签署或 Gold，不改写 v5 原始运行；C04 仍 unresolved，整树仍 blocked |
| [FTA baseline manifest v50](../evaluation/quality_eval/fta_baseline_manifest_v50.json) | 历史快照：记录 F30021 定位来源/范围对账前的当前 v5 真实来源开发运行及阻断状态；保留原清单 |
| [P2真实来源开发审计 v2](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.md) · [JSON](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.json) | F30021 当前版本单例：原因分类、事件身份、层级、子项集合与门证据逐项审计；AI工程审计而非真人专家审核、非Gold/准确率结论 |
| [P2真实来源开发合同审计 v1](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.md) · [JSON](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.json) | 六个真实来源开发案例的离线合同/历史运行审计；不代表当前模型运行或模型准确率 |
| [FTA baseline manifest v49](../evaluation/quality_eval/fta_baseline_manifest_v49.json) | 历史快照：记录 F30021 当前版本真实来源运行前的 P2合同/历史案例审计状态；保留不可变哈希 |
| [FTA baseline manifest v48](../evaluation/quality_eval/fta_baseline_manifest_v48.json) | 历史快照：记录观察共现边界单次在线开发验证（单个合成非Gold样例）、证据核验与P1窄范围通过；readiness仍false；v47保留固定哈希 |
| [FTA baseline manifest v47](../evaluation/quality_eval/fta_baseline_manifest_v47.json) | 历史快照：登记观察专用runner单次请求预算门禁及离线测试/preflight；当时尚无新模型语义验证；readiness仍false；v46保留固定哈希 |
| [FTA baseline manifest v46](../evaluation/quality_eval/fta_baseline_manifest_v46.json) | 历史快照：固定当前完成度与下一阶段计划，观察runner预算上界仍为3；未调用模型；readiness仍false；v45保留固定哈希 |
| [FTA baseline manifest v45](../evaluation/quality_eval/fta_baseline_manifest_v45.json) | 历史快照：具名因果Gold、AI全量审核、事件scope、门节点与provisional视图分账；64项离线回归、357项工件校验，未做新模型语义验证 |
| [FTA baseline manifest v44](../evaluation/quality_eval/fta_baseline_manifest_v44.json) | 历史快照：记录 detached-observation 窄修正及保存响应离线重放；不包含 2026-10-07 审核台账对账，v45 起为当前状态 |
| [FTA baseline manifest v42](../evaluation/quality_eval/fta_baseline_manifest_v42.json) | 历史快照：SMOKE-001…004 符合隔离的非 Gold 政策预期；SMOKE-005 门型为预期 `unknown`，但单子项 scope 结构阻断，整体 `requires_review`；5 条均为合成观察，不是专家 Gold、准确率或泛化证据 |
| [事件范围树语义审核规则 v1](../evaluation/quality_eval/fta_event_scope_semantic_review_policy_v1.md) · [回归案例 v1](../evaluation/quality_eval/datasets/fta_event_scope_semantic_review_cases_v1.json) | 直接 OR/AND 候选需有同一 scope 的证据；共现不足以推 AND；共享事件身份与复合节点边界人工复核；案例不是 Gold 或准确率样本 |
| [事件范围树层级合同](../evaluation/quality_eval/event_scope_tree_contract.py) · [prompt v6](../evaluation/quality_eval/event_scope_tree_prompt_v6.py) · [prompt v7](../evaluation/quality_eval/event_scope_tree_prompt_v7.py) · [prompt v8 离线候选](../evaluation/quality_eval/event_scope_tree_prompt_v8.py) · [v6 单次请求器](../evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py) | v8 按完整语义判断逻辑门并要求关系证据；独立 smoke runner 的 SMOKE-001…005 均已分别单次授权运行、各零重试；详细输出与局部结构评估见下方各自记录。v6 请求器授权已使用，任何新在线运行均须针对该次请求重新授权 |
| [prompt v8 非 Gold 回归案例](../evaluation/quality_eval/datasets/fta_event_scope_prompt_v8_regression_cases_v1.json) · [离线测试](../evaluation/quality_eval/test_event_scope_tree_prompt_v8.py) | 覆盖无显式运算符的语义 OR/AND、原因列表/事件共现反例、scope 外的字面 or，以及 Figure 7 S1 原文；测试只校验离线策略与输入隔离，不代表模型准确率 |
| [语义 smoke 输入](../evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_inputs_v1.json) · [分离的预期标签](../evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json) · [单次运行器](../evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py) | 5 条合成政策样例：隐含 OR、隐含 AND、原因列表、事件共现、无关词面 OR。运行器不读取参考文件；预期标签不是专家 Gold，样例不是来源语料，不能报告准确率或泛化 |
| [SMOKE-001 原始运行](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29.json) · [机械评估](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29_assessment.json) · [离线预期对照](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-001_v1_2026-09-29_offline_comparison.json) | 单次请求、零重试；输出 OR，与手写非 Gold 政策预期一致，5/5 证据位置有效。没有真人专家语义验收，不构成模型准确率、校准或真实来源泛化成绩 |
| [SMOKE-002 原始运行](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29.json) · [机械评估](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29_assessment.json) · [离线预期对照](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-002_v1_2026-09-29_offline_comparison.json) | 单次请求、零重试；无显式 AND 字样仍输出 AND，与手写非 Gold 政策预期一致，5/5 证据位置有效。只属合成单例定性观察 |
| [SMOKE-003 原始运行](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29.json) · [机械评估](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_assessment.json) · [v1 比较诊断](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_offline_comparison.json) · [门型专属 v2 对照](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-003_v1_2026-09-29_offline_comparison_v2.json) | 单次请求、零重试；原因列表输出 `unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。v1 比较器对 unknown 错误要求直接逻辑引文；v2 按 prompt 合同校验 unknown。仍是合成非 Gold 定性观察 |
| [SMOKE-004 原始运行](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29.json) · [机械评估](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29_assessment.json) · [尝试收据](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29.attempt.json) · [v2 离线对照](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-004_v1_2026-09-29_offline_comparison_v2.json) | 单次请求、零重试；事件共现但原文明确未判定共同必要/单独充分，模型输出 `unknown`；结构有效、4/4 引文位置有效。合成非 Gold 定性观察，不代表语义准确率 |
| [SMOKE-005 原始运行](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29.json) · [机械评估](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29_assessment.json) · [尝试收据](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29.attempt.json) · [v2 离线对照](../evaluation/quality_eval/runs/fta_event_scope_semantic_smoke_smoke-005_v1_2026-09-29_offline_comparison_v2.json) | 单次请求、零重试；无关的显示颜色短语含 `or`，模型未将其用于故障门，输出预期 `unknown`；但仅生成一个 child，树结构合同阻断，整体需复核；3/3 引文位置有效。 |
| [FTA smoke 比较器 v2](../evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py) · [测试](../evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py) | 已知 AND/OR 必须绑定直接逻辑引文；unknown 必须无逻辑引文且提供允许的 `unknown_reason`。此为离线评估器规则，不修改原始模型输出、输入或参考标签 |
| [事件范围输入包 Schema](../evaluation/quality_eval/schemas/fta_event_scope_input_packet_v1.schema.json) · [参考 Gold Schema](../evaluation/quality_eval/schemas/fta_event_scope_reference_gold_v1.schema.json) · [合同校验器](../evaluation/quality_eval/fta_event_scope_packet_contract.py) | 输入只含一个顶事件及有页码定位的原文；图示参考门型与原文直接授权门型分开，模型投影不含 Gold |
| [NASA 电池模块 Figure 7 Dev 输入包](../evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json) · [独立参考图](../evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json) · [AI 角色审核](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_ai_role_review_v1_2026-09-29.json) · [来源筛查](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29.json) | 1 个已见开发样例；模型输入与图/Gate 标签分离；图示为 OR/AND/AND，文本授权为 OR/AND/unknown（第三门因精确子项范围不明而弃判）；非真人专家 Gold、无模型效果成绩、不可作 Final |
| [Figure 7 v1 单次尝试](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.md) · [v2 重跑评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.md) | 两次请求均重试 0 次；v1 用满 3000 tokens，v2 用满 8192 tokens 并启用 JSON mode，均以 `finish_reason=length` 结束且正文为空；未比较门型，不构成准确率或泛化结果 |
| [Figure 7 v3 受控请求器](../evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py) · [原始运行](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v3_2026-09-29.json) · [结构/证据评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v3_2026-09-29.json) | 单次 API 对照已完成、零重试；JSON 有效、8/8 引文逐字匹配输入原文；见下方定性对照，不宣称统计准确率 |
| [Figure 7 v3 定性对照报告](../evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md) · [JSON](../evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json) | 顶事件文字与根 OR 标签对齐，但复合分支结构、次生爆炸 AND 作用域和节点层级存在错误；仅为已见 Dev 单样例的 AI 工程定性分析，参考标注非人类专家 Gold |
| [Figure 7 v4 原始响应](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json) · [合同评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json) · [尝试收据](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.attempt.json) | 一次已授权请求、零重试；JSON 解析成功，层级 blocker 1 个（S2 单子项），引文定位 9/9；所有门为 `unknown` |
| [Figure 7 v4 定性对照报告](../evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.md) · [JSON](../evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.json) | seen-Dev 单样例；AI 角色文本参考非真人专家 Gold；不计算准确率/校准，不接受为 FTA Preview 树 |
| [Figure 7 v5 原始响应](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.json) · [合同评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v5_2026-09-29.json) · [尝试收据](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v5_2026-09-29.attempt.json) · [定性复核](../evaluation/quality_eval/runs/fta_event_scope_model_run_v5_dev_comparison_2026-09-29.md) | 1 次授权请求、0 重试；JSON 有效、15/15 引文位置有效；整树 blocked：同一输出节点有多个 scope、S2 只有一个 child、S4 缺 `unknown_reason`；不计算准确率/门型成绩 |
| [Figure 7 v6 原始响应](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json) · [assessment](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v6_2026-09-29.json) · [attempt receipt](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.attempt.json) · [定性复核](../evaluation/quality_eval/runs/fta_event_scope_model_run_v6_dev_comparison_2026-09-29.md) | 1 次授权请求、0 重试；7 节点/3 scopes，结构合同通过、10/10 引文位置有效；三个门均 unknown。显式替代连接词未绑定为门证据，重复事件身份及复合节点粒度仍需审查；不是 Gold 或语义验收 |
| [FTA 来源筛查 v1：NASA XVS](../evaluation/quality_eval/runs/fta_event_scope_xvs_source_screen_v1_2026-09-29.json) | 已扫描40页文本、查看8张 Appendix D 树图并记录权利声明；来源族已见，仅可作为 Dev/弃判边界候选，不可作盲测 Final；1998 前身及相关 XVS 文档的语义重叠仍未完成核对 |
| [FTA 来源元数据线索 v1](../evaluation/quality_eval/runs/fta_event_scope_source_leads_v1_2026-09-29.json) | v18 历史快照中的来源线索；当时未下载 PDF，当前状态以 v19 来源筛查记录为准 |
| [独立 Final 来源筛选 v1](../evaluation/quality_eval/runs/fta_independent_final_source_screen_v1_2026-09-28.json) | 记录 NASA/FAA 公共整本文档的可用性、排除项、SHA-256 与当前单条 FaultRecord 服务的合同差异；不是数据集、Gold 或模型成绩 |
| [FTA 范围 readiness 评估 v1](../evaluation/quality_eval/runs/fta_scoped_readiness_assessment_v1_2026-09-28.json) | 仅评估 v15 已见合同/边界回归与公开图示开发集；明确范围、来源 SHA、排除集、证据和阻塞项，不修改单棵 Preview 或全局就绪状态 |
| [FTA 建树评测配置锁 v1](../evaluation/quality_eval/fta_generation_eval_lock_v1.json) | 仍表示完整 raw-FaultRecord 多阶段 Candidate FTA runner 尚未运行；它不覆盖此次独立 event-scope 单次调用。DeepSeek 别名不保证权重不可变 |
| [S210 AI 授权审核进度](siemens-s210-ai-authorized-review-v1.md) | AI 角色审核的来源、范围、统计和非专家声明 |
| [S210 RAG Baseline v1.1](rag-baseline-v1.1.md) | RAG/边界策略冻结与既有回归证据 |
| [Generic Retrieval Pipeline v1 冻结](retrieval-platform-v1-freeze.md) | 通用 schema、adapter、检索管线设计与生产切换边界 |
| [Domain Router v1](domain-router-v1.md) | 可解释路由规则、离线结果和未接线状态 |
| [数据集状态注册表 v1](dataset-registry.md) | 数据集标签状态与数据库导入事实的分层口径 |
| [已知问题](known-issues.md) | 已知限制和当前风险入口 |

RAG、Router、证据和 FTA 的专项评测集及运行文件位于 `evaluation/quality_eval/`，其 `README.md`、manifest 和相应报告是数据与单次实验的局部真源。历史版本不得覆盖当前报告。

## 当前范围声明

- 现有抽取/审核/放行/建树 API 与 AI 授权因果审核 API 属于已接线的后端流程；它们与递归候选 FTA Preview 是不同合同。
- Generic Retrieval、Rule Router 和 Aerospace Adapter 有独立模块/离线评测，但不能据此声称已切入当前 S210 在线 API。
- 递归候选 FTA 目前有合同、服务和离线测试；截至本索引日期，`api_server.py` 没有候选 FTA API 路由，也没有正式 Gold/数据库写入。结果仍是 Preview。
- AI 角色审核不是具名真人专家签署。模型自报门置信度没有校准，不能用于生产接受 AND/OR。
- `fta_ready=false`、`production_ready=false` 必须保持，直到相应证据和门禁真实完成。

## 文档维护

改变 API 行为、模块 owner、数据合同、运行面或阶段门禁时，同步更新本索引和对应专项文档。已过期材料应标注历史/归档，不要留作当前承诺。
