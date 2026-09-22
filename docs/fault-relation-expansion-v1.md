# Siemens S210 Fault Relation Expansion v1

## 定位

本模块用于补足 RAG 回答中的“配对故障/消息码”和“共享参数关联”展示能力。它位于检索与重排之后、答案生成之前：

```text
Query
  ↓
Rule Router v1
  ↓
Retrieval / Reranker
  ↓
Fault Relation Expansion  ← 本模块
  ↓
Evidence-bound RAG Answer
```

本轮不修改 embedding、Hybrid Retrieval、Reranker、Router、候选池或既有 281 条 Fault Gold。运行注册表不是关系语义的唯一真源；关系语义现在由独立的 `Fault Relation Gold v1` 管理。它仍不是因果关系 Gold，也不是自动 FTA 建树。

## 关系 Gold 真源

正式关系 Gold：`evaluation/quality_eval/datasets/siemens_s210_fault_relation_gold_v1.json`。

该版本只覆盖已经由刘武专家复审的 5 条**无方向关联关系**：

- `paired_fault_message`：配对故障/消息码或同描述消息关系；
- `shared_parameter`：两个故障记录共同出现同一参数的关联关系。

Gold 明确标记 `causal_relations_complete=false` 和 `logic_gates_complete=false`。因此任何消费者都不能把这些关系解释为 `causes`、`leads_to`、AND 或 OR。

运行注册表 `evaluation/quality_eval/datasets/siemens_s210_fault_relation_registry_v1.json` 是 API 运行投影，必须通过 `validate_siemens_s210_fault_relation_gold.py` 与 Gold 对账后才可使用。

## 当前关系注册表

注册表：`evaluation/quality_eval/datasets/siemens_s210_fault_relation_registry_v1.json`

当前包含 5 条由刘武专家在 RAG 语义审核中确认的关系：

| 关系 | 类型 | 触发信息 | 关系证据 |
|---|---|---|---|
| A01693 ↔ F01679 | `paired_fault_message` | `Safety parameters have been changed` | 两条记录的 cause evidence |
| A01706 ↔ F01682 | `shared_parameter` | `p9506` | 两条记录的 parameter evidence |
| A01707 ↔ A30707 | `paired_fault_message` | `p9530` | 相同 description + 参数 evidence |
| A01709 ↔ A30709 | `paired_fault_message` | `p9553` | 相同 description + 参数 evidence |
| A01711 ↔ A30711 | `paired_fault_message` | `r9725` | 相同 description + 参数 evidence |

这 5 条已由刘武专家完成定向复审，当前状态为 `expert_validated`。5 条关系的完整性、类型、证据支持均通过，且均确认不存在无依据的参数语义扩展。

## 实现边界

- `backend-python/fault_relation_expansion.py`：读取关系注册表、按问题触发关系、解析关联故障上下文，并且只保留能在当前 Fault evidence 中解析到的关系证据。
- `backend-python/rag_contract.py`：增加 `FaultRelationEvidence`、`FaultRelation`，并在 `FaultContext` / `RagResponse` 中暴露关系结果。
- `backend-python/rag_service.py`：在候选加载后做关系扩展，将关联故障和关系证据加入生成上下文；不改变召回候选排名。
- `backend-python/api_server.py` / `backend-python/config.py`：为 S210 RAG 服务加载关系注册表。

关系层的安全约束：

1. 只有当前主故障属于注册关系，且用户问题命中已登记触发信息时才尝试扩展。
2. 关联故障必须已经在现有候选上下文中解析到，避免关系层暗中改变召回结果。
3. 每条关系至少保留一条能回溯到原始 Fault evidence 的引用。
4. 未被原文支持的参数含义不得由关系层补写；尤其 `r9725` 只能说明其在两条记录中出现，不能擅自扩大具体语义。
5. 注册表缺失或不可解析时，基础 RAG 继续可用；关系扩展失败不能让基础回答整体失败。

## 定向回归结果

脚本：`evaluation/quality_eval/public_sources/run_siemens_s210_relation_targeted_regression.py`

本轮复用原 30 条评测的 Retrieval / Reranker / Router 结果，只重新生成 5 条被专家指出关系展示不足的回答：RAG-021、RAG-027、RAG-028、RAG-029、RAG-030。

结果：

| 指标 | 结果 |
|---|---:|
| 定向样本 | 5 |
| 故障码合同命中 | 1.0000 |
| 引用有效性 | 1.0000 |
| 引用归属对齐 | 1.0000 |
| 答案合同通过率 | 1.0000 |

产物：

- 回答：[siemens_s210_fault_relation_targeted_regression_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_fault_relation_targeted_regression_v1_2026-09-21.json)
- 自动合同报告：[siemens_s210_fault_relation_targeted_contract_report_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_fault_relation_targeted_contract_report_v1_2026-09-21.json)

这里的 1.0000 只证明结构合同和证据链没有回归，不代表 5 条关系已经获得专家最终通过。

## 专家定向复审结果

专家已填写并通过的结果：

- 原始待审清单：[siemens_s210_fault_relation_targeted_expert_review_v1_2026-09-21.md](../evaluation/quality_eval/runs/siemens_s210_fault_relation_targeted_expert_review_v1_2026-09-21.md)
- 正式 JSON 结果：[siemens_s210_fault_relation_expert_review_v1_2026-09-21.json](../evaluation/quality_eval/runs/siemens_s210_fault_relation_expert_review_v1_2026-09-21.json)
- 正式文本报告：[siemens_s210_fault_relation_expert_review_v1_2026-09-21.md](../evaluation/quality_eval/runs/siemens_s210_fault_relation_expert_review_v1_2026-09-21.md)

专家只复审了 5 条，不需要重做全部 30 条。结果为 5/5 `pass`，因此关系注册表可以作为 RAG Answer 的正式关系层配置使用；这不等同于已经完成因果关系 Gold、AND/OR 标注或自动 FTA 建树验收。

## Gold 校验

校验脚本：`evaluation/quality_eval/public_sources/validate_siemens_s210_fault_relation_gold.py`。

校验内容包括：关系端点唯一性、关系类型、无方向约束、逐条证据引用、专家结论，以及 Gold 与运行注册表的一致性。校验产物：`evaluation/quality_eval/runs/siemens_s210_fault_relation_gold_v1_validation_2026-09-22.json`。

## 下一步边界

当前可以继续做：

- 将 5 条已通过关系作为 `Fault Relation Gold v1` 的正式关联关系基线。
- 建立独立的因果关系候选清单，由专家逐条判断因果方向、证据和是否可进入 FTA。
- 因果关系审核通过后，再建立 AND/OR Logic Gold；两者都不能由当前 5 条关联关系自动推导。

当前不应做：

- 把关系注册表直接当作完整 FTA 因果图。
- 根据“共享参数”自动推断因果方向或 AND/OR 门。
- 修改 Retrieval 以追求这 5 条定向样本的分数。

只有关系 Gold、关系证据和 AND/OR 标注分别完成后，才进入自动建树验收。
