# Candidate FTA 原始公开文本端到端开发探针

- 样本：`SIEMENS_S120_S150_2023_F06000_P2792_N001`
- 故障码：`F06000`
- 来源：SINAMICS S120/S150 List Manual（11/2023），PDF 页 2792–2793
- 原始 PDF：`SINAMICS_S120_S150_List_Manual_11-2023_EN.pdf`；章节：`4.2 List of faults and alarms`；PDF SHA-256：`f7684038621ae9faaedbed1780e23c48775c19d76ae0fbd0adce268d69f489f4`
- 原文字符数：2529
- 模型阶段：fault_extraction, cause_disposition, structure_decomposition, gate_assessment
- 请求尝试：4；成功响应：4
- 抽取：`success`，1 条记录
- 原因处置：`{"fta_event_candidate": 11}`
- 候选结果：`proposed`；树=True；节点=15
- 抽取证据：26 条，offset 精确=True，源文重复短引文数=3（以明确 offset 定位，不要求引文在全文唯一）
- 树证据：21 条，offset 精确=True，引文唯一=True

## 门与阻断

- `top_event_scope`：not_applicable，子项 1；阻断：无
- `causal_condition`：not_applicable，子项 1；阻断：无
- `or_candidate`：unknown，子项 10；阻断：gate_confidence_policy_unavailable
- `or_candidate`：unknown，子项 2；阻断：gate_confidence_policy_unavailable

## 解释边界

这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。
