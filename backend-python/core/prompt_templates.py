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
     a. 文本中明确出现关键词：故障码 / 错误码 / error code / fault code，且后面紧邻故障编号；
     b. 文本行首直接出现故障编号并紧跟故障标题（西门子手册常见格式），也视为明确故障记录声明；
   - 故障编号格式包括：
        - A\\d+（如 A01032）
        - F\\d+（如 F01651）
        - N\\d+（如 N01004）
        - E\\d+（如 E45）
        - ERR_\\w+（如 ERR_OVERCURRENT）
   - 普通编号、参数号（如 1234, p1278）不得作为 fault_code

   (2) component：
   - 提取原文明确声明的主组件（如：电机、逆变器、传感器）
   - 英文手册标题中明确的组件前缀可作为主组件证据；保留原文中的组件名称，
     后端统一词典负责同义词和标题变体归一化，不要为未确认的新名称自行发明规范名
   - 如果原文写“组件为无”或“组件为无（关联……）”，component 必须填写 ""
   - “组件为无（关联控制单元及电机模块）”表示没有主组件，不得把关联对象拼进 component
   - 只有原文明确把多个对象作为同一主组件合并表达时，component 才填写合并表达
   - 若无法明确识别，填 ""
   - 禁止使用泛化词（如：系统、设备）

   (2.1) related_components：
   - 将同一故障记录中明确出现的关联组件拆成列表
   - 若原文写“组件为无（关联……）”，只把括号内对象写入 related_components
   - 英文只有出现 associated with、related to、connected to/with、linked to 等明确关系表达时，才写入 related_components
   - 普通正文、故障原因或处理建议中单独提到的组件，不得仅凭提及关系写入 related_components
   - 若原文只声明一个主组件且没有“关联……”表达，related_components 必须为 []，不得复制主组件
   - “驱动对象为无（关联……）”属于驱动对象字段，不等于组件关联；除非原文另有组件关联声明，不得写入 related_components
   - 这只是组件属性，不是新的故障记录
   - 若无法识别，返回 []

   (3) description：
   - 仅描述“故障现象 / 报警信息 / 系统表现”
   - 中文手册优先取“故障现象为/报警信息为/故障描述为”之后的完整现象短语；不要把“故障类别”、组件声明或前面的分类标题一并复制进来
   - 英文手册若记录以“故障码 + 标题”开头，description 只取标题行；遇到 Reaction、Acknowledge、Cause、Fault value、Remedy 等段落立即停止，不要把后续段落拼入 description
   - 如果现象短语前已经重复写了独立的主组件标签，只保留现象本身；不要为了补充组件而改写 description
   - 禁止包含原因、解决方案、推测内容

   (4) causes：
   - 候选原因的定义是：导致故障/报警成立的原因、触发条件或明确故障场景；不是只限于传统“根因”名词
   - 优先来源是 Cause、故障值/报警值对应的场景说明，以及原文中的直接因果描述；故障定义中“识别出组件更换”这类触发场景也可以保留
   - 关联故障值/信息值中的具体触发场景要保留完整语义；例如“新增传感器更换标识”不能只概括成“组件更换”
   - 候选原因使用自然语言场景，不要把“0表示”“故障值为10、11”“xxxx=000B”等参数值前缀原样放入 causes；保留“表示/括号”后面的故障场景含义
   - 纯参数编号、故障值编号、仅用于定位的诊断索引不能单独作为候选原因；例如“1~999表示交叉比较数据编号”不是原因，应为空，除非原文同时明确说明编号对应的异常/不一致/故障场景
   - 条件原因要保持原文逻辑关系，例如“p1215=0（不存在电机抱闸）且p9602=1（SBC使能）”应写为“不存在电机抱闸且SBC使能”，不要把“且”改成“但”
   - “因散热不良”“故障值20表示制动绕组短路”“若故障值为6000~6999表示PROFIsafe控制故障”属于原因/故障场景，应提取
   - “检查参数”“重新上电”“升级固件”“更换模块”“修复漏洞”等处理动作不是 causes，不得提取；但故障定义中明确表示“组件更换触发/检测到组件更换”的场景不是处理动作，可以提取
   - 处理建议中的预防性描述（如“避免因散热不良导致二次故障”）默认不是当前故障原因，除非原文明确说明它就是该故障的触发原因
   - 不要把处理动作后面的修复目标自动改写成原因；例如“升级固件，修复软件超时漏洞”不能仅凭这句话新增“软件超时漏洞”
   - 同一原因只保留一次；原因粒度保持原文表达，不要把一个完整场景拆成泛化短语
   - 每一个候选原因都必须能被原文中的直接 Cause/场景/因果短语支持；无法绑定直接证据时仍可保留候选值，但必须让后端将记录标记为 pending / missing_reason_evidence，不得无证据放行
   - 禁止推理、补全或扩展
   - 若无明确原因，返回 []

   (5) parameters：
   - 仅提取具有参数ID格式的字段（如：p1234, P0456, r2124, R0949）
   - 禁止提取普通数值（如 220V, 50Hz）
   - 若无，返回 []

3. 多组件处理规则（强制）：
   - 一个明确的“故障码 + 故障现象”只输出一个 item
   - 多个关联组件必须保留在同一个 item 的 related_components 中，不得自动提升为 component
   - 只有出现不同故障码，或原文明确出现不同故障现象记录时，才输出多个 item
   - 例如“组件为无（关联控制单元及电机模块）”仍然只输出一个 item

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
      "related_components": ["String"],
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
      "related_components": [],
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
