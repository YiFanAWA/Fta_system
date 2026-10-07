# F30021-C04 原文证据定位确认单

用途：只确认 `F30021-C04`（“short-circuit at the braking resistor”）应绑定到哪一处原文。此确认**不审核 AND/OR**，不把 F30021 顶层门从 `unknown` 改为其他标签，也不授权生成正式故障树。

## 当前状态

- 数据集：门节点审核集 v5
- 故障码：`F30021`
- 子项：`F30021-C04` — `short-circuit at the braking resistor`
- 状态：`pending_manual_locator`
- 原文 SHA-256：`f3178a6c9c46aa2109a44eb118c6a8730ebfdd6d9a6f5660147529f01ce41d31`
- offset 约定：原始 `input_text` 的 Unicode 字符索引，左闭右开 `[start,end)`

该短语在原文出现两次。按已确认规则，不自动选择其中一处。

## 候选位置

### 候选 A — `Possible causes` 原因列表

完整精确引用：

> `- short-circuit at the braking resistor.`

位置：`[332,372)`

上下文：

```text
Possible causes:
- ground fault in the power cables.
- ground fault at the motor.
- when the brake closes, this causes the hardware DC current monitoring to respond.
- short-circuit at the braking resistor.
```

### 候选 B — 故障值说明段

完整精确引用：

> `- short-circuit at the braking resistor.`

位置：`[468,508)`

上下文：

```text
... hardware DC current monitoring has responded.
- short-circuit at the braking resistor.
> 0:
Absolute value summation current amplitudes ...
```

## 审核填写

请选择该子项作为“Possible causes”原因列表证据应绑定的位置：

- [ ] 候选 A `[332,372)`
- [ ] 候选 B `[468,508)`
- [ ] 两处均需保留，并说明各自证据作用
- [ ] 两处都不足以支持该子项，继续 pending

审核理由：

```text
（请填写）
```

审核人/角色：____________________    日期：____________________

## 变更边界

仅当审核完成后，才可将该子项从 `pending_manual_locator` 改为经确认的精确跨度。无论选哪一处，故障值说明或原因列表本身都没有直接 AND/OR 组合语句；F30021 的事件级门仍应为 `unknown`，除非另有该作用域内的直接逻辑证据。
