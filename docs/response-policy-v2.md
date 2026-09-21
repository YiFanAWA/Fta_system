# Response Policy v2

## 目标

v2 将回答策略从一个三分类名称，收紧为可直接被 RAG Answer 层消费的结构化合同：

```json
{
  "policy": "P1_ANSWER_WITH_WARNING",
  "answer_allowed": true,
  "confidence_level": "medium",
  "need_additional_info": true,
  "warning_required": true,
  "retrieval_policy": "allow"
}
```

实现 owner：`backend-python/response_policy.py` 的 `ResponsePolicyLayer.decide_v2()`。

## 三档合同

| policy | answer_allowed | confidence | need_additional_info | warning_required | 用途 |
|---|---:|---|---:|---:|---|
| `P0_DIRECT_ANSWER` | true | high | false | false | 信息足够，正常给出有证据回答 |
| `P1_ANSWER_WITH_WARNING` | true | medium | true | true | 继续回答，但降低确定性并提示补充信息 |
| `P2_ASK_BEFORE_DEFINITIVE_ANSWER` | false | low | true | false | 可以检索候选帮助澄清，但不输出确定性结论 |

`retrieval_policy` 在三档中都为 `allow`。v2 仍然不能控制 Retrieval scope、RRF、Reranker 或候选池。

## Gold 状态

由 `response_policy_gold_v1.json` 规范化生成：
`evaluation/quality_eval/runs/response_policy_gold_v2.json`。

当前专家审核数据只有：

- P0：9 条；
- P1：70 条；
- P2：0 条。

因此 P2 合同目前是结构和行为定义，尚未得到真实专家正例的精度/召回验证。

## 验收边界

- 不重新训练 embedding、LLM 或 Reranker；
- 不改变 Rule Router v1 和 Retrieval 结果；
- 不把 v2 Gold 当作 Siemens 领域事实金标；
- 需要新的低信息查询并由专家审核后，才能评估 P2；
- 真实回答正确性进入独立的 RAG Semantic Evaluation，不由 Policy Accuracy 代替。
