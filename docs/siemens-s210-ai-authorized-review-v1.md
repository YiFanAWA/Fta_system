# Siemens S210 AI 授权专家角色审核基线 v1

更新时间：2026-09-26

## 1. 当前决策

本阶段按照用户明确授权：**将 AI 待审结果视为本轮审核的最终审核结果**。

该决定只适用于本文件及其关联的 AI 审核快照，不把 AI 冒充为刘武或其他真人专家，也不覆盖既有人工 Gold。所有结果保留以下来源标识：

```yaml
reviewer_provenance: user_authorized_ai_expert_role
human_reviewer_claim: false
review_scope: all_source_candidates
```

因此，本快照可以用于当前开发、数据库测试、检索/因果链路验证；若对外声明为“真人领域专家金标”，仍需另行取得真人签字。

## 2. 审核范围与完整性

| 项目 | 当前结果 |
| --- | ---: |
| S210 源候选总数 | 1,041 |
| AI 授权专家角色已审核 | 1,041 |
| 缺失候选 ID | 0 |
| 多余候选 ID | 0 |
| 重复候选 ID | 0 |
| 证据偏移错误 | 0 |
| 初始数据库逻辑门审核行 | 6 |
| 事件级深审进度（Batch02–Batch97） | 269/281 故障码；1,016/1,041 候选 |

这里区分两层：1,041 条是第一轮候选分类清单覆盖；事件级深审还要把同一故障的完整候选集合、原文证据和 AND/OR 门一起核验。截至 Batch97，第二层仍未全覆盖，剩余 12 个故障码、25 条候选 ID。累计统计只计 Batch02–Batch97，排除独立的 Batch01 初始快照；已复算 96 份批次 JSON，故障码和候选 ID 均无重复。

### 最新批次：Batch97（2026-09-26）

- 本批审核 F01011、F01031、F01033，共 7 条完整 manifest 候选；Beauvoir、Hypatia、Leibniz 三个用户授权 AI 子代理分别完成只读独立复核，主 AI 再核对完整 `input_text`、现有 Gold、manifest/context 和原文跨度。所有结论均明确标记为 AI 审阅，不是真人 Siemens 专家签字；Gold、manifest、父 context 与数据库均未改。
- **F01011 / 5 条候选**：V5“下载被中断”与顶事件同义，主审归为 `causal_summary`、非叶；这与既有人类 Gold v7 的 `causal`/FTA eligible 标注冲突，保留分歧、不覆盖 Gold。V6–V9 为 r0949 fault value 1/2/3/100 的条件性下载中断模式；没有当前设备的 r0949 实测值，因此不把四个枚举模式合成 OR。V7 虽能唯一定位 `[214,293)`，但 manifest 的候选文本、source node 和目标描述字段为空，列为待修记录；V9 manifest 无 evidence，完整唯一条目 `[368,517)` 仅记在本批 overlay，并保留人工身份绑定要求。下载后的 first commissioning 是响应状态，电缆检查、重新下载和版本匹配均属 Remedy，不当作已发生的原因。
- **F01031 / 1 条候选**：OFF in REMOTE 激活时三秒内未收到 sign-of-life，是条件性触发描述，完整句唯一跨度 `[93,177)`；candidate 引号格式与原文不同，保留待人工身份绑定。独立 AI 将单条件逻辑语义称作 `not_applicable_single_cause`，主审核字段继续按项目门禁记 `logic_gate=unknown`；两种说法都不意味着 AND/OR，也都不允许建树。OFF3/IMMEDIATELY 是响应信息，电缆检查是处理建议。
- **F01033 / 1 条候选**：参考表示切换时所需 reference parameter 不得为 0.0，是条件性因果候选；原文完整 Cause 句唯一跨度 `[106,257)`，候选为语义压缩且不逐字出现，保留待人工身份绑定。`r0949` 未提供现场参数读数；See also 参数不作为额外原因。独立复核发现 manifest `source_node_id` 为 `cause:0`、citation id 后缀为 `cause:7`；引文与偏移本身正确，该标识映射问题留待单独核对。
- 三个事件均保持 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 新增树 0 棵。批次不改正式 Gold/数据库，`fta_ready=false`、`production_ready=false`。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch97.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch97.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch97_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch97_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch97_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch97_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch97_2026-09-26.md)。Batch97 单批合同测试 10 项通过；Batch02–Batch97 批次回归 447 项通过；FTA Preview owner 40 项、AI preview integration 1 项、FTA preview contract 1 项、后端 FTA graph contract 4 项、context revalidation 5 项通过；Python 编译和 `git diff --check` 通过（仅报告既有文件的 LF→CRLF 提示）。

**截至 Batch97，按 Batch02–Batch97 的 96 份审核 JSON 复算：**269/281 个唯一故障码、1,016/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 12 个故障码、25 个候选 ID。故障码与候选 ID 均无重复。批次 Preview JSON 共 95 份（Batch02 无对应文件），累计树数仍为 10 棵；本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入正式 Gold；`fta_ready=false`、`production_ready=false`。

### 前一批：Batch96（2026-09-26）

- 本批审核 N30620、N30621、F01003，共 3 条完整 manifest 候选。因子代理本轮遇到使用额度限制，未能返回独立审阅；本批如实记录为主 AI 单审，不声称多代理交叉审核。审阅来源、完整候选集和唯一原文跨度均已核验；Gold、manifest 与数据库未改。
- **N30620、N30621**：Cause 字段分别描述 STO、SS1 已经在监控通道 2 被选中并处于 active，是运行/安全状态说明，不是导致该状态的上游失效原因。AI 建议分类为 `associated_only` / `associated_with` / `undirected`，不作 FTA 叶。引文经单/双引号规范化，原文唯一位置保留在 overlay 并标记待人工身份对齐。
- **F01003**：Cause 描述 memory area 未返回 `READY`，可作为确认延迟的条件性 `causal` / `causes` / `source_to_target` 叶候选。完整原文唯一跨度为 `[101,159)`；原 manifest 引文 `[101,157)` 截断了结尾引号和句点。本批 overlay 仅记录完整唯一跨度且保留待人工身份对齐，不回写既有 Gold。r0949 只标注为 Siemens 内部排查，没有设备实读值，也不引入额外枚举原因。
- 三个事件均保持 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；即使 F01003 有单条条件性原因，也没有事件级门证据或已证明完整的现场根因集合，因此本批不建树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch96.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch96.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch96_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch96_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch96_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch96_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch96_2026-09-26.md)。Batch96 单批合同测试 5 项通过；Batch02–Batch96 跨批次审核测试 437 项通过；FTA Preview owner 40 项、后端 FTA graph contract 4 项通过；Python 编译检查通过。

**截至 Batch96，按 Batch02–Batch96 的 95 份审核 JSON 复算：**266/281 个唯一故障码、1,009/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 15 个故障码、32 个候选 ID。累计范围内故障码与候选 ID 均无重复。94 份批次 Preview JSON 累计仍为 10 棵树。本批未改 Gold/数据库；`fta_ready=false`、`production_ready=false`。

### 前一批：Batch95（2026-09-26）

- 本批审核 A30706、A30709、A30716，共 6 条完整 manifest 候选；Euler、Helmholtz、Bacon 三个用户授权 AI 角色分别独立只读复核一个事件。6 个来源跨度逐项回切且各唯一命中 1 次；候选文本与原文在参数条件、引号或消息码标签上存在归一化差异，均保留唯一上下文并标记人工对齐，不自动绑定。父 Gold、manifest、context 与数据库未改。
- **A30706**：SAM（p9506=0）与 SBR（p9506=2）各有一条 Cause 条件：触发相应安全功能后速度超过设置容差。两条保留为 `causal` / `causes` / `source_to_target` 条件性叶候选；p9506 是手册条件，不是本设备读数。SS1/SS2、SS1/SLS 是每条描述内部的触发场景，不推出顶事件 AND/OR；F30700 是后续停止消息，不作为根因。
- **A30709**：候选 Cause 描述沿路径 SS2E 制动、延时后激活 SOS，AI 独立意见与人工 Gold 一致，归为 `associated_only`、`associated_with`、`undirected`、非叶。`Possible causes` 下的 A30714/A30716 是后续响应交叉引用，不是上游故障原因。
- **A30716**：Cause 候选说明安全运动方向容差超限；作为 `causal_summary` 保留 `causes` / `source_to_target` 关系，但不重复建为独立 FTA 叶。r2124 的 `0=正向`、`1=负向` 是码义而非当前设备读取值，V6/V7 归为无方向的码义关联。V5、V6 的 AI 分类/叶资格与既有人类 Gold 冲突；V7 只与非人工 manifest 状态比较。本批记录差异、不覆盖 Gold。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。未从条件内 `or`、消息值枚举或后续消息推断事件级门；处理建议与确认步骤未当作根因。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch95.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch95.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch95_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch95_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch95_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch95_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch95_2026-09-26.md)。Batch95 单批合同测试 7 项通过；Batch02–Batch95 跨批次审核测试 432 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过；Python 编译检查通过。

**截至 Batch95，按 Batch02–Batch95 的 94 份审核 JSON 复算：**263/281 个唯一故障码、1,006/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 18 个故障码、35 个候选 ID。累计范围内故障码与候选 ID 均无重复。93 份批次 Preview JSON 累计仍为 10 棵树。本批未改 Gold/数据库；`fta_ready=false`、`production_ready=false`。

### 更早批次：Batch94（2026-09-26）

- 本批审核 A13032、A13033、A30042，共 8 条完整 manifest 候选；Parfit、Planck、Kuhn 三个用户授权 AI 角色分别独立只读复核一个事件。候选 8 个来源跨度与 prior context 中 10 个跨度均逐项回切核验；父 Gold、manifest、context 与数据库未改。
- **A13032、A13033**：Cause 分别描述试用许可末期临近、最后期限已过，属于告警/许可状态摘要，不是可分离的物理故障叶；AI 角色复核与既有人类 Gold 的 `causal`/`fta_eligible=true` 标签冲突。本批保留冲突，不覆盖人工 Gold。候选使用单引号，原文是双引号，逐字候选匹配为 0；完整原文句分别在 `[83,173)`、`[81,174)` 唯一匹配，本批仅留作可能上下文并标记人工对齐，不自动绑定。
- **A30042**：V4 Cause 是寿命阈值告警摘要；V5/V6/V7/V8/V9 分别映射 r2124 Bit 0/1/2/8/10，均是报警编码解释，不是现场 bit 读数，也不证明风扇已经物理失效。V4/V5/V6 与既有人类 Gold 的分类/叶资格有冲突，V9 只与非人工 manifest 状态不同；均只记入审计，不改正式 Gold。V6 候选以分号归一化了原文两句，原文精确短语 `[447,536)` 唯一出现，旧 manifest 引用 `[447,534)` 截断；本批 overlay 留存完整 Bit 1 上下文 `[436,617)` 并标记人工对齐。用户此前对 F31120 的确认同样适用：没有现场读数时，位/值定义保留为条件/诊断模式，不能从枚举推出 OR/AND。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。A30042 Bit 2 的 `and/or` 只属于该编码项描述，不能当作事件级门。更换风扇、复位计数器等 Remedy 不作故障原因或当前设备测量值。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch94.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch94.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch94_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch94_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch94_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch94_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch94_2026-09-26.md)。Batch94 单批合同测试 7 项通过；Batch02–Batch94 跨批次审核测试 425 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过；Python 编译检查通过。

**截至 Batch94，按 Batch02–Batch94 的 93 份审核 JSON 复算：**260/281 个唯一故障码、1,000/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 21 个故障码、41 个候选 ID。故障码与候选 ID 均无重复。92 份批次 Preview JSON 累计仍为 10 棵树。本批未改 Gold/数据库；`fta_ready=false`、`production_ready=false`。

### 更早批次：Batch93（2026-09-26）

- 本批审核 A07091、A13030、A13031，共 7 条完整 manifest 候选；Bernoulli、Darwin、Carson 三个用户授权 AI 角色分别独立只读复核一个事件。候选共 7 个来源跨度，prior context 中 8 个跨度逐项回切核验。Gold、manifest、父 context 与数据库均未改；只生成本批 overlay、审核与 Preview 文件。
- **A07091**：V5“incorrectly set current controller”和 V6“PRBS amplitude set too high”位于原文 `Possible causes` 列表，保留为条件性因果叶候选；V4 是调试/测量流程背景；V7/V8 是 r2124 报警值映射结果，不是当前读数或上游原因。两条可能原因并列不足以判定顶层 OR/AND，原因全集也未证明穷尽。V4 候选文本省略原文 `(p5300 = 1)`，本批仅保存可能上下文跨度并标记待人工核对，不自动绑定。
- **A13030、A13031**：两条 Cause 都描述试用许可激活/期限临近或到期状态，与通知标题语义重叠；独立 AI 复核判为 `causal_summary`、非 FTA 叶。现有 manifest 的 human Gold v7 把它们标为 `causal` 且 `fta_eligible=true`，本批将冲突作为审计信息保留，不覆盖既有人工 Gold；应由真人专家决定是否修订正式标注。两条引文在原文均唯一回切，context 原有规范化匹配失败只在本批 overlay 中记录。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。没有从两个 `Possible causes` 推 OR，也没有从 Remedy 参数或状态信息推当前现场条件。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch93.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch93.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch93_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch93_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch93_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch93_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch93_2026-09-26.md)。Batch93 单批合同测试 9 项通过；Batch02–Batch93 跨批次审核测试 418 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过；Python 编译与 `git diff --check` 通过（Git 仅提示工作区既有文件的 LF→CRLF 规范化）。

**截至 Batch93，按 Batch02–Batch93 的 92 份审核 JSON 复算：**257/281 个唯一故障码、992/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 24 个故障码、49 个候选 ID。累计范围内故障码与候选 ID 均无重复。91 份批次 Preview JSON 累计仍为 10 棵树。本批未改 Gold/数据库；`fta_ready=false`、`production_ready=false`。

### 更早批次：Batch92（2026-09-26）

- 本批审核 F40000、N01620、N01621，共 3 条完整 manifest 候选；Descartes、Curie、Anscombe 三个用户授权 AI 审核角色分别独立复核一个事件。候选证据 3 个跨度均在完整 `input_text` 中唯一精确回切；prior context 可回核的 2 个跨度也逐一验证。N01620/N01621 旧 context 因候选引文规范化差异而没有绑定证据，本批只在 scoped overlay 中恢复唯一原文跨度，未修改父 context。Gold、manifest 与数据库未改。
- **F40000**：候选 `CR-CAND-V16-290` 的 Cause 句只是重述“DRIVE-CLiQ socket X100 处 drive object 已发生故障”的状态，不是独立上游原因；归为 `associated_only`、不具备 FTA 叶资格。r0949 后的“first fault”是字段解释，不是当前设备实际读数；读取故障缓冲区属于 Remedy。
- **N01620**：候选描述 STO 已经选中且激活，是状态/通知，不是上游根因。原文写明 `Reaction: NONE`，并明确该消息“不导致安全停止响应”；Extended Functions 的说明是消息适用条件，不是原因或逻辑门证据。
- **N01621**：候选描述 SS1 已选中且激活，是状态/通知，不是上游根因。原文明示该消息不导致安全停止响应；不能把“active”改写成现场安全停车已发生。
- 三个事件都没有独立原因集合、现场参数/遥测读数或事件级布尔方程，均为 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。所有结果是用户授权 AI 角色复核，不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch92.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch92.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch92_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch92_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch92_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch92_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch92_2026-09-26.md)。Batch92 单批合同测试 9 项通过；Batch02–Batch92 跨批次审核测试 409 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过；Python 编译与 `git diff --check` 通过（Git 仅提示工作区既有文件的 LF→CRLF 规范化）。

**截至 Batch92，按 Batch02–Batch92 的 91 份审核 JSON 复算：**254/281 个唯一故障码、985/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 27 个故障码、56 个候选 ID。累计范围内故障码与候选 ID 均无重复。90 份批次 Preview JSON 累计仍为 10 棵树。本批未改 Gold/数据库；`fta_ready=false`、`production_ready=false`。

### 前一批：Batch91（2026-09-26）

- 本批审核 F31886、F31895、F31896，共 6 条完整 manifest 候选；Schrodinger、Bohr、Boole 三个用户授权 AI 审核角色各独立只读复核一个事件。候选证据共 7 个精确跨度，旧 context 的 10 个跨度均逐一回切核验。父 Gold、manifest、context 与数据库未改。
- **F31886**：Cause 通信错误句保留为摘要，不作为独立叶；单一 Fault cause 65 (= 41 hex) 映射到“Telegram type does not match send list”，作为条件性模式叶候选。`Data were not able to be sent` 是结果，不是上游原因。没有当前 r0949/r2124 读数。
- **F31895**：Cause 通信错误句为摘要；单一 Fault cause 11 (= 0B hex) 映射到交替循环数据传输同步错误，保留为条件性模式叶候选。没有现场消息值。
- **F31896**：V16 节点身份指向“组件属性不兼容”状态摘要，但旧 manifest evidence 指向下一候选的“电缆/组件已更换”可能原因句。两处精确位置 `[115,301)`、`[303,392)` 均保留，标记 `candidate_identity_evidence_conflict_manual_review_required`，不自动绑定；V16 不形成因果边。V17 作为原文明确支持的非穷尽条件性可能原因保留。r0949 仅说明 Fault value 是组件编号，没有当前设备编号，也未证明原因集合完整。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。依用户对 F31120 的明确确认，无现场参数/故障值读数时不从位/值说明推 OR/AND；句内 `or` 也不直接变成事件门。

截至 Batch91，Batch02–Batch91 共 90 份审核 JSON：251/281 个唯一故障码、982/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 30 个故障码、59 个候选 ID。89 份批次 Preview JSON累计仍为 10 棵树。本批 9 项合同测试通过；Batch02–Batch91 跨批次回归 400 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过。AI 审核角色不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch91.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch91.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch91_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch91_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch91_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch91_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch91_2026-09-26.md)。

Batch91 之后剩余范围为 30 个故障码、59 条候选 ID。Batch02–Batch90 的逐批明细作为历史记录保留在后续章节。

### 前一批：Batch90（2026-09-26）

- 本批审核 F31851、F31860、F31885，共 26 条完整 manifest 候选；三位用户授权 AI 审核角色各独立复核一个事件。共保留 41 个候选/编码证据跨度；其中重复短语的 8 个候选位置及其 8 个编码块全部列出，不自动择一。旧 context 中可回核的 50 个跨度也重新核验。父 Gold、manifest、context 与数据库未改。
- **F31851**：通信故障总述和“组件未发送 sign-of-life”作为因果摘要/中间条件；Fault cause 10 (= 0A hex) 的接收报文 sign-of-life 位未置位保留为条件性模式。无现场 r0949/r2124 读数。
- **F31860**：Cause 为上位通信错误摘要；15 条可见 Fault cause 编码行均被候选覆盖并保留为条件性模式。`CR-CAND-V20-088` 的短语 `receive telegram is too early.` 在 8 个编码块重复，全部候选位置及对应编码行均保留并标记待人工定位；该候选暂不具备 FTA 叶资格。没有本次设备实际消息值；编码空档不补造语义；条目内 and/or 不推事件门。
- **F31885**：通信错误和节点不同步作为摘要/中间条件；26、33、34、64、98 五条 Fault cause 编码均有候选覆盖。码 26 描述中的 and 是单项编码语义，不等于事件顶层 AND；其余枚举并列也不推出 OR。
- 三个事件均无现场诊断值，`cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数 0。Reaction、Acknowledge、Remedy 都与原因候选分开。

截至 Batch90，Batch02–Batch90 共 89 份审核 JSON：248/281 个唯一故障码、976/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 33 个故障码、65 个候选 ID。88 份批次 Preview JSON累计仍为 10 棵树。本批 9 项合同测试通过；Batch02–Batch90 跨批次回归 391 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过。AI 审核角色不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch90.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch90.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch90_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch90_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch90_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch90_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch90_2026-09-26.md)。

Batch90 之后剩余范围为 33 个故障码、65 条候选 ID。Batch02–Batch89 的逐批明细作为历史记录保留在后续章节。

### 前一批：Batch89（2026-09-26）

- 本批审核 A01709、A01716、A01782，共 8 条完整 manifest 候选；三位用户授权 AI 审核角色各独立只读复核一个事件。候选证据新增 8 个精确跨度；旧 context 中可回核的 6 个跨度也逐一复核。父 Gold、manifest、context 与数据库未改。
- **A01709**：Cause 两句描述 SS2E 停止状态及定时后 SOS 状态，均不作为上游原因叶；`Possible causes:` 列表为空。A01714/A01716 明确是 subsequent/following messages，保留为后续消息关系线索，不反向认作原因；p9553 是参数引用，不是现场读数。
- **A01716**：Cause 总述作为事件条件摘要、不作基本叶；r2124 十进制值 0/1 分别保留为正向/负向 SDI 容差超限的条件性模式候选。未见本次设备 r2124 实际值，0/1 并列不能推出 OR/AND。
- **A01782**：Cause 句保留为 `causal_summary`，不作独立叶；Alarm value 0 和 Bit 2 保留为条件性因果模式。Bit 0/Bit 1 在原文可见且出现在模型预测中，但未进入 Gold/manifest 的 3 条候选集，本轮只登记覆盖差异，不擅自新增候选。Bit 2 原文含重复词 `configured`，Gold/context 文本规范化且 manifest 缺稳定 `source_node_id`，因此保留条件性关系但不授权为树叶。A01785 是同时输出的伴随消息，不是 A01782 的原因。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。按用户确认的原则，不从诊断码/报警位枚举推导 OR/AND。

截至 Batch89，Batch02–Batch89 共 88 份审核 JSON：245/281 个唯一故障码、950/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 36 个故障码、91 个候选 ID。87 份批次 Preview JSON 累计仍为 10 棵树。本批 9 项合同测试通过；Batch02–Batch89 跨批次回归 382 项通过；context revalidation 5 项、FTA Preview owner 40 项、后端 FTA graph contract 4 项通过。用户授权 AI 复核不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch89.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch89.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch89_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch89_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch89_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch89_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch89_2026-09-26.md)。

Batch89 之后剩余范围为 36 个故障码、91 条候选 ID。Batch02–Batch88 的逐批明细作为历史记录保留在后续章节。

### 前一批：Batch88（2026-09-25）

- 本批审核 F31837、F31845、F31850 共 18 条候选，新增候选/编码来源跨度 36 个，在完整原文中精确回切；旧 context 中可回核的 34 个跨度也逐一复核。父 Gold、manifest、context 与数据库未改。
- F31837：32、35、66、67 四个 Fault cause 编码由三条候选覆盖；66 与 67 的发送错误描述相同。CR-CAND-V18-161 保留两个原文位置和两条独立编码行，manual_review_required=true，不选某一处作为唯一位置。Cause 中“Faulty hardware cannot be excluded”保持可能性摘要，不升级为已确认硬件根因。
- F31845：Cause 总述为 causal_summary、不作为基本叶；11 (= 0B hex) 同步错误保留为条件性候选叶。没有实际 r0949/r2124 读数。
- F31850：Cause 总述为 causal_summary；12 个 r0949 Fault value 描述按独立 AI 复核保留为条件性模式候选。旧 manifest 中 7 条分类/叶资格不同，作为本轮差异记录，不回写 manifest。旧 context 的数值范围截窗以完整 input_text 编码行重新取证。
- 三个事件均 cause_set_complete=false、logic_gate=unknown、build_allowed=false；本批 Preview 树数为 0。审核遵守用户在 F31120 上确认的门逻辑原则：r0949 位/值枚举本身不能推出 OR/AND。

截至 Batch88，Batch02–Batch88 共 87 份审核 JSON：242/281 个唯一故障码、942/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 39 个故障码、99 个候选 ID。86 份批次 Preview JSON 累计仍为 10 棵树。本批 15 项合同测试通过；Batch02–Batch88 全批次合同回归 373 项通过。用户授权 AI 复核不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch88.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch88.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch88_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch88_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch88_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch88_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch88_2026-09-25.md)。

Batch88 之后剩余范围为 39 个故障码、99 条候选 ID。Batch02–Batch87 的逐批明细作为历史记录保留在后续章节。

### 前一批：Batch87（2026-09-25）

本批审核 F31813、F31820、F31835 共 18 条候选。候选引文及对应 Bit/Fault cause 编码行共 33 个跨度，在完整 `input_text` 中唯一精确回切；旧 context 的 cause 与 cause_context 共 36 个跨度重新核验。9 条 manifest evidence 缺少 `source_id`，仅在其引文和偏移与 context 绑定的原文证据完全相等后，才在本批 overlay 中解析来源身份；父 manifest/context 未改。

- **F31813 / 3 条候选**：Cause 句是顶事件状态摘要；两条 r0949 Bit 定义保留为诊断关联，不当作现场已发生原因或 FTA 叶。没有实际位值，位定义并列也不证明 OR/AND。
- **F31820 / 11 条候选**：Cause 总述作为通信错误摘要；10 个 `Fault cause` 编号文本保留为条件性故障模式候选。没有当前 `r0949/r2124` 读数；可见编号未解释 `0A–0F`，因此不能宣称原因全集闭合，也不能从枚举推出 OR 门。
- **F31835 / 4 条候选**：Cause 总述为上位通信状态摘要；33、34、64 三个 Fault cause 编码保留为条件性候选模式，不代表现场实测。manifest 对 V16 的叶资格标记与本轮独立复核不同，作为差异记录，不回写来源数据。
- 三个事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批 Preview 树数为 0。独立角色审核是用户授权的 AI 复核，不是真人西门子专家签署；Gold、manifest、基础 context 和数据库均未修改。

截至 Batch87，Batch02–Batch87 共 86 份审核 JSON：239/281 个唯一故障码、924/1,041 个唯一候选 ID 已完成事件级 AI 审核；还剩 42 个故障码、117 个候选 ID。85 份批次 Preview JSON 累计仍为 10 棵树。本批 14 项合同测试通过；Batch02–Batch87 全批次合同回归 358 项通过；FTA Preview owner 40 项、context revalidation 5 项及后端 FTA graph contract 4 项通过。AI 角色审核不是真人 Siemens 专家签署。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch87.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch87.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch87_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch87_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch87_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch87_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch87_2026-09-25.md)。

完整审核清单由 V1–V21 候选批次合并生成，唯一候选 ID 覆盖源候选全集。当前主清单为：

`evaluation/quality_eval/runs/siemens_s210_ai_authorized_full_causal_review_manifest_v1_2026-09-23.json`

结构验证结果为：

`evaluation/quality_eval/runs/siemens_s210_ai_authorized_full_causal_review_manifest_v1_validation_2026-09-23.json`

V21 的原始声明哈希与当前原始文件哈希不一致，但该批 45 条候选的源上下文逐条匹配成功；因此 V21 结果可用于当前 AI 审核快照，同时保留为数据版本审计警告，后续应补做源文件指纹对齐。

## 3. 审核结果分布

| 审核状态 | 数量 | 含义 |
| --- | ---: | --- |
| `causal` | 815 | 可作为候选因果关系使用，但仍受 FTA 全局门禁约束 |
| `causal_summary` | 14 | 有因果含义，但属于事件摘要/条件节点，默认不直接作为基本事件 |
| `associated_only` | 121 | 有关联或共现依据，不作为独立因果边 |
| `cannot_determine` | 78 | 当前证据不足或存在歧义，保留待后续补证 |
| `not_supported` | 13 | 原文证据不足以支持该候选 |
| **合计** | **1,041** | **账目闭合** |

其中，复核阶段的 `revise` 已通过 AI 授权专家角色的闭环补充处理；补充结果分别保存在：

- `evaluation/quality_eval/runs/siemens_s210_ai_review_revision_closure_v1_2026-09-23.json`
- `evaluation/quality_eval/runs/siemens_s210_v15_v17_ai_review_revision_closure_v1_2026-09-23.json`
- `evaluation/quality_eval/runs/siemens_s210_and_or_ai_review_revision_closure_v1_2026-09-23.json`

证据无法唯一定位时，采用已确认的保守规则：**不自动猜引文，不自动绑定证据；保留为待补证/无法确定状态**。

事件级门逻辑补充确认：用户已确认 F31120 的 r0949 位/值说明没有现场读数时，只能保留为条件性模式，`logic_gate` 必须保持 `unknown`，不能据此推断 OR/AND。

## 4. AND/OR 审核状态

以下表格记录的是初始逻辑门审核基线及早期批次（不是截至当前的全量事件门状态）；后续 Batch02–Batch70 的逐故障事件级审核覆盖与差异见第13–43节。A01631 在该历史阶段为冲突暂缓：

| 故障/事件 | AI 授权专家角色结论 |
| --- | --- |
| A01069 | `not_applicable` |
| A01631 | 历史 AI 角色审核为 `AND`；与既有人类 Gold `OR` 冲突，且组合候选证据待人工定位，批次12暂缓，不作当前定论 |
| A01981 | `OR` |
| A07094 | `OR` |
| A30714 | `OR` |
| F01611 | `unknown` |
| A01590 | `not_applicable` |
| A01637 | `unknown`（保留为单一复合状态；不把语法 and 推断成 FTA 门） |
| A01638 | `not_applicable`（成功状态消息，不是因果故障） |
| A01654 | `OR`（仅限 r2124=1/2 两种配置不匹配状态） |
| A01691 | `OR`（等时/非等时模式结构；V5 修订未闭合，暂不建树） |
| A01693 | `not_applicable`（安全参数变更触发重启提示；单一条件） |
| A01695 | `not_applicable`（传感器模块更换通知；associated_only，不是失效原因） |
| A01696 | `not_applicable`（启动时测试停止程序已选中；单一条件） |
| A01697 | `unknown`（p9559超时与启动后报警说明的组合关系未明确） |
| A01707 | `not_applicable`（位置偏离静止容差；F01701为下游停止消息） |

`F01611` 在该历史阶段保持 `unknown`，不允许为了生成树而猜测逻辑门。即使后续某些事件有新的独立复核，也只有事件级证据完整、门与叶结构均闭合时才允许 Preview；逻辑门全量覆盖仍未完成。

## 5. 数据库存储与回读

AI 审核快照已独立写入 SQLite，不修改既有人工 Gold：

```text
数据库：backend-python/outputs/extraction_workflow.sqlite3
schema user_version：5
因果审核 manifest：1
候选审核行：1,041
逻辑门审核行：6
```

导入采用事务、版本/内容哈希冲突保护和幂等检查。当前导入回读报告为：

`evaluation/quality_eval/runs/siemens_s210_ai_authorized_full_causal_review_import_2026-09-23.json`

报告确认：

- `status=completed`
- `readback_status=completed`
- `readback_candidate_ids_unique=true`
- `human_gold_mutated=false`
- 二次导入返回 `inserted=false`，数量和内容哈希保持一致

数据库备份位于：

`backend-python/outputs/extraction_workflow_before_causal_review_v1_retry_2026-09-23.sqlite3`

只读核查还观察到基础 `fault_records` 表当前有 283 行，而历史数据说明常写 281 条；这属于既有数据库口径差异，本轮没有擅自删除或重算。它不影响本次因果 manifest 的 1,041 条候选对账，但后续应单独建立基础故障记录数据集注册表，解释 281/283 的来源和版本关系。

第一次导入因逻辑门字段映射错误而回滚，修正映射后重试成功；回滚没有留下半成品数据。

## 6. 生产门禁

当前必须保持：

```yaml
causal_relations_complete: false
logic_gates_complete: false
fta_ready: false
```

原因是：

1. “1,041 条候选已完成审核”不等于“1,041 条都是独立因果关系”；其中包含关联、无法确定、摘要节点和不支持项。
2. 初始数据库逻辑门表只有 6 行；事件级审核截至 Batch87 覆盖 239/281 个故障码，仍有 42 个未覆盖；全量事件原因集合与逻辑门尚未闭合。
3. 当前结果可以进入因果审核数据库和 FTA Preview 验证，但不能自动写入生产故障树注册表。

## 7. 与既有人工 Gold 的关系

既有人工 Gold v7 原文件保持不变。AI 授权审核是独立快照，不覆盖、不回写、不改名为人工 Gold。

当前系统同时保留两条事实线：

```text
人工 Gold v7
  → 历史人工审核事实

