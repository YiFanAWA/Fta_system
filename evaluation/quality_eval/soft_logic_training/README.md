# 软逻辑训练数据合同

本目录定义“模型软判断、后端硬约束”的训练中间格式。它不是生产 API，也不是最终专家金标，
而是把不同公开数据源统一成可转换为 SFT、LoRA 或其他模型训练格式的规范化样本。

## 目标

模型可以提出：

- 故障记录、组件、描述和原因；
- 每个字段对应的原文证据；
- 原因与故障之间的因果关系；
- `AND` / `OR` 的候选逻辑门和置信度。

后端约束仍然负责决定结果能否进入正式故障树：

- 没有证据的字段不能通过；
- 只有明确语言线索或后续审核确认的逻辑门才能通过；
- 不明确的关系保持 `UNKNOWN`；
- `UNKNOWN` 不生成正式 FTA 树，而是进入可追踪的建树拒绝记录。

## Canonical 样本

每行是一个 JSON 对象，核心字段如下：

```json
{
  "schema_version": "soft_logic_training.v1",
  "sample_id": "PL-100004",
  "split": "train",
  "task": "fault_record_and_causal_candidate_extraction",
  "input_text": "Problem: ...",
  "target": {
    "top_event": "...",
    "records": [],
    "relations": [],
    "logic_candidates": []
  },
  "evidence_spans": [],
  "hard_constraints": {
    "allowed_gates": ["AND", "OR", null],
    "unknown_gate_policy": "keep_unknown",
    "require_evidence_for_records": true
  },
  "provenance": {
    "dataset": "Annotated Maintenance Logbook",
    "label_status": "source_annotated_provisional",
    "human_expert_reviewed": false
  }
}
```

`target.logic_candidates[*].status` 只有以下含义：

- `explicit_source_candidate`：来源文本直接给出逻辑提示，例如“or/either”或“both/together”；
- `source_relation_only`：来源只给出了因果关系，不能推出 AND/OR；
- `unknown`：没有足够依据，必须保留未知。

不能把公开数据的“CAUSES”关系自动改成 `OR`。因果边和 FTA 逻辑门是两个不同概念。

## 当前生成命令

已有的公开维修日志证据集可以转换为统一训练格式：

```powershell
python evaluation/quality_eval/soft_logic_training/build_soft_logic_training_dataset.py `
  --input-json evaluation/quality_eval/datasets/fta_public_logbook_evidence.json `
  --input-json evaluation/quality_eval/datasets/fta_project_handbook_evidence.json `
  --output evaluation/quality_eval/datasets/fta_soft_logic_training.jsonl
```

OMIn 的 100 条人工金标样本可以通过以下参数追加。原始数据放在仓库外部目录，不提交到本仓库：

```powershell
python evaluation/quality_eval/soft_logic_training/build_soft_logic_training_dataset.py `
  --input-json evaluation/quality_eval/datasets/fta_public_logbook_evidence.json `
  --omin-text-csv <OMIn>/OMIn_dataset/data/FAA_data/FAA_sample_100.csv `
  --omin-ner-csv <OMIn>/OMIn_dataset/gold_standard/raw/ner.csv `
  --omin-re-csv <OMIn>/OMIn_dataset/gold_standard/processed/re.csv `
  --output evaluation/quality_eval/datasets/fta_soft_logic_training.jsonl
```

车辆故障数据集目前只登记为候选来源，尚未进入主 JSONL。Mendeley 页面在本轮审计中没有提供
可复现的原始归档文件，且车辆数据的三张表（故障记录、实体标注、知识图谱）需要先按实际
下载版本核对列合同。因此脚本会对 `--mendeley-*` 参数主动阻断，不会在字段未验证时生成
假样本。来源状态见 `source_manifest.json`；待原始 CSV 可复现下载并完成列映射审计后，再
新增专用 adapter 和测试。

## 数据边界

- 公开数据的实体/关系标签是 `source_annotated_provisional`，不能直接作为项目专家金标；
- 当前项目手册样本只进入 `test`，不能混入训练集；
- OMIn 的 NER/关系金标可以训练文本实体和关系抽取，但不能证明本项目设备的 AND/OR；
- 逻辑门候选只作为模型软输出，正式建树仍由后端合同和审核状态控制；
- 训练、开发、测试按来源提供的 split 或稳定 ID 划分，禁止同一原文跨集合泄漏。

## 当前可复现产物

主产物 `evaluation/quality_eval/datasets/fta_soft_logic_training.jsonl` 当前由三类来源组成：

- 公开维修日志：76 条，来源标注的临时样本；
- OMIn：100 条，包含来源仓库提供的 NER/关系标注，仍不是本项目设备专家金标；
- 项目手册：27 条，全部强制进入 `test`，用于检验项目域迁移，不参与训练。

精确来源、状态、数量和限制见同目录的 `source_manifest.json`。

## 转换为训练文件

先生成统一 JSONL，再按任务拆分为 provider-neutral 的对话 JSONL：

```powershell
python evaluation/quality_eval/soft_logic_training/convert_soft_logic_training.py `
  --input evaluation/quality_eval/datasets/fta_soft_logic_training.jsonl `
  --output-dir evaluation/quality_eval/datasets/soft_logic_sft
```

转换器会生成：

- `fault_record_evidence_sft_train/dev/test.jsonl`：故障记录和证据抽取；仅输出该来源实际标注的字段，缺失标注不是负样本；
- `causal_relation_sft_train/dev/test.jsonl`：只包含来源确实提供关系标注的样本；
- `gate_candidate_review.jsonl`：逻辑门候选审核清单，不进入 SFT；
- `conversion_manifest.json`：数量、任务和边界记录。

项目手册样本仍只出现在 `test` 文件。将文件接入具体微调平台时，平台若不接受顶层
`metadata`，应由 provider adapter 删除 `metadata`，不能删除消息中的证据字段或改变
训练/测试划分。
