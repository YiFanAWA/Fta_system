# Candidate FTA 原始公开文本端到端开发探针

- 样本：`SIEMENS_S210_2019_F30021`
- 故障码：`F30021`
- 来源：SINAMICS S210 servo drive system with SIMOTICS S-1FK2 and S-1FT2（None），PDF 页 498–499
- 原始 PDF：`S210_Manual_2019.pdf`；章节：`15.2 List of faults and alarms`；PDF SHA-256：`4e32930c2c86300b3699ce9ef321948bf7d40065775944e90d6ed19b11c588cd`
- 原文字符数：736
- 模型阶段：fault_extraction, cause_disposition, structure_decomposition, gate_assessment
- 请求尝试：4；成功响应：4
- 抽取：`success`，1 条记录
- 模型提议处置（原始响应）：`{"fta_event_candidate": 4, "relation_only": 1}`
- 宿主最终处置（含证据门禁规范化）：`{"fta_event_candidate": 3, "relation_only": 1, "unresolved": 1}`
- 候选结果：`blocked`；树=True；节点=4
- 抽取证据：16 条，offset 精确=True，源文重复短引文数=5（以明确 offset 定位，不要求引文在全文唯一）
- 树证据：5 条，offset 精确=True，引文唯一=False
- 原因处置账证据：4 条，offset 精确=True，引文唯一=True；未决且无证据 1 项

## 门与阻断

- 再核验说明：Offline re-audit only: response stages were classified from response contracts; extraction spans are checked by exact offsets, while uniqueness is required only for candidate-tree quotations. No model call was made.

- `possible_causes_enumeration`：unknown，子项 3；阻断：cause_set_incomplete_or_not_leaf_normalized, gate_confidence_policy_unavailable

## 解释边界

这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。

本次调用约束：最多 4 次；外层重试 0 次；SDK 重试 0 次；预算耗尽=False。
