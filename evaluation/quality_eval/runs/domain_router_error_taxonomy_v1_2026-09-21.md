# Domain Router Error Taxonomy v1

总查询：79；cross_domain：22；scoped：57。
本报告是诊断结果，不自动修改 Router 规则；所有逐条分类仍需要人工确认。

## 分类统计

| 分类 | 数量 | 预期动作 |
|---|---:|---|
| A missing_router_signal | 4 | 作为 Router v2 候选，但先人工确认 |
| B domain_ambiguous | 2 | 保持 cross_domain 或请求澄清 |
| C query_insufficient | 16 | 先请求补充信息 |
| false_scoped | 0 | 必须阻断 Router scope |

## 逐条分类

| Query | 期望领域 | 分类 | 当前信号 | 说明 |
|---|---|---|---|---|
| S210-FT007 | industrial_drive | A_missing_router_signal | cu | contains a diagnostic high-signal term but current Router returned cross_domain |
| S210-FT008 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT009 | industrial_drive | B_domain_ambiguous | ram | contains technical vocabulary that is not unique to one domain |
| S210-FT010 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT011 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT013 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT014 | industrial_drive | B_domain_ambiguous | 24/48 | contains technical vocabulary that is not unique to one domain |
| S210-FT015 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT016 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT017 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT019 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT020 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT021 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT022 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT023 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT027 | industrial_drive | A_missing_router_signal | sensor module | contains a diagnostic high-signal term but current Router returned cross_domain |
| S210-FT029 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT030 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT031 | industrial_drive | A_missing_router_signal | si motion | contains a diagnostic high-signal term but current Router returned cross_domain |
| S210-FT032 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT038 | industrial_drive | C_query_insufficient | 无 | contains no diagnostic domain cue in the analysis-only vocabulary |
| S210-FT039 | industrial_drive | A_missing_router_signal | sto | contains a diagnostic high-signal term but current Router returned cross_domain |

## 边界

- A/B/C 是错误分析标签，不是 Gold 领域标注，也不是线上规则。
- 当前报告未发现 false_scoped；但这不等于 Router 已通过生产门禁。
- 只有 A 经人工确认后，才允许进入 Router v2 设计；B/C 不应靠增加词表强行 scope。
