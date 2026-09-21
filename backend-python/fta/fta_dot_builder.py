from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List


# =========================
# Pattern Layer
# =========================

BULLET_PREFIX_RE = re.compile(
    r"^\s*(?:[-*•]|\d+[\.)、]|[A-Za-z][\.)]|[（(]?[一二三四五六七八九十]+[)）.、])\s*"
)
INLINE_BULLET_RE = re.compile(r"(?:(?<=^)|(?<=[\s:：;；\|]))(?:[-*•])\s*")
SEPARATOR_RE = re.compile(r"[\n、，；;]+")


@dataclass
class ListPattern:
    has_newline: bool
    has_bullet: bool
    separator_count: int
    item_count_estimate: int
    is_list_like: bool


def detect_list_structure(text: str) -> Dict[str, Any]:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    has_newline = "\n" in s

    lines = [ln for ln in s.split("\n") if ln.strip()]
    bullet_hits = sum(1 for ln in lines if BULLET_PREFIX_RE.match(ln) is not None)
    has_bullet = bullet_hits > 0 or INLINE_BULLET_RE.search(s) is not None

    separator_count = len(re.findall(r"[、，；;]", s))
    item_count_estimate = max(1, bullet_hits + separator_count + (1 if has_newline else 0))

    is_list_like = (bullet_hits >= 1 and len(lines) >= 1) or separator_count >= 2 or (has_newline and len(lines) >= 2)

    return {
        "has_newline": has_newline,
        "has_bullet": has_bullet,
        "separator_count": separator_count,
        "item_count_estimate": item_count_estimate,
        "is_list_like": is_list_like,
    }


# =========================
# Parsing Layer
# =========================


def _clean_text(text: str) -> str:
    s = (text or "").replace("\u3000", " ").strip()
    s = re.sub(r"\s+", "", s)
    return s


def _strip_edge_punct(text: str) -> str:
    return re.sub(r"^[，。；：、,.!?:;()（）\[\]{}\-_/\s]+|[，。；：、,.!?:;()（）\[\]{}\-_/\s]+$", "", text or "")


def _strip_cause_prefix(text: str) -> str:
    s = (text or "").strip()
    s = re.sub(r"^(?:可能原因|原因|根因|诱因)(?:包括)?[：:\s]*", "", s)
    return _strip_edge_punct(s)


def _semantic_key(text: str) -> str:
    s = _clean_text(text).lower()
    s = re.sub(r"[，。；：、,.!?:;\-_/()（）\[\]{}\"'`]+", "", s)
    return s


