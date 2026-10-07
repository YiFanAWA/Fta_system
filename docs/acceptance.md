# 验收与验证清单

更新时间：2026-10-07  
所有结果都应写清测试对象、样本/路径、命令与日期。离线单测、API 回归、专家语义审核和生产验收是不同证据层，不能互相替代。

## 2026-10-07 P2e 内部 evidence occurrence locator overlay

当前合同由后端 `EvidenceOccurrenceLocatorReview` / `EvidenceLocatorReviewResolver` 所有。它只允许显式、source-pinned 的位置选择；不等于原因语义确认、真人专家签署或 Gold。locator 随原因处置批次/候选树输出保留 provenance。无 locator、哈希不匹配、scope 内多处命中或模型引文偏离选定抽取跨度时必须 fail-closed。无模型调用；不改公开 API、数据库、Gold、原始运行或 readiness。

```powershell
python -m unittest discover -s backend-python/tests -p 'test_fta_evidence_locator_review.py' -q
python -m unittest discover -s backend-python/tests -p 'test_fta_cause_disposition.py' -q
python -m unittest discover -s backend-python/tests -p 'test_*candidate_fta*.py' -q
python -m unittest discover -s backend-python/tests -p 'test_candidate_fta_application_service.py' -q
python -m unittest discover -s backend-python/tests -p 'test_recursive_candidate_fta_extraction_service.py' -q
python evaluation/quality_eval/build_fta_baseline_manifest_v52.py --check --captured-at 2026-10-07
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

本轮结果以各项实际运行记录及 v52 manifest 为准。它证明内部合同/离线行为，不是新模型运行或 FTA 语义效果成绩。

## 2026-10-07 P2d F30021 occurrence/scope 离线对账

报告：[Markdown](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.md) · [JSON](../evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.json)。核验了 F30021-C04 的历史定位审核、来源哈希、唯一 Possible causes scope 和当前 v5 原始运行。定位范围核验通过，但没有应用到原始运行；C04 仍 unresolved，树仍 blocked，语义缺陷关闭数为0。

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_reconcile_f30021_occurrence_review_v1 -v
python evaluation/quality_eval/public_sources/reconcile_f30021_occurrence_review_v1.py --check
python evaluation/quality_eval/build_fta_baseline_manifest_v51.py --check --captured-at 2026-10-07
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

7项对账回归通过；没有模型请求、原始运行修改、Gold/数据库/生产 API/共享合同或 readiness 变化。

## 2026-10-07 P2b F30021 当前版本真实来源开发运行

单例审计：[报告 v2](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.md) · [结构化结果](../evaluation/quality_eval/runs/fta_real_source_development_case_audit_v2_2026-10-07.json) · [原始模型运行](../evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json) · [不覆盖原文的离线复核 v2](../evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.json)。

用户授权上限4次模型请求，实际4次成功、重试0、无自动修复。整树因cause occurrence歧义、顶事件引文不唯一、子项集合不完整及门置信策略不可用而blocked；`fta_ready=false`、`production_ready=false`。runner 15项、后端相关86项、event-scope 8项离线测试通过。该结果是单例工程审计，不是专家Gold或准确率结论。

```powershell
python -m unittest -v test_probe_candidate_fta_raw_source_v1.py
python -c "import sys,unittest; sys.path.insert(0,'tests'); names=['test_evidence_mapping','test_fta_cause_disposition','test_candidate_fta_extraction_service','test_recursive_candidate_fta_extraction_service']; suite=unittest.TestSuite(); loader=unittest.TestLoader(); [suite.addTests(loader.loadTestsFromName(n)) for n in names]; result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(not result.wasSuccessful())"
python evaluation/quality_eval/build_fta_baseline_manifest_v50.py --check --captured-at 2026-10-07
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

第一条命令在 `evaluation/quality_eval/public_sources` 目录执行；第二条在 `backend-python` 目录执行；其余在仓库根目录执行。P2a合同/历史审计曾通过35+16+8项定向测试及v48 367/367哈希校验，属于此前独立证据，不与本次模型运行合并成准确率。

## 2026-10-07 P2真实来源开发案例合同审计（离线）

只读审计覆盖 F01681、F30027、F30021、F06000、F35400 与 NASA Figure 7，分别检查原因分类、事件身份、层级、子项集合及逻辑门证据。审计工件：[Markdown报告](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.md) · [结构化JSON](../evaluation/quality_eval/runs/fta_real_source_development_contract_audit_v1_2026-10-07.json)。当前 `CauseDispositionService` 为 v5，而归档的 Siemens 模型运行是 v2/v4、NASA Figure 7 是 event-scope v6；因此历史输出没有被当作当前版本验收。

```powershell
python -m unittest discover -s backend-python/tests -p 'test_*candidate_fta*.py' -q
python -m unittest discover -s backend-python/tests -p 'test_fta_cause_disposition.py' -q
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_run_fta_event_scope_model_v6 -q
python evaluation/quality_eval/build_fta_baseline_manifest_v49.py --check --captured-at 2026-10-07
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

本轮结果：35 + 16 + 8 项定向测试通过；v48快照校验367/367有效。没有模型请求、Gold/数据库/生产API写入或 readiness 提升。P2合同和历史运行审计完成，但当前v5真实来源运行及语义缺陷关闭仍待后续；`fta_ready=false`、`production_ready=false`。

## 2026-09-29 Event-scope prompt v8 候选（离线）

本节记录 v36 阶段的历史状态；当时 v8 确实尚未接入 runner。当前 v37 的 runner 与预检状态见本文件末尾的“事件范围语义 smoke 输入与 one-shot runner”。

用户指出部分逻辑门需要通过语义而非显式 `OR/AND` 字样判断。v8 允许依据完整命题提出语义 OR（多个独立替代路径指向同一输出）或语义 AND（多个共同必要条件指向同一输出）。逻辑引文仍必须直接支持 child 命题、child 间逻辑关系及同一 output；单纯原因列表、事件共现、scope 外的 `or`、不连续拼接或实质歧义均不能定门，应 fail-closed 为 `unknown`。回归集含 6 条非 Gold 案例，包含无运算符 OR/AND 正例和歧义/词面反例。

```powershell
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v36 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python evaluation/quality_eval/build_fta_baseline_manifest_v36.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

验收边界：离线测试只检查提示内容、非 Gold 回归策略和 label-free 输入；v8 未接 runner、未调用模型，不能声称语义问题已解决或报告模型准确率。v6 原始失败观察保留；正式 Gold/生产 API/数据库不变，`fta_ready=false`、`production_ready=false`。在线验证需另行明确授权。

## 2026-09-29 Event-scope 语义审核回归 v1（离线）

新增审核规则与回归案例，范围仅限评测：直接 OR/AND 连接关系必须有同一 scope 的原文证据；仅共现不推 AND；共享事件身份和复合长句不由自动测试修补。案例包含三个手写政策示例与三个 Figure 7 v6 实际观察，不是专家 Gold，不计算模型准确率。

```powershell
python -m unittest evaluation.quality_eval.test_fta_event_scope_semantic_review_regression_v1 evaluation.quality_eval.test_build_fta_baseline_manifest_v34 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python evaluation/quality_eval/build_fta_baseline_manifest_v34.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

验收要求：v6 的 S1 替代连接词漏绑定继续被测试标为语义待审；E2/E4 与 E5/E7 保留人工审核、不自动合并/拆分；Gold/生产/数据库/readiness 状态不提升。本轮无在线模型调用。

## 2026-09-29 Event-scope prompt v7 候选（离线）

v7 在 v6 文本提示基础上要求已知门型的 `logic_evidence` 直接覆盖 child 间逻辑及其通向同一 output 的关系；连接词孤立出现、事件共现或与当前 output 无关的局部 `or` 均不足以确定门型。固定输入使用 Figure 7 已见 Dev 包，回归集包含正例和反例；此检查只证明提示规则与输入隔离合同存在，不证明模型会正确遵循提示。

```powershell
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v7 evaluation.quality_eval.test_fta_event_scope_semantic_review_regression_v1 evaluation.quality_eval.test_build_fta_baseline_manifest_v35 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python evaluation/quality_eval/build_fta_baseline_manifest_v35.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

验收边界：v7 尚未接入模型 runner、未运行模型；v6 输出和三个语义问题保持不变。任何线上验证需单独明确授权；不得据离线测试提升 Gold、语义接受、`fta_ready` 或 `production_ready`。

## 2026-09-29 Figure 7 v6 单次授权运行与离线复核

用户明确授权一次请求后，执行 `python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py --authorize-single-request`：请求 1 次、重试 0 次，`finish_reason=stop`，严格 JSON 解析成功。输出 7 个节点、3 个 scope；层级合同有效，10/10 引文位置通过。v5 的重复输出 scope、单子项 gate 和已知门缺 `unknown_reason` 三类结构问题均未重现。

但语义尚不接受：S1 的作用域引文含显式 `or`，模型仍返回 `unknown` 且 `logic_evidence=null`；E2/E4 重复表示单个电芯爆炸，E5/E7 的复合事件边界也不确定。详细定性观察见 [v6 复核](../evaluation/quality_eval/runs/fta_event_scope_model_run_v6_dev_comparison_2026-09-29.md)。这是一个已见 Dev 样例，不是准确率、Gold 或独立泛化测试；没有修改正式 Gold、数据库、生产 API 或 readiness，`fta_ready=false`、`production_ready=false`。本次单次授权已用完，不得自动重试；新请求需要新的明确授权。

可重复的非网络检查：

```powershell
python -m unittest evaluation.quality_eval.test_run_fta_event_scope_model_v6 evaluation.quality_eval.test_build_fta_baseline_manifest_v33 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python evaluation/quality_eval/build_fta_baseline_manifest_v33.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

## 2026-09-29 v6 提示词离线准备（无模型请求）

v6 是针对 v5 层级/字段合同失败准备的离线提示词候选，不接入请求器，也没有发起模型请求。以下验证只证明本地提示词约束与结构 fixture 合同一致，不证明模型输出质量。最近一次实际模型运行仍是 v5，整树被合同阻断。

```powershell
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v6 evaluation.quality_eval.test_run_fta_event_scope_model_v5 evaluation.quality_eval.test_build_fta_baseline_manifest_v31 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python -m unittest evaluation.quality_eval.test_event_scope_tree_contract -v
python evaluation/quality_eval/build_fta_baseline_manifest_v31.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

在线对照未授权于本轮；需要 v6 请求器接线和新的明确授权后才能进行。Gold、数据库、生产 API 和 readiness 均未改变。

## 2026-09-29 v6 单次请求器接线与离线验收（无模型请求）

v6 专用请求器已接线到 v6 提示词，保留验证后的 label-free 输入投影、严格 JSON、thinking disabled、8192 输出上限、SDK 零重试和独占运行产物。默认 `--preflight` 仅校验输入/配置且不访问模型；任何真实请求都必须显式传入 `--authorize-single-request` 并另行取得用户针对该请求的明确授权。无效或被合同阻断的输出原样保存并标记 `blocked`，不自动修复、不重试。以下本地验证与 mock 测试没有产生模型请求：

```powershell
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v6 evaluation.quality_eval.test_run_fta_event_scope_model_v5 evaluation.quality_eval.test_run_fta_event_scope_model_v6 evaluation.quality_eval.test_build_fta_baseline_manifest_v32 evaluation.quality_eval.test_validate_fta_baseline_manifest -v
python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v6.py --preflight
python evaluation/quality_eval/build_fta_baseline_manifest_v32.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

此阶段只证明请求器的本地接线、授权门、单次/零重试约束和输出留存合同；没有 v6 模型输出、语义评估、准确率/校准/泛化结论，也没有改 Gold、数据库或 readiness。v5 仍是最新实际模型运行。

## 2026-09-29 Figure 7 v5 单次模型运行与离线复核

本轮按用户明确授权执行一次 DeepSeek 请求，重试 0 次，thinking 关闭，Gold 未进入模型输入。响应严格 JSON 可解析，输出 10 个节点、4 个 scope，15/15 引文位置唯一有效。树合同仍 `blocked`：E1 有多个输出 scope，S2 只有一个直接 child；证据结构检查发现 S4 的已知门缺少必需的 `unknown_reason` 字段。模型局部将 A、B 列作顶事件 T 的同级子项，但不可将这个局部表现外推为整树正确或门型准确。该 seen-Dev 单例不计算准确率、F1、校准或泛化；不接受为 Preview 树，不写 Gold/数据库/生产 API，`fta_ready=false`、`production_ready=false`。此次授权已用完，不得自动重发。

离线回归和清单验证命令：

```powershell
python -m unittest evaluation.quality_eval.test_event_scope_tree_prompt_v5 evaluation.quality_eval.test_run_fta_event_scope_model_v5 evaluation.quality_eval.test_build_fta_baseline_manifest_v30 -v
python evaluation/quality_eval/build_fta_baseline_manifest_v30.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

