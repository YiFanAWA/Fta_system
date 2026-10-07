# NASA Figure 7 v6 单次开发运行定性复核

日期：2026-09-29  
样例：`NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001`（已见 Development）  
提示词：`event-scope-text-only-tree-v6-single-hierarchy`

## 运行事实

- DeepSeek Flash 请求 1 次、重试 0 次；`finish_reason=stop`，严格 JSON 解析成功；思考模式关闭，Gold 未进入模型输入。
- 输出 7 个节点、3 个 gate scope，3 个门均为 `unknown`；结构合同通过，节点/作用域共 10 条引文均在输入段落中唯一定位。
- v5 的三类结构问题在本次输出中没有重现：输出节点没有重复 gate scope、没有单子项 gate、所有 gate 必需字段齐全。
- 详细原始内容、请求元数据、尝试收据和机械评估分别见 [run JSON](fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.json)、[assessment JSON](fta_event_scope_nasa_battery_fig7_model_run_assessment_v6_2026-09-29.json) 和 [attempt receipt](fta_event_scope_nasa_battery_fig7_model_run_v6_2026-09-29.attempt.json)。

## 语义风险观察（不是 Gold 裁定）

1. **显式替代连接词没有转成可审核的门证据。** S1 的 `scope_evidence` 本身描述两条路径由 “or” 连接，但模型仍输出 `gate=unknown`、`logic_evidence=null`。这至少表明模型没有把文本中可见的 OR 线索绑定为逻辑证据；是否最终接受为 OR，仍需按冻结的逻辑门政策/人工审核裁定。
2. **重复事件身份仍不清楚。** E2 和 E4 都表示“单个电芯爆炸”，各自引用不同原文提法。输入后文说明该事件是两个主分支共有的中间事件。当前树合同要求单父层级，故需要明确共享事件应如何表示；本次结果没有证明两个节点应合并或必须分开。
3. **事件粒度可能过粗。** E5 将过压/过温、邻近电池受损或不稳定、次生爆炸及排气不足压缩成一个很长的中间事件；E7 又将复合路径整体作为中间事件。引文位置正确，但尚未证明这些节点的边界和层级在语义上正确。
4. **门型证据提取整体偏保守。** S2、S3 也都为 `unknown`，且没有任何 `logic_evidence`。原文包含条件、合取及替代路径表述；当前机械合同不评估这些连接词是否被正确映射为各自 scope 的门型。

## 结论与边界

v6 **解决了本样例上 v5 的结构/字段合同阻断**，并通过引用位置检查；这不是模型语义验收，也不是已接受的 FTA Preview。S1 对明确 “or” 线索的漏绑定，以及重复事件身份和复合事件粒度问题，说明仍需补足语义审查/评测合同。未计算准确率、F1、校准或泛化指标；参考图与 AI 角色审核不是真人专家 Gold。未修改正式 Gold、数据库、生产 API 或 readiness；`fta_ready=false`、`production_ready=false`。

下一步先把上述失败模式固定成**开发回归与人工语义审查项**，明确连接词到 scope 的证据政策及共享事件/复合事件表示规则；不要仅凭这一条样例立即迭代提示词并再次调用模型。后续任何在线请求都需要新的明确授权。
