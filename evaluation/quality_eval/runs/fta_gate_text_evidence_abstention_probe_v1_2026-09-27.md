# 外部原文门证据与 unknown 弃判探针 v1（2026-09-27）

## 目的

前一轮公开图示测试只含已知 AND/OR，不能证明模型面对“只列可能原因、没有组合关系证据”时会不会弃判。本轮单独测文字证据边界：三个原因清单应保留 `unknown`，另设一条原文在同一原因短语内明确写出 `or` 的 OR 阳性对照。

这轮只测试**给定原文证据后门关系分类/弃判**；不测试模型抽取原因集合的完整性，也不改变生产门禁。

## 数据与审核

| 文档簇 | 样本 | 预期 | 判定依据 |
| --- | ---: | --- | --- |
| NASA Apollo 15 降落伞调查报告 NTRS 摘要 | 1 | unknown | 三个条件称为可能原因，但没有说各自独立足以导致故障或必须共同发生 |
| U.S. Army TM 8-630（X-ray 场地发电机） | 1 | unknown | 同一故障现象下列出 Possible cause 表项，未说明各项组合逻辑 |
| U.S. Army TM 9-803（1/4-ton 4x4 truck） | 1 | unknown | 同一燃油故障下列出 Possible Cause 表项，未说明各项组合逻辑 |
| FAA AC 65-15A，Figure 14-44 | 1 | OR | Possible Cause 原句在两个原因之间直接写出 `or`；父事件自身的 `or` 不作为门证据 |

每份来源 PDF 均已下载并计算 SHA-256，与夹具记录逐一核对，4/4 匹配。测试材料保存来源链接、位置、哈希、子项与标签依据；模型输入不含来源身份、文档位置、预期标签、审核理由或预期门证据。PDF 副本未放入仓库；宿主策略拒绝了临时文件清理操作，目前仍保留在 `%TEMP%\fta-gate-text-evidence-20260927`（5 个 PDF，约 105 MiB）。

TM 8-630 的出版月份在模型运行后依据美国国会图书馆目录补正为 1944-11。运行 JSON 中的 `fixture_sha256` 对应运行时原始夹具；按原始日期值重建后与该哈希完全一致。此次仅改来源元数据、不在提示输入内；4 条当前提示的 SHA-256 与运行记录仍逐条一致，因此模型结果没有被改写或重跑。

候选 C（TM 9-808 “Engine turns but will not start”）未纳入：独立 AI 复核指出初始材料没有提供足够的原文版面/栏目上下文以独立确认父子集合归属；此外，手册前文对“逐项判断哪一个原因负责”的概括可能影响 OR/unknown 的定义边界。该项在模型调用前排除，不计入结果。

标签经过一次独立 AI 角色复核，**不是人类领域专家签署或项目正式 Gold**。这里的 `unknown` 仅表示所给原文作用域未直接确定 AND/OR，不表示物理系统不存在逻辑关系。

## 实测结果

- 模型：`deepseek-flash`，temperature=0；4/4 请求成功，无接口或格式失败。
- 总体：4/4 与 AI 角色审核标签一致（描述性命中率 1.00）。
- unknown：3/3 保持 unknown；错误强判 AND/OR 为 **0/3**。
- OR 阳性对照：1/1 判为 OR；模型引用的门证据是原因短语 `Defective temperature control or refrigeration bypass valve inoperative.`，且该引文精确存在于同一原因作用域文本。
- 决定性输出覆盖率：1/4（25%）；其余三条正确弃判。
- 模型自报分数为 1.0，但不是校准概率、物理事件概率，也不能用于选择生产阈值。

逐条预测、概率分布、理由、提示哈希和引用子串校验保存在[JSON 运行产物](fta_gate_text_evidence_abstention_probe_v1_2026-09-27.json)；输入与标签依据见[测试夹具](../datasets/fta_gate_text_evidence_abstention_external_test_v1.json)，测试器见[探针脚本](../public_sources/probe_fta_gate_text_evidence_abstention_v1.py)。

## 结论与限制

本次小样本信号符合预期：模型没有把“可能原因清单”自动等同为 OR，并且能够识别一条原因集合内部明确出现的 OR。它补上了既有图示分类测试缺少 `unknown` 的测试覆盖，但**不能据 3 个 unknown 样本声称弃判能力已经充分验证**。

限制：只有 4 个节点/4 个来源簇；标签是 AI 复核；仅有 1 个已知 OR 阳性、没有 AND 阳性；样本来自历史航空/军用维护资料；没有完整测试抽取、来源 offset、原因集合召回、嵌套 FTA 或生产策略。FAA 手册已于 2025-03-21 取消并由新版手册取代，此处仅作历史文本分类控制，不是现行维护指导。下一步应新增有**同范围直接 AND 证据**的文本控制和更多跨来源 unknown，然后按文档簇复核；不应调生产规则或阈值。

没有合并 Gold、没有写数据库、没有选置信阈值、没有修改生产 API。`formal_gold=false`、`database_written=false`、`gate_policy_applied=false`、`fta_ready=false`、`production_ready=false` 均保持。

## 验证

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -v
python -m py_compile evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py
```

5 项单元/合同测试通过；Python 编译检查通过；真实模型请求 4/4 成功。

## 来源

- [NASA NTRS：Apollo 15 main-parachute failure](https://ntrs.nasa.gov/citations/19730010152)
- [GovInfo：TM 8-630](https://www.govinfo.gov/content/pkg/GOVPUB-W-2d0ab034c3b55aecb517846ed3680576/pdf/GOVPUB-W-2d0ab034c3b55aecb517846ed3680576.pdf)
- [GovInfo：TM 9-803](https://www.govinfo.gov/content/pkg/GOVPUB-W-0a65af7e43e49e4126a777e69bc7fe4f/pdf/GOVPUB-W-0a65af7e43e49e4126a777e69bc7fe4f.pdf)
- [Library of Congress：TM 8 系列目录（TM 8-630，1944 年 11 月）](https://guides.loc.gov/us-army-technical-manuals/series-8-medical-department)
- [FAA：AC 65-15A PDF](https://www.faa.gov/documentlibrary/media/advisory_circular/ac_65-15a.pdf)；[FAA 目录中的撤销/替代说明](https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentid/23018)
