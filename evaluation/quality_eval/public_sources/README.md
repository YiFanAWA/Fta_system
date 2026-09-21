# 公开手册故障语料

## 当前数据

`evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl`

Manifest：

`evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.manifest.json`

该语料从 SINAMICS S210 手册的 `15.2 List of faults and alarms` 章节抽取，包含：

- 281 条消息记录；
- 169 条 F 类故障；
- 106 条 A 类报警；
- 6 条 N 类内部消息；
- 每条保留原文、故障码、标题、参数候选、页码范围、源文件哈希和来源 URL。

## 来源

- 可访问的 PDF 来源：
  `https://publikacje.siemens-info.com/pdf/681/S210%20Manual.pdf`
- 西门子 Industry Online Support 的新版官方参考：
  `https://support.industry.siemens.com/cs/attachments/109827474/S210_S-1FK2_S-1FT2_op_instr_0424_en-US.pdf`

当前 JSONL 的 `source_sha256` 对应本次下载的 2019 手册副本。新版官方链接只作为同产品官方参考，
不同固件/手册版本不能直接混为同一金标。

## 重要边界

该语料的 `weak_record` 只是程序解析结果，不是专家金标：

- Cause 可能包含参数值说明、故障场景和 Remedy 上下文；
- 组件字段和关联组件需要专家按当前项目规则复核；
- AND/OR 故障树逻辑保持 `unknown`；
- 原始 PDF 未标注开放数据许可，不能直接把 PDF 或派生数据对外再发布；
- 使用前应确认西门子资料的再利用条款，并保留来源、版本和哈希。

## 生成命令

```powershell
python evaluation/quality_eval/public_sources/build_siemens_s210_fault_corpus.py `
  --pdf tmp/pdfs/S210_Manual_2019.pdf `
  --output-jsonl evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl `
  --output-manifest evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.manifest.json `
  --retrieved-date 2026-09-19
```

该命令只生成未标注公共语料，不调用 DeepSeek API，也不会修改生产数据库或前端。

## 30 条专家抽样清单

已从 281 条语料中按消息类型做确定性分层抽样：F 类 20 条、A 类 8 条、N 类 2 条。

- 抽样数据：`evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v1.json`
- 专家清单：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v1.md`

该清单没有预填审核结论。专家填写完成后，才能把这 30 条转换为独立金标并计算外部数据 F1。

## 第二批 30 条扩展审核清单

为扩展数据量，已从剩余未抽样语料中生成第二批审核候选：

- 候选数据：`evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v2.json`
- 专家清单：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v2.md`
- 构成为 F 类 20 条、A 类 8 条、N 类 2 条；与第一批 30 条无重复；
- 第一批和第二批合计覆盖 60 条，281 条原始语料中仍有 221 条未抽样；
- 当前仍是 `unlabeled_expert_review_sample`，不是金标，也不会自动写入生产数据库。

生成第二批时使用排除参数，确保批次之间不重复：

```powershell
python evaluation/quality_eval/public_sources/build_siemens_s210_review_sample.py `
  --input-jsonl evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl `
  --exclude-json evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v1.json `
  --output-json evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v2.json `
  --output-md evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v2.md `
  --batch-name v2
```

专家审核完成后，再将第二批导入候选标注集；只有确认审核结论、专家身份和证据后，才进入专家金标库。数据库导入应使用金标/审核后的记录，不应把这份未标注清单直接当作 `approved`。

## 第三批 30 条扩展审核清单

继续从剩余语料生成第三批不重复候选：

- 候选数据：`evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v3.json`
- 专家清单：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_review_checklist_v3.md`
- 与前两批均无重复；三批合计 90 条，仍有 191 条未抽样；
- 构成为 F 类 20 条、A 类 8 条、N 类 2 条；
- 当前仍为未标注审核候选，不进入正式金标或生产数据库。

## 全量 281 条审核队列

已将 281 条公开语料组织为 10 个互不重复的审核批次：v1–v9 每批 30 条，v10 为剩余 11 条。
批次清单见：

`evaluation/quality_eval/datasets/siemens_s210_public_fault_review_batches_v1.manifest.json`

当前状态为 `unlabeled_expert_review_queue`：其中第一批 30 条已由用户确认的专家结果覆盖，
其余 251 条仍待审核。该清单只证明覆盖和去重完成，
不证明字段语义已经正确。审核完成后，需将每批审核结果导入候选标注集，解决所有未决项，
再生成全量金标并进入数据库导入流程。

已生成统一审核队列：

`evaluation/quality_eval/datasets/siemens_s210_public_fault_full_review_queue_281_2026-09-20.json`

专家填写用文本清单：