AI Authorized Review v1
  → 用户明确授权后用于本轮开发/入库/评测的完整审核快照
```

后续如需合并两者，必须通过显式的 precedence 规则和审计报告，不允许直接覆盖原文件。

## 8. 验收命令与结果

Batch87 本轮验收：批次专属合同测试 14 项通过；Batch02–Batch87 全批次合同回归 358 项通过；FTA Preview owner 40 项、context revalidation 5 项及后端 FTA graph contract 4 项通过。批次生成器与测试文件 `py_compile` 通过。全量批次对账为 86 份审核 JSON、239 个唯一故障码、924 个唯一候选 ID，无重复；85 份 Preview 累计 10 棵树。本批 `git diff --check` 通过。

本轮已执行：

```powershell
python -m unittest discover -s backend-python/tests -p 'test_*.py' -v
```

结果：前一轮为 `187 tests OK`；本次因果上下文证据接入后重新执行，结果为 `194 tests OK`。

并执行：

```powershell
python -m compileall -q backend-python/contracts backend-python/extraction evaluation/quality_eval/public_sources
```

结果：通过。

AI 完整审核清单验证结果：`status=valid`；源候选 1,041 条、清单 1,041 条、唯一 ID 1,041 条、证据偏移错误 0 条。

## 9. 当前已生成的 FTA Preview

已基于 AI 授权审核快照生成独立的 `preview_only`：

- JSON：`evaluation/quality_eval/runs/siemens_s210_ai_authorized_fta_preview_v1_2026-09-23.json`
- Markdown：`evaluation/quality_eval/runs/siemens_s210_ai_authorized_fta_preview_v1_2026-09-23.md`
- 后端规则 owner：`backend-python/fta/ai_authorized_fta_preview_service.py`
- 评测适配器：`evaluation/quality_eval/public_sources/build_siemens_s210_ai_authorized_fta_preview.py`
- 预览树：3 个（A01981、A07094、A30714）
- 排除事件：3 个（A01069、A01631、F01611）
- FTA 合同校验：通过

Preview 专项测试通过；后端回归测试为 `187 tests OK`。

A01631 的既有 AI 逻辑审核曾判为 AND，但当时活动候选是 `causal_summary` 且 `fta_eligible=false`；此外人类 Gold 为 OR、AI 角色审核为 AND，且具体配置候选仍待定位证据。批次12因此保留冲突并暂缓，不把摘要节点伪装成基本事件。F01611 的逻辑门为 `unknown`，A01069 为 `not_applicable`，均被安全排除。这里的 3 棵属于 2026-09-23 初始 Preview v1；后续事件审核批次累计 Preview 见第42节。

## 10. 原文输入接入状态

原文抽取服务现在可以通过 `extract_with_causal_candidates()` 同时返回：

1. 原有的故障记录审核结果；
2. 由 `causes + evidence_spans` 生成的 `pending_expert_review` 因果候选队列。

候选准备层只做证据搬运和状态初始化，不做因果判断。原因字段保留精确 `cause` 引文，并额外保留同一故障记录内有界的 `cause_context` 原文句子（最多 1,200 字符）；字符偏移仍指向原始输入。唯一原因证据可绑定为 `exact`；同一短语多处出现时标记为 `ambiguous` 且不自动绑定；没有上下文时 `relation_context_status=missing`。AI 决议不得仅凭候选原因词组或领域常识批准因果关系；生产新批次的 `causal` 决议必须引用 `cause_context`。结构化校验失败就拒绝生成审核 manifest、保留已保存的抽取结果。因此原文可进入审核流程，但不能绕过审核直接生成生产 FTA。

既有抽取记录不会自动补写新的上下文证据；重试接口只重用该结果中已保存的跨度。如果旧记录缺少 `cause_context`，即使重试也不会重新读取原文；需要通过新原文抽取接口重新提交文本以生成上下文证据。重试仍保留原抽取历史，不覆盖旧记录。

应用层入口为 `CausalReviewApplicationService`。后端 API 现在提供两个入口：

- `POST /api/fta/extract/causal-review`：接收新原文，保存抽取结果与初始审核状态，准备候选原因，执行 AI 因果审核并导入校验通过的 manifest。
- `POST /api/fta/extractions/{result_id}/causal-review`：对已保存的抽取结果重试因果审核，不重复抽取原文。

如果 AI 调用、结构化审核校验或 manifest 导入失败，普通抽取历史仍保留；失败响应包含 `extraction_result_id` 和重试路径。审核 manifest 只在结构化校验通过后写入，写入仍经过 SQLite 仓储的事务、幂等和哈希冲突门禁。成功响应明确保留 `reviewer_provenance=user_authorized_ai_expert_role` 与 `human_reviewed=false`，表示用户授权的 AI 专家角色审核，而不是人工签字。没有候选原因时返回 `no_candidates`，不写入空 manifest。

这两个 API 目前只闭合“原文 → 抽取/证据 → AI 因果审核 → 审核快照入库”。它们不自行审核 AND/OR 逻辑门，也不生成可发布的故障树；响应继续标记 `fta_ready=false`。完整故障树仍须满足对应的逻辑门和 FTA 门禁。

## 11. 历史候选的上下文证据复核

历史 1,041 条审核 manifest 没有为 causal 决议保存独立的 `cause_context`，因此不能直接复用旧决议生成新的 FTA 树。已生成只读复核准备包：

- JSON：`evaluation/quality_eval/runs/siemens_s210_causal_context_revalidation_v1_2026-09-23.json`
- Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_context_revalidation_v1_2026-09-23.md`
- 校验：`evaluation/quality_eval/runs/siemens_s210_causal_context_revalidation_v1_validation_2026-09-23.json`
- 生成器：`evaluation/quality_eval/public_sources/build_siemens_s210_causal_context_revalidation_v1.py`

生成器只按候选 ID 对账，再以原文中的唯一规范化精确匹配定位原因；它不对原因语义重新裁决，不覆盖旧 manifest，不写数据库或 Gold。当前结果：1,041 条候选全部匹配到源身份；917 条具有唯一原文定位并附有独立原因/上下文引用，124 条因短语未匹配、重复或上下文不适用而要求人工定位。旧判为 `causal` 的 815 条中，744 条具备上下文待重新审核，71 条待人工定位；旧 `fta_eligible=true` 的 645 条中，581 条上下文可用、64 条待人工定位。

上述 917/744/581 只是“证据上下文可供复核”，**不是**新的因果批准，也不代表原因集合完整。尤其 581 条旧 `fta_eligible` 记录仍须在事件级复核中重新审查其完整候选集合与 AND/OR；一个故障只有在完整原因集合已核对、因果证据有效且逻辑门明确时才允许进入树。门为 `unknown`、证据待定位或候选集不完整时均 `build_allowed=false`。本包的校验状态为 `valid`，同时明确 `database_written=false`、`gold_mutated=false`、`fta_ready=false`。

本次执行：

```powershell
python evaluation/quality_eval/public_sources/build_siemens_s210_causal_context_revalidation_v1.py
python -m unittest evaluation.quality_eval.public_sources.test_build_siemens_s210_causal_context_revalidation_v1 -v
python -m unittest evaluation.quality_eval.public_sources.test_build_siemens_s210_causal_event_gate_preview_v1 -v
python evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_preview_v1.py
python -m unittest discover -s backend-python/tests -p 'test_*.py' -v
```

上一轮完整回归结果为上下文 artifact `status=valid`、上下文生成器测试 `5 tests OK`、事件级预览测试 `3 tests OK`、预览合同通过且只含 A01780 的 1 棵 OR 树、后端回归 `194 tests OK`。增加 reviewed-section 源跨度门禁后，第三至第二十五批 artifact 合同均通过。本轮第 20–25 批预览均为 0 棵树；事件预览定向测试 `27 tests OK`、相关 Python 文件 `py_compile` 通过；完整后端回归未在本轮变更后重跑。

首轮事件级试点的 10 个故障码现已全部检查（这不等于 281 条全量事件审核）：

- A01006：唯一原因有原文支持，但门为 `unknown`，不建树。
- A01069：Cause 与 Example 是同一原因及其具体实例；门为 `not_applicable`，不生成 AND/OR 树。该结论与既有 AI 逻辑审核一致，但与现有人类 Gold 的 OR 决策存在冲突；两者均保留，未覆盖人类 Gold。
- A01780：完整核对 Cause、Alarm value、Note 三段；报警位是“制动器未打开”的状态证据，不作为第三个原因；Note 明确说明未配置制动器时报警“也会”触发，支持 OR。该事件已生成一个 `preview_only` 局部预览。
- A13021：只有一个触发场景，不支持 AND/OR；当前候选只覆盖 Cause 首句，遗漏许可证限定语，完整性门禁未通过，不建树。
- A30044：单一阈值超限原因完整；参数值解释和 Remedy 均不是额外原因。逻辑门为 `not_applicable`，不建 AND/OR 树。
- F01030：监控时间内未收到生命信号是唯一触发原因；Cause 第二句是主控权返回状态，不是另一原因。Remedy/Notice 不作为原因，逻辑门 `not_applicable`。
- F01044：从非易失性存储器加载描述数据时检测到错误是唯一原因；更换存储卡或控制单元属于 Remedy，逻辑门 `not_applicable`。
- F01656：Cause 为通道 2 安全参数访问错误总括；r0949 的 129/131/132 是诊断子型，possible 离线复制不确定，255 指向通道 1。原因集合门禁未过，故障值间逻辑未知，不建树。
- F01674：Cause 总括与 r0949 五个 bit 诊断子型完整对应；bit 列举没有给出 AND/OR 组合规则，gate `unknown`，不建树。
- F01611：已逐条复核完整 Cause 与 r0949 故障值清单及 27 个候选。多个值是诊断子型/状态编码，1…999 与参数 2…15 表示被交叉比较的数据编号；`alternatively` 仅支持 1000 分支内的局部替代情形。手册未证明完整 FTA 根因集或全局 AND/OR，`cause_set_complete=false`、gate `unknown`，不建树。

事件级审核快照：

