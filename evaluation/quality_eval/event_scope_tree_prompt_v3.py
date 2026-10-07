"""Versioned evaluation-only prompt with gate scopes as the sole hierarchy source."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "event-scope-text-only-tree-v3-gate-scopes-canonical"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build the next offline-testable prompt; this module performs no API call."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "仅依据输入中的顶事件和原文，生成可审核的单顶事件候选结构；不看图、不用外部知识。"
        "只在原文直接支持时建立节点、组合和门型；时间先后、并列罗列、工程常识及单独出现的 and/or 字样，"
        "都不能自动证明逻辑门。证据或作用域不清时使用 unknown/unresolved，不得猜测。\n"
        "层级合同：gate scopes 是父子层级的唯一事实来源。每个 scope 用 output_node_id 和 child_node_ids 表示"
        "直接父子关系；scope 输出节点可在更高层作为 child，从而表达嵌套。每个门 scope 必须有至少两个不同的直接 child；"
        "不得让同一个输出节点拥有多个门 scope。禁止输出 parent_id 或任何第二套父子关系。"
        "一个节点不得在不同 scope 中拥有多个直接父节点；不得把同一复合分支的原子子项同时列为根 scope 的直接 child。"
        "若不能形成一致的单根层级，保留可定位节点、将 structure_status 设为 unresolved，并明确 unresolved_questions；"
        "存在层级/引用/作用域 blocker 时不得标 complete。"
        "不要自动修复、摊平或重复挂接节点。\n"
        "例如原文明确表达 (A AND B) OR (C AND D) 时，根 OR 的直接子项应是两个分支输出事件；"
        "再分别用局部 scope 表达每个分支的子项。若文本不能直接授权某个局部门，保留该 scope 为 unknown，"
        "但仍须准确表达其候选层级和完整 child set。\n"
        "每个节点和每个门 scope 都要有原文连续引文；不得把引用存在误当成语义支持。输出严格 JSON，不输出推理过程：\n"
        '{"structure_status":"complete|unresolved",'
        '"nodes":[{"id":"E1","text":"...",'
        '"type":"top_event|intermediate_event|basic_event|undeveloped_event",'
        '"evidence_quote":"...或null"}],'
        '"gates":[{"scope_id":"S1","output_node_id":"E1",'
        '"child_node_ids":["E2","E3"],"gate":"AND|OR|unknown",'
        '"evidence_quote":"...或null","reason":"..."}],'
        '"unresolved_questions":[]}\n输入 JSON：\n'
        + payload
    )
