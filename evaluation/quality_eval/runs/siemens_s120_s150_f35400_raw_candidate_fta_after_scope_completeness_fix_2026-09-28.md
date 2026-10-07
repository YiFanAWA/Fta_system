# Candidate FTA 原始公开文本端到端开发探针

- 样本：`SIEMENS_S120_S150_2023_F35400_P3271_N001`
- 故障码：`F35400`
- 来源：SINAMICS S120/S150 List Manual（11/2023），PDF 页 3271–3271
- 原文字符数：1643
- 模型阶段：fault_extraction, cause_disposition, structure_decomposition, gate_assessment
- 请求尝试：4；成功响应：4
- 抽取：`success`，1 条记录
- 原因处置：`{"fta_event_candidate": 2}`
- 候选结果：`proposed`；树=True；节点=3
- 抽取证据：18 条，offset 精确=True，源文重复短引文数=4（以明确 offset 定位，不要求引文在全文唯一）
- 树证据：5 条，offset 精确=True，引文唯一=True

## 门与阻断

- `at_least_one_of_following`：unknown，子项 2；阻断：gate_confidence_policy_unavailable

## 解释边界

这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。
