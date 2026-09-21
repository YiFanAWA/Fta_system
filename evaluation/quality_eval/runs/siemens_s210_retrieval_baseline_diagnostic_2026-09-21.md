# Siemens S210 检索基线诊断报告

本报告使用字符 n-gram TF-IDF，仅用于检索诊断，不代表生产 embedding、reranker 或最终 RAG 指标。
排名单位为 `fault_code`，每个查询只要 Top-K 命中任一 `relevant_fault_codes` 即算命中。

| 版本 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| baseline_a_full_record | 0.2381 | 0.2857 | 0.3333 | 0.4286 | 0.2937 |
| baseline_b_description_cause | 0.0714 | 0.0952 | 0.1190 | 0.2143 | 0.1139 |
| baseline_c_hybrid | 0.3095 | 0.3810 | 0.4048 | 0.5000 | 0.3729 |

## 解读边界

- 这是 42 条派生中文查询上的可复现实验，不是人工查询金标。
- 不能根据该报告直接宣布生产检索效果，也不能据此修改 Gold。
- 后续应接入真实多语言 embedding，并加入按 fault_code 聚合后的 reranker。