def _dedup_texts(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for v in values:
        if not isinstance(v, str):
            continue
        s = _strip_edge_punct(v)
        if not s:
            continue
        key = _semantic_key(s)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _filter_causes_by_context(causes: List[str], top: str, fault: str) -> List[str]:
    top_key = _semantic_key(top)
    fault_key = _semantic_key(fault)

    out: List[str] = []
    seen = set()
    for c in causes:
        if not isinstance(c, str):
            continue
        s = _strip_edge_punct(c)
        if not s:
            continue
        key = _semantic_key(s)
        if not key:
            continue

        # Remove causes that are semantically same as top/fault or contain them.
        if top_key and (key == top_key or key in top_key or top_key in key):
            continue
        if fault_key and (key == fault_key or key in fault_key or fault_key in key):
            continue

        if key in seen:
            continue
        seen.add(key)
        out.append(s)

    return out


def split_into_items(text: str) -> List[str]:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not s:
        return []

    # Normalize inline bullets to newlines.
    s = INLINE_BULLET_RE.sub("\n", s)

    rough_chunks = re.split(r"\n+", s)
    items: List[str] = []

    for chunk in rough_chunks:
        part = chunk.strip()
        if not part:
            continue

        # Remove line-leading bullet/enumeration markers.
        part = BULLET_PREFIX_RE.sub("", part).strip()
        if not part:
            continue

        # Split by common list separators.
        sub_parts = [p.strip() for p in SEPARATOR_RE.split(part)]
        for sp in sub_parts:
            sp = _strip_edge_punct(sp)
            sp = re.sub(r"^(?:\d+[\.)、]|[A-Za-z][\.)])\s*", "", sp)
            if not sp:
                continue
            items.append(sp)

    # Stable dedup.
    out: List[str] = []
    seen = set()
    for it in items:
        key = _semantic_key(it)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


# =========================
# Semantic Layer
# =========================

TOP_EVENT_TERMS = (
    "停机",
    "跳闸",
    "系统故障",
    "shutdown",
    "保护动作",
    "保护停机",
)
FAULT_CODE_PATTERNS = (
    r"\b[A-Z]{2,}(?:-[A-Z0-9]{1,16})+\b",
    r"\b[A-Z]-?\d{2,5}\b",
)
FAULT_TERMS = (
    "报警",
    "告警",
    "异常",
    "故障",
    "压力过低",
    "压力过高",
    "过流",
    "过压",
    "欠压",
    "过温",
    "温度过高",
    "温度过低",
    "振动过大",
)
CAUSE_OBJECT_TERMS = (
    "泵",
    "阀",
    "滤芯",
    "密封",
    "传感器",
    "电缆",
    "接头",
    "连接器",
    "轴承",
    "线圈",
    "继电器",
    "接插件",
    "管路",
    "油路",
)
CAUSE_FAILURE_TERMS = (
    "故障",
    "堵塞",
    "老化",
    "脆化",
    "硬化",
    "软化",
    "破裂",
    "磨损",
    "松动",
    "短路",
    "断路",
    "泄漏",
    "腐蚀",
    "损坏",
    "失效",
    "漂移",
    "偏移",
    "卡滞",
    "变形",
    "开裂",
    "进水",
    "绝缘",
)
INVALID_CONNECTORS = (
    "同时",
    "并且",
    "以及",
    "或者",
    "此外",
    "然后",
)
INVALID_SENTENCE_PATTERNS = (
    r"^如果.+则.+$",
    r"^当.+时.+$",
    r"^任一.+均会.+$",
    r"^可能.+包括.*$",
    r"^原因.+如下.*$",
    r"^原因.+有.*$",
)
CAUSAL_VERBS = ("导致", "引起", "造成", "使得")


def _split_branch_chain(segment: str) -> List[str]:
    s = (segment or "").strip()
    if not s:
        return []

    s = re.sub(r"\s*(?:→|⇒|➜|⟶|—>)\s*", " -> ", s)
    chain = [p.strip() for p in re.split(r"\s*->\s*", s) if p.strip()]

    # 某些来源会把箭头吞掉成连续空格，退化用双空格切分链路。
    if len(chain) < 2:
        chain = [p.strip() for p in re.split(r"\s{2,}", s) if p.strip()]

    return chain


def _extract_branch_causes(text: str) -> List[str]:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not s.strip():
        return []

    # 支持："故障树分支：A -> B + C -> D"
    m = re.search(r"故障树分支\s*[：:]\s*(.+)", s)
    segment = m.group(1).strip() if m else s.strip()
    segment = segment.split("技术关键")[0].strip()

    chain = _split_branch_chain(segment)
    if len(chain) >= 2:
        # 最后一段通常是结果事件，前面段落用于提取原因。
        candidates = chain[:-1]
    else:
        candidates = [segment]

    out: List[str] = []
    for part in candidates:
        for chunk in re.split(r"[+＋/、，,；;]|\band\b", part):
            t = _strip_edge_punct(chunk)
            t = re.sub(r"^(?:单一|持续|最终|并且|以及)\s*", "", t)
            t = t.strip()
            if not t:
                continue
            if classify_role(t) == "CAUSE":
                out.append(t)
                continue

            # 对流程/管理缺陷类原因放宽接收，避免被全部打回泛化兜底。
            if any(k in t for k in ("校验", "培训", "冗余", "缺失", "失效", "异常", "故障")):
                out.append(t)

    # 这里不走 deduplicate_causes，避免被严格CAUSE校验误删（如“传感器故障”）。
    return _dedup_texts(out)


def _extract_branch_effect(text: str) -> str:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    m = re.search(r"故障树分支\s*[：:]\s*(.+)", s)
    segment = m.group(1).strip() if m else ""
    if not segment:
        return ""

    segment = segment.split("技术关键")[0].strip()
    chain = _split_branch_chain(segment)
    if len(chain) >= 2:
        return _strip_edge_punct(chain[-1])
    return ""


def classify_role(text: str) -> str:
    s = _strip_edge_punct((text or "").strip())
    if not s:
        return "INVALID"

    if len(_clean_text(s)) < 3:
        return "INVALID"

    if s in INVALID_CONNECTORS:
        return "INVALID"

    if any(re.match(p, s) for p in INVALID_SENTENCE_PATTERNS):
        return "INVALID"

    # Strong rule: phrases with cause prefixes should always be treated as causes.
    if re.match(r"^(?:可能原因|原因|根因|诱因)(?:包括)?[：:]", s):
        return "CAUSE"

    low = s.lower()

    if any(term in low for term in TOP_EVENT_TERMS):
        return "TOP_EVENT"

    if any(re.search(pat, s) for pat in FAULT_CODE_PATTERNS):
        return "FAULT_EVENT"

    # 对FTA中常见的因果事件先判定为CAUSE，避免“传感器故障”被误归为FAULT_EVENT。
    has_object = any(t in s for t in CAUSE_OBJECT_TERMS)
    has_failure = any(t in s for t in CAUSE_FAILURE_TERMS)
    has_causal_phrase = any(v in s for v in CAUSAL_VERBS)
    if has_object and (has_failure or has_causal_phrase):
        return "CAUSE"

    if any(k in s for k in ("校验", "培训", "冗余", "缺失", "人为", "流程")):
        return "CAUSE"

    # 环境/工况类上下文在事故文本中常是上游触发因素。
    if any(k in s for k in ("低温", "高温", "环境", "温度", "湿度", "工况", "外部条件", "气压")):
        return "CAUSE"

    if any(term in s for term in FAULT_TERMS):
        return "FAULT_EVENT"

    starts_with_causal = any(s.startswith(v) for v in CAUSAL_VERBS)
    if starts_with_causal:
        return "INVALID"

    if has_failure:
        return "CAUSE"

    return "INVALID"


def normalize_cause(text: str) -> str:
    raw = _strip_edge_punct((text or "").strip())
    if not raw:
        return ""

    raw = _strip_cause_prefix(raw)
    if not raw:
        return ""

    # Merge generic causal expression: A导致B -> A（导致B）
    m = re.match(r"^(.*?)\s*(导致|引起|造成)\s*(.+)$", raw)
    if m:
        left = _strip_edge_punct(m.group(1))
        right = _strip_edge_punct(m.group(3))
        if left and right:
            raw = f"{left}（导致{right}）"

    # Fix unclosed Chinese parentheses.
    lcnt = raw.count("（")
    rcnt = raw.count("）")
    if lcnt > rcnt:
        raw += "）" * (lcnt - rcnt)

    raw = _strip_edge_punct(raw)

    if classify_role(raw) != "CAUSE":
        return ""

    return raw


def deduplicate_causes(causes: List[str]) -> List[str]:
    if not isinstance(causes, list):
        return []

    cleaned = [normalize_cause(c) for c in causes if isinstance(c, str)]
    cleaned = [c for c in cleaned if c]

    # 1) Exact semantic dedup with longest-retain rule.
    best_by_key: Dict[str, str] = {}
    for c in cleaned:
        k = _semantic_key(c)
        if not k:
            continue
        prev = best_by_key.get(k)
        if prev is None or len(_clean_text(c)) > len(_clean_text(prev)):
            best_by_key[k] = c

    uniques = list(best_by_key.values())

    # 2) Containment semantic dedup: A vs A(导致B) => keep longer one.
    sem = [_semantic_key(x) for x in uniques]
    drop = set()
    for i, a in enumerate(sem):
        if i in drop or not a:
            continue
        for j, b in enumerate(sem):
            if i == j or j in drop or not b:
                continue
            composite = any(tok in uniques[j] for tok in ("+", "＋", "->", "→", "导致", "引起", "造成"))
            # 仅在“长文本不是复合因果串”时才删除被包含的短原因，避免把原子原因误删。
            if len(a) < len(b) and a in b and not composite:
                drop.add(i)
                break

    out: List[str] = []
    seen = set()
    for i, val in enumerate(uniques):
        if i in drop:
            continue
        key = _semantic_key(val)
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out


def generate_fallback_causes(fault: str) -> List[str]:
    s = (fault or "").lower()

    if any(k in s for k in ("姿态", "星敏", "反作用轮", "imu", "天线指向", "轨控", "aocs")):
        return [
            "星敏感器测量异常",
            "反作用轮执行机构异常",
            "姿态控制回路参数失配",
        ]

    if any(k in s for k in ("温度", "过热", "偏低")):
        return [
            "温度传感器故障",
            "信号采集线路异常",
            "控制模块采集异常",
        ]

    if "压力" in s:
        return [
            "压力传感器故障",
            "管路堵塞或泄漏",
            "泵或阀异常",
        ]

    if "电流" in s:
        return [
            "电流检测异常",
            "负载异常",
            "驱动模块故障",
        ]

    return [
        "传感器故障",
        "信号线路异常",
        "控制模块故障",
    ]


# =========================
# FTA Integration
# =========================


def extract_fault_event(text: str) -> str:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not s.strip():
        return "未命名故障"

    def _compact_fault_label(raw: str) -> str:
        t = _strip_edge_punct((raw or "").replace("\n", " ").strip())
        if not t:
            return ""

        t = _strip_cause_prefix(t)
        if not t:
            return ""

        # Keep first sentence fragment to avoid carrying full narrative text.
        t = re.split(r"[。！？!?]", t)[0].strip()

        # Prefer concise segment around fault keywords.
        m = re.search(
            r"([^，；;]{0,18}(?:报警|告警|异常|故障|过低|过高|过流|过压|欠压|过温)[^，；;]{0,18})",
            t,
        )
        if m:
            t = _strip_edge_punct(m.group(1))

        # Remove common leading narrative fillers.
        t = re.sub(r"^(地面测控站接收到|数据显示|系统显示|监测到|观测到)", "", t).strip()
        t = re.sub(r"^.{0,12}接收到", "", t).strip()
        t = re.sub(r"^“[^”]{1,24}”卫星的", "", t).strip()
        t = re.sub(r"^[""“”'']?[^""“”'']{1,24}[""“”'']?卫星的", "", t).strip()
        t = _strip_edge_punct(t)

        # Length guard for UI readability.
        if len(_clean_text(t)) > 36:
            m2 = re.search(r"(报警|告警|异常|故障)", t)
            if m2:
                start = max(0, m2.start() - 10)
                end = min(len(t), m2.end() + 12)
                t = _strip_edge_punct(t[start:end])
            else:
                t = t[:24].strip()
        return t

    # Prefer explicit fault/alarm codes before generic parameter-like codes.
    preferred_fault_patterns = (
        r"\b(?:F|A|E)\d{3,5}\b",
        r"\b[A-Z]{2,}(?:-[A-Z0-9]{1,16})+\b",
        r"\b[A-Za-z]-?\d{2,5}\b",
    )

    for pat in preferred_fault_patterns:
        m = re.search(pat, s)
        if m:
            return m.group(0)

    candidates = split_into_items(s)
    fault_candidates = [c for c in candidates if classify_role(c) == "FAULT_EVENT"]
    fault_candidates = [c for c in fault_candidates if not re.match(r"^(?:可能原因|原因|根因|诱因)(?:包括)?[：:]", c)]
    if fault_candidates:
        # Prefer shorter, compact fault phrase instead of full narrative sentence.
        best = max(fault_candidates, key=lambda x: len(_clean_text(x)))
        compact = _compact_fault_label(best)
        if compact:
            return compact
        return best

    return "未命名故障"


def _extract_text_fields(items: List[dict]) -> List[str]:
    texts: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        for key in ("text", "raw_text", "description", "fault", "fault_event", "top_event", "cause"):
            v = item.get(key)
            if isinstance(v, str) and v.strip():
                texts.append(v)

        arr = item.get("causes")
        if isinstance(arr, list):
            for c in arr:
                if isinstance(c, str) and c.strip():
                    texts.append(c)

    return texts


def process_items(items: List[dict]) -> Dict[str, Any]:
    texts = _extract_text_fields(items)

    top_candidates: List[str] = []
    fault_candidates: List[str] = []
    cause_candidates: List[str] = []
    branch_effect_candidates: List[str] = []

    for text in texts:
        branch_causes = _extract_branch_causes(text)
        if branch_causes:
            cause_candidates.extend(branch_causes)

        branch_effect = _extract_branch_effect(text)
        if branch_effect:
            branch_effect_candidates.append(branch_effect)

        structure = detect_list_structure(text)
        fragments = split_into_items(text)

        # If text is not list-like and split returns empty/single weak chunk, keep original as fallback unit.
        if not fragments:
            fragments = [_strip_edge_punct(text)]
        elif not structure["is_list_like"] and len(fragments) == 1:
            fragments = [fragments[0]]

        for frag in fragments:
            role = classify_role(frag)
            if role == "TOP_EVENT":
                top_candidates.append(frag)
            elif role == "FAULT_EVENT":
                fault_candidates.append(frag)
            elif role == "CAUSE":
                norm = normalize_cause(frag)
                if norm:
                    cause_candidates.append(norm)

    top = "系统级故障"
    if top_candidates:
        top = max(top_candidates, key=lambda x: len(_clean_text(x)))
    else:
        # Honor explicit top_event from payload even when it does not match keyword heuristics.
        explicit_tops = []
        for item in items:
            if isinstance(item, dict):
                tv = item.get("top_event")
                if isinstance(tv, str) and tv.strip():
                    explicit_tops.append(tv.strip())
        if explicit_tops:
            top = max(explicit_tops, key=lambda x: len(_clean_text(x)))

    fault = "未命名故障"
    if fault_candidates:
        fault = max(fault_candidates, key=lambda x: len(_clean_text(x)))

    if fault.startswith("技术关键"):
        fault = "未命名故障"

    # Global fallback fault extraction from full text corpus.
    parsed_fault = extract_fault_event("\n".join(texts))
    if parsed_fault.startswith("技术关键"):
        parsed_fault = "未命名故障"

    branch_effect = ""
    if branch_effect_candidates:
        branch_effect = max(branch_effect_candidates, key=lambda x: len(_clean_text(x)))
        if branch_effect and classify_role(branch_effect) == "CAUSE":
            branch_effect = ""

    if fault == "未命名故障":
        fault = branch_effect or parsed_fault
    elif parsed_fault != "未命名故障":
        # Prefer compact code/event representation over verbose sentence labels.
        if len(_clean_text(fault)) > 40 or (
            parsed_fault in fault and len(_clean_text(fault)) > len(_clean_text(parsed_fault))
        ):
            fault = parsed_fault

    causes = deduplicate_causes(cause_candidates)

    # Strong constraints: top-event/result wording is not allowed in causes.
    filtered_causes: List[str] = []
    for c in causes:
        if any(t in c.lower() for t in TOP_EVENT_TERMS):
            continue
        if classify_role(c) != "CAUSE":
            continue
        filtered_causes.append(c)

    filtered_causes = deduplicate_causes(filtered_causes)
    filtered_causes = _filter_causes_by_context(filtered_causes, top=top, fault=fault)

    if len(filtered_causes) == 0:
        filtered_causes = generate_fallback_causes(fault)
        filtered_causes = _filter_causes_by_context(filtered_causes, top=top, fault=fault)

    if len(filtered_causes) == 0:
        filtered_causes = ["原因待补充"]

    return {
        "top": top,
        "fault": fault,
        "causes": filtered_causes,
    }


def build_fta(items: List[dict]) -> Dict[str, Any]:
    if not isinstance(items, list):
        raise ValueError("items must be a list")

    parsed = process_items(items)

    top = parsed.get("top") or "系统级故障"
    fault = parsed.get("fault") or "未命名故障"
    causes = parsed.get("causes") or []
    if not isinstance(causes, list):
        causes = []
    causes = _filter_causes_by_context(_dedup_texts(causes), top=str(top), fault=str(fault))
    if len(causes) == 0:
        causes = _filter_causes_by_context(generate_fallback_causes(str(fault)), top=str(top), fault=str(fault))
    if len(causes) == 0:
        causes = ["原因待补充"]

    return {
        "top": top,
        "fault": fault,
        "gate": "OR",
        "causes": causes,
    }


def build_dot_from_fta(fta: Dict[str, Any]) -> str:
    if not isinstance(fta, dict):
        raise ValueError("fta must be a dict")

    top = str(fta.get("top") or "系统级故障")
    fault = str(fta.get("fault") or "未命名故障")
    gate = str(fta.get("gate") or "OR").upper()
    if gate not in {"OR", "AND"}:
        gate = "OR"

    causes = fta.get("causes", [])
    if not isinstance(causes, list):
        causes = []

    cleaned_causes = _filter_causes_by_context(
        _dedup_texts([c for c in causes if isinstance(c, str)]),
        top=top,
        fault=fault,
    )
    if len(cleaned_causes) == 0:
        cleaned_causes = _filter_causes_by_context(generate_fallback_causes(fault), top=top, fault=fault)
    if len(cleaned_causes) == 0:
        cleaned_causes = ["原因待补充"]

    intermediates_raw = fta.get("intermediates") if isinstance(fta.get("intermediates"), list) else []
    cleaned_intermediates: List[Dict[str, Any]] = []
    seen_mid = set()
    for item in intermediates_raw:
        if not isinstance(item, dict):
            continue
        name = _strip_edge_punct(str(item.get("name") or item.get("fault") or "").strip())
        if not name:
            continue
        nk = _semantic_key(name)
        if not nk or nk in seen_mid:
            continue
        seen_mid.add(nk)

        mgate = str(item.get("gate") or "OR").upper()
        if mgate not in {"OR", "AND"}:
            mgate = "OR"

        mcauses_raw = item.get("causes") if isinstance(item.get("causes"), list) else []
        mcauses = _filter_causes_by_context(
            _dedup_texts([c for c in mcauses_raw if isinstance(c, str)]),
            top=top,
            fault=name,
        )
        if len(mcauses) == 0:
            mcauses = _filter_causes_by_context(generate_fallback_causes(name), top=top, fault=name)
        if len(mcauses) == 0:
            mcauses = ["原因待补充"]

        cleaned_intermediates.append({"name": name, "gate": mgate, "causes": mcauses})

    def _is_fault_code_only(text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return False
        return any(re.fullmatch(pat, t) for pat in FAULT_CODE_PATTERNS)

    render_fault_node = bool(fault.strip()) and fault.strip() != top.strip() and not _is_fault_code_only(fault)

    lines = [
        "digraph FTA {",
        "  rankdir=TB;",
        "  graph [fontname=Helvetica, nodesep=0.35, ranksep=0.35];",
        "  node [fontname=Helvetica];",
        "  edge [fontname=Helvetica];",
        f'  top [label="{top.replace(chr(34), chr(39))}", shape=doubleoctagon, style=filled, fillcolor=lightcoral];',
        f'  gate [label="{gate}", shape=diamond, width=0.5, height=0.5, fixedsize=true];',
    ]

    if cleaned_intermediates:
        lines.append("  top -> gate;")

        for i, mid in enumerate(cleaned_intermediates, start=1):
            eid = f"e{i}"
            gid = f"g{i+1}"
            label = str(mid.get("name") or "").replace('"', "'")
            mgate = str(mid.get("gate") or "OR")
            lines.append(f'  {eid} [label="{label}", shape=box];')
            lines.append(f"  gate -> {eid};")
            lines.append(f'  {gid} [label="{mgate}", shape=diamond, width=0.45, height=0.45, fixedsize=true];')
            lines.append(f"  {eid} -> {gid};")

            lines.append("  { rank=same;")
            for j, cause in enumerate(mid.get("causes") or [], start=1):
                cid = f"c{i}_{j}"
                clabel = str(cause or "").replace('"', "'")
                lines.append(f'  {cid} [label="{clabel}", shape=ellipse];')
            lines.append("  }")

            for j, _cause in enumerate(mid.get("causes") or [], start=1):
                cid = f"c{i}_{j}"
                lines.append(f"  {gid} -> {cid};")

        lines.append("}")
        return "\n".join(lines)

    if render_fault_node:
        lines.append(f'  fault [label="{fault.replace(chr(34), chr(39))}", shape=box];')
        lines.append("  top -> fault;")
        lines.append("  fault -> gate;")
    else:
        lines.append("  top -> gate;")

    lines.append("  { rank=same;")

    for i, cause in enumerate(cleaned_causes, start=1):
        node_id = f"c{i}"
        label = cause.replace('"', "'")
        lines.append(f'  {node_id} [label="{label}", shape=ellipse];')
    lines.append("  }")

    for i, _cause in enumerate(cleaned_causes, start=1):
        node_id = f"c{i}"
        lines.append(f"  gate -> {node_id};")

    lines.append("}")
    return "\n".join(lines)


def build_fta_dot(items: List[dict]) -> str:
    return build_dot_from_fta(build_fta(items))


__all__ = [
    "detect_list_structure",
    "split_into_items",
    "classify_role",
    "normalize_cause",
    "deduplicate_causes",
    "generate_fallback_causes",
    "extract_fault_event",
    "process_items",
    "build_fta",
    "build_dot_from_fta",
    "build_fta_dot",
]