- 第一批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch01_2026-09-23.json`
- 第二批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch02_2026-09-24.json`
- 第三批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch03_2026-09-24.json`
- 第四批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch04_2026-09-24.json`
- 第五批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch05_2026-09-24.json`
- 第六批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch06_2026-09-24.json`
- 第七批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch07_2026-09-24.json`
- 第八批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch08_2026-09-24.json`
- 第九批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch09_2026-09-24.json`
- 第十批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch10_2026-09-24.json`
- 第十一批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch11_2026-09-24.json`
- 第十二批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch12_2026-09-24.json`
- 第十三批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch13_2026-09-24.json`
- 第十四批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch14_2026-09-24.json`
- 第十五批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch15_2026-09-24.json`
- 第十六批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch16_2026-09-24.json`
- 第十七批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch17_2026-09-24.json`
- 第十八批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch18_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch18_2026-09-24.md`
- 第十九批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch19_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch19_2026-09-24.md`
- 第二十批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch20_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch20_2026-09-24.md`
- 第二十一批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch21_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch21_2026-09-24.md`
- 第二十二批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch22_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch22_2026-09-24.md`
- 第二十三批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch23_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch23_2026-09-24.md`
- 第二十四批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch24_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch24_2026-09-24.md`
- 第二十五批：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch25_2026-09-24.json`；可读审核摘要：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch25_2026-09-24.md`
- A01780 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_v1_2026-09-24.json`
- A01780 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_v1_2026-09-24.md`
- 第三批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch03_2026-09-24.json`
- 第三批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch03_2026-09-24.md`
- 第四批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch04_2026-09-24.json`
- 第四批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch04_2026-09-24.md`
- 第五批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch05_2026-09-24.json`
- 第五批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch05_2026-09-24.md`
- 第六批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch06_2026-09-24.json`
- 第六批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch06_2026-09-24.md`
- 第七批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch07_2026-09-24.json`
- 第七批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch07_2026-09-24.md`
- 第八批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch08_2026-09-24.json`
- 第八批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch08_2026-09-24.md`
- 第九批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch09_2026-09-24.json`
- 第九批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch09_2026-09-24.md`
- 第十批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch10_2026-09-24.json`
- 第十批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch10_2026-09-24.md`
- 第十一批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch11_2026-09-24.json`
- 第十一批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch11_2026-09-24.md`
- 第十二批零树 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch12_2026-09-24.json`
- 第十二批零树 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch12_2026-09-24.md`
- 第十三批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch13_2026-09-24.json`
- 第十三批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch13_2026-09-24.md`
- 第十四批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch14_2026-09-24.json`
- 第十四批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch14_2026-09-24.md`
- 第十五批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch15_2026-09-24.json`
- 第十五批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch15_2026-09-24.md`
- 第十六批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch16_2026-09-24.json`
- 第十六批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch16_2026-09-24.md`
- 第十七批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch17_2026-09-24.json`
- 第十七批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch17_2026-09-24.md`
- 第十八批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch18_2026-09-24.json`
- 第十八批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch18_2026-09-24.md`
- 第十九批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch19_2026-09-24.json`
- 第十九批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch19_2026-09-24.md`
- 第二十批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch20_2026-09-24.json`
- 第二十批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch20_2026-09-24.md`
- 第二十一批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch21_2026-09-24.json`
- 第二十一批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch21_2026-09-24.md`
- 第二十二批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch22_2026-09-24.json`
- 第二十二批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch22_2026-09-24.md`
- 第二十三批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch23_2026-09-24.json`
- 第二十三批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch23_2026-09-24.md`
- 第二十四批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch24_2026-09-24.json`
- 第二十四批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch24_2026-09-24.md`
- 第二十五批 Preview JSON：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch25_2026-09-24.json`
- 第二十五批 Preview Markdown：`evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch25_2026-09-24.md`
- Preview 适配器：`evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_preview_v1.py`；核心仍由 `backend-python/fta/ai_authorized_fta_preview_service.py` 构建。

哈希口径：`source_dataset_sha256` 与 `previous_manifest_sha256` 使用规范化 JSON payload（`ensure_ascii=false`、排序键、紧凑分隔符）的 SHA-256；`context_revalidation_sha256` 使用该 JSON 文件原始字节的 SHA-256。第十五批独立审核者曾按原始文件哈希检查前两项而误判不匹配；按构建器的规范化口径复核后均一致，构建器输入指纹校验通过。

A01780 预览包含两个 OR 子事件，生成前复核了 5 个候选的 10 个证据跨度；这只是 AI 授权角色审核的局部预览，不是人类签字、Gold 合并或生产树。首轮试点 10/10 已检查，只有 A01780 产生 1 棵 `preview_only` OR 树；其余 9 个事件均因门未知、不适用、原因集不完整或当前 AND/OR 合同不适配而未建树。第七至第十一批新增 A01007、A01019、A01020、A01045、A01049、A01064、A01073、A01099、A01251、A01016、A01035、A01304、A01306、A01330、A01489，均未生成树；A01009 因候选证据映射未闭合而暂缓。第十二批新增 A01590、A01637 两个完整事件级审核快照，均未生成树；A01631 单独保留在证据/逻辑门冲突暂缓区。第十三批新增 A01638、A01654、A01691 三个事件快照：A01638 是关联状态消息，不建树；A01654 按 r2124 的两个配置不匹配分支生成 1 棵局部 `preview_only` OR 树；A01691 的模式级 OR 已记录，但 CR-CAND-V5-007 仍处于 Gold v7 `revise`，当前候选写的是阈值规范而非实际违规条件，因此原因集合映射不完整、不生成树。第十四批新增 A01693、A01695、A01696：A01693 是参数更改触发的重启提示，A01696 是单一启动配置条件，两者的逻辑门均为 `not_applicable`；A01695 是传感器模块更换通知，保留 `associated_only`，同时记录 `Acknowledge: NONE` 与后续确认要求的表面不一致。三条均不生成树。第十五批新增 A01697、A01707 两个事件审核快照：A01697 的 p9559 超时是明确触发条件，但 Note 另述启动完成后总会发出报警，未说明与计时器超时的组合关系，故原因集不完整、gate=`unknown`；A01707 只有位置偏离静止容差这一 Cause，F01701 是下游停机消息，gate=`not_applicable`。两条均不生成树。A01698、A01699 因 context revalidation 尚无验证证据行继续暂缓，不自动补绑。

第三批结果：

- A13021：完整检查 Cause、Note、Remedy。唯一触发场景是输出频率超过 550 Hz，但现有候选只摘 Cause 首句，遗漏同段明确的许可证限定语；`cause_set_complete=false`，不建树。
- A30044：唯一 Cause 是功率单元电源上限被超过；Alarm value 是电压/通道编码说明，Remedy 是检查动作。原因集合完整，单一原因不适用 AND/OR，保留因果候选但不生成 AND/OR 树。
- 第三批预览通过合同校验，生成 0 棵树；`fta_ready=false`、`database_written=false`、`gold_mutated=false`。
- 第五批检查了 F01656 的 Cause、STO Note、完整 r0949 故障值表和分值 Remedy，以及 F01674 的 Cause、STO Note、5 个 bit 与 Remedy/术语表。两者都不生成树：F01656 原因集合门禁未过、F01674 bitwise 组合逻辑未知。第五批预览合同通过，0 棵树；数据库、Gold 未改。
- 第六批由三个独立 AI 子审核者分组检查 F01611 的 27 个候选，主审核随后逐段核对原文。显式参数/通信错误等保留为候选；范围摘要不重复计叶；跨通道停止请求及可能由其他故障引起的 2001 状态不作为独立根因。编号枚举不能直接推导全局 OR；原因集是否覆盖全部真实根因也无法由该诊断表确认。第六批预览合同通过，0 棵树；数据库、Gold 未改。
- 第七批检查 A01007、A01019、A01020：A01007 的候选只保留了 `e.g.` 举出的固件更新示例，未覆盖完整 POWER ON 条件；A01019/A01020 候选逐字对应 Cause，但只是写入失败模式，手册没有展开底层根因。三条均不适用多原因 AND/OR，且不建树。A01009 经独立 AI 语义复核发现候选删去了 `r0037[0]`；context revalidation 为 `manual_evidence_alignment_required`，未自动补绑引文，暂缓进入事件预览。第七批预览合同通过，0 棵树；数据库、Gold 未改。
- 第八批检查 A01045、A01049、A01064，均为单一Cause条件，不适用AND/OR，故不生成树。A01045的第二句是文件评估错误的后果；A01049独立审核者提醒候选没有复述“写请求中断”，主审将其作为明确后果而非第二原因记录，并保留了口径差异；A01064的POWER ON、升级和技术支持均属Remedy。第八批预览合同通过，0棵树；数据库、Gold未改。
- 第九批检查 A01073、A01099、A01251，均只有一个明确 Cause 条件，不适用 AND/OR，故不生成树。A01073 的一位独立审核者认为候选遗漏“visible partition”；主审将 manifest 候选文本与原文引文逐字对照，确认候选本身包含该限定语，因此不采纳该遗漏意见，并把异议及核对依据写入审核快照。该 Cause 后句是备份同步所需的 POWER ON/硬件复位，Note 是可能触发该请求的上下文。A01099 的 `r3107` 是诊断读数；A01251 的内部故障值和分支处理均非额外原因。第九批预览合同通过，0 棵树；数据库、Gold 未改。
- 第十批检查 A01016、A01035、A01304。A01016 的六个候选证据均精确匹配：Cause 总括条件加 r2124 五项诊断细分；独立子审指出它们不能作为六个并列基本事件，物理根因集合不完整/不可判定，gate=`unknown`、不建树。A01035 的候选显示启动时数据不完整、保存未完成及可能的备份中断，属于层级链路；后者的局部“or”不能外推为顶层门，且手册未证明根因集合穷尽，故完整性=false、gate=`unknown`、不建树。A01304 只有一个固件版本不匹配原因，`r2124` 是组件编号、更新固件是 Remedy，gate=`not_applicable`。独立 AI 子审已确认三条事件；A01016 子审确认六候选共12段原文/上下文引文与来源偏移逐字一致。预览合同通过，0 棵树；数据库、Gold 未改。
- 第十一批主审与独立AI子审共同检查 A01306、A01330、A01489，三条均为单一Cause，故不推断AND/OR、不生成树。A01306是固件更新进行中的状态/报警条件，底层根因未说明，因此不作为FTA基本事件；组件号为诊断信息，自动撤销是后续结果。A01330的原因是实际拓扑不符合要求，具体拓扑缺陷未说明；OCC电缆/上电/硬件支持检查属于Remedy。A01489是实际与目标拓扑不一致，`r2124`/Note用于组件定位，Remedy中的电源、电缆和组件检查不能擅自提升为原因。预览合同通过，0棵树；数据库、Gold未改。
- 第十二批由两名独立 AI 子审核者分别复核 A01590/A01631 与 A01637。A01590 的唯一 Cause 是选定电机维护间隔到期，`r2124` 为电机数据组定位，维护/复位为 Remedy；其单一条件记为 `not_applicable`。A01637 的 Cause 是一个完整复合安全配置状态，`r9767` 为状态参照，密码分配/保存为 Remedy；不把语法 `and` 推断成 FTA 门，记为 `unknown`。两者均不生成树。A01631 的总括候选和具体配置不是并列原因；具体配置句内部明确写 `and`，但组合候选仍需人工定位证据，且既有人类 Gold `OR` 与 AI 角色审核 `AND` 冲突未解决，因此继续 deferred，不自动补绑、不进 Preview。独立审核已完成；第十二批 Preview 合同通过，0 棵树，Gold/数据库未改。
- 第十三批由两名独立 AI 子审核者分别复核 A01638/A01654 与 A01691。A01638 是成功密码录入状态消息，候选为 `associated_only`；A01654 的 r2124=1、2 分别描述两种具体配置不匹配状态，总括 Cause 不另算一叶，故接受事件范围内的 OR，生成 1 棵局部 `preview_only` 树。A01691 的等时/非等时为互斥模式，记录为模式级 OR；但 CR-CAND-V5-007 在 Gold v7 中仍为 `revise`，写的是“周期至少 4 倍”的规范而非已发生的违规条件。为避免用规则描述冒充故障叶，原因集合映射保持不完整，不生成 A01691 树。第十三批 Preview 合同通过，共 1 棵树；Gold/数据库未改，`fta_ready=false`。
- 第十四批由两名独立 AI 子审核者分别复核 A01693、A01695；主审核逐段核对 A01696。A01693 的安全参数更改是重启提示的单一触发条件，r2124 是参数编号，重启与验收要求不是新原因；A01696 的启动时 test-stop 选择是单一不允许状态，后一句解释测试重做时机。A01695 是 Sensor Module 更换通知，不是模块失效根因，归为 `associated_only`；同时记录 `Acknowledge: NONE` 与 Cause/Remedy 的确认要求表面不一致，暂不解释字段语义。三条逻辑门均为 `not_applicable`，均不生成树。第十四批 Preview 合同通过，0 棵树；Gold/数据库未改，`fta_ready=false`。
- 第十五批由两名独立 AI 子审核者分别复核 A01697 与 A01707。A01697 的 Cause 将 p9559 设定时间超限列为触发条件；Note 又称启动完成后总会发出报警，但没有说明它与计时器超限的逻辑关系，因此完整原因集不能确认、gate=`unknown`。A01707 的 Cause 是实际位置偏离目标超过静止容差，F01701 是停止消息结果；Remedy 里的故障检查和 POWER ON 不提升为原因，单一条件记为 `not_applicable`。A01698、A01699 因 context revalidation 标为 `manual_evidence_alignment_required` 且无验证证据行，留在待定位队列，不自动绑定。第十五批 Preview 合同通过，0 棵树；Gold/数据库未改，`fta_ready=false`。
- 第十六批由 Euler、Aristotle 两名独立 AI 子审核者复核 A01714。Cause 明确支持驱动速度超过 p9531 限值；Cause 后句描述 p9563 配置的停止响应，属于结果。r2124 的 100/200/300/400/1000 是消息值释义，但原文未明确它们与总括 Cause 的层级，也未声明为独立树叶或 AND/OR 分支；故 `cause_set_complete=false`、gate=`unknown`，不建树。六条候选及 Cause、消息值、Remedy、Note、See also 的引文偏移均通过源文本核验。A01709（CR-CAND-V4-013）及 A01711（CR-CAND-V10-001、CR-CAND-V11-001）因上下文证据对齐未闭合而继续暂缓；不自动补绑。第十六批 Preview 合同通过，0 棵树；Gold/数据库未改，`fta_ready=false`。
- 第十七批由 Bacon 独立复核 A01730、Boyle 独立复核 A01750/A01751，主审核逐字核对全部相关跨度。A01730 的 Cause 明确给出“reference block is negative”；V4 候选的 manifest 证据错误复用了 Cause 跨度，而 context source candidate 指向 r2124 的 “requested, invalid reference block”。不自动重绑；V4 按诊断消息值处理，FTA 原因集不完整、gate=`unknown`，暂不建树。A01750 的单一 Cause 是安全运动监控编码器报告硬件故障，状态字是诊断信息、检查/更换是 Remedy；A01751 的单一 Cause 是安全运动监控编码器在 effectivity test 中报错，内部故障值说明、Remedy 和 PROFIsafe 确认 Note 均非新增原因。后二者只在手册显式 Cause 范围内标完整、gate=`not_applicable`；底层物理根因未展开，且当前合同不生成单因果 AND/OR 树。A01716 三条候选均缺少已验证上下文证据，整条暂缓，不做部分审核。第十七批 Preview 合同通过，0 棵树；Gold/数据库未改，`fta_ready=false`。

第十八批由 Poincare 独立复核 A01781/A01783、Plato 独立复核 A01785，主审核逐段核对三条记录的 Cause、Possible causes、r2124、Note、Remedy。A01781 的超时 Cause 是事件定义，Possible cause 描述驱动故障导致制动器关闭这一可能上游链路，报警值是无法打开状态；根因集合未证明穷尽，gate=`unknown`。A01783 的 Cause 是关闭超时定义，报警值描述无法关闭状态，Remedy中的外部反馈检查不证明反馈已失效；更深层物理根因未展开，gate=`not_applicable`。A01785 的 r2124=1/4/8/16 分别列出配置消息；第16项是一个“同时使能”的复合条件，不等于顶层AND门；枚举未证明完整FTA原因集合，项间门逻辑也未声明，gate=`unknown`。CR-CAND-V7-023 的 manifest 文本/target字段缺失被明确保留，未静默补写。A01782 因 CR-CAND-V5-021 缺少已验证上下文证据，整条暂缓，不部分审核。第十八批 Preview 合同通过，0棵树；Gold/数据库未改，`fta_ready=false`。

第十九批由 Mencius 独立复核 A01788、Pauli 独立复核 A01796，主审核复核 A01798 并逐字核对源跨度。A01788 的 Cause 描述 test-stop 无法执行状态，Possible causes 中 STO 选择与安全消息导致 STO 两条均有原文，但彼此可能是替代原因或因果链，局部上下文未共同覆盖完整列表，原因集合/AND-OR 未证实，gate=`unknown`。A01796 的 Cause、r2124均描述等待通信状态；Remedy检查清单不能证明通信故障根因，CR-CAND-V4-057 manifest文本为空且上下文宽跨度跨入Remedy，审核快照保留精确消息值引文，不改manifest。A01798 是test-stop执行中的正常状态，完成后消息自动撤销，gate=`not_applicable`。三条均不建树；第十九批 Preview 合同通过，0棵树；Gold/数据库未改，`fta_ready=false`。

第二十批由主审核逐段核对 A01799、A01839、A01932，Ampere 独立复核 A01839、Gibbs 独立复核 A01932。A01799 是验收测试模式激活状态，归为 `associated_only`，不适用 AND/OR。A01839 的计数器递增属于连接/电缆监测诊断指标；故障位置说明不能补足该记录未提供的上游根因，故原因集合不完整、gate=`unknown`。A01932 保留时钟同步/同步生命信号缺失且选择 DSC 的因果候选，但原句的否定范围与连接关系不足以安全拆成逻辑叶或判定 AND/OR，原因集合不完整、gate=`unknown`。三条均不建树。首次构建检测到 A01839 标题结束偏移不准确，已依据原文修正为 `[0,60)` 并重跑通过。第二十批 Preview 合同通过，0 棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十一批由主审核逐段核对 A01940、A01941、A01943。曾尝试让子智能体独立复核 A01940/A01943，但均因平台使用额度耗尽失败，所以本批没有独立复核意见。A01940 的 Cause 列出三条具体同步失败解释，候选逐条对应且来源跨度准确；列表没有直接证明OR或AND，gate=`unknown`。A01941 的单一候选覆盖完整复合Cause，句内 `and` 不拆成FTA逻辑门，gate=`not_applicable`。A01943 的候选覆盖配置前提、直接异常状态及两条上游解释，但状态与上游解释有层级、两条解释的AND/OR未明确，gate=`unknown`。三条均不建树。第二十一批 Preview 合同通过，0棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十二批由主审核逐字核对 A01900 的 15 个候选与源文本跨度；本批没有独立复核意见。Cause 中的通用“错误配置报文”保留为因果摘要；13 个 r2124 报警值解释保留为有证据的配置/诊断候选，但不认定为独立FTA基本事件；r2124=4 明确指向 A01902，按跨故障关联处理，不重复生成 A01900 原因叶。原文还注明存在仅供 Siemens 内部排查的 Additional values，因此公开候选集合不完整，cause_set_complete=false；报警值枚举不能证明 AND/OR，gate=`unknown`。A01900 不建树。第二十二批 Preview 合同通过，0棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十三批由主审核逐字复核 A01902 的 15 个候选。Cause 总括与全部 14 个已列出的 r2124 时序/采样诊断条件均有原文对应；Remedy 参数调整动作没有提升为原因。该事件在“覆盖本记录明示Cause与报警值条目”的范围内标记原因列举完整，但不声称物理根因全集已知。报警值编号及个别诊断条件内部的 `or` 不能证明顶层OR门，gate=`unknown`；A01902 不建树。第二十三批 Preview 合同通过，0棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十四批由主审核逐字核对 A01944、A01980、A01981 的 6 个候选。A01944 的 Cause 使用 `because` 明确支持生命信号变化与Tmapc配置不一致这一单一因果条件，运行状态只作前置条件，门为 `not_applicable`；A01980 的 Cause 仅重述循环连接中断，未给出上游原因，故 cause_set_complete=false、gate=`unknown`；A01981 明确给出控制器连接尝试导致允许连接数超限，RT/IRT 是报警值诊断分类而非独立原因，完整覆盖本条明示因果内容，门为 `not_applicable`。三条均不生成AND/OR树。第二十四批 Preview 合同通过，0棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十五批由主审核逐字核对 A01989、A02007、A05000、A05001、A05003、A05006 的 6 个单一Cause候选。传输超时、驱动对象类型不匹配及温度/温差阈值均保留为本条明确的报警触发条件；`and/or`仅说明传输对象，未提升成FTA门。温度继续上升后触发 F30004/F30025/F30036/F30024 是不同的后续故障/风险，不作为当前报警的第二原因；Remedy中的环境、负载、冷却和风扇检查是排查建议，不代表确认根因。六条均在本记录明示范围内完整，逻辑门 `not_applicable`，不生成单因果AND/OR树。第二十五批 Preview 合同通过，0棵树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十六批由主审核逐字核对 A07012、A07092、A07094 的 7 个候选，并由 Fermat 独立复核 A07012/A07092、Carson 独立复核 A07094。A07012 的 Cause 总括与 r2124=200/300 两种电机温度模型过温子型去重后形成局部 OR；A07094 的一般参数限值违反由最小/最大限值两种相反越限分支形成局部 OR；两者各生成一棵 `preview_only` 树，范围仅限手册列出的报警子型/越限方向，不声称物理根因已知。A07092 的候选只描述惯量估算器未得到有效值这一未就绪状态，手册未给出上游根因，原因集合不完整、gate=`unknown`，不建树。A07012 的Hysteresis、参数引用与负载/环境检查，A07094 的参数号及纠正建议均未误作根因。两位独立 AI 子审核者均未发现阻断性问题，并各自核验了相关候选/审核引文偏移与原文一致；AI 交叉复核不等同真人专家签署。第二十六批 Preview 合同通过，共 2 棵局部 OR 树；Gold、manifest、数据库未改，`fta_ready=false`。

第二十七批主审逐字核对 A07095、A07200、A07565 的 3 个候选，并由 Maxwell 独立复核 A07095/A07200、Arendt 独立复核 A07565。A07095 与标题重述同一 One Button Tuning 激活状态，修订为 `causal_summary/describes`，不作为关联实体或FTA叶节点；A07200 的唯一Cause是ON/OFF1命令存在，原文还明确给出 p0840 或主控制字bit 0两条替代信号路径（局部信号源OR）。子审核指出应记录该OR；主审采纳并明确它是控制信号路径，不属于当前“故障根因树”的门逻辑，不生成设备故障叶节点。A07565只报告编码器接口错误信号，r2124仅说明可读取G1_XIST2错误码而未提供具体码义；Arendt确认应保持原因集合不完整、gate=`unknown`、不建树。所有复核跨度与原文偏移一致。第二十七批Preview合同通过，0棵树；AI交叉复核未声称真人专家意见，Gold、manifest、数据库未改，`fta_ready=false`。

预览适配器同时验证审核记录中的 `reviewed_sections` 引文及字符区间与原始文本逐字一致，防止在完整性判断中引用错位或编造的非因果区段。

第四批中，两名独立 AI 审核者都认为单一原因可作为一个叶节点展示；但当前 `fta_graph_contract` 只接受根事件上的显式 `AND`/`OR` 门，预览 owner 也只生成这两类门。因此当前批次采用保守合同：保留单一因果关系，不生成 AND/OR FTA 树。若将来要支持无组合门的单叶关系预览，需要单独变更并验收 FTA 合同，不能把它混称为当前树。

第五批两条复杂事件经独立 AI 审阅与主线程逐字符跨度复核：F01656 未能证明目标通道 2 事件的完整独立原因集合，F01674 的 bitwise 诊断列表未给出组合逻辑；均保持不建树。第六批 F01611 同样没有全局逻辑门及完整根因集合的充分证据；第七至第十二批十七条事件均没有足够依据生成多原因 AND/OR 树，保持不建树。第十三批 A01654 生成一棵局部 OR 预览；A01638 无因果叶，A01691 因 `revise` 候选未闭合而不建树。第十四批 A01693、A01695、A01696 均不适用 AND/OR，因此不建树。第十五批 A01697 保持 gate=`unknown`、A01707 为单因果 `not_applicable`，均不建树。第十六批 A01714 的 r2124 消息值表不能单独证明树分支或逻辑门，故 gate=`unknown`；A01709、A01711 因证据对齐阻塞暂缓。第十七批 A01730 因候选—证据对齐冲突暂不建树，A01750/A01751 为单一Cause且不适用AND/OR；A01716因证据未闭合暂缓。第十八批 A01781/A01783/A01785 均未生成树，A01782 因证据未闭合暂缓。第十九批 A01788/A01796/A01798 均未生成树；A01631 另为证据/Gold 门冲突暂缓，不计入完整事件审核快照。

第二十八批主审逐字核对 A07805、A08511、A08800 的 13 个候选，并由 Newton 独立复核 A08511、Confucius 独立复核 A07805/A08800。A07805 的唯一候选是 I2t 报警阈值超限这一直接触发条件；p0290响应及Remedy检查项不升格为原因，完整覆盖本条明示Cause，但单一条件不适用AND/OR树。A08511 的Cause总述加公开列出的10个r2124诊断值共11候选均有精确证据；但原文明确注明还有仅供Siemens内部排查的Additional values，公开集合不完整，r2124列表也没有FTA门证据，故gate=unknown、不建树；A01902仅作为交叉引用，不当作新增原因。A08800描述PROFIenergy节能模式激活状态，退出模式的Note是状态撤销条件，不是故障根因或OR门，改为描述性状态摘要、不建树。第二十八批预览合同通过，0棵树；两名独立AI复核与主审边界判断一致，但不等于真人专家签署；Gold、manifest、数据库未改，fta_ready=false。

第二十九批主审逐字核对 F07901、F30040、F30025 的 8 个候选，并由 Herschel 独立复核 F07901/F30040、Hilbert 独立复核 F30025。F07901 的Cause以 `either ... or ...` 明确正/负超速两个替代触发方向，故仅在手册明示触发条件层面记为局部OR；目前唯一候选是合并文本，不能临时拆造两个叶节点，不建树。F30040 仅有一个欠压阈值持续超限条件；r0949的24/48 V字段是诊断编码，不是两个原因，gate=`not_applicable`。F30025 的Cause摘要和五项列表全部逐项定位（源文本项目覆盖6/6），但“insufficient cooling, fan failure”内部关系未明，不能宣称FTA叶节点集合完整或据列表标点推断OR，cause_set_complete=false、gate=`unknown`。三条均不生成树；本批Preview合同通过，0棵树；manifest中 V13-223 的 candidate_text 为空但原文与context证据可逐字验证，此数据质量点未被静默改写。AI复核不是真人专家签署；Gold、manifest、数据库未改，`fta_ready=false`。

第三十批主审逐字核对 A09000、A13001、A30016 的 6 个候选，并由 Cicero 独立复核前两条、Sartre 独立复核 A30016。A09000 的 Cause 是配置错误概括，r0949列出无管理员密码/管理员密码无效/SINAMICS密码无效三种诊断状态；虽然三个故障值文本均覆盖，但它们不足以证明完整FTA根因集合或OR门，且相关候选未批准为FTA叶节点，故cause_set_complete=false、gate=`unknown`。A13001 的 Cause 只说明检查license key校验和时发现错误，与故障状态近似，手册未给出上游根因，gate=`unknown`。A30016 明确给出单一“DC link voltage too low”触发条件，r2124是跳闸时电压测量，Remedy为恢复/检查动作；对手册明示触发条件完整，但单原因不适用AND/OR树。三条均不建树；Preview合同通过、0棵树。另记录 A30016 数据集审核元数据与manifest对reviewer身份标记冲突，以及 A09000 的V7候选manifest字段缺失；本批不修改这些源数据，不宣称真人专家审核，Gold/数据库未改，`fta_ready=false`。

## 12. 下一步边界

第二十九批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch29_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch29_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch29_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch29_2026-09-24.md)。第三十批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch30_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch30_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch30_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch30_2026-09-24.md)。第三十一批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch31_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch31_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch31_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch31_2026-09-24.md)。第三十二批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch32_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch32_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch32_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch32_2026-09-24.md)。

**截至第三十一批**，已有 80 个唯一故障码完成事件级 AI 审核快照，281 条中还有 201 条未审核；累计逐条复核 208/1041 个候选，尚有 833 个候选未覆盖。第三十一批核查 A30031、A30041、A30054：A30031 的五项原因文本已覆盖，但全局 AND/OR 未明，两个局部 OR 不替代全局逻辑门；A30041/A30054 仅确认手册明示的单一欠压触发条件，未提供上游物理根因。三条均不生成树，Preview 为 0 棵，`fta_ready=false`。Locke 与 Turing 为用户授权 AI 专家角色复核，不是真人专家签署；Gold、manifest、数据库未改。

**截至第三十二批**，已有 83 个唯一故障码完成事件级 AI 审核快照，281 条中还有 198 条未审核；累计复核 212/1041 个候选，尚有 829 个候选未覆盖。A30076 的 80% 阈值属于明确触发条件，但上游物理根因未知；A30077 候选是热过载状态复述；A30076 原文提到输出 A30077，只记录显式报警引用，不自动建因果边。A30502 两项列表原因均已核对，但 AND/OR 未知。三条均不建树，Preview 为 0 棵，`fta_ready=false`。Nietzsche 与 James 的独立 AI 复核已完成，审核来源元数据冲突已记录；不是真人专家签署，不修改 Gold、manifest 或数据库。

第三十三批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch33_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch33_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch33_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch33_2026-09-24.md)。第三十四批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch34_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch34_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch34_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch34_2026-09-24.md)。第三十五批产物：[AI审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch35_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch35_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch35_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch35_2026-09-24.md)。

第三十三批检查 A30693、A30707。A30693 的安全参数变更是状态/触发提示，重启仅使变更生效；A30707 的位置超出静止容差是直接触发条件，F30701 是停机响应，均不能说明上游物理根因。两条均不建树。第三十四批检查 A30711 的 12 个候选：Cause 段的“incorrect synchronization”保留为条件性候选；r2124 消息值条目按诊断子型记录而不升级为 FTA 叶节点；A01711/F01611 是定义交叉引用，F30701 是响应消息。Cause/Remedy 对消息值范围还存在 1024 及 6000...6166/6000...6999 的覆盖差异，需要查证，不能据此补造根因。A30711 完整原因集合未证实、全局 gate=`unknown`，不建树。两批均由用户授权的 AI 专家角色交叉复核，不是真人专家签署；Gold、manifest、数据库未改，`fta_ready=false`。

**截至第三十四批（当前）**，已有 86 个唯一故障码完成事件级 AI 审核快照，281 条中还有 195 条未审核；累计逐条复核 226/1041 个候选，尚有 815 个候选未覆盖。批次产物是 AI 角色审核快照，不等于真人专家金标；完整原因集合或逻辑门未知时继续禁止建树。

第三十五批检查 A30714、F01000，共 7 条候选。A30714 的 Cause 总述是速度超过限值；5 个 r2124 值是 SLS/编码器限频诊断子型，不能直接当成五个独立 FTA 叶或 OR 门。旧 manifest 将其判为 OR，但 Gold 的 `logic_status=unknown` 且 `gold_relations=[]`，本条原文也没有全局 OR 证据；本批保持 gate=`unknown`、不建树。F01000 的候选只是重述“内部软件错误”，r0949仅限内部诊断，Remedy检查、升级、重启和更换均不反推成原因。两条均未建树；两名用户授权 AI 专家角色各复核一条，不是真人专家签署；Gold/manifest/数据库未改。

**截至第三十五批**，已有 88 个唯一故障码完成事件级 AI 审核快照，281 条中还有 193 条未覆盖；累计逐条复核 233/1041 个候选，剩余 808 个候选。以上“覆盖”指 AI 审核快照范围，不代表完整人工专家金标或全量物理根因已知。

第三十六批复核 F07433、F30657 两条记录。F07433 的 Cause 只支持“编码器未完成 unparking，无法切换到闭环控制”这一直接状态条件，未解释其上游原因；长定子 Note 是有适用范围的操作前提，Remedy 不反推成根因。F30657 的已有候选只覆盖 Cause 首句；“启用 PROFIsafe 时允许报文号为 30/901”是条件，“copy function was not used”与无效报文号的关系未说明，不能擅自补造成因或 AND/OR。两条均不建树。F06310 的 `CR-CAND-019` 因 context revalidation 要求人工证据定位，整条暂缓，不自动绑定或猜引文。Russell 与 McClintock 分别完成一条的独立 AI 专家角色复核，不是真人专家签署；Gold、manifest、数据库未改。

**截至第三十六批**，已有 90 个唯一故障码完成事件级 AI 审核快照，281 条中还有 191 条未覆盖；累计逐条复核 235/1041 个候选，剩余 806 个候选。以上仍仅代表 AI 角色审核快照范围。

第三十六批文件：[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch36_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch36_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch36_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch36_2026-09-24.md)。

第三十七批检查 F01694、F07955、F30003，共 8 条候选；Rawls、Kuhn、Euclid 分别完成一条记录的独立 AI 专家角色复核。F01694 的一个候选重述故障状态，另一个是 Note 中有直接依据的条件性发生场景，但不能证明原因穷尽；F07955 两条编码不匹配条件覆盖了手册 Cause 列表，但 AND/OR 未说明；F30003 四条 Cause 列表项均已核对，其中宽泛的 `line supply failure` 可能与具体供电情形重叠，不能径直作为并列树叶。三条均保持逻辑门 `unknown`、不建树；本批 Preview 为 0 棵，`fta_ready=false`。官方 Siemens 手册交叉核对与 Gold 原文一致；同时记录 manifest 人工审核标志冲突、F01694 Note 来源字段错标、部分候选行缺文本/证据等数据质量问题，不回写源数据。

截至第三十七批，已有 93 个唯一故障码完成事件级 AI 审核快照，281 条中还有 188 条未覆盖；累计逐条复核 243/1041 个候选，剩余 798 个候选。以上仅代表 AI 角色审核快照，不等于真人专家金标或全量根因已知；该数字为 Batch 38 前的历史截面。

第三十七批文件：[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch37_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch37_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch37_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch37_2026-09-24.md)。

第三十八批检查 F30078、F30701、F31138，共复核 6 条现有候选，并额外识别 1 条模型预测里出现但没有独立 Gold/manifest 候选 ID 的 Possible causes 项；Harvey、Curie、Archimedes 分别完成一条独立 AI 专家角色复核。F30078 的原文支持监控对象层面的局部 OR 和线电抗器分支内部的局部 AND，但这是嵌套结构，当前单层 AND/OR Preview 合同无法忠实表示，原因集合也未证明穷尽，因此不压平建树。F30701 的模型预测有 3 条原因、Gold/manifest 只有 2 条；“subsequent response, following messages…”更像时序/关联信息，类型未决，作为未映射项保留；p9556/p9560 的 OR 是 F30700 下游输出条件，不是 F30701 的原因门。F31138 的 Cause 是故障状态摘要，r0949 表是诊断码义，当前没有本次实际故障值与编码器版本，无法挑选原因叶。三条均保持 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`，本批 Preview 为 0 棵，`fta_ready=false`。AI 角色复核与旧 Gold/manifest 中的人类审核标记存在来源口径冲突，本批只记录、不回写；Gold、manifest、数据库未改。

第三十八批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch38.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch38_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch38_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch38_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch38_2026-09-24.md)。

第三十九批检查 A30798、A30799、A30999，共 4 条候选；Turing、Curie、Feynman 分别独立复核一条。A30798 的唯一 Cause 是安全运动监控 test stop 正在进行，解释报警触发条件，不解释 test stop 为何启动；A30799 的唯一 Cause 是 acceptance test mode active，r9733 句说明运行后果；两条均是单条件，不适用 AND/OR。A30999 的两条候选中，第一条是“未知报警/无法解释”状态摘要，第二条是手册列出的一个可能固件版本条件；去重后没有原文支持的 AND/OR 组合，也不能证明该次报警实际由该版本差异造成。三条均 `build_allowed=false`，本批 Preview 为 0 棵，`fta_ready=false`。AI 审核与当前“仅 AND/OR 树预览”的 `build_allowed` 口径分开：可以记录单条因果关系，不代表可生成故障树。Gold、manifest、数据库未改；旧人工审核来源标志冲突继续只记录、不回写。

第三十九批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch39.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch39_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch39_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch39_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch39_2026-09-24.md)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch39.py)。