`evaluation/quality_eval/runs/siemens_s210_public_fault_full_review_queue_281_2026-09-20.md`

审核前结构审计报告：

`evaluation/quality_eval/runs/siemens_s210_public_fault_pending_structural_audit_2026-09-20.json`

该报告发现 251 条待审核记录中有 129 条需要专家重点处理；它只报告缺证据或需语义核对，不能替代专家结论。
另有 1 条记录可以从 Cause 原文中精确提出证据补齐建议，建议文件为
`evaluation/quality_eval/runs/siemens_s210_public_fault_pending_evidence_proposals_2026-09-20.json`，
该建议同样需要专家接受后才可写回。

专家填写结论后，使用 `finalize_public_review_decisions.py` 生成最终金标快照；该工具要求所有 `pending` 都有明确结论，
并会拒绝未提供修正内容的“语义需修改”。只要仍有 `pending`、`证据不足`、`无法判断` 或明确排除记录，
输出的 `import_ready` 就保持为 `false`。

空白结论模板：

`evaluation/quality_eval/runs/siemens_s210_public_fault_review_decisions_template_251_2026-09-20.json`

当前队列统计为：281 条总记录，其中 30 条已有专家结论并已完成专家明确指出的证据补齐，另有 251 条仍为模型候选 `pending`。
因此该队列的 `import_ready=false`，不能直接写入正式金标库。原始 6 条“证据不足”结论没有被覆盖，已保留在
`fta_unified_expert_review_57_2026-09-20.json` 的历史中；补证据后的派生版本为
`fta_unified_expert_review_57_2026-09-20_evidence_resolved.json`。队列由
`evaluation/quality_eval/public_sources/build_full_public_review_queue.py` 生成，并校验覆盖、去重、批次重叠和候选证据状态。

第二批已完成一次模型抽取回放：

- 预测结果：`evaluation/quality_eval/runs/siemens_s210_public_predictions_review_v2_2026-09-20.json`
- 待审核候选：`evaluation/quality_eval/datasets/siemens_s210_public_fault_review_candidate_v2_2026-09-20.json`
- 文本清单：`evaluation/quality_eval/runs/siemens_s210_public_fault_review_candidate_v2_2026-09-20.md`
- 结果：30/30 抽取成功，30/30 证据位置通过结构匹配校验；30 条仍保持 `pending`，没有自动批准。

批量脚本使用 `/api/fta/generate` 的 `raw_text` 合同，并支持中断后按成功记录续跑；模型预测与专家审核状态分开保存。
v2–v10 共 251 条候选均已完成一次真实后端抽取回放，候选输出和字符位置校验通过，但仍全部等待专家审核。

## 最终入库闸门

全量审核完成后，使用：

`evaluation/quality_eval/project_gold/import_reviewed_dataset_to_sqlite.py`

该导入器只接受包含最终 `gold_records`、字段级 `evidence_spans` 和已解决专家结论的全量数据集，
默认要求 281 条。它会拒绝 `pending`、证据不足、无法判断或证据位置不匹配的记录；导入过程使用单事务，
并以数据集名称/版本和稳定 ID 实现幂等重跑。数据库额外保存数据集版本、原文快照、来源哈希、页码、
样本到抽取结果的映射和审核历史。

示例：

```powershell
python evaluation/quality_eval/project_gold/import_reviewed_dataset_to_sqlite.py `
  --dataset <全量最终金标.json> `
  --database backend-python/outputs/extraction_workflow.sqlite3
```

当前数据库 schema 已升级到 v4；导入测试覆盖事务回滚、证据校验和重复执行不重复写入。

## 已完成 DOCX 的候选导入

如果专家把清单填写为 DOCX，可先导入为候选标注集，不会自动升级为正式金标：

```powershell
python evaluation/quality_eval/public_sources/import_siemens_s210_expert_docx.py `
  --review-docx "C:\path\SINAMICS_S210_专家审核清单_30条.docx" `
  --sample-json evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v1.json `
  --output-json evaluation/quality_eval/datasets/siemens_s210_public_expert_review_candidate_v1.json `
  --output-md evaluation/quality_eval/runs/siemens_s210_public_expert_review_candidate_v1_report.md
```

当前候选导入结果：

`evaluation/quality_eval/datasets/siemens_s210_public_expert_review_candidate_v1.json`

复核报告：

`evaluation/quality_eval/runs/siemens_s210_public_expert_review_candidate_v1_report.md`

该文件保留原始专家填写字段、证据引用、页码、来源手册哈希和审核结论，并增加结构化疑点标记。由于 DOCX 未提供可验证的专家身份，且少数证据栏把故障上下文放在“关联组件”字段下，当前必须保持：

- `label_status=external_expert_review_candidate`；
- `human_expert_reviewed=false`；
- `eligible_for_training=false`。

