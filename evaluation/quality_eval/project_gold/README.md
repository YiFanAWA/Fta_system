# 项目手册证据集

这里保存从本项目自己的中文驱动系统手册样例构建的第一批证据评测集。它用于验证：

- 故障码、故障现象、组件和参数是否能回指项目原文；
- 故障处理段落中的候选场景是否能保留原文证据；
- 原文缺失字段是否保持为空或未知；
- 评测样本是否能追溯到源文件、字符偏移和行号。

## 当前边界

第一轮试运行先选择了 8 个故障码；当前生成器已扩展为自动收集手册中明确写出
`故障现象为`字段的故障码，目前生成 27 条样本。输入由故障定义段和同故障码的处理段组成，
生成器会为每条样本保存源文件哈希、源字符范围、行号和输入文本内的证据偏移。

这不是专家审核后的工程金标：

- 原手册注明部分内容可能由 AI 生成；
- `gate_type`、顶事件关系和 FTA 因果逻辑保持未知；
- `causes` 中的内容是“故障值场景候选”，不是专家确认的根因；
- 组件只有在原文明确写成非“无”的情况下才进入 `component`；
- 不得用该集合自动批准生产审核结果。

## 复现

在仓库根目录运行：

```powershell
python evaluation/quality_eval/project_gold/build_project_evidence_dataset.py
```

也可以显式指定输入和输出：

```powershell
python evaluation/quality_eval/project_gold/build_project_evidence_dataset.py `
  --input backend-python/examples/manual_handbook_sample.txt `
  --output evaluation/quality_eval/datasets/fta_project_handbook_evidence.json
```

当前生成结果应包含 27 条 `test` 样本。若源手册发生变化，应重新生成数据集，并检查
`source.sha256`、样本数量和证据偏移是否按预期变化。

面向人工逐条检查的清单见 `evaluation/quality_eval/runs/fta_project_handbook_review_checklist.html`；
它提供搜索、状态筛选、原文展开、证据展开、本地保存和审核结果导出。纯文本版本仍保留在
`evaluation/quality_eval/runs/fta_project_handbook_review_checklist.md`，完整原文和字符证据以生成后的 JSON 数据集为准。

当前在线模型输出的独立审核清单见
`evaluation/quality_eval/runs/fta_project_handbook_online_review_checklist.html`，对应的可追溯审核包见
`evaluation/quality_eval/runs/fta_project_handbook_online_review_bundle.json`。它把基准统计报告和
`backend-python/outputs/*_extracted_faults.json` 中的故障记录、证据跨度配对起来；配对规则是按故障码
选择最新输出，并保留候选文件数。该清单只用于人工审核，不会修改生产接口、数据库或现有前端页面。

当前审核副本另有一份保守的语义预审结果：
`evaluation/quality_eval/runs/fta_project_handbook_online_review_decisions_provisional.json`。
其中“审核通过（证据级）”只表示原文和字段语义足够一致，不等同于专家金标或后台最终 `approved`；
“语义需修改”保留给主组件/关联组件边界、原因完整性或原因归并仍有问题的记录。

组件合同修复后的第二版基线报告为
`evaluation/quality_eval/runs/fta_project_handbook_online_baseline_component_contract_v2.json`，
对应审核清单为 `evaluation/quality_eval/runs/fta_project_handbook_online_review_checklist_v2.html`。
第二版将原文明确“组件为无”的 15 条记录保留为空主组件，并将关联对象放入
`related_components`；当前 27 条中 21 条达到“审核通过（证据级）”，6 条仍需处理原因字段。

第三版原因合同复测报告为
`evaluation/quality_eval/runs/fta_project_handbook_online_baseline_cause_contract_v3.json`，对应清单为
`evaluation/quality_eval/runs/fta_project_handbook_online_review_checklist_v3.html`。原因规则修复后，
`F01023、F01600、F01630、F01632、F01650` 已达到证据级通过；`A01013` 仍保留为语义需修改，
因为模型漏掉了原文中的“因散热不良”，不能仅凭证据存在就批准。

第四版显式因果复测报告为
`evaluation/quality_eval/runs/fta_project_handbook_online_baseline_explicit_cause_v4.json`，对应审核包和清单为
`evaluation/quality_eval/runs/fta_project_handbook_online_review_bundle_explicit_cause_v4.json` 与
`evaluation/quality_eval/runs/fta_project_handbook_online_review_checklist_explicit_cause_v4.html`。
本版在抽取适配器增加了保守的显式因果补回：只有原文出现“因/由于/因为……导致/造成/引起”时，
才将中间的明确原因补入 `causes` 并绑定原文证据；同时按故障码隔离相邻记录，避免串入下一条故障。
27 条真实 API 样本全部结构合法并产出故障树，217/217 条证据跨度可回指原文，`A01013` 的“散热不良”
已可被审核为“审核通过（证据级）”。这仍然不是专家金标，只是证据级预审结论。

