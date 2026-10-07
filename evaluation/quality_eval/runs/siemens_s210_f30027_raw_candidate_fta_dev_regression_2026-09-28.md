# Candidate FTA 原始公开文本端到端开发探针

- 样本：`SIEMENS_S210_2019_F30027`
- 故障码：`F30027`
- 来源：SINAMICS S210 servo drive system with SIMOTICS S-1FK2 and S-1FT2（None），PDF 页 500–502
- 原文字符数：3693
- 模型阶段：fault_extraction, cause_disposition, structure_decomposition, gate_assessment
- 请求尝试：4；成功响应：4
- 抽取：`success`，1 条记录
- 原因处置：`{"exclude_from_tree": 1, "fta_event_candidate": 5, "unresolved": 4}`
- 候选结果：`blocked`；树=True；节点=8
- 抽取证据：25 条，offset 精确=True，源文重复短引文数=4（以明确 offset 定位，不要求引文在全文唯一）
- 树证据：11 条，offset 精确=True，引文唯一=True

## 门与阻断

- `unknown_cause_list`：unknown，子项 5；阻断：cause_set_incomplete_or_not_leaf_normalized, gate_confidence_policy_unavailable
- `OR`：unknown，子项 2；阻断：gate_confidence_policy_unavailable

## 解释边界

这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。
