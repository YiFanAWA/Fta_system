# 真实来源开发案例：合同与历史运行语义审计 v1

日期：2026-10-07  
审计性质：只读工程审计，不是专家签署或 Gold 评测  
模型请求：0；未读取参考 Gold 作为模型输入；未改 Gold、数据库、生产 API 或 readiness。

## 结论

计划 P2 的“输入/输出合同审计”和指定历史开发案例逐项检查已完成。**P2 整体未完成**：五条 SINAMICS 原文运行使用 cause-disposition v2/v4，而当前服务提示版本是 v5；NASA Figure 7 是独立 event-scope v6 runner，也不是当前 v8 真实来源运行。因此旧结果只能作为历史缺陷/回归依据，不能证明当前提示或模型行为已经修复缺陷。

本轮没有关闭任何模型语义缺陷，也没有产生准确率结论。要验证 v5 对真实文本是否改进，需要针对具体样本单独授权新模型请求；本轮未调用模型。

## 当前合同核对

- `CauseDispositionService` 当前提示版本为 `fta-cause-disposition-v5`。它要求逐条处置抽取原因、区分独立因果条件与顶事件摘要/诊断映射/故障值映射，并要求唯一原文证据；歧义时 `unresolved`。
- `CandidateFtaExtractionService` 把候选节点、局部 scope、因果边和门型分开处理。完整单子项 scope 可为 `not_applicable`；多子项若置信策略不可用，宿主保持 `unknown`，不会将模型自报门概率当校准概率。
- 证据位置有效与证据语义支持是两个不同检查。精确 offset 只能证明文本定位，不能单独证明事件身份、因果方向、子项完整性或 AND/OR。
- NASA Figure 7 的 event-scope runner 与逐故障 CauseDisposition/CandidateFtaApplicationService 是不同运行面，不能混为同一次验证。

## 逐案例结论

| 案例 | 原因分类 | 事件身份与层级 | 子项集合 | 门证据 | 当前结论 |
| --- | --- | --- | --- | --- | --- |
| F01681 | v4 把 1 条顶事件摘要和 15 条诊断/故障值映射留在 `relation_only`；未运行树阶段 | 无候选事件树，身份/层级未测 | `xxxx=9507` 的 Cause/Fault value/Remedy 边界仍未解决 | 未测 | 旧版本只支持原因处置观察；不能证明 v5 |
| F30027 | v2 把 9 条原因全部作为事件候选，需 v5 复核角色边界 | 局部 either/or 保留为一个组节点及两个叶子，未升成外层兄弟项 | 旧输出为外层 9 项和内层 2 项两个 scope，均声称完整 | 原文有 either/or；两处多子项门因置信策略缺失仍为 `unknown` | 结构值得复测；旧标签不可作为当前验收 |
| F30021 | v2 产生 4 个候选原因；其中一项证据缺失 | 4 子项枚举；顶事件引文及一项原因引文有重复/定位风险 | 旧输出列 4 子项，但完整性未独立确认 | 门保持 `unknown`，证据问题使树 `blocked` | 保持阻断；AI 定位说明没有回写旧树，也不能替代新运行 |
| F06000 | v2 将 11 项都放为候选；cause 0 与顶事件可能重叠 | 15 节点；外层原因组与内层 either/or 分开，但组节点可能只是摘要而非独立事件 | 旧输出的 10 子项外层和 2 子项内层标为完整；语义集合/身份仍待复核 | 来源含 one-of/either-or；多子项门仍 `unknown` | 引文 21/21 精确唯一不等于语义通过；需 v5 重跑 |
| F35400 | v2 保留两条阈值条件 | 一个顶事件、两个不同条件子项，无嵌套层级 | 原文列出两个条件并称至少一个成立；旧输出标完整 | 原文明确 at-least-one/or；当前宿主因没有置信策略仍置 `unknown` | 历史上最清晰的替代路径正例；不是 v5 或校准结果 |
| NASA Figure 7 | 不属于当前 CauseDisposition 管线 | 7 节点/3 scope 结构合同通过，但 E2/E4 重复概念，E5 过度复合，E6/E7 粒度偏粗 | 结构有效不能代替子项语义/图示映射验收 | S1 有 `or`、S3 有 `and`，但 v6 缺少绑定逻辑证据；S2 的 unknown 可由纯文本输入解释 | 10/10 引文位置正确仅是定位结果；当前 v8 真实来源 runner 仍未验证 |

逐条工件路径、提示版本、测试命令与运行边界记录在同目录 JSON 审计工件中。原始运行文件均保持不变。

## 本轮实际离线验证

| 命令 | 结果 | 证明范围 |
| --- | --- | --- |
| `python -m unittest discover -s backend-python/tests -p 'test_*candidate_fta*.py' -q` | 35 项通过 | 候选服务/合同行为回归，不代表真实模型语义正确 |
| `python -m unittest discover -s backend-python/tests -p 'test_fta_cause_disposition.py' -q` | 16 项通过 | 当前 v5 原因处置合同回归，不代表模型遵循提示 |
| `python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_run_fta_event_scope_model_v6 -q` | 8 项通过 | v8 策略与 v6 runner 合同测试，不等于 v8 真实来源运行 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py --manifest evaluation/quality_eval/fta_baseline_manifest_v48.json` | 367/367 哈希有效 | v48 快照工件完整性 |

## 下一步与停止边界

P2 当前状态：合同审计完成；历史案例审查完成；v5/当前 event-scope 真实来源复跑待授权。下一次运行应一次选定代表样本、锁定其原文输入与预算，保存原始响应；不自动修复、不自动重试、不把模型结果并入 Gold。首选 F30021（重复引文/阻断反例）或 F06000（事件身份/嵌套正反例）；多阶段候选服务最多需要四次模型请求，必须先对具体样本和请求数取得新的明确授权。NASA Figure 7 如另跑 v8，须走独立 event-scope runner，并继续将图示参考与模型输入隔离。

在当前样本获得新版本真实运行之前，不宣称 P2 缺陷已关闭；全局 `fta_ready=false`、`production_ready=false` 保持。