**截至第三十九批**，已有 99 个唯一故障码完成事件级 AI 审核快照，281 条中还有 182 条未覆盖；累计逐条复核 253/1041 个候选 ID，尚有 788 个候选 ID 未覆盖。另有 F30701 一条模型预测原因没有对应独立候选 ID，已检查其文本但保留为未映射/待分类项，不计入 1041 个候选 ID 的闭合数。以上仍仅代表 AI 角色审核快照，不等于真人专家金标或全量物理根因已知。

第十五批历史截面为 35 个故障码已有事件级审核快照、246 条尚未完成。第十六批后有 36 个快照、245 条尚未完成。第十七批后有 39 个快照、242 条尚未完成。第十八批后有 42 个快照、239 条尚未完成。第十九批后有 45 个唯一故障码完成事件级审核快照、236 条尚未完成。第二十批后有 48 个快照、233 条尚未完成。第二十一批后有 51 个快照、230 条尚未完成。第二十二批后有 52 个快照、229 条尚未完成。第二十三批后有 53 个快照、228 条尚未完成。第二十四批后有 56 个快照、225 条尚未完成。第二十五批后有 62 个快照、219 条尚未完成。第二十六批后有 65 个快照、216 条尚未完成。**截至第二十七批**，已有 68 个唯一故障码完成事件级审核快照，281 条记录中仍有 213 条尚未完成事件级审核。A01009/A01631/A01730 因证据或逻辑冲突，A01698/A01699/A01706/A01709/A01711/A01716/A01782/A01784/A07091 因候选证据未完全闭合，仍不得自动补证或视作完整事件审核；A01691 的 V5 与 A01695 的候选仍保留既有 `revise` 状态，等待独立修订闭环。A01785 的 V7、A01796 的 V4 manifest字段缺失均保留为数据质量问题，本轮不修补Gold或manifest。A01900 已完成事件级复核，但由于 Additional values 明示存在未公开条目，候选集合完整性未通过；A01902 的已列举原因/报警值覆盖完整，但逻辑门未知；A01944/A01981 属单一明确因果条件或诊断状态，不适用AND/OR；A01980 只有故障状态复述，未查明上游原因；A01989/A02007/A05000/A05001/A05003/A05006 的单一Cause覆盖完整但不适用AND/OR；A07012/A07094仅对手册列出的替代子型生成局部OR预览，A07092仍因未说明上游原因不建树；A07095/A07200为功能/命令状态，A07565错误码码义缺失而保持unknown。以上均不自动补证或覆盖 Gold。全项目事件级审核仍未完成。下一步是：

1. 扩展事件级复核到未覆盖故障记录；截至第三十九批，已有 99 个唯一故障码具有事件级审核快照，281 条记录中其余 182 条尚未覆盖；累计复核 253/1041 个候选 ID，788 个候选 ID 尚未完成事件级覆盖；
2. 修订并核对 A13021 候选与许可证限定语映射；关闭 A01009/A01631/A01730 证据与冲突待办，并分别处理 A01691 V5、A01695 候选的既有 `revise` 状态及 A01698/A01699/A01709/A01711/A01716 的手工证据定位；不自动绑定近似文本；
3. 为 `cannot_determine`、诊断值与根因边界不清、以及非唯一证据建立待补证/人工定位队列；
4. 在完整原因集和逻辑门门禁关闭前，只生成 `preview_only` 故障树，不宣布生产 FTA 就绪。

RAG 检索、证据合同和边界回归已有独立报告；当前文档不把 RAG 语义审核结果与因果/FTA 审核混为一谈。

## 13. 第四十批与当前累计进度（2026-09-24）

第四十批检查 A40100、F01002、F01012，共 4 条候选；Newton、Anscombe、Noether 分别独立复核一条。主审逐字复核完整 Gold `input_text`，候选及必要条件上下文均为唯一精确匹配。

- **A40100 / CR-CAND-V5-142**：Cause 只是“X100 插座处发生报警”的顶事件复述；r2124 没有实际报警值，Remedy 仅要求查看报警缓冲区。没有已确认原因组，`cause_set_complete=false`、`logic_gate=not_applicable`，不建树。
- **F01002 / CR-CAND-V5-150**：Cause 只是“内部软件错误”状态复述；实际 r0949 值缺失，固件升级、POWER ON 和联系支持均属 Remedy。无可识别的因果条件组，门标记 `not_applicable`，内部根因仍未知，不建树。
- **F01012 / CR-CAND-V5-170、CR-CAND-V6-125**：V5 是旧固件项目转换过程中的触发情境，方向为 `source_to_target`，但不是机制级树叶；V6 只描述 r0949=600 时的诊断子型，实际值未确认，不作为第二个原因。无可建立的 AND/OR 组，原因集合仍不完整，不建树。

本批所有证据位置在完整 Gold 输入中唯一匹配；AI 主审与独立复核对“不可据此建 AND/OR 树”一致，但 F01002 的旧 manifest 因果标记、F01012-V6 的旧类别与本次语义判断存在差异，作为数据质量/历史判定冲突记录，不回写 Gold 或 manifest。审核者均为用户授权的 AI 专家角色，不是真人领域专家签署。

第四十批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch40.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch40.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch40_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch40_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch40_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch40_2026-09-24.md)。

**截至第四十批，按现存批次 JSON 可复算：** 101/281 个唯一故障码已有事件级 AI 审核快照，180 个故障码未覆盖；256/1041 个唯一候选 ID 已逐条复核，785 个候选 ID 未覆盖。批次文件之间没有重复故障码或候选 ID，且本次所审 4 个 ID 全部存在于 1041 条 manifest 候选中。注意：此前“截至第三十九批 99/253”的文字统计与实际 38 份批次 JSON 不符，按文件复算为 98/252；本节的 101/256 是当前可复核统计。全批次历史累计仍有 4 个事件标记可进入 preview builder，但不代表本次新建任何树；第四十批 Preview 为 0 棵，`fta_ready=false`，生产 FTA 仍未就绪。Gold、manifest 与数据库均未修改。

下一步继续从未覆盖的故障码中挑选证据完整、候选上下文可唯一定位的批次；遇到非唯一引文或证据/manifest 冲突时标记待人工定位，不自动补证。保持逐批 AI 角色复核、独立交叉检查和 `preview_only` 门禁，直到全量审核范围闭合；之后仍需单独复核逻辑门与 FTA 合同，不因候选覆盖完成而自动宣称生产建树就绪。

## 14. 第四十一批与当前累计进度（2026-09-24）

第四十一批检查 A01006、F01015、F01018，共 5 条候选；Laplace、Hegel、Popper 分别独立复核一条。所有候选引文均在完整 Gold `input_text` 中唯一匹配，位置为 0-based Unicode `[start,end)`。

- **A01006 / CR-CAND-001**：固件不适用于与 Control Unit 配合的条件有 Cause 原文支持，因果方向成立；Cause 范围内唯一条件已覆盖，但实际固件不适用的更深层原因未知。原文没有足够信息确定 AND/OR，因此不建树。
- **F01015 / CR-CAND-V5-172**：`An internal software error has occurred.` 只是顶事件状态复述，不是内部根因；实际 r0949 值缺失。与旧 manifest 的 `causal / source_to_target / fta_eligible=true` 及其历史 human 标志有实质冲突，记录为待治理分歧，不回写 Gold/manifest。
- **F01018 / CR-CAND-V5-173、CR-CAND-V6-126、CR-CAND-V7-099**：三项均由 `Possible reasons for booting being interrupted` 标题引出，完整覆盖该手册小节列出的可能原因。独立复核将其解释为**该清单范围内的局部 OR**，门证据定位到 Cause 标题 `[201,248)`；原文没有字面写 `OR`，所以这是明确标注范围的 AI 语义判断，而非引用到显式门符号。它不判断具体一次故障实际由哪一项引发，也不宣称穷尽所有现实根因。

按现有 Preview 合同，A01006 门未知、F01015 没有独立原因叶，均不建树；F01018 原因列表与范围内 OR 有证据，准入一棵 `preview_only` 局部 OR 预览。第四十一批 Preview 因此为 1 棵树（F01018），但 `fta_ready=false`、`production_ready=false` 不变。该树是 AI 授权角色审查的预览，不是真人专家签字或生产 FTA。

第四十一批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch41.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch41.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch41_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch41_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch41_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch41_2026-09-24.md)。

**截至第四十一批，按现存批次文件复算：** 104/281 个唯一故障码已有事件级 AI 审核快照，177 个未覆盖；261/1041 个唯一候选 ID 已复核，780 个未覆盖。40 份批次 JSON 中故障码与候选 ID 均无重复，所审候选均可在 manifest 中找到。累计可进入 Preview 的事件由 4 条增至 5 条；这只统计允许预览的树，不代表生产建树就绪。历史统计说明：按 Batch 39 时现存 38 份批次 JSON 复算为 98 个故障码、252 个候选；Batch 40 后为 101/256；本节 104/261 为当前口径。所有批次均未修改 Gold 或数据库，`fta_ready=false`。

继续下一批时，优先顺序仍是：在未审核记录中选取 context 已唯一定位的候选；对多个可能原因的记录，单独审查列表范围和门证据；门型不明确则保持 `unknown` 并不建树。AI 角色审核的全量完成也不自动等于真人专家确认或生产 FTA Ready。

## 15. 第四十二批与当前累计进度（2026-09-24）

第四十二批检查 F01023、F01034、F01036，共 3 条候选；Ramanujan、Carver、Beauvoir 分别独立复核一条。3 条引文均与完整 Gold `input_text` 唯一匹配，候选的精确跨度已在本批 JSON 中记录。

- **F01023 / CR-CAND-V5-176**：内部软件超时句子重述标题中的故障状态，不说明超时原因；`r0949` 无实际值，处理建议不反推为原因。旧 manifest 标为因果关系，本次 AI 复核不支持该判断；不建树。
- **F01034 / CR-CAND-V6-129**：参考参数变化与涉及参数无法按 per-unit 重新计算之间有明确因果表述，方向 `source_to_target` 成立；但未证明根因集合穷尽，且没有 AND/OR 依据。参数被拒绝并恢复原值是结果，p0595/p0596 设置建议属 Remedy；不建树。
- **F01036 / CR-CAND-V6-130**：下载时找不到备份文件的句子描述的就是故障状态，没有解释文件为何缺失，不支持将该候选当成独立上游原因。r0949 表格只是故障值编码说明，没有本次实际值；旧 manifest 的 causal/leaf 标记与本次复核不一致；不建树。

第四十二批 Preview 为 0 棵，`fta_ready=false`；Gold、manifest、数据库不修改。AI 独立审核指出的 manifest 历史 `human_reviewed` 标志与数据集中 AI 辅助身份存在冲突，仅记录为 provenance/分类待治理事项，不据此称真人签署。

第四十二批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch42.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch42.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch42_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch42_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch42_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch42_2026-09-24.md)。

**截至第四十二批，按现存 41 份批次 JSON 复算：**107/281 个唯一故障码已有事件级 AI 审核快照，174 个未覆盖；264/1041 个唯一候选 ID 已复核，777 个未覆盖。批次间无重复故障码和候选 ID。当前 5 个事件允许受限 preview；第四十二批未新增树，所有产物仍标记为 preview-only、`fta_ready=false`、非生产就绪。Gold 与数据库未改。

## 16. 第四十三批与当前累计进度（2026-09-24）

第四十三批检查 F01040、F01050、F01072，共 3 条候选；Parfit、Helmholtz、Dewey 分别独立复核一条。三条候选跨度均已在完整 Gold `input_text` 中逐字核验，记录为 0-based 半开区间。

- **F01040 / CR-CAND-V6-134**：参数更改是手册明确写出的“保存参数并执行 POWER ON”要求的触发条件，方向 `source_to_target`；但这是操作要求的触发关系，不是已查明的上游故障根因。候选引文 `[100,123)` 唯一匹配。单一条件不构成 AND/OR 组，原因集合对更上游根因不完整，不建树；该候选不作为 FTA 基本事件叶。
- **F01050 / CR-CAND-V6-218**：Cause 明确说明存储卡/设备类型不匹配会触发兼容性故障，方向 `source_to_target`；引文 `[90,201)` 唯一匹配。只确认 Cause 中这一项明示条件，未说明更上游原因，也无 AND/OR 依据，不建树。
- **F01072 / CR-CAND-V6-219**：手册明确说明写入存储卡期间控制单元掉电会导致可见分区损坏；随后从备份分区恢复属于恢复过程，不是额外原因。因果上下文 `[96,215)` 唯一匹配。手册未证明故障码整体原因集合穷尽，单条因果链也不能推出 AND/OR，不建树。

本批发现的旧 manifest `human_reviewed` / `fta_eligible` 与 Gold、context 中 AI 审核来源及当前语义复核之间的差异，作为来源/分类治理事项保留，不回写 Gold 或 manifest；本批审核者是用户授权的 AI 专家角色，不是真人领域专家签署。第四十三批 Preview 合同通过，树数为 0；`fta_ready=false`、`production_ready=false`，Gold 与数据库均未修改。

第四十三批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch43.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch43.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch43_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch43_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch43_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch43_2026-09-24.md)。

**截至第四十三批，按现存批次 JSON 复算：**110/281 个唯一故障码已有事件级 AI 审核快照，171 个未覆盖；267/1041 个唯一候选 ID 已复核，774 个未覆盖。42 份批次 JSON 之间无重复故障码或候选 ID，所审候选均可在来源 manifest 中找到。历史累计允许进入 Preview 的事件仍为 5 个；第四十三批未新增树。以上是 AI 审核覆盖率，不代表真人专家审核或全量 FTA 就绪；`fta_ready=false`、生产 FTA 不可用。

## 17. 第四十四批与当前累计进度（2026-09-24）

第四十四批检查 F31836、F01001、F01041，共 15 条候选；Godel、Hooke、Socrates 分别独立复核一条，主审对三条记录的完整 `input_text`、manifest 候选集合和 context 证据重新核对。

- **F31836 / CR-CAND-028、CR-CAND-V2-066**：CR-CAND-028 描述通信错误和数据未能发送，与顶事件“Send error for DRIVE-CLiQ data”重叠，不认作独立上游原因。Fault cause 65 的码义是可能故障原因定义，但文中没有 `r0949/r2124` 实际消息值；因此不确认具体实例命中该码义。无 AND/OR 证据，不建树。既有 manifest 对 CR-CAND-028 的 causal/FTA 叶标记与本次复核不同，保留为数据治理分歧，不改写原数据。
- **F01001 / 7 条候选**：Cause 句说明“basic system 或 technology function”可能导致异常，存在局部、可能性限定的 OR；FBLOCKS、DCC、TEC 是示例，不是穷尽子项。`An exception occurred...` 是顶事件复述；r0949 bit 0–4 是诊断枚举，未提供实际值；`r9999[2]` 只说明原因编号字段，没有编号实值。原因集合未闭合，因此虽记录局部 OR 文字，仍不建树。历史 manifest 将部分诊断枚举列为 causal/FTA eligible，与本次分类存在分歧，未回写。
- **F01041 / 6 条候选**：Cause 总述“启动时检测到存储卡文件损坏或缺失”是有原文支持的高层原因条件。其余 5 条是 `r0949` 故障值 1–5 的码义；没有实际值，不能当作本次已发生的五个独立原因，也不能仅凭枚举推出 OR。文本还提示有 additional values；原因覆盖不完整，不建树。Remedy 未被当作原因。

F31836 的独立复核者曾将原始字节 SHA 与 `source_dataset_sha256` 对照并提出差异；主审按 context 声明的规范化 JSON payload 哈希口径复算，证实 context 与当前 Gold 的规范化指纹一致，原始文件字节哈希差异仅是格式化口径不同，不是 Gold 被更改。该核对结论记录在本批产物中。

本批完整记录：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch44.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch44.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch44_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch44_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch44_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch44_2026-09-24.md)。

**截至第四十四批，按现存 43 份批次 JSON 复算：**113/281 个唯一故障码已有事件级 AI 审核快照，168 个未覆盖；282/1041 个候选 ID 已复核，759 个未覆盖。批次间故障码和候选 ID 均无重复；所有审核偏移都针对当前 Gold 原文验证。历史累计允许进入 Preview 的事件仍为 5 个；第四十四批未新增树。Gold 与数据库未修改，`fta_ready=false`、生产 FTA 不可用。

另：A30034 的 processor-area temperature 短语在原文重复两次，context 标为 `needs_manual_alignment`。依照“不自动挑选重复引文”的规则，该故障码不纳入第四十四批，也不计入上述覆盖数；待后续人工定位或获得能区分 bit 编号的确切源片段后再审核。下一批继续只选完整候选集可核对、偏移唯一的事件；遇到重复证据仍保留待定位，不为提升覆盖率猜选。

## 18. 第四十五批与当前累计进度（2026-09-24）

第四十五批检查 F30002、F30004、F07900，共 10 条候选；Mill、Ohm、Nash 分别独立复核一条。候选引文和门证据均在完整 Gold `input_text` 中唯一匹配，且主审重新检查了全记录、context 与既有 manifest。

- **F30002 / 3 条候选**：Cause 总述描述 DC-link 过压顶事件状态；三条项目符号是手册列出的直接可能原因。可在这份手册列表范围内视作完整的局部 OR，生成 1 棵 `preview_only` 树。没有实际 `r0949` 读数，因此不判定某一次实例具体由哪项触发，也不声称穷尽现实根因。
- **F30004 / 5 条候选**：温度越限总述是顶事件/阈值状态，不作为原因叶；其后四条 Cause 列表项按原样组成局部 OR，生成 1 棵 `preview_only` 树。`insufficient cooling, fan failure` 保留为一个证据节点，不根据逗号自行拆分。没有实际 `r0949` 温度值，不推断实例原因。
- **F07900 / 2 条候选**：手册描述两条信号触发路径，整体为 OR；每条路径内部还包含 AND 条件（持续时间/扭矩/速度阈值；速度振荡/控制器输出到限值）。原因路径在文字范围内完整，但当前 FTA 合同是 flat 单门结构，不能无损表达 OR-of-AND，也没有已审核的原子子事件，因此不建树、不把复合句压成假叶节点。此项揭示了嵌套逻辑树合同的后续设计需求，本批不扩展该合同。

以上 Preview 只展示手册明确列举范围内的局部结构，不代表因果关系 Gold 已改、现场实际原因已诊断或生产 FTA 就绪。Gold、manifest、数据库均未修改，`fta_ready=false`、`production_ready=false`。历史 manifest 中部分候选的 `fta_eligible` 状态与本次 AI 事件级判断不同，仅记为治理差异，不回写历史字段；审核者是用户授权的 AI 专家角色，不是真人签署。

第四十五批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch45.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch45.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch45_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch45_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch45_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch45_2026-09-24.md)。

**截至第四十五批，按现存 44 份批次 JSON 复算：**116/281 个唯一故障码已有事件级 AI 审核快照，165 个未覆盖；292/1041 个候选 ID 已复核，749 个未覆盖。批次间故障码和候选 ID 均无重复。历史累计允许进入 Preview 的事件从 5 增至 7；第四十五批新增 F30002、F30004 两棵局部 OR 预览，F07900 因嵌套门表达能力不足而不建树。所有 Preview 仍为 `preview_only`，生产 FTA 不可用。

## 19. 第四十六批与当前累计进度（2026-09-24）

第四十六批检查 F01680、F01682、F01700，共 13 条候选；Heisenberg、Darwin、Singer 分别独立复核一条，主审随后对照完整 Gold `input_text`、全部 manifest 候选和 context 证据完成裁定。所有 13 条候选引文及门证据均通过唯一原文匹配，偏移为 0-based `[start,end)`；Gold、manifest、数据库均未修改。

- **F01680 / 5 条候选**：校验和与参考值不匹配是故障状态；`Safety-relevant parameters have been changed or a fault is present` 仅支持一个含未具体化对象的复合可能原因，句内虽有 OR，但不能据此确定顶事件级门型或完整原子原因集合。r0949 的 0/1/2 是校验错误子类型说明，未提供实际值，不作为本次事件原因。STO 是故障后果，检查参数、Copy RAM to ROM、POWER ON 和验收测试属于 Remedy。本记录不建树。
- **F01682 / 5 条候选**：Cause 段支持“启用的监控功能不受当前固件版本支持”这一故障成立条件；r0949 的 20/21/59/9612 是诊断子类型，未提供实际值，且原文写明尚有 `Additional fault values`，所以子类型集合并不完整。不能把枚举值视为一次事件中实际发生的独立原因，也没有 AND/OR 门依据。本记录不建树。既有 manifest 的部分 causal/FTA 叶标记与本次事件级复核不同，仅作为治理差异留档。
- **F01700 / 3 条候选**：顶事件状态“驱动器通过 STO 停止”不作为自己的原因。`Possible causes` 下前两项是两个并列的可能触发条件；在该明确清单范围内可作受限 OR preview（OR 是语义解释，原文没有直接写出 OR）。第三项被原文称为 `subsequent response / following messages`，属于后续响应消息，不是原因。生成 1 棵仅反映清单范围的 `preview_only` 树，不表示某次现场事件的实际触发项，也不声称穷尽现实根因。

第四十六批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch46.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch46.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch46_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch46_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch46_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch46_2026-09-24.md)。

**截至第四十六批，按正式累计批次 Batch02–Batch46 的 45 份 JSON 复算：**119/281 个唯一故障码已有事件级 AI 审核快照，162 个未覆盖；305/1041 个候选 ID 已复核，736 个未覆盖。该正式累计范围内故障码和候选 ID 均无重复。仓库另存有 Batch01 的早期部分预审快照，其中 A01006/CR-CAND-001 后来由 Batch41 重新完整复核；Batch01 不计入正式累计，以免重复计数。本批新增 F01700 一棵受限局部 OR 预览，累计 8 个事件可进入 Preview；所有产物仍为 AI 角色审核快照，不是 Gold 或真人专家签署。`fta_ready=false`、`production_ready=false`，生产 FTA 不可用。

## 20. 第四十七批与当前累计进度（2026-09-24）

第四十七批检查 N30800、F13009、F13010，各 1 条候选；Anscombe、Hypatia、Einstein 分别独立复核一条，主审重新核对完整 Gold `input_text`、manifest 候选集合及 context。三条候选引文均唯一匹配原文，偏移为 0-based `[start,end)`；Gold、manifest、数据库均未修改。

- **N30800 / CR-CAND-030**：`The power unit has detected at least one fault` 是组信号/汇总状态，未给出其检测到的底层故障码或事件。不能把“至少一个”直接推成 OR，也无法定义原因集合，因此不建树。Remedy 要求评估其他消息，属于排查指引。
- **F13009 / CR-CAND-V10-299**：Cause 段 `[98,180)` 明确写出至少一个需要许可的 Technology Extension 未获许可，可作为该记录范围内的单一因果条件；未说明许可证为何缺失，也无多原因门型依据。Note 参数说明及输入/激活或停用扩展的建议分别属于参考信息和 Remedy，不增列为原因；不建 AND/OR 树。
- **F13010 / CR-CAND-V10-300**：Cause 段 `[146,211)` 明确写出至少一个需要许可的功能模块未获许可。r0949 的 bit 定义只是诊断映射，未给出本次实际 bit 值；许可证激活/停用均属 Remedy。虽然单一条件有因果文本支持，但无多原因集合和 AND/OR 门证据，不建树。

第四十七批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch47.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch47.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch47_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch47_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch47_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch47_2026-09-24.md)。

**截至第四十七批，按正式累计批次 Batch02–Batch47 的 46 份 JSON 复算：**122/281 个唯一故障码已有事件级 AI 审核快照，159 个未覆盖；308/1041 个候选 ID 已复核，733 个未覆盖。该正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 8 个，本批未新增树。本批及累计产物均为用户授权 AI 专家角色审核，不是真人专家签署，也没有写入 Gold。`fta_ready=false`、`production_ready=false`，生产 FTA 不可用。

## 21. 第四十八批与当前累计进度（2026-09-24）

第四十八批检查 F31875、N01004、F31950，各 1 条候选；Mill、Turing、Sagan 分别独立复核一条，主审逐条核对完整来源、候选集合与原文定位。三条候选引文均与完整 Gold `input_text` 唯一匹配，偏移为 0-based `[start,end)`。三位独立复核者均支持“不建树”，Gold、manifest 和数据库保持不变。

- **F31875 / CR-CAND-V16-270**：候选是 `Fault cause: 9` 后对“组件电源电压故障”的码义说明，偏移 `[255,310)`；原文没有本次实际消息值。它与故障状态相关，但不证明电压为何失效，不能作为已确认的独立上游原因。Cause 段只说明组件通过 DRIVE-CLiQ 向控制单元报告供电故障；Remedy 的上电、检查接线及核算电源容量不是原因。原因集合和门型均未闭合。
- **N01004 / CR-CAND-V16-291**：`An internal software error has occurred`（候选跨度 `[71,111)`）重述顶事件“Internal software error”，没有给出造成软件错误的上游机理。r0949 被限定为 Siemens 内部排查信息，读取诊断参数和联系技术支持属于 Remedy；不作为因果叶或门。
- **F31950 / CR-CAND-V16-289**：`An internal software error has occurred`（候选跨度 `[142,182)`）同样重述 Encoder 1 的内部软件错误状态。r0949 没有给出实际故障值，升级 Sensor Module 固件和联系技术支持属于 Remedy；不作为独立根因，也无 AND/OR 门依据。

第四十八批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch48.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch48.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch48_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch48_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch48_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch48_2026-09-24.md)。

**截至第四十八批，按正式累计批次 Batch02–Batch48 的 47 份 JSON 复算：**125/281 个唯一故障码已有事件级 AI 审核快照，156 个未覆盖；311/1041 个候选 ID 已复核，730 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 8 个，本批未新增树。审核均为 AI 专家角色结果，不是真人专家签署，不构成 Gold；`fta_ready=false`、`production_ready=false`。

## 22. 第四十九批与当前累计进度（2026-09-24）

第四十九批检查 F30043、F30682、F31135，各 1 条候选；Ramanujan、Godel、Leibniz 分别独立复核一条，主审重新核对完整原文、候选集合及证据跨度。全部候选和门证据均唯一匹配完整 Gold `input_text`；未改 Gold、manifest 或数据库。本批没有树进入 Preview。

