# Siemens S210 Causal Relation Gold v7（专家审核进度）

## 当前结论

第一批 30 条、第二批 66 条及第三至第六批各 50 条候选，累计 296 条，已完成刘武专家审核。A01730 已在 **Gold v5 阶段**完成修订复审并正式批准；第六批中 42 条符合批准门禁并进入 Gold，4 条待修订、4 条拒绝。当前 `Causal Relation Gold v7` 收录 205 条专家确认的 `causes` 且 `source_to_target` 关系，覆盖 132 个目标故障；91 条候选保存在排除或暂缓清单中。

这仍然是 **六批已审核候选范围的因果 Gold**，不是 281 条数据的全量因果闭环，也不是可直接自动建树的最终数据。当前仍保留 `causal_relations_complete=false`、`logic_gates_complete=false` 和 `fta_ready=false`。

原始来源数据包含 281 条 S210 故障记录、1041 条候选原因和字符级证据。v1 阶段最初从中抽取 30 条分层候选；随后 v2 补充 66 条同故障剩余原因，v3、v4 和 v5 各补充 50 条此前未审核候选，因此当前累计专家审核范围为 246 条。每条候选都保留故障描述、候选原因、原文全文、证据引用和字符位置。

`causes` 字段只能说明抽取管线把这段内容归入了“候选原因”，不能自动证明：

- 该节点确实导致目标故障；
- 因果方向是原因节点到故障实体；
- 该关系可以进入 FTA；
- 多个原因之间存在 AND/OR 逻辑。

## 当前文件

