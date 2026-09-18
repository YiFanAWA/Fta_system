import json
import re
import time
from typing import Any, Dict, List, Optional

from config import (
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MAX_RETRIES,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from extraction_contract import (
    ExtractionDiagnostic,
    ExtractionResult,
    ExtractionStatus,
)
from model_client import ModelClient, RetryingModelClient
from openai_model_client import OpenAICompatibleModelClient
from prompt_templates import (
    build_analysis_report_prompt,
    build_draft_review_prompt,
    build_failure_generation_prompt,
    build_text_extraction_prompt,
)
from text_extraction_adapter import TextExtractionAdapter
from utils import log


_MODEL_CLIENT = OpenAICompatibleModelClient(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
    model=OPENAI_MODEL,
    timeout_seconds=OPENAI_TIMEOUT_SECONDS,
)
_TEXT_MODEL_CLIENT = RetryingModelClient(
    _MODEL_CLIENT,
    max_retries=OPENAI_MAX_RETRIES,
    delay_seconds=2.0,
)

def _chat_completion_request(prompt: str) -> str:
    return _MODEL_CLIENT.complete(prompt)


def _extract_json_array(text):
    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1 or start >= end:
        raise ValueError("AI输出中未找到有效的JSON数组")

    return text[start : end + 1]


def _extract_json_object(text):
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start >= end:
        raise ValueError("AI输出中未找到有效的JSON对象")

    return text[start : end + 1]


def _to_probability(value):
    if value is None:
        return None

    try:
        prob = float(value)
    except (TypeError, ValueError):
        return None

    if prob < 0:
        return 0.0

    if prob > 1:
        return 1.0

    return prob


def _normalize_failure_item(item):
    if isinstance(item, str):
        name = item.strip()
        if not name:
            return None
        return {
            "name": name,
            "probability": None,
            "gate": "OR",
            "causes": []
        }

    if not isinstance(item, dict):
        return None

    raw_name = item.get("name", "")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return None

    gate = item.get("gate", "OR")
    if not isinstance(gate, str) or gate.upper() not in {"AND", "OR"}:
        gate = "OR"

    causes_raw = item.get("causes", [])
    if not isinstance(causes_raw, list):
        causes_raw = []

    causes = []
    seen_causes = set()
    for cause in causes_raw:
        normalized_cause = _normalize_failure_item(cause)
        if not normalized_cause:
            continue
        cause_name = normalized_cause["name"]
        if cause_name in seen_causes:
            continue
        seen_causes.add(cause_name)
        causes.append(normalized_cause)

    return {
        "name": raw_name.strip(),
        "probability": _to_probability(item.get("probability")),
        "gate": gate.upper(),
        "causes": causes
    }


def _normalize_failures(data):
    if not isinstance(data, list):
        raise ValueError("AI输出不是列表格式")

    cleaned = []
    seen = set()

    for item in data:
        normalized = _normalize_failure_item(item)
        if not normalized:
            continue

        name = normalized["name"]
        if name in seen:
            continue

        seen.add(name)
        cleaned.append(normalized)

    if not cleaned:
        raise ValueError("AI未返回有效故障事件")

    return cleaned


def _chat_with_retry(prompt):
    last_error = None
    for attempt in range(1, OPENAI_MAX_RETRIES + 2):
        try:
            return _chat_completion_request(prompt)
        except Exception as exc:
            last_error = exc
            log(
                f"调用AI接口失败(第{attempt}次, model={OPENAI_MODEL}, "
                f"base={OPENAI_API_BASE or 'default'}): {exc}"
            )
            if attempt <= OPENAI_MAX_RETRIES:
                time.sleep(2)

    raise RuntimeError("调用AI接口失败，请检查API_BASE、KEY或网络连接") from last_error


def answer_question_with_context(question: str, hits: List[Dict[str, Any]], system: Optional[str] = None) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("未配置OPENAI_API_KEY环境变量")

    safe_question = (question or "").strip()
    if not safe_question:
        raise ValueError("question不能为空")

    if not isinstance(hits, list) or not hits:
        raise ValueError("hits不能为空")

    context_blocks: List[str] = []
    for idx, item in enumerate(hits[:5], start=1):
        if not isinstance(item, dict):
            continue

        code = str(item.get("fault_code", "")).strip()
        component = str(item.get("component", "")).strip()
        description = str(item.get("description", "")).strip()
        causes = item.get("causes", []) if isinstance(item.get("causes"), list) else []
        params = item.get("parameters", []) if isinstance(item.get("parameters"), list) else []
        extra_text = str(item.get("text", "")).strip()

        causes_text = "、".join([str(c).strip() for c in causes if str(c).strip()]) or "未提供"
        params_text = "、".join([str(p).strip() for p in params if str(p).strip()]) or "未提供"
        block = (
            f"[{idx}] 故障代码: {code or '未知'}\n"
            f"组件: {component or '未知'}\n"
            f"故障描述: {description or '未提供'}\n"
            f"可能原因: {causes_text}\n"
            f"相关参数: {params_text}"
        )
        if extra_text:
            block += f"\n补充上下文:\n{extra_text}"
        context_blocks.append(block)

    if not context_blocks:
        raise ValueError("hits中没有可用内容")

    system_name = (system or "未指定系统").strip()
    prompt = (
        "你是工业故障诊断助手。请基于给定知识条目回答用户问题。\n"
        "要求:\n"
        "1) 优先使用提供的知识条目作为证据，避免与证据冲突。\n"
        "2) 用中文输出，结构包含: 结论、可能原因、建议排查步骤。\n"
        "3) 每条关键结论后追加证据编号，如[1]、[2]，编号对应下方知识条目。\n"
        "4) 若证据不足，明确说明不足，并补充可执行的通用工程建议（标注为“通用建议”）。\n"
        "5) 若多个条目冲突，先说明冲突再给出保守建议。\n\n"
        "补充说明:\n"
        "- 若知识条目包含故障树DOT/结构化摘要，请优先提取: 顶事件、逻辑门类型、父子关系、关键路径再解释。\n"
        "- 若已给出布局方向（如左到右/LR），解释时保持该方向的因果阅读顺序。\n\n"
        f"系统: {system_name}\n"
        f"用户问题: {safe_question}\n\n"
        "知识条目:\n"
        + "\n\n".join(context_blocks)
    )

    return _chat_with_retry(prompt)


def answer_general_question(question: str, system: Optional[str] = None) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("未配置OPENAI_API_KEY环境变量")

    safe_question = (question or "").strip()
    if not safe_question:
        raise ValueError("question不能为空")

    system_name = (system or "未指定系统").strip()
    prompt = (
        "你是工业智能助手。请对用户问题给出清晰、可执行的中文回答。\n"
        "要求:\n"
        "1) 回答结构包含: 结论、可能原因、建议步骤。\n"
        "2) 如果问题信息不足，明确说明并给出补充信息建议。\n"
        "3) 避免编造具体参数值或现场结论。\n\n"
        f"系统: {system_name}\n"
        f"用户问题: {safe_question}\n"
    )

    return _chat_with_retry(prompt)


def generate_failure_events(
    system_description,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
):
    if not isinstance(system_description, str) or not system_description.strip():
        raise ValueError("system_description不能为空")

    if not OPENAI_API_KEY:
        raise RuntimeError("未配置OPENAI_API_KEY环境变量")

    prompt = build_failure_generation_prompt(
        system_description=system_description,
        profile=prompt_profile,
        custom_instructions=custom_instructions,
    )

    result = _chat_with_retry(prompt)

    try:
        payload = json.loads(result)
    except json.JSONDecodeError:
        # New prompt asks for a JSON object; keep backward compatibility with array output.
        try:
            payload = json.loads(_extract_json_object(result))
        except Exception:
            payload = json.loads(_extract_json_array(result))

    # Compatible normalization:
    # 1) legacy format: List[Failure]
    # 2) new format: recursive object with top and causes
    if isinstance(payload, dict):
        causes = payload.get("causes", []) if isinstance(payload.get("causes", []), list) else []
        if causes:
            payload = causes
        else:
            payload = [payload]

    return _normalize_failures(payload)


def _normalize_text_fault_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    fault_code = item.get("fault_code")
    description = item.get("description")

    if fault_code is not None and (
        not isinstance(fault_code, str) or not fault_code.strip()
    ):
        return None
    if not isinstance(description, str) or not description.strip():
        return None

    component = item.get("component", "")
    if not isinstance(component, str):
        component = ""

    causes_raw = item.get("causes", [])
    if not isinstance(causes_raw, list):
        causes_raw = []
    causes: List[str] = []
    cause_seen = set()
    for cause in causes_raw:
        if not isinstance(cause, str):
            continue
        name = cause.strip()
        if not name or name in cause_seen:
            continue
        cause_seen.add(name)
        causes.append(name)

    params_raw = item.get("parameters", [])
    if not isinstance(params_raw, list):
        params_raw = []
    parameters: List[str] = []
    param_seen = set()
    for p in params_raw:
        if not isinstance(p, str):
            continue
        name = p.strip()
        if not name or name in param_seen:
            continue
        param_seen.add(name)
        parameters.append(name)

    return {
        "fault_code": fault_code.strip().upper() if fault_code else None,
        "component": component.strip(),
        "description": description.strip(),
        "causes": causes,
        "parameters": parameters,
    }


def _merge_fault_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[tuple, Dict[str, Any]] = {}

    for item in records:
        normalized = _normalize_text_fault_item(item)
        if not normalized:
            continue

        code = normalized["fault_code"]
        key = (
            "code",
            code,
        ) if code else (
            "fact",
            normalized.get("component", ""),
            normalized.get("description", ""),
        )
        entry = merged.get(key)
        if not entry:
            merged[key] = normalized
            continue

        if not entry.get("description") and normalized.get("description"):
            entry["description"] = normalized["description"]
        if not entry.get("component") and normalized.get("component"):
            entry["component"] = normalized["component"]

        for cause in normalized.get("causes", []):
            if cause not in entry["causes"]:
                entry["causes"].append(cause)

        for p in normalized.get("parameters", []):
            if p not in entry["parameters"]:
                entry["parameters"].append(p)

    return sorted(merged.values(), key=lambda x: x.get("fault_code", ""))


def _shorten_text(text: str, max_len: int = 28) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + "..."


def _extract_component_hint(text: str) -> str:
    component_keywords = [
        "控制单元", "功率单元", "电机模块", "液压模块", "编码器", "传感器",
        "端子模块", "通讯组件", "DRIVE-CLiQ", "PROFIBUS", "PROFINET",
    ]
    for key in component_keywords:
        if key in text:
            return key
    return ""


def _extract_records_by_rules(source_text: str) -> List[Dict[str, Any]]:
    # Rule fallback: for highly structured manuals with explicit fault codes,
    # extract code/description/parameters directly to improve recall and stability.
    code_pattern = re.compile(r"\b([FA]\d{5})(?:（[^）]*）)?\b", re.IGNORECASE)
    param_pattern = re.compile(r"\b([pr]\d{4}(?:\[[^\]]+\])?)\b", re.IGNORECASE)

    matches = list(code_pattern.finditer(source_text or ""))
    if not matches:
        return _extract_records_without_standard_codes(source_text)

    records: List[Dict[str, Any]] = []
    for idx, match in enumerate(matches):
        code = match.group(1).upper()
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source_text)
        window = source_text[start:end].replace("\n", " ").replace("\r", " ").strip()

        desc = window
        for marker in ["故障现象为", "故障现象：", "故障现象", "信息值格式为", "处理建议", "处理细则"]:
            if marker in window:
                desc = window.split(marker, 1)[1].strip()
                break

        sentence_split = re.split(r"[。；;]", desc)
        desc = (sentence_split[0] if sentence_split else desc).strip()
        desc = re.sub(r"\s+", " ", desc)
        if not desc:
            desc = window[:80]

        parameters = []
        seen_params = set()
        for p in param_pattern.findall(window):
            p_norm = p.upper()
            if p_norm not in seen_params:
                seen_params.add(p_norm)
                parameters.append(p_norm)

        cause_candidates = []
        for marker in ["常见原因", "可能原因", "原因", "故障值"]:
            if marker in window:
                tail = window.split(marker, 1)[1]
                parts = re.split(r"[，,。；;]", tail)
                for part in parts[:3]:
                    text = part.strip()
                    if 2 <= len(text) <= 30:
                        cause_candidates.append(text)

        records.append(
            {
                "fault_code": code,
                "component": _extract_component_hint(window),
                "description": desc,
                "causes": cause_candidates,
                "parameters": parameters,
            }
        )

    return _merge_fault_records(records)


