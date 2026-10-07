# F01681 Cause Disposition v2 独立 AI 语义复核

- 样本：`SIEMENS_S210_2019_F01681`
- 复核范围：Cause disposition v2 原文完整运行及来源元数据审计副本
- 复核角色：用户授权的独立 AI 审核角色；**不是 Siemens 真人专家意见，也不是正式 Gold**
- 结论：当前把故障值解释项连接到顶事件的候选边，不能视为已建立的因果关系
- 状态边界：`human_reviewed=false`、`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`

## 主要发现

1. 15 条 `r0949` Fault value 解释是混合内容。多数描述配置冲突或条件，可以保留为通用可能原因候选；但逐项文本主要证明其属于该故障记录/诊断映射，并未逐项直接断言其导致 F01681，更不能证明某台现场设备实际发生。诊断关联不能自动提升为有向因果边。
2. `source_cause_index=1` 在 Fault Extraction 的 evidence 中没有任何 span。后续 disposition/tree 层引文虽然能精确回切，不能补成“抽取阶段证据覆盖完整”。
3. 当前候选结构把这些 Fault value 条件作为顶事件 children，和“无实例观测的查表/诊断映射不得直接连到顶事件”的策略存在冲突；Gate evidence 或候选节点存在本身不等于因果边证据。
4. 顶层原因 scope 的完整性也未闭合：模型 rationale 提到 Remedy 中有 `xxxx=9507`，但候选原因中没有对应项。它可能是单独的 Remedy/configuration 分支，并不自动构成因果子节点；应先与当前 scope 对账，不应宣告完整或自动将它加入树。
5. 现有 offset 经复核可精确回切，输入文本 SHA-256 与原始运行/语料相同，来源 PDF SHA-256、页码 455–457 和 corpus offset `[75195,79293)` 由既有 provenance audit 与语料元数据相互核对一致。注意：原始 v2 运行 artifact 自身的 `source_document_sha256` 是 null；不能说原始运行已携带 PDF 哈希。“引用精确”也不等于“引用在语义上支持因果关系”。

## 建议的处置

- 保留候选运行与全部审计材料，不导入 Gold/数据库。
- 把 fault-value diagnostic mapping 与 causal candidate 分开；在完成政策和结构 owner 修正之前，不接受这些 top-event causal edges。
- 补齐每个抽取 cause 的 evidence-span 覆盖校验，并处理 `xxxx=9507` 遗漏。
- 12 个门 scope 继续 `unknown`；模型 OR/AND 概率不代表真值或设备事件概率。

完整结构化记录见同名 JSON。来源：
[原始运行](siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_2026-09-28.json) ·
[来源审计副本](siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json)