## 2026-09-29 NASA Figure 7 v4 单次模型运行与离线复核

本节记录一次用户明确授权的外部请求，不构成可重复的自动验收命令；不得为复现报告而重发 API 请求。原始响应、尝试收据和合同评估分别见 [run JSON](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.json)、[attempt receipt](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v4_2026-09-29.attempt.json) 和 [assessment JSON](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v4_2026-09-29.json)。

观察结果：1 次请求、0 次重试，`finish_reason=stop`，严格 JSON 成功；Gold 未进入模型输入。证据位置合同为 9/9 唯一字面匹配，但这不证明引用语义支持。树层级合同有 1 个 blocker：`S2` 只有 1 个直接子项，未自动修改输出；三个预测门均为 `unknown`。根门与 AI 角色审核文本标签存在定性分歧，但参考并非人类专家 Gold，且预测/参考 scope 映射未验证，因此不计算准确率、F1、校准或泛化成绩。该输出不接受为 FTA Preview 树，不写 Gold/数据库/生产 API，`fta_ready=false`、`production_ready=false`。

离线复核可重复运行：

```powershell
python evaluation/quality_eval/compare_fta_event_scope_model_run_v4_dev.py --check
python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_model_run_v4_dev evaluation.quality_eval.test_run_fta_event_scope_model_v4 evaluation.quality_eval.test_build_fta_baseline_manifest_v28
```

活动清单通过：

```powershell
python evaluation/quality_eval/build_fta_baseline_manifest_v28.py --check --captured-at 2026-09-29
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

## 2026-09-29 NASA Figure 7 单样例单次推理

```powershell
python -m unittest evaluation.quality_eval.test_run_fta_event_scope_model_v1 -v
python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v1.py --preflight
python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v1.py
```

本轮执行了上述本地隔离测试与预检，并发起**恰好一次** DeepSeek 请求，SDK 自动重试关闭。API 返回 `finish_reason=length`，已用满 3000 输出 token，但最终正文为空且非严格 JSON；因此没有候选节点/门型预测，未执行 Gold 对比，准确率/校准指标为 N/A。未重发。输入严格来自验证后的 `model_input` 投影；Gold 与图示参考未发给模型。完整事实见[JSON 运行记录](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v1_2026-09-29.json)、[单独评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v1_2026-09-29.md)。该技术尝试不是专家审核/正式 Gold/独立 Final；未改数据库、生产 API 或 readiness。

## 2026-09-29 NASA Figure 7 JSON-mode 单次重跑

~~~powershell
python -m unittest evaluation.quality_eval.test_run_fta_event_scope_model_v2 -v
python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v2.py --preflight
python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v2.py
~~~

v2 单测 4 项通过，预检确认 DeepSeek provider/model、同一隔离 `model_input`、8192 `max_tokens`、`response_format=json_object` 和 0 SDK 重试。获准 API 请求恰好 1 次；completion tokens 达 8192，`finish_reason=length`，最终 content 为空，严格 JSON 未解析。结构/引文评估为 `truncated`；Gold 比较未执行。DeepSeek JSON Output 文档说明 JSON mode 仍可能返回空 content，因此本次不能确定根因，也不能宣称提高预算/JSON mode 后得到模型成绩。v1+v2 累计两次单次尝试、零重试；没有第三次请求。详见 [v2 原始响应](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.json)、[attempt receipt](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_v2_2026-09-29.attempt.json)、[机器评估](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.json) 和 [重跑报告](../evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v2_2026-09-29.md)。未改 Gold、数据库、生产 API 或 readiness。

## 本地基础检查

从仓库根目录运行：

```powershell
python scripts/verify_repo_layout.py
python -m unittest discover -s backend-python/tests -p "test_*candidate_fta*.py" -q
python -m unittest discover -s backend-python/tests -p "test_generic_retrieval_pipeline.py" -q
python -m unittest discover -s backend-python/tests -p "test_domain_router.py" -q
python -m unittest discover -s backend-python/tests -p "test_rag_api.py" -q
```

2026-09-27 历史运行结果：布局检查通过；以上四组分别为 24、3、4、4 项测试，全部通过。它们覆盖当前候选 FTA 合同/应用服务、离线 Generic Retrieval、Router 规则与 RAG API 固定测试，不覆盖整套后端和真实生产环境。

## 2026-09-28 Candidate FTA 门评估证据回归

以下是 v8 轮次的验收快照；本轮 v9 新增验证见文末，快照中的结果保留原值，不代表 v9 总测试量。

| 命令 | 结果 | 覆盖边界 |
| --- | --- | --- |
| `python -m unittest discover -s backend-python/tests -p "test_*candidate_fta*.py" -q` | v8 快照：33 tests，OK | 当时 Candidate FTA 合同/应用/递归候选固定测试 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_probe_candidate_fta_gate_text_evidence_v1.py" -q` | 5 tests，OK | PDF 来源哈希/页码引文、标签盲化、提示构造、评分合同、默认 fail-closed 策略 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v8.py --check --captured-at 2026-09-28` | v8 历史快照检查；活动版本现为 v9 | v1–v8 保留为历史快照 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | 校验活动 manifest 的全部 artifact 哈希 | 当前默认目标为 v13；历史验收记录保留各自当时版本 |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_gate_text_evidence_v1.py` | DeepSeek Flash 11/11 成功；原文复核标签描述性一致 11/11；known 9/9、unknown 2/2、引文 9/9 | 只测候选门评估提示和门证据绑定；不是完整 FTA Pipeline 或正式 Gold 成绩 |

在线探针每节点一次请求、无重试，完整结果见[Markdown 报告](../evaluation/quality_eval/runs/candidate_fta_gate_text_evidence_probe_v1_2026-09-28.md)和[JSON 运行文件](../evaluation/quality_eval/runs/candidate_fta_gate_text_evidence_probe_v1_2026-09-28.json)。标签来自 AI 原文证据复核，不是人类专家 Gold；样本只覆盖 3 个来源簇的 11 个特选节点。候选服务未注入置信策略时仍 fail-closed 为 `unknown`；本次没有选阈值或改变策略。pypdf 对 DOE PDF 重复 `/Length` 字典键有警告，PDF 摘录仍通过哈希/页码检查；此来源警告保留为已记录的非阻断限制。`fta_ready=false`、`production_ready=false`、Gold 与数据库状态均未变。

项目 README 中其余最小检查入口是：

```powershell
python -m compileall -q backend-python evaluation
$env:PYTHONUTF8='1'
python backend-python/fta_regression_check.py
npm run build --prefix frontend
```

本轮没有重跑以上完整 compile/regression/frontend build；前端依赖目录当前存在，但必须以新鲜命令结果为准。需要复核所有测试时，使用：

```powershell
python -m unittest discover -s backend-python/tests -v
```

## 当前路径验收矩阵

| 路径 | 必要验收 | 当前证据 | 当前限制/停止条件 |
| --- | --- | --- | --- |
| 原文抽取与审核 | 抽取记录与 evidence 一起持久化；review 追加不可变决定；重启后仍能按最新状态读取 | `test_extraction_pipeline.py`、`test_causal_review_repository.py`；API 见 `docs/api-usage.md` | 本轮未向用户 SQLite 写入或做运行 API 全流程 |
| 放行与建树尝试 | 只按最新审核状态放行；每次建树尝试均有独立历史及树合同校验 | `docs/extraction-review-build-workflow.md`；对应 build/repository tests | 不代表自然语言因果和门型正确 |
| S210 RAG API | 30 条语义回归及 24 条 Boundary 回归保持合同、citation 和边界指标 | [Baseline v1.1](rag-baseline-v1.1.md) 记录 2026-09-22 的历史真实 API 回归 | 本轮未启动 API/模型；不可标注为本轮重新通过 |
| Generic Retrieval | adapter roles、exact fusion、候选去重和 reranker 输入合同 | 本轮 `test_generic_retrieval_pipeline.py`：3/3 通过 | 离线模块测试不等于 Generic 已切入 S210 API |
| Rule Domain Router | 可解释强弱信号、低证据时保留 cross-domain | 本轮 `test_domain_router.py`：4/4 通过；[Router v1](domain-router-v1.md) 有离线对照 | 未接 API，不作为生产默认 |
| 候选 FTA Preview | 引文/offset、scope、child set、unknown/blockers、局部重试合同 | 2026-09-28 候选 FTA 测试 33/33；另有门提示探针 11 个开发样例 | 无候选 API、无正式 DB/Gold；未选门策略、概率未校准；探针不覆盖完整流程 |
| 生产级自动 FTA | 专家/正式 Gold、独立来源校准、接受与弃判风险门槛、持久化/API/回滚/审计 | 当前候选 FTA 报告及门节点状态 | **未通过**；`fta_ready=false`、`production_ready=false` 必须保持 |

## 2026-09-28 Preview Ready 标志合同回归

```powershell
python -m unittest backend-python.tests.test_fta_graph_contract -v
```

本轮新增 `test_preview_cannot_be_marked_fta_ready`，与既有生产就绪标志测试一起验证 Preview 同时拒绝 `dataset_info.fta_ready=true` 和 `dataset_info.production_ready=true`。该测试只证明合同拒绝路径受回归保护，不代表模型能正确生成因果结构或逻辑门；当前 readiness 仍为 blocked，两个全局标志仍为 false。此测试在当前工作树，尚未提交。

真实 FTA 效果评测当前仍不可作为可信独立验证：候选运行配置已由下方 lock v1 快照，但现有 47 案例是 36 条非模型调用的合同/边界回归加 11 条已标注图示开发样本，不含逐故障完整原文因果结构的独立 Final Gold。还需准备未参与开发的整份来源文档及其完整树标签，才能运行锁定配置并报告结构、因果边、证据、逻辑门和弃判指标。

### 2026-09-28 建树评测运行配置快照

```powershell
python evaluation/quality_eval/build_fta_generation_eval_lock_v1.py --check --captured-at 2026-09-28
python -m unittest discover -s evaluation/quality_eval -p "test_build_fta_generation_eval_lock_v1.py" -q
```

配置锁当前解析为 `deepseek-flash`（`api.deepseek.com`），temperature=0、timeout=120 秒、最多 2 次重试；记录了抽取至候选树的 14 个源文件 SHA-256 和 Python/OpenAI SDK 版本。配置锁不包含 API 密钥、不调用模型；供应商别名不等于不可变权重快照。该快照只冻结候选运行配置，独立 Final 数据仍未创建，故不得据此报告建树准确率。

## 候选 FTA 进入更高阶段的硬门禁

下列条件全部满足前，不得把 Preview 输出升级成自动批准树：

1. 门节点审核集 v6 已关闭 F30021-C04 的证据定位 pending：子项精确跨度为 `[332,372)`，位于唯一 Possible causes scope 内；故障值段重复句不纳入该 scope。此项只解决引用位置，逻辑门仍为 `unknown`；
2. 建立与评估目标一致、跨来源/独立簇切分的节点级 AND、OR、unknown 金标。当前事件级 AND 为 0，不能校准三分类门策略；AI 角色标签不能替代具名领域专家 Gold；
3. 以独立评测验证候选结构、作用域、原因完整性、证据支持及 unknown 拒判；报告覆盖率与错误接受率，不仅报告 Top-1 一致率；
4. 明确允许风险与弃判策略后，才可选择/校准门接受策略；模型自报概率本身不是校准证据；
5. 覆盖真实原文到 ExtractionResult、递归 Preview、持久化、API、重试、审批和审计的集成链路；失败不得丢失已有抽取和证据；
6. 完成并审阅事件发生概率数据的来源、时间窗口、样本数与独立性依据；概率检查只能审计已确认结构，不得自动推翻门标签；
7. 通过独立的端到端验收、备份/恢复与回滚验证后，才能重新讨论 `fta_ready` 与 `production_ready`。

## Stop Conditions

