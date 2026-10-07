# Candidate FTA 门评估提示：外部原文证据回归 v1

日期：2026-09-28（Asia/Shanghai）  
用途：开发/错误分析；不是 Gold，不进入数据库，不改变 readiness。  
机器结果：[JSON artifact](candidate_fta_gate_text_evidence_probe_v1_2026-09-28.json)

## 问题与范围

检查当前候选 FTA 的门评估阶段能否根据原始手册叙述，在明确直接证据时提出 AND/OR，并在证据不足时保留 `unknown`。

评测复用生产代码中的 `build_candidate_fta_gate_assessment_prompt`、概率格式校验和唯一原文引文绑定。11 个图示案例的父事件与直接子事件固定；输入模型的只有事件文本和经来源页核对的手册摘录。预期标签、审核者的 `supports` 解释及总结理由没有传给模型。DeepSeek Flash，temperature=0，每个样例一次请求、无重试。

这不是整个 Candidate FTA Pipeline 的端到端测试：没有运行 raw-text 故障抽取、原因语义处置、递归节点结构生成、完整原因集判定、连通性验证或数据库/API 写入。

## 结果

11 个样例全部与本轮 AI 原文证据复核标签描述性一致；请求及响应合同没有失败。

| 指标 | 结果 |
| --- | ---: |
| 总体标签一致 | 11/11 |
| 文本支持的确定门型一致 | 9/9 |
| `unknown` 弃判一致 | 2/2 |
| AND / OR / unknown 标签数 | 4 / 5 / 2 |
| 决定性引文唯一、位于输入 scope | 9/9 |
| 模型请求失败 | 0/11 |

| 样本 | 参考标签 | 模型输出 | 引文检查 |
| --- | --- | --- | --- |
| Q01 | unknown | unknown | 未给门型引文 |
| Q02 | unknown | unknown | 未给门型引文 |
| Q03 | OR | OR | 通过；子标签与原文类别为缩写映射 |
| Q04 | OR | OR | 通过 |
| Q05 | AND | AND | 通过；使用同页精确短引文 |
| Q06 | AND | AND | 通过 |
| Q07 | AND | AND | 通过 |
| Q08 | OR | OR | 通过 |
| Q09 | OR | OR | 通过 |
| Q10 | AND | AND | 通过 |
| Q11 | OR | OR | 通过 |

模型对已知门型自报的 Top 分数范围是 0.90–0.99；两个 unknown 都给出 1.0。该分数是未经校准的门型自评，不能解释成事件发生概率或生产置信度。

## 来源核验与异常

三份输入 PDF 的 SHA-256 与源文档证据审查 artifact 一致；每条提供给模型的引文均在所指 PDF 页找到。FAA Q05 原审查长引文中的 AND 引号在 PDF 文本层编码异常，因此评测输入改用同页逐字可定位的句子：`That is, both must fail for the engine to fail.` 它直接表达“两者都必须失效”，没有将参考门标签文字注入提示。

pypdf 读取 DOE PDF 时报告重复 `/Length` 字典键警告；文件哈希、页码范围及引用文本校验均通过。该警告属于 PDF 来源解析限制，保留记录，不静默屏蔽。

## 解释与限制

1. 11 条来自 3 个完整文档簇且为有目的选择，不是代表性抽样；标签是 AI 对原文的证据审核，不是领域专家 Gold。
2. 本次验证的是固定节点结构下的 gate assessment 阶段，不证明抽取、完整树结构或真实故障系统泛化。
3. Q03 的图示子节点是缩写类别，原文支持其高层原因类别，但不能由此推断这些分支下层门型。
4. 当前 `CandidateFtaExtractionService` 未注入 `GateConfidencePolicy` 时，`_select_gate` 仍因 `gate_confidence_policy_unavailable` 失败关闭为 `unknown`。因此本次 9/9 是模型原始类别偏好表现，不是系统最终接受门型 9/9。
5. 没有选择/校准阈值，没有修改冻结 baseline manifest v6、Gold、数据库、API、生产策略或就绪标记。`fta_ready=false`、`production_ready=false` 保持。

## 复现与验证

```powershell
python -m unittest discover -s backend-python/tests -p "test_*candidate_fta*.py" -q
python -m unittest discover -s evaluation/quality_eval -p "test_probe_candidate_fta_gate_text_evidence_v1.py" -q
python evaluation/quality_eval/public_sources/probe_candidate_fta_gate_text_evidence_v1.py
python evaluation/quality_eval/build_fta_baseline_manifest_v6.py --check
python evaluation/quality_eval/validate_fta_baseline_manifest.py
```

本轮结果：候选 FTA 固定测试 33 项通过；本探针合同测试 5 项通过；manifest v6 为 `current`（84 artifacts），validator `valid`（84/84）。模型运行 artifact 保留逐条概率、引用、理由、提示摘要和失败列表。