| 层 | 文件 | 职责 |
|---|---|---|
| 候选数据 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v1.json` | 第一批 30 条候选来源，已完成专家审核 |
| 第二批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v2_remaining_same_faults.json` | 15 个目标故障的 66 条剩余原因，已完成专家审核，用于补齐同一故障的多原因关系及后续 AND/OR 判断 |
| 第三批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v3_remaining_unreviewed.json` | 排除 v1/v2 后生成的 50 条候选来源，覆盖 50 个故障 |
| 第四批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v4_remaining_unreviewed.json` | 排除 v1/v2/v3 后生成的 50 条候选来源，覆盖 50 个故障 |
| 第五批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v5_remaining_unreviewed.json` | 排除 v1-v4 后生成的 50 条候选来源，覆盖 50 个故障；已完成专家审核，其中 45 条 approve、2 条 revise、3 条 reject |
| 第六批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v6_remaining_unreviewed.json` | 排除 v1-v5 后生成的 50 条候选来源，覆盖 50 个故障；已完成专家审核 |
| 专家清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md` | 给专家逐条填写因果状态、方向、关系类型、FTA 资格和意见 |
| 第二批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v2_remaining_same_faults_2026-09-22.md` | 补齐同一故障的其他原因，避免只审核每个故障的第一条原因 |
| 第三批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v3_remaining_unreviewed_2026-09-22.md` | 扩大目标故障覆盖，供专家继续审核 |
| 第四批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v4_remaining_unreviewed_2026-09-22.md` | 第四批 50 条候选的专家审核底稿 |
| 第五批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v5_remaining_unreviewed_2026-09-22.md` | 第五批 50 条候选的专家审核底稿 |
| 第六批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v6_remaining_unreviewed_2026-09-23.md` | 第六批 50 条候选的专家审核底稿 |
| 第四批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v4_LiuWu_FULL_50.json/.md/.docx` | 刘武对第四批 50 条候选的逐条审核原件，JSON 为结构化转换输入，MD/DOCX 为审核记录原件 |
| 第五批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v5_LiuWu_FULL_50.json/.md/.docx` | 刘武对第五批 50 条候选的逐条审核原件，JSON 为结构化转换输入，MD/DOCX 为审核记录原件 |
| 第六批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v6_LiuWu_FULL_50.json/.md/.docx` | 刘武对第六批 50 条候选的逐条审核原件；JSON、Markdown、Word 已逐条交叉核对 |
| 第三批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v3_LiuWu_FULL_50.json/.md/.docx` | 刘武对第三批 50 条候选的逐条审核原件，JSON 为结构化转换输入 |
| 正式 Gold | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v1.json` | 25 条专家确认的因果关系，另含 5 条排除候选 |
| 合并 Gold v2 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v2.json` | 两批合并后的 39 条专家确认因果关系，另含 57 条排除候选 |
| 合并 Gold v3 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v3.json` | 三批合并后的 72 条专家确认因果关系，另含 74 条排除候选 |
| 合并 Gold v4 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v4.json` | 四批合并后的 117 条专家确认因果关系，另含 79 条排除候选 |
| A01730 批准材料 | `Siemens_S210_Causal_Relation_Revision_Confirmation_v4_A01730_LiuWu_APPROVED.json/.md/.docx` | 刘武对 A01730 修订候选的批准原件，包含最终原因文本和审批门禁 |
| 合并 Gold v5 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v5.json` | 在 v4 基础上合并 A01730 修订后的 118 条专家确认因果关系，另含 78 条排除候选 |
| 合并 Gold v6 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v6.json` | 在 v5 基础上合并第五批 45 条批准关系，共 163 条专家确认因果关系，另含 83 条排除或暂缓候选 |
| 合并 Gold v7 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v7.json` | 在 Gold v6 基础上合并第六批 42 条批准关系，共 205 条专家确认因果关系，另含 91 条排除或暂缓候选 |
| 生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle.py` | 从冻结的 S210 Gold 可重复生成候选包与清单 |
| Word 转换器 | `evaluation/quality_eval/public_sources/convert_siemens_s210_causal_relation_expert_review.py` | 将专家填写的 Word 表转换为正式 Gold |
| 候选校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_candidates.py` | 校验候选字段、证据偏移和“未提前批准”门禁 |
| Gold 校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_gold.py` | 校验专家 Gold 的方向、证据和 FTA 未就绪门禁 |
| 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v1_validation_2026-09-22.json` | 当前候选包的结构校验结果 |
| Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v1_validation_2026-09-22.json` | 25 条正式关系的校验结果 |
| 第二批 Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v2_remaining_same_faults_validation_2026-09-22.json` | 14 条第二批确认关系的校验结果 |
| 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v2.py` | 合并两批专家 Gold，并检查关系 ID 不重复 |
| 合并 Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v2_validation_2026-09-22.json` | 39 条合并关系的校验结果 |
| v3 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v3.py` | 校验第三批逐条审核结果并合并到 Gold v3 |
| v3 合并器测试 | `evaluation/quality_eval/public_sources/test_merge_siemens_s210_causal_relation_gold_v3.py` | 校验 50 条审核结果、72 条关系和历史日期缺失兼容 |
| 合并 Gold v3 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v3_validation_2026-09-22.json` | 72 条合并关系的结构校验结果 |
| v4 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v4.py` | 校验第四批结构化审核结果并合并到 Gold v4 |
| v4 合并器测试 | `evaluation/quality_eval/public_sources/test_merge_siemens_s210_causal_relation_gold_v4.py` | 校验 revise 记录不会进入正式 Gold |
| 合并 Gold v4 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v4_validation_2026-09-22.json` | 117 条合并关系的结构校验结果 |
| A01730 修订包 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_v4_a01730.json` | 保存原候选、完整原文、证据和专家待填写字段；未进入 Gold |
| A01730 修订清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_v4_a01730_2026-09-22.md` | 供刘武专家确认规范化候选原因 |
| 修订包生成器 | `evaluation/quality_eval/public_sources/prepare_siemens_s210_causal_relation_revision_v4.py` | 从第四批候选中隔离指定 revise 候选 |
| 修订包测试 | `evaluation/quality_eval/public_sources/test_prepare_siemens_s210_causal_relation_revision_v4.py` | 校验原文证据、待审核状态和 Gold 门禁 |
| v5 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v5.py` | 移除 A01730 的 pending 排除项，并合并专家批准的规范化原因和 Cause 证据 |
| v5 合并器测试 | `evaluation/quality_eval/public_sources/test_merge_siemens_s210_causal_relation_gold_v5.py` | 校验 A01730 的排除项替换、证据定位和生产门禁 |
| 合并 Gold v5 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v5_validation_2026-09-22.json` | 118 条合并关系的结构校验结果 |
| 第三批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v3_remaining_unreviewed_validation_2026-09-22.json` | 50 条候选来源的结构校验结果 |
| 第四批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v4_remaining_unreviewed_validation_2026-09-22.json` | 50 条候选来源的结构校验结果 |
| 第五批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v5_remaining_unreviewed_validation_2026-09-22.json` | 审核前 50 条候选来源的结构校验报告；不代表专家审核状态，最终状态以第五批专家审核结果为准 |
| 第六批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v6_remaining_unreviewed_validation_2026-09-23.json` | 第六批 50 条候选来源的结构校验报告，已通过；不代表专家审核状态 |
| 第五批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v5.py` | 排除 v1-v4 已审核候选并按故障码轮询生成第五批 |
| 第五批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v5.py` | 校验第五批不重复、数量和证据结构 |
| 第六批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v6.py` | 排除 v1-v5 已审核候选并按故障码轮询生成第六批 |
| 第六批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v6.py` | 校验第六批不重复、数量和证据结构 |
| 第五批修订包 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_v5.json` | 保存 A01691、A01782 两条 revise 候选及专家建议，未进入 Gold |
| 第五批修订清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_v5_2026-09-22.md` | 供刘武复核原因文本和 A01782 证据定位 |
| v6 修订确认包 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu.json` | A01691、A01782 的专家确认表单，保持 pending，不代表 Gold 批准 |
| v6 修订确认清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu_2026-09-23.md` | 供刘武逐条填写最终原因、证据、因果状态、方向、关系类型和 FTA 资格 |
| v6 修订确认 Word | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu_2026-09-23.docx` | 可下载填写的专家确认单 |
| v6 修订确认生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_revision_confirmation_v6.py` | 从 v5 pending 修订包生成 JSON、Markdown 和 Word 确认单 |
| v6 修订确认测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_revision_confirmation_v6.py` | 校验两条记录保持 pending 且建议证据不覆盖当前错误证据 |
| AI 模拟预审结果 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.json/.md` | 独立智能体对两条 revise 的准备性意见；不属于专家 Gold，不得直接合并 |
| AI 临时 v7 数据 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v7_ai_provisional.json` | 在 Gold v6 上叠加两条 AI 模拟修订关系的临时视图；不属于正式 Gold |
| AI 临时 v7 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_ai_provisional_v7.py` | 生成明确标记为 `ai_assisted_provisional` 的临时数据 |
| AI 临时 v7 合并器测试 | `evaluation/quality_eval/public_sources/test_merge_siemens_s210_causal_relation_ai_provisional_v7.py` | 校验临时关系数量和正式专家门禁不被打开 |
| 第五批修订包生成器 | `evaluation/quality_eval/public_sources/prepare_siemens_s210_causal_relation_revision_v5.py` | 从第五批专家结果中隔离两条 revise 候选 |
| 第五批修订包测试 | `evaluation/quality_eval/public_sources/test_prepare_siemens_s210_causal_relation_revision_v5.py` | 校验两条修订候选保持 pending |
| v6 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v6.py` | 合并第五批已批准关系，并保留 revise/reject 排除项 |
| v6 合并器测试 | `evaluation/quality_eval/public_sources/test_merge_siemens_s210_causal_relation_gold_v6.py` | 校验仅批准项进入 Gold |
| 合并 Gold v6 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v6_validation_2026-09-22.json` | 163 条合并关系的结构校验结果 |
| v7 合并器 | `evaluation/quality_eval/public_sources/merge_siemens_s210_causal_relation_gold_v7.py` | 对照专家 JSON、Markdown、Word 和候选包，验证证据区间后仅合并符合全部批准门禁的关系 |
| v7 合并审计 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v7_merge_audit_2026-09-23.json` | 记录三份审核原件一致性、50 条证据/原文校验、批准/修订/拒绝名单与数量对账 |
| 合并 Gold v7 校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v7_validation_2026-09-23.json` | 205 条正式关系的 Gold 结构校验结果；FTA 门禁仍关闭 |
| AND/OR 候选包 | `evaluation/quality_eval/datasets/siemens_s210_and_or_logic_candidates_v1.json` | 6 个多原因故障事件，逻辑门字段全部待审核 |
| AND/OR 专家清单 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_expert_review_checklist_v1_2026-09-22.md` | 供专家确认子原因集合和 AND/OR/unknown |
| AND/OR Gold | `evaluation/quality_eval/datasets/siemens_s210_and_or_logic_gold_v1.json` | 5 个 OR 已确认，F01611 保留 unknown |
| AND/OR Gold 校验报告 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_gold_v1_validation_2026-09-22.json` | 6 个事件均已结构校验 |
| AND/OR 就绪报告 | `evaluation/quality_eval/runs/siemens_s210_and_or_logic_readiness_v1_2026-09-22.md` | 当前因果 Gold 和逻辑门审核门禁 |
| FTA Preview 生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_fta_preview.py` | 只从已批准逻辑事件生成带证据预览 |
| FTA Preview | `evaluation/quality_eval/datasets/siemens_s210_fta_preview_v1.json` | 5 个 OR 事件，明确标记为 preview_only |
| FTA Preview 文本报告 | `evaluation/quality_eval/runs/siemens_s210_fta_preview_v1_2026-09-22.md` | 供人工查看的故障树预览 |
| FTA Preview 校验报告 | `evaluation/quality_eval/runs/siemens_s210_fta_preview_v1_validation_2026-09-22.json` | 证据和生产门禁校验结果 |
| FTA Graph 合同 | `backend-python/contracts/fta_graph_contract.py` | 后端唯一 owner，校验逻辑门、因果方向、节点唯一性、证据和生产门禁 |
| FTA Graph 合同测试 | `backend-python/tests/test_fta_graph_contract.py` | 验证 Preview 可通过、生产标记被拒绝、证据缺失被拒绝 |

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

