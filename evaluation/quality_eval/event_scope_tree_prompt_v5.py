"""Evaluation-only prompt for preserving natural-language causal path scope."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "event-scope-text-only-tree-v5-causal-path-scope"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build a label-free prompt that keeps causal conditions under their outcome."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "仅依据输入中的顶事件和原文，生成可审核的单顶事件候选结构；不看图、不用外部知识。"
        "先从每个完整因果句识别结果事件、导致该结果的条件集合和彼此替代的路径，再构造节点与 gate scopes。"
        "不要把原因/条件层级与语法从句层级混为一谈。\n"
        "因果范围规则：若原文表达‘A may lead to T if B’、‘A can cause T when B’或等价关系，"
        "A 与 B 是共同参与通向 T 的条件；B 不是导致 A 发生的子事件。不得建立 output=A、child=B 的 scope。"
        "应把 A、B 放在它们共同导致的结果事件或有原文支持的路径事件之下；只有原文直接授权其逻辑关系时才标 AND，"
        "否则 gate=unknown，但仍须保持条件与结果的正确方向。不要为了通过结构校验而虚构缺失条件。\n"
        "替代路径规则：若原文表达‘A and B, or C and D, lead to T’这类完整并列路径，"
        "按命题范围保留为 (A AND B) OR (C AND D)，而不是把 A 单独当作一条完整路径，"
        "也不要把第一条路径塞进第二条路径的子项。每个局部 scope 只收录该路径的直接、完整子项；"
        "只有原文明确列出的替代路径才进入根 scope。句中任意 and/or 词、时间先后、并列罗列、工程常识都不单独构成门证据。\n"
        "重复事件规则：若原文在不同路径中明确重复陈述同一事件，而输出合同要求树而非 DAG，"
        "可按各自路径保留不同 occurrence 节点并分别引用对应原文；不得把一个节点挂到多个父 scope。"
        "不得从图示补充模型输入未出现的事件、子项或门型。\n"
        "层级合同：gate scopes 是父子层级的唯一事实来源。每个 scope 用 output_node_id 和 child_node_ids 表示"
        "直接父子关系；scope 输出节点可在更高层作为 child，从而表达嵌套。每个门 scope 至少有两个不同的直接 child；"
        "不得让同一个输出节点拥有多个门 scope。禁止输出 parent_id 或任何第二套父子关系。"
        "一个节点不得在不同 scope 中拥有多个直接父节点。若不能形成一致的单根层级，保留可定位节点、"
        "将 structure_status 设为 unresolved，并明确 unresolved_questions；不得自动修复、摊平或重复挂接节点。\n"
        "每个节点必须提供 evidence.segment_id 和原文连续 evidence.quote，引用应支持该节点描述。"
        "每个门 scope 必须提供 scope_evidence，支持该输出事件与直接子项构成此 scope；只有原文直接支持 AND/OR 时才提供"
        "logic_evidence 并输出对应门型。若没有直接门型证据，gate=unknown、logic_evidence=null，并填写 unknown_reason。"
        "引文必须逐字来自指定 segment；不要改写、拼接或根据常识补证。引用可定位不代表语义必然成立。"
        "存在层级/引用/作用域 blocker 时不得标 complete。\n"
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
