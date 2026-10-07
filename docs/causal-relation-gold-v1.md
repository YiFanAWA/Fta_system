# Siemens S210 Causal Relation Gold v7（专家审核进度）

> **当前状态入口（2026-09-23）**：本文件以下内容保留 Gold v7 的历史人工审核事实，不覆盖人工 Gold。按照用户本轮明确授权，V1–V21 的全部 1,041 条候选另已形成独立的 **AI 授权专家角色审核快照**，并完成 SQLite 导入/回读。当前状态、来源标识、统计和数据库合同以 [`docs/siemens-s210-ai-authorized-review-v1.md`](siemens-s210-ai-authorized-review-v1.md) 及其运行报告为准；不得把 AI 快照称为真人专家签字，也不得把 `fta_ready` 改为 true。

## 当前结论

第一批 30 条、第二批 66 条及第三至第六批各 50 条候选，累计 296 条已取得逐条刘武审核决议。这里的“已审核”表示决议已记录，不代表所有 `revise` 均已关闭：当前仍有 40 条 `revise`，其中仅 6 条进入现有修订确认包，另 34 条来自 v1-v3、尚未找到后续关闭记录。A01730 已在 **Gold v5 阶段**完成修订复审并正式批准；第六批中 42 条符合批准门禁并进入 Gold，4 条待修订、4 条拒绝。当前 `Causal Relation Gold v7` 收录 205 条专家确认的 `causes` 且 `source_to_target` 关系，覆盖 132 个目标故障；91 条候选保存在排除或暂缓清单中，其中 40 条 revise、40 条 cannot_determine、11 条 reject。

这仍然是 **六批已审核候选范围的因果 Gold**，不是 281 条数据的全量因果闭环，也不是可直接自动建树的最终数据。当前仍保留 `causal_relations_complete=false`、`logic_gates_complete=false` 和 `fta_ready=false`。

