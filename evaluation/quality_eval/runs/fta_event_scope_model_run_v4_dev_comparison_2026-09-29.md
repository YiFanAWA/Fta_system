# NASA Figure 7 v4 开发样例：离线定性复核

日期：2026-09-29  
样本：`NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001`（已见 Development；单样例）  
结论：**结构合同阻断，不接受为 FTA Preview 树。**

本报告只做单样例离线定性检查。参考标签由 AI 角色审核，非真人专家 Gold；不计算准确率、F1、校准或泛化指标；图示门标签没有被当作原文语义金标。

## 运行与合同结果

| 项目 | 结果 | 边界 |
| --- | --- | --- |
| 请求 | 1 次，重试 0 次；`finish_reason=stop` | thinking disabled；输入不含 Gold |
| 严格 JSON | 通过 | 仅格式检查 |
| 层级合同 | 阻断；1 个 blocker | `S2` 只有 1 个直接子项，原输出不修复 |
| 引文位置 | 9/9 唯一匹配 | 只证明原文定位，不证明语义蕴含 |
| 门型输出 | 3 个 scope 均为 `unknown` | 根 scope 与 AI 角色审核的 OR 标签不同；次级 AND 未被输出；无准确率结论 |

## 定性发现

根 scope：模型输出 `unknown`，AI 角色审核的文本参考为 `OR`。这是单个已见样例上的标签分歧，不是真人专家结论。模型给全部 scope 都选择 unknown，说明当前提示词在本例偏保守。

结构上，根 scope 连接 E2 与 E4，但 E2 的 S2 scope 只有 E3 一个 child，因此整棵树按合同阻断。模型确实产生了引用段落定位，但这不能补救层级不完整。内部 scope 与参考 Gold scope 没有经过验证的一对一映射，所以不计算门型准确率。

## 限制与后续

- v4 仅是一轮 seen-Dev 对照；其输出不进入 Gold、数据库或生产服务。
- 不能据此宣称一般性模型改善或退化；只能确认这一个输出的合同和观察结果。
- 后续若调整 prompt，Figure 7 应留作开发回归；最终泛化需用未见来源独立验证。
- `fta_ready=false`、`production_ready=false` 保持不变。

机器可读记录：`evaluation/quality_eval/runs/fta_event_scope_model_run_v4_dev_comparison_2026-09-29.json`。