Gold v7 结构校验已通过，当前门禁为：

- `expert_validated=true`，范围严格限定为 `expert_validation_scope=reviewed_candidates_only`；
- `source_candidate_count=1041`、`reviewed_candidate_count=296`、`unreviewed_candidate_count=745`；
- 205 条关系通过命名专家批准门禁；91 条在排除/暂缓清单中，其中包含待修订记录；
- 第六批 42 条批准进入正式 Gold；4 条 revise 和 4 条 reject 未进入 Gold；
- 第五批遗留的 A01691、A01782 revise 仍未关闭；第六批 revise 为 A30730、F01001、F01640、F01641；
- AI 临时 Gold v7 是独立的 provisional 文件，不是本次正式 Gold v7 的来源；
- `causal_relations_complete=false`；
- `logic_gates_complete=false`（F01611 仍为 `unknown`）；
- `fta_ready=false`，`runtime_registry_updated=false`。

累计候选账目闭合：`1041 = 296 reviewed + 745 unreviewed`；已审核范围内 `296 = 205 approved relations + 91 excluded_or_pending`。Gold v7 覆盖 132 个目标故障，其中 40 个目标故障有至少两条已批准因果关系。当前生成的 5 个 OR 事件 FTA Preview 仅用于查看和合同验证，不得写入生产树注册表；整体 FTA 尚未就绪。