原始来源数据包含 281 条 S210 故障记录和 1041 条候选原因。v1 阶段最初抽取 30 条分层候选；v2 补充 66 条同故障剩余原因；v3 至 v7 各补充 50 条，因此 v1-v7 共打包 346 条，其中 296 条已取得具名专家审核决议、v7 的 50 条仍待审核。v8 再从尚未打包候选中选取 50 条，当前总打包数为 396，具名专家已审核范围仍为 296，待审核为 100，尚未打包为 645。历史 V1-V7 的证据位置曾发现候选顺序错配风险，不能只因偏移有效就视为语义对齐；V8 改为从候选文本和完整原文独立重新定位。

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
| 第七批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v7_remaining_unreviewed.json` | 排除 v1-v6 已审核候选后生成 50 条，覆盖 50 个故障；尚待专家审核 |
| 第八批候选 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_candidates_v8_remaining_unreviewed.json` | 从前七批未打包候选中选择 50 条；45 条有唯一规范化精确原文匹配，5 条无精确匹配并保持证据空白待人工定位；尚待专家审核 |
| 专家清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v1_2026-09-22.md` | 给专家逐条填写因果状态、方向、关系类型、FTA 资格和意见 |
| 第二批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v2_remaining_same_faults_2026-09-22.md` | 补齐同一故障的其他原因，避免只审核每个故障的第一条原因 |
| 第三批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v3_remaining_unreviewed_2026-09-22.md` | 扩大目标故障覆盖，供专家继续审核 |
| 第四批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v4_remaining_unreviewed_2026-09-22.md` | 第四批 50 条候选的专家审核底稿 |
| 第五批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v5_remaining_unreviewed_2026-09-22.md` | 第五批 50 条候选的专家审核底稿 |
| 第六批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v6_remaining_unreviewed_2026-09-23.md` | 第六批 50 条候选的专家审核底稿 |
| 第七批清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v7_remaining_unreviewed_2026-09-23.md` | 第七批 50 条候选的专家审核底稿 |
| 第四批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v4_LiuWu_FULL_50.json/.md/.docx` | 刘武对第四批 50 条候选的逐条审核原件，JSON 为结构化转换输入，MD/DOCX 为审核记录原件 |
| 第五批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v5_LiuWu_FULL_50.json/.md/.docx` | 刘武对第五批 50 条候选的逐条审核原件，JSON 为结构化转换输入，MD/DOCX 为审核记录原件 |
| 第六批专家审核结果 | `Siemens_S210_Causal_Relation_Expert_Review_v6_LiuWu_FULL_50.json/.md/.docx` | 刘武对第六批 50 条候选的逐条审核原件；JSON、Markdown、Word 已逐条交叉核对 |
| Gold v7 revise 台账审计 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_gold_v7_revise_backlog_audit_2026-09-23.md` | 只读核对 1041 个源候选、v1-v7 候选包、Gold v7 决议、证据跨度及 v1-v3 专家原件；确认 40 条 revise 中 34 条历史项仍未关闭 |
| 历史 revise 独立 AI 第二意见 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_legacy_revise_ai_second_opinion_v1_2026-09-23.md` | 对 34 条 v1-v3 历史 revise 的独立 AI 复核；突出 A01064、A01035、A01695 的事件层级/具体性疑点，不是专家结论，不改变 Gold |
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
| 第七批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v7_remaining_unreviewed_validation_2026-09-23.json` | 第七批候选的结构、证据和未审核门禁校验；已通过，不代表专家审核状态 |
| 第八批专家清单（Markdown） | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v8_remaining_unreviewed_2026-09-23.md` | 50 条待审核清单；逐条展示唯一精确匹配或要求人工定位/补证，并保留完整原文及原始换行 |
| 第八批专家清单（Word） | `evaluation/quality_eval/runs/siemens_s210_causal_relation_expert_review_checklist_v8_remaining_unreviewed_2026-09-23.docx` | 可编辑的逐条专家审核表，包含 50 条候选、完整原文、引用状态和空白审核项 |
| 第八批候选校验报告 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v8_remaining_unreviewed_validation_2026-09-23.json` | 对唯一匹配重新计算并验证原文 quote/offset，同时与权威来源数据逐字段核对；确认待人工定位的证据为空、Gold/FTA 门禁关闭；不代表专家审核状态 |
| 第八批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v8.py` | 从 `gold_records.causes` 独立定位原文，不依赖模型证据数组索引；只绑定唯一匹配，未匹配/重复匹配保持人工处理 |
| 第八批证据定位模块 | `evaluation/quality_eval/public_sources/causal_relation_evidence_binding.py` | 仅作 Unicode、大小写、空白及换行连字符规范化后精确匹配，并返回原文字符偏移；拒绝只匹配到 Unicode 展开字符片段的情况；不做模糊或语义猜测 |
| 第八批校验器 | `evaluation/quality_eval/public_sources/validate_siemens_s210_causal_relation_candidates_v8.py` | 重算证据匹配并核对权威来源数据指纹及候选字段，拒绝来源文本被改写、错引文、错偏移、歧义证据被绑定及人工候选被提前填证据 |
| 第八批 Word 导出器 | `evaluation/quality_eval/public_sources/export_siemens_s210_causal_relation_review_bundle_docx.py` | 先对照权威来源校验，再生成可编辑 Word 专家审核表 |
| 第八批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v8.py` | 覆盖唯一匹配、无匹配、多处重复、Unicode 展开边界、换行引用展示、来源篡改拒绝、跨批去重、账目和 DOCX 导出 |
| 第七批 AI 预审摘要 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v7_ai_pre_review_2026-09-23.json/.md` | 子代理完成 50 条 AI 初筛并标出 15 条优先复核项；仅供专家审核排序，不作 Gold 决策 |
| 第八批 AI 预审结果 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v8_ai_pre_review_2026-09-23.md` | 独立 AI 子代理完成 50 条语义初筛（32 较像因果、17 关联/状态、1 方向不明）；不构成专家意见、不进入 Gold；5 条证据仍待人工定位 |
| 第七批 AI 独立二次意见（全量） | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v7_ai_second_opinion_2026-09-23.md` | 多名 AI 子代理复核 50 条：31 较像因果、11 较像关联/状态、7 需专家判断、1 倾向不作因果边；不是专家决议，不进入 Gold |
| 第七批 AI 独立二次意见（历史快照） | `evaluation/quality_eval/runs/siemens_s210_causal_relation_candidates_v7_ai_second_opinion_partial_2026-09-23.md` | 仅覆盖 10/50 条的中间快照，已被全量二次意见取代，不得作为当前全批结论 |
| 第五批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v5.py` | 排除 v1-v4 已审核候选并按故障码轮询生成第五批 |
| 第五批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v5.py` | 校验第五批不重复、数量和证据结构 |
| 第六批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v6.py` | 排除 v1-v5 已审核候选并按故障码轮询生成第六批 |
| 第六批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v6.py` | 校验第六批不重复、数量和证据结构 |
| 第七批生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_review_bundle_v7.py` | 排除 v1-v6 已审核候选并按故障码轮询生成第七批 |
| 第七批生成器测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_review_bundle_v7.py` | 锁定 296/745/1041 数量、跨批去重、专家字段和未就绪门禁 |
| 第五批修订包 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_v5.json` | 保存 A01691、A01782 两条 revise 候选及专家建议，未进入 Gold |
| 第五批修订清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_v5_2026-09-22.md` | 供刘武复核原因文本和 A01782 证据定位 |
| v6 修订确认包 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu.json` | A01691、A01782 的专家确认表单，保持 pending，不代表 Gold 批准 |
| v6 修订确认清单 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu_2026-09-23.md` | 供刘武逐条填写最终原因、证据、因果状态、方向、关系类型和 FTA 资格 |
| v6 修订确认 Word | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v6_LiuWu_2026-09-23.docx` | 可下载填写的专家确认单 |
| v6 修订确认生成器 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_revision_confirmation_v6.py` | 从 v5 pending 修订包生成 JSON、Markdown 和 Word 确认单 |
| v6 修订确认测试 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_revision_confirmation_v6.py` | 校验两条记录保持 pending 且建议证据不覆盖当前错误证据 |
| 六条 revise 确认包 v7 | `evaluation/quality_eval/datasets/siemens_s210_causal_relation_revision_confirmation_v7_LiuWu.json` | 汇总 v5 的 2 条与 v6 的 4 条 revise，逐条保留前次专家意见、AI 预审参考、原文证据及同故障 Gold 关系；专家填写字段为空，不能直接合并 |
| 六条 revise 确认清单 v7 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v7_LiuWu_2026-09-23.md` | 供专家逐条确认最终原因、证据、因果状态、方向、FTA 资格和结论 |
| 六条 revise 确认 Word v7 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_confirmation_v7_LiuWu_2026-09-23.docx` | 已用本机 Microsoft Word 导出并检查 19 页；专家填写字段为空且内容可读，但第 4、7、10、13、16 页只剩填写表尾部字段，版式待修；修复前可使用 Markdown 版 |
| 六条 revise 确认生成器 v7 | `evaluation/quality_eval/public_sources/build_siemens_s210_causal_relation_revision_confirmation_v7.py` | 对照 v5/v6 具名审核原件、当前候选、Gold v7 和 AI 预审，生成保持 pending 的六条确认包 |
| 六条 revise 确认生成器测试 v7 | `evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_relation_revision_confirmation_v7.py` | 验证六条范围、pending 状态、证据偏移和 Gold/FTA 门禁 |
| AI 模拟预审结果 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_ai_pre_review_v1_2026-09-23.json/.md` | 独立智能体对两条 revise 的准备性意见；不属于专家 Gold，不得直接合并 |
| 六条 revise 的 AI 独立预审 | `evaluation/quality_eval/runs/siemens_s210_causal_relation_revision_ai_pre_review_v2_2026-09-23.json/.md` | 对 A01691、A01782、A30730、F01001、F01640、F01641 的准备性意见；不属于专家结论，不能合并 Gold |
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
- 205 条关系通过命名专家批准门禁；91 条在排除/暂缓清单中，细分为 40 条 `revise`、40 条 `cannot_determine`、11 条 `reject`；
- 第六批 42 条批准进入正式 Gold；4 条 revise 和 4 条 reject 未进入 Gold；
- 40 条 revise 尚未全部关闭：现有六条确认包只覆盖 v5 的 A01691、A01782 与 v6 的 A30730、F01001、F01640、F01641；另 34 条 v1-v3 历史 revise 尚未找到后续专家关闭记录；
- 两份独立 AI 预审意见不能代替具名专家复核；第二意见特别指出 A01064、A01035、A01695 可能被过度排除或需要事件层级判断，须在专家确认材料中单列；
- AI 临时 Gold v7 是独立的 provisional 文件，不是本次正式 Gold v7 的来源；
- `causal_relations_complete=false`；
- `logic_gates_complete=false`（F01611 仍为 `unknown`）；
- `fta_ready=false`，`runtime_registry_updated=false`。

累计候选账目闭合：`1041 = 296 reviewed + 745 unreviewed`；已审核范围内 `296 = 205 approved relations + 91 excluded_or_pending`。Gold v7 覆盖 132 个目标故障，其中 40 个目标故障有至少两条已批准因果关系。当前生成的 5 个 OR 事件 FTA Preview 仅用于查看和合同验证，不得写入生产树注册表；整体 FTA 尚未就绪。

**正式因果关系 Gold 尚未入库，不能把当前 JSON 误称为已入库。** 截至 2026-09-23 的只读 SQLite 核查显示，基础故障记录数据集 `siemens_s210_public_fault_full_review_queue`（版本 `2026-09-20`）已有 281 条导入记录、281 条关联故障记录和 2847 条关联证据跨度；这只是故障记录工作流导入，不代表 Gold v7 的 205 条因果关系已入库。当前 SQLite schema 没有专用因果关系表，不能完整保存稳定的 relation/candidate ID、因果方向、专家审核状态、关系证据映射和 Gold 版本审计。后端 Neo4j 通用建图代码按事件名称写入 `Failure` 节点和 `CAUSES` 边，也不能直接作为正式 Gold 导入器。本次没有检查 Neo4j 实例中的现存图数据。全量审核完成后，应先确定 SQLite Gold 真源与 Neo4j 图投影的存储合同，再定义幂等导入/回读对账；不得把部分 Gold 或 AI provisional 数据提前写成正式知识。

## 下一阶段目标

### 当前状态更新（2026-09-23，V8 候选包生成后）

Gold v7 仍是正式版本，统计和门禁未变：205 条批准关系、91 条排除/暂缓、296 条已记录专家决议、745 条尚未获得专家决议；40 条 `revise` 仍未全部关闭。候选包 V1-V7 共 346 条，另新增 V8 50 条，故累计打包 396 条，其中 V7/V8 共 100 条仍待具名专家审核，尚未打包 645 条。V8 中 45 条具备唯一规范化精确匹配，5 条无精确匹配，保持无绑定证据并待人工定位/补证。独立 AI 子代理的语义预审已完成（32 较像因果、17 关联/状态、1 方向不明），逐条意见仅用于专家审核排序，不改变任何专家状态。

V8 只在候选文本经大小写、Unicode、空白及换行连字符规范化后于完整 `input_text` 中唯一出现时自动绑定引文，并由专用校验器重新定位验证。零匹配或多处匹配均不自动选择引文；具名专家补充直接支持的原文及准确字符范围并通过校验前，不得合并 Gold。唯一文本匹配仅证明引文出处和偏移，不替代对因果语义的专家判断。

V8 对账字段显式记录 `packaged_candidate_count_after`，并校验“累计已打包 = 已有专家决议 + 当前待审”及“来源候选 = 累计已打包 + 未打包”，避免把上一批打包数与加入本批后的待审数混为同一时点。

以下“下一阶段”详细计划最初以 V7 为上下文编写；其中 V7 审核项仍有效，另须将 V8 纳入同等专家审核与验收。

当前目标为 **Causal Relation Coverage Expansion v2**：保持 Gold v7 正式门禁，先对 40 条 `revise` 完成逐条关闭记录，再对第七批 50 条候选完成专家审核。现有六条 revise 确认 JSON/Markdown 只覆盖 v5/v6 的 6 条；Word 已完成 19 页渲染检查，但 5 页填写表尾部被拆页，修复前可使用 Markdown 版。剩余 34 条 v1-v3 revise 必须单独核对原专家意见并补充明确复审结论，不能沿用 AI 预审直接关闭。第七批 AI 初筛已完成，但第七批仍待专家审核。因此 Gold 仍为 296 条已记录决议/745 条未审候选；“已记录决议”中仍含 40 条未关闭 revise，不能把候选包生成或 AI 初筛计作完成审核。

### 目标范围

- V8 更新：第八批 50 条已生成，45 条自动唯一匹配、5 条待人工定位/补证；两种情况都等待刘武逐条审核，自动文本匹配不能代替因果语义判断。
- 待修订集合：共 40 条，完整候选 ID 与故障码见 `siemens_s210_causal_relation_gold_v7_revise_backlog_audit_2026-09-23.md`。其中六条已有统一专家确认包，34 条 v1-v3 历史项仍待整理复审材料。全部 40 条均不得直接进入正式 Gold；每条需确认最终原因文本、证据映射、与现有 Gold 是否重复及完整批准门禁。AI 预审只能作为独立参考。
- 第七批：从 745 条未审核候选中按既有去重和轮询策略选择的 50 条候选，已经生成候选包、字符级证据、专家清单并通过结构校验；仍等待审核结论。
- 每条审核结果继续保留 `causal_status`、`direction`、`relation_type`、`fta_eligible`、`overall_decision`、证据和专家意见。

### 验收条件

- 正式 Gold 只允许真实命名专家 `approve` 的关系进入；AI 模拟关系只能进入临时视图。
- 新批次与前序候选不重复，证据引用和字符位置通过校验。
- `reviewed_candidate_count`、`unreviewed_candidate_count`、Gold 数量和排除/暂缓数量能够对账。
- `causal_relations_complete=false`、`logic_gates_complete=false`、`fta_ready=false` 继续保持，直到全量关系和逻辑门门禁完成。

### 停止条件

V8 的零匹配或多处匹配候选必须保持 `evidence=[]`；只有具名专家在完整原文中提供直接支持的 quote 与准确 `start/end`，且 V8 校验器复核通过后，才可进入后续 Gold 合并审查。

未关闭的 revise 不得晋升 Gold；40 条 revise 均有明确关闭结论前，不得声称待修订已清零；第七批审核材料未通过结构校验前不发给审核；在因果关系全量覆盖和 AND/OR 逻辑门审核门禁完成前，不更新生产树注册表或宣布 FTA 就绪。
