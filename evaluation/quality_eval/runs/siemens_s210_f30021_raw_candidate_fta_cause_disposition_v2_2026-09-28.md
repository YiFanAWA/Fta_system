# Candidate FTA 原始公开文本端到端开发探针

- 样本：`SIEMENS_S210_2019_F30021`
- 故障码：`F30021`
- 来源：SINAMICS S210 servo drive system with SIMOTICS S-1FK2 and S-1FT2（None），PDF 页 498–499
- 原始 PDF：`S210_Manual_2019.pdf`；章节：`15.2 List of faults and alarms`；PDF SHA-256：`4e32930c2c86300b3699ce9ef321948bf7d40065775944e90d6ed19b11c588cd`
- 原文字符数：736
- 模型阶段：fault_extraction, cause_disposition, structure_decomposition, gate_assessment
- 请求尝试：4；成功响应：4
- 抽取：`success`，1 条记录
- 原因处置：`{"fta_event_candidate": 4}`
- 候选结果：`blocked`；树=True；节点=5
- 抽取证据：12 条，offset 精确=True，源文重复短引文数=3（以明确 offset 定位，不要求引文在全文唯一）
- 树证据：6 条，offset 精确=True，引文唯一=False

## 门与阻断

- `possible_causes_enumeration`：unknown，子项 4；阻断：gate_confidence_policy_unavailable

## 解释边界

这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。