## 下一阶段目标

当前目标为 **Causal Relation Coverage Expansion v2**：保持 Gold v7 正式门禁，优先为 6 条 revise 建立明确的修订确认/暂缓闭环，再从剩余 745 条候选中生成第七批审核材料。

### 目标范围

- 待修订集合：A01691、A01782、A30730、F01001、F01640、F01641。当前这些记录均不得直接进入正式 Gold；需要确认最终原因文本、证据映射和完整批准门禁。AI 预审只能作为独立参考。
- 第七批：待从剩余 745 条未审核候选中按既有去重和轮询策略选择，生成候选包、字符级证据、专家清单和结构校验报告。
- 每条审核结果继续保留 `causal_status`、`direction`、`relation_type`、`fta_eligible`、`overall_decision`、证据和专家意见。

### 验收条件

- 正式 Gold 只允许真实命名专家 `approve` 的关系进入；AI 模拟关系只能进入临时视图。
- 新批次与前序候选不重复，证据引用和字符位置通过校验。
- `reviewed_candidate_count`、`unreviewed_candidate_count`、Gold 数量和排除/暂缓数量能够对账。
- `causal_relations_complete=false`、`logic_gates_complete=false`、`fta_ready=false` 继续保持，直到全量关系和逻辑门门禁完成。

### 停止条件

未关闭的 revise 不得晋升 Gold；第七批审核材料未通过结构校验前不发给审核；在因果关系全量覆盖和 AND/OR 逻辑门审核门禁完成前，不更新生产树注册表或宣布 FTA 就绪。
