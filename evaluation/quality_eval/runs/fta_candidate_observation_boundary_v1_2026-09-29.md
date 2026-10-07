# Candidate FTA 观察共现边界受控运行

- 案例：`OBSERVATION-COOCCURRENCE-001`（合成、非 Gold）
- 运行状态：`response_received`；候选树：`blocked`
- 模型请求：1；SDK 自动重试：0；外层重试：0
- 观察节点分开保留：False
- 观察节点均断开：False
- Gate scope 接触观察节点：False
- Relation 接触观察节点：False
- 规则匹配：False

## 边界说明

此运行仅验证生产 Candidate FTA 三阶段服务对一条合成共现输入的行为；不读取 Gold/参考标签，不写数据库或生产 API。它不是专家审核、准确率或泛化成绩。模型失败或政策不匹配时保留响应，不自动修复或重试。