- 文档性目标：索引、状态审计、架构、验收四份文档互相链接，引用路径存在，根 README 可到达索引；
- 回归性目标：只报告本轮实际执行的命令和样本范围；历史/API 运行明确标日期；
- 生产性目标：未满足上一节全部硬门禁时，停止在 Preview，绝不把 AI 探针或离线树图描述为已批准/生产树。

## Evidence Log

本轮的证据是当前代码固定测试和仓库布局脚本输出；以上历史 RAG HTTP 报告仍带原始运行日期，不以本轮单测代替重跑。所有运行产物应保存命令、数据集版本、source/model/config digest、开始日期和结果路径；AI/人工来源必须分开记载。

## Drift Checklist

- API 端点是否真的组装并调用了文档声称的 owner 模块？
- offline/preview 模块是否被误报为生产接线？
- Gold、AI 角色审核、真人专家签署是否被区分？
- 模型自报 gate probability 是否被误写为校准 confidence 或事件概率？
- 评测报告是否对应当前代码、数据集版本及明确的样本范围？
- dirty worktree 的既有变更是否被保护，且无未授权 stage/commit？

## Drift Lock

每次推进先对照 [当前状态审计](current-state-audit.md)、[架构边界](architecture.md) 与本验收表；任何当前接线、owner、Gold provenance 或生产状态变化都必须同步写回本真源索引。运行门禁失败时保留失败证据，不通过改写历史报告来消除差异。

## 项目治理 guardrail

```powershell
python C:/Users/爹/.codex/skills/sliver-engineering-workflow/scripts/check_project_guardrails.py `
  C:/Users/爹/Documents/Codex/2026-09-11/ni/work/Fta_system `
  --mode adoption --truth-dir docs
```

本次新建真源文档前运行该检查时，报告缺少 4 份真源文档及 `AGENTS.md` 所需治理片段。补齐文档并重跑后，文档缺项、heading/snippet 和索引链接均已消除；目前只剩仓库 `AGENTS.md` 未包含工具要求的治理片段。该宪法文件不在本次授权修改范围内，因此保留为治理项，不擅自改写。

## 2026-09-28 当前原文候选 FTA 回归

提示语义修正后，本地执行候选 FTA 固定测试 33 项、cause disposition 测试 9 项、原文探针测试 8 项，均通过；相关 Python 文件 `py_compile` 成功。

使用当前 CandidateFtaApplicationService 和 DeepSeek Flash，对两条来源固定的完整原文重新运行四个阶段（Fault Extraction → Cause Disposition → Structure Decomposition → Gate Assessment），关闭重试：

| 样本 | 结果 | 运行报告 |
| --- | --- | --- |
| F35400 | 3 节点；2 个定性触发条件均连接顶事件；闭合枚举 scope 完整；5/5 候选树引文精确且唯一；gate=unknown，唯一 blocker 为置信策略不可用 | [JSON](../evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.json) · [Markdown](../evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.md) |
| F06000 | 13 节点；10 个事件候选、1 项通用摘要被排除；十项外层 scope 和两项局部 either-or scope 完整；17/17 候选树引文精确且唯一；两门均 unknown，唯一 blocker 为置信策略不可用 | [JSON](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.json) · [Markdown](../evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.md) |

这是两条开发回归，不是独立 Final、Gold、真人专家审核或整体准确率；仅证明这两条原文在当时提示下可生成带来源的可审核 Preview。正式 Gold、数据库及生产 API 未变，`fta_ready=false`、`production_ready=false`。

### 2026-09-28 Cause disposition v2 原文回归

先修正原文探针把数据集名写死为 S120/S150 的审计错误：artifact 现在记录实际输入 corpus 的文件名，并有单测覆盖。还修正了 S210 corpus 来源字段名与旧脚本不一致的问题，来源 PDF 文件名/SHA-256、章节、页码、原文 offset 均写入来源元数据。随后对 S210 原文 F01681、F30027 各运行当前完整四阶段流程；`OPENAI_MAX_RETRIES=0`，无重试。之后离线重核两份产物的 corpus 来源元数据，没有再次调用模型。

| 样本 | 结果 | 审计 |
| --- | --- | --- |
| F01681 | 15条故障值配置原因候选、1条通用摘要排除；38节点、12个局部分组 | 树引文60/60精确且唯一；所有门 unknown；1个替代集合与1个条件作用域仍有完整性 blocker |
| F30027 | 9条原因候选；12节点、2个作用域 | 树引文15/15精确且唯一；9项编号原因集合和局部 either-or scope 完整；两门均 unknown |

两条均为 `candidate_ready_for_review` Preview，而不是已审核树。F30027 顶层“9个候选原因”本身不自动证明 OR；F01681 故障值说明也没有因改成候选原因就被当作实例已发生。两个 artifact 均保留 `fta_ready=false`、`production_ready=false`、`formal_gold=false`、`database_written=false`。第一轮 cause prompt v1 的阻断运行作为失败诊断继续保留。完整数据和边界说明见[候选 FTA 文档](candidate-fta-generation-v1.md)及 [FTA baseline manifest v8](../evaluation/quality_eval/fta_baseline_manifest_v8.json)。

### 2026-09-28 Cause disposition v2 扩展原文回归（历史 manifest v9）

继续使用固定来源原文跑四阶段流程（Fault Extraction → Cause Disposition → Structure Decomposition → Gate Assessment），关闭重试；这是开发回归，不是准确率、正式 Gold 或独立 Final。AI 子智能体仅作为受授权的 AI 复核角色；这不等于真人签署，Gold/数据库/readiness 均保持 false。

| 样本 | 结果 | 复核要点 |
| --- | --- | --- |
| F30021（S210） | 5 节点、4 个 cause 候选；树 blocked；一个 OR 提议最终仍为 unknown | cause-3 引文重复，保留 blocker；顶事件短引文也非全局唯一。该历史运行早于顶事件歧义守卫，故 artifact 未被改写；v9 单测验证新守卫会额外阻断这类顶事件证据 |
| F35400（S120/S150） | 3 节点、2 个 cause 候选；`candidate_ready_for_review`；5/5 引文精确且唯一 | 一个 scope 的模型 OR 提议未被接受，门仍 unknown（置信策略不可用） |
| F06000（S120/S150） | 15 节点、11 个 cause 候选、4 个 scope；21/21 引文精确且唯一 | 两个布尔门 scope 均 unknown；`not_applicable` scope 另计。顶事件与“监测时间内未出现 READY”存在潜在语义重叠，嵌套原因范围需人工语义复核，不能仅凭结构和证据完整就宣称树正确 |

F01681 的独立 AI 角色复核另发现：15 条 `r0949` Fault value 解释不能自动证明到顶事件的逐项因果关系；`source_cause_index=1` 在抽取层缺 evidence span；Remedy 中出现 `xxxx=9507`，但它与顶层 cause scope 的关系尚未对账，因此暂不能声称原因范围完整，也不能自动把它提升为 causal child。输入文本 SHA-256 与原始运行/语料一致；原始运行自身未记录 PDF SHA-256，后续 provenance audit 中的 PDF 哈希与语料元数据匹配。详细 findings 见[结构化复核 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json)和[复核说明](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md)。这些是 AI 审计发现，不是真人签署或 Gold。

来源 PDF/输入文本哈希、章节、页码与 offsets 记录在运行 JSON 中。artifact 根部 `live_model_development_probe_not_expert_review` 描述模型开发运行；树对象的 `user_authorized_ai_expert_role` 表示流程使用受授权 AI 角色；两者都不表示真人审核完成，运行中没有把 `human_reviewed` 置为 true。候选状态仍只供审核，门概率为未校准提议。该 v9 是历史基线；当时活动策略记录在 v12、活动研究清单为 [FTA baseline manifest v14](../evaluation/quality_eval/fta_baseline_manifest_v14.json)，后续活动基线已更新至 v15。独立 Final 未建立，Gold、数据库、生产 API 均未变，`fta_ready=false`、`production_ready=false`。

本轮针对性验收：

