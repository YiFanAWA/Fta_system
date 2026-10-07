"""Evaluation-only prompt for evidence-located, gate-scope-canonical FTA trees."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "event-scope-text-only-tree-v4-located-evidence"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build a prompt from the validated, label-free packet projection."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "仅依据输入中的顶事件和原文，生成可审核的单顶事件候选结构；不看图、不用外部知识。"
        "只在原文直接支持时建立节点、组合和门型；时间先后、并列罗列、工程常识及单独出现的 and/or 字样，"
        "都不能自动证明逻辑门。证据或作用域不清时使用 unknown/unresolved，不得猜测。\n"
        "层级合同：gate scopes 是父子层级的唯一事实来源。每个 scope 用 output_node_id 和 child_node_ids 表示"
        "直接父子关系；scope 输出节点可在更高层作为 child，从而表达嵌套。每个门 scope 至少有两个不同的直接 child；"
        "不得让同一个输出节点拥有多个门 scope。禁止输出 parent_id 或任何第二套父子关系。"
        "一个节点不得在不同 scope 中拥有多个直接父节点；不得把同一复合分支的原子子项同时列为根 scope 的直接 child。"
        "若不能形成一致的单根层级，保留可定位节点、将 structure_status 设为 unresolved，并明确 unresolved_questions；"
        "存在层级/引用/作用域 blocker 时不得标 complete。不要自动修复、摊平或重复挂接节点。\n"
        "每个节点必须提供 evidence.segment_id 和原文连续 evidence.quote，引用应支持该节点描述。"
        "每个门 scope 必须提供 scope_evidence，支持该输出事件与直接子项构成此 scope；只有原文直接支持 AND/OR 时才提供"
        "logic_evidence 并输出对应门型。若没有直接门型证据，gate=unknown、logic_evidence=null，并填写 unknown_reason。"
        "引文必须逐字来自指定 segment；不要改写、拼接或根据常识补证。引用可定位不代表语义必然成立。\n"
        "例如原文明确表达 (A AND B) OR (C AND D) 时，根 OR 的直接子项应是两个分支输出事件；"
        "再分别用局部 scope 表达每个分支的子项。若文本不能直接授权某个局部门，保留该 scope 为 unknown，"
        "但仍须准确表达其候选层级和完整 child set。\n"
        "输出严格 JSON，不输出推理过程：\n"
        '{"structure_status":"complete|unresolved",'
        '"nodes":[{"id":"E1","text":"...",'
        '"type":"top_event|intermediate_event|basic_event|undeveloped_event",'
        '"evidence":{"segment_id":"...","quote":"..."}}],'
        '"gates":[{"scope_id":"S1","output_node_id":"E1",'
        '"child_node_ids":["E2","E3"],"gate":"AND|OR|unknown",'
        '"scope_evidence":{"segment_id":"...","quote":"..."},'
        '"logic_evidence":{"segment_id":"...","quote":"..."}或JSON null,'
        '"unknown_reason":"no_direct_logic_evidence|incomplete_child_set|scope_ambiguity|input_context_unavailable 或 JSON null"}],'
        '"unresolved_questions":[]}\n输入 JSON：\n'
        + payload
    )
