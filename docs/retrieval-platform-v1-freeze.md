# Retrieval Platform v1 冻结说明

更新时间：2026-09-21
适用项目：FTA System
冻结范围：Common Fault Schema v1、Domain Adapter Contract v1、Generic Retrieval Pipeline v1

## 冻结结论

三个 v1 已达到当前工程门禁，可以作为下一阶段 `AerospaceAdapter` 的稳定依赖。冻结不等于已经切换生产：S210 生产 API 仍使用旧链路，后续必须经过 shadow mode 和 rollback 验证后再切换。

## 1. Common Fault Schema v1

实现：`backend-python/common_fault_schema.py`

当前父实体身份为：

```text
domain + manufacturer + system + fault_code
```

当前验收：281 条 S210 Gold 无损映射、281 个唯一 `entity_id`、evidence/raw text 保留。

未来版本预留但本版不强行改造的来源维度：

```text
SourceRecord / KnowledgeVersion
source_id
source_version
manual_revision
effective_date
software_version
configuration
```

这些字段用于区分“同一故障实体”与“不同版本手册中的描述”，不能直接拼入当前 v1 的 `entity_id`。

## 2. Domain Adapter Contract v1

实现：`backend-python/domain_adapter_contract.py`

Adapter 负责：

- `parse_source()`；
- `normalize_entity()`；
- `build_retrieval_chunks()`；
- `extract_exact_fields()`；
- 提供 `RetrievalFieldValues` 的语义/精确字段角色。

Adapter 可以声明字段角色，例如：

```text
description / failure text -> semantic_primary
cause / trigger             -> semantic_cause
alarm / maintenance text   -> semantic_auxiliary
fault code / BIT code       -> exact_identifier
parameter / part number    -> exact_parameters
ATA / LRU / component      -> metadata 或 reranker context
```

禁止规则：Adapter 不得决定通用排名算法、RRF 参数、Top-K、bonus 权重或通过 `if domain == aerospace` 修改 Generic Pipeline。领域差异必须先表现为字段角色或 Adapter 数据，再用独立开发集证明公共能力确实不足后才扩展公共契约。

## 3. Generic Retrieval Pipeline v1

实现：`backend-python/generic_retrieval_pipeline.py`

冻结配置：

```yaml
main_retriever: description dense + cause dense + RRF
exact_signals: fault_code + parameter
auxiliary_retriever: alarm dense
candidate_pool: D2 Top20 union Alarm Top10
aggregation: parent entity_id deduplication
reranker: BAAI/bge-reranker-v2-m3
production_guard: explicit fault_code deterministic pin
component_boost: disabled
```

`component` 保留在 metadata、reranker context 或明确 scoped filter 的候选能力中，不默认转成 exact score bonus；此前消融实验已证明默认 component boost 会损害排序。

Parity 证据：

- 候选召回 39/39；
- Top-1 相关性保持 39/39；
- R@1=0.9231，R@3/R@5/R@10/R@20=1.0，MRR=0.9573；
- 自动门禁 PASS；
- FT022/FT023/FT030 的候选边界差异仅作为诊断，不影响相关故障召回。

## 4. 数据集生命周期

- `Gold Dataset v1`：281 条，冻结，只读；
- `Retrieval Evaluation v1`：42 条，开发/调参阶段冻结；
- `Retrieval Final Test v1`：39 条，已封存，只能作为历史回归参考；任何 Generic 算法、chunk、router、reranker 或生产切换变化都新建 Final Test v2；
- `RAG Answer Development / Validation v1`：12 条，已完成工程验证，但不能宣称生产泛化 100%；未来另建 `RAG Answer Final Test v1`，建议 20～30 条全新查询。

## 5. 生产切换边界

切换前采用 shadow mode：

```text
真实 Query
   ├─ Legacy：继续生成用户答案
   └─ Generic：只记录 Top1/Top3、候选召回、延迟、错误和 exact 行为
```

生产配置保留：

```text
retrieval_backend=legacy
retrieval_backend=generic
```

只有 shadow 数据没有明显 regression 后，才允许把默认值切到 generic；出现回归时可以立即回到 legacy。前端布局和回答合同不因 shadow 增加 UI。

## 6. 下一阶段

只启动 `AerospaceAdapter` 的单域验证：小规模公开数据 → Common Schema 映射 → RetrievalChunk → 航空 Dev Set → Generic Pipeline。暂不做 Domain Router，不把航空逻辑写进通用核心，不构造没有证据支持的 AND/OR FTA 门。

## 7. Phase G 当前进度（2026-09-21）

G1～G3 已完成第一轮：

- 数据源选定为 FAA Service Difficulty Reports 2024 官方 CSV；
- 已生成 40 条确定性开发样本：`evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json`；
- 已实现 `backend-python/aerospace_adapter.py`，只负责 FAA SDR → Common Fault Schema v1 的映射和检索字段角色声明；
- 已生成 `evaluation/quality_eval/runs/aerospace_schema_fit_report_v1_2026-09-21.md` / `.json`；
- Fit 结论为 `fit_with_explicit_adaptations`：原始数据没有独立 native fault code，`OperatorControlNumber` 作为记录身份，`JASCCode` 保留为航空 exact identifier；BIT、显式 ATA、标准化 flight phase、专家 cause 和 FTA relations 保持缺失，不做推断；
- 40/40 entity 具备字符证据，40/40 entity_id 唯一，118 个 RetrievalChunk 维持父实体归属；
- 未修改 Generic Retrieval Pipeline、未实现 Router、未接生产索引，也未把该样本当作专家 Gold。

G4/G5 已完成：基于这 40 条样本建立 `Aerospace Retrieval Dev v1`，并用冻结的 Generic Pipeline 做了单域开发评测。查询已增加 `sufficient / partially_sufficient / insufficient` 分层。结果保存于 `evaluation/quality_eval/runs/aerospace_generic_retrieval_dev_v1_sufficiency_stratified_2026-09-21.json/.md`；误差分类保存于 `evaluation/quality_eval/runs/aerospace_generic_retrieval_error_taxonomy_v2_2026-09-21.json/.md`。

分层结果：明确查询 24 条的 Candidate R@20/Reranked R@1 均为 1.0000；部分充分查询 10 条的两项均为 0.7000；信息不足查询 6 条的 Candidate R@20 为 0.5000、Reranked R@1 为 0.1667。6 条候选池漏召回、2 条候选内排序未到 Top1，当前暂归字段检索角色和查询歧义，未修改公共契约。

查询充分性对照已完成：component/condition 的 16 条 base 与 16 条 enriched 查询中，Candidate R@20 从 0.6250 提升到 1.0000，Reranked R@1 从 0.5000 提升到 1.0000。无 Router 混合索引也已完成首轮：321 个实体、79 条查询，WrongDomain@1/3/5 为 0.1772/0.3418/0.3797，S210 Candidate R@20=1.0000、Aerospace=0.8500。下一步是固定同一数据和查询，比较 `no-router` 与 `metadata scope`，再决定是否有必要实现 Domain Router。

Oracle metadata scope 对照已完成：WrongDomain@1/3/5 降为 0，整体 Candidate R@20 仍为 0.9241，说明 scope 只解决跨域污染，不解决航空域内部召回。下一步先建立不含显式领域关键词的跨域识别查询，再决定是否实现生产 Router。

数据源：

- FAA 下载说明：<https://www.faa.gov/av-info/download_SDR>
- 2024 CSV：<https://external.apic4e.faa.gov/sdrs/retrieve/SDR-2024.csv>
