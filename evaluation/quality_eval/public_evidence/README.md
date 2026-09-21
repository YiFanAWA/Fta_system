# 公开资料证据标注集

这里保存从公开资料构建的、带来源和原文位置的临时评测集。它的用途是验证：

- 故障记录字段是否能从输入文本中抽取；
- 抽取字段是否能回指原文证据；
- 公开资料来源是否能被复现；
- 未知字段是否保持为 `unknown`，而不是被模型臆造。

## 当前来源

第一批来源是 [Annotated Maintenance Logbook](https://zenodo.org/records/20779601)，
数据集页面说明该数据包含 6169 条航空发动机维修记录和实体标注，当前版本许可为
CC BY 4.0。仓库不提交原始 CSV，只提交来源信息、生成器和生成后的评测集。

当前生成集保留 `CAUSE` 与 `PROBLEM` 等来源标注，但明确标记为
`source_annotated_provisional`。它不是本项目专家确认的 FTA 金标集：

- `fault_code`、`parameters`、`gate` 默认未知；
- 只有出现在组装输入文本中的字面片段才生成 `evidence_spans`；
- 因果关系保留来源字段，但 `causal_logic_status` 仍为 `unknown`；
- 不得据此自动批准生产审核结果。

## 复现

先从 Zenodo 下载原始 CSV，再运行：

```powershell
& .\.venv\Scripts\python.exe evaluation/quality_eval/public_evidence/build_public_evidence_dataset.py `
  --input "ANNOTATED LOGBOOK. Refinement according to expert feedback.csv" `
  --output evaluation/quality_eval/datasets/fta_public_logbook_evidence.json
```

生成器会输出样本数、train/dev/test 划分和可定位证据数量，并按输入文本的稳定哈希
划分集合，避免同一文本因为来源记录不同而跨集合泄漏。

## 标注责任边界

生成器负责机械整理、来源记录和字面证据定位；项目使用者负责确认样本是否符合当前
业务定义。没有设备或可靠性专家确认的字段必须保持 `unknown`，后续只对争议样本做
小规模专家复核。

该数据集可转换为统一的“模型软判断 + 后端硬约束”中间格式，命令和字段边界见
`evaluation/quality_eval/soft_logic_training/README.md`。转换只保留来源关系和证据，
不会把 `CAUSE` 自动解释为 FTA 的 `AND` 或 `OR`。
