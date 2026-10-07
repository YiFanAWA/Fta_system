"""Evaluation-only prompt candidate for evidence-bound event-scope gate decisions."""

from __future__ import annotations

import hashlib
from typing import Any

from evaluation.quality_eval.event_scope_tree_prompt_v6 import build_prompt as build_prompt_v6


PROMPT_VERSION = "event-scope-text-only-tree-v7-bound-logic-evidence"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build v6's label-free prompt with stricter gate-to-evidence binding rules."""
    base_prompt = build_prompt_v6(model_input)
    marker = "输出严格 JSON，不输出推理过程：\n"
    if base_prompt.count(marker) != 1:
        raise ValueError("v6 prompt structure changed; v7 insertion point is no longer unique")

    binding_rules = (
        "已知门型与逻辑证据绑定（v7重点）：只有在同一个 gate scope 内，原文直接支持"
        "该 scope 的全部 child 之间的 AND/OR 关系，并支持这个 child 组合或替代路径指向该 scope 的 output_node_id，"
        "才可输出 gate=AND 或 gate=OR。logic_evidence 必须是一段来自指定 source segment 的连续原文，"
        "应足以核对 child 关系和共同 output；优先引用完整因果命题，不得只引用孤立的 and/or、条件词或局部并列短语。"
        "scope_evidence 只能证明该组事件属于这个 output 的范围，不能代替 logic_evidence 对门逻辑的直接支持。"
        "例如，‘either pathway A or pathway B can lead to T’明确把两个替代路径连到同一 T，可提出 OR，"
        "logic_evidence 应覆盖这条完整关系；‘T occurs only when A and B are both present’或等价的明确共同条件可提出 AND。"
        "相反，‘A and B were both observed before T’或‘A and B were both recorded during the incident’只说明共现；"
        "‘A or B’若未说明它们如何共同指向当前 output，或‘A or B may occur; C can lead to T’这类连接词与当前 output 无关；"
        "或引用只包含连接词而缺少 child/output 关系，均不得据此确定门型，应保持 unknown 并给出允许的 unknown_reason。"
        "不能把 may/can/if/and/or 等单个词直接当作门型标签；必须判断完整命题表达的逻辑关系。"
        "若一段连续原文不能同时支持当前 scope 的 child 逻辑和 output 关系，不得拼接引文、跨 scope 借证或推断补齐；"
        "应保持 unknown。该规则只生成待审核的文本证据候选，不表示专家批准或最终 Gold。\n"
    )
    return base_prompt.replace(marker, binding_rules + marker, 1)


def prompt_sha256(model_input: dict[str, Any]) -> str:
    """Return a deterministic digest for offline review/preflight artifacts."""
    return hashlib.sha256(build_prompt(model_input).encode("utf-8")).hexdigest()
