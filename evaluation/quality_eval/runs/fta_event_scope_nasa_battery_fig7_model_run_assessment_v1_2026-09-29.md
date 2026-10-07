# NASA Figure 7 单事件 FTA 模型运行评估

- 样例：`NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001`（Development-only）
- 模型：请求与响应别名均为 `deepseek-flash`，提供方 `api.deepseek.com`
- 实际请求：1 次；重试：0 次
- 输入：仅使用经过合同校验的 `model_input` 投影；模型未收到来源包络、图示参考树或 AND/OR Gold
- 输出 token 上限：3000；实际完成 token：3000；`finish_reason=length`

## 结果

API 请求返回成功，但没有可用的最终答案：保存的 message content 长度为 0，严格 JSON 解析失败，未得到任何 gate scope。由于没有模型预测，未与独立参考 Gold 比较，门型指标留空。

最直接的观察是输出达到 3000-token 上限并以 `length` 结束。输出预算不足以产生可用 JSON 是合理解释，但仅凭该响应不能证明供应商内部具体在哪个生成阶段耗尽预算。

遵守本次“一次推理”授权，本轮没有重试或追加请求。任何更大输出预算的后续试验都需要新的单独授权。

## 解释边界

这是一个已见 NASA 开发样例上的单次技术可用性尝试，不是模型准确率、门型能力、校准或泛化结果；也不是人类专家审核或正式 Gold。Gold、生产 API、数据库及全局 readiness 未改；`fta_ready=false`、`production_ready=false` 保持不变。