只有专家确认身份、审核日期以及疑点字段后，才能生成独立外部金标。

## 3 条疑点确认后的外部审核版

当专家确认 A01706、A01788、F30655 的证据归属后，可生成审核版数据：

```powershell
python evaluation/quality_eval/public_sources/finalize_siemens_s210_expert_gold.py `
  --candidate-json evaluation/quality_eval/datasets/siemens_s210_public_expert_review_candidate_v1.json `
  --confirmation-docx "C:\path\SINAMICS_S210_3条疑点记录专家确认.docx" `
  --output-json evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v1.json `
  --reviewer-name "刘武" `
  --review-date 2026-09-19
```

该版本会保留三条证据重分类历史，并将关联组件维持为空。审核者姓名和日期通过命令参数写入；同时因为字段仍包含双语专家原值，`f1_ready=false`，需要先统一评估语言和字段归一化后再计算 F1。

## 外部金标 F1 评估

F1 评估只接受独立模型预测文件，不会把金标自身当作预测：

```powershell
python evaluation/quality_eval/public_sources/evaluate_siemens_s210_gold.py `
  --gold evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v1.json `
  --predictions evaluation/quality_eval/runs/siemens_s210_public_predictions_v1.json `
  --output evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v1_f1.json
```

没有 `--predictions` 时，程序会明确输出阻断状态，不生成虚假 F1。

生成独立模型预测的入口：

```powershell
python evaluation/quality_eval/public_sources/run_siemens_s210_predictions.py `
  --dataset evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_review_sample_v1.json `
  --output evaluation/quality_eval/runs/siemens_s210_public_predictions_v1.json
```

该入口调用本地后端的 `/api/fta/generate`，关闭知识图谱、分析报告和审核报告，只保存每条样本的抽取响应；支持中断后从已有成功记录继续。它不会写入审核数据库。

当前金标的 `gold_status.f1_ready=false`，因此生成的报告状态为 `diagnostic_completed` / `diagnostic_only`：它可以暴露漏抽、误抽和字段口径问题，但不能直接作为最终语义 F1。正式 F1 前，需要统一组件字段的中英双语表达，并明确候选原因被拆分或改写时的匹配规则。

已完成两轮独立预测对比：

- v1：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v1.json`；故障码严格 F1 为 0.500，主要问题是模型漏抽行首故障码。
- v2：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v2.json`；加入行首故障码约束和窄范围回填后，30/30 条故障码均有原文证据，故障码严格 F1 提升到 1.000。
- v2 评估报告：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_f1.json`。

v2 报告同时保留两套指标：严格字符串匹配与归一化诊断匹配。归一化后组件 F1 为 0.583，候选原因 F1 为 0.411；它只处理中英组件别名、参数括号和明确原因列表拆分，不会把空字段算作正确，也不会做无证据的语义推断。

v4 是固定 `temperature=0` 后的可比较基线：

- 预测：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v4.json`；
- 报告：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v4_f1.json`；
- 归一化主组件 F1 为 0.667，故障码 F1 为 1.000，参数 F1 为 0.864；
- 关联组件仍未放宽自动推断，归一化 F1 为 0.167，需先确认专家标注中的“关联”定义。

v6 是重启本地后端、加载“显式关系才算关联组件”规则后的完整复评：

- 预测：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v6.json`；
- 诊断报告：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v6_f1.json`；
- 30/30 条请求成功，故障码严格 F1 为 1.000，参数归一化 F1 为 0.864；
- 归一化主组件 F1 为 0.654，关联组件为 0.000。后者不是“模型已经证明关联组件错误”，而是因为当前专家金标 v1
  仍把若干正文上下文组件标在 `related_components` 中，与本轮确认的保守口径不一致；在金标重标前只作为口径诊断结果。

当前后端口径：普通正文、故障原因或处理建议中单独提到的组件，不自动进入 `related_components`；
只有明确关系表达才保留。中文 `组件为无（关联……）` 仍保留括号内组件。

已增加金标派生脚本，用于在不覆盖专家原始审核值的前提下生成口径统一版本：

```powershell
python evaluation/quality_eval/public_sources/project_related_component_policy.py `
  --input evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v1.json `
  --output evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v2_related_policy.json
