# NASA Figure 7 单事件 DeepSeek 重跑评估 v2

日期：2026-09-29  
样例：`NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001`（已见 Development 样例）  
用途：检查启用 JSON 输出模式、压缩输出要求并增大输出上限后，能否得到可解析的单事件树结果。

## 结果

本次获准调用恰好 1 次，SDK 重试关闭。使用 `deepseek-flash`、`temperature=0`、`max_tokens=8192` 和 `response_format={"type":"json_object"}`。模型耗尽 8192 个 completion tokens，返回 `finish_reason=length`，最终 `message.content` 仍为空；没有可解析 JSON、节点或门型。离线结构/引文评估状态为 `truncated`，Gold 比较未执行。

这次没有解决 v1 的输出问题。累计是两次独立、各一次请求的开发尝试（v1：3000 tokens；v2：8192 tokens），均未产生可用正文；没有第三次请求。

## 能得出什么、不能得出什么

- 能得出：本次提供的请求配置没有产出可消费的结构化回答；增大预算并启用 JSON mode 后仍遇到截断/空正文。
- 不能据此断定根因是提示词、模型推理、API JSON mode 或输出预算中的某一项。DeepSeek 官方 JSON Output 文档明确提示该模式仍可能返回空 content，且要求合理设置 `max_tokens`；本次现象与“格式/完成问题”一致，但根因未被证明。
- 不能报告树结构正确率、AND/OR/unknown 准确率、校准度或模型失败率；模型没有给出可评分预测。
- 本样例来源与参考树已在开发阶段被查看，不是独立 Final，也不是人类专家 Gold。

## 输入隔离与状态边界

模型只接收通过 `fta_event_scope_packet_contract.model_input_payload()` 投影并校验的顶事件与原文段落；输入键为 `event_scope_id`、`top_event`、`source_segments`。独立参考 Gold、图示门型和 AI 审核标签没有进入 prompt。模型输入 SHA-256 与 v1 相同：`1e77b80a8f2a6ae62443468d21b075e4a213a3544cdc2b882a5d69b6ba6d4325`。

没有修改 Gold、数据库、生产 API 或就绪门禁。`fta_ready=false`、`production_ready=false` 保持不变。

## 可复核文件

- 原始响应：[v2 run JSON](fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json)
- 调用防重收据：[v2 attempt receipt](fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.attempt.json)
- 机器评估：[v2 assessment JSON](fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.json)
- 隔离运行器：[v2 runner](../public_sources/run_fta_event_scope_model_v2.py)
- 官方行为说明：[DeepSeek JSON Output](https://api-docs.deepseek.com/guides/json_mode/)

结论：此次只完成了一个受控格式/输出实验，模型树结果仍不可评估。后续不得自动重试；若未来需要继续排查，应先审查当前 API 返回对象可观测性与模型调用模式，再由用户明确授权新的调用。