def _extract_records_without_standard_codes(source_text: str) -> List[Dict[str, Any]]:
    text = (source_text or "").strip()
    if not text:
        return []

    incident_code_pattern = re.compile(r"\b([A-Z]{2,}-\d{4}-\d{4}-[A-Z0-9]+-\d+)\b")
    incident_match = incident_code_pattern.search(text)
    fault_code = incident_match.group(1).upper() if incident_match else None

    normalized = re.sub(r"\s+", " ", text)

    # Split with causal markers first, then punctuation.
    parts = re.split(r"(?:随后|导致|并且|同时|然后|因此|故障现象描述[:：]|[。；;])", normalized)
    clauses = []
    noise_markers = ["故障编号", "发生时间", "故障等级", "接收到", "报警"]
    for part in parts:
        item = part.strip(" ，,：:")
        if len(item) < 6:
            continue
        if any(m in item for m in noise_markers):
            continue
        if item in clauses:
            continue
        clauses.append(item)

    if not clauses:
        return []

    description = clauses[0]
    causes = []
    for clause in clauses[1:6]:
        short = _shorten_text(clause, max_len=36)
        if short and short not in causes:
            causes.append(short)

    parameters = []
    for m in re.findall(r"\b([pr]\d{4}(?:\[[^\]]+\])?)\b", normalized, flags=re.IGNORECASE):
        p = m.upper()
        if p not in parameters:
            parameters.append(p)

    return [
        {
            "fault_code": fault_code,
            "component": _extract_component_hint(normalized),
            "description": _shorten_text(description, max_len=48),
            "causes": causes,
            "parameters": parameters,
        }
    ]


