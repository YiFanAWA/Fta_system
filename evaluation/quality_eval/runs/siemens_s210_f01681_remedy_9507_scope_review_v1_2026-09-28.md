# F01681 Remedy `xxxx=9507` 范围复核 v1

日期：2026-09-28  
对象：固定公开语料样本 `SIEMENS_S210_2019_F01681`   
性质：只读来源范围审查；AI 子智能体角色复核 + 本地原文偏移核验。

## 结论

原文在 Remedy 中写明：

> `If xxxx = 9507:`  
> `Set synchronous motor.`

这直接支持的事实仅是：当 `xxxx=9507` 时，手册给出“设置为同步电机”的处理指令。它没有直接说明现场的电机类型当前设置错误，也没有把该现场状态明确表述为顶事件 `Incorrect parameter value` 的独立上游原因。因此：

- `xxxx=9507` 不加入 `FaultRecord.causes` 或现有 cause disposition ledger；
- 不新增 FTA 事件节点或因果边；
- 作为 Remedy 条件分支保留；
- 由于 `xxxx=9507` 出现在 Remedy、但未出现在此前 Cause/Fault value 映射项中，原因/映射集合是否完整仍为 `unresolved`，不能宣称 scope 已闭合。

## 固定来源证据

语料文件：`evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl`  
样本：`SIEMENS_S210_2019_F01681`  
输入文本 SHA-256：`5517c4e678dfa57286a7ae5426e4d40ed7322a4c88241593b6a55d068f0e994b`

| 原文引文 | 0-based 字符范围（end-exclusive） | 用途 |
| --- | ---: | --- |
| `Fault value (r0949, interpret decimal):` | `[211, 250)` | Cause/Fault value 映射区段的起始标识 |
| `Remedy: Correct parameters:` | `[2218, 2245)` | Remedy 区段起始标识 |
| `If xxxx = 9507:\nSet synchronous motor.` | `[2526, 2564)` | 唯一 `xxxx=9507` 条件及其处理指令 |

对 `xxxx = 9507:` 的固定原文检索结果：全文共 1 处；Remedy 标题之前 0 处，Remedy 区段内 1 处。位置由主 agent 对固定语料逐字核验。AI 子智能体没有声称核算字符偏移。

## 独立 AI 角色复核

只读 AI 复核同意：这是条件式处理指令，不是因果陈述或现场状态证据；不能据此把“未设置同步电机”自动连到 F01681；同时，Cause 与 Remedy 的编号范围差异使 cause-set completeness 仍未解决。

该复核不是刘武或其他真人领域专家签署，也不是正式 Gold。它不能回答手册未明示的工程语义。正式 Gold、数据库、生产 API 与 readiness 均未改变，`fta_ready=false`、`production_ready=false`。

结构化账目见同名 JSON。活动基线通过后续 manifest v14 登记；v13 历史文件不覆盖。
