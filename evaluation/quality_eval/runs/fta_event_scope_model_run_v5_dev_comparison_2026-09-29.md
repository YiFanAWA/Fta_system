# NASA Figure 7 v5 单次开发运行复核

日期：2026-09-29  
样例：`NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001`（已见 Development）  
模型提示词：`event-scope-text-only-tree-v5-causal-path-scope`

## 运行事实

- 外部请求：1 次；重试：0；`finish_reason=stop`；严格 JSON 解析成功。
- 输出 10 个节点、4 个 gate scope。所有输出引文均唯一回指输入段落：15/15。
- 离线树合同：`blocked`；证据对象合同另有 1 项格式 blocker。
- 门型计数：`AND=0`、`OR=1`、`unknown=3`。
- 未向模型提供参考图门型或参考审核标签；未写正式 Gold、数据库、生产 API；`fta_ready=false`、`production_ready=false`。

## 对 v5 修改点的观察

模型在 `S1` 中把单电芯爆炸和模块容器失效列为顶事件的两个直接子项，方向上不再把“容器失效”挂成“电芯爆炸”的子事件。这是本次单样例中观察到的局部提示词遵循现象，不是门型正确性结论。

## 阻断问题

1. `S1`、`S2`、`S3`、`S4` 都以同一个 `E1` 为 output，违反一个事件只能有一个直接输出 scope 的层级合同。
2. `S2` 只有一个直接 child (`E4`)，scope 不满足至少两个不同直接 child 的结构要求。
3. 已知门 `S4=OR` 缺少合同要求的 `unknown_reason: null` 字段，输出形状不完整。

因此，即使模型把两条替代路径放进 `S4` 并标为 OR，整棵树仍不能被接受为 FTA Preview。不能由校验器自动删除其他 scope 或替模型重排层级。

## 结论边界

本报告只复核这一条已见开发样例的输出可用性、结构合同和引文定位。引文定位通过不代表引文语义蕴含；参考标签为 AI 角色审核，且预测与参考 scope 未建立可验证映射。因此不计算准确率、F1、校准、泛化或专家一致率，也不能据此宣称 v5 整体优于 v4。v5 的主要剩余缺陷已从目标条件方向转为“单一层级内组织多个因果 scope”及输出字段完整性。
