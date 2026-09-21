# Aerospace Generic Retrieval Error Taxonomy v2

状态：`provisional_engineering_review`。当前航空 Dev Query 为模板派生集，不是专家相关性标注。

## 当前结果

- 40 条查询；
- Candidate Recall@20：`0.8500`；
- Reranked R@1：`0.8000`；
- 6 条候选池漏召回；2 条进入候选池但未排到 Top1；
- 本轮不修改 Common Schema、Adapter Contract 或 Generic Pipeline。

## 按充分性分层

| Query sufficiency | 数量 | Candidate R@20 | Reranked R@1 | Reranked MRR |
|---|---:|---:|---:|---:|
| `sufficient` | 24 | 1.0000 | 1.0000 | 1.0000 |
| `partially_sufficient` | 10 | 0.7000 | 0.7000 | 0.7000 |
| `insufficient` | 6 | 0.5000 | 0.1667 | 0.3333 |

## 暂定分类

| 查询 | 类型 | 暂定类别 | 判断 |
|---|---|---|---|
| AERO-Q022 / Q024 | component | `retrieval_role` | 组件单独查询缺少机型/JASC 上下文；组件当前只进入 metadata/reranker。 |
| AERO-Q027 | condition | `retrieval_role` | CHAFED 只作为状态/症状出现，当前没有独立 condition dense 通道。 |
| AERO-Q028 / Q029 / Q030 / Q031 / Q032 | condition | `query_ambiguity` | FAILED/BROKEN/MAKING METAL 等低信息状态词缺少实体区分上下文。 |

## 决定

1. 不恢复全局 component boost。
2. 先做 enriched-query sufficiency 实验，再判断是查询不足还是需要新的 Adapter retrieval role。
3. 继续保持 Generic v1、Common Schema v1、Adapter Contract v1 冻结。
4. 下一项实验是 Siemens + Aerospace 无 Router 混合索引，并测 WrongDomain@K / DomainPurity@K。