- **F30043 / CR-CAND-V12-279**：`[80,151)` 的“电源上限已被超过”是过压事件的阈值状态/触发条件，未解释电压为何升高。r0949 只有编码格式及 24/48 V 通道映射，没有实际消息值；检查电源属于 Remedy。旧 manifest 虽标为 `causal`、`fta_eligible=true`，但事件级原因集合和 AND/OR 门均未闭合，因此不建树。
- **F30682 / CR-CAND-V13-302**：`[102,206)` 明确支持“启用的监控功能不受当前固件支持”这一单一因果条件。故障值只重复通用诊断文字，没有实际 r0949 值；Cause 未给多原因组合或 AND/OR 门。单条因果候选不等于完整树结构，因此不建树。旧候选叶资格也不能替代事件级门型审核。
- **F31135 / CR-CAND-V15-225**：候选 `[173,320)` 描述编码器报告单圈位置确定故障及其状态/故障字；后文 `[321,460)` 明确说明“部分 bit 会触发该故障，其他 bit 只是状态显示”。因此不能笼统声称原文完全没有因果线索；真正阻塞点是未提供本次实际 r0949 bitfield，不能选出触发位，也不能确认触发位之间的组合逻辑或完整原因集合。Remedy 也要求依据 fault value 再确定详细原因。故当前仍不建树。

第四十九批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch49.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch49.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch49_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch49_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch49_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch49_2026-09-24.md)。

**截至第四十九批，按正式累计批次 Batch02–Batch49 的 48 份 JSON 复算：**128/281 个唯一故障码已有事件级 AI 审核快照，153 个未覆盖；314/1041 个候选 ID 已复核，727 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；可进入 Preview 的事件仍为 8 个，本批未新增树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 23. 第五十批与当前累计进度（2026-09-24）

第五十批检查 F30050、F30051、F30055，各 1 条候选；Russell、Peirce、Ampere 分别独立复核一条，主审再次核对完整 Gold `input_text`、候选 ID、唯一证据跨度和现有 manifest/context。三位 AI 复核均支持本批不生成树；候选原文跨度均唯一匹配，偏移为 0-based `[start,end)`。Gold、manifest、数据库均未修改。

- **F30050 / CR-CAND-V12-280**：Cause `[87,150)`“电压监视器报告模块过压”是检测/状态信息，没有给出导致 24 V 过压的上游原因或实测值，不能作为因果叶，也不能由单句推 OR。额外发现旧 causal context 只覆盖完整 `input_text` 的 `[0,189)`，遗漏 `[192,224)` 的 Remedy “replace the module if necessary.”；本批审核使用完整原文，并把该上下文覆盖缺口记为数据质量问题。检查电源和必要时更换模块均仍是 Remedy，不作为已确认原因。
- **F30051 / CR-CAND-V12-281**：Cause `[109,180)`明确说明检测到电机抱闸端子短路，可作为该记录范围内的直接故障条件；但不能推断短路的更上游物理原因。`r0949` 没有实际值，Remedy 的检查建议不是已证实原因；单一因果条件没有 AND/OR 门证据，故不建树。旧 manifest 的候选级 `fta_eligible=true` 不替代本次事件级门禁。
- **F30055 / CR-CAND-V12-285**：Cause `[94,155)`“制动斩波器发生过电流”重述顶事件状态，没有解释上游根因。Remedy 中检查制动电阻短路或容量偏小只是待排查假设，不能提升为已发生原因；原因集合和逻辑门均未闭合。

第五十批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch50.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch50.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch50_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch50_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch50_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch50_2026-09-24.md)。本批 6 项合同测试通过，Preview 树数为 0。

**截至第五十批，按正式累计批次 Batch02–Batch50 的 49 份 JSON 复算：**131/281 个唯一故障码已有事件级 AI 审核快照，150 个未覆盖；317/1041 个候选 ID 已复核，724 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 8 个，本批未新增树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 24. 第五十一批与当前累计进度（2026-09-24）

第五十一批检查 A30730、A30788、A31700，共 8 条候选；Euclid、Galileo、Bernoulli 分别独立复核一条事件，主审重新核对完整 Gold `input_text`、manifest/context 候选集合及每个候选的唯一原文跨度。所有候选引文均精确匹配完整原文且只出现一次；没有修改 Gold、manifest 或数据库。

- **A30730 / CR-CAND-V5-130、CR-CAND-V6-097**：Cause `[118,176)`明确指出经 PROFIsafe 传入的 reference block 为负，是本记录陈述的直接故障条件；`r2124` 消息 `[426,461)`“requested, invalid reference block.” 是诊断标签，不是第二个上游原因。原文没有 reference block 为负的更深原因，也没有逻辑门，因此不建树。
- **A30788 / CR-CAND-V5-132、CR-CAND-V6-098、CR-CAND-V7-078**：开场句 `[101,174)`概括自动测试停止未能执行，是顶事件摘要，不作为树叶；两条 `Possible causes` 条目分别是通过 Safety Extended Functions 选择 STO `[194,253)`、以及存在导致 STO 的安全消息 `[256,308)`。这两项覆盖手册所列的可能原因清单，支持范围受限的局部 OR 预览；门证据为完整清单 `[175,308)`。该 OR 是对“Possible causes”并列项的语义推断，并非手册中的字面 OR，也不代表穷尽现实物理根因或某个实例的实际原因。
- **A31700 / CR-CAND-V5-139、CR-CAND-V6-101、CR-CAND-V7-079**：功能安全激活 `[97,128)`是运行情境；编码器自检检测到故障 `[130,186)`是告警层面的因果摘要，但没有说明编码器的上游物理根因；`r2124` 的 `Effectivity test x unsuccessful` `[238,269)`是条件性位映射，原文没有本次实际位值，不能实例化为故障树叶。门型未知，不建树。

另记录一项不回写的数据质量矛盾：A31700 的 `review_queue.status=confirmed_expert`，但 `annotation.human_expert_reviewed=false`，并且 `expert_review.reviewer_name` 标为 AI agent、`accepted_as_expert_by_user=false`。本批不把这个字段解释成真人签署。

第五十一批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch51.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch51.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch51_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch51_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch51_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch51_2026-09-24.md)。本批 6 项合同测试通过；仅 A30788 生成 1 棵受限 `preview_only` OR 树。

**截至第五十一批，按正式累计批次 Batch02–Batch51 的 50 份 JSON 复算：**134/281 个唯一故障码已有事件级 AI 审核快照，147 个未覆盖；325/1041 个候选 ID 已复核，716 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计 9 个事件可进入 Preview，本批新增 1 个。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 25. 第五十二批与当前累计进度（2026-09-24）

第五十二批检查 F01120、F01122、F01250，各 1 条候选；Carver、Kuhn、Archimedes 分别独立复核一条事件，主审核对完整 Gold `input_text`、候选集合与证据跨度。三条候选引文均唯一匹配完整原文；没有修改 Gold、manifest 或数据库。本批没有事件满足 AND/OR Preview 门禁。

- **F01120 / CR-CAND-V6-271**：Cause `[89,177)`指出 terminal functions 初始化期间发生内部软件错误，是解释初始化失败的概括性即时条件；内部错误的底层机理和 r0949 实际值均未给出。重启、升级固件、联系支持和更换控制单元属于 Remedy。按 `causal_summary` 处理，不作当前 FTA 原子叶；原因范围仅覆盖该 Cause 陈述，门型未知，不建树。
- **F01122 / CR-CAND-V6-272**：Cause `[102,171)`重述测量探头脉冲频率过高这一顶事件状态，未解释频率为什么升高。r0949 中 1/2/4 等 DI/DO 通道号是诊断映射，没有本次实际值；降低频率属于 Remedy。该候选为 `causal_summary`，上游原因未闭合，不建树。
- **F01250 / CR-CAND-V6-273**：Cause `[90,162)`说明控制单元 EEPROM 只读数据读取失败，是故障报告的即时状态，但没有说明为何读取失败。r0949 仅供 Siemens 内部排查且无实际值；POWER ON 和更换控制单元属于响应/Remedy。按 `causal_summary` 处理，不作为已查明的物理根因或 FTA 叶，不建树。

本批的 manifest 原候选曾标记 `fta_eligible=true`；该候选级状态不替代事件级根因完整性与 AND/OR 门审核，本次结论独立保存在审核快照中，不回写旧 manifest。

第五十二批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch52.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch52.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch52_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch52_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch52_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch52_2026-09-24.md)。本批 4 项合同测试通过，Preview 树数为 0。

**截至第五十二批，按正式累计批次 Batch02–Batch52 的 51 份 JSON 复算：**137/281 个唯一故障码已有事件级 AI 审核快照，144 个未覆盖；328/1041 个候选 ID 已复核，713 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批未新增树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 26. 第五十三批与当前累计进度（2026-09-24）

第五十三批检查 F01357、F01625、F01649，共 4 条候选；Rawls、Boyle、Hooke 分别独立复核一个事件，主审核对完整 Gold `input_text`、候选全集、context 复核记录及精确字符跨度。四条候选引文均与完整原文唯一匹配，偏移为 0-based `[start,end)`。本批只生成独立 AI 审核快照与零树 `preview_only` 结果，没有修改 Gold、manifest 或数据库。

- **F01357 / CR-CAND-V6-274**：`[116,206)` 描述两台控制单元通过 DRIVE-CLiQ 互连，是原文给出的直接拓扑条件；紧接着原文说明该配置通常不允许，但两台控制单元均安装并在线调试 OALINK 时例外 `[207,386)`。记录没有说明现场是否满足例外条件，也未解释更深层形成原因；`r0949` 仅说明连接号/组件号编码，无本次实际值。该候选可保留为直接因果条件，但原因集合与实例状态不完整，只有一个条件也不能推出 AND/OR 门，不建树。
- **F01625 / CR-CAND-V6-280、CR-CAND-V7-236**：`[267,346)` 列出 DRIVE-CLiQ communication error **or** communication has failed；`[347,407)` 另列 safety software time-slice overflow。第一条内部的 `or` 不能证明它和第二条之间也是顶层 OR；现有 flat AND/OR 合同也不能无损表达其内部层级。两条候选作为直接机制保留，事件级门型仍为 `unknown`，不压平、不建树。Cause 首句是检测/响应摘要；`r0949` 无本次实际值，Remedy 不作为原因。
- **F01649 / CR-CAND-V6-300**：`[85,174)` 将内部错误定位到 Safety Integrated 软件监控通道 1，属于能够解释报警的 `causal_summary`，但没有给出内部缺陷机理或更深根因。`r0949` 无实际值，STO 是后果/响应，升级、重新调试及更换均属 Remedy；门型未知、不建树。

补充状态边界：本批相关 context 虽记录了唯一原文匹配，但 `revalidation_status` 仍为 `pending_ai_context_re_review`；本次只核实完整来源中的跨度，不回写旧 context 状态，也不将该状态伪装成已完成复核。

第五十三批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch53.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch53.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch53_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch53_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch53_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch53_2026-09-24.md)。本批 5 项合同测试通过，Preview 树数为 0。

**截至第五十三批，按正式累计批次 Batch02–Batch53 的 52 份 JSON 复算：**140/281 个唯一故障码已有事件级 AI 审核快照，141 个未覆盖；332/1041 个候选 ID 已复核，709 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批未新增树（Batch02 的初始 Preview 文件名为 `...preview_v1...`，累计统计包含该文件）。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 27. 第五十四批与当前累计进度（2026-09-24）

第五十四批检查 F01655、F01658、F01670，共 12 条候选；Nash、Newton、Arendt 分别独立复核一个故障事件，主审核对完整 Gold `input_text`、manifest 全部候选及 context 证据。12 条候选引文均与完整原文切片精确一致，且每条引文全文唯一匹配；偏移为 0-based `[start,end)`。本批生成独立 AI 审核快照和零树 `preview_only` 结果，不修改 Gold、manifest 或数据库。

- **F01655 / 3 条候选**：对齐失败摘要不是上游叶节点；Cause 另列通信错误/中断和固件升级后未执行 POWER ON。通信候选内部含 `either/or`，原文没有说明它与另一条件之间的顶层关系。Cause 文本覆盖完整，但根因集合与事件门型未闭合，不建树。
- **F01658 / CR-CAND-V7-282**：`[95,164)` 明确指出 `p9611` 与 `r60022` 的 PROFIsafe 电报号设置不一致；第二句只是同一一致性要求的补充。该单一直接条件可确认，但手册未说明值为何不一致，也没有 AND/OR 门，不建树。
- **F01670 / 8 条候选**：一条 Cause 总述按 `causal_summary` 保留，不作为独立叶；其余 7 条是 `r0949=1,2,3,4,5,6,8` 对应的可能原因文本，全部逐一核验。手册没有本次实际 `r0949` 值，故不能选定现场分支；枚举本身不等于 AND/OR 证据，不建树。独立 AI 复核把 CR-CAND-V7-291 从历史 `associated_only` 重新评为 `causal_summary`；仅记录差异，不回写 manifest。

另记录两项历史数据状态问题：F01655 的 CR-CAND-V7-277 在 manifest 中 `candidate_text/target_description` 为空，但 context 与原文存在对应内容；本批三条记录的 context 虽显示唯一来源匹配，`revalidation_status` 仍为 `pending_ai_context_re_review`。本次不擅自关闭历史待复核状态。

第五十四批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch54.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch54.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch54_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch54_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch54_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch54_2026-09-24.md)。

**截至第五十四批，按正式累计批次 Batch02–Batch54 的 53 份 JSON 复算：**143/281 个唯一故障码已有事件级 AI 审核快照，138 个未覆盖；344/1041 个候选 ID 已复核，697 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 28. 第五十五批与当前累计进度（2026-09-24）

第五十五批检查 F01671、F01672、F01673，各 1 条候选；Hubble、Noether、Bohr 分别独立复核一个事件，主审核对完整 Gold `input_text`、manifest 候选全集和 context 证据。三条候选引文均与完整原文切片精确一致且全文唯一匹配，偏移为 0-based `[start,end)`；没有修改 Gold、manifest 或数据库。

- **F01671 / CR-CAND-V7-299**：`[96,219)` 明确指出 Safety Integrated 编码器与标准编码器的参数化不同，可作为单一直接条件；原因段文本覆盖完整，但 `r0949` 只说明不匹配参数号、没有现场值，也没有进一步解释不匹配原因。单一条件不能推出 AND/OR，不建树。
- **F01672 / CR-CAND-V7-300**：`[111,322)` 是一个复合软件兼容条件，并明确以 `or` 连接“两通道通信错误”替代分支（局部短语 `[248,322)`）。原文有局部 OR 语义，但这条候选没有拆成经审核的独立分支，原因集合也没有展开到更深层；故只在 `local_logic_observations` 留存原文逻辑，不将其冒充事件级已审核门，不压平成当前 FTA 树。
- **F01673 / CR-CAND-V7-301**：`[110,246)` 概括现有 Sensor Module 软件和/或硬件不支持安全运动监控功能，分类为 `causal_summary`，未说明具体软件缺陷、硬件缺陷或实例条件。`and/or` 只记录为单句内部未解析逻辑，不是事件级 AND/OR 门证据，不建树。

三条记录的候选 manifest `candidate_text` 均为空，但 context 和原文存在对应候选；context 虽显示唯一源匹配，`revalidation_status` 仍为 `pending_ai_context_re_review`。这些历史字段保持不变，仅在本批记录差异。

第五十五批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch55.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch55.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch55_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch55_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch55_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch55_2026-09-24.md)。

**截至第五十五批，按正式累计批次 Batch02–Batch55 的 54 份 JSON 复算：**146/281 个唯一故障码已有事件级 AI 审核快照，135 个未覆盖；347/1041 个候选 ID 已复核，694 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 29. 第五十六批与当前累计进度（2026-09-24）

第五十六批检查 F01679、F01689、F01690，共 5 条候选；Aquinas、Fermat、Avicenna 分别独立复核一个事件，主审核对完整 Gold 原文、全部候选和 context 证据。候选级证据按完整 `input_text` 唯一定位；本批无事件满足 Preview 门禁，不改 Gold、manifest 或数据库。

- **F01679 / 2 条候选**：`Safety parameters have been changed` `[137,172)` 与“随后对修改配置执行 partial power-up” `[259,331)` 覆盖 Cause 中的两个文本条件。它们呈现顺序关系，但不足以推断 AND/OR；`warm restart or POWER ON` 描述参数生效所需的操作选项，不是候选之间的逻辑门。旧 manifest 给第一条候选附的 `[137,332)` 跨度实际覆盖了两句，不能当作该单一候选的精确引文；本批以 context 的候选级短语在完整来源中重定位，并留下历史跨度问题记录。
- **F01689 / CR-CAND-V8-285**：`[81,157)` 描述轴配置更改并在内部设为正确值。独立审核者认为它只是 `associated_only`；主审核裁定为 `causal_summary`，因为原文将其直接放在 Cause 段并描述触发“Axis re-configured”告警的变更本身，但它不是上游 FTA 叶。两种判断的差异已保留，不回写历史标签；为何发生配置变化仍未知。
- **F01690 / 2 条候选**：Cause `[94,209)` 明确指出 NVRAM 空间不足，无法保存安全日志参数。r0949 故障值 1 的说明 `[313,367)` 只是重复“无剩余存储空间”这一状态；没有实际故障值时不把它计为第二个独立原因，也不推导 OR。其原因集合限于手册明示的直接存储容量条件。

第五十六批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch56.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch56.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch56_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch56_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch56_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch56_2026-09-24.md)。

**截至第五十六批，按正式累计批次 Batch02–Batch56 的 55 份 JSON 复算：**149/281 个唯一故障码已有事件级 AI 审核快照，132 个未覆盖；352/1041 个候选 ID 已复核，689 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 30. 第五十七批与当前累计进度（2026-09-24）

第五十七批复核 F01701、F01910、F01911，共 7 条候选；Curie、Plato、Kant 分别独立复核一个事件，主审核逐条核对 manifest/context 候选全集及完整 Gold input_text。7 条候选引文均全文唯一匹配，所有 branch/gate 引文也逐字校验。本批新增 0 棵 Preview 树；不修改 Gold、manifest、context 或数据库。

- **F01701 / CR-CAND-V8-291、CR-CAND-V9-253**：The drive is stopped using SS1. 是目标 SS1 停止响应/状态，不是上游原因；另一个监控通道的停止请求是原文明列的直接可能触发条件。原文中 p9556 超时或 p9560 速度阈值满足，描述的是后续 F01700 消息的输出条件，不是 F01701 原因之间的门。第二通道停止请求的上游来源未说明，事件原因链不完整，门型未知、不建树。
- **F01910 / 4 条候选**：setpoint 接收中断是故障状态摘要，按 causal_summary 保留，不作重复叶；总线连接中断、控制器关闭、控制器进入 STOP 是 Cause 中列出的三个直接条件。并列项目本身不能证明 OR 或 AND，底层触发原因也未展开；门型未知、不建树。
- **F01911 / CR-CAND-V8-304**：复合 Cause 候选直接描述时钟控制报文连续周期失败，或参数化时序网格被违反。原文 OR 及两个分支分别保留为精确证据，历史 associated_only 与本次复核的 causal 判断差异明确留痕；不回写 manifest/context。由于当前来源只提供一个合并候选，两个分支没有各自独立审核的稳定树叶身份，本批记录 logic_gate=OR 但 build_allowed=false，不把复合候选压成一片叶，也不生成树。

本批 context 的 revalidation_status 仍为 pending_ai_context_re_review；本次审核仅在独立快照中重新核实完整原文，不擅自关闭旧状态。

第五十七批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch57.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch57.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch57_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch57_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch57_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch57_2026-09-24.md)。本批 6 项合同测试通过，树数为 0。

**截至第五十七批，按正式累计批次 Batch02–Batch57 的 56 份审核 JSON 复算：**152/281 个唯一故障码已有事件级 AI 审核快照，129 个未覆盖；359/1041 个候选 ID 已复核，682 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；fta_ready=false、production_ready=false。

## 31. 第五十八批与当前累计进度（2026-09-24）

第五十八批复核 F01912、F01950、F03001，共 4 条候选；Maxwell、Bacon、Lorentz 分别独立复核一个事件。三条记录的全部 context 候选均为 verified_unique_source_match，主审核再次对照完整 Gold input_text 检查引文切片与全文唯一匹配。本批不修改 Gold、manifest、context 或数据库，Preview 树数为 0。

- **F01912 / CR-CAND-V8-305**：Cause 明确指出循环运行时控制器 sign-of-life 错误数超过许可值，按 causal_summary 保留为告警触发状态摘要，而非已确认的基本事件叶；底层错误为何累积未说明。Remedy 中的总线检查、trace、参数检查均不转成原因。门型未知、不建树。
- **F01950 / CR-CAND-V8-306、CR-CAND-V9-262**：Cause 分别记载同步到全局控制报文失败、内部时钟周期出现意外偏移。第一句实质重述目标故障，第二句虽是明示异常状态，原文没有明确说明它是前者的原因、结果还是伴随状态；两者均不构成已确认的上游因果边。两句相邻不构成 AND/OR 证据，不建树。
- **F03001 / CR-CAND-V8-308**：唯一候选“评估控制单元 NVRAM 数据时发生校验和错误”重述目标故障状态，按 associated_only 处理，不创建故障指向自身的因果边；下一句“受影响的 NVRAM 数据被删除”是后果，POWER ON 是 Remedy。底层校验和错误的起因未说明；门型未知、不建树。

三条记录的 Cause 候选范围已按手册直接陈述限定核对；这不等于现场更深层根因已查明或穷尽。context 中的历史 revalidation_status 仍为 pending_ai_context_re_review，本批不擅自关闭。

第五十八批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch58.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch58.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch58_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch58_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch58_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch58_2026-09-24.md)。本批 7 项合同测试通过，树数为 0。

独立复核分歧留痕：F01950 的 Bacon 将 CR-CAND-V8-306 视为 causal_summary，主审核按它与目标描述实质重述而裁定为 associated_only；V9-262 的因果方向原文未说明，主审核与独立复核均保留 associated_only。F01912 的主审核与独立复核均采用 causal_summary、且均不准作树叶；F03001 主审核与 Lorentz 均判为目标状态重述。完整裁决依据及历史标签差异保存在本批 JSON，不回写旧 manifest。

**截至第五十八批，按正式累计批次 Batch02–Batch58 的 57 份审核 JSON 复算：**155/281 个唯一故障码已有事件级 AI 审核快照，126 个未覆盖；363/1041 个候选 ID 已复核，678 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计可进入 Preview 的事件仍为 9 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；fta_ready=false、production_ready=false。

## 32. 第五十九批与当前累计进度（2026-09-24）

第五十九批复核 F07011、F07085、F07414，共 17 条候选；Wegener、Euler、Epicurus 分别独立复核一个事件。所有 context 候选均有唯一来源匹配，主审核再次对照完整 Gold input_text 检查全部候选与证据切片。Gold、manifest、context、数据库均未修改。

- **F07011 / 8 条候选**：Cause 段的“计算温度过高”是告警状态摘要；“电机过载、环境温度过高、传感器断线”是 Possible causes 中的直接可能原因。r0949 的 200/300/301/302 是诊断值解释，但本条没有实际 r0949 值，不能据此判定实例原因。301 值说明内部有 OR，只记录为局部诊断逻辑；事件门仍 unknown、不建树。
- **F07085 / 5 条候选**：开环/闭环参数被更改是目标行为摘要；其余四条是手册列出的可能原因。条目编号本身不证明 OR/AND，门型 unknown、不建树。
- **F07414 / 4 条候选**：手册分别编号 Cause 1–4：更换编码器、重新调试电机、更换带集成且已调整编码器的电机、更新到会检查编码器序列号的固件。四项均有唯一原文证据。按四个独立编号原因及 Remedy 按原因号分组，主审核采用范围受限的 OR，仅覆盖这四个手册列出的触发场景；生成 1 棵 preview_only 局部树，不表示编码器物理根因已穷尽，也不表示某一现场实例命中了哪一项。

F07414 的独立复核分歧：一位复核认为 Cause 1–4 的结构和按编号分组的 Remedy 足以支持限定范围的 OR；另一位因原文没有直接写 OR 或“任一项即可”而保持 unknown。主审核依据 Cause 1–4 各自独立列项、每项对应同一顶事件且 Remedy 按编号分组，采纳范围受限 OR；分歧与理由保存在批次 JSON。若需要更严格的字面逻辑门口径，可将其 gate 降为 unknown 并撤销本地预览树，但当前版不把它标成全量/生产 FTA。

F07011 的独立复核确认了本批“诊断值映射不能代替现场值”的判定。历史 manifest 的 V12（`causal` 且 `fta_eligible=true`）、V13（`not_supported`）、V14（`causal_summary`）均与本批按“未观测到 r0949 实值”作出的诊断映射分类存在差异；V14 的 manifest `candidate_text` 为空，但 context 和唯一原文跨度有文本支撑。本批只记录这些差异，不回写 manifest/context。

F07011 的 r0949 诊断值解释与本次现场实际值之间仍有信息缺口；三条记录的 context 历史 revalidation_status 仍为 pending_ai_context_re_review，本批不回写该状态。

第五十九批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch59.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch59.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch59_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch59_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch59_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch59_2026-09-24.md)。本批合同测试 7 项通过；F07414 生成 1 棵范围受限的预览树。

**截至第五十九批，按正式累计批次 Batch02–Batch59 的 58 份审核 JSON 复算：**158/281 个唯一故障码已有事件级 AI 审核快照，123 个未覆盖；380/1041 个候选 ID 已复核，661 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计进入 Preview 的事件为 10 个（含独立初始 `siemens_s210_causal_event_gate_preview_v1_2026-09-24.json`，而非 Batch02 专属产物），本批新增 1 棵。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 33. 第六十批与当前累计进度（2026-09-24）

第六十批审核 F07434、F07801、F07802，共 11 条候选；Aristotle、Ptolemy、Socrates 分别独立复核一个事件，主审核逐条核对完整 Gold `input_text`、manifest/context 候选全集及证据。全部候选引文在原文中唯一匹配；Gold、manifest、context、数据库均未修改。本批未生成 Preview 树。

- **F07434 / CR-CAND-V9-304**：原文唯一 Cause 句明确指出：在脉冲使能时选中了方向参数 p1821 不同的驱动数据组，直接解释无法改变旋转方向。作为一个复合运行/配置条件保留为 `causal`，不擅自拆成多个基本事件；原文没有事件级 AND/OR 门，也没有可审核的独立叶节点集合，不建树。范围完整仅指该手册 Cause 句，不声称现场物理根因已穷尽。
- **F07801 / 6 条候选**：`The permissible motor limit current was exceeded` 是目标报警状态摘要；后续 5 条是 Cause 段明列的可能触发原因。短路或接地故障这一候选内部存在原文 OR，但它不确定其余 4 个候选与该候选之间的整体事件门，因此事件门仍为 unknown、不建树。分支短语 `ground fault` 也出现在 Remedy 中，未自动选择重复文本的位置，标记待人工定位；完整候选句本身有唯一跨度，因此原因审核可以继续，但不能把这个局部逻辑变成建树证据。
- **F07802 / 4 条候选**：首句“内部启动命令后驱动未发出就绪状态”按目标状态摘要处理；直流母线无电压、驱动器损坏和电源电压设定错误是 3 条明确列出的可能原因。条目并列未说明 AND/OR，门型 unknown、不建树。

