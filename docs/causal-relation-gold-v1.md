# Siemens S210 Causal Relation Gold v1（专家审核前候选包）

## 当前结论

当前生成的是 **Causal Relation Candidate Bundle v1**，不是因果关系 Gold，也不是可直接用于 FTA 建树的关系集合。

来源数据包含 281 条 S210 故障记录、1041 条候选原因和字符级证据。现阶段只抽取 30 条分层抽样候选，作为第一批专家审核材料：每条候选都保留故障描述、候选原因、原文全文、证据引用和字符位置，但所有因果结论都保持 `pending`。

`causes` 字段只能说明抽取管线把这段内容归入了“候选原因”，不能自动证明：

- 该节点确实导致目标故障；
- 因果方向是原因节点到故障实体；
- 该关系可以进入 FTA；
- 多个原因之间存在 AND/OR 逻辑。

## 当前文件

| 层 | 文件 | 职责 |
|---|---|---|
| 候选数据 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v1.json` | 30 条待专家确认的因果候选，未接入运行层 |
| 专家清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md` | 给专家逐条填写因果状态、方向、关系类型、FTA 资格和意见 |
| 生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle.py` | 从冻结的 S210 Gold 可重复生成候选包与清单 |
| 候选校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_candidates.py` | 校验候选字段、证据偏移和“未提前批准”门禁 |
| 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v1_validation_2026-09-22.json` | 当前候选包的结构校验结果 |

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

当前校验报告必须保持：

- `expert_validated=false`；
- `causal_relations_complete=false`；
- `logic_gates_complete=false`；
- `fta_ready=false`。

只有专家填写后，才能生成独立的 `Causal Relation Gold`，并再次校验证据、方向和审核状态。即使因果 Gold 通过，也仍需单独建立 AND/OR Gold，才能进入自动建树验收。
