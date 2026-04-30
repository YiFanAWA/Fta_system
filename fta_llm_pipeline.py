import json
import os
import re
from typing import Any, Dict, List, Optional

from config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

try:
    httpx = __import__("httpx")
except Exception:
    httpx = None  # type: ignore


PROMPT1_TEMPLATE = """你是一名FTA专家，请从文本中提取：
- 顶事件
- 至少2个一级原因
- 每个原因至少2个子原因
- 默认逻辑为OR

输出JSON：
{
  \"top_event\": \"\",
  \"logic\": \"OR\",
  \"intermediate_events\": [
    {
      \"name\": \"\",
      \"probability\": null,
      \"logic\": \"OR\",
      \"causes\": [
        {\"name\": \"\", \"probability\": null},
        {\"name\": \"\", \"probability\": null}
      ]
    }
  ]
}

只输出JSON，不要解释。

原始故障文本：
{text}
"""


PROMPT2_TEMPLATE = """将输入JSON转换为标准FTA DOT代码，必须满足：

- 方向：Basic -> Gate -> Intermediate -> Gate -> Top
- 每个Gate至少2输入
- 自动修复错误结构
- 节点规范：
  - Top：doubleoctagon
  - Gate：diamond
  - 中间：box
  - 底事件：ellipse
- 使用 rankdir=TB

只输出DOT代码，不要解释。

输入JSON：
{json_payload}
"""


DEFAULT_MODEL = OPENAI_MODEL
DEFAULT_BASE_URL = OPENAI_API_BASE
DEFAULT_API_KEY = OPENAI_API_KEY
DEFAULT_TIMEOUT = float(OPENAI_TIMEOUT_SECONDS)


def _prob_text_to_value(text: Any) -> Optional[float]:
    val = str(text or "").strip()
    if not val:
        return None

    mapping = {
        "极高": 0.85,
        "高": 0.7,
        "中": 0.5,
        "低": 0.3,
        "极低": 0.15,
    }
    if val in mapping:
        return mapping[val]

    # Support numeric probability forms such as 70% / 0.7.
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", val)
    if m:
        p = float(m.group(1)) / 100.0
        return max(0.0, min(1.0, p))

    try:
        p = float(val)
        return max(0.0, min(1.0, p))
    except Exception:
        return None


