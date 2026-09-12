from typing import Dict, Optional


PROMPT_PROFILES: Dict[str, Dict[str, str]] = {
    "balanced": {
        "style": "保持专业、结构化、不过度推测。",
        "risk": "仅在证据不足时给出低置信度提示。",
    },
    "strict": {
        "style": "严格保守，仅基于输入文本和树结构给结论。",
        "risk": "禁止臆测，缺失信息直接标注为未知。",
    },
    "exploratory": {
        "style": "允许提出可能的扩展原因链，但必须显式标注推测。",
        "risk": "可给出候选项并附置信度等级。",
    },
}


DEFAULT_PROFILE = "balanced"


def _resolve_profile(profile: Optional[str]) -> Dict[str, str]:
    key = (profile or DEFAULT_PROFILE).strip().lower()
    return PROMPT_PROFILES.get(key, PROMPT_PROFILES[DEFAULT_PROFILE])


def _append_custom_instructions(prompt: str, custom_instructions: Optional[str]) -> str:
    text = (custom_instructions or "").strip()
    if not text:
        return prompt
    return f"{prompt}\n\n额外约束:\n{text}\n"


def build_failure_generation_prompt(
    system_description: str,
    profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    p = _resolve_profile(profile)
    safe_system_description = (system_description or "").replace('"', "'")
    prompt = f"""
  你是工业系统故障分析专家。请基于以下系统描述构建一个层级化的故障树（Fault Tree）。

  系统描述:
  \"\"\"
  {safe_system_description}
  \"\"\"

行为约束:
- 风格: {p['style']}
- 风险策略: {p['risk']}
- 逻辑门规则:
  1. "OR" 门表示任一子故障发生即导致父故障。
  2. "AND" 门表示所有子故障同时发生才导致父故障。
- 概率逻辑:
  1. 若已知具体数据，请填写 probability (0-1)。
  2. 若未知，请设为 null。
  3. 重要: 尽量保证父节点概率符合逻辑门估算（例如 OR 门的父概率应大于等于任意子概率），但不需要精确计算，保持数量级合理即可。

输出要求:
1) 仅输出一个标准的JSON对象（不要包裹在数组中，不要包含Markdown标记如```json）。
2) JSON结构必须递归，格式如下:
{{
  "name": "顶事件名称",
  "probability": null,
  "gate": "OR",
  "causes": [
    {{
      "name": "中间事件或基本事件名称",
      "probability": 0.05,
      "gate": "AND",
      "causes": [
        {{
          "name": "更底层的故障",
          "probability": 0.1,
          "gate": null,
          "causes": []
        }}
      ]
    }},
    {{
      "name": "另一个子故障",
      "probability": null,
      "gate": null,
      "causes": []
    }}
  ]
}}
3) 如果是基本事件（没有子故障），"causes" 为空数组 [], "gate" 为 null。
4) 确保JSON语法严格正确，可直接被Python json.loads()解析。
5) 不要输出任何解释、前言或后缀文本。
""".strip()
    return _append_custom_instructions(prompt, custom_instructions)


def build_text_extraction_prompt(
    chunk_text: str,
    index: int,
    total: int,
    profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    p = _resolve_profile(profile)
    safe_chunk_text = (chunk_text or "").replace('"', "'")
    prompt = f"""
你是工业故障知识抽取助手（面向生产环境）。你的任务是从文本中稳定、保守、无歧义地抽取结构化故障信息。

【全局行为约束】
- 风格: {p['style']}
- 风险策略: {p['risk']}
- 原则: 宁可少提取，不可错误提取（高精度优先）

【抽取规则（必须严格遵守）】

1. 忠实原文：
- 仅提取文本中明确出现的信息
- 严禁编造、补全或引入外部知识

2. 字段定义与约束：

   (1) fault_code：
   - 仅在满足以下任一条件时提取，否则必须为 null：
     a. 文本中明确出现关键词：故障码 / 错误码 / error code / fault code
     b. 且同时满足格式之一：
        - F\\d+（如 F123）
        - E\\d+（如 E45）
        - ERR_\\w+（如 ERR_OVERCURRENT）
   - 普通编号、参数号（如 1234, p1278）不得作为 fault_code

   (2) component：
   - 提取具体设备或模块名称（如：电机、逆变器、传感器）
   - 若无法明确识别，填 ""
   - 禁止使用泛化词（如：系统、设备）

   (3) description：
   - 仅描述“故障现象 / 报警信息 / 系统表现”
   - 禁止包含原因、解决方案、推测内容

   (4) causes：
   - 仅提取文本中“明确出现”的原因描述
   - 禁止推理、补全或扩展
   - 若无明确原因，返回 []

   (5) parameters：
   - 仅提取具有参数ID格式的字段（如：p1234, P0456）
   - 禁止提取普通数值（如 220V, 50Hz）
   - 若无，返回 []

3. 多组件处理规则（强制）：
   - 如果一个故障涉及多个组件，必须拆分为多个 item
   - 每个 item 仅对应一个 component

4. 空值规范（强制）：
   - fault_code：无则为 null
   - component / description：无则为 ""
   - causes / parameters：无则为 []
   - 除 fault_code 外，禁止使用 null

5. 无故障信息处理：
   - 若文本不包含任何故障相关信息，输出：
     {{"items": []}}

【输出格式（严格要求）】
- 仅输出 JSON，不要任何解释说明
- 不要使用 Markdown（如 ```json）
- 必须完全符合以下 Schema：

{{
  "items": [
    {{
      "fault_code": "String or null",
      "component": "String",
      "description": "String",
      "causes": ["String"],
      "parameters": ["String"]
    }}
  ]
}}

【示例】

输入：
电机过热报警，未提供故障码，可能由于散热不良

输出：
{{
  "items": [
    {{
      "fault_code": null,
      "component": "电机",
      "description": "过热报警",
      "causes": ["散热不良"],
      "parameters": []
    }}
  ]
}}

---

当前片段序号: {index}/{total}

待分析文本:
\"\"\"
{safe_chunk_text}
\"\"\"
""".strip()
    return _append_custom_instructions(prompt, custom_instructions)


def build_analysis_report_prompt(
    system_description: str,
    top_event: str,
    tree_text: str,
    profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    p = _resolve_profile(profile)
    prompt = f"""
你是FTA工程专家。请基于故障树生成分析报告和可执行建议。

系统: {system_description}
顶事件: {top_event}
故障树JSON:
{tree_text}

行为约束:
- 风格: {p['style']}
- 风险策略: {p['risk']}

仅输出JSON对象，格式:
{{
  "top_event_analysis": "一句话说明顶事件风险",
  "key_paths": [
    {{"path": "路径描述", "risk_level": "高/中/低", "reason": "原因"}}
  ],
  "weak_links": [
    {{"component": "薄弱环节", "reason": "原因", "severity": "高/中/低"}}
  ],
  "recommended_actions": [
    {{"priority": "P0/P1/P2", "action": "建议动作", "expected_effect": "预期效果"}}
  ],
  "verification_plan": [
    {{"task": "验证任务", "method": "验证方法", "pass_criteria": "通过标准"}}
  ]
}}
""".strip()
    return _append_custom_instructions(prompt, custom_instructions)


def build_draft_review_prompt(
    system_description: str,
    top_event: str,
    tree_text: str,
    profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    p = _resolve_profile(profile)
    prompt = f"""
你是FTA审查专家。请对初稿故障树进行结构与逻辑检验。

系统: {system_description}
顶事件: {top_event}
初稿故障树JSON:
{tree_text}

行为约束:
- 风格: {p['style']}
- 风险策略: {p['risk']}

审查重点:
1) 结构完整性
2) 逻辑合理性
3) 概率合理性
4) 可验证性
5) 工程可执行性

仅输出JSON对象，格式:
{{
  "overall_score": 0,
  "summary": "一句话总结初稿质量",
  "deficiencies": [
    {{
      "id": "D1",
      "title": "不足点标题",
      "severity": "高/中/低",
      "location": "节点或路径",
      "issue": "具体问题",
      "impact": "影响",
      "suggestion": "修复建议"
    }}
  ],
  "missing_events": ["建议补充的事件1", "建议补充的事件2"],
  "gate_adjustments": [
    {{"node": "节点名", "current_gate": "OR", "recommended_gate": "AND", "reason": "理由"}}
  ],
  "probability_notes": [
    {{"node": "节点名", "problem": "概率问题", "suggestion": "建议"}}
  ],
  "next_steps": [
    {{"priority": "P0/P1/P2", "task": "后续任务", "output": "预期产出"}}
  ]
}}
""".strip()
    return _append_custom_instructions(prompt, custom_instructions)