def _build_text_extraction_adapter(
    chunk_size_chars: int,
    overlap_chars: int,
    prompt_profile: Optional[str],
    custom_instructions: Optional[str],
    model_client: Optional[ModelClient] = None,
    fallback_builder=None,
) -> TextExtractionAdapter:
    def prompt_builder(chunk_text: str, index: int, total: int) -> str:
        return build_text_extraction_prompt(
            chunk_text=chunk_text,
            index=index + 1,
            total=total,
            profile=prompt_profile,
            custom_instructions=custom_instructions,
        )

    return TextExtractionAdapter(
        model_client if model_client is not None else _TEXT_MODEL_CLIENT,
        prompt_builder,
        chunk_size_chars=chunk_size_chars,
        overlap_chars=overlap_chars,
        fallback_builder=fallback_builder,
    )


def build_text_extraction_adapter(
    chunk_size_chars: int = 6000,
    overlap_chars: int = 300,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    model_client: Optional[ModelClient] = None,
) -> TextExtractionAdapter:
    """Build the configured text extractor for application-layer injection."""
    return _build_text_extraction_adapter(
        chunk_size_chars=chunk_size_chars,
        overlap_chars=overlap_chars,
        prompt_profile=prompt_profile,
        custom_instructions=custom_instructions,
        model_client=model_client,
    )