```

派生结果会保留 `related_components_original_v1` 和修订原因；当前 11 条含关联组件的专家记录中，
只有存在明确连接关系的记录保留关联组件，其余作为正文上下文组件从评估字段移出。

基于该派生金标和 v8 独立预测的诊断结果：关联组件归一化 F1 为 `1.000`。唯一保留的
明确关系样本 F01357 已成功回填 `Control Unit`；普通正文中的 `using the Control Unit`
和 `to the Control Unit` 仍保持空值。该召回规则只对受控组件词表生效，不会为了提高分数
放宽普通正文提及的关联组件判定。

v8 预测和报告：

- 预测：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v8.json`；
- 报告：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_related_policy_v8_f1.json`；
- 30/30 条请求成功；故障码 F1 为 `1.000`，关联组件归一化 F1 为 `1.000`，参数归一化 F1 为 `0.864`；
- 该报告仍是 `diagnostic_only`，因为整套公开金标的 `f1_ready=false`，不能直接宣称为最终语义 F1。

## 正式 F1 前的就绪检查

为避免把诊断分数误写成“最终 F1”，已增加就绪审计脚本：

```powershell
python evaluation/quality_eval/public_sources/audit_siemens_s210_gold_readiness.py `
  --gold evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v2_related_policy.json `
  --diagnostic-report evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_related_policy_v8_f1.json `
  --output-json evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_readiness.json `
  --output-markdown evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_readiness.md
```

当前报告：

- `evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_readiness.md`；
- `evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v2_readiness.json`；
- 结论为 `not_ready_for_official_f1`；
- 故障码、参数和 `explicit_relation_only` 关联组件策略可以继续做诊断评估；
- 主组件仍保存了中英双语显示值，需要先确定规范标签/别名合同；
- `description` 和 `causes` 需要专家确认同义改写、原因拆分和参数括号处理的正式匹配规则；
- AND/OR 逻辑门仍为独立后续任务，当前不进入字段 F1。

该审计只读检查数据和已有 v8 结果，不修改专家金标，也不会把 `f1_ready` 自动改成 `true`。

## v3 正式字段评估版

在确认组件规范化、L3 description 和 L4 causes 规则后，使用以下脚本生成新的 gold 副本；原 v2 文件保持不变：

```powershell
python evaluation/quality_eval/public_sources/canonicalize_siemens_s210_gold.py `
  --input evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v2_related_policy.json `
  --output evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v3_official.json
```

v3 生成结果：

- `evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v3_official.json`；
- 30/30 条样本完成规范化；
- 33 条别名映射写入 `component_aliases`；
- 原双语组件值保留在 `component_original_v2` / `related_components_original_v2`，用于审计；
- `f1_ready=true`；
- AND/OR 逻辑门明确排除在当前字段 F1 之外。

评估器现在同时输出：

- `canonical_exact`：故障码、组件、关联组件、参数；
- `l3_semantic_macro`：description，按完全等价 1、部分等价 0.5、不等价 0 计分；
- `l4_coverage_times_precision`：causes，按原因拆分后的 coverage × precision 计分。

用已有 v8 独立预测复评：

```powershell
python evaluation/quality_eval/public_sources/evaluate_siemens_s210_gold.py `
  --gold evaluation/quality_eval/datasets/siemens_s210_public_fault_expert_gold_v3_official.json `
  --predictions evaluation/quality_eval/runs/siemens_s210_public_predictions_v8.json `
  --output evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v3_official_f1.json
```

v8 基线正式字段结果为：故障码 `1.000`、组件 `0.655`、关联组件 `1.000`、参数 `0.864`、description `0.617`、causes `0.601`。这说明语义等价规则已经真正参与计分，但模型组件抽取还没有达到报告中预期的 `0.95+`；该预期不能当作实际结果。

随后后端增加了西门子英文标题组件归一化：`SI Motion P1/P2 -> SI Motion`、`SI P1/P2 -> Safety Integrated`、`Internal software/Software timeout -> Control system (internal software)`、`Parameter error -> Parameter configuration system`、`DRIVE-CLiQ line` 和 `Encoder 1 DRIVE-CLiQ (CU)`，并将显式英文关联组件复数统一为单数规范名。

v11 完整复评结果：

- 预测：`evaluation/quality_eval/runs/siemens_s210_public_predictions_v11.json`；
- 报告：`evaluation/quality_eval/runs/siemens_s210_public_fault_expert_gold_v3_official_v11_f1.json`；
- 30/30 条请求成功；
- 故障码 F1 `1.000`，组件 F1 `1.000`，关联组件 F1 `1.000`，参数 F1 `0.864`；
- description `0.633`，causes `0.598`。

v11 中组件和关联组件没有发现未匹配记录；评估报告仍保留严格匹配、归一化匹配和正式策略匹配三套结果，便于继续定位其他字段问题。

公开数据测试套件中依赖 PDF 解析的 `test_siemens_s210_fault_corpus.py` 需要本地安装
`pdfplumber`；不依赖 PDF 的评估、抽样和策略投影测试已通过。

该修复只影响后端抽取与证据绑定，不改变现有前端布局或审核页面样式。
