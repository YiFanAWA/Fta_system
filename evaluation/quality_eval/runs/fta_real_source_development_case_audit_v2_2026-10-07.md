# F30021 当前提示版本真实来源审计 v2

日期：2026-10-07  
审计性质：一次获授权的真实来源开发运行 + 离线证据/结构复核；不是人工专家签署、不是 Gold、不是盲测。  
运行提示：fta-cause-disposition-v5  
结果：候选树 blocked；fta_ready=false、production_ready=false。

## 结论

F30021 已按当前 Candidate FTA 链路运行完四个阶段：故障抽取、原因处置、结构分解、门评估。实际请求 4 次、成功响应 4 份，外层重试和 SDK 重试均为 0，没有自动修复或重试。模型原始响应保存在[原始运行 JSON](siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json)；随后用离线工具复核，生成[派生复核 JSON](siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.json)及[运行摘要](siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_offline_audit_v2_2026-10-07.md)。派生文件未再调用模型，也未覆盖原始输出。

本例**验证了 fail-closed 行为确实生效**，但没有关闭语义缺陷：一个原因短语在“Possible causes”和 r0949=0 故障值释义中重复出现，被绑定到同一抽取原因索引，宿主按既定规则保留为 unresolved；顶事件短引文也重复出现，未通过唯一引文门禁。完整四项可能原因因此没有进入完整子项集合，逻辑门保持 unknown，整树阻断。

## 五项逐条检查

### 1. 原因分类

原文抽取到 5 项原因文本。模型原始提议为 4 项 fta_event_candidate、1 项 relation_only；宿主最终处置为 3 项候选、1 项 relation_only、1 项 unresolved。这两组数字不能混为一谈：宿主对模型提议执行了证据门禁。

| 索引 | 原因文本 | 模型提议 | 宿主最终处置 | 审计判断 |
| --- | --- | --- | --- | --- |
| 0 | ground fault in the power cables | 因果条件 / 候选 | 候选 | Possible causes 原文支持，offset 精确且唯一；仍是 AI 提案，不是确认因果 |
| 1 | ground fault at the motor | 因果条件 / 候选 | 候选 | Possible causes 原文支持，offset 精确且唯一；仍是 AI 提案 |
| 2 | when the brake closes, this causes the hardware DC current monitoring to respond | 因果条件 / 候选 | 候选 | 原文明确表达制动器闭合触发监控响应，并列于该故障的 Possible causes；可以作为待审核候选，不能据此宣称关系已获专家确认 |
| 3 | short-circuit at the braking resistor | 因果条件 / 候选 | unresolved | 同一短语在 [332,372) 和 [468,508) 两处出现；一处属 Possible causes，一处属 r0949=0。抽取证据把两处都绑定到索引 3，宿主没有采纳模型自行挑选的上下文引文，符合“重复位置不自动选”的既定规则 |
| 4 | the hardware DC current monitoring has responded | 故障值模式 / relation_only | relation_only | 该项位于 r0949=0 解释中；没有设备现场读数，不自动连入故障树 |

**问题定位：**这里暴露的是“同一规范化 cause 值对应多个来源出现位置/段落角色”的证据身份问题，不是简单的 offset 错误。所有抽取 offset 都精确；但精确定位不代表系统有权替审核者选择某一语义出现位置。当前阻断是安全行为。后续应先审计抽取证据合同如何保留 occurrence/scope 身份，不得通过“默认取第一次”绕过。

### 2. 事件身份

顶事件节点对应记录 F30021 — ground fault，记录码与抽取描述一致，节点 ID 也绑定到该条 FaultRecord。可是顶事件证据只引用 ground fault，原文中该短语出现 4 次：[14,26)、[152,164)、[185,197)、[221,233)。树证据检查要求唯一引文，因此该锚点被拒绝并产生 top_event_evidence_ambiguous。

结论是**记录身份看起来对齐，但顶事件证据没有通过当前唯一定位合同**；不能把“码对了”说成事件身份与证据已经完整通过。

### 3. 层级

模型提议 4 个节点（1 个顶事件、3 个原因候选）和 1 个 possible_causes_enumeration scope。三个已接受原因作为顶事件 scope 的直接 child；child/output ID 均可解析；没有虚构嵌套层级，也没有额外生成显式因果关系边。

该结构仅对通过处置的三个子项内部一致，不能视作完整有效树：顶事件锚点不唯一，且候选集合缺一项，最终仍为 blocked。

### 4. 子项集合完整性

原文 Possible causes 列出 4 项。当前只有 3 项进入 child 列表；第 4 项因重复证据未决。scope 的 cause_set_complete=false，这是正确结果。模型没有为了得到“完整树”静默删除或改写未决条目。

### 5. 门证据

门型为 unknown，gate_evidence 为空。原文只是列出 Possible causes，并未直接说明这四条是互相替代（OR）还是共同必要（AND）；按当前审核规则，列表本身不足以推出逻辑门。因此保留 unknown 是合适的。

模型给出的 AND=0.0 / OR=0.1 / unknown=0.9 是**未校准的模型估计**，不是故障概率，也没有被宿主用于提升门型。当前门置信策略不可用，故 gate_confidence_policy_unavailable 继续阻断。

## 证据与运行账

- 抽取证据：16 条，offset 全部精确；5 个短引文在原文不唯一。
- 树证据：5 条，offset 全部精确，但顶事件短引文不唯一。
- 原因处置账：5 项、4 条已绑定证据，offset 精确且引文唯一；1 条未决项无绑定证据。
- 原始运行：4/4 模型响应完整保存；来源输入 SHA-256 为 f3178a6c9c46aa2109a44eb118c6a8730ebfdd6d9a6f5660147529f01ce41d31。
- 期间发现原始运行摘要把模型提议计数当作宿主最终计数。原文件保持原样；评估 runner 已修正为分别报告“模型提议”和“宿主最终处置”，并单独核验原因处置证据。离线派生文件中宿主最终计数是 3 candidate / 1 relation_only / 1 unresolved。
- 未修改 Gold、数据库、生产 API 或任何 readiness；本例不提供准确率、校准或泛化指标。

## 当前发现与后续边界

1. **案例阻断原因明确：**重复出现的 cause 短语导致 occurrence/scope 归属不唯一；顶事件短引文重复；候选集合不完整；门置信策略不可用。
2. **正确的安全行为已观察到：**未决原因不自动选位置，故障值释义不连成原因节点，列举不自动推 OR，阻断状态保留。
3. **仍需工程处理的问题：**审计 TextExtractionAdapter 的 cause 证据生成及 source occurrence 表达，定义如何保留段落/出现位置而不自动消歧；增加 F30021 离线回归。任何核心证据合同修改须先写清 owner、schema 影响和验收，不与 prompt/门阈值调整混做。
4. **后续真实模型复验：**本次 4 次授权请求已用完；如修改抽取/证据合同后还要再调用模型，必须另行取得针对具体样本与请求数的明确授权。不得把本次失败输出自动修复或覆盖。

P2 仅完成了 F30021 的当前版本单例观察，整体仍进行中；其余代表案例和独立来源验证尚未闭环。
