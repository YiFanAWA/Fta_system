# Aerospace Schema Fit Report v1

## 结论

> FAA SDR 2024 的 40 条公开样本可以进入 Common Fault Schema v1，但存在明确的领域适配：原始记录没有原生 fault code，当前使用 OperatorControlNumber 作为唯一记录身份；JASCCode 作为 exact identifier 保留。该样本不是专家金标，也不能证明航空检索泛化。

## 样本与证据

- 原始样本：40 条。
- Common Fault Entity：40 条；唯一 entity_id：40 条。
- RetrievalChunk：118 个。
- 字符证据可回溯实体：40/40。
- 原始 CSV 字段保存在每个 entity 的 `domain_specific.raw_record`，不把缺失字段推断成标签。

## 字段映射

| 原始字段 | Common Schema 目标 | 检索角色 | 状态 | 说明 |
|---|---|---|---|---|
| `OperatorControlNumber` | `FaultEntity.fault_code + domain_specific.source_record_id` | `identity / metadata` | **adapted** | FAA SDR has no native fault-code column; the source record identifier fills the required identity slot and is explicitly typed. Generic v1 exact ranking uses JASC as the single adapter exact identifier; record-id exact ranking is not claimed. |
| `JASCCode` | `domain_specific.jasc_code + RetrievalFieldValues.exact_identifier` | `exact_identifier` | **preserved** | JASC is not promoted to a unique fault entity because multiple reports can share one JASC code. |
| `Discrepancy` | `FaultEntity.description + raw_text + evidence` | `semantic_primary` | **preserved** | The original narrative is retained; an explicit C/A: suffix is separately exposed as remedy. |
| `PartCondition` | `FaultEntity.symptoms + domain_specific.part_condition` | `semantic condition / reranker` | **preserved** | Condition is not relabeled as a cause. |
| `PartName / ComponentName` | `FaultEntity.components + domain_specific component fields` | `metadata / reranker` | **preserved** | UNKNOWN placeholders are not promoted to components. |
| `PartNumber / ComponentPartNumber` | `FaultEntity.parameters` | `exact_parameters` | **preserved** | Part numbers are kept as exact values; they are not treated as Siemens-style parameters. |
| `AircraftMake / AircraftModel` | `domain_specific.aircraft_make/model + metadata` | `metadata / reranker` | **preserved** | Aircraft identity is available to the parent document without changing generic ranking. |
| `NatureOfConditionA-C` | `domain_specific.nature_of_condition_codes` | `metadata` | **preserved** | Codes are retained as codes; no unsupported natural-language cause is invented. |
| `PrecautionaryProcedureA-D` | `domain_specific.precautionary_procedure_codes` | `metadata` | **preserved** | The CSV contains procedure codes, not a complete free-text maintenance action field. |
| `StageOfOperationCode / HowDiscoveredCode` | `domain_specific stage/how-discovered fields` | `metadata` | **preserved** | These are source codes, not a derived flight phase or causal label. |
| `C/A: text embedded in Discrepancy` | `FaultEntity.remedies` | `semantic_auxiliary` | **partial** | Only explicit C/A: text is parsed; the source has no dedicated structured corrective-action column. |
| `BIT code` | `not present in FAA SDR 2024 sample` | `not available` | **absent** | Must not be fabricated; add only when a later aerospace source provides it. |
| `ATA chapter` | `not explicit; JASC retained instead` | `not available` | **absent** | No derived ATA chapter is created in this adapter. |
| `flight phase` | `not explicit; StageOfOperationCode retained` | `not available` | **absent** | The adapter does not reinterpret a source stage code as a standardized flight phase. |
| `relations / AND-OR gates` | `FaultEntity.relations=empty; review_status unknown` | `not available` | **absent** | This Phase G sample is entity/evidence/retrieval validation only, not FTA labeling. |

## 明确缺失或暂不派生

- BIT code
- explicit ATA chapter
- standardized flight phase
- native structured fault code
- expert cause labels
- fault relations and AND/OR gates

## 边界

- 当前只完成 G1（公开样本）和 G2/G3（Adapter + Fit Report）。
- 未修改 Generic Retrieval Pipeline，未实现 Domain Router，未建立航空专家 Gold。
- 下一步是建立 Aerospace Retrieval Dev v1，并先做错误分类；不能直接把 Dev 结果当 Final Test 或生产结论。

## 来源

- https://external.apic4e.faa.gov/sdrs/retrieve/SDR-2024.csv
- 来源：FAA Service Difficulty Reports 2024 CSV；具体条款和再利用边界仍应按 FAA 页面与下载说明核对。