def extract_fault_result_from_text(
    source_text: str,
    chunk_size_chars: int = 6000,
    overlap_chars: int = 300,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    model_client: Optional[ModelClient] = None,
) -> ExtractionResult:
    """Return the new structured extraction contract for one source text."""
    adapter = _build_text_extraction_adapter(
        chunk_size_chars=chunk_size_chars,
        overlap_chars=overlap_chars,
        prompt_profile=prompt_profile,
        custom_instructions=custom_instructions,
        model_client=model_client,
    )
    return adapter.extract(source_text)


def _record_to_legacy_dict(record) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "component": record.component or "",
        "description": record.description,
        "causes": list(record.causes),
        "parameters": list(record.parameters),
    }
    if record.confidence is not None:
        result["confidence"] = record.confidence
    return result


def _diagnostic_to_dict(diagnostic: ExtractionDiagnostic) -> Dict[str, Any]:
    return {
        "code": diagnostic.code,
        "message": diagnostic.message,
        "stage": diagnostic.stage,
        "retryable": diagnostic.retryable,
    }


def extract_fault_records_from_text(
    source_text: str,
    chunk_size_chars: int = 6000,
    overlap_chars: int = 300,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> Dict[str, Any]:
    """Compatibility projection for existing API and Agent callers.

    New code should consume extract_fault_result_from_text instead.
    """
    adapter = _build_text_extraction_adapter(
        chunk_size_chars=chunk_size_chars,
        overlap_chars=overlap_chars,
        prompt_profile=prompt_profile,
        custom_instructions=custom_instructions,
        fallback_builder=_extract_records_by_rules,
    )
    result = adapter.extract(source_text)

    if result.status is ExtractionStatus.FAILED:
        diagnostic = result.diagnostics[0]
        raise RuntimeError(f"{diagnostic.code}: {diagnostic.message}")
    if result.status is ExtractionStatus.EMPTY:
        raise ValueError("未从文本中抽取到有效故障记录")

    chunk_reports = [
        {
            **report,
            "diagnostic_codes": list(report.get("diagnostic_codes", ())),
        }
        for report in adapter.last_chunk_reports
    ]
    model_chunk_count = sum(
        1 for report in chunk_reports if report.get("source") == "model"
    )
    return {
        "chunk_count": model_chunk_count,
        "chunk_size_chars": chunk_size_chars,
        "overlap_chars": overlap_chars,
        "records": [_record_to_legacy_dict(record) for record in result.records],
        "chunks": chunk_reports,
        "status": result.status.value,
        "diagnostics": [
            _diagnostic_to_dict(diagnostic) for diagnostic in result.diagnostics
        ],
    }


def convert_fault_records_to_failures(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError("records必须是列表")

    failures: List[Dict[str, Any]] = []
    seen = set()

    effect_markers = [
        "报警", "中断", "骤降", "偏离", "失控", "旋转", "停止", "停机", "异常报警"
    ]

    def _is_effect_like(text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return True
        return any(m in t for m in effect_markers)

    def _infer_gate(description: str, causes_count: int) -> str:
        if causes_count <= 1:
            return "OR"
        d = (description or "").lower()
        and_markers = ["同时", "并且", "均", "均为", "且", "协同", "共同"]
        seq_markers = ["随后", "然后", "导致", "进而"]
        if any(k in d for k in and_markers) or any(k in d for k in seq_markers):
            return "AND"
        return "OR"

    def _build_incident_hierarchy(normalized: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        code = normalized["fault_code"]
        text = " ".join([
            normalized.get("description", ""),
            " ".join(normalized.get("causes", []) or []),
        ])

        is_incident_code = bool(
            re.match(r"^[A-Z]{2,}-\d{4}-\d{4}-[A-Z0-9]+-\d+$", code or "")
        )
        has_aocs_keywords = any(k in text for k in ["星敏感器", "滤波器", "飞轮", "姿态", "天线", "链路"])
        if not (is_incident_code or has_aocs_keywords):
            return None

        branches = []

        if any(k in text for k in ["星敏感器", "滤波器", "姿态确定", "输出数据不一致"]):
            control_causes = []
            if "A" in text or "星敏感器A" in text:
                control_causes.append({"name": "星敏感器A异常", "probability": None, "gate": "OR", "causes": []})
            if "B" in text or "星敏感器B" in text:
                control_causes.append({"name": "星敏感器B异常", "probability": None, "gate": "OR", "causes": []})
            control_causes.append({"name": "姿态融合算法容错参数不当", "probability": None, "gate": "OR", "causes": []})
            branches.append(
                {
                    "name": "姿态确定系统输出错误数据",
                    "probability": None,
                    "gate": "OR",
                    "causes": control_causes,
                }
            )

        if any(k in text for k in ["飞轮", "转速异常", "饱和"]):
            branches.append(
                {
                    "name": "反作用飞轮组执行异常",
                    "probability": None,
                    "gate": "OR",
                    "causes": [
                        {"name": "飞轮Y轴转速异常饱和", "probability": None, "gate": "OR", "causes": []},
                        {"name": "飞轮驱动控制回路异常", "probability": None, "gate": "OR", "causes": []},
                    ],
                }
            )

        if not branches:
            return None

        return {
            "name": f"{code + ' ' if code else ''}姿态控制链故障",
            "probability": None,
            "gate": "OR",
            "causes": branches,
            "metadata": {
                "fault_code": code,
                "component": normalized.get("component", ""),
                "parameters": normalized.get("parameters", []),
            },
        }

    for item in records:
        normalized = _normalize_text_fault_item(item)
        if not normalized:
            continue

        incident = _build_incident_hierarchy(normalized)
        if incident:
            incident_name = incident["name"]
            if incident_name not in seen:
                seen.add(incident_name)
                failures.append(incident)
            continue

        code = normalized["fault_code"]
        desc = normalized["description"]
        name = f"{code + ' ' if code else ''}{_shorten_text(desc)}".strip()
        if name in seen:
            continue

        seen.add(name)
        clean_causes = []
        for cause in normalized["causes"]:
            if _is_effect_like(cause):
                continue
            if cause not in clean_causes:
                clean_causes.append(cause)

        # Keep structure informative: if filtering leaves too few causes,
        # retain up to two original causes as fallback candidates.
        if len(clean_causes) < 2:
            for cause in normalized["causes"]:
                c = (cause or "").strip()
                if not c or c in clean_causes:
                    continue
                clean_causes.append(c)
                if len(clean_causes) >= 2:
                    break

        gate = _infer_gate(desc, len(clean_causes))
        causes = [{"name": cause, "probability": None, "gate": "OR", "causes": []} for cause in clean_causes]

        failures.append(
            {
                "name": name,
                "probability": None,
                "gate": gate,
                "causes": causes,
                "metadata": {
                    "fault_code": code,
                    "component": normalized["component"],
                    "parameters": normalized["parameters"],
                },
            }
        )

    if not failures:
        raise ValueError("records中没有可转换的故障事件")

    return failures


def analyze_fault_tree_report(
    system_description,
    top_event,
    tree,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
):
    if not isinstance(system_description, str) or not system_description.strip():
        raise ValueError("system_description不能为空")

    if not isinstance(top_event, str) or not top_event.strip():
        raise ValueError("top_event不能为空")

    if not isinstance(tree, dict):
        raise ValueError("tree必须是字典")

    tree_text = json.dumps(tree, ensure_ascii=False, indent=2)

    prompt = build_analysis_report_prompt(
        system_description=system_description,
        top_event=top_event,
        tree_text=tree_text,
        profile=prompt_profile,
        custom_instructions=custom_instructions,
    )

    result = _chat_with_retry(prompt)

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return json.loads(_extract_json_object(result))


def review_fault_tree_draft(
    system_description,
    top_event,
    tree,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
):
    if not isinstance(system_description, str) or not system_description.strip():
        raise ValueError("system_description不能为空")

    if not isinstance(top_event, str) or not top_event.strip():
        raise ValueError("top_event不能为空")

    if not isinstance(tree, dict):
        raise ValueError("tree必须是字典")

    tree_text = json.dumps(tree, ensure_ascii=False, indent=2)

    prompt = build_draft_review_prompt(
        system_description=system_description,
        top_event=top_event,
        tree_text=tree_text,
        profile=prompt_profile,
        custom_instructions=custom_instructions,
    )

    result = _chat_with_retry(prompt)

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return json.loads(_extract_json_object(result))