给领域专家使用的空白文本清单为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v1.md`，对应数据包为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v1.json`。该版本不预填任何
助手预审状态，专家应独立依据原文和证据填写结论与修改意见。

根据专家对 v1 清单的审核意见，已完成第二版抽取合同修正并用 DeepSeek API 重跑 27 条样本：
报告为 `evaluation/quality_eval/runs/fta_project_handbook_online_baseline_expert_feedback_v5.json`，
新版专家文本清单为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v2.md`，
数据包为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v2.json`。
本版新增主组件/关联组件/组件声明三类证据字段；主组件不再自动复制到关联组件；“组件为无”会留下
组件声明证据；“驱动对象为无（关联……）”不会被当作组件关联；参数值前缀会提炼为自然语言场景。
专家仍需独立判断这些候选原因是否满足工程语义，自动结构合法不等于金标正确。

专家提供审核规则和分类索引后，已将 5 条核心规则、4 种审核结论、27 条记录的组件/故障类别分组、
关键参数分布以及“修复后重点复核”事项加入文本清单 v3：
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v3.md`。

根据专家提交的 v3_2 审核报告，已继续修正并用全新后端进程重新运行 27 条在线样本。最终报告为
`evaluation/quality_eval/runs/fta_project_handbook_online_baseline_evidence_binding_v8.json`，
证据包为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v5.json`，
专家文本清单为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v6.md`，
浏览器清单为 `evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v5.html`。

本轮具体修复如下：

- `PH-A01006`：将“驱动对象为无”与“组件为无”分开；主组件保持为空，关联组件恢复为
  `DRIVE-CLiQ组件、编码器模块`，并保留驱动对象声明证据。
- `PH-A01016`：识别跨换行的“关联控制单元存储器”，恢复关联组件及其证据。
- `PH-F01611`：补回候选原因“STO状态不一致”的故障处理证据。
- `PH-A01631`：对被参数赋值打断的条件原因拆分绑定多个原文证据片段，但保留一个候选原因值。
- `PH-F01641`：补回故障处理段中的 `r9776` 参数证据。

最终包包含 27 条样本，证据审计为 27/27 有效、0 条警告，主组件与关联组件重复数为 0。
在线结构指标为合法性 100%、FTA 产出率 100%、启发式疑似幻觉率 1.06%；这些指标只能说明接口
和证据结构可用，不能代替专家对候选原因、字段归属和故障逻辑的语义判断。参数值说明的进一步
简化，以及候选原因是否是真正的工程原因，仍应由专家在最终清单中确认。

针对后续专家报告，又完成三处收口：Record 10 将“交叉比较数据编号异常”恢复为原文一致的“交叉比较数据编号”；
Record 15 将两条条件原因规范为“不存在电机抱闸且SBC使能”和“电机抱闸控制，B且SBC使能”，并合并
重复的 `SBC使能` 证据；Record 24 的“编码器模块”证据改为优先命中组件声明中的跨换行文本。三条记录
均已通过真实 API 复测。最终审核包为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v8.json`，文本清单为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v9.md`，HTML 清单为
`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v8.html`。该包仍为 27 条样本、
27/27 条证据有效、0 条警告。

## 当前抽取器基线

已使用当前 `extract_fault_result_from_text` 对第一轮 8 条试运行样本做过只读基线运行。修复前报告为
`evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline.json`，8 条样本全部返回
`success`，但预测证据为 0 条。补上适配器的字面证据绑定后，8 条试运行样本的最新报告为
`evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline_after_evidence.json`：
8 条样本全部返回 `success`，预测证据 56/56，且 56/56 通过原文偏移校验。

字段级微平均结果如下：

| 字段 | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| 故障码 | 1.0000 | 0.7500 | 0.8571 |
| 故障现象 | 0.8750 | 0.8750 | 0.8750 |
| 组件（仅统计原文明确组件） | 1.0000 | 1.0000 | 1.0000 |
| 故障值场景候选 | 0.8750 | 0.5833 | 0.7000 |
| 参数 | 1.0000 | 1.0000 | 1.0000 |

组件的 1.0000 只针对 4 条有明确组件金标的样本；原文写“组件为无”的样本单独统计，
不纳入该字段的 Precision/Recall/F1。模型调用具有非确定性，故障值场景候选的结果可能
随重复运行变化；它本身也仍然只是候选标签，不是专家根因结论。

### 扩展到 27 条后的基线

此前报告 `fta_project_handbook_extraction_baseline_27_final.json` 是切段和临时标注修正后的
旧在线预测重评分，仅作为语义规则修改前的对照，不代表专家真值。

### 语义规则修正后的基线

`evaluation/quality_eval/runs/fta_project_handbook_extraction_baseline_semantic_v2.json`
是修改提示词和后端归并规则后重新调用模型的结果。27 条样本全部返回 `success`，且没有
样本再返回多条故障记录；预测证据为 196 条，其中 196/196 能回指输入文本。故障码 F1=1.0000，
故障现象 F1=0.9630，组件 F1=0.9167，故障值场景候选 F1=0.4167，参数 F1=0.9931。
`A01032` 已识别，`r2124` 已识别，`F01651` 已归并为一条记录并保留两个关联组件。
临时标注仍不是专家金标，证据跨度有效只代表引用位置存在，不代表工程语义已经确认。

候选原因的工程语义和组件归属已经完成 v9 项目审核并写入中间集；组件列表继续作为后台字段保留，
不改变现有前端 `component` 展示字段。由于当前字段仍来自最终模型输出的同源审核包，不能据此计算独立
专家 F1；故障树 AND/OR 逻辑也仍未纳入该中间集。

2026-09-19 已使用当前 DeepSeek API 配置重新运行 27 条样本，报告见
`evaluation/quality_eval/runs/fta_project_handbook_online_baseline_after_fallback_merge.json`。
修复兜底归并后 27/27 条返回 `success`，每条保留一条故障记录，输出 196 个证据跨度并全部
通过输入原文偏移校验。结构合法率和 FTA 文件产出率为 100%，但这些指标不等于工程语义正确；
当前报告中的疑似幻觉率是字符串启发式结果，不能替代专家审核。

该集合可以转换为统一的软逻辑训练中间格式，但 27 条样本会强制保持在 `test`，不参与
训练。这样可以检验公开来源训练后的项目域迁移效果，同时避免项目手册原文泄漏到训练集；
转换合同见 `evaluation/quality_eval/soft_logic_training/README.md`。

仓库中若仍保留 `fta_project_handbook_extraction_baseline_27.json`，它只是切段修正前的无效历史
产物，不得作为当前结论；当前语义规则验证报告是 `fta_project_handbook_extraction_baseline_semantic_v2.json`。

## 金标边界与未完成项

本轮已完成项目审核并整理故障记录边界、组件归属、参数语义、候选原因和字段证据，形成下方的
项目审核中间集。AND/OR 逻辑仍需要独立的故障树审核，不能从当前字段审核结果推断；在逻辑审核完成前，
中间集中的 `logic_status` 保持 `unknown`。当前字段保留在 `gold_records`，原始模型输出保留在
`model_prediction`，审核者、审核时间和修正历史保留在 `expert_review`/`review_history` 中。

## 项目审核中间集（v1.1.0-provisional）

在 v9 清单完成项目审核后，已生成项目审核中间集：

`evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v1.json`

该文件包含 27 条故障记录，全部放在 `test` 集，项目审核结论为 27 条“审核通过”。
同时保留模型原始结果、字段级证据、项目审核决定、修正字段以及修正前后的审核历史，
因此不会把修正过程覆盖成一个无法追溯的最终值。没有提供审核者姓名，所以姓名字段保持为空，
不伪造专家身份。该文件不是独立专家金标，也不能用来证明模型零误差。

该金标当前只用于抽取质量评估、错误分析和后续 F1 计算，不直接用于训练：

- `human_expert_reviewed=false`，表示仍待领域专家独立复核；
- `label_status=project_reviewed_provisional`，表示这是项目审核中间集；
- `training_policy.eligible_for_training=false`，避免把项目手册原文泄漏到训练集；
- 27 条样本的 `logic_status` 均为 `unknown`，没有擅自补写故障树 AND/OR 逻辑；
- 若未来补充逻辑门标注，应在独立版本中增加，不覆盖当前字段和证据。

生成命令：

```powershell
.venv\Scripts\python.exe evaluation/quality_eval/project_gold/build_expert_gold_dataset.py `
  --bundle evaluation/quality_eval/runs/fta_project_handbook_expert_review_bundle_v8.json `
  --output evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v1.json `
  --review-date 2026-09-19 --review-version v9
```

