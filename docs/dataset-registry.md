# 数据集状态注册表 v1

## 目的

`evaluation/quality_eval/runs/dataset_registry_v1.json` 是当前数据集生命周期的汇总投影，用来统一回答：

- 这是什么数据集、哪个版本、样本/查询数量是多少；
- 它是知识 Gold、检索评测、RAG 回答评测还是领域适配开发集；
- 审核状态、审核 authority、是否允许训练、逻辑门是否已标注；
- 是否真实写入 SQLite，以及实际导入了多少条。

它不覆盖数据集文件中的字段事实，也不替代 SQLite 的导入事实。三者的 owner 分工固定为：

| 信息 | 唯一来源 |
| --- | --- |
| Gold 字段、审核标签、样本/查询内容 | 对应数据集 JSON |
| 数据库实际导入状态 | SQLite `dataset_imports` |
| 跨数据集生命周期汇总 | Dataset Registry |

旧数据集中的 `merge_summary.database_written` 或同名历史字段只作为历史信息，不再作为数据库是否入库的判断条件。

## 当前生成

源清单：

`evaluation/quality_eval/dataset_registry_sources_v1.json`

生成命令：

```powershell
D:\Miniconda\envs\NLP\python.exe evaluation/quality_eval/build_dataset_registry.py
```

默认输出：

`evaluation/quality_eval/runs/dataset_registry_v1.json`

构建器会读取数据集 JSON、计算 artifact SHA-256，并以只读方式查询
`backend-python/outputs/extraction_workflow.sqlite3` 的 `dataset_imports`。如果数据库文件、表、导入行或数量不一致，状态只能是
`not_verified` 或 `inconsistent`，不会伪造为 `completed`。

## 当前范围

- Siemens S210 Gold v1：281 条，评测/知识使用，不参与训练；
- Siemens S210 Retrieval Final Test v1：39 条查询，封存的历史最终测试集；
- Siemens S210 RAG Answer Dev v1：12 条查询，回答合同开发/验证集，尚非人工语义 Final Test；
- Aerospace Retrieval Dev v1：40 条查询，Adapter/跨领域开发集，尚非专家 Final Test。

评测报告必须同时说明 dataset、population、gold source、metric definition 和 sample/query count；不能只写一个脱离口径的 F1、Recall 或 MRR。

## 验收与边界

本注册表通过的是数据状态和评测口径治理，不等同于：

- 领域专家重新确认全部数据；
- RAG 回答语义正确；
- Generic Pipeline 已切入生产；
- FTA 因果关系或 AND/OR 逻辑已经可信。
