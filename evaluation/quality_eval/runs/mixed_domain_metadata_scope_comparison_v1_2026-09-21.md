# Mixed-Domain Metadata Scope Comparison v1

这是使用评测集已知领域标签的 oracle scope 对照，不是生产 Domain Router。

| 阶段 | R@1 | R@3 | R@5 | R@10 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Oracle metadata scope | 0.5949 | 0.6582 | 0.6709 | 0.8101 | 0.9241 | 0.6515 |

| 指标 | 值 |
|---|---:|
| WrongDomain@1 | 0.0000 |
| WrongDomain@3 | 0.0000 |
| WrongDomain@5 | 0.0000 |

## 解释

scope 将跨域污染强制降为 0，只能证明“领域边界有效”，不能证明领域识别器已经实现。还需要下一轮比较真实的 Query → Domain/System 分类器或 Router。