## 历史流程：独立专家标注

以下内容记录统一 57 条审核来源导入前的流程，当前不再作为阻塞条件：

`evaluation/quality_eval/runs/fta_project_handbook_expert_review_checklist_v9.md`

当时原计划是在专家填写后，把每条记录的结论、修改后的字段、证据引用和审核者信息导入新的专家标注文件；
当前已经改由统一 57 条审核来源承担这一步，结构化结果见文末“统一 57 条审核结果”章节。

## 正式独立专家金标（v2）

已收到并导入 `FTA_故障记录_2.txt` 的领域专家审核报告，生成正式独立专家金标：

`evaluation/quality_eval/datasets/fta_project_handbook_expert_gold_v2.json`

该版本的 27 条记录均由审核报告判定为“审核通过”，字段值和证据均确认，审核者角色为“领域专家”。
Record 15 的逗号调整仅作为不影响语义的建议，没有被当作字段修改；AND/OR 逻辑仍保持 `unknown`。
该金标仍固定为 `test`，不可混入训练集。

基于已有 27 条语义修正版模型结果回放重评分，结果见：

`evaluation/quality_eval/runs/fta_project_handbook_expert_gold_v2_f1.json`

| 字段 | Precision | Recall | F1 |
|---|---:|---:|---:|
| 故障码 | 1.0000 | 1.0000 | 1.0000 |
| 故障现象 | 0.9259 | 0.9259 | 0.9259 |
| 组件 | 0.9167 | 0.9167 | 0.9167 |
| 候选原因 | 0.8800 | 0.4490 | 0.5946 |
| 参数 | 1.0000 | 1.0000 | 1.0000 |