本批 Causes 的“范围完整”仅表示已逐条覆盖手册明确写出的 Cause 句和相邻原因条目，不等于所有现场根因穷尽。context 历史 `revalidation_status` 仍为 `pending_ai_context_re_review`，本批不更改该状态。

三位独立 AI 复核者均确认候选集合和唯一证据跨度。F07801 的复核确认短路/接地故障候选内部有明确 OR，但与其余可能原因之间的事件门仍 unknown；F07434 的单一复合 Cause 保留为未拆解原因候选，不认定为已验证基本事件；F07802 的首句按状态摘要与三个直接可能原因分开处理。另有复核者用原始字节 SHA 与 context 摘要比较时曾误报来源哈希不一致；主审核核验后确认 context 使用规范化 JSON 摘要，source 与前序 manifest 摘要均精确匹配，不存在该项来源冲突。

第六十批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch60.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch60.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch60_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch60_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch60_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch60_2026-09-24.md)。本批 8 项合同测试通过；Preview 树数为 0。

**截至第六十批，按正式累计批次 Batch02–Batch60 的 59 份审核 JSON 复算：**161/281 个唯一故障码已有事件级 AI 审核快照，120 个未覆盖；391/1041 个候选 ID 已复核，650 个未覆盖。正式累计范围内故障码和候选 ID 均无重复；累计进入 Preview 的事件仍为 10 个，本批新增 0 棵树。所有结论仍是用户授权 AI 专家角色审核，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 34. 第六十一批与当前累计进度（2026-09-24）

第六十一批审核 F08501、F13000、F13101，共 14 条候选；Carson、Mendel、Pasteur 分别独立复核一个事件，主审核逐条核对完整 Gold `input_text`、manifest/context 候选全集及证据跨度。所有候选引文在完整原文中唯一匹配；未修改 Gold、manifest、context 或数据库。本批未生成 Preview 树。

- **F08501 / 5 条候选**：`The reception of setpoints from the COMM BOARD has been interrupted` 是直接指向超时的中间因果状态，不是基本事件叶；其后四条分别列出总线连接中断、控制器关闭、控制器进入 STOP、COMM BOARD 故障。Cause 条目集合已覆盖，但并列没有明确 AND/OR，门型 unknown、不建树。
- **F13000 / 7 条候选**：Cause 段的两条直接陈述为“使用需要许可的功能但许可不足”和“检查现有许可时发生错误”。r0949=1–3 的映射用明确因果句指出运行中移除存储卡、缺少许可数据、密钥校验和错误，可作为通用条件式可能原因；value=4 的内部检查错误也是条件式原因候选，但可能与 Cause 段的一般检查错误重叠。value=0 只重述“许可不足”状态。原文没有现场 r0949 值，因此不能说某个分支已在具体实例发生；并且整体 AND/OR 未说明，门型 unknown、不建树。许可激活、插拔存储卡、重输密钥、POWER ON、升级固件等均是 Remedy，不列为原因。
- **F13101 / 2 条候选**：Cause 句“尝试激活存储卡复制保护时发生错误”是故障状态/摘要；r0949=0“未插入存储卡”可作为条件式可能原因，但无现场故障值，不能认定该分支在具体实例发生。来源没有完整的事件级 AND/OR 分解；插卡、POWER ON 和重试均属 Remedy；不建树。

三条记录的“原因范围完整”仅表示已复核手册明确列出的 Cause 和相关 fault-value 条目；不代表现场根因穷尽。旧 context 的 `revalidation_status` 仍为 `pending_ai_context_re_review`，本批不更改历史状态。

第六十一批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch61.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch61.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch61_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch61_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch61_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch61_2026-09-24.md)。本批 8 项合同测试通过；Preview 树数为 0。

**截至第六十一批，按正式累计批次 Batch02–Batch61 的 60 份审核 JSON 复算：**164/281 个唯一故障码已有事件级 AI 审核快照，117 个未覆盖；405/1041 个候选 ID 已复核，636 个未覆盖。正式累计范围内故障码和候选 ID 均无重复。累计 Preview 树为 10 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch61 复核产物合计 9 棵），本批新增 0 棵。AI 角色审核不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 35. 第六十二批与当前累计进度（2026-09-24）

第六十二批审核 F13102、F30001、F30005，共 17 条候选；Goodall、Gauss、Hilbert 分别独立复核一个事件，主审核重新对照 Gold 完整 `input_text`、候选 manifest/context、Gold causes 与证据跨度。三条事件的候选全集均与 Gold/manifest/context 对齐；17 条候选引文均在完整原文中唯一匹配。未修改 Gold、manifest、context 或数据库；本批 Preview 树数为 0。

- **F13102 / 4 条候选**：第一条是“检查受保护文件一致性时发现错误”的状态/诊断摘要，不作为独立上游原因边；r0949 的 `xxxx=1/2/3` 分别映射文件校验和错误、文件不一致、加载的项目文件不一致，可作为条件式可能原因，但没有实例故障值，不能确认哪一支发生。候选值编码不等于已审核的事件级 OR；整体门型 unknown、不建树。
- **F30001 / 10 条候选**：Cause 段十条可能原因均有证据。V11“电机短路或接地故障”内部存在明确 OR，只保留为该复合候选内部的局部 OR，不提升为顶事件门；r0949 的 bit 0–3 是过流相位/位置诊断，不能当作原因。十条候选整体门型 unknown、不建树。
- **F30005 / 3 条候选**：“电源模块过载”是状态摘要，后两项为额定电流超限过久、负载周期未保持两条可能原因。r0036=100% 与 r0949 I2t 标度是测量/诊断信息，不是额外原因。两项原因如何组合未说明，门型 unknown、不建树。Hilbert 独立意见把状态摘要理解为可指向故障的概括性条件；主审核裁定为 `describes_overload_state`、方向为空，不建立状态到目标本身的因果边，差异留痕。旧 manifest 中 `CR-CAND-V12-241` 的 reason 文本乱码；本批以可读原文和精确证据独立判断，不回写历史 manifest。

三条记录的候选范围完整，仅表示 Gold 候选覆盖当前手册显式列出的 Cause 与相关故障值条目；不能证明现实根因穷尽。历史 manifest 中个别候选的 `fta_eligible=true` 不等于事件级逻辑门已批准或整树可生成；最终事件门仍以审核结果为准。AI 独立复核不是真人领域专家签署，也不写入 Gold；`fta_ready=false`、`production_ready=false`。

第六十二批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch62.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch62.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch62_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch62_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch62_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch62_2026-09-24.md)。本批 8 项合同测试通过；Preview 树数为 0。

**截至第六十二批，按 Batch02–Batch62 的 61 份审核 JSON 复算：**167/281 个唯一故障码已有事件级 AI 审核快照，114 个未覆盖；422/1041 个候选 ID 已复核，619 个未覆盖。累计审核范围内故障码和 candidate ID 均无重复。累计 Preview 树为 10 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch62 复核产物合计 9 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 36. 第六十三批与当前累计进度（2026-09-24）

第六十三批复核 F30011、F30015、F30024，共 15 条 Cause 候选。主审逐条核对完整 Gold `input_text`、manifest/context 候选集合和唯一证据跨度；三位用户授权 AI 专家角色复核者各独立复核一个事件。所有候选引文均在完整原文中唯一匹配；未修改 Gold、manifest、context 或数据库。本批 Preview 树数为 0。

- **F30011 / 7 条候选**：纹波超限是故障状态摘要；后续六条 Possible causes 均逐条覆盖。直流母线电容、线路电感和集成电抗器的谐振候选保留整体机理，不伪拆基本叶；单相设备有功功率超限保留其适用条件。线路相失效和主回路熔断器熔断可能存在上下游或重叠关系，候选并列不足以证明整体 OR。独立复核者认为纹波状态可以指向故障；主审仍将其作为状态摘要，方向留空，避免建立状态到自身/目标的因果边。事件门 `unknown`，不建树。
- **F30015 / 2 条候选**：首句是检测到电机馈线电缆缺相的状态描述；第二句明确说明电机正确连接但速度闭环不稳定、产生振荡转矩时也可能输出同一信号。它支持“报警信号输出的替代触发工况”，但不支持“物理电缆确实缺相”。独立复核指出，若另行将顶事件定义为“F30015 信号输出”，两种信号情形可能形成范围有限的局部 OR；当前事件实体仍是物理电缆缺相故障，不能直接把该条件性 OR 套到现有故障实体，因此维持 `unknown`、不建树。电缆与速度控制器检查均为 Remedy。
- **F30024 / 6 条候选**：温差超限为超温状态摘要，后续五条原因均已覆盖。`insufficient cooling, fan failure` 保留为未拆解复合短语；原文不足以决定风扇故障与冷却不足的内部关系。旧 manifest 中 `CR-CAND-V13-219.candidate_text=null`，但 Gold/context 和唯一原文证据可相互核验；记录此历史字段缺口，不回写 manifest。独立复核者认为温差状态可以指向故障；主审仍按状态摘要处理，方向留空。整体 AND/OR `unknown`，不建树。

本批存在的意见差异均已留在审核 JSON 的 `data_quality_observations`，没有覆盖原 manifest 历史标签。完整 `input_text` 唯一跨度已复核，但 context 的 `revalidation_status` 仍为 `pending_ai_context_re_review`，本批不擅自关闭该状态。“原因范围完整”仅表示覆盖该手册记录明列的 Cause 项，不意味着现场物理根因穷尽。AI 角色审核不是真人专家签署，也不构成真人 Gold。

第六十三批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch63.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch63.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch63_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch63_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch63_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch63_2026-09-24.md)。本批 9 项合同测试通过；全量 Batch02–Batch63 审核批次回归共 137 项测试通过；Preview 树数为 0。

**截至第六十三批，按 Batch02–Batch63 的 62 份审核 JSON 复算：**170/281 个唯一故障码已有事件级 AI 审核快照，111 个未覆盖；437/1041 个候选 ID 已复核，604 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。累计 Preview 树仍为 10 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch63 批次产物合计 9 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 37. 第六十四批与当前累计进度（2026-09-24）

第六十四批审核 F30052、F30068、F30075，共 10 条候选；Lovelace、Locke、Faraday 三位用户授权 AI 专家角色分别独立复核一个事件。主审核对完整 Gold `input_text`、Gold causes、manifest/context 候选集合及证据偏移；10 条引文均在完整原文中唯一匹配。未修改 Gold、manifest、context 或数据库。本批生成 1 棵范围受限的 OR Preview，仍为 `preview_only`。

- **F30052 / 3 条候选**：EEPROM 数据错误句是目标状态摘要；r0949=0/2/3/4 对应读入数据不正确，r0949=1 对应 EEPROM 数据与应用固件不兼容。两条可作为条件式可能原因候选，但无本次实例 r0949 读数，不能确认哪一支实际发生；故障值枚举不自动决定事件门。门型 `unknown`，不建树。
- **F30068 / 3 条候选**：逆变器散热器温度低于允许下限是状态摘要；`Possible causes` 下的环境温度低于允许范围、温度传感器评估故障为两条完整且同层的可能原因。经回查 Batch46 的 F01700 先例，统一采用“完整、范围明确的 `Possible causes` 清单可作受限 OR 解释”的口径，只生成这两条子项的 OR Preview，不把温度状态摘要列为子事件。该树只覆盖手册明列范围，不代表现场原因穷尽、实例根因确认或生产 FTA。
- **F30075 / 4 条候选**：配置期间发生通信错误被判为指向配置失败的直接因果条件（`causal/source_to_target`），但“原因不清楚”意味着更深层机制未说明，故不列为已分解的基本事件叶。r0949=0/1/2 分别指出输出滤波器初始化、能量回馈功能启停、斩波器功能启停失败，按配置失败的诊断子类型处理，不提升为底层根因。事件门 `unknown`，不建树。独立复核者对通信错误与配置失败的直接因果关系提出意见后，主审采纳其方向，同时保留非叶裁决。

三条记录的原因范围完整性只表示覆盖手册中已标注的 Cause/故障值内容，不表示现场根因穷尽。context 的历史 `revalidation_status` 仍为 `pending_ai_context_re_review`；本批不回写或关闭该字段。独立审核者为 AI 角色而非真人专家签署，本批结果不进入真人 Gold；`fta_ready=false`、`production_ready=false`。

第六十四批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch64.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch64.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch64_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch64_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch64_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch64_2026-09-24.md)。本批 7 项合同测试通过；Batch02–Batch64 全部审核批次回归共 144 项测试通过；编译检查和 `git diff --check` 通过。

**截至第六十四批，按 Batch02–Batch64 的 63 份审核 JSON 复算：**173/281 个唯一故障码已有事件级 AI 审核快照，108 个未覆盖；447/1041 个候选 ID 已复核，594 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。累计 Preview 树为 11 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch64 批次产物合计 10 棵），本批新增 1 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 38. 第六十五批与当前累计进度（2026-09-24）

第六十五批复核 F30611、F30625、F30649，共 16 条候选。Pascal、Helmholtz、Hegel 三位用户授权 AI 专家角色分别独立复核一个事件；主审对完整 Gold `input_text`、Gold causes、manifest/context 候选集合及字符跨度逐项核对。16 条候选引文均在完整原文中唯一匹配。未修改 Gold、manifest、context 或数据库；本批不生成树。

- **F30611 / 12 条候选**：候选集合和证据跨度完整对应，但这不等于基本原因集合完整。r0949 同时列出参数索引、通道差异状态、条件触发项和诊断类别；本记录没有设备实例的 r0949 读数。V16 的 STO 反复选择/取消选择还可能是后续响应，因果方向不能统一；2001 明示也可能是其他故障的后续结果；6000…6999 只给出宽泛 PROFIsafe 诊断范围。原文 `alternatively` 只支持 F-DI 信号变化与 PROFIsafe STO 选择状态变化之间的局部替代关系，不能外推成 F30611 全局 OR。候选范围已审、根因叶集合未闭合，整体门 `unknown`，不建树。
- **F30625 / 3 条候选**：三项 Cause 子项均保留为条件性因果候选；首项的 `either…or…` 是该单条候选内部的局部 OR，不拆造候选 ID，也不决定三条顶层候选与故障事件之间的逻辑门。原文没有本次实例的故障值或状态观测，整体门 `unknown`，不建树。
- **F30649 / 1 条候选**：Cause 句“监控通道2的 Safety Integrated 软件内部错误”与目标标题 `Internal software error` 是同一故障状态的补充描述，不构成独立上游原因；保持候选 `not_supported`。STO 是故障结果，r0949 仅供 Siemens 内部排查且无实例值，原因分解不完整、门 `unknown`，不建树。单一候选数不能推出 `not_applicable`。

独立复核意见与主审裁定一致的重点包括：不从故障值枚举推断现场实例、不能把局部 OR 升格为全局事件门、不能把同义目标状态当自因果；候选关系、实例是否发生、基本事件叶资格和事件 AND/OR 分别记录。context 的历史 `revalidation_status` 仍为 `pending_ai_context_re_review`，本批不擅自关闭。独立复核者均为 AI 角色，不是真人专家签署，本批结果不进入真人 Gold；`fta_ready=false`、`production_ready=false`。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch65.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch65.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch65_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch65_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch65_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch65_2026-09-24.md)。本批 7 项合同测试通过；Batch02–Batch65 全部审核批次回归共 151 项测试通过；编译检查与 `git diff --check` 通过。

**截至第六十五批，按 Batch02–Batch65 的 64 份审核 JSON 复算：**176/281 个唯一故障码已有事件级 AI 审核快照，105 个未覆盖；463/1041 个候选 ID 已复核，578 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。批次 Preview 合计仍为 11 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch65 批次产物合计 10 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 39. 第六十六批与当前累计进度（2026-09-24）

第六十六批审核 F30655、F30656、F30659，共 6 条候选。Averroes、Volta、McClintock 三位用户授权 AI 专家角色分别独立复核一个事件；主审逐项对照完整 Gold `input_text`、Gold causes、manifest/context 候选集合和原文位置。6 条候选引文均在完整来源中唯一匹配。未修改 Gold、manifest、context 或数据库；本批不生成树。

- **F30655 / 1 条候选**：Cause 唯一条件明确写 `either … or …`，因此事件原因门可判为 `OR`。但两个替代通信分支被合并在一个候选 ID 中，尚无两个独立审核的叶节点；原因叶集合门禁未通过，故 `build_allowed=false`，不生成树。独立复核者将该候选类别描述为 `causal_summary`，主审按 Cause 中明确列出的通信条件记为 `causal`；双方对 source→target、非原子叶、OR 门及不建树结论一致，差异已记录在审核 JSON。
- **F30656 / 4 条候选**：Cause 句“访问 channel 2 安全参数时出错”与目标参数错误状态接近。独立复核者认为该句可标 `causal/source_to_target` 但不具备叶资格；主审按目标状态摘要归为 `causal_summary`，不建立自因果边。r0949=129/131/255 分别解释参数损坏和两个通道的软件错误诊断；没有实例 r0949 值，不能证明哪一诊断分支实际发生或它们是完整根因叶。事件门 `unknown`，不建树。
- **F30659 / 1 条候选**：唯一 Cause 句复述“参数写请求被拒绝”，并未说明上游原因；保持 `not_supported`，方向未知。F01659 是交叉引用、OFF2 是响应、固件升级是处理措施，均不补成原因。单候选不足以判断 `not_applicable` 或事件逻辑门，维持 `unknown`，不建树。

context 的候选证据重验状态仍是 `pending_ai_context_re_review`，本批不回写或关闭。AI 角色复核不是真人专家或 Siemens 签署，本批结果仅为 AI review/preview，不进入正式 Gold；`fta_ready=false`、`production_ready=false`。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch66.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch66.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch66_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch66_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch66_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch66_2026-09-24.md)。本批 7 项合同测试通过；Batch02–Batch66 全部审核批次回归共 158 项测试通过；脚本编译检查与 `git diff --check` 通过。

**截至第六十六批，按 Batch02–Batch66 的 65 份审核 JSON 复算：**179/281 个唯一故障码已有事件级 AI 审核快照，102 个未覆盖；469/1041 个候选 ID 已复核，572 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。批次 Preview 合计仍为 11 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch66 批次产物合计 10 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 40. 第六十七批与当前累计进度（2026-09-24）

第六十七批审核 F30674、F30680、F30700，共 7 条候选。Chandrasekhar、Feynman、Singer 三位用户授权 AI 专家角色分别独立复核一个事件；主审逐项核对完整 Gold `input_text`、Gold causes、manifest/context 候选集合和原文位置。7 条候选引文均在完整来源中唯一匹配。未修改 Gold、manifest、context 或数据库；本批不生成树。

- **F30674 / 3 条候选**：主审与独立复核将 V13（启用的安全监控功能不受当前 PROFIsafe 报文支持）判为该抽象层级的直接因果条件，方向 `source_to_target`，可作该层级叶；r0949 bit18、bit24 是故障值诊断子型，无实例位值，不作为独立已确认原因叶。此处与 manifest 将三条候选都标为因果且可建树叶的旧状态不同，具体差异留在本批审核记录。`weak_record.causes_text` 仅包含第一句，而 Gold causes/evidence 有三项，作为历史字段不一致记录。位值之间的关系未说明，事件门 `unknown`，不建树。
- **F30680 / 2 条候选**：V13 的校验和不匹配是目标报警状态摘要；V14 指出安全参数被更改“或”存在故障，是合并的可能条件摘要。句内 `or` 仅是候选内部的局部析取，尚未拆成独立叶；r0949 的 0/1 是诊断分型、不是实例读数。独立复核确认原因叶集合未闭合，事件门 `unknown`，不建树。
- **F30700 / 2 条 Gold 候选**：两条实际可能触发条件都被唯一定位；完整 Possible causes 列表第三项明确写为 subsequent response/following messages，归为下游响应/消息，不作原因。模型预测有 3 个 cause、Gold 有 2 个；第三项多抽差异被保留，未并入 Gold。主审与一位独立复核者对两条并列 Possible causes 能否依据项目既有先例解释为受限 OR 存在分歧；为遵守“门型有疑义则不建树”的保守要求，事件门记 `unknown`。第一条“另一监控通道的停止请求”是否可在 F30700 边界视为叶也有一处独立意见差异；本批不将其提升为最底层叶，因为该通道上游原因未展开。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch67.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch67.py)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch67_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch67_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch67_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch67_2026-09-24.md)。本批 7 项合同测试通过；Batch02–Batch67 全部审核批次回归共 165 项测试通过。

**截至第六十七批，按 Batch02–Batch67 的 66 份审核 JSON 复算：**182/281 个唯一故障码已有事件级 AI 审核快照，99 个未覆盖；476/1041 个候选 ID 已复核，565 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。批次 Preview 合计仍为 11 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch67 批次产物合计 10 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 41. 第六十八批与当前累计进度（2026-09-24）

第六十八批审核 A01631、A01699、F06310，共 4 条候选。Planck、Banach、Harvey 三位用户授权 AI 专家角色分别独立复核一个事件；主审逐项核对完整 Gold `input_text`、Gold causes、manifest/context 候选集合和原文位置。4 条候选引文均唯一定位。三条旧 context 的 `manual_evidence_alignment_required` 候选由本批在完整来源中重新定位；为兼容只读预览合同，另生成仅含本批 4 条候选的 scoped source-alignment overlay，保留原 context 文件及其哈希不变，并在派生行中保留原状态、记录定位前状态且仍标为待人工复核。未修改 Gold、原 manifest、原 context 或数据库；本批不生成树。

- **A01631 / 2 条候选**：CR-CAND-003 是“制动器/SBC 配置不切实际”的目标摘要，不作自因果边；CR-CAND-V2-002 是 Cause 下明确列出的“无电机制动器且启用 SBC”配置条件，方向 `source_to_target`。其中 `and` 是该复合候选内部的局部 AND，两个配置条件在原文中可分别唯一定位；但现有候选只有一个 ID，当前扁平 Preview 合同没有独立子叶，且手册说该配置“可导致”消息，不证明根因场景穷尽。独立 AI 复核认为可做仅覆盖该配置的 AND 子树；主审不拆造 Gold 候选身份，事件门 `unknown`、不建树，并记录意见差异。
- **A01699 / 1 条候选**：p9659 规定的 STO 强制测试停止间隔超限是直接触发条件，CR-CAND-004 可作该抽象层级的条件叶；后续“需要执行新检查”、STO 重新选择后的消息撤销/计时器复位、无安全停止响应说明及 Remedy 均不另算原因。单候选不推断 `not_applicable` 或 AND/OR，事件门 `unknown`、不建树。
- **F06310 / 1 条候选**：Cause 及公式支持预充电完成后直流电压超出容差范围的条件；完整原文还限定 `For AC/AC drive units`。Gold 候选未保留这个适用范围，因此本批证据跨度补入限定，但不回写 Gold，当前候选暂不作为无条件 FTA 叶。独立 AI 复核建议单原因记 `not_applicable`；主审按项目既定“单候选不推门”规则保留 `unknown`，不建树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch68.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch68.py)、[AI 源文定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch68_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch68_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch68_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch68_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch68_2026-09-24.md)。本批 8 项合同测试通过；Batch02–Batch68 全部审核批次回归共 173 项测试通过。

**截至第六十八批，按 Batch02–Batch68 的 67 份审核 JSON 复算：**185/281 个唯一故障码已有事件级 AI 审核快照，96 个未覆盖；480/1041 个候选 ID 已复核，561 个未覆盖。累计审核范围内故障码与候选 ID 均无重复。批次 Preview 累计仍为 11 棵（独立初始 Preview v1 为 1 棵，Batch03–Batch68 批次产物合计 10 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 42. 第六十九批与当前累计进度（2026-09-24）

第六十九批审核 F30027、F31887、A01711，共 25 条候选。Popper、Halley、Hume 三位用户授权 AI 专家角色分别独立复核一个事件；主审对完整 Gold input_text、Gold causes、manifest/context 候选集合和字符跨度逐项核对。5 个候选原 context 标为 manual_evidence_alignment_required，由主审在完整来源中重新定位；A01711 两条候选各需要两段原文共同支持诊断值与参数映射，因此合计保留 7 个精确跨度。原 context、Gold、manifest 和数据库均未修改。

- **F30027 / 10 条候选**：Cause 首句是预充电超时状态摘要，不作为自因果；后续 9 个编号 Cause 项均是手册列出的条件性可能原因。编号列表本身是否足以推出受限 OR，独立 AI 复核与主审有分歧：独立复核认为可在手册范围内作 OR；主审依据既有门控先例保留 unknown，因为原文未明确组合规则。第 9 项又把 ground fault / short-circuit 合并在单个候选 ID 中。候选均已复核，但事件不建树。
- **F31887 / 6 条候选**：32/35/66/67/96/97 是 Fault cause 消息值下的条件性故障模式；“Faulty hardware cannot be excluded”可作为未确认的条件性硬件假设，但不代表本次设备实例已发生。发送错误原句出现两次，证据绑定 66 和 67 两个消息值标签所在的完整唯一文本块，不任意挑选一个重复位置。事件门 unknown，不建树。
- **A01711 / 9 条候选**：区分报警状态摘要、明确 Possible cause、以及 r2124 消息值诊断定义；原文另有 incorrect synchronization，但 Gold 没有独立候选 ID，本批不虚构候选。V10/V11 需要分别引用参数映射和对应消息值说明，不能只靠单一跨度支持候选中的全部内容。原因全集相对完整诊断表未闭合，且没有实例 r9725/r2124 读数；事件门 unknown，不建树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch69.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch69.py)、[AI 源文定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch69_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch69_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch69_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch69_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch69_2026-09-24.md)。本批 10 项合同测试通过；Batch02–Batch69 批次回归共 183 项测试通过；Preview owner 40 项测试和 context revalidation 5 项测试通过；Python 编译检查与 git diff --check 通过。

