# Siemens S210 因果关系专家审核 v6 批次摘要

审核人：刘武
审核日期：2026-09-23
范围：第六批 50 条候选
正式合并目标：Causal Relation Gold v7

## 审核结论

| 结论 | 数量 | 处理 |
|---|---:|---|
| `approve` 且满足因果方向与 FTA 资格门禁 | 42 | 并入正式 Gold v7 |
| `revise` | 4 | 保留为待修订，不进入 Gold |
| `reject` | 4 | 保留在排除候选审计清单 |
| `causal` | 46 | 其中只有 42 条同时满足完整批准门禁 |
| `associated_only` | 4 | 不作为因果关系晋升 |

批准门禁为：`causal_status=causal`、`direction=source_to_target`、`relation_type=causes`、`fta_eligible=true` 且 `overall_decision=approve`。不得仅凭“causal”标签晋升。

## 待修订记录

| 候选 ID | 故障码 | 专家指出的问题 | 审核给出的规范化文本 |
|---|---|---|---|
| `CR-CAND-V6-097` | A30730 | 原候选只是报警值短语，未表达 Cause 段真实语义 | `PROFIsafe transferred reference block is negative.` |
| `CR-CAND-V6-103` | F01001 | “basic system or a technology function”是复合 OR 候选，需拆成独立原因节点后再审核 | 未给出最终拆分文本 |
| `CR-CAND-V6-292` | F01640 | 候选混入“Safety Integrated 已识别”的诊断动作；应规范为被监控组件更换事件 | `A Safety Integrated monitored component has been replaced.` |
| `CR-CAND-V6-296` | F01641 | 同类诊断动作与上游组件更换事件混写 | `A Safety Integrated monitored component has been replaced.` |

以上文本均是审核意见中的修订建议，不因出现在专家审核文件中就自动获得批准；需完成修订确认并重新满足完整批准门禁后，才能进入后续 Gold 版本。

## 拒绝记录

| 候选 ID | 故障码 | 主要理由 |
|---|---|---|
| `CR-CAND-V6-141` | F01042 | 当前候选主要复述目标故障状态；具体错误参数需从故障值中另行抽取 |
| `CR-CAND-V6-192` | F01043 | 只描述检测到致命下载错误，没有给出具体上游条件 |
| `CR-CAND-V6-275` | F01600 | 候选基本重述监控通道故障及 STO 响应；应审核其中具体上游条件 |
| `CR-CAND-V6-301` | F01650 | “需要验收测试”近似目标故障本身，未说明导致该状态的上游原因 |

拒绝只针对本批候选作为因果边的资格；不删除来源记录，也不影响后续从原文中提出更具体候选。

## 三份审核材料与证据核验

- JSON、Markdown、Word 均包含同一组 50 个候选，记录顺序及逐条审核结论一致。
- 50/50 条证据字符区间与候选包一致，且引用文本精确匹配来源全文对应区间。
- 50/50 条完整来源文本与候选包一致。
- 合并器验证只把满足完整批准门禁的 42 条写入 Gold；其余 8 条保留在 excluded/pending 审计数据中。

## Gold v7 对账

| 项目 | 数量/状态 |
|---|---:|
| 正式因果关系 | 205 |
| 已审核候选 | 296 / 1041 |
| 未审核候选 | 745 |
| 排除或暂缓候选 | 91 |
| 覆盖目标故障 | 132 |
| 至少有两条已批准原因的目标故障 | 40 |
| `causal_relations_complete` | `false` |
| `logic_gates_complete` | `false` |
| `fta_ready` | `false` |

验证报告：`siemens_s210_causal_relation_gold_v7_validation_2026-09-23.json`。AI provisional Gold v7 与本正式 Gold v7 是两个独立文件；本次正式合并没有使用 AI 模拟审核作为专家批准。

## 下一步

先为 A01691、A01782（前批遗留）及 A30730、F01001、F01640、F01641（本批）建立修订确认材料。未完成修订复核的记录继续保持 pending；随后再从剩余 745 条候选中生成第七批。任何一步都不得提前打开自动建树或生产 FTA 门禁。