证据方面，模型预测的 196 条跨度全部能回指原文；专家金标记录了 232 条审核证据跨度。
证据位置有效不等于字段语义正确，当前最需要优化的是候选原因的召回率，而不是继续修改前端或建树流程。

## 外部公开手册扩展语料

为获得不参与当前 27 条样本修正的新数据，已从公开的 SINAMICS S210 手册故障章节抽取
`evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl`，共 281 条消息记录。
其中 169 条为 F 类故障、106 条为 A 类报警、6 条为 N 类内部消息。该集合是未标注公共语料，
不会直接替代专家金标；详细来源、页码、哈希和许可边界见
`evaluation/quality_eval/public_sources/README.md`。

## 统一 57 条审核结果（用户确认采用为专家审核来源）

2026-09-20，用户明确确认采用下载的
`FTA_故障记录专家审核清单_57条_专家逐条已审核完整版.md` 作为本项目的专家审核来源。
该文件覆盖项目手册 27 条和公开 SINAMICS S210 30 条，并已导入为：

- 原始审核文本：`evaluation/quality_eval/datasets/fta_unified_expert_review_57_2026-09-20.md`
- 结构化审核集：`evaluation/quality_eval/datasets/fta_unified_expert_review_57_2026-09-20.json`
- 导入脚本：`evaluation/quality_eval/project_gold/import_unified_expert_review.py`

结构化数据同时保留 `model_prediction`、字段级 `evidence_spans`、完整 `input_text`、
`expert_review`、`review_history` 和修正后的 `gold_records`，不会覆盖原始抽取结果。
当前审核结论为：42 条审核通过、8 条语义需修改、6 条证据不足、1 条无法判断；
故障树 AND/OR 逻辑仍为 `unknown`，且由于存在未决审核结果，严格 F1 暂不标记为 ready。
该集合固定为测试/评估用途，不直接混入训练集或生产数据库。

基于该集合的离线 F1 诊断报告为：

- `evaluation/quality_eval/runs/fta_unified_expert_review_57_f1_diagnostic_2026-09-20.md`
- `evaluation/quality_eval/runs/fta_unified_expert_review_57_f1_diagnostic_2026-09-20.json`

该报告是旧模型输出的历史基线：在排除 1 条“无法判断”和 6 条“证据不足”后，50 条字段语义闭合记录的候选原因 F1 为
`0.9370`；故障码、组件、关联组件、故障现象和参数均为 `1.0000`。

2026-09-20 已按新的候选原因语义约束和 description 边界规则真实重跑 57 条（项目 27/27、公开 30/30），
并将新预测写入独立回放文件，不覆盖上述专家审核集：

- 预测回放：`evaluation/quality_eval/runs/fta_unified_expert_review_57_after_boundary_policy_2026-09-20.json`
- 最新 F1 报告：`evaluation/quality_eval/runs/fta_unified_expert_review_57_f1_after_boundary_policy_2026-09-20.md`
- 最新 F1 数据：`evaluation/quality_eval/runs/fta_unified_expert_review_57_f1_after_boundary_policy_2026-09-20.json`

最新 `fully_supported_50` 口径结果为：故障码 `1.0000`、组件 `0.9836`、关联组件 `1.0000`、
故障现象 `0.9900`、候选原因 `0.9503`、参数 `1.0000`。其中候选原因评分包含已确认的复合原因拆分兼容、
中文换行和少量同义表述归一化。剩余误差已定位到少数样本：F01640 有一条泛化原因冗余，
F30655 的 Cause 段粒度与当前金标不同，F40000 漏掉一条 Cause；这些不应再通过扩大枚举字典解决，
应作为后续错误样本复核或补充训练/评估数据。该 57 条集合仍只用于测试/评估，不直接用于训练。