| 命令 | 结果 | 边界 |
| --- | --- | --- |
| `python -m unittest backend-python.tests.test_candidate_fta_extraction_service -q` | 17 tests，OK | 含重复顶事件引文时整树阻断的回归 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v9 -q` | 3 tests，OK | v9 数据账、运行边界与 artifact 哈希构造校验 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v9.py --check --captured-at 2026-09-28` | `status=current`，119 artifacts，3 条新增原文样本，readiness 均 false | 历史 v9 manifest 与其生成内容一致性 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py --manifest evaluation/quality_eval/fta_baseline_manifest_v9.json` | `valid`，121/121 artifact 哈希通过 | 历史 v9 artifact 的路径及 SHA-256 |

#### 抽取原因证据门禁与 F01681/F30027 离线重放后续

随后增加 FTA 专用的抽取证据门禁：cause disposition 只接受抽取阶段已绑定的唯一 indexed `CAUSE` span；处置阶段模型引用不能代替缺失/歧义的抽取证据。Cause mapper 对 source-only 的保守对齐可忽略省略的括号参数注记与末尾句号，同时返回含原注记的真实 source slice；单双/弯引号与空白也参与规范化。重复位置仍全部保留，不自动选位。使用归档的模型抽取响应离线重放 S210 原文，F01681 16/16 与 F30027 23/23 cause 均有唯一 indexed span；F01681 index 1 缺失问题在当前 mapper 回放中已补齐，但旧 Preview 保持原样。此项不解决因果边证明、`xxxx=9507` cause scope 对账或门型真值。

| 命令 | 结果 | 边界 |
| --- | --- | --- |
| `python -m unittest backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_recursive_candidate_fta_extraction_service backend-python.tests.test_fta_cause_disposition backend-python.tests.test_evidence_mapping -q` | 78 tests，OK | 含 F01681/F30027 保存响应离线重放与缺/重复抽取证据 fail-closed |
| `python -m unittest discover -s backend-python/tests -q` | 263 tests，OK | 后端回归；不是语义准确率或专家 Gold |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v9.py --check --captured-at 2026-09-28` | `status=current`，121 artifacts，readiness 均 false | 历史 v9 manifest 与其生成内容一致性 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py --manifest evaluation/quality_eval/fta_baseline_manifest_v9.json` | `valid`，121/121 artifact 哈希通过 | 历史 v9 artifact 账目 |

### 2026-09-28 Cause disposition v3：F01681 单样本在线复演（历史开发快照）

用户确认的边界保持不变：Cause/Possible causes 范围内明确列出的自然语言原因可作为待审核候选；故障值/参数/位/索引到解释文本的映射不能仅凭映射连至顶事件。F01681 v2 历史运行不回写。

本轮对固定原文 `SIEMENS_S210_2019_F01681` 使用 DeepSeek Flash 跑完整四阶段流程，`OPENAI_MAX_RETRIES=0`。4/4 阶段成功；15 条 fault-value/parameter 解释被归为 `relation_only`，唯一 `Cause` 条目 index 0 被提出为候选。树有 2 节点、1 个单 child `not_applicable` scope，无独立关系边；抽取 54/54 引文 offset 精确，候选树 3/3 引文精确且唯一。在线运行是**单样本开发证据**，不是准确率或泛化成绩。

独立 AI 子智能体只读复核结论 `NEEDS_REVISION`：Cause index 0 的 “The parameter cannot be parameterized with this value.” 可能只是顶事件 “Incorrect parameter value” 的同义重述，没有提供独立上游机制。运行产物保留原样；不把候选静默删除或批准，不写 Gold/数据库。后续需在 Cause disposition 中区分“有新增因果机制的信息”与“对顶事件的释义/摘要”，添加离线回归，再另行评估是否需要在线重跑。此前 `Remedy xxxx=9507` 与 Cause 范围关系仍未闭合。

| 命令/证据 | 结果 | 边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py --corpus evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl --sample-id SIEMENS_S210_2019_F01681 --output evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.json`，环境 `OPENAI_MAX_RETRIES=0` | 4 次请求、4 次成功；`relation_only=15`、`fta_event_candidate=1`；结果 proposed | 单样本在线开发复演，不是专家 Gold/准确率；旧 v2 保持不变 |
| [运行 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.json) 与 [Markdown](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.md) | 引文 offset 与唯一性检查均通过；`fta_ready=false`、`production_ready=false` | 只证明该运行文件中保存的偏移和当前状态 |
| [独立 AI 子智能体复核](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.md) | `NEEDS_REVISION`；唯一 Cause 候选可能重述顶事件 | AI 角色审核，不是真人专家签署；阻止语义验收/Gold 合并 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v11 -q` | 2 tests，OK | manifest 数据账合同、v10 不变、运行实况与 readiness 边界 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | 路径约束、哈希校验和活动 v12 |
| `python -m unittest discover -s backend-python/tests -p "test_fta_cause_disposition.py" -q` | 12 tests，OK | v3 cause disposition 合同回归；不等于在线语义准确率 |
| `python -m unittest discover -s backend-python/tests -p "test_candidate_fta_extraction_service.py" -q` | 17 tests，OK | 候选树层的映射隔离与证据/结构合同 |
| `python -m unittest discover -s evaluation/quality_eval/public_sources -p "test_probe_candidate_fta_raw_source_v1.py" -q` | 10 tests，OK | 原文探针来源、阶段归属与当前 v3 prompt 标识 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v11.py --check --captured-at 2026-09-28` | `current`，131 artifacts，readiness 均 false | 检查历史 v11 快照可重复生成 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py --manifest evaluation/quality_eval/fta_baseline_manifest_v11.json` | v11 历史生成时为 `valid`，131/131 | 历史 v11 哈希；共享文件后续更新后以当前 v12 为活动真源 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |

Formal Gold、数据库、生产 API、门策略和 readiness 均未改变；v3 是旧 prompt 的在线开发快照，当时活动清单为 v12、后续更新为 v14（现行活动基线已更新至 v15）。

### 2026-09-28 Cause disposition v4：顶事件重述边界离线回归（历史快照，后续已有在线复演）

v4 要求将候选原因与 `top_event` 作语义比较：纯释义/同义重述且没有新增独立上游信息时留为 `causal_summary + relation_only`；无法判断则 `unresolved`。这次只做 prompt 与合同回归，没有发起在线模型调用。v3 的 F01681 运行、独立 AI 复核和所有 Gold 数据保持原样。

| 命令 | 结果 | 边界 |
| --- | --- | --- |
| `python -m unittest discover -s backend-python/tests -p "test_fta_cause_disposition.py" -q` | 14 tests，OK | 提示词、summary/顶事件重述、host downgrade、原 cause 正例与证据门禁；不证明模型在线语义准确率 |
| `python -m unittest discover -s backend-python/tests -p "test_candidate_fta_extraction_service.py" -q` | 17 tests，OK | 候选树消费与映射隔离合同 |
| `python -m unittest discover -s evaluation/quality_eval/public_sources -p "test_probe_candidate_fta_raw_source_v1.py" -q` | 10 tests，OK | 新建原文探针记录当前 prompt v4 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v12 -q` | 2 tests，OK | v11 不变、v12 状态/哈希数据账、readiness 边界 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | manifest 校验器和活动 v12 |
| `python -m unittest discover -s backend-python/tests -q` | 266 tests，OK | 完整后端单测；不等于外部模型语义正确或专家 Gold |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v12.py --check --captured-at 2026-09-28` | `current`，134 artifacts，readiness 均 false | 活动 manifest 可重复生成检查 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，134/134 artifact 哈希通过 | 活动 v12 路径和 SHA-256 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0；仅提示仓库既有文件的 LF→CRLF 转换 | 未发现空白错误；未进行 stage/commit |

结论边界：以上是在线复演前的 v4 离线验收快照；当时没有用外部模型重跑 F01681。后续单样本复演与限制条件见下节。没有改正式 Gold、数据库、生产 API、门策略或 `fta_ready` / `production_ready`。

### 2026-09-28 Cause disposition v4：F01681 单样本在线开发复演及只读 AI 复核

在明确授权的一次在线调用范围内，固定语料样本 `SIEMENS_S210_2019_F01681` 使用 DeepSeek Flash 重跑 Cause disposition v4，环境设置 `OPENAI_MAX_RETRIES=0`。流程在没有任何可建树候选时 fail-closed，因此只运行 Fault Extraction 与 Cause Disposition 两阶段，共 2 次成功请求；Structure Decomposition 和 Gate Assessment 未调用。

| 结果项 | 实际结果 | 解释边界 |
| --- | --- | --- |
| 原因处置 | 16/16 为 `relation_only`：1 条顶事件释义摘要、15 条诊断映射 | 本样本未提出任何候选因果边；单样本开发观察，不是总体准确率 |
| 树状态 | `blocked`，`no_fta_event_candidates`；1 个顶事件节点、0 条关系、0 个门 | 阻断符合“摘要/诊断映射不能自动连边”的当前规则；不是建树成功 |
| 证据核验 | 输入文本 SHA-256 与固定语料一致；独立复核账共 71 个引用位置全部精确 | 证明来源/偏移可回查，不证明因果语义是真值 |
| 独立复核 | AI 子智能体只读角色复核 `PASS` | 非刘武签署、非真人领域专家审核、非正式 Gold |

运行与复核 artifact：

- [运行 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.json) · [运行报告](../evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.md)
- [AI 复核 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.json) · [AI 复核报告](../evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.md)

验收命令及结果：

| 命令 | 结果 | 边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v13 -q` | 2 tests，OK | v13 账目、哈希、来源与 readiness 不变性 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | validator 默认活动 v13 manifest |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v13.py --check --captured-at 2026-09-28` | `current`，141 artifacts，readiness 均 false | v13 可重复生成性 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，141/141 artifact 哈希通过 | 活动 v13 全量路径与 SHA-256 |
| `python -m unittest discover -s backend-python/tests -p "test_fta_cause_disposition.py" -q` | 14 tests，OK | v4 语义边界合同回归 |
| `python -m unittest discover -s backend-python/tests -p "test_candidate_fta_extraction_service.py" -q` | 17 tests，OK | 候选树消费、映射隔离与证据合同 |
| `python -m unittest discover -s evaluation/quality_eval/public_sources -p "test_probe_candidate_fta_raw_source_v1.py" -q` | 10 tests，OK | 原文探针和当前 prompt 标识 |
| `python -m unittest discover -s backend-python/tests -q` | 266 tests，OK | 后端完整回归；不等于模型语义准确率或 Gold |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0 | 无空白错误；Git 提示既有文件 LF→CRLF 转换；未 stage/commit |

正式 Gold、数据库、生产 API、门策略均未修改；`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false`。本轮没有提交 Git。

### 2026-09-28 F01681 Remedy `xxxx=9507` 来源范围复核

对固定公开语料中的 F01681 做只读复核：`xxxx=9507` 唯一出现在 Remedy 条件分支，原文引文 `If xxxx = 9507:\nSet synchronous motor.` 精确位于 `[2526,2564)`。该句只支持处理指令，不证明现场原因状态或到顶事件的因果边。因此不追加 cause、不创建 FTA 节点/边；Cause/Fault value 与 Remedy 的范围完整性保留为 `unresolved`。

AI 子智能体只读角色复核与主 agent 的来源核验结论一致；AI 未计算 offset，offset 由主 agent 对固定语料逐字核实。此结果不是真人专家签署，不是 Gold 或因果准确率结论。详细记录见[结构化 JSON](../evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.json)与[审计报告](../evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.md)。Gold、数据库、生产 API 和 readiness 均不变。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v14 -q` | 2 tests，OK | 源文本 SHA、offset、唯一出现次数、AI-only provenance 与 readiness 边界 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | validator 默认活动 v14 |
| `python -m unittest discover -s backend-python/tests -q` | 266 tests，OK | 后端完整回归 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v14.py --check --captured-at 2026-09-28` | `current`，146 artifacts | v14 可重复生成性；readiness 均 false |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，146/146 artifact 哈希通过 | 活动 v14 路径与 SHA-256 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0 | 无空白错误；仅报告既有工作树的 LF→CRLF 提示 |

当时活动 manifest v14 登记了来源复核和该轮文档哈希，现作为历史快照保留；v13 也未覆盖；未执行 Git stage/commit。

### 2026-09-28 已见 FTA 门型案例回归范围审计（manifest v15）

复核 v14 中 36 个已探索案例的 fixture 与测试实现后，确认其离线单测覆盖来源/证据引用、模型输入隔离、响应解析/合同，以及使用确定性测试替身的 probe 汇总；不调用当前模型，也不验证当前模型在这 36 条上的预测。因此将活动 suite 从 `fta_gate_behavior_regression_v1` 重分类为 `fta_gate_contract_boundary_regression_v1`。旧 ID 留在 v14 历史快照中，v14 未覆盖。数据标签、15 个来源簇、Dev 分配和独立 Final 状态未改变；Final 仍 `not_created`。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v15 -q` | 2 tests，OK | manifest 账目、suite 范围、v14 不变性及 readiness |
| `python -m unittest evaluation.quality_eval.public_sources.test_fta_gate_diagram_development_v1 evaluation.quality_eval.public_sources.test_probe_faa_ast_fta_gate_external_v1 evaluation.quality_eval.public_sources.test_probe_multisource_fta_gate_external_v1 evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -q` | 21 tests，OK | fixture、来源隔离、提示/探针合同；不调用当前模型。DOE PDF 读取有既有重复 `/Length` 警告，来源哈希/引文测试仍通过 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | validator 默认活动 v15 与路径/哈希守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v15.py --check --captured-at 2026-09-28` | `current`，150 artifacts | 活动 v15 可重复生成性；`fta_ready=false`、`production_ready=false` |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，150/150 artifact 哈希通过 | 活动 v15 artifact 路径与 SHA-256 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `python .../check_project_guardrails.py ... --truth-dir docs` | 未通过 | 仓库治理脚手架仍缺 `docs/project-initiation.md` 等既定片段；此为既有 adoption/bootstrap 缺口，不属于本次评测口径修订，未改根 AGENTS 或新增项目立项文档 |
| `git diff --check` | 退出码 0 | 无空白错误；Git 对既有 dirty 文件提示 LF→CRLF 转换 |

本次不调用外部模型、不修改 Gold/数据库/生产 API 或 FTA readiness，不 stage/commit。AI 模型实际 36 条预测、独立 Final 和 FTA 整体准确率仍未验证。

### 2026-09-28 FTA scoped readiness report v1（评估层合同；结论未就绪）

用户确认将 `FTA-Structure Ready` 与 `FTA-Quantitative Ready` 放入独立的范围报告/manifest，不增加到单棵 Preview。报告钉定 v15 manifest 字节哈希，逐项记录纳入数据集哈希、18 个来源簇及分配、3 个显式未纳入范围、审核 provenance、评估配置、逐项标准/证据引用/阻塞项。该范围包含 36 条已见 fixture/合同/证据边界回归和 11 条公开图示开发案例，共 47 条/18 个来源簇；它不是完整故障树评估，也不代表当前模型准确率或真人专家审核。

范围结论：`FTA-Structure=blocked`、`FTA-Quantitative=blocked`。原因包括当前模型未在声明范围内运行、范围数据不包含每项完整原文因果结构、独立 Final 未创建、没有真实设备事件概率/失效率及观测窗口/分母、依赖与不确定性传播未验证。六条具名专家逻辑 Gold 单独披露，未混入 47 条分母，且其类别支持不足；AI 角色审核不转写为真人专家审核。全局 `fta_ready=false`、`production_ready=false` 继续保持。

相邻合同复核还发现一项独立的测试覆盖债务：`fta_graph_contract.py` 会拒绝 `dataset_info.fta_ready=true`，但当前专门反例测试显式覆盖了 `production_ready=true`，没有直接断言 `fta_ready=true` 的拒绝。代码守卫存在，本轮不改核心合同/测试；该项已列入 readiness 报告的 `related_non_readiness_gaps`，后续应作为单独的合同回归改动补测。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/build_fta_scoped_readiness_report_v1.py --check --assessed-at 2026-09-28` | `current`，47 cases、18 source clusters | readiness 报告可复现；只读 v15 固定证据，不做模型推理 |
| `python evaluation/quality_eval/fta_readiness_report_v1.py` | `valid`，Structure/Quantitative 均 `blocked` | 校验数据/来源哈希、范围算术、来源分配、证据引用、审核身份和全局不提升约束 |
| `python -m unittest evaluation.quality_eval.test_build_fta_scoped_readiness_report_v1 -q` | 2 tests，OK | 报告范围与 v15 不变性 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_fta_readiness_report_v1.py" -q` | 10 tests，OK | 阻止哈希漂移、来源污染、假专家 provenance 和全局 readiness 提升 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v16 -q` | 2 tests，OK | v16 登记报告，不改 v15，也不升级全局标志 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v16.py --check --captured-at 2026-09-28` | `current`，157 artifacts | v16 可重复生成性；Structure/Quantitative 均 blocked，全局 flag false |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，157/157 artifact 哈希通过 | 活动 v16 路径与 SHA-256 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | 活动 v16 manifest 与路径/哈希守卫 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0 | 无空白错误；仅有既有工作树 LF→CRLF 提示 |

