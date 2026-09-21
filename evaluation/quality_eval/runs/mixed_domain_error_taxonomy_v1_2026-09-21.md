# Mixed-Domain Error Taxonomy v1

状态：`provisional_engineering_review`；当前混合评测包含 S210 冻结查询和航空非专家 Dev Query，不能作为生产泛化结论。

## 无 Router 基线

- 实体：321 条（S210 281 + 航空 40）；
- 查询：79 条（S210 39 + 航空 40）；
- Candidate Recall@20：`0.9241`；
- WrongDomain@1：`0.1772`；WrongDomain@3：`0.3418`；WrongDomain@5：`0.3797`；
- DomainPurity@1：`0.8228`；DomainPurity@3：`0.7932`；DomainPurity@5：`0.8127`。

## 按领域

| 领域 | 查询数 | Candidate R@20 | MRR |
|---|---:|---:|---:|
| Siemens S210 | 39 | 1.0000 | 0.8611 |
| Aerospace | 40 | 0.8500 | 0.4785 |

## 判断

无 Router 的混合索引确实存在跨域污染，且主要伤害航空低信息量的组件/状态查询。这个结果足以支持下一轮“无 Router vs metadata scope”的对照实验，但还不足以直接决定实现 Domain Router。

下一轮保持数据、模型和查询不变，只增加显式领域范围对照；如果 scope 能消除污染，再评估是否需要真正的 Query → Domain/System Router。
