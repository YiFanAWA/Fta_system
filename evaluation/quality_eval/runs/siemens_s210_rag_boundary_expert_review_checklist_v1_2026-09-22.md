# Siemens S210 RAG 边界策略专家审核清单 v1

> 审核专家：刘武
> 审核状态：待专家填写；本文件不是 Gold 数据，不提供预审结论。
> 审核对象：S210 RAG 在“可回答、需警告、证据不足、库外问题”之间的边界行为。

## 一、审核目的

请判断系统面对每个用户问题时，是否可以基于当前 Siemens S210 知识库给出回答，以及回答应采用的安全策略。这里只审核边界决策，不审核 embedding、检索排序、Reranker 或具体回答文本。

## 二、标注规则

| expected_knowledge_status | 判定标准 |
| --- | --- |
| `supported` | 有明确 S210/Siemens/SINAMICS 身份、故障码、参数或足够明确的 S210 故障实体，可正常回答。 |
| `supported_with_warning` | 属于技术故障问题，可以检索和回答，但缺少型号、故障码、参数或组件等关键信息，必须降低确定性并提示补充。 |
| `insufficient_evidence` | 信息过少，不能定位到具体故障，禁止输出确定诊断，必须请求补充信息。 |
| `out_of_domain` | 明确属于当前 S210 知识库之外的领域，不进入 S210 故障诊断回答。 |

| expected_action | 与状态的关系 |
| --- | --- |
| `answer` | 正常回答，仍须遵守证据引用合同。 |
| `answer_with_warning` | 可以回答，但必须明确不确定性并列出建议补充信息。 |
| `ask_information` | 先请求信息，不给确定故障诊断。 |
| `reject` | 明确告知超出 S210 知识库范围，不生成该领域诊断。 |

## 三、专家填写要求

- 逐条依据 S210 知识库边界和问题本身判断，不把工程预期当成专家结论。
- supported 只表示当前问题有足够身份/证据可以正常回答；不是说答案中的每个事实都已验证。
- supported_with_warning 表示可以检索和回答，但必须降低确定性并提示补充信息。
- insufficient_evidence 表示不能给出确定诊断，必须请求补充信息。
- out_of_domain 表示问题明确超出 Siemens S210 当前知识库，不进入 S210 故障诊断回答。
- 若选择 answer_allowed=true，必须说明为什么当前信息足够；若选择 false，必须填写 missing_information 或拒答理由。
- 不要依据模型输出或当前实现行为审核；这里只审核边界策略的专家标准。

每条记录必须填写：
- `expected_knowledge_status`：四选一；
- `answer_allowed`：是否允许给出知识库回答；
- `warning_required`：是否必须带风险/不确定性提示；
- `need_additional_info`：是否需要用户补充信息；
- `missing_information`：需要补充的具体字段；
- `expected_action`：四选一；
- `expert_reason`：至少一句可复核理由；
- `expert_status=reviewed`、审核人和日期。

## 四、逐条审核表

### 1. BOUNDARY-001

**用户问题：** S210 F01630 是什么故障？

**工程分类（仅供追踪，不是专家结论）：** `explicit_fault_code`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 2. BOUNDARY-002

**用户问题：** Siemens S210 的 p7829 参数有什么作用？

**工程分类（仅供追踪，不是专家结论）：** `explicit_parameter`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 3. BOUNDARY-003

**用户问题：** SINAMICS A01009 控制单元过热怎么办？

**工程分类（仅供追踪，不是专家结论）：** `explicit_system_and_code`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 4. BOUNDARY-004

**用户问题：** STO 状态不一致对应什么 S210 故障？

**工程分类（仅供追踪，不是专家结论）：** `explicit_safety_signal`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 5. BOUNDARY-005

**用户问题：** DRIVE-CLiQ 组件固件升级失败的原因是什么？

**工程分类（仅供追踪，不是专家结论）：** `explicit_component_signal`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 6. BOUNDARY-006

**用户问题：** Siemens 控制单元温度过高，应该检查什么？

**工程分类（仅供追踪，不是专家结论）：** `explicit_manufacturer_and_component`
**工程预期（仅供对照，不得直接复制）：** `supported` / `normal` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 7. BOUNDARY-007

**用户问题：** 温度异常怎么办？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 8. BOUNDARY-008

**用户问题：** 电机通信失败是什么原因？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 9. BOUNDARY-009

**用户问题：** 编码器信号异常，怎么排查？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 10. BOUNDARY-010

**用户问题：** 驱动报警后停止运行，可能是什么问题？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 11. BOUNDARY-011

**用户问题：** 控制单元过热应该如何处理？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 12. BOUNDARY-012

**用户问题：** 参数设置错误导致报警，怎么判断？

**工程分类（仅供追踪，不是专家结论）：** `technical_low_identity`
**工程预期（仅供对照，不得直接复制）：** `supported_with_warning` / `warning` / answer_allowed=`True`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 13. BOUNDARY-013

**用户问题：** 设备坏了。

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 14. BOUNDARY-014

**用户问题：** 报警了怎么办？

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 15. BOUNDARY-015

**用户问题：** 不工作了。

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 16. BOUNDARY-016

**用户问题：** 帮我看看这个问题。

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 17. BOUNDARY-017

**用户问题：** 系统有点异常。

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 18. BOUNDARY-018

**用户问题：** 这个故障严重吗？

**工程分类（仅供追踪，不是专家结论）：** `low_information`
**工程预期（仅供对照，不得直接复制）：** `insufficient_evidence` / `clarify` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 19. BOUNDARY-019

**用户问题：** 今天天气怎么样？

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 20. BOUNDARY-020

**用户问题：** 帮我推荐一只股票。

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 21. BOUNDARY-021

**用户问题：** 帮我写一首诗。

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 22. BOUNDARY-022

**用户问题：** 飞机液压系统故障怎么处理？

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 23. BOUNDARY-023

**用户问题：** 请分析这个航空器的 ATA 故障。

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

### 24. BOUNDARY-024

**用户问题：** 帮我做一个旅游计划。

**工程分类（仅供追踪，不是专家结论）：** `explicit_external_domain`
**工程预期（仅供对照，不得直接复制）：** `out_of_domain` / `out_of_domain` / answer_allowed=`False`

| 专家字段 | 填写值 |
| --- | --- |
| expert_status | `reviewed` |
| expected_knowledge_status | `supported` / `supported_with_warning` / `insufficient_evidence` / `out_of_domain` |
| answer_allowed | `true` / `false` |
| warning_required | `true` / `false` |
| need_additional_info | `true` / `false` |
| missing_information | 例如：`设备型号；故障码；报警原文`，无则填 `[]` |
| expected_action | `answer` / `answer_with_warning` / `ask_information` / `reject` |
| expert_reason | 说明依据和边界判断 |
| reviewer | `刘武` |
| reviewed_at | `YYYY-MM-DD` |

**专家填写：**
```text
expected_knowledge_status:
answer_allowed:
warning_required:
need_additional_info:
missing_information:
expected_action:
expert_reason:
```

## 五、审核完成后的交付

请将填写结果保存为 JSON，并保留 `query_id` 与原问题不变。使用项目校验脚本检查后，才能生成 Boundary Gold v1 和安全边界指标。未完成专家审核前，不得把工程预期字段改名为 Gold。

建议文件名：`siemens_s210_rag_boundary_expert_gold_v1.json`。