本轮只在 evaluation/docs 层增补报告合同、builder、validator、测试和 manifest；不改 Candidate FTA 树合同、正式 Gold、数据库、API 或生产逻辑。Git 未 stage/commit。报告完成表示 readiness 评估有了可审计载体，不表示 Structure/Quantitative Ready 已达成。

### 2026-09-28 外部完整来源筛选与 v17 活动基线

筛选了 4 份官方 FAA/NASA 整本文档并固定下载件 SHA-256。NASA/CR-2019-220217 与 DOT/FAA/TC-15/62 因本轮已检查代表性树图，归为已见开发/适配来源，不可用于盲测 Final；NASA CR-108289 只适合图结构补充；NASA-TM-105505 实际下载 PDF 不含页面描述中的附录树图，排除。来源筛选记录见 [JSON](../evaluation/quality_eval/runs/fta_independent_final_source_screen_v1_2026-09-28.json)。

合同审查确认当前 Candidate FTA 服务按单条 `FaultRecord` 生成候选树，不支持将一整份系统报告直接作为一棵树评测。因此独立 Final 仍为 0 条/0 来源簇、`not_created`；模型调用未运行。后续需先完成评测专用的顶事件范围包，并把图示参考门型与“输入文本直接证据授权的门型”分开标注；新 Final 必须来自未查看过树图内容的完整新文档。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v17 -v` | 2 tests，OK | 记录 2 份已见开发候选、0 份盲测 Final 合格来源；Final 未创建、全局 readiness 保持 false |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v17.py --check --captured-at 2026-09-28` | `current`，165 artifacts | v17 可复现；4 份已筛来源、Final `not_created` |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，165/165 artifact 哈希通过 | 活动 v17 路径与 SHA-256 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -v` | 6 tests，OK | validator 默认活动 v17 与路径/哈希守卫 |

### 历史验收快照：2026-09-29 单事件 FTA 评测包合同与 v18 活动基线

新增[模型输入包 JSON Schema](../evaluation/quality_eval/schemas/fta_event_scope_input_packet_v1.schema.json)和[参考 Gold JSON Schema](../evaluation/quality_eval/schemas/fta_event_scope_reference_gold_v1.schema.json)。模型只获得单一顶事件和定位到页码/章节的允许原文；来源审计包络与 Gold 标签不进入模型输入。参考 Gold 分别保留图中呈现的门型与限定文本证据授权的门型，并绑定来源文件 SHA-256 与规范化模型输入 SHA-256。`unknown` 必须记录原因；AND/OR 必须带可在输入段中唯一回切的直接证据。跨 artifact 校验检查来源身份、引文唯一性、单一顶事件、图连通与环。v18 截止时 packet=0、reference Gold=0；12 项测试均为合成合同测试，不代表模型效果。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_fta_event_scope_packet_contract -v` | 12 tests，OK | 输入/GOLD隔离、证据唯一、来源哈希、页码、门标签、连通性、审核者身份/日期校验；不调用模型 |
| JSON Schema Draft 2020-12 `check_schema`（两个新 Schema） | 2 schemas valid | 验证 Schema 结构；未创建实际样本 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v18 -q` | 2 tests，OK | v18统计、v17不变性、全局 false 标志 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v18.py --check --captured-at 2026-09-29` | `current`，173 artifacts | v18 可复现，输入包/GOLD 均为0，Final未创建 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，173/173 artifact 哈希通过 | 活动 v18 artifact 路径与 SHA-256 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | validator 默认活动 v18 及路径/哈希守卫 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0 | 未发现空白错误；Git 对既有工作副本报告 LF→CRLF 提示；新建未跟踪文件不在该命令检查范围内，已由 manifest 哈希登记但不代表 whitespace lint |

NASA XVS 仅登记为官方元数据线索；未下载 PDF、未查看树图，权利和来源重叠尚未审计，不作为 Final 来源。本轮不调用模型、不创建 Final Gold、不接生产 API、不写数据库/正式 Gold、不改 readiness，也不 stage/commit。

历史来源筛选记录（2026-09-28，manifest v17）：当轮没有调用模型、生成 Final Gold、修改生产代码/API/数据库或改写已有测试集；没有 stage/commit。外部 PDF 留在 `tmp/pdfs/fta-source-screen-20260928/` 临时目录；当时本机安全策略拦截了删除命令，因此未纳入 Gold 或稳定评测资产，来源记录保留官方 URL 与 SHA-256。

## 2026-09-29 NASA XVS 整篇来源筛查与 v19 活动基线