**截至第六十九批，按 Batch02–Batch69 的 68 份审核 JSON 复算：**188/281 个唯一故障码有事件级 AI 审核快照，93 个未覆盖；505/1,041 个候选 ID 已复核，536 个未覆盖。累计审核范围内故障码和候选 ID 均无重复。批次 Preview 仍累计为 11 棵（独立初始 Preview v1 为 1 棵、Batch03–Batch69 共 10 棵），本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 43. 第七十批（2026-09-24）

第七十批审核 A01784、A30034、F01005，共 38 条候选。Euler、Curie、Raman 三位用户授权 AI 专家角色分别独立复核一个事件；主审核对完整 Gold `input_text`、全部 Gold causes、manifest/context 候选集合与原文字符跨度。4 条缺失或歧义来源在完整原文中重新定位，形成仅限本批的 source-alignment overlay；原 context、Gold、manifest 和数据库均未修改。三条事件的原因集合或逻辑门未闭合，本批新增 0 棵树。

- **A01784 / 17 条候选**：2019 原文把 bit17 的原因指向 bits 0–10，但列表缺少 bit7；bits20–26 是报警值诊断状态，未明确列入 bit17 的原因列表。bits4/8 的局部 OR 不能推出事件全局门，p1217 处理段中的条件也不足以证明它是 A01784 的独立直接原因叶。保持原因集合未闭合、事件门 `unknown`、不建树。另发现样本 provenance 的 `source_pdf` 标为 2019，但 `official_reference_url` 指向 04/2024 版本；审核只按嵌入的 2019 原文裁定，不把后续版本的 bit7 定义回填到 Gold，并将来源版本不一致单独列为数据质量问题。
- **A30034 / 8 条候选**：Cause 明确列出环境温度可能过高、冷却不足/风扇故障；区域过热位属于诊断子型。bit4 与风扇故障候选语义重叠且无实例 `r2124` 值，不升格为独立基本事件；处理器区域文本分别对应 bit2 与 bit3，保留两条带标签的精确跨度。原因集合未闭合、事件门 `unknown`、不建树。
- **F01005 / 13 条候选**：公开故障值映射可作为条件性故障模式，但没有本次实例 `r0949` 值；Cause 摘要不作为自因果，boot-loader 加载属于升级过程/诊断状态，复合条件不拆造成虚构叶。手册说明另有仅供 Siemens 内部排查的 `Additional values`，公开原因集合不完整；事件门 `unknown`、不建树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch70.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch70.py)、[AI 源文定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch70_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch70_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch70_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch70_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch70_2026-09-24.md)。Batch02–Batch70 的批次合同回归共 193 项测试通过；FTA Preview owner 40 项测试、context revalidation 5 项测试通过；Python 编译检查与 `git diff --check` 通过。

**截至第七十批，按 Batch02–Batch70 的 69 份审核 JSON 复算：**191/281 个唯一故障码有事件级 AI 审核快照，90 个未覆盖；543/1,041 个候选 ID 已复核，498 个未覆盖。累计审核范围内故障码和候选 ID 均无重复。各批次 Preview 合计 10 棵，另有独立初始 Preview v1 的 1 棵，合计 11 棵；本批新增 0 棵。审核者为用户授权 AI 角色，不是真人专家签署，不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 44. 第七十一批与当前累计进度（2026-09-24）

第七十一批审核 F01042、F01043、F01082，共 128 条 Gold 候选。Raman、Cicero、Parfit 三位用户授权 AI 专家角色分别独立复核一个事件；主审核对完整 Gold `input_text`、Gold causes、manifest/context 候选集合和原文字符跨度。本批对 10 条原 context 标记为歧义/错位的候选重新定位，使用完整参数值编号行，共保留 14 个精确跨度；相同短语映射多个编号时保留全部编号行，不任意选一条。定位结果只写入本批 scoped overlay，原 context、Gold、manifest 与数据库不变。

- **F01042 / 51 条候选**：49 个参数故障值模式是有条件的可能故障原因，不代表当前设备实例已发生；开头 Cause 句为摘要，参数限制依赖关系证据不足。`r0949` 编号表不是事件级逻辑方程，也没有实例参数读数，原因集合未闭合、事件门 `unknown`，不建树。
- **F01043 / 26 条候选**：区分具体配置/对象错误、故障摘要、状态/诊断及恢复信息；“Additional values”仅供 Siemens 内部排查，公开原因值不完整。另将旧 manifest 中错指 Drive 状态行的 Device 状态证据，在 scoped overlay 中定位到正确的 Device 行；不回写来源文件。事件门 `unknown`，不建树。
- **F01082 / 51 条候选**：参数故障值映射是条件性候选，不是实例观测；概要句不作独立原因，试探性的参数依赖关系标为无法确定。发现 `CR-CAND-V6-220` 在 manifest/context 中标为 `human_gold_v7_existing`、`human_reviewed=true`，但其父故障记录 annotation 仍写 `human_expert_reviewed=false`、`unlabeled_public_corpus`。本批保留该状态矛盾为数据质量警告，不修改 Gold 或状态源。事件门 `unknown`，不建树。
- 三条来源记录的 `source_pdf`/嵌入文本指向 2019 版，而官方链接指向 2024 版。本批只按嵌入的 2019 原文审核，不将新版信息倒灌至旧版数据。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch71.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch71.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch71_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch71_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch71_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch71_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch71_2026-09-24.md)。Batch02–Batch71 批次合同回归共 202 项测试通过；FTA Preview owner 40 项测试、context revalidation 5 项测试通过；本批 Python 编译检查通过，`git diff --check` 通过（Git 仅报告工作区已有文件的 LF→CRLF 提示）。

**截至第七十一批，按 Batch02–Batch71 的 70 份审核 JSON 复算：**194/281 个唯一故障码有事件级 AI 审核快照，87 个未覆盖；671/1,041 个候选 ID 已复核，370 个未覆盖。批次范围内故障码与候选 ID 均无重复。所有批次 Preview 文件累计生成 10 棵树（另有独立初始 Preview v1 的 1 棵）；本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 45. 第七十二批与当前累计进度（2026-09-24）

第七十二批审核 F01600、F01630、F01650，共 32 条候选。Laplace、Tesla、Confucius 三位用户授权 AI 专家角色分别独立复核一个事件；主审核对完整 Gold `input_text`、Gold causes、manifest/context 候选集合和原文字符跨度。8 条原 context 标记为需人工定位的候选在完整来源中重新核对，保留 10 个精确跨度；重复短语覆盖到多个故障值时，引用各自带编号的完整原文块，不任意择一。来源版本疑问及审核状态冲突均作为警告记录，不覆盖 Gold、manifest、context 或数据库。

- **F01600 / 5 条候选**：测试停止失败与另一监控通道停止请求是原文明示的可能条件；r0949=1005/1010 两条状态映射虽有文本支持，但其因果触发还是诊断状态无法仅凭表格确认，故保留 `cannot_determine`。原文还提到 F01611 的后续响应，不作为普通上游基本原因。发现继承的 Gold 审核字段称 `correction_applied=true`，却没有 `modified_content`，Gold 内容仍保留该审核意见称需删除的若干候选；本批只记差异、不改 Gold。
- **F01630 / 10 条候选**：直接 Cause 中的 OCC 屏蔽层错误连接、制动控制回路缺陷被区分于 r0949 对应的运行/状态诊断类别；“制动器未闭合或电缆中断”及“制动绕组短路”分别关联两个故障值组，所有带值上下文均保留。局部 `or` 不推成顶事件 OR，原因集合和事件门均未闭合。
- **F01650 / 17 条候选**：区分验收测试需求摘要、不同 r0949 值的条件触发、调试说明和另一安全故障的后续响应；没有实际 r0949 读数，不能把任一条说成当前实例根因。`CR-CAND-V6-301` 的 manifest/context “human-reviewed”标记与样本 annotation 的未标注状态冲突；本批按 AI 角色审核记录，不声称真人签署。
- 三条原文来源元数据均标 2019 文本、官方链接指向 2024 手册。本批只按嵌入的 2019 `input_text` 核验，不从新版补内容。三条事件的 cause set 没有达到 FTA 门禁所需的关闭状态，event gate 均 `unknown`，不建树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch72.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch72.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch72_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch72_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch72_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch72_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch72_2026-09-24.md)。Batch02–Batch72 批次合同回归共 211 项测试通过；FTA Preview owner 40 项测试、context revalidation 5 项测试通过；本批 Python 编译检查和 `git diff --check` 通过（Git 报告的是工作区已有文件 LF→CRLF 提示）。

**截至第七十二批，按 Batch02–Batch72 的 71 份审核 JSON 复算：**197/281 个唯一故障码已有事件级 AI 审核快照，84 个未覆盖；703/1,041 个候选 ID 已复核，338 个未覆盖。批次范围内故障码与候选 ID 均无重复。当前批次 Preview 文件共 70 份、合计生成 10 棵树（另有独立初始 Preview v1 的 1 棵）；本批新增 0 棵。AI 角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 46. 第七十三批与当前累计进度（2026-09-24）

第七十三批审核 F01653、F01659、F01681，共 31 条 Gold cause 候选。Descartes、James、Zeno 三位用户授权 AI 专家角色分别独立复核一个事件；主审核逐条核对完整 Gold `input_text`、候选清单、manifest/context 与字符跨度。本批 5 条 context 标为需人工定位的候选在完整来源中重新对齐，覆盖 7 个精确跨度；F01653 的两种重复“错误长度”分别保留 230/231、330/331 全部故障值标签，不任选一个位置。原 Gold、manifest、context 和数据库均未修改。

- **F01653 / 8 条候选**：8 条均是手册列出的条件性 PROFINET/安全槽配置原因，不是现场实例读数。完整 Cause 摘要句未进入 Gold 候选表，作为 `causal_summary` 单独记为未映射来源项；故障导致 STO 的 Note 是结果，不反向当原因。r0949 映射没有事件级逻辑方程，原因集合与 gate 未闭合。
- **F01659 / 7 条候选**：7 条均是导致安全参数写请求被拒绝的条件映射；其中不支持的组合请求保留为一个完整潜在配置叶，不拆成臆造子事件。通用 Cause 摘要句也单独登记为未映射摘要。原文明确说明该故障不产生安全停止响应，审核未把它误作安全停止故障。
- **F01681 / 16 条候选**：15 条具体参数/配置条件映射判为条件因果候选；通用 Cause 句属于 `causal_summary`，不是单独基本原因。对 SCC/epos 同时启用、F-DI/PROFIsafe 配置冲突等复合状态，独立审核者对“整项配置是否可作为潜在叶”有口径差异；本批按整项配置事件保留，不拆子事件，也不由局部 `and/or` 推导顶事件门。`xxxx=9501` 的原始 Cause 引文按双引号和带值完整块重新定位。
- 三条故障值表都只是手册映射，没有本次设备实例的 r0949 读数；没有证据证明现场原因集合完整，也没有事件级 AND/OR 依据。三条事件均为 `logic_gate=unknown`、`build_allowed=false`，本批新增 0 棵树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch73.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch73.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch73_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch73_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch73_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch73_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch73_2026-09-24.md)。本批 7 项合同测试通过；Batch02–Batch73 批次合同回归共 218 项测试通过；FTA Preview owner 40 项测试、context revalidation 5 项测试通过；Python 编译和 `git diff --check` 通过（Git 仅报告此前已修改文件的 LF→CRLF 提示）。

**截至第七十三批，按 Batch02–Batch73 的 72 份审核 JSON 复算：**200/281 个唯一故障码已有事件级 AI 审核快照，81 个未覆盖；734/1,041 个候选 ID 已复核，307 个未覆盖。累计范围内故障码、候选 ID 均无重复。批次 Preview 累计仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入 Gold；`fta_ready=false`、`production_ready=false`。

## 47. 第七十四批与当前累计进度（2026-09-24）

第七十四批审核 F01800、F07093、F07220，共 15 条 Gold cause 候选。Herschel、Sartre、Pauli 三位用户授权 AI 专家角色分别独立复核一个事件，主审对完整嵌入原文、候选、manifest/context 和字符跨度逐项复核。7 条来源定位待重验候选在完整来源中由 AI 审核者唯一定位，覆盖 7 个完整跨度；来源重定位只写入 Batch74 scoped overlay，未回写 Gold、manifest、原 context 或数据库。

- **F01800 / 5 条候选**：V8 是重述故障状态的摘要，改判 `associated_only`；V9/V10 是带嵌套可能机制的条件因果复合项，不视为原子叶；V11 是连接检测重复故障状态；V12 按原文“probably defective”保留为带概率限定的因果假设，但不是现场确认或基本叶。记录 Gold、manifest、context 对部分分类/证据状态不一致，不覆盖父文件。Cause 摘要和 4 组 r0949 故障值均被覆盖，但物理根因集合未闭合。
- **F07093 / 7 条候选**：r0949=1–7 的条件故障值映射均为因果候选，且只在本故障局部抽象下标记为潜在叶候选；这不是现场实测、FTA 根因全集闭合，也不授权推导 OR 门。Cause 首句作为未映射摘要单独记录；“function was not executed or was canceled”标为关联结果，不作为第八个原因。V10/V12 的参数遗漏型候选通过故障值标签唯一定位并写入 scoped overlay；另记录旧 manifest 的 `fta_eligible` 口径与本轮潜在叶判断不一致。
- **F07220 / 3 条候选**：三条 Cause 项均是原文支持的可能原因，方向为候选原因到故障。V9 是当前抽象下的潜在叶；V10 上位控制撤销、V11 总线中断可能仍是中间事件，不确认基本叶。Gold 前两条证据跨度缺少末尾标点，本轮 overlay 引用完整 Cause 行；V11 的 context 跨入 Remedy，本轮仅用 Cause 原句作证据。三项文本来源覆盖完整不等于物理根因集合穷尽。
- 三条记录都没有设备实例读数和明确事件级 AND/OR 方程，`cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；本批新增 0 棵树。AI 审核被用户授权作为本轮审核结果，但不是 Siemens 真人签署，且不写入正式 Gold。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch74.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch74.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch74_2026-09-24.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch74_2026-09-24.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch74_2026-09-24.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch74_2026-09-24.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch74_2026-09-24.md)。本批 8 项合同测试通过；Batch02–Batch74 批次合同回归 226 项通过；FTA Preview owner 40 项、context revalidation 5 项通过；本批 Python 编译通过，`git diff --check` 通过（仅有工作区既有文件的 LF→CRLF 提示）。

**截至第七十四批，按 Batch02–Batch74 的 73 份审核 JSON 复算：**203/281 个唯一故障码已有事件级 AI 审核快照，78 个未覆盖；749/1,041 个候选 ID 已复核，292 个未覆盖。累计审核范围内故障码和候选 ID 均无重复。批次 Preview 文件共 72 份；累计生成树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。`fta_ready=false`、`production_ready=false`。

## 48. 第七十五批与当前累计进度（2026-09-25）

第七十五批审核 A01009、A01698、A01706，共 4 条 Gold cause 候选。Ramanujan、Pauli、Herschel 三位用户授权 AI 专家角色分别独立复核一个事件；主审重新核对完整嵌入原文、Gold cause、manifest/context 候选集合和证据跨度。4 条候选均在完整 `input_text` 中找到唯一原文位置；其中 A01706 两条原 context 未对齐的候选，通过保留 `p9506` 模式标签的完整 Cause 段重新定位。对齐结果仅写入 Batch75 scoped overlay，Gold、基础 context、manifest 和数据库均未修改。

- **A01009 / 1 条候选**：`The temperature (r0037[0]) ... has exceeded the specified limit value.` 是报警触发条件，作为潜在叶仅限“报警触发条件”这一抽象，不解释控制单元为何过热，也不是设备实例读数。Gold/manifest 候选文字遗漏了参数 `r0037[0]` 和句末标点；overlay 保留完整唯一原句。Remedy 中的进风口/风扇检查是排查动作，Note 中报警撤销条件是恢复行为，不提升为原因。原因集合与事件级门未闭合，不建树。
- **A01698 / 1 条候选**：调试模式被选中是与状态消息相关的运行/配置状态，不是独立设备故障叶。Pauli 独立意见建议标为 `causal_summary/describes_fault_state`；主审裁定保留 `associated_only/associated_with`，因为该文本描述的是状态消息本身，未给出独立故障机制。两种分类都不支持 FTA 建树。原文明确指出该消息不会导致安全停止响应；不能把“内部选择 STO”解释成实际发生安全停车。Gold/manifest 证据缺句末句点，overlay 中为完整原文唯一跨度。
- **A01706 / 2 条候选**：SAM (`p9506=0`) 和 SBR (`p9506=2`) 两段均支持相应模式下速度超出容差的条件性因果候选；它们不是本次设备的参数读数、速度曲线或现场事件。Herschel 提出在模式触发条件局部抽象下按 `OR` 做 preview-only 树；主审保留 `logic_gate=unknown`、`build_allowed=false`：两个参数模式标签本身不能证明原因集合穷尽，也没有明示顶层事件布尔方程。依照“原因集合或 AND/OR 未知则不建树”的既定门禁，不生成树。F01700 停车句是结果/交叉引用，PROFIsafe 确认及 Remedy 是确认/处理信息，不是上游原因。
- 本批 3 个事件的 `cause_set_complete=false`、事件门 `unknown`、`build_allowed=false`；本批新增 0 棵树。独立意见与主审裁定的差异已结构化写入审核 JSON 和 Markdown，没有伪装成一致，也没有回写正式 Gold。AI 授权审核不是真人 Siemens 专家签署，`fta_ready=false`、`production_ready=false`。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch75.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch75.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch75_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch75_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch75_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch75_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch75_2026-09-25.md)。Batch02–Batch75 批次合同回归 236 项通过；FTA Preview owner 40 项、context revalidation 5 项通过；本批 Python 编译检查和 `git diff --check` 通过（仅显示工作区既有文件的 LF→CRLF 提示）。

**截至第七十五批，按 Batch02–Batch75 的 74 份审核 JSON 复算：**206/281 个唯一故障码已有事件级 AI 审核快照，75 个未覆盖；753/1,041 个候选 ID 已复核，288 个未覆盖。累计审核范围内故障码和候选 ID 均无重复。批次 Preview 文件共 73 份、累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。`fta_ready=false`、`production_ready=false`。
## 49. 第七十六批与当前累计进度（2026-09-25）

第七十六批审核 F07410、F07412、F07575，共 21 条 manifest 候选项（其中包含故障值诊断关联项，不应统称为 21 条因果 Gold）。Kant、Galileo、Nash 三位用户授权 AI 专家角色分别独立复核一个事件；主审对完整 Gold `input_text`、候选文本、manifest/context 集合和字符跨度逐项复核。21 条候选证据均在完整原文中唯一匹配；两处历史引文格式/截断问题仅通过 Batch76 scoped overlay 修复，未回写 Gold、manifest、基础 context 或数据库。

- **F07410 / 4 条候选**：条件摘要 `I_act=0` 且 `Uq_set_1` 超过 16 ms 达限值，属于被解释的状态/触发条件，不是独立物理根因；“电机未连接或电机接触器断开”是一个合并的局部 OR 候选，未拆成新 ID；无直流母线电压和 Motor Module 缺陷是手册列出的可能条件，不是设备实例测量。条件内部 AND 与候选内部 OR 不能扁平化为事件顶层门；原因集合、嵌套结构和事件级门均未闭合，不建树。
- **F07412 / 12 条候选**：`Possible causes` 的 9 项逐条覆盖；其中电机模型参数组（p0356/p0350/p0352 的 and/or 组合）及“控制环不稳定”两项，独立复核意见认为应视作摘要/非原子条件，主审保留 `causal` 语义但均标为非基本叶，并将分歧显式保存在独立意见中。3 条 r0949 故障值说明来自诊断映射而非 Possible causes，其中 VECTOR `r0949=1` 项本轮按 `associated_only` 处理，且无设备实例读数。Cause 开头描述作为状态/结果摘要记录，不重复增造原因叶；物理根因范围未证明穷尽，事件门 `unknown`，不建树。
- **F07575 / 5 条候选**：Cause 首句“编码器报告未就绪”是故障状态摘要；后续 4 条手册条件逐项有证据，包括初始化失败、parking encoder 功能激活、编码器接口停用及 Sensor Module 缺陷。parking encoder 只是在触发条件抽象下的潜在叶，不代表现场状态读数。来源只列条件，未明确这些条件与事件之间的完整布尔关系，物理根因也未闭合，不建树。
- 三条事件均为 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；Preview `tree_count=0`。本轮维持“原因集合或 AND/OR 未知则不建树”的门禁。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch76.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch76.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch76_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch76_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch76_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch76_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch76_2026-09-25.md)。本批 9 项合同测试通过；Batch02–Batch76 批次合同回归共 245 项测试通过；FTA Preview owner 40 项、context revalidation 5 项测试通过；Python 编译检查通过。`git diff --check` 通过，只有工作区既有文件的 LF→CRLF 提示。

**截至第七十六批，按 Batch02–Batch76 的 75 份审核 JSON 复算：**209/281 个唯一故障码已有事件级 AI 审核快照，72 个未覆盖；774/1,041 个候选 ID 已复核，267 个未覆盖。累计范围内故障码与候选 ID 均无重复（独立初始 Batch01 快照不计入本累计）。批次 Preview 文件共 74 份、累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入正式 Gold；`fta_ready=false`、`production_ready=false`。

## 50. 第七十七批与当前累计进度（2026-09-25）

第七十七批审核 F07930、F07935、F13100，共 20 条 manifest 候选项。Averroes、Turing、Hume 三位用户授权 AI 专家角色分别独立复核一个事件；主审逐项比对完整嵌入原文、候选语义、manifest/context 状态和字符跨度。20 条候选共复核 22 个来源跨度，全部在完整 `input_text` 中唯一匹配。F07935 的 V11 原 manifest 无证据，本批在 scoped overlay 中恢复完整的 `r0949=0` 分支；F07930 重复原因保留两个故障值上下文，F13100 的 r0949 行补入行首故障值编号。父 Gold、manifest、context 和数据库未修改。

- **F07930 / 10 条候选**：5 条保留为条件性因果、4 条为故障值诊断/状态关联、1 条（r0949=50 的混合诊断文本）为摘要级描述。制动控制回路缺陷的独立审核意见认为可作局部潜在叶；主审依据 F01630 同类事件的已用口径保留为因果边但不标基本叶，分歧明示记录。`brake not closed or interrupted cable` 与 `short-circuit in brake winding` 各关联两个故障值组，证据分别保留，不把局部 OR 推成事件门。Gold `weak_record.causes_text` 只含 Cause 摘要及两个直接条目，不覆盖全部 10 条来源范围；原因全集与事件门未闭合，不建树。
- **F07935 / 3 条候选**：Cause 首句改判为故障状态摘要；`r0949=0`、`r0949=1` 是不同的条件配置映射，不是本次设备实测值。V11 将 `p1215=0` 与仅限首次调试的 `p1215=1` 陈述合并，故保留因果条件但不认作原子叶；V12 只在局部配置触发条件抽象下作为潜在叶。Gold 引文有截断，V11 manifest 缺引用而 V12 manifest/context 证据状态互相不一致；来源人工审核状态字段也相互冲突。门 `unknown`、不建树。
- **F13100 / 7 条候选**：6 条为条件性原因/细分情景，1 条“检查存储卡时发生错误”作为摘要级描述。r0949=0/2/3/12/13 映射不是现场读数；值 12/13 的 OEM 输入条件是 invalid-card / another-Control-Unit 情景的细分，不额外算作独立根因。独立复核指出审核队列仍为 pending、没有 `gold_records`，而 AI 辅助最终数据文件有 7 条候选；这是数据状态/版本范围差异，不视为真人批准。候选全集、物理根因层级和事件 AND/OR 未闭合，不建树。
- 三条事件均 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`；Preview 树数为 0。AI 角色审核结果用于本轮审核与开发验证，不是真人 Siemens 专家签署，也不进入正式 Gold。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch77.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch77.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch77_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch77_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch77_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch77_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch77_2026-09-25.md)。本批 11 项合同测试通过；Batch02–Batch77 批次合同回归共 256 项测试通过；FTA Preview owner 40 项、context revalidation 5 项测试通过；编译检查通过。`git diff --check` 通过，仅显示工作区既有文件的 LF→CRLF 提示。

**截至第七十七批，按 Batch02–Batch77 的 76 份审核 JSON 复算：**212/281 个唯一故障码已有事件级 AI 审核快照，69 个未覆盖；794/1,041 个候选 ID 已复核，247 个未覆盖。累计范围内故障码和候选 ID 均无重复（独立初始 Batch01 快照不计入本累计）。批次 Preview 文件共 75 份、累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入正式 Gold；`fta_ready=false`、`production_ready=false`。

## 51. 第七十八批与当前累计进度（2026-09-25）

第七十八批审核 F30017、F30021、F30036，共 22 条 manifest 候选项。Boyle、Fermat、Cicero 三位用户授权 AI 专家角色分别独立复核一个事件；主审再对照完整 `input_text`、Gold/manifest/context 以及证据跨度。22 条候选共重验 26 个来源跨度，所有引用均能按 Unicode 码点 0-based 半开区间 `[start,end)` 从输入原文精确回切；重复文本保留其设备类别、Cause/Fault value 或 bit 编号上下文。只生成本批 overlay、审核记录和 preview-only 工件，Gold、manifest、基础 context 和数据库均未修改。

- **F30017 / 7 条候选**：两个设备类别列表的 9 个 Cause 位置对应 7 个不同原因描述，均已覆盖；重复的闭环控制参数错误、功率单元缺陷分别保留两类设备上下文。Cause 内部的 reactor “missing or wrong type”以及 motor/cable “or”是局部复合条件，不推断为顶事件门。r0949 phase bits 和 Note 是诊断信息，不是设备实测；A30031/A30032/A30033 仅为交叉引用。原文 Cause 清单范围覆盖为完整，但不代表现实根因已穷尽。
- **F30021 / 5 条候选**：Possible causes 的四项均已覆盖：电缆接地、 motor 接地、制动闭合时监控响应机制、制动电阻短路。短路同时出现在 r0949=0 映射中，两个上下文均保留；V13 保留为机制摘要，不提升为独立物理根因，V15 是 r0949 监控响应的诊断状态。发现父 manifest 的 V15 候选文本为空且证据错指 V13，context/source-node 则指向 fault-value 监控响应行；错配作为数据质量问题记录，未回写父文件。四条 Possible causes 的来源清单覆盖完成，不表示现实根因穷尽。
- **F30036 / 10 条候选**：Cause 中温度超限摘要与冷却不足、风扇故障、过载、环境温度过高均已审核；摘要不重复作为独立原因。r0949 Bit 0–5 的六条内容属于区域/条件诊断映射，不是现场 bit 实测；Bit 2 与 Bit 3 的相同处理器过温短语分别引用并保留位号。Cause 和故障值段落均逐项盘点，但不宣称现实物理根因全集穷尽。
- 三个事件均没有直接证据确定事件级 AND/OR，故均为 `logic_gate=unknown`、`build_allowed=false`，本批生成 0 棵树；来源清单覆盖完成与“可建树”严格区分。AI 角色审核不是 Siemens 真人专家签署，也不进入正式 Gold。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch78.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch78.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch78_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch78_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch78_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch78_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch78_2026-09-25.md)。本批 9 项合同测试通过；Batch02–Batch78 批次合同回归共 265 项测试通过；FTA Preview owner 40 项、context revalidation 5 项测试通过；编译检查与 `git diff --check` 通过。