def _parse_structured_branch_text(text: str) -> Optional[Dict[str, Any]]:
    """Parse troubleshooting outlines like:
    分支一 / 子分支3.1 / 概率 / 可能原因 / 检查步骤
    and convert to FTA intermediate events.
    """
    if not isinstance(text, str):
        return None

    lines = [ln.strip() for ln in text.replace("\r", "").split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return None

    branch_re = re.compile(r"^分支[一二三四五六七八九十\d]+\s*[：:]\s*(.+)$")
    subbranch_re = re.compile(r"^子分支\s*[\d\.]+\s*[：:]\s*(.+)$")
    prob_re = re.compile(r"^概率\s*[：:]\s*(.+)$")
    bullet_re = re.compile(r"^[\-•·]\s*(.+)$")

    branches: List[Dict[str, Any]] = []
    current_branch: Optional[Dict[str, Any]] = None
    current_sub: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None

    for ln in lines:
        m_branch = branch_re.match(ln)
        if m_branch:
            current_branch = {
                "title": m_branch.group(1).strip(),
                "probability": None,
                "causes": [],
                "subbranches": [],
            }
            branches.append(current_branch)
            current_sub = None
            mode = None
            continue

        m_sub = subbranch_re.match(ln)
        if m_sub and current_branch is not None:
            current_sub = {
                "title": m_sub.group(1).strip(),
                "probability": None,
                "causes": [],
            }
            current_branch["subbranches"].append(current_sub)
            mode = None
            continue

        if current_branch is None:
            continue

        m_prob = prob_re.match(ln)
        if m_prob:
            target = current_sub if current_sub is not None else current_branch
            target["probability"] = _prob_text_to_value(m_prob.group(1).strip())
            mode = None
            continue

        if ln.startswith("可能原因"):
            mode = "causes"
            continue

        # End cause capture when entering another section.
        if ln.startswith("检查步骤") or ln.startswith("快速排查顺序") or ln.startswith("快速判断技巧"):
            mode = None
            continue

        if mode == "causes":
            m_bullet = bullet_re.match(ln)
            if m_bullet:
                cause_name = m_bullet.group(1).strip()
                if cause_name:
                    target = current_sub if current_sub is not None else current_branch
                    target["causes"].append(cause_name)

    if len(branches) < 2:
        return None

    intermediate_events: List[Dict[str, Any]] = []
    for branch in branches:
        title = str(branch.get("title") or "").strip()
        if not title:
            continue

        subbranches = branch.get("subbranches") if isinstance(branch.get("subbranches"), list) else []
        branch_causes = branch.get("causes") if isinstance(branch.get("causes"), list) else []

        if subbranches:
            # Keep explicit hierarchy: parent branch -> sub-branches.
            parent_causes: List[Dict[str, Any]] = []
            for sub in subbranches:
                sub_title = str(sub.get("title") or "").strip()
                if not sub_title:
                    continue
                parent_causes.append(
                    {
                        "name": sub_title,
                        "probability": _prob_text_to_value(sub.get("probability")),
                    }
                )

            if len(parent_causes) >= 1:
                intermediate_events.append(
                    {
                        "name": title,
                        "probability": _prob_text_to_value(branch.get("probability")),
                        "logic": "OR",
                        "causes": parent_causes,
                    }
                )

            # Expand each sub-branch into its own intermediate event with root causes.
            for sub in subbranches:
                sub_title = str(sub.get("title") or "").strip()
                if not sub_title:
                    continue
                sub_causes_raw = sub.get("causes") if isinstance(sub.get("causes"), list) else []
                sub_causes = [{"name": c, "probability": None} for c in sub_causes_raw if isinstance(c, str) and c.strip()]
                intermediate_events.append(
                    {
                        "name": sub_title,
                        "probability": _prob_text_to_value(sub.get("probability")),
                        "logic": "OR",
                        "causes": sub_causes,
                    }
                )
            continue

        causes = [{"name": c, "probability": None} for c in branch_causes if isinstance(c, str) and c.strip()]
        intermediate_events.append(
            {
                "name": title,
                "probability": _prob_text_to_value(branch.get("probability")),
                "logic": "OR",
                "causes": causes,
            }
        )

    if not intermediate_events:
        return None

    return {
        "top_event": "系统硬件异常",
        "logic": "OR",
        "intermediate_events": intermediate_events,
    }


def _extract_json_object(raw: str) -> Dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty LLM response")

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")

    sub = text[start : end + 1]
    payload = json.loads(sub)
    if not isinstance(payload, dict):
        raise ValueError("JSON is not object")
    return payload


def _extract_dot(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty LLM response")

    fence = re.search(r"```(?:dot|graphviz)?\s*(digraph[\s\S]*?)```", text, flags=re.IGNORECASE)
    if fence:
        return fence.group(1).strip()

    start = text.find("digraph")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()

    raise ValueError("no DOT found")


def _llm_chat(prompt: str, model: Optional[str] = None) -> str:
    api_key = DEFAULT_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 或 QWEN_API_KEY is required")

    chosen_model = model or DEFAULT_MODEL

    if OpenAI is not None:
        kwargs: Dict[str, Any] = {"api_key": api_key, "timeout": DEFAULT_TIMEOUT}
        if DEFAULT_BASE_URL:
            kwargs["base_url"] = DEFAULT_BASE_URL
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return (content or "").strip()

    if httpx is None:
        raise RuntimeError("Neither openai SDK nor httpx is available")

    if not DEFAULT_BASE_URL:
        raise RuntimeError("OPENAI_API_BASE 或 QWEN_BASE_URL is required")

    url = DEFAULT_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": chosen_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _ensure_name(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _ensure_probability(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        p = float(value)
        if p < 0:
            return 0.0
        if p > 1:
            return 1.0
        return p
    except Exception:
        return None


def _normalize_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    top_event = _ensure_name(data.get("top_event"), "设备故障")
    logic = str(data.get("logic") or "OR").upper()
    if logic not in {"OR", "AND"}:
        logic = "OR"

    raw_intermediate = data.get("intermediate_events")
    if not isinstance(raw_intermediate, list):
        raw_intermediate = []

    intermediates: List[Dict[str, Any]] = []
    for i, event in enumerate(raw_intermediate, start=1):
        if not isinstance(event, dict):
            continue

        name = _ensure_name(event.get("name"), f"中间事件{i}")
        ev_logic = str(event.get("logic") or "OR").upper()
        if ev_logic not in {"OR", "AND"}:
            ev_logic = "OR"

        causes_raw = event.get("causes")
        if not isinstance(causes_raw, list):
            causes_raw = []

        causes: List[Dict[str, Any]] = []
        for j, c in enumerate(causes_raw, start=1):
            if isinstance(c, dict):
                cname = _ensure_name(c.get("name"), f"原因{j}")
                cprob = _ensure_probability(c.get("probability"))
            elif isinstance(c, str):
                cname = _ensure_name(c, f"原因{j}")
                cprob = None
            else:
                continue
            causes.append({"name": cname, "probability": cprob})

        while len(causes) < 2:
            idx = len(causes) + 1
            causes.append({"name": f"未知原因{idx}", "probability": None})

        intermediates.append(
            {
                "name": name,
                "probability": _ensure_probability(event.get("probability")),
                "logic": ev_logic,
                "causes": causes,
            }
        )

    while len(intermediates) < 2:
        k = len(intermediates) + 1
        intermediates.append(
            {
                "name": f"中间事件{k}",
                "probability": None,
                "logic": "OR",
                "causes": [
                    {"name": "未知原因1", "probability": None},
                    {"name": "未知原因2", "probability": None},
                ],
            }
        )

    return {
        "top_event": top_event,
        "logic": logic,
        "intermediate_events": intermediates,
    }


def _fallback_dot(json_data: Dict[str, Any]) -> str:
    data = _normalize_structure(json_data)

    lines: List[str] = []
    lines.append("digraph FTA {")
    lines.append("  rankdir=TB;")
    lines.append("  graph [fontname=Helvetica];")
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    top_label = data["top_event"].replace('"', "'")
    lines.append(f'  top [label="{top_label}", shape=doubleoctagon, style=filled, fillcolor=lightcoral];')

    g_top = "g1"
    lines.append('  g1 [label="OR", shape=diamond, width=0.5, height=0.5, fixedsize=true];')
    lines.append("  g1 -> top;")

    gate_index = 2
    event_index = 1
    cause_index = 1

    for ev in data["intermediate_events"]:
        eid = f"e{event_index}"
        event_index += 1
        elabel = str(ev["name"]).replace('"', "'")
        lines.append(f'  {eid} [label="{elabel}", shape=box];')
        lines.append(f"  {eid} -> {g_top};")

        gmid = f"g{gate_index}"
        gate_index += 1
        glogic = str(ev.get("logic") or "OR").upper()
        if glogic not in {"OR", "AND"}:
            glogic = "OR"
        lines.append(f'  {gmid} [label="{glogic}", shape=diamond, width=0.5, height=0.5, fixedsize=true];')
        lines.append(f"  {gmid} -> {eid};")

        causes = ev.get("causes", [])
        if not isinstance(causes, list):
            causes = []
        if len(causes) < 2:
            causes = list(causes)
            while len(causes) < 2:
                idx = len(causes) + 1
                causes.append({"name": f"未知原因{idx}", "probability": None})

        for c in causes:
            cid = f"c{cause_index}"
            cause_index += 1
            cname = str((c or {}).get("name") if isinstance(c, dict) else c)
            if not cname.strip():
                cname = "未知原因"
            cname = cname.replace('"', "'")
            lines.append(f'  {cid} [label="{cname}", shape=ellipse];')
            lines.append(f"  {cid} -> {gmid};")

    lines.append("}")
    return "\n".join(lines)


def _deterministic_multilevel_dot(json_data: Dict[str, Any]) -> str:
    """Build DOT without LLM, preserving multi-level relations when cause names
    reference other intermediate event names.
    """
    data = _normalize_structure(json_data)
    top_logic = str(data.get("logic") or "OR").upper()
    if top_logic not in {"OR", "AND"}:
        top_logic = "OR"

    events = data.get("intermediate_events", []) if isinstance(data.get("intermediate_events"), list) else []
    event_map: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        if not isinstance(ev, dict):
            continue
        name = str(ev.get("name") or "").strip()
        if not name or name in event_map:
            continue
        event_map[name] = ev

    referenced_events = set()
    for ev in events:
        if not isinstance(ev, dict):
            continue
        causes = ev.get("causes", []) if isinstance(ev.get("causes"), list) else []
        for c in causes:
            if not isinstance(c, dict):
                continue
            cname = str(c.get("name") or "").strip()
            if cname in event_map:
                referenced_events.add(cname)

    root_events = [name for name in event_map.keys() if name not in referenced_events]
    if not root_events:
        root_events = list(event_map.keys())

    lines: List[str] = []
    lines.append("digraph FTA {")
    lines.append("  rankdir=TB;")
    lines.append("  graph [fontname=Helvetica];")
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    top_label = str(data.get("top_event") or "设备故障").replace('"', "'")
    lines.append(f'  top [label="{top_label}", shape=doubleoctagon, style=filled, fillcolor=lightcoral];')
    lines.append(f'  g_top [label="{top_logic}", shape=diamond, width=0.5, height=0.5, fixedsize=true];')
    lines.append("  g_top -> top;")

    event_ids: Dict[str, str] = {}
    gate_ids: Dict[str, str] = {}
    e_idx = 1
    g_idx = 1

    def ensure_event(name: str, probability: Optional[float] = None, logic: str = "OR") -> None:
        nonlocal e_idx, g_idx
        if name in event_ids:
            return
        eid = f"e{e_idx}"
        gid = f"g{g_idx}"
        e_idx += 1
        g_idx += 1
        event_ids[name] = eid
        gate_ids[name] = gid

        label = name.replace('"', "'")
        if probability is not None:
            label = f"{label}\\nP={probability:.3f}"

        g_logic = (logic or "OR").upper()
        if g_logic not in {"OR", "AND"}:
            g_logic = "OR"

        lines.append(f'  {eid} [label="{label}", shape=box];')
        lines.append(f'  {gid} [label="{g_logic}", shape=diamond, width=0.5, height=0.5, fixedsize=true];')
        lines.append(f"  {gid} -> {eid};")

    for name, ev in event_map.items():
        ensure_event(name, _ensure_probability(ev.get("probability")), str(ev.get("logic") or "OR"))

    for name in root_events:
        lines.append(f"  {event_ids[name]} -> g_top;")

    b_idx = 1
    for name, ev in event_map.items():
        gid = gate_ids[name]
        causes = ev.get("causes", []) if isinstance(ev.get("causes"), list) else []
        if not causes:
            # Keep gate valid with at least 2 placeholder basics.
            for k in range(2):
                bid = f"b{b_idx}"
                b_idx += 1
                lines.append(f'  {bid} [label="未知原因{k+1}", shape=ellipse];')
                lines.append(f"  {bid} -> {gid};")
            continue

        link_count = 0
        for c in causes:
            if not isinstance(c, dict):
                continue
            cname = str(c.get("name") or "").strip()
            if not cname:
                continue
            if cname in event_map and cname != name:
                lines.append(f"  {event_ids[cname]} -> {gid};")
            else:
                bid = f"b{b_idx}"
                b_idx += 1
                cp = _ensure_probability(c.get("probability"))
                blabel = cname.replace('"', "'")
                if cp is not None:
                    blabel = f"{blabel}\\nP={cp:.3f}"
                lines.append(f'  {bid} [label="{blabel}", shape=ellipse];')
                lines.append(f"  {bid} -> {gid};")
            link_count += 1

        if link_count == 1:
            # Duplicate a neutral placeholder to keep AND/OR gate semantics visible.
            bid = f"b{b_idx}"
            b_idx += 1
            lines.append(f'  {bid} [label="补充原因", shape=ellipse, style=dashed];')
            lines.append(f"  {bid} -> {gid};")

    lines.append("}")
    return "\n".join(lines)


def extract_fta_structure(text: str, force_llm: bool = False) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("input text is empty")

    if not force_llm:
        parsed = _parse_structured_branch_text(text)
        if parsed:
            normalized = _normalize_structure(parsed)
            normalized["_source"] = "structured_rule"
            return normalized

    prompt = PROMPT1_TEMPLATE.format(text=text.strip())
    raw = _llm_chat(prompt)
    parsed_llm = _extract_json_object(raw)
    return _normalize_structure(parsed_llm)


def generate_dot(json_data: Dict[str, Any], allow_fallback: bool = True) -> str:
    if isinstance(json_data, dict) and str(json_data.get("_source") or "") == "structured_rule":
        return _deterministic_multilevel_dot(json_data)

    normalized = _normalize_structure(json_data)
    payload = json.dumps(normalized, ensure_ascii=False, indent=2)
    prompt = PROMPT2_TEMPLATE.format(json_payload=payload)

    try:
        raw = _llm_chat(prompt)
        dot = _extract_dot(raw)
        return dot
    except Exception:
        if allow_fallback:
            return _fallback_dot(normalized)
        raise


def save_dot(dot_str: str, filename: str) -> None:
    if not filename.lower().endswith(".dot"):
        filename = f"{filename}.dot"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(dot_str)


def main() -> None:
    sample_text = (
        "无人机飞行中发生坠机，系统记录到动力系统失效、电池异常、通信中断和飞行控制异常。"
        "可能原因包括电机过热停转、电调故障、电池电压骤降、BMS误触发保护、"
        "遥控信号干扰、图传模块异常、飞控软件崩溃以及IMU传感器失效。"
    )

    structure = extract_fta_structure(sample_text)
    dot = generate_dot(structure)
    output_file = "fault_tree_llm.dot"
    save_dot(dot, output_file)
    print(output_file)


if __name__ == "__main__":
    main()
