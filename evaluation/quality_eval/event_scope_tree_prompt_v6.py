"""Evaluation-only prompt for one coherent event-scope hierarchy and complete gate objects."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "event-scope-text-only-tree-v6-single-hierarchy"


def build_prompt(model_input: dict[str, Any]) -> str:
    """Build a label-free prompt with explicit single-parent scope construction rules."""
    payload = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "仅依据输入中的顶事件和原文，生成可审核的单顶事件候选结构；不看图、不用外部知识。"
        "先识别每个完整因果命题的结果、条件集合和替代路径，再将它们组织成一棵连贯的树。"
        "不要把语法从句层级误当成因果层级。\n"
        "条件方向：原文若表达‘A may lead to T if B’、‘A can cause T when B’或等价关系，"
        "A 与 B 都是通向 T 的相关条件；B 不是导致 A 的子事件。必须保留 A、B 到 T 的方向，"
        "不得建立 output=A、child=B 的 scope。该表达本身不自动授权 AND 门；门型仍须有直接逻辑证据，"
        "否则 gate=unknown，但保留有证据的事件和正确方向。\n"
        "单树层级硬约束：一个 output_node_id 在全份输出中只能出现于一个 gate scope；"
        "每个非叶输出节点最多一个直接子项 scope，每个节点最多一个直接父节点；gate scopes 是唯一层级来源，"
        "禁止输出 parent_id、重复 scope、DAG 多父节点或互相冲突的第二套层级。顶事件必须只有一个根 scope。"
        "若多个原文命题都通向同一顶事件，合并到同一个根 scope 的直接子项集合；不得为每个句子各自重复创建顶事件 scope。\n"
        "复合替代路径：原文若直接支持‘(A AND B) OR (C AND D) leads to T’这样的完整路径，"
        "用两个有原文支持的 intermediate_event 分支 P1、P2 表示；根 T 只建立一个 scope，直接 child 为 P1、P2；"
        "P1 的局部 scope 直接 child 为 A、B，P2 的局部 scope 直接 child 为 C、D。"
        "根 OR 或局部 AND 只有在对应原文直接授权时才标为已知门，否则该 scope 保留 unknown。"
        "这只是层级形状示例，不得照搬未被输入原文支持的事件、节点或门型。若不能找到支撑中间分支节点的原文短语，"
        "不得虚构该节点；保留 structure_status=unresolved 并写明问题。不得将完整复合路径当叶节点后又重复拆出其子项。\n"
        "避免单子项 scope：每个 gate scope 至少有两个不同的直接 child。若某句只给出单一后续事件，"
        "不要为它创建单子项 gate；保留事件关系的证据并说明层级无法形成，或将该事件放入其有原文支持的更大 scope。"
        "不得为满足数量要求而补造兄弟节点。\n"
        "替代路径和重复事件：‘A and B, or C and D’的两条路径不可交叉嵌套。若同一事件在不同路径中被原文重复陈述，"
        "树中可保留不同 occurrence 节点并分别引用其原文；禁止一个 occurrence 挂到多个父节点。不得从图示补充输入中没有的内容。\n"
        "字段完整性：所有 gate 对象必须始终包含 scope_id、output_node_id、child_node_ids、gate、scope_evidence、"
        "logic_evidence、unknown_reason 七个字段。gate=AND/OR 时 logic_evidence 必须是直接支持该门的证据，"
        "unknown_reason 必须显式为 JSON null；gate=unknown 时 logic_evidence 必须显式为 JSON null，"
        "unknown_reason 必须是允许的原因代码。不得省略任何字段。节点 evidence.quote 和 scope_evidence.quote"
        "必须是指定 segment 中唯一出现的连续原文；不可改写、拼接或根据常识补证。引文位置正确不等于语义蕴含。"
        "存在层级、引用、作用域或字段 blocker 时，structure_status 不得为 complete。\n"
        "输出严格 JSON，不输出推理过程：\n"
        '{"structure_status":"complete|unresolved",'
        '"nodes":[{"id":"E1","text":"...",'
        '"type":"top_event|intermediate_event|basic_event|undeveloped_event",'
        '"evidence":{"segment_id":"...","quote":"..."}}],'
        '"gates":[{"scope_id":"S1","output_node_id":"E1",'
        '"child_node_ids":["E2","E3"],"gate":"AND|OR|unknown",'
        '"scope_evidence":{"segment_id":"...","quote":"..."},'
        '"logic_evidence":{"segment_id":"...","quote":"..."} 或 JSON null,'
        '"unknown_reason":"no_direct_logic_evidence|incomplete_child_set|scope_ambiguity|input_context_unavailable" 或 JSON null}],'
        '"unresolved_questions":[]}\n输入 JSON：\n'
        + payload
    )