**截至第七十八批，按 Batch02–Batch78 的 77 份审核 JSON 复算：**215/281 个唯一故障码已有事件级 AI 审核快照，66 个未覆盖；816/1,041 个候选 ID 已复核，225 个未覆盖。累计范围内故障码与候选 ID 均无重复（Batch01 初始快照不计入本累计）。批次 Preview 文件共 76 份、累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入正式 Gold；`fta_ready=false`、`production_ready=false`。

## 52. 第七十九批与当前累计进度（2026-09-25）

第七十九批审核 F30600、F30630、F30650，共 22 条 manifest 候选。Lagrange、Poincare、Heisenberg 三个用户授权 AI 专家角色分别独立复核一个故障；主审随后对照完整嵌入 `input_text`、候选清单、来源章节、context 和精确字符跨度，并将独立意见与主审裁定分栏保存。22 条候选证据均以 Unicode 码点 0-based 半开区间 `[start,end)` 唯一回切成功。只写本批 overlay、审核快照、Preview 和测试；Gold、manifest、父 context、数据库均未修改。

- **F30600 / 6 条候选**：V13 定为 `causal_summary`（Safety Integrated 检出通道故障并触发 STO 的机制摘要，不是基本故障叶）；V14 测试停止失败、V15 另一通道停止请求为条件性 `causal`；三个 STO 状态/诊断值候选为 `associated_only`。另将 Cause 栏中的 F30611 后续响应条目和 r0949=9999 映射单列为跨故障响应/引用，没有方向反转成“F30611 由 F30600 导致”。独立审核发现所有候选的元数据都把来源字段写作 cause，但 V15 以后实际出现在 Fault value 段；以原文章节和语义为准，并保留元数据冲突。Cause 栏清单项均已盘点，但不代表现实原因穷尽。
- **F30630 / 7 条候选**：Cause 栏两项——OCC 屏蔽连接错误、制动控制回路缺陷——明确为条件性因果。100–102、300–302、200–202 三组 Fault value 含状态和其下级故障条件，主审将其保留为条件性因果组，但不作为原子 FTA 叶；400–402 与 60/70 仅为关联诊断状态。独立复核对前三组保留 `cannot_determine`，理由是其位于 Fault value 而非 Cause 栏；主审的层级解释与该意见并列记录，不把它说成共识。局部 “or” 不推出事件级 OR。Gold 的 `weak_record.causes_text` 与 `gold_records.causes` 来源范围不一致，作为数据质量问题登记，未改 Gold。
- **F30650 / 9 条候选**：V13 是目标事件的重述摘要，不作为独立上游原因；130、首次调试、启动校验和差异、其下配置/数据项、commissioning-mode 差异和参数变更情形均保留为有条件的因果关系，基本叶资格单独判断。V19-088/089 的句子本身同时包含原因和“需要验收测试”目标，主审保留因果方向但不把整句直接当叶。r0949=9999 的另一安全故障后续响应未进入九条候选，另列为未映射引用。独立意见与主审在 V13、V19-088/089 的分类上有分歧；Gold 的 expert_review 建议与 causes 列表仍有内部不一致，均只记录、不回写。
- **FTA 门禁**：三事件的事件级门均为 `unknown`，没有直接来源证据证明完整 AND/OR 方程，因此 `build_allowed=false`，本批树数为 0。所谓“原文清单覆盖”只表示可见 Cause/Fault value 来源项目已被盘点，不表示真实根因全集完整，也不表示可进入正式故障树。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch79.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch79.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch79_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch79_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch79_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch79_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch79_2026-09-25.md)。本批 8 项合同测试通过；Batch02–Batch79 全部批次合同回归 273 项通过；FTA Preview/context/contract 相关测试 47 项通过；本批脚本与测试编译检查通过。

**截至第七十九批，按 Batch02–Batch79 的 78 份审核 JSON 复算：**218/281 个唯一故障码已有事件级 AI 审核快照，63 个未覆盖；838/1,041 个候选 ID 已复核，203 个未覆盖。累计范围内故障码与候选 ID 均无重复（独立初始 Batch01 快照不计入本累计）。批次 Preview 文件共 77 份、累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人专家签署、不写入正式 Gold；`fta_ready=false`、`production_ready=false`。

## 53. 第八十批与当前累计进度（2026-09-25）

第八十批审核 F30651、F30681、F30683，共 11 条 manifest 候选。Lavoisier、Curie、Noether 三个用户授权 AI 角色分别独立复核一个事件；主审再对照完整 Gold input_text、manifest、context 和原文跨度。11 条候选引文均按 Unicode 码点 0-based 半开区间 [start,end) 在完整 input_text 中唯一回切。仅新增本批来源定位 overlay、AI 审核快照、Preview 和测试；Gold、manifest、基础 context、数据库均未修改。

- **F30651 / 1 条候选**：Cause 句说明同步例程未成功，与目标故障“监控通道 1 同步失败”描述的是同一事件，归为 causal_summary，不作为独立 FTA 基本叶。both monitoring channels 只是同步参与通道，不构成事件级 AND 证据。STO 无法确认是结果信息，POWER ON/软件升级是处理措施；均不当作上游原因。
- **F30681 / 9 条候选**：通用句 “The parameter cannot be parameterized with this value.” 归为 causal_summary；其余 8 条是 r0949 故障值下列出的参数不兼容/配置不匹配场景，保留为条件性 causal 候选。其中 yyyy=1 明确包含两个设置同时启用的局部复合条件，因此不当作原子叶；其余潜在叶也仅表示手册情景粒度，不表示某台设备实测。不同故障值的枚举不等于顶层 OR。原文 Remedy 引用 xxxx=9317，但可见 Fault value 列表没有该项；作为未映射交叉引用记录，不推测缺失原因。未提供现场 r0949 或参数值。
- **F30683 / 1 条候选**：Cause 句与“SOS/SLS enable missing”故障状态高度重合，归为 causal_summary，不作为独立基本叶。原文明确说明该消息不会导致安全停车，因此不能把报警本身说成安全停车已发生。although 不构成事件级门型依据。
- 三个事件均 logic_gate=unknown、build_allowed=false，本批生成 0 棵树。cause_set_complete 的可见来源清单盘点不表示现实物理根因穷尽；fta_ready=false、production_ready=false。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch80.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch80.py)、[AI 来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch80_2026-09-25.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch80_2026-09-25.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch80_2026-09-25.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch80_2026-09-25.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch80_2026-09-25.md)。Batch80 合同测试 8 项通过；Batch02–Batch80 全部审核批次回归 281 项通过；FTA Preview/context/contract 回归 11 项通过；Python 编译检查通过。git diff --check 通过，仅有工作区既有文件的 LF→CRLF 提示。

**截至第八十批，按 Batch02–Batch80 的 79 份审核 JSON 复算：**221/281 个唯一故障码已有事件级 AI 审核快照，60 个未覆盖；849/1,041 个候选 ID 已复核，192 个未覆盖。累计范围内故障码与候选 ID 均无重复（Batch01 初始快照不计入本累计）。批次 Preview 文件共 78 份，累计树数仍为 10 棵（另有独立初始 Preview v1 的 1 棵），本批新增 0 棵。AI 授权角色审核不是真人 Siemens 专家签署、不写入正式 Gold；fta_ready=false、production_ready=false。

## 54. 第九十八批与当前累计进度（2026-09-26）

第九十八批完整审核 F01039、F01640、F01641 的 11 条候选。Aristotle、Carver、Russell 三个用户授权 AI 专家角色分别只读复核一个完整事件；主审逐项核对完整 `input_text`、候选全集、Gold、manifest/context、手册语义和来源跨度。主审与独立复核使用同一原文锚点，11 条候选各有唯一来源跨度，独立意见共 11 条引用跨度也逐一验证唯一。所有审核者意见均明确标为 AI 角色意见，不是真人 Siemens 专家签署。

- **F01039 / 3 条候选**：只读属性导致备份文件不能覆盖、非易失存储空间不足、非易失存储器损坏且不可写，均为手册列出的条件性因果模式，可作为潜在叶候选；Cause 前置句只是写入失败摘要，不是第四条独立原因。三项列表不能证明某个现场实例的原因全集，也不足以推导 OR。r0949 是十六进制码义、p0977/p0971 是操作参数说明，均非现场值。V7 manifest 缺 `candidate_text/source_node_id/target_description`，虽然完整原文存在唯一短句，仍作为身份字段缺失待修订，不自动补正式记录。
- **F01640 / 4 条候选**：V6 描述更换被 Safety Integrated 识别及驱动运行受影响，是状态/触发摘要而不是基本物理失效叶；V7–V9 是 r0949 bit 0/3/5 对驱动器、Sensor Module、sensor 更换识别的条件性码义。没有现场位读数，不判断当前实例更换了哪个部件。独立 AI 将 V7–V9 视为条件性 causal，主审归为 associated-only 诊断映射；3 条分类、关系类型与方向差异均保留。Gold v7 中 V6 决议为 `revise`，不是已批准关系；manifest 状态不一致及身份字段缺失均记录但不回写。
- **F01641 / 4 条候选**：V6 为组件更换识别通知；手册明确无额外故障响应且运行不受限，不能与 F01640 的运行影响混为一谈。V7–V9 是 r0949 位码对更换对象的诊断释义，不是现场位读数；安全功能启用时的 partial acceptance test 是后续安全验证义务，不是故障原因。独立 AI 将 V6 视作“更换导致通知”的 causal，主审将原复合候选视作 causal summary；该分类/关系差异保留。Gold v7 对 V6 是 `revise`，而 manifest 标记完成，状态冲突不覆盖。
- **FTA 门禁**：三个事件的现场实例信息或完整原因集合不足，事件级逻辑门均为 `unknown`，`cause_set_complete=false`、`build_allowed=false`；本批生成 0 棵树。Preview 继续保持 `fta_ready=false`、`production_ready=false`。本批只新增来源定位 overlay、AI 审核快照、Preview 和测试，不改 Gold、manifest、既有 context 或数据库。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch98.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch98.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch98_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch98_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch98_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch98_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch98_2026-09-26.md)。Batch98 合同测试 7 项通过；Batch02–Batch98 回归共 454 项通过；FTA Preview owner、AI Preview 集成、Preview contract、context revalidation 与后端 graph contract 回归共 51 项通过；编译检查与 `git diff --check` 通过（Git 仅报告若干既有工作文件的 LF→CRLF 提示）。

**截至第九十八批，按 Batch02–Batch98 的 97 份审核 JSON 复算：**272/281 个唯一故障码已有事件级 AI 审核快照，9 个未覆盖；1,027/1,041 个候选 ID 已复核，14 个未覆盖。该累计范围内故障码和候选 ID 均无重复（不计 Batch01 初始快照；此前修订批次中的 A01006/CR-CAND-001 不作为重复计数）。批次 Preview 文件共 96 份，历史累计树数仍为 10 棵，本批新增 0 棵。所有 AI 授权角色审核不是真人 Siemens 专家签署，也未写入正式 Gold 或数据库；`fta_ready=false`、`production_ready=false`。

## 55. 第九十九批与全候选审核覆盖收口（2026-09-26）

第九十九批审核剩余 9 个故障事件、14 条候选：F01651、F01657、F01663、F01675、F01683、F01685、F01708、F07097、F07860。Hilbert、Ptolemy、Meitner 三个用户授权 AI 专家角色分别独立复核三组完整事件；主审对照完整来源、候选清单、Gold、manifest/context、原文和偏移。14 条主审证据跨度与 15 条独立意见证据跨度均按 0 起始 Unicode 半开位置验证为原文精确且唯一。八处候选分类/方向差异并列保留，不将 AI 角色意见伪装成人类共识。

- **F01651 / 1 条**：同步例程失败与顶事件重合，没有解释同步为何失败；主审视作关联状态摘要，独立 AI 视作 causal summary；没有上游原因。STO 是故障结果/响应。
- **F01657 / 2 条**：无效 p9611 报文号状态与故障标题重合；另一条是 PROFIsafe 启用时编号必须大于 0 的有效性规则。主审与独立 AI 对两条分别是“状态摘要 vs 条件因果”“条件因果 vs 规则/关联”的意见不同；记录规则不等于现场违反规则，缺少 p9601.3/p9611 实读值。
- **F01663 / 1 条**：源通道未选择安全功能时启动间复制被安全拒绝，有因果链证据，但候选是复合机制摘要，不直接作为原子叶。参数不一致及 F30625 是下游结果/消息。
- **F01675 / 3 条**：一条配置错误摘要，另两条分别是 fault value 1 的 Tdp/p9500 不符和 fault value 2 的未设置等时运行。两条是条件模式；无现场 r0949 值，码值 1/2 不推事件级 OR。V9 原审核无 evidence，完整带码值原文唯一定位，但仍保留人工候选身份对齐状态。
- **F01683 / 1 条、F01685 / 1 条**：分别为 SOS/SLS 未启用的配置条件、SLS 限值超过编码器 500 kHz 限频对应速度；都是有原文支持的条件性原因叶候选，但没有现场参数读数。两记录均明确不导致安全停止响应。
- **F01708 / 2 条**：SS2 停车及延时后 SOS 激活描述事件后的安全响应。独立 AI 指出可能方向是“故障事件 → 响应状态”，而不是“候选原因 → F01708”；主审与独立意见保留分歧。A01714/A01716 是后续响应消息，不是上游原因。
- **F07097 / 2 条**：test signal/自动调谐未执行或取消的候选被主审看作过程状态，独立 AI 看作非原子触发摘要；fault cause=4 映射为到 EPOS 软件限位开关距离不足，可作为条件性叶候选，但不是设备实测值。局部 `or` 不证明事件门。
- **F07860 / 1 条**：原句“External fault condition is present”重述目标状态，没有指出外部信号来源；不补造上游原因。原审核无 evidence，人工核查到唯一原文，但保留待绑定标记。
- 14 条均完成候选审阅；但所有 9 个事件的 `cause_set_complete=false`、`logic_gate=unknown`、`build_allowed=false`，本批树数 0。正式 Gold v7 没有这些新事件的专家因果关系或 AND/OR 门结论。Gold/manifest/context/数据库均未回写；`fta_ready=false`、`production_ready=false`。

本批产物：[审核生成脚本](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_batch99.py)、[批次合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_batch99.py)、[来源定位 overlay](../evaluation/quality_eval/runs/siemens_s210_causal_context_source_recheck_batch99_2026-09-26.json)、[审核 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch99_2026-09-26.json)、[审核说明](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_batch99_2026-09-26.md)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch99_2026-09-26.json)、[Preview Markdown](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_batch99_2026-09-26.md)。Batch99 合同测试 8 项通过；Batch02–Batch99 批次合同回归 **462 项全通过**；FTA Preview owner、AI Preview 集成、Preview contract、context revalidation、后端 graph contract 回归 **51 项全通过**；本批 Python 编译检查与 `git diff --check` 通过。

**截至第九十九批，全量覆盖对账通过：**Batch02–Batch99 共 98 份审核 JSON 覆盖 281/281 个唯一故障码、1,041/1,041 条唯一候选 ID；重复故障码和候选 ID 均为 0，剩余未审核数均为 0（排除 Batch01 初始单条快照）。Batch Preview 共 97 份，累计仍为 10 棵历史 Preview 树，本批新增 0 棵；另有独立初始 Preview v1 的 1 棵。**这是 AI 授权角色的全范围复核完成，不等同于 1,041 条真人专家 Gold，也不等同于可自动建树。** 正式 Gold、数据库未改变；`fta_ready=false`、`production_ready=false`。

## 56. Batch02–Batch99 全量审核汇总与 Preview 对账（2026-09-26）

新增汇总生成器，将 Batch02–Batch99 的 98 份 AI 授权角色审核快照合并为一个可机读审阅集，并单独打包通过既有 Preview owner 门禁的树。它只聚合已有决策，不推断 AND/OR、不覆盖主审与独立意见分歧、不更改正式 Gold 或数据库。

- 覆盖与身份对账：281/281 个唯一故障事件、1,041/1,041 个唯一候选 ID；与全量候选 manifest 缺项 0、多项 0、重复 0。98 批声明的原文来源 SHA-256 均对应规范来源语料哈希 `12863288cae14b97d587b3cc4deb3e03aeea3331716d5b4e3f5b2cc7471eff44`。
- 事件门状态：OR 17、`not_applicable` 60、`unknown` 204。原因集合完整标记 121、不完整标记 160；完整标记不单独授权建树。
- Preview 门禁：11 个事件 `build_allowed=true`，与 11 棵既有 Preview owner 输出逐事件一一对应；270 个事件未获准。另有 6 个 OR 事件因其他建树条件未满足而阻止 Preview：A01691、F01001、F01911、F07900、F07901、F30655。未知逻辑门继续不建树。
- 候选证据审计：1,096 个跨度均可从声明的完整原文精确回切；其中 1,086 个短语唯一、10 个为重复短语跨度。59 个候选没有证据；38 个来源布尔标记要求人工复核，40 个候选经原状态及重复短语规则综合后仍需人工定位/绑定。精确回切只证明位置与原文一致，不代表语义支持已经解决；重复短语不自动选定某一处。
- 37 个候选存在明确主审/独立意见差异；分歧与两方原意见原样并存，未以多数票消解。AI 授权角色意见不是真人 Siemens 专家签署。
- 汇总 Preview 只索引和对账既有树结构，不重新生成树语义；`fta_ready=false`、`production_ready=false`、`formal_gold_mutated=false`、`database_written=false`。因此“98 批审核覆盖完成”不代表正式 Gold 完成，也不代表 281 条都可建树。

本次产物：[汇总生成器](../evaluation/quality_eval/public_sources/build_siemens_s210_causal_event_gate_review_consolidated_v1.py)、[汇总合同测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_causal_event_gate_review_consolidated_v1.py)、[全量审核汇总 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.json)、[全量审核摘要](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.md)、[Preview 树汇总 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_consolidated_v1_2026-09-26.json)、[Preview 树汇总摘要](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_consolidated_v1_2026-09-26.md)。本次汇总合同测试共 6 项；测试覆盖来源/manifest 全量对账、审阅分歧保留、门禁与 Preview 一一对应、证据定位状态及禁止写入正式 Gold/数据库。

## 57. 现有 11 棵 Preview 树核验与其余事件处置（2026-09-26）

对已汇总的 11 棵树逐棵复核树根故障码、AND/OR 门、已审核候选身份、候选叶资格、关系方向、原始 Preview 来源哈希和证据跨度；同时重新运行原始 Preview owner 的 `validate_fta_preview` 合同校验。结果为 11/11 结构/来源核验通过、198 项检查零失败、9 个原始 Preview 来源文件合同错误 0；56/56 条树内引用都能按起止位置精确回切完整原文，重复引文位置 0。**这证明的是现有 Preview 结构与来源合同一致，不证明现实工程因果已完整或树已生产验收。**

- 11 棵树均为 OR；每棵的 Preview 门与事件审核快照一致，子节点均能映射回该事件已审核且标记为可作 Preview 叶的候选 ID。没有发现门型错配、候选身份错配、错引原文或重复引文自动选位。
- **粒度注意：F30004 / CR-CAND-V11-280** 的来源 Cause 列表项是 `insufficient cooling, fan failure`，Preview 保留为一个复合文字叶节点。引文和候选身份无误，但仅凭当前逗号表述不能确定这是一个复合事件还是两个独立基本事件；不拆造候选、不改正式审核，展示时不得把它说成已分解到原子物理故障。
- 其余 270 条按现有审核门型拆为：204 条 `unknown`（继续不建树）、60 条 `not_applicable`（保留不适用，不作为待补树数量）、6 条门型虽为 OR 但其他门禁未通过。unknown 中有 64 条原因集合完整标记、140 条不完整标记；完整标记不替代明确逻辑门与可审计叶节点。204/60 条均在审计 JSON 的 `other_excluded_event_dispositions` 中逐故障码列出门型、完整性标记、阻塞码和处置边界。
- 6 条 OR 阻塞分别为：**A01691** 的非等时模式候选仍是 revise/规范要求而非已确认违规节点；**F01001** 只有宽泛可能原因组且未证明穷尽；**F01911** 两个 OR 分支尚无独立审核候选身份；**F07900** 是 OR-of-AND，当前 S210 证据型 Preview 投影不能从扁平候选记录无损输出嵌套分支；**F07901** 正/负超限共用一个候选，缺分支节点身份；**F30655** 两个替代通信条件共用一个候选，且底层原因集合未闭合。上述均保留 `build_allowed=false`，不由汇总器拆分或补造节点。
- 本轮仅新增只读审计报告和测试；未改正式 Gold、manifest、context、数据库或 11 棵源 Preview。仍保持 `fta_ready=false`、`production_ready=false`，不宣称真人 Siemens 专家签署。

本轮产物：[逐树审计生成器](../evaluation/quality_eval/public_sources/audit_siemens_s210_causal_event_gate_preview_consolidated_v1.py)、[逐树审计测试](../evaluation/quality_eval/public_sources/test_audit_siemens_s210_causal_event_gate_preview_consolidated_v1.py)、[逐树审计 JSON](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_audit_v1_2026-09-26.json)、[逐树审计报告](../evaluation/quality_eval/runs/siemens_s210_causal_event_gate_preview_audit_v1_2026-09-26.md)。

## 59. 递归证据型 FTA Preview v2 试点（2026-09-26）

针对旧 Preview 只能表达单层 gate 的合同限制，新增向后兼容的 v2 递归树验证。v1 扁平 Preview 仍按原合同验证；v2 对每一层 gate、node、relation 和 citation 递归检查，要求门证据和边证据均存在，位置为有效字符范围，节点/关系/引文 ID 在树内唯一，并对嵌套深度、节点数、引文数设上限。S210 专用生成器进一步按固定来源语料逐字核对每个 `[start:end]`，并拒绝来源重复或跨故障引用。

- **F01911**：将原文明示的两个同步失败触发条件以 OR 表达；来源候选仍是一个复合项，因此分支节点身份明确标为 `preview_local_derived_not_gold`，不是正式 Gold 节点。
- **F07901**：将“正向或负向超过最大允许速度”展示为两个 Preview-local 触发条件和 OR。两个分支引用同一条原文，因为手册在同一句中给出 either/or，没有分别的独立引文。
- **F07900**：依照“此信号也可由……”与两句内部 `and` 表达为 `OR(AND(path 1), AND(path 2))`。第一路径保留“超过 0.2 秒”的原文，显式注明时长修饰范围不作额外解释；该树只描述手册触发条件，不声称是设备实例的物理根因树。
- **F30655**：继续不建树。通信错误与通信失败可能语义重叠，候选集合未闭合；排除说明引用了原文 `[329:406]`，没有拆成两个分支。

新产物是单独的目标 Preview，不合并、覆盖或重生成原有 11 棵树。递归 Preview 共 3 棵，F30655 排除 1 条；17 个树内引文跨度和 1 个排除引文跨度均与唯一来源记录精确匹配。审阅身份明确为用户授权 AI 专家角色、非真人 Siemens 专家签署；所有节点身份标为 Preview-local 派生而非 Gold。正式 Gold 和数据库均未修改，`fta_ready=false`、`production_ready=false`。

本轮产物：[递归合同实现](../backend-python/contracts/fta_graph_contract.py)、[Preview owner service](../backend-python/fta/ai_authorized_fta_preview_service.py)、[生成器](../evaluation/quality_eval/public_sources/build_siemens_s210_recursive_fta_preview_v2.py)、[生成器测试](../evaluation/quality_eval/public_sources/test_build_siemens_s210_recursive_fta_preview_v2.py)、[AI 审核 overlay](../evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_review_overlay_v1_2026-09-26.json)、[Preview JSON](../evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_v2_2026-09-26.json)、[Preview 阅读版](../evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_v2_2026-09-26.md)。

验证：`test_fta_graph_contract.py` 8 项、AI Preview owner 3 项、递归 S210 Preview 4 项、原 S210 event Preview 回归 40 项、既有 Preview 审计回归 4 项，共 **59 项通过**；递归生成器输出 3 棵树/1 条排除/18 个精确来源跨度；`scripts/verify_repo_layout.py` 通过。目标文件 `git diff --check` 无空白错误（Git 仅提示两份既有风格文件下次写入时 LF 将转为 CRLF）。本轮没有 stage、commit 或 push。

## 58. 显式 OR 阻塞复核与嵌套门合同调查（2026-09-26）

对 F01911、F07901、F30655 做主审与独立 AI 授权角色复核，并检查 F07900 的嵌套门 Preview 合同。F01911 的两个时钟同步条件、F07901 的正/负超限均可从原文中区分，建议进入分支级审核表示；F30655 的“通信错误/通信失败”可能重叠，保留一个复合候选，不拆叶。三个事件当前都保持 `build_allowed=false`，不新增正式候选身份。

F07900 的 Cause 文本支持两条复合触发路径组成 OR-of-AND；普通 `fta_tree_contract.py` 有递归节点校验，但证据图合同与 S210 Preview 投影仍为扁平结构，尚不能逐层验证嵌套门和证据。因此本轮只记录合同缺口，不改 schema、生成器或 Preview。四项都不是现场实例根因证明；Gold、数据库不变，`fta_ready=false`、`production_ready=false`。

本轮产物：[显式 OR 阻塞复核 JSON](../evaluation/quality_eval/runs/siemens_s210_explicit_or_blocker_recheck_v1_2026-09-26.json)、[显式 OR 阻塞复核说明](../evaluation/quality_eval/runs/siemens_s210_explicit_or_blocker_recheck_v1_2026-09-26.md)。
