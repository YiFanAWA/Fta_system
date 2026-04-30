import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


_NOISE_CAUSE_RE = re.compile(r'^(?:[:：%\s].*|.*bin["\'”’)]?.*|检查.*|重新.*|请.*|见.*)$', re.IGNORECASE)
_TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")
_FAULT_CODE_RE = re.compile(r"[A-Z]\d{5}", re.IGNORECASE)

# Basic query expansion to improve recall for common industrial terms.
_SYNONYM_GROUPS: List[List[str]] = [
    ["编码器", "encoder"],
    ["控制单元", "cu", "controlunit"],
    ["驱动", "drive", "driveliq", "drive-cliq"],
    ["固件", "firmware"],
    ["参数", "parameter", "params"],
    ["过热", "温度", "热"],
    ["通讯", "通信", "网络"],
    ["安全", "si", "safety"],
]


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) >= 2]


def _expand_tokens(tokens: List[str]) -> List[str]:
    if not tokens:
        return []

    out = set(tokens)
    token_set = set(tokens)
    for group in _SYNONYM_GROUPS:
        group_set = {x.lower() for x in group}
        if token_set.intersection(group_set):
            out.update(group_set)
    return list(out)


def _score_text(query: str, text: str) -> int:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0
    haystack = (text or "").lower()
    return sum(1 for t in q_tokens if t in haystack)


def _extract_fault_codes(query: str) -> List[str]:
    return [x.upper() for x in _FAULT_CODE_RE.findall(query or "")]


def _hybrid_score(query: str, doc: Dict[str, Any]) -> float:
    q_tokens = _expand_tokens(_tokenize(query))
    if not q_tokens and not _extract_fault_codes(query):
        return 0.0

    code = str(doc.get("fault_code", "")).strip().upper()
    component = str(doc.get("component", "")).strip().lower()
    description = str(doc.get("description", "")).strip().lower()
    causes = [str(x).strip().lower() for x in (doc.get("causes") or []) if str(x).strip()]
    params = [str(x).strip().lower() for x in (doc.get("parameters") or []) if str(x).strip()]
    full_text = str(doc.get("text", "")).lower()

    score = 0.0
    matched = 0
    for t in q_tokens:
        hit = False
        if t in description:
            score += 2.0
            hit = True
        if t in component:
            score += 1.8
            hit = True
        if any(t in c for c in causes):
            score += 1.6
            hit = True
        if any(t == p or t in p for p in params):
            score += 1.4
            hit = True
        if t in full_text:
            score += 0.5
            hit = True
        if hit:
            matched += 1

    for q_code in _extract_fault_codes(query):
        if q_code == code:
            score += 8.0

    if q_tokens:
        coverage = matched / len(q_tokens)
        score += coverage * 2.0

    return score


def _is_noise_cause(text: str) -> bool:
    name = _safe_text(text)
    if not name:
        return True
    if _NOISE_CAUSE_RE.match(name):
        return True
    return False


def _dedup_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def normalize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for item in records:
        if not isinstance(item, dict):
            continue

        code = _safe_text(item.get("fault_code")).upper()
        if not code:
            continue

        component = _safe_text(item.get("component"))
        description = _safe_text(item.get("description"))

        causes_raw = item.get("causes", [])
        if not isinstance(causes_raw, list):
            causes_raw = []
        causes = [_safe_text(c) for c in causes_raw if isinstance(c, str)]
        causes = [c for c in causes if c and not _is_noise_cause(c)]

        params_raw = item.get("parameters", [])
        if not isinstance(params_raw, list):
            params_raw = []
        params = [_safe_text(p) for p in params_raw if isinstance(p, str) and _safe_text(p)]

        if code not in merged:
            merged[code] = {
                "fault_code": code,
                "component": component,
                "description": description,
                "causes": _dedup_keep_order(causes),
                "parameters": _dedup_keep_order(params),
            }
            continue

        target = merged[code]
        if not target["component"] and component:
            target["component"] = component
        if (not target["description"] or len(description) > len(target["description"])) and description:
            target["description"] = description

        target["causes"] = _dedup_keep_order(target["causes"] + causes)
        target["parameters"] = _dedup_keep_order(target["parameters"] + params)

    return sorted(merged.values(), key=lambda x: x["fault_code"])


def build_docs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for r in records:
        causes = r.get("causes", []) if isinstance(r.get("causes"), list) else []
        params = r.get("parameters", []) if isinstance(r.get("parameters"), list) else []

        causes_text = "、".join(causes) if causes else "未提供"
        params_text = "、".join(params) if params else "未提供"

        text = (
            f"故障代码：{r.get('fault_code', '')}\n"
            f"组件：{r.get('component', '')}\n"
            f"故障描述：{r.get('description', '')}\n"
            f"可能原因：{causes_text}\n"
            f"相关参数：{params_text}\n"
        )

        docs.append(
            {
                "fault_code": r.get("fault_code", ""),
                "component": r.get("component", ""),
                "description": r.get("description", ""),
                "causes": causes,
                "parameters": params,
                "text": text,
            }
        )
    return docs


def find_latest_records_file(output_dir: Path) -> Optional[Path]:
    files = sorted(output_dir.glob("*_extracted_faults.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_records_from_file(file_path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    raw_records = payload.get("records", []) if isinstance(payload, dict) else []
    if not isinstance(raw_records, list):
        return []
    return normalize_records([r for r in raw_records if isinstance(r, dict)])


def simple_search(query: str, docs: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        score = _hybrid_score(query, doc)
        if score <= 0.0:
            continue
        ranked.append({"score": score, "doc": doc})

    ranked.sort(key=lambda x: (-x["score"], str(x["doc"].get("fault_code", ""))))
    return [item["doc"] for item in ranked[:top_k]]


def compose_answer(question: str, hits: List[Dict[str, Any]]) -> str:
    if not hits:
        return "未在当前语料中检索到高相关条目。建议补充故障代码、组件名或参数编号后重试。"

    top = hits[0]
    code = top.get("fault_code", "")
    desc = top.get("description", "")
    causes = top.get("causes", []) if isinstance(top.get("causes"), list) else []
    params = top.get("parameters", []) if isinstance(top.get("parameters"), list) else []

    lines = [
        "【问题结论】",
        f"{code}：{desc}" if code else desc,
        "",
        "【原因分析】",
    ]

    if causes:
        for cause in causes[:6]:
            lines.append(f"- {cause}")
    else:
        lines.append("- 该条目未给出明确原因。")

    lines.append("")
    lines.append("【相关参数】")
    if params:
        lines.append("- " + "、".join(params[:10]))
    else:
        lines.append("- 该条目未给出参数。")

    lines.append("")
    lines.append("【检索说明】")
    lines.append(f"- 命中条目数：{len(hits)}")
    lines.append(f"- 用户问题：{question}")

    return "\n".join(lines)
