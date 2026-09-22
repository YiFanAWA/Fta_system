# Siemens S210 Fault Relation Gold v1

## 当前结论

`Fault Relation Gold v1` 已完成第一阶段：5 条关联关系均由刘武专家复审通过，证据和运行注册表已对账。

它可以支持：

- RAG 回答中展示配对故障/消息码；
- 参数查询返回共享参数关联的故障集合；
- 对关联证据进行逐条引用和回溯。

它不能支持：

- 推断故障因果方向；
- 自动判断 AND/OR；
- 直接生成可信 FTA 故障树。

## Gold 与运行层

| 层 | 文件 | 职责 |
|---|---|---|
| 语义真源 | `evaluation/quality_eval/datasets/siemens_s210_fault_relation_gold_v1.json` | 记录专家确认的关联关系、方向、关系类型和证据 |
| 运行投影 | `evaluation/quality_eval/datasets/siemens_s210_fault_relation_registry_v1.json` | 给 RAG Relation Expansion 加载 |
| 对账校验 | `evaluation/quality_eval/public_sources/validate_siemens_s210_fault_relation_gold.py` | 检查 Gold 与运行投影一致 |
| API 展示 | `backend-python/rag/fault_relation_expansion.py` | 只扩展已登记、已命中、证据可解析的关联关系 |

## 关系范围

当前只有两类关系：

- `paired_fault_message`：配对故障/消息码或同描述消息关系；
- `shared_parameter`：两个记录共同出现参数的无方向关联关系。

所有关系都使用 `direction=undirected`。`shared_parameter` 只证明共同出现，不证明一个故障导致另一个故障。

## 验收结果

- 关系数量：5；
- 专家审核：5/5 `pass`；
- 关系证据：5/5 `supported`；
- Gold/运行注册表：一致；
- 因果关系：未完成；
- AND/OR 逻辑门：未完成。

验证命令：

```powershell
python evaluation/quality_eval/public_sources/validate_siemens_s210_fault_relation_gold.py `
  --gold evaluation/quality_eval/datasets/siemens_s210_fault_relation_gold_v1.json `
  --registry evaluation/quality_eval/datasets/siemens_s210_fault_relation_registry_v1.json `
  --output evaluation/quality_eval/runs/siemens_s210_fault_relation_gold_v1_validation_2026-09-22.json
```

## 下一阶段

下一阶段已建立 `Causal Relation Candidate Bundle v1`，详见 `docs/causal-relation-gold-v1.md`。当前只生成待专家确认的候选，不把候选自动写入运行注册表。

每条候选至少需要专家确认：

- source 和 target 是否为可区分的故障实体/原因节点；
- 是否存在明确因果证据；
- 因果方向是 `source_to_target` 还是不能判断；
- 是否只能标记为关联而不能标记为因果；
- 是否允许进入 FTA 节点和边集合。

只有因果关系 Gold 和 AND/OR Gold 都通过专家审核后，才允许进入自动建树验收。
