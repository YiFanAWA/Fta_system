# FTA 门型证据消融探针 v1（2026-09-27）

## 目的

前一轮证明模型能在给出明确门型原文时区分 AND/OR，也能对两个近邻案例弃判。本轮反向检查它是否依赖输入证据：取 6 个之前已判对的 AND/OR 正例，保留父事件、子事件和父事件上下文，移除决定性门型句及候选集标题，再要求模型判断。

由于决定性关系证据不在模型可见范围内，预期标签全部为 `unknown`。这是一组配对的**合成证据消融控制**，不是把原始公开来源重新标注为 unknown，也不是自然分布测试。

## 运行结果

`deepseek-flash`、temperature=0，6/6 请求成功：

| 指标 | 结果 |
| --- | ---: |
| 消融输入判为 `unknown` | 6/6 |
| 缺证据时错误强判 AND/OR | 0/6 |
| 门型证据引文 | 0/6（符合 unknown 合同） |
| 请求失败/格式失败 | 0 |

六个样本分别对应 FAA 空调故障原因、NASA 泵系统灾难事件、Vesely 电阻关键路径、CARE III 两个不同门定义，以及 NASA 高压太阳能阵列逻辑定义。CARE III 两条共享一个来源簇，所以这是 6 个节点、5 个来源簇，而非 6 个完全独立文档。

作为配对对照，原始六个已知门样本此前输出均正确；去掉门型证据后，六个对应样本均转为 `unknown`。该对照显示模型在这组构造输入上遵循了“门型需有可见直接证据”的提示约束。它不能排除模型预训练中见过公开材料，也不能证明模型在其他文本或场景下同样保守。

逐条输出、理由、原始自报分数、提示哈希及请求状态见[运行 JSON](fta_gate_text_evidence_ablation_v1_2026-09-27.json)；成对输入和来源哈希见[消融夹具](../datasets/fta_gate_text_evidence_ablation_v1.json)。FAA 材料是已撤销/被替代的历史手册，仅作文本分类控制，不是现行维修指导。

## 解释与限制

- 结果说明：对本组已知正例，移除门型决定性句后，模型没有继续沿用先前标签或凭子事件名字猜门型。
- 由于提示明确要求“证据不足判 unknown”，该结果也同时反映提示遵循情况，不是模型脱离提示的独立门型能力证明。
- 样本是从原始正例派生，且只覆盖 5 个来源文档簇；标签按“当前暴露证据范围”在推理前指定，来自 AI 角色审核，不是人类专家 Gold。
- 六条 `top_probability` 均为 1.0，是未校准的模型自评；不能解释为正确率概率或作为生产阈值。
- 不测试源文档抽取、cause completeness、递归树结构、参数校准、数据库/API 接入或生产运行。

## 验证命令

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -v
python -m py_compile evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py
python evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py --dataset evaluation/quality_eval/datasets/fta_gate_text_evidence_ablation_v1.json --output evaluation/quality_eval/runs/fta_gate_text_evidence_ablation_v1_2026-09-27.json
```

夹具合同测试 8 项通过；本轮真实模型请求 6/6 完成。未修改正式 Gold、数据库、门策略或生产 API。`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false` 保持。
