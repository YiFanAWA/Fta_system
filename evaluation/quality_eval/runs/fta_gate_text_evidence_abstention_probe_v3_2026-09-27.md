# FTA 门型文本证据与 unknown 弃判探针 v3（2026-09-27）

## 目的与边界

本轮在先前“可能原因列表/明确 OR/直接 AND”探针上，增加不同措辞的 AND 正例、直接 OR 正例，以及两种不能仅凭连词或时间先后推断门型的近邻样本。要验证的是：**给定父事件、子事件和限定范围的原文后，模型是否只在原文直接表达必要逻辑时判断 AND/OR，并在证据不足时保留 `unknown`。**

这不是从原始手册自动抽取完整故障树的端到端评测；不改变生产逻辑、门型策略、阈值、正式 Gold、数据库或就绪状态。

标注语义复核：用户确认 Apollo 13 引文中“压力、温度都出现”本身不足以判为 AND；AND 还要求证据支持所有输入均为父事件所必需。因此该样本继续保留 `unknown`。这确认了门型判定口径，不构成领域专家对物理因果机理的签署。

## 本轮新增材料

新增 6 个节点，来自 5 个 NASA/NTRS 来源文档簇。CARE III 手册提供一条“所有输入均须发生”的 AND 和一条“任一输入即可”的 OR，因此这两个节点共享一个来源簇。标签由主 AI 角色在模型推理前依据夹具内原文直接证据规则赋予；不是人工领域专家签署，也没有独立第二审阅者确认。

| 案例 | 来源及判定 | 预期 | 输出 | 证据核对 |
| --- | --- | --- | --- | --- |
| Vesely 电阻关键路径 | 两种指定模式的电阻故障“必须发生”才能导致顶事件 | AND | AND | 门证据为输入证据的精确子串 |
| CARE III：全部输入 | 明确要求 m 至 z 的所有事件发生 | AND | AND | 精确子串 |
| CARE III：任一输入 | 明确写明 m 至 z 中任一事件发生即触发父事件 | OR | OR | 精确子串 |
| 高压太阳能阵列逻辑定义 | 输出事件要求所有输入事件共存 | AND | AND | 精确子串 |
| 植物生长舱可能原因列表 | 只列可能原因，列表末尾使用语法连接词 `and` | unknown | unknown | 未输出门证据引文，符合弃判合同 |
| Apollo 13 压力/温度叙述 | 只叙述压力和温度上升后发生破裂，没有说明两项是否必要或任一项是否足够 | unknown | unknown | 未输出门证据引文，符合弃判合同 |

来源与引文可由[扩展夹具](../datasets/fta_gate_text_evidence_abstention_extension_v2.json)中的记录和哈希追溯。官方来源：[Vesely/NASA NTRS](https://ntrs.nasa.gov/citations/19720018331)、[NASA CARE III](https://ntrs.nasa.gov/citations/19850017881)、[NASA 高压太阳能阵列报告](https://ntrs.nasa.gov/citations/19700026276)、[植物生长舱报告摘要](https://ntrs.nasa.gov/search.jsp?R=19960047562)、[Apollo 13 Review Board 报告](https://ntrs.nasa.gov/api/citations/19700078913/downloads/19700078913.pdf)。PDF SHA-256 或摘要文本 SHA-256 均记录在夹具中；植物生长舱 NTRS 条目没有可下载 PDF，因此只对官方摘要原句计算文本哈希。

模型输入不包含来源身份、预期门标签、审核理由或期望引文。来源 URL、逐字原文、位置、哈希、标签依据与模型结果分别保存在夹具和运行 JSON 中。

## 当前扩展运行结果

运行使用 `deepseek-flash`、temperature=0，6/6 请求成功，没有接口/格式失败。

| 指标 | 结果 |
| --- | ---: |
| 本轮标签一致 | 6/6 |
| 本轮明确 AND/OR 正例正确 | 4/4（AND 3/3，OR 1/1） |
| 本轮 `unknown` 保留 | 2/2 |
| 本轮 unknown 被错误强判 AND/OR | 0/2 |
| 明确门型的证据引文精确命中输入范围 | 4/4 |
| 决定性输出覆盖率 | 4/6（66.7%） |

逐条分布、模型理由、原始自报分数、提示哈希及引文子串校验见[本轮运行 JSON](fta_gate_text_evidence_abstention_extension_v2_2026-09-27.json)。本轮六条自报 Top probability 均为 1.0；这是未校准的模型自评，不能解释为真实正确概率。

## 累计描述性结果（前三轮合并）

将 v1 的 4 条、扩展 v1 的 2 条及本轮新增的 6 条合并，共 12 个节点、11 个来源文档簇：

| 指标 | 累计结果 |
| --- | ---: |
| 标签一致 | 12/12 |
| AND 正例 | 4/4 |
| OR 正例 | 2/2 |
| `unknown` 保留 | 6/6 |
| `unknown` 被错误强判 AND/OR | 0/6 |
| 明确门型引文精确落在输入证据子串 | 6/6 |
| 决定性输出覆盖率 | 6/12（50.0%） |

这只是同一模型、同一提示合同下的 12 个探索性观察，不是独立盲测准确率或统计可靠性结论。累计类别数为 AND 4、OR 2、unknown 6；正例规模仍小，且样本是为证据规则构造的文本探针。

## 测试器验证

实际执行：

```powershell
python -m unittest evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -v
python evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py --dataset evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v2.json --output evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v2_2026-09-27.json
```

本轮新增运行完成；针对性测试在收尾复跑中确认。测试夹具校验覆盖来源文档/簇数量、标签分布、明示证据、列表语法 `and` 的 unknown、共现叙述的 unknown，以及摘要来源使用文本哈希而非 PDF 哈希的情形。

## 缺陷、限制与结论

- **未发现本轮这 6 个样本上的门型分类或弃判错误。** 但此结论仅描述这些构造样例。
- 两条 CARE III 样本共享同一手册；12 个节点虽来自 11 个来源簇，仍不能当成 12 个完全独立来源。
- 其中多个 AND/OR 样本是文献中的逻辑定义或解释性示例；它们测试文本语义分类，不证明真实设备故障树结构完整。
- Apollo 13 的 `unknown` 表示给定引文没有证明 Boolean 必要性/充分性，并非断言物理机理不存在 AND/OR 关系。
- 模型每条都自报 1.0，显示该分数不能作为信心阈值；本轮不做概率校准，也不据此定策略。
- 标签为主 AI 角色推理前标注，不是专家 Gold；没有独立第二 agent 审核。
- 不测试源文档自动抽取、完整原因集合召回、递归/嵌套建树、专家接受标准、数据库集成或生产运行。

结论仅限于：**这轮探针中，显式“全部必须发生”“任一即可”语义被分对，语法并列和时序共现没有被升级为确定门型；精确引文校验也通过。** 这支持继续扩充跨来源、真实故障文本和独立审核样本，不足以开放自动建树。

以下状态保持不变：`formal_gold=false`、`database_written=false`、`gate_policy_selected=false`、`fta_ready=false`、`production_ready=false`。
