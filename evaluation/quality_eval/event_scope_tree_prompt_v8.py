"""Evaluation-only prompt candidate for semantic, evidence-bound gate interpretation."""

from __future__ import annotations

from typing import Any

from evaluation.quality_eval.event_scope_tree_prompt_v7 import build_prompt as build_prompt_v7


PROMPT_VERSION = "event-scope-text-only-tree-v8-semantic-gate-evidence"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build v7's label-free prompt with explicit semantic-not-keyword interpretation."""
    base_prompt = build_prompt_v7(model_input)
    marker = "输出严格 JSON，不输出推理过程：\n"
    if base_prompt.count(marker) != 1:
        raise ValueError("v7 prompt structure changed; v8 insertion point is no longer unique")

    semantic_rules = (
        "逻辑门按语义判断，不按关键词匹配（v8重点）：原文不必出现字面 ‘OR’/‘AND’、‘or’/‘and’ 或固定连接词；"
        "可以依据完整因果命题的语义识别替代路径或共同必要条件，即使作者用了不同句式。"
        "例如，原文若分别说明路径 A 能导致同一顶事件 T，并说明另一条独立路径 B 也能导致 T，"
        "即使没有写 ‘or’，语义明确时也可提出 OR；原文若表达 T 仅在 A 与 B 同时成立时发生，"
        "即使没有写 ‘and’，语义明确时也可提出 AND。上述例子仅用于说明语义，不是封闭词表或关键词规则。"
        "logic_evidence 仍必须直接支持该语义：它应以连续原文覆盖相关 child 命题、它们是替代路径或联合条件的关系、"
        "以及它们共同指向当前 scope 的同一 output。不能只因多个原因被列出就假设 OR，也不能只因多个事件出现在同一事故中就假设 AND。"
        "若原文只是列举可能因素、分散提及事件、只说明相关性，或无法确定单个替代路径是否能通向该 output，"
        "即使常识上‘像’某种门，也必须保持 unknown。不得把跨段落非连续内容拼成一条逻辑证据；语义仍有实质歧义时使用允许的 unknown_reason。"
        "模型应解释并绑定原文表达的逻辑含义，而不是寻找显式运算符；任何门型都仍是待审核候选，不代表专家批准或 Gold。\n"
    )
    return base_prompt.replace(marker, semantic_rules + marker, 1)