来源为 [NASA NTRS 20250005835](https://ntrs.nasa.gov/citations/20250005835)。已核对官方元数据、固定下载件 SHA-256，并扫描 PDF 全部40页文本、视觉查看封面、Appendix D 索引及8张树图。正文 FHA 表给出高层 failure conditions，但不足以复现 Appendix D 的完整下层因果分解；图示门型只来自树图符号，不能当作输入原文直接授权的 AND/OR 标签。该来源族已被项目成员查看，状态为 `seen_development_only_not_final`，不可用于独立盲测 Final。1998 前身及关联 CR #29-C19 尚未内容比对，语义重叠审计未完成。

权利筛查仅记录 NTRS Public / Public Use Permitted 元数据，同时保留 PDF 中 NASA Langley STI 流程及其他限制声明；本次只作暂定内部评估判断，不是法律或人工权利审查，也不授权再分发。用户确认模型输入只含按页/章节定位的原文、参考树和 AND/OR Gold 独立隔离；当前尚未从 XVS 创建 packet 或 Gold。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_fta_event_scope_xvs_source_screen evaluation.quality_eval.test_build_fta_baseline_manifest_v19 evaluation.quality_eval.test_build_fta_baseline_manifest_v18 -q` | 6 tests，OK | 来源筛查、v19 builder 与 v18 历史快照不变性 |
| `python -m unittest evaluation.quality_eval.test_fta_event_scope_packet_contract -q` | 12 tests，OK | 输入/GOLD 分离、引用与门证据合同；不调用模型 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | 活动 v19 与路径/哈希守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v19.py --check --captured-at 2026-09-29` | `current`，178 artifacts | v19 可复现；XVS Dev-only；packet=0；Final 未创建；全局 readiness false |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，178/178 哈希通过 | 活动 v19 清单登记文件完整且哈希一致 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库布局门禁 |
| `git diff --check` | 退出码 0 | 无空白错误；Git 提示若干既有 tracked 文件 LF→CRLF；该命令不检查 untracked 文件 |

本轮未创建 packet/Gold、未运行模型、没有准确率结果；未改变正式 Gold、数据库、生产 API 或 readiness，未 stage/commit。v19 是来源审计与活动索引版本，不代表 FTA Structure/Quantitative Ready。

## 2026-09-29 NASA 电池模块 Figure 7 单事件 Dev 样例与 v20

来源： [NASA NTRS 19880001643](https://ntrs.nasa.gov/citations/19880001643)。官方记录元数据将报告列为 Public / Public Use Permitted；此处只记录元数据，非法律审查或再分发许可。固定 PDF SHA-256、页数、来源扫描范围和已见/不可作 Final 的原因见来源筛查 JSON。

本轮新增一条单事件输入包与独立参考图 artifact。输入侧只含顶事件及 Section 5.0 按 PDF 页/印刷页定位的原文；参考侧单独记录 Figure 7 七个图示节点、三个图示 AND/OR 门和文本授权门标签。独立 AI 角色审核指出重复出现的两个 “Single cell explodes” 图形是两个不同节点；“Two module vents clog”是图示专属细节，输入原文仅支持更宽泛的排气口故障。故图示门标签为 OR/AND/AND，而精确范围的文本授权标签为 OR/AND/unknown（第三门 `scope_ambiguity`）。模型输入 projection 的字段集合严格限制为 `event_scope_id`、`top_event`、`source_segments`。该报告及 Figure 7 已被打开，因此整个来源族标为 `seen_development_only`，不能用于盲测 Final；来源族语义重叠审计仍未完成。AI 角色审核不等同人类专家签署。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.public_sources.test_nasa_battery_fig7_event_scope_dev_v1 -v` | 4 tests，OK | 单案例输入与参考图隔离、引用合同、门标签分离、Dev-only 声明；不调用模型 |
| `python -m unittest evaluation.quality_eval.test_fta_event_scope_packet_contract -q` | 12 tests，OK | 共用事件包合同，不调用模型 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v20 -q` | 2 tests，OK | v20 数量、历史 v19 不变性和 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v20.py --check --captured-at 2026-09-29` | `current`，187 artifacts | 活动 manifest 可重复生成 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`，187/187 | 当前活动 artifact 路径与 SHA-256 |
| `python -m unittest evaluation.quality_eval.public_sources.test_nasa_battery_fig7_event_scope_dev_v1 evaluation.quality_eval.test_fta_event_scope_packet_contract evaluation.quality_eval.test_build_fta_baseline_manifest_v20 evaluation.quality_eval.test_build_fta_baseline_manifest_v19 evaluation.quality_eval.test_build_fta_baseline_manifest_v18 -q` | 22 tests，OK | 当前开发样例及 v18/v19 不变快照合同回归；不调用模型 |
| `python -m unittest discover -s evaluation/quality_eval -p "test_validate_fta_baseline_manifest.py" -q` | 6 tests，OK | 默认活动 v20 与路径/哈希拒绝逻辑 |
| `python scripts/verify_repo_layout.py` | `repository layout verified` | 仓库目录约束 |
| `git diff --check` | 退出码 0 | 无空白错误；Git 报告的是既有 CRLF/LF 转换提示 |

截至 v20 快照时模型 inference 尚未运行，因此当时没有模型效果/准确率结果。该历史句不代表当前状态；后续 v24 登记 v3 单次模型运行，v25 增加了不计分的定性对照。独立 Final=0；未改正式 Gold、数据库、生产 API；`fta_ready=false`、`production_ready=false`。v20 来源为已见开发样例，不是独立泛化证明。

## 2026-09-29 Figure 7 v3 受控请求：单变量在线对照已完成

v3 请求器以 v2 为对照，只改变 DeepSeek thinking mode：从默认状态显式改为 `disabled`；保持模型别名、输入投影、提示、temperature、8192 `max_tokens` 与 `json_object` 不变，实际发出 1 次请求且 SDK 重试为 0。用户报告本地凭证已更新。响应 `finish_reason=stop`，正文长度 2450 字符、严格 JSON 可解析；推理字段不存在，API 未返回 reasoning token 数，推理文本未持久化。结构/证据评估为 5 个节点、3 个门范围、8 条引用全部有效、无结构错误。

安全记录：此前一次本地配置诊断曾意外将旧 provider Key 打印到工具输出；本轮未读取、输出或保存密钥。用户报告已更新本地凭证后，v3 使用配置中的凭证完成单次调用。thinking-disabled 仅在这一个已见 Dev 样例上与可用响应同时出现；不能据此断定普遍根因或模型性能提升。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_run_fta_event_scope_model_v3 -v` | 8 tests，OK | 单变量请求设置、响应诊断、推理文本不落盘、空内容分类、异常结构 fail-closed、凭证与仓库外产物路径守卫；使用 mock，不联网 |
| `python -m unittest evaluation.quality_eval.test_run_fta_event_scope_model_v2 -v` | 4 tests，OK | v2 历史 runner 回归未变 |
| `python -m unittest evaluation.quality_eval.public_sources.test_nasa_battery_fig7_event_scope_dev_v1 -v` | 4 tests，OK | 输入/GOLD 隔离、开发样本边界和来源合同未回归 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v24 -v` | 2 tests，OK | v24 只记录已完成的单次对照；不提升 Gold 或 readiness |
| `python -m unittest test_validate_fta_baseline_manifest -v`（在 `evaluation/quality_eval` 目录运行） | 6 tests，OK | 校验哈希、路径边界及活动 manifest v24 |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py --preflight` | 退出码 0 | 输入投影、prompt SHA、provider/model 锁、8192 预算、JSON mode 与 thinking disabled；无请求，仅显示凭证是否配置，不显示凭证内容 |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v3.py --confirm-credential-rotated` | 1 request，0 retries；`finish_reason=stop`；JSON parsed | 单变量在线对照；5 nodes、3 gate scopes、8/8 quotes valid、0 structural errors；Gold comparison 未运行 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v24.py --check --captured-at 2026-09-29` | current；213 artifacts | v24 可重复生成，登记 v3 运行及当前文件哈希 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | 213/213 hashes valid | 默认验证活动 manifest v24 |

本轮只完成输出可用性、结构和引文回指检查；没有与参考 Gold 比较，也不宣称语义/逻辑门正确性、准确率或校准结果。NASA Figure 7 仍为已见 Development 样例；独立 Final 未创建，正式 Gold、数据库、生产 API 与 readiness 未改变。

## 2026-09-29 Figure 7 v3 离线定性对照与活动基线 v25

这一步仅将已保存的 v3 模型输出与隔离保存的 `text_gate_reviews` 做离线定性对照；没有重新调用模型，没有把图示门型当作文本金标，没有修改 Gold，也不生成准确率/F1/校准数字。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py` | 已生成 JSON + Markdown 定性对照 | 固定已见 Dev 单例；核对 packet/hash、节点/门作用域和原文引文；不计分 |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_model_run_v3_dev -v` | 3 tests，OK | 保护文本授权标签与图示标签分离、语义不通过结论及 readiness 不提升 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v25 -v` | 2 tests，OK | v25 登记定性不通过，不改 v24 历史快照或 readiness |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v25.py --check --captured-at 2026-09-29` | current；219 artifacts | v25 可重现生成 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；219/219 hashes | 默认校验活动 manifest v25 的路径与 SHA-256 |

结论：根顶事件文字对齐、顶层 OR 标签对齐，但根门直接子项没有表达两个复合分支；次生爆炸分支模型输出 `unknown`，参考文本授权标签为 AND，且“模块正常运行”未作为单独节点；结构失效参考范围保持 `unknown/scope_ambiguity`，模型的 `unknown` 却绑定到了“单体爆炸”节点，不能视为作用域命中。模型虽然 8/8 引文逐字出现在输入中，但这不证明引文蕴含整个节点语义或树拓扑。完整发现见[定性对照报告](../evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.md)与[JSON](../evaluation/quality_eval/runs/fta_event_scope_model_run_v3_dev_comparison_2026-09-29.json)。该参考审核为 AI 角色审核，不是人类专家 Gold；这个单样例只支持错误分析，不支持泛化或模型准确率结论。`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-09-29 单事件树层级合同 v1 与活动基线 v26

规则：gate scopes 是唯一父子层级来源。`parent_id` 若存在只与推导出的父节点作一致性校验；不一致时阻断该树、保留原始模型输出，禁止自动修复。合同另检查唯一顶事件、门作用域直接子项数量、单父关系、可达性、环、输出 scope 唯一性及 `structure_status`。新版评测 prompt 已建立但**没有提交模型运行**；本阶段只离线复核保存的 v3 输出，不改生产服务、Gold、数据库或 readiness。

真实已保存 v3 输出被合同判为 blocked，含 6 个 blocker：旧输出缺少新版要求的 `structure_status`、S2/S3 各只有一个 child、E3 有多个父 scope、E3/E4 的 `parent_id` 与 gate scopes 不一致。原 JSON 没有被改写。一个合成 OR→(AND, AND) 嵌套正例通过；刻意冲突 `parent_id` 的反例被阻断且原字段仍保持错误值，以证明不自动修补。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py` | 已生成更新后的 JSON + Markdown | 对保存的 Dev 输出离线执行合同；无模型调用 |
| `python -m unittest evaluation.quality_eval.test_event_scope_tree_contract evaluation.quality_eval.test_compare_fta_event_scope_model_run_v3_dev evaluation.quality_eval.test_build_fta_baseline_manifest_v26 -v` | 15 tests，OK | 合法嵌套正例、真实 v3 负例、冲突不修复、环、畸形标识、报告与 manifest 边界 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v26.py --captured-at 2026-09-29` | 已生成 manifest v26；225 artifacts | 从冻结 v25 派生、登记结构合同/评测 prompt/报告/验收文档并重算 SHA-256 |
| `python evaluation/quality_eval/compare_fta_event_scope_model_run_v3_dev.py --check` | current；6 findings | 比较报告与当前代码生成内容一致；仍不计分 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v26.py --check --captured-at 2026-09-29` | current；225 artifacts | 活动研究基线可确定性重现 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；225/225 hashes | 当前登记路径存在且哈希匹配 |
| `python -m unittest test_validate_fta_baseline_manifest -v`（在 `evaluation/quality_eval` 目录运行） | 6 tests，OK | 包括 active v26 快照、哈希变化、重复 ID、缺失文件及路径逃逸拒绝 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 仓库目录边界未受影响 |
| `git diff --check` | exit 0 | 无空白错误；Git 对现有 dirty tracked 文件显示 LF/CRLF 转换提示 |

不代表模型语义准确率、门型正确率或泛化成绩。生产 FTA 路径没有变化，`fta_ready=false`、`production_ready=false`。

## 2026-09-29 事件范围评测 prompt/runner v4（历史快照：请求前，manifest v27）

本段只记录 v27 生成时的请求前状态，不代表当前状态。v4 是评测专用隔离入口，不接生产 Candidate FTA，不读取/提交参考 Gold，不覆盖 v3 原始运行。输出合同要求节点和门作用域证据标出输入 `segment_id`；区分结构 scope 引文与 AND/OR 直接逻辑引文；Unknown 门只允许无逻辑引文并带结构化 reason。层级冲突 fail-closed，不自动修复。请求固定 `deepseek-flash`、`api.deepseek.com`、thinking disabled、JSON mode、8192 max tokens、120 秒超时、SDK retry 0；每次调用必须明确授权，运行收据与独占产物路径阻止意外重跑。在线单次运行及结果见本文件顶部“v4 单次模型运行与离线复核”当前记录。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_event_scope_tree_contract evaluation.quality_eval.test_compare_fta_event_scope_model_run_v3_dev evaluation.quality_eval.test_run_fta_event_scope_model_v4 evaluation.quality_eval.test_build_fta_baseline_manifest_v27 -v` | 22 tests，OK | 层级合同、原始结果不修复、严格输出/段落证据定位、Unknown 门、mock 请求仅一次/零重试、thinking disabled、不写 reasoning |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py --preflight` | `live_request_performed=false`；prompt SHA `a1d532cd253c2ca4ab7deb4ba71740d76b862c369a8278d4c84573e762c4a3e2` | 输入为校验过的 model_input 投影且不含 Gold；显示 endpoint/model，不显示密钥，不发请求 |
| `python -m compileall -q evaluation/quality_eval/event_scope_tree_prompt_v4.py evaluation/quality_eval/public_sources/run_fta_event_scope_model_v4.py evaluation/quality_eval/test_run_fta_event_scope_model_v4.py evaluation/quality_eval/build_fta_baseline_manifest_v27.py` | 退出码 0 | 仅语法/字节码编译检查，不等于在线推理 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v27.py --captured-at 2026-09-29` | 已生成 manifest v27；231 artifacts | 从冻结 v26 派生并登记 v4 prompt、runner、mock tests 与当前文档；在线请求状态 not_run，readiness false |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v27.py --check --captured-at 2026-09-29` | current；231 artifacts | 可重复构建检查；请求数为 0，FTA/production readiness 均 false |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；231/231 hashes | 默认校验 active v27 路径与 SHA-256 |
| `python -m unittest test_validate_fta_baseline_manifest -v`（在 `evaluation/quality_eval` 目录运行） | 6 tests，OK | 包括 active v27 快照、哈希变化、重复 ID、缺失文件及路径逃逸拒绝 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 仓库目录边界未受影响 |
| `git diff --check` | exit 0 | 无 whitespace errors；Git 对已有 dirty tracked files 给出 LF/CRLF 转换提示 |

本段记录不代表模型语义准确率、门型正确率或泛化成绩；生产 FTA 路径、Gold、数据库和 readiness 均未变化。

## 2026-09-29 事件范围语义 smoke 输入与 one-shot runner（v37；离线预检）

本组样例只验证 prompt v8 对隐含语义门型及常见误判边界的单次行为，不是真实手册数据、专家 Gold、准确率或泛化测试。5 条输入位于 `fta_event_scope_semantic_smoke_inputs_v1.json`；预期标签位于独立的 `fta_event_scope_semantic_smoke_reference_v1.json`，runner 不读取参考文件。在线运行需要对具体 case 重新明确授权；单次请求最多 1 次、SDK retries=0，保留原始响应，失败不自动修复或重试。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v37 -v` | 14 tests，OK | 输入/标签隔离、隐含语义 OR/AND 与未知边界、单次请求授权、零重试/不修复、原始响应保留、v37 状态与 readiness 守卫；无外部模型调用 |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-001 --preflight`（SMOKE-002…005 同样执行） | 5/5 预检成功；均显示 `live_request_performed=false`、`reference_labels_loaded=false`，使用锁定 provider/model 配置 | 逐条预检请求元数据；无模型请求，不输出密钥，不加载参考标签 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v37.py --captured-at 2026-09-29` | 已生成 v37；297 artifacts | 从不可变 v36 派生 v37，登记输入、分离标签、runner、测试、文档和哈希；live request 仍为 false |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v37.py --check --captured-at 2026-09-29` | `current`；297 artifacts；`preflight_ready_not_run`；请求未执行；readiness false | 确定性复现检查 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`；297/297 hashes | 默认验证活动 v37 manifest 注册工件路径与 SHA-256 |
| `python -m unittest evaluation.quality_eval.test_validate_fta_baseline_manifest evaluation.quality_eval.test_build_fta_baseline_manifest_v37 -v` | 9 tests，OK | 校验活动 v37、哈希变化、重复 ID、缺失文件及路径逃逸拒绝 |
| `python -m compileall -q evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py evaluation/quality_eval/test_run_fta_event_scope_semantic_smoke_v1.py evaluation/quality_eval/build_fta_baseline_manifest_v37.py evaluation/quality_eval/test_build_fta_baseline_manifest_v37.py evaluation/quality_eval/validate_fta_baseline_manifest.py` | 退出码 0 | 语法/字节码检查；不代表在线模型效果 |

以上均为离线验证；未调用在线模型，未写 Gold、数据库或生产 API。`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-09-29 SMOKE-001 单次模型运行及离线对照（v38；合成非 Gold）

本节为 manifest v38 的历史快照；其中“其余 4 条未调用”仅描述 v38 当时状态。SMOKE-002 后续结果见文末 v39 记录。

用户对 SMOKE-001 明确授权一次调用。输入只含顶事件和原文段落，不含预期标签；请求 1 次、SDK retries=0、thinking disabled。模型输出隐含语义 OR，严格 JSON 解析成功；结构合同通过，5/5 引文位置有效。响应保存后，离线比较器才读取分离的政策预期，Observed OR 与 Expected OR 匹配。预期标签未经专家审核，故不报告 accuracy、calibration 或泛化；其余 4 条样例未调用。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-001 --authorize-single-request` | `response_received`；1 request、0 retries；`finish_reason=stop`；strict JSON parsed | 已授权的单次外部请求；输入不含参考标签；保存原始响应、机械评估和 attempt receipt |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py --case-id SMOKE-001` | Observed OR = Expected OR；逻辑证据精确匹配决定句；结构有效、5/5 证据位置有效；无 accuracy/calibration claim | 只离线比较已保存输出与分离的非 Gold 政策预期，不发请求、不产生准确率结论 |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v1 evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v38 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 22 tests，OK | 输出/参考分离、单请求及零重试合同、比较拒绝边界、v38 与 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v38.py --captured-at 2026-09-29` | 已生成 v38；306 artifacts | 从不可变 v37 派生 v38，登记单次结果及 hashes；语义 acceptance/readiness 保持 false |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v38.py --check --captured-at 2026-09-29` | `current`；306 artifacts；仅 SMOKE-001 已完成；语义 acceptance/readiness false | 确定性复现检查 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`；306/306 hashes | 默认校验活动 v38 的全部 artifact 路径及 SHA-256 |

本次没有调用 SMOKE-002…005，没有写 Gold、数据库或生产 API。`event_scope_prompt_v8_semantic_acceptance=false`、`fta_ready=false`、`production_ready=false`。

## 2026-09-29 SMOKE-002 隐含 AND 单次模型运行及离线对照（v39；合成非 Gold）

用户对 SMOKE-002 单独授权一次调用。输入只含顶事件和原文段落，不含预期标签；请求 1 次、SDK retries=0、thinking disabled。原文没有字面 AND，模型输出两个共同必要条件并以 AND 连接；严格 JSON 解析成功，结构合同通过，5/5 引文位置有效。响应保存后，离线比较器才读取隔离的编写者政策预期，Observed AND 与 Expected AND 匹配。该预期未经过专家审核，因此不报告 accuracy、calibration 或泛化。SMOKE-003…005 未调用。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-002 --authorize-single-request` | `response_received`；1 request、0 retries；`finish_reason=stop`；strict JSON parsed | 已授权的单次外部请求；输入不含参考标签；保存原始响应、机械评估和 attempt receipt |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py --case-id SMOKE-002` | Observed AND = Expected AND；决定句作为 logic evidence；结构有效、5/5 证据位置有效；无 accuracy/calibration claim | 只离线比较已保存输出与分离的非 Gold 政策预期，不发请求、不产生准确率结论 |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v1 evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v39 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 23 tests，OK | 输出/参考分离、两条已保存结果各自的非 Gold 对照、单请求及零重试合同、v39 与 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v39.py --check --captured-at 2026-09-29` | current；313 artifacts；SMOKE-001/002 完成，003–005 未运行；readiness false | v39 可重现生成；记录两条定性观察且 readiness false |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；313/313 hashes | 默认校验活动 v39 的全部 artifact 路径与 SHA-256 |
| `python -m compileall -q evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v1.py evaluation/quality_eval/build_fta_baseline_manifest_v39.py evaluation/quality_eval/test_build_fta_baseline_manifest_v39.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码 0 | 语法/字节码检查，不代表模型语义验收 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 项目目录边界检查通过 |
| `git diff --check` | 退出码 0 | 无 whitespace errors；Git 对部分已有 dirty 文件提示 LF/CRLF 转换 |

本次未写 Gold、数据库或生产 API。`event_scope_prompt_v8_semantic_acceptance=false`、`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-09-29 SMOKE-003 unknown 单次运行与比较器 v2 合同修正（v40；合成非 Gold）

用户明确授权 SMOKE-003 一次请求。模型收到无标签输入，单次请求、零重试，输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`；严格 JSON 解析、结构合同及 5/5 引文位置检查通过。首次比较用 v1 得到 `requires_review`，因为它错误地要求 unknown 门也必须把逻辑引文与决定句逐字匹配。prompt 已规定 unknown 不提供逻辑引文、而提供原因码，因此新增 v2 离线比较器，按门类型区分合同；未改模型响应、输入或预期标签。v2 对照符合编写者非 Gold 预期。原始运行和 v1 诊断均保留，v2 结果另存。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-003 --authorize-single-request` | `response_received`；1 request、0 retries；`finish_reason=stop`；strict JSON parsed | 针对 SMOKE-003 的单次明确授权；请求不含预期标签；没有自动重试或修复 |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v1.py --case-id SMOKE-003` | `requires_review`；预期/观察门型均 unknown，但 v1 逻辑引文精确匹配为 false | 保留为比较器 v1 诊断，不将 unknown 的无逻辑引文误作模型失败结论 |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py --case-id SMOKE-003` | `matched_authored_policy_expectation_not_expert_validation`；unknown 合同有效、原因码 `no_direct_logic_evidence`；5/5 引文位置有效 | v2 对 AND/OR 要求直接逻辑引文；对 unknown 检查逻辑引文为空及允许的原因码；纯离线，不发模型请求 |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v2 evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v1 evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v40 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 27 tests，OK | 比较器 v2 已知/unknown 分支、失败边界、三条已保存观察、单次请求合同、v40 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v40.py --check --captured-at 2026-09-29` | current；323 artifacts；001–003 完成、004/005 未运行；readiness false | v40 可重现；Gold/准确率/语义接受/readiness 不提升 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；323/323 hashes | 默认校验活动 v40 全部 artifact 路径与 SHA-256 |
| `python -m compileall -q evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/build_fta_baseline_manifest_v40.py evaluation/quality_eval/test_build_fta_baseline_manifest_v40.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码 0 | 语法/字节码检查，不代表模型语义验收 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 项目目录边界检查 |
| `git diff --check` | 退出码 0 | 无 whitespace errors；Git 对部分已有 dirty 文件提示 LF/CRLF 转换 |

v2 是评估器合同修正，不是 Gold 修订、模型重跑、专家验收或准确率提升。SMOKE-004/005 未调用，正式 Gold、数据库及生产 API 未变化，`event_scope_prompt_v8_semantic_acceptance=false`、`fta_ready=false`、`production_ready=false`。

## 2026-09-29 SMOKE-004 事件共现边界单次运行（v41；合成非 Gold）

用户对 SMOKE-004 明确授权一次请求。输入只包含顶事件和原文段落，不含预期标签；请求 1 次、SDK retries=0、thinking disabled。原文记录压力和温度在储罐破裂前都曾升高，同时明确表示报告没有断定两者都必需或任一单独充分。模型保留两个候选子事件，门型输出 `unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。严格 JSON 和树结构合同通过，4/4 引文位置有效。离线 v2 比较与隔离的编写者非 Gold 预期相符；这不是专家语义验收、准确率或泛化结果。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-004 --authorize-single-request` | `response_received`；1 request、0 retries；`finish_reason=stop`；strict JSON parsed | 针对单个样例的明确授权；请求不含参考标签；原始响应、assessment、attempt receipt 均保留 |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py --case-id SMOKE-004` | `matched_authored_policy_expectation_not_expert_validation`；Observed `unknown`；unknown 合同有效；4/4 引文位置有效 | 只离线比较已保存输出与隔离的非 Gold 政策预期，不发模型请求，不产生准确率结论 |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v2 evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v1 evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v41 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 28 tests，OK | 比较器 known/unknown 分支、单次请求保护、SMOKE-004 保存结果、v41 manifest 与 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v41.py --captured-at 2026-09-29` | 已生成 manifest v41；330 artifacts | 从不可变 v40 派生；记录 4 条合成观察，SMOKE-005 未运行；语义接受和 readiness 不提升 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v41.py --check --captured-at 2026-09-29` | current；330 artifacts；SMOKE-001…004 完成、SMOKE-005 未运行 | 检查活动基线确定性可重建 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；330/330 hashes | 默认校验活动 v41 注册工件路径与 SHA-256 |
| `python -m compileall -q evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/build_fta_baseline_manifest_v41.py evaluation/quality_eval/test_build_fta_baseline_manifest_v41.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码 0 | 语法/字节码检查；不代表在线模型语义正确 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 检查仓库目录边界 |
| `git diff --check` | 退出码 0 | 无 whitespace errors；Git 对原有 dirty tracked 文件提示 LF/CRLF 转换 |

SMOKE-004 展示的行为边界是：同一事件记录里的共现不自动证明 AND，也不证明 OR；只有能支持组合关系的证据才允许判已知门。此结果来自合成输入与编写者预期，不证明真实来源语义正确。未改 Gold、数据库、生产 API 或模型策略；SMOKE-005 未调用，`event_scope_prompt_v8_semantic_acceptance=false`、`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-09-29 SMOKE-005 无关词面 OR 与结构阻断（v42；合成非 Gold）

用户对 SMOKE-005 明确授权一次请求。输入只包含顶事件和原文段落，不含预期标签；请求 1 次、SDK retries=0、thinking disabled。原文记录 alarms A/B 同时出现，但没有说明它们是否导致泵停机或是否共同必要；随后提到面板可显示 red or amber，并明确这是独立的显示选择。模型没有将此处字面 `or` 用作泵停机的逻辑证据，输出 `gate=unknown`、`logic_evidence=null`、`unknown_reason=no_direct_logic_evidence`。但它把两个 alarm 合并成一个 child，形成单子项 gate scope；结构合同报 `gate_scope_requires_at_least_two_children`，因此结果被阻断。3/3 引文位置有效只证明引用片段存在于输入，不证明树结构或语义正确。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-005 --preflight` | `live_request_performed=false`；参考标签未加载；请求上限 1、SDK retries=0 | 离线确认模型输入、提示版本与请求设置；不发请求 |
| `python evaluation/quality_eval/public_sources/run_fta_event_scope_semantic_smoke_v1.py --case-id SMOKE-005 --authorize-single-request` | `response_received`；1 request、0 retries；strict JSON parsed；assessment `blocked` | 该样例的明确一次授权；原始结果/assessment/attempt receipt 已保存；不自动修复或重试 |
| `python evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py --case-id SMOKE-005` | 退出码 1，比较状态 `requires_review`；expected/observed `unknown` 相同；unknown 合同有效；结构无效（单 child）；3/3 引文位置有效 | 非零码表示比较器按设计报告整体未通过；离线比较不发模型请求。门型一致不能抵消结构 blocker |
| `python -m unittest evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v2 evaluation.quality_eval.test_compare_fta_event_scope_semantic_smoke_run_v1 evaluation.quality_eval.test_run_fta_event_scope_semantic_smoke_v1 evaluation.quality_eval.test_event_scope_tree_prompt_v8 evaluation.quality_eval.test_build_fta_baseline_manifest_v42 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 29 tests，OK | known/unknown 比较规则、SMOKE-005 门型与结构分别判定、单次请求合同、v42 与 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v42.py --captured-at 2026-09-29` | 已生成 manifest v42；337 artifacts | 从不可变 v41 派生，记录四条整体符合政策预期及一条门型匹配但结构阻断；readiness 不提升 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v42.py --check --captured-at 2026-09-29` | current；337 artifacts；五条均已请求；结构阻断 1；readiness false | 检查活动基线可确定性重建 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；337/337 hashes | 默认校验活动 v42 注册工件路径与 SHA-256 |
| `python -m compileall -q evaluation/quality_eval/compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/test_compare_fta_event_scope_semantic_smoke_run_v2.py evaluation/quality_eval/build_fta_baseline_manifest_v42.py evaluation/quality_eval/test_build_fta_baseline_manifest_v42.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码 0 | 语法/字节码检查；不代表模型语义正确 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 检查仓库目录边界 |
| `git diff --check` | 退出码 0 | 无 whitespace errors；Git 对原有 dirty tracked 文件提示 LF/CRLF 转换 |

SMOKE-005 的窄结论是：模型在该合成输入上忽略了不相关的词面 `or`，但没有形成合同有效的树结构，因此整例为 `requires_review`，不能列为 smoke 通过。未修复原始输出、未重试、未写 Gold/数据库/生产 API；语义接受、`fta_ready`、`production_ready` 均保持 false。该样例已经用掉单次授权，不得再次请求，除非用户另行明确授权。

## 2026-09-29：生产候选 FTA 观察与门型语义提示（v43；离线）

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_recursive_candidate_fta_extraction_service -v` | 27 tests，OK | 验证提示边界与递归候选结构回归；不证明真实模型语义准确 |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v43 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 8 tests，OK | 验证活动 v43 清单、哈希与 readiness 守卫 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v43.py --captured-at 2026-09-29` | 已生成 v43；340 artifacts | 从 v42 快照派生；不调用模型、不修改 Gold/数据库/生产 API |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v43.py --check --captured-at 2026-09-29` | current；340 artifacts；无模型请求；readiness false | 检查活动基线可确定性重建 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；340/340 hashes | 默认校验活动 v43 注册工件路径与 SHA-256 |

本轮生产提示明确两条规则：共同出现、同时记录、顺序出现或并列列举不能证明观察节点与顶事件的因果关系；有证据但无因果连接的节点必须保留并阻断整树。门型可基于语义判断，不要求原文出现 `AND/OR` 字样，但必须由原文直接支持替代路径/联合必要关系和同一 output，否则保持 `unknown`。SMOKE-005 历史运行不重跑、不自动修复。`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-09-29：合成观察的在线边界发现与 detached-observation 合同（v44）

受控运行使用一条合成原文：报警 A/B 在泵停机前被记录，原文明示没有说明任一报警导致停机或二者共同必要，另有无关的 `red or amber` 显示选择。只授权并执行了 1 次模型请求，SDK/外层重试均为 0。模型没有把无关 `or` 当作泵停机逻辑，也没有产生因果边；但它把 A/B 分类为 `state + relation_only`。旧服务因此提前返回，仅保留 ledger，没有按用户确认的边界保留两个独立断开观察节点。结果为 `policy_boundary_match=false`，树为 blocked（`no_fta_event_candidates`）。这次运行确认了真实实现缺口，不是通过样例。

命令 `python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --authorize-single-run` 已用掉单次授权。模型响应已原样保存在 JSON；首次 Markdown 渲染因报告字段路径错误中断，之后仅用 `--render-existing` 从保存响应恢复 Markdown，没有重发请求或改写响应。复核发现模型给出的 `state + relation_only + descriptive_association` 已表达“描述性关联、无因果边”，缺口在宿主把它只留 ledger。现加入窄规范化：仅当这三个标签同时匹配且证据唯一绑定时，宿主最终处置规范化为 `detached_observation`，保留原 `proposed_disposition=relation_only` 与 provenance；模型原始响应不改。已将该保存响应离线重放，结果为两个分别有精确证据的断开观察节点、无门/关系、整树 blocked。修订提示尚未重新在线验证。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --authorize-single-run` | 1 request、0 SDK retries、0 outer retries；模型答复已保存；观察节点数 0；`policy_boundary_match=false` | 单次合成探测；不读取 Gold，不写 DB/API；该响应证明修复前行为不符合要求，不作为准确率成绩 |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --render-existing` | `report_rendered_from_preserved_response`；0 model request；原始响应未修改 | 只从保存的 JSON 生成 Markdown 报告 |
| `python -m unittest backend-python.tests.test_fta_cause_disposition backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_recursive_candidate_fta_extraction_service backend-python.tests.test_openai_model_client evaluation.quality_eval.public_sources.test_probe_candidate_fta_observation_boundary_v1 -v` | 52 tests，OK | 覆盖 detached 分类、窄宿主规范化、保存响应离线重放、证据绑定、断开节点、禁止 gate/relation 连接与零重试配置；不证明新提示在线语义表现 |
| `python -m compileall -q backend-python/core/openai_model_client.py backend-python/contracts/fta_cause_disposition_contract.py backend-python/contracts/candidate_fta_contract.py backend-python/fta/cause_disposition_service.py backend-python/fta/candidate_fta_extraction_service.py evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py evaluation/quality_eval/build_fta_baseline_manifest_v44.py evaluation/quality_eval/test_build_fta_baseline_manifest_v44.py` | 退出码 0 | 语法检查 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v44.py --captured-at 2026-09-29` / `--check --captured-at 2026-09-29` | `written`，随后 `current`；349 artifacts | 从 v43 派生 v44；记录 pre-fix 失败、窄宿主规范化及保存响应离线重放，不提升 readiness |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v44 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 8 tests，OK | 校验 manifest 账目、活动快照、离线重放状态与文件哈希 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | `valid`；349/349 | 校验活动 v44 注册 artifacts 的路径与 SHA-256 |

未修改 Gold、数据库或生产 API。修订合同已通过对既有原始模型响应的离线重放，仍待一次新的在线模型验证；此前单次在线授权已经消费，不会自动重跑。该合成案例不是专家 Gold、模型准确率或泛化验证。`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-10-07：因果/门型状态台账对账与 v45 基线（离线）

本轮把不同来源、不同审核粒度的状态分开登记：具名专家因果 Gold、具名专家 AND/OR Gold、AI 角色批次事件/原因审核、AI 事件 scope 审核、AI 门节点审核，以及 AI provisional 视图。各轨迹分母不能相加；AI 角色标签不升级为真人专家 Gold，provisional 视图也不作为新增独立样本。正式 Gold、数据库和生产 API 未改。

原因语义分类没有新增平行 taxonomy：现有 disposition contract 已区分 `causal_condition`、`diagnostic_mapping`、`fault_value_mode`、`consequence`、`state`、`causal_summary`、`remedy`、`other` 和 `mixed_unresolved`，并由 disposition/evidence 合同控制树准入。离线回归覆盖该合同；本轮未改语义 owner。

| 命令 | 结果 | 验收边界 |
| --- | --- | --- |
| `python -m unittest backend-python.tests.test_fta_cause_disposition backend-python.tests.test_candidate_fta_extraction_service backend-python.tests.test_recursive_candidate_fta_extraction_service backend-python.tests.test_openai_model_client evaluation.quality_eval.public_sources.test_probe_candidate_fta_observation_boundary_v1 evaluation.quality_eval.test_build_fta_baseline_manifest_v44 evaluation.quality_eval.test_build_fta_baseline_manifest_v45 evaluation.quality_eval.test_validate_fta_baseline_manifest -v` | 64 tests，OK | 离线合同、递归提取、零重试/保存响应重放、v44 不可变性及 v45 对账清单测试；不代表新模型语义准确率 |
| `python -m compileall -q backend-python/contracts/fta_cause_disposition_contract.py backend-python/fta/cause_disposition_service.py backend-python/tests/test_fta_cause_disposition.py evaluation/quality_eval/build_fta_baseline_manifest_v45.py evaluation/quality_eval/test_build_fta_baseline_manifest_v45.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码 0 | Python 语法/字节码检查 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v45.py --check --captured-at 2026-10-07` | current；357 artifacts；readiness false | v45 从固定哈希的 v44 派生、确定性重建；Gold 与审核原件不改 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；357/357 hashes | 校验活动 v45 清单注册的路径与 SHA-256 |
| `git diff --check` | 退出码 0 | 没有 whitespace errors；Git 对部分既有工作区文件发出 LF/CRLF 转换提示，不清理或提交这些文件 |

本轮没有新的在线模型请求；修订提示在线验证仍待单独明确授权。该待办不影响本轮离线台账对账，但不能据此宣称新提示已通过真实模型语义验证。`fta_ready=false`、`production_ready=false` 保持不变。

## 2026-10-07：当前完成度与后续执行计划（v46；文档/清单）

沿用`docs/fta-validation-reliability-plan-v1.md`作为唯一执行计划，新增当前完成度、P0～P7依赖、owner、产物、验收指标和停止条件；早期过程保留为历史。v46从固定SHA-256的v45派生，审核分账与readiness不变。本轮只调整文档、清单生成/默认校验入口，不修改FTA业务代码、Gold、数据库或生产API。

| 命令/检查 | 本轮结果 | 证明范围 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.test_build_fta_baseline_manifest_v45 evaluation.quality_eval.test_validate_fta_baseline_manifest` | 10 tests，OK | 分账、父快照保护、当前manifest完整性与失效边界；未重新宣称模型质量通过 |
| `python evaluation/quality_eval/build_fta_baseline_manifest_v46.py --check --captured-at 2026-10-07` | current；359 artifacts；readiness false | 新文档与计划可确定性登记 |
| `python evaluation/quality_eval/validate_fta_baseline_manifest.py` | valid；359/359 | 活动v46工件哈希完整性 |
| `python -m compileall -q evaluation/quality_eval/build_fta_baseline_manifest_v46.py evaluation/quality_eval/validate_fta_baseline_manifest.py evaluation/quality_eval/test_validate_fta_baseline_manifest.py` | 退出码0 | 清单工具语法检查 |
| `python scripts/verify_repo_layout.py` | repository layout verified | 目录边界仍有效 |
| 四份变更文档的本地Markdown链接扫描 | 全部目标存在 | 计划、索引、当前状态与候选FTA说明可导航 |
| v45固定哈希与审核分账比对 | SHA-256仍为`152736cb9acd69f2ddde7db530324c630800cf7b952ac1119d86180e4114d27d`；审核范围/来源不变 | 旧快照未改，未增加审核量或升级provenance |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --preflight --output evaluation/quality_eval/runs/candidate_fta_observation_boundary_v2_2026-10-07.json` | preflight_only；0模型请求；输出路径可用；planned calls=3，SDK/外层重试=0；Gold未加载 | 发现运行上界仍为3，P1须先落实1请求门禁；本次不是在线复验 |
| 工作流治理检查`--truth-dir docs --mode adoption` | FAIL：根AGENTS缺4段固定规范片段 | 改动前已存在的治理债务；本轮不改agent宪法。默认bootstrap检查还要求立项文件，当前成熟项目采用adoption口径 |

当前仍是“候选FTA工程合同已成立，模型语义/独立可靠性验收待完成”。本计划交付不代表P1～P7执行完成；没有新模型准确率、正式Gold更新、数据库写入或生产就绪结论。工作区已有大量未跟踪/未提交内容，staged为0，本轮不提交或推送。

## 2026-10-07：观察边界runner单请求预算门禁（P1离线）

将观察专用runner的真实provider调用预算从3收紧为1。预算外的结构阶段请求在委托provider之前被拒绝，失败类型为`model_request_budget_exceeded`，stage为`structure_decomposition`，运行结果应为`blocked`；首个原因处置阶段的原始响应及SHA-256仍保存在运行artifact中，不自动修复、不重试。此变更只作用于评测runner，没有改生产Candidate FTA多阶段服务。

| 命令 | 结果 | 证明范围 |
| --- | --- | --- |
| `python -m unittest evaluation.quality_eval.public_sources.test_probe_candidate_fta_observation_boundary_v1 -v` | 7 tests，OK | 离线验证真实service第二阶段请求被预算门禁挡在provider之前、首个原始响应保留、`run_once`将blocked artifact持久化；不证明模型语义分类正确 |
| `python evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py --preflight --output evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json` | `preflight_only`；模型请求0；planned calls=1；SDK/外层重试=0；Gold未加载且不入模型输入；数据库/生产API写入=false；输出路径可用；provider为`api.deepseek.com`、model为`deepseek-flash` | 只预检配置与输出位置；没有创建运行结果，也没有调用模型 |

在manifest v47封存时，P1在线语义复验尚未进行；其后续获授权运行单独记录在本文件下一节。该历史快照当时没有新模型输出或准确率结论；Gold、数据库、生产API及readiness均未变。

## 2026-10-07：观察共现边界单次在线开发复验（P1窄范围）

用户对本次新请求作出明确授权；先重新preflight确认路径空闲、最多1次provider调用、SDK/外层重试0、Gold未加载且不进入模型输入，再使用`--authorize-single-run`运行。provider/model为`api.deepseek.com` / `deepseek-flash`，temperature=0、timeout=120秒。

| 检查 | 结果 | 解释 |
| --- | --- | --- |
| 请求数 / 成功响应 / 重试 | 1 / 1 / 0 | 仅运行`cause_disposition`阶段；未触发结构或门型阶段 |
| 模型处置 | 两条分别为`state + detached_observation + descriptive_association` | 解释为仅报告停机前报警共现，没有原文因果/共同必要关系 |
| 节点与连接 | 观察节点2个且分开保留；relations=0；gate assessments=0；tree=`blocked` | 命中本例预期边界：两观察不连入顶事件；blockers列出无FTA候选及两个断开节点 |
| 引文和哈希 | 5条节点/处置引用均offset精确且唯一；source与response SHA-256相符 | 机械出处核验通过，不等同于独立语义专家审核 |
| 写入与 readiness | formal Gold=false；human expert Gold=false；database/API未写；FTA/production readiness=false | 单个合成非Gold样例，不产生准确率、校准或泛化结论 |

| 文件 | SHA-256 |
| --- | --- |
| [运行 JSON](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.json) | `6db1d6bad2e6a42b04c50bd3919d148c59b86ee97c23318a5a9dcbf175159f58` |
| [运行 Markdown](../evaluation/quality_eval/runs/candidate_fta_observation_boundary_v3_2026-10-07.md) | `4a81a34dd150765bae49638e97755541ba510d4caa761106ccab218ad01449f2` |

运行 JSON 内记录prompt SHA-256为`032cc045af891f704828e0913f150a4f411910211205bcf820913ebb57343567`，模型原始响应SHA-256为`075767d8b219f7df7528988138f83c50f231fcf6d17f340e3978f2f59c35e52c`。P1仅对此合成边界样例验收通过；不能据此推断模型对其他文本的断开观察识别准确率。下一阶段是P2真实来源开发回归，逐例检查原因语义角色、事件身份、层级/粒度、child集合与门证据；任何后续模型请求均需要针对新的运行单独授权。
