# 多来源公开故障树门型探针 v1（2026-09-27）

## 目的与边界

在既有 FAA 图示分类探针（13 个节点、单份指南）之外，增加来自三份公开 PDF 的明确 AND/OR 图示样本，检查相同文本提示和 DeepSeek 模型能否在新的来源文档上分类。模型只看到父事件和直接子事件文本；图示、图号、来源、图注、门符号和门标签都没有送入提示。

这不是项目 Gold、人工专家签署、置信度校准、真实故障原文到树的端到端验收，也不是生产门型策略。图中的真实门型并不等同于原始故障叙述对门型提供了直接证据；本探针只测“从父/子事件文本猜图示门型”，不证明证据约束建树可以放行。

## 来源与标注依据

| 来源簇 | 样本 | 标注依据 |
| --- | ---: | --- |
| NASA *Fault Tree Handbook with Aerospace Applications*, Version 1.1 (2002) | 2 | Fig. 4-3 图注明确为 OR；Fig. 5-5 后续正文明确该序列以 AND 建模 |
| NRC *Fault Tree Handbook*, NUREG-0492 | 1 | Fig. IV-6 图注和随文说明明确为 AND |
| HERMES CubeSat FTA（Felix Bidner，University of Colorado Boulder；NASA SSRI 知识库托管） | 2 | Fig. 4 的门符号逐一对照同文 Fig. 3 的门型图例，为 OR；该论文不是 NASA 编写的标准 |

NASA 手册、NRC 手册及 HERMES 论文的 PDF SHA-256 和逐条图页信息保存在[测试夹具](../datasets/fta_gate_multisource_diagram_external_test_v1.json)。HERMES 论文参考了 NASA 手册，因此三个文档簇不能被解读成完全统计独立的来源。

来源：[NASA Fault Tree Handbook](https://extapps.ksc.nasa.gov/reliability/Documents/Fault_Tree_Handbook_with_Aerospace_Applications_August_2002.pdf)、[NRC NUREG-0492](https://www.govinfo.gov/content/pkg/GOVPUB-Y3_N88-PURL-gpo80924/pdf/GOVPUB-Y3_N88-PURL-gpo80924.pdf)、[HERMES CubeSat FTA paper](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/CUSRS10_14%20Fault%20Tree%20Analysis%20of%20the%20HERMES%20CubeSat.pdf)。

## 结果

- 模型：`deepseek-flash`，temperature=0；5/5 请求成功。
- 图示门型分类：**5/5 正确**；AND 2/2，OR 3/3。
- Always-OR 基线：3/5 = 0.60；本小样本 balanced accuracy / macro-F1 均为 1.00。
- 决策覆盖率 5/5，模型没有对任何已知图示门型弃判。
- 模型自报概率的描述性 Brier 为 0.06756；这是自报分数，**不是校准结果**，也不可用来选择运行阈值。

逐条结果：

| 节点 | 图示标签 | 预测 | Top 分数 | Top margin | 观察 |
| --- | --- | --- | ---: | ---: | --- |
| NASA Fig. 4-3 阀门关闭 | OR | OR | 0.85 | 0.73 | 将硬件故障、人为错误、测试解释为可替代成因；指出 testing 的轻微歧义 |
| NASA Fig. 5-5 肼泄漏后爆炸 | AND | AND | 0.75 | 0.60 | 将泄漏、规模条件、点燃爆炸解释为需要共同成立的条件链 |
| NRC Fig. IV-6 现场直流电源失效 | AND | AND | 0.90 | 0.85 | 根据所有现场直流电源失效，要求两台发电机与电池均失效 |
| HERMES Fig. 4 天线指向精度超差 | OR | OR | 0.70 | 0.45 | 指出磁强计节点描述并不完整，仍作 OR 判断 |
| HERMES Fig. 4 磁强计 | OR | OR | 0.85 | 0.75 | 将无供电和引脚失效理解为各自可导致该节点失效 |

逐条原始输出见[JSON 运行产物](fta_gate_multisource_external_probe_v1_2026-09-27.json)，探针入口见[多来源探针](../public_sources/probe_multisource_fta_gate_external_v1.py)。

## 失败模式与尚未验证项

1. **没有 unknown / 证据不足样本。** 五个标签都由完整 FTA 图示给出，模型被要求在已知 AND/OR 两类中分类；5/5 没有弃判不等于它能在原始文本缺少门证据时保留 `unknown`。
2. **这不是直接证据授权测试。** 部分事件措辞可启发 AND/OR，但模型理由仍可能借助工程常识补全图外因果；本探针没有验证这些理由是否逐句得到源文证据支持。
3. **样本极小且成簇。** 五个节点来自三份 PDF；HERMES 的两个节点还来自同一棵树。指标只作冒烟信号，不能估计稳健泛化或风险上界。
4. **模型的高分不是门型概率。** `top_probability` 和 Brier 仅为模型自我报告；不代表真实正确概率、工程事件概率或可用于自动接受的置信阈值。
5. **没有改变产品门禁。** 没有写正式 Gold、数据库、生产 API 或自动树；`formal_gold=false`、`database_written=false`、`fta_ready=false`、`production_ready=false` 保持。

为构造样本而排除的内容及原因也记录在 JSON 夹具中：抽象 `Q/A/B` 示意门的文字本身无法分辨隐藏门型；图 6-7 的子事件文本直接写了 “B OR C”，且与另一手册的公式示例重复；HERMES Fig. 1 的事件文字含有 “or”。

## 验收

本轮针对性离线测试：FAA 旧探针 5 项 + 多来源夹具/探针 4 项，共 9 项通过；相关 Python 文件 `compileall` 通过；三份下载 PDF 均与夹具保存的 SHA-256 一致。模型请求共 5 次。探针不会自动选阈值或改变运行时策略。

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_probe_faa_ast_fta_gate_external_v1 evaluation.quality_eval.public_sources.test_probe_multisource_fta_gate_external_v1 -v
python -m compileall -q evaluation/quality_eval/public_sources/fta_gate_external_probe_core.py evaluation/quality_eval/public_sources/probe_faa_ast_fta_gate_external_v1.py evaluation/quality_eval/public_sources/probe_multisource_fta_gate_external_v1.py evaluation/quality_eval/public_sources/test_probe_multisource_fta_gate_external_v1.py
```

下一步应保持 AND/OR 判定 fail-closed：用实际源文直接支持的节点继续评“证据完整性/作用域完整性”，另外单独扩展 `unknown`/证据不足对照；不要把这 5 个图示分类样本用于阈值拟合。
