# Siemens S210 Causal Relation Gold v1（专家审核前候选包）

## 当前结论

第一批 30 条候选已经完成刘武专家审核，并转换为 `Causal Relation Gold v1`。第二批 66 条同一故障剩余原因也已完成审核。两批合并后的 `Causal Relation Gold v2` 收录 39 条专家确认的 `causes` 且 `source_to_target` 关系，覆盖 25 个目标故障；其余 57 条候选保存在排除清单中。

这仍然是 **两批试点范围的因果 Gold**，不是 281 条数据的全量因果闭环，也不是可直接自动建树的最终数据。当前 6 个故障已经拥有至少两个已确认因果子节点，具备进入 AND/OR 专家审核的条件，但逻辑门尚未确认。

来源数据包含 281 条 S210 故障记录、1041 条候选原因和字符级证据。本批从中抽取 30 条分层抽样候选，作为第一批专家审核材料；每条候选都保留故障描述、候选原因、原文全文、证据引用和字符位置。

`causes` 字段只能说明抽取管线把这段内容归入了“候选原因”，不能自动证明：

- 该节点确实导致目标故障；
- 因果方向是原因节点到故障实体；
- 该关系可以进入 FTA；
- 多个原因之间存在 AND/OR 逻辑。

## 当前文件

| 层 | 文件 | 职责 |
|---|---|---|
| 候选数据 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v1.json` | 第一批 30 条候选来源，已完成专家审核 |
| 第二批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json` | 15 个目标故障的 66 条剩余原因，待专家审核，用于后续 AND/OR 判断 |
| 专家清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md` | 给专家逐条填写因果状态、方向、关系类型、FTA 资格和意见 |
| 第二批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v2_remaining_same_faults_2026-09-22.md` | 补齐同一故障的其他原因，避免只审核每个故障的第一条原因 |
| 正式 Gold | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v1.json` | 25 条专家确认的因果关系，另含 5 条排除候选 |
| 合并 Gold v2 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v2.json` | 两批合并后的 39 条专家确认因果关系，另含 57 条排除候选 |
| 生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle.py` | 从冻结的 S210 Gold 可重复生成候选包与清单 |
| Word 转换器 | `evaluation/quality_eval/public_sources/convert_siemens_s210_causal_relation_expert_review.py` | 将专家填写的 Word 表转换为正式 Gold |
| 候选校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_candidates.py` | 校验候选字段、证据偏移和“未提前批准”门禁 |
| Gold 校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_gold.py` | 校验专家 Gold 的方向、证据和 FTA 未就绪门禁 |
| 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v1_validation_2026-09-22.json` | 当前候选包的结构校验结果 |
| Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v1_validation_2026-09-22.json` | 25 条正式关系的校验结果 |
| 第二批 Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v2_remaining_same_faults_validation_2026-09-22.json` | 14 条第二批确认关系的校验结果 |
| 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v2.py` | 合并两批专家 Gold，并检查关系 ID 不重复 |
| 合并 Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v2_validation_2026-09-22.json` | 39 条合并关系的校验结果 |
| AND/OR 候选包 | `evaluation/quality_eval/datasets/siemens_s210_and_or_logic_candidates_v1.json` | 6 个多原因故障事件，逻辑门字段全部待审核 |
| AND/OR 专家清单 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_expert_review_checklist_v1_2026-09-22.md` | 供专家确认子原因集合和 AND/OR/unknown |
| AND/OR Gold | `evaluation/quality_eval/datasets/siemens_s210_and_or_logic_gold_v1.json` | 5 个 OR 已确认，F01611 保留 unknown |
| AND/OR Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_gold_v1_validation_2026-09-22.json` | 6 个事件均已结构校验 |
| AND/OR 就绪报告 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_readiness_v1_2026-09-22.md` | 当前因果 Gold 和逻辑门审核门禁 |
| FTA Preview 生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_fta_preview.py` | 只从已批准逻辑事件生成带证据预览 |
| FTA Preview | `evaluation/quality_eval/datasets/siemens_s210_fta_preview_v1.json` | 5 个 OR 事件，明确标记为 preview_only |
| FTA Preview 文本报告 | `evaluation/quality_eval/runs/siemens_s210_fta_preview_v1_2026-09-22.md` | 供人工查看的故障树预览 |
| FTA Preview 校验报告 | `evaluation/quality_eval/runs/siemens_s210_fta_preview_v1_validation_2026-09-22.json` | 证据和生产门禁校验结果 |

## 专家需要确认什么

每条候选必须独立填写：

1. `causal_status`：`causal`、`associated_only`、`unsupported` 或 `cannot_determine`；
2. `direction`：`source_to_target`、`target_to_source`、`undirected` 或 `unknown`；
3. `relation_type`：`causes`、`caused_by`、`associated_with` 或 `no_relation`；
4. `fta_eligible`：只有证据直接、因果明确、方向清楚时才为 `true`；
5. `overall_decision` 和审核意见。

“Cause”标题、参数共同出现或处理建议本身，都不能单独作为因果关系通过依据。

## 生成与校验

```powershell
python evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle.py `
  --limit 30 `
  --reviewer 刘武 `
  --output evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v1.json `
  --checklist evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md

python evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_candidates.py `
  --input evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v1.json `
  --output evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v1_validation_2026-09-22.json
```

## 审核统计矛盾

Word 文档前置汇总写成 `causal=26`、`associated_only=3`、`cannot_determine=1`，但逐条审核表实际为 `causal=25`、`associated_only=4`、`cannot_determine=1`。转换器以逐条表格为权威，并在 Gold 的 `dataset_info.summary_discrepancy` 中保留了这项审计差异；没有把第 26 条虚增进入关系 Gold。

## 当前门禁

当前校验报告保持：

- `expert_validated=true`（仅针对当前两批 96 条候选范围）；
- `causal_relations_complete=false`；
- `logic_gates_complete=false`（F01611 为 `unknown`）；
- `fta_ready=false`。

同时，因果 Gold 目前只覆盖两批试点候选，不能代表 281 条记录的全量因果召回。当前已经生成 5 个 OR 事件的带证据 FTA Preview，但它只用于查看和验证数据链路，不得写入生产树注册表。F01611 仍不得自动建树；整体 FTA 仍未就绪。
