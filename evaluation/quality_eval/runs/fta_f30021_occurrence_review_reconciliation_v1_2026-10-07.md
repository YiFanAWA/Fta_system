# F30021 重复证据定位离线对账 v1

日期：2026-10-07  
性质：离线工程复核；无模型调用，不改原始运行、Gold、数据库、共享合同或 readiness。

## 结论

已有 C04 定位审核在来源哈希、原文偏移和唯一 Possible causes scope 上一致：`[332,372)` 是原因列表内的唯一出现，`[468,508)` 位于后续 r0949 故障值说明。该历史定位结果本次**没有回填**到最新 v5 原始运行。

因此最新运行仍为 `blocked`：C04=`unresolved` 且没有已确认 evidence；顶事件短语在原文出现 4 次；child 集合不完整；门型为 `unknown`。本次关闭的是定位工件与来源的离线一致性核对，不是 FTA 语义缺陷。

## 来源与偏移核验

- 样本：`SIEMENS_S210_2019_F30021` / `F30021`
- 原文 SHA-256：`f3178a6c9c46aa2109a44eb118c6a8730ebfdd6d9a6f5660147529f01ce41d31`
- 偏移：Unicode code point，zero-based half-open [start,end)
- 唯一审核 scope：`[166,372)`，其中 exact quote 位于 `[332,372)`
- 全文重复 exact quote：`[332,372)`（scope 内）；`[468,508)`（scope 外）
- 原定位材料来源：授权 AI 子智能体审核；`reviewer_is_human_expert=false`、`formal_gold=false`。

## 最新运行未解除的阻断

- 当前原因处置：index 3 `short-circuit at the braking resistor` → `unresolved` / `evidence_missing_or_ambiguous`，`evidence=[]`。
- 原始抽取仍保留两个 cause span：`334–371`、`470–507`；对应 context span：`332–372`、`468–508`。
- Blockers：`cause_disposition_unresolved:3, top_event_evidence_ambiguous`。
- 门型继续 `unknown`，没有添加门证据；本材料不推 OR/AND。

## 边界与下一步

本轮不改共享 evidence/API 合同。若未来要让运行时或审核端消费已确认的定位，必须先明确唯一 owner 与持久化/审核出口，再单独评审合同变更；在此之前，最新 v5 原始运行保持不可变且 blocked。任何新的在线模型请求都需要针对该次请求重新授权。
