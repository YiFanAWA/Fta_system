from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import re

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_workflow import run_agent_workflow

from ai_module import (
    analyze_fault_tree_report,
    answer_general_question,
    answer_question_with_context,
    build_text_extraction_adapter,
    convert_fault_records_to_failures,
    extract_fault_records_from_text,
    generate_failure_events,
    review_fault_tree_draft,
)
from extraction_application_service import ExtractionApplicationService
from extraction_contract import EvidenceSpan, FaultRecord
from build_contract import FaultTreeBuildAttempt
from config import ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE, EXTRACTION_DB_PATH
from fault_tree_build_service import FaultTreeBuildService
from sqlite_extraction_repository import SQLiteExtractionWorkflowRepository
from release_contract import ReleaseBlock, ReleasedExtractionResult
from release_service import FaultRecordReleaseService
from review_contract import (
    FaultRecordReview,
    PendingReviewItem,
    ReviewStatus,
    ReviewableExtractionResult,
)
from review_decision_service import ReviewDecisionService
from fta_llm_pipeline import extract_fta_structure, generate_dot
from fta_dot_builder import (
    build_dot_from_fta,
    build_fta,
    deduplicate_causes,
    extract_fault_event,
    generate_fallback_causes,
)
from fta_generator import build_fault_tree
from file_text_extractor import FileTextExtractionError, extract_text_from_uploaded_file
from kg_builder import create_failure_nodes
from kg_reasoner import get_failure_paths, query_knowledge_graph
from utils import log, save_json, save_text
from vector_store import (
    build_docs,
    compose_answer,
    find_latest_records_file,
    load_records_from_file,
    simple_search,
)
from visualizer import export_visuals
from xml_exporter import export_xml


class FailureInput(BaseModel):
    name: str = Field(..., min_length=1)
    probability: Optional[float] = None
    gate: Optional[Literal["AND", "OR"]] = "OR"
    causes: List["FailureInput"] = Field(default_factory=list)


if hasattr(FailureInput, "model_rebuild"):
    FailureInput.model_rebuild()
else:
    FailureInput.update_forward_refs()


class GenerateFTARequest(BaseModel):
    system: str = Field(..., min_length=1)
    top_event: str = Field(..., min_length=1)
    source: Literal["ai", "manual", "text"] = "ai"
    manual_failures: List[FailureInput] = Field(default_factory=list)
    raw_text: Optional[str] = None
    text_chunk_size_chars: int = 6000
    text_chunk_overlap_chars: int = 300
    use_knowledge_graph: bool = True
    run_analysis_report: bool = True
    run_draft_review: bool = True
    output_prefix: Optional[str] = None
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = "balanced"
    custom_instructions: Optional[str] = None


class ReviewFTARequest(BaseModel):
    system: str = Field(..., min_length=1)
    top_event: str = Field(..., min_length=1)
    tree: Dict[str, Any]
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = "balanced"
    custom_instructions: Optional[str] = None


class KGQueryRequest(BaseModel):
    cypher: str = Field(..., min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=200, ge=1, le=1000)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    use_knowledge_graph: bool = True
    system: Optional[str] = None
    tree_context: Optional[str] = None


class BuildDotRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)


class FullGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    system: Optional[str] = "生产系统"
    top_event: Optional[str] = None
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = "strict"
    mode: Optional[Literal["hybrid", "llm", "deterministic"]] = "hybrid"
    text_chunk_size_chars: int = 6000
    text_chunk_overlap_chars: int = 300


class ExtractTextRequest(BaseModel):
    """Request for the review-first text extraction use case."""

    text: str = Field(..., min_length=1)
    text_chunk_size_chars: int = Field(default=6000, ge=1, le=100000)
    text_chunk_overlap_chars: int = Field(default=300, ge=0, le=99999)
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = "balanced"
    custom_instructions: Optional[str] = None


class ReviewDecisionRequest(BaseModel):
    """Human decision submitted for one persisted fault record."""

    record_id: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    reason: Optional[str] = None


class ReleaseExtractionRequest(BaseModel):
    """Request to project one persisted extraction into downstream-safe data."""

    result_id: str = Field(..., min_length=1)


class BuildReleasedExtractionRequest(BaseModel):
    """Request to build a tree from one persisted release projection."""

    release_id: str = Field(..., min_length=1)
    top_event: str = Field(..., min_length=1)


app = FastAPI(title="AI FTA API", version="1.0.0")

# Allow Vue dev server and configurable origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite provides process-restart persistence while keeping the repository
# contract independent from the database implementation.
app.state.extraction_workflow_repository = SQLiteExtractionWorkflowRepository(
    EXTRACTION_DB_PATH
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def _sanitize_prefix(prefix: Optional[str]) -> str:
    if prefix and prefix.strip():
        text = prefix.strip().replace(" ", "_")
        return "".join(ch for ch in text if ch.isalnum() or ch in {"_", "-"}) or "fta"
    return datetime.now().strftime("fta_%Y%m%d_%H%M%S")


def _failure_models_to_dict(items: List[FailureInput]) -> List[Dict[str, Any]]:
    payload = []
    for item in items:
        if hasattr(item, "model_dump"):
            payload.append(item.model_dump())
        else:
            payload.append(item.dict())
    return payload


def _fault_record_to_api_dict(record: FaultRecord) -> Dict[str, Any]:
    return {
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "component": record.component,
        "description": record.description,
        "causes": list(record.causes),
        "parameters": list(record.parameters),
        "confidence": record.confidence,
    }


def _evidence_span_to_api_dict(span: EvidenceSpan) -> Dict[str, Any]:
    return {
        "record_id": span.record_id,
        "field": span.field.value,
        "source_id": span.source_id,
        "quote": span.quote,
        "start": span.start,
        "end": span.end,
        "value_index": span.value_index,
    }


def _review_to_api_dict(review: FaultRecordReview) -> Dict[str, Any]:
    return {
        "review_id": review.review_id,
        "record_id": review.record_id,
        "status": review.status.value,
        "reason": review.reason,
        "reviewer": review.reviewer,
        "created_at": review.created_at.isoformat(),
    }


def _reviewable_extraction_to_api_dict(
    bundle: ReviewableExtractionResult,
) -> Dict[str, Any]:
    extraction = bundle.extraction
    return {
        "result_id": extraction.result_id,
        "status": extraction.status.value,
        "records": [_fault_record_to_api_dict(record) for record in extraction.records],
        "evidence_spans": [
            _evidence_span_to_api_dict(span)
            for span in extraction.evidence_spans
        ],
        "diagnostics": [
            {
                "code": diagnostic.code,
                "message": diagnostic.message,
                "stage": diagnostic.stage,
                "retryable": diagnostic.retryable,
            }
            for diagnostic in extraction.diagnostics
        ],
        "reviews": [_review_to_api_dict(review) for review in bundle.reviews],
    }


def _pending_review_item_to_api_dict(item: PendingReviewItem) -> Dict[str, Any]:
    return {
        "result_id": item.result_id,
        "extraction_status": item.extraction_status.value,
        "diagnostics": [
            {
                "code": diagnostic.code,
                "message": diagnostic.message,
                "stage": diagnostic.stage,
                "retryable": diagnostic.retryable,
            }
            for diagnostic in item.diagnostics
        ],
        "record": _fault_record_to_api_dict(item.record),
        "evidence_spans": [
            _evidence_span_to_api_dict(span) for span in item.evidence_spans
        ],
        "review": _review_to_api_dict(item.review),
    }


def _release_block_to_api_dict(block: ReleaseBlock) -> Dict[str, Any]:
    return {
        "record_id": block.record_id,
        "status": block.status.value if block.status is not None else None,
        "reason": block.reason,
    }


def _released_extraction_to_api_dict(
    released: ReleasedExtractionResult,
) -> Dict[str, Any]:
    return {
        "release_id": released.release_id,
        "source_result_id": released.source_result_id,
        "records": [
            _fault_record_to_api_dict(record) for record in released.records
        ],
        "review_decisions": [
            _review_to_api_dict(decision)
            for decision in released.review_decisions
        ],
        "blocked": [
            _release_block_to_api_dict(block) for block in released.blocked
        ],
    }


def _build_attempt_to_api_dict(attempt: FaultTreeBuildAttempt) -> Dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "release_id": attempt.release_id,
        "source_result_id": attempt.source_result_id,
        "top_event": attempt.top_event,
        "status": attempt.status.value,
        "reason": attempt.reason,
        "retryable": attempt.retryable,
        "tree": attempt.tree,
        "created_at": attempt.created_at.isoformat(),
    }


def _build_output_paths(prefix: str) -> Dict[str, Path]:
    return {
        "xml": OUTPUT_DIR / f"{prefix}.xml",
        "dot": OUTPUT_DIR / f"{prefix}.dot",
        "png": OUTPUT_DIR / f"{prefix}.png",
        "extracted_json": OUTPUT_DIR / f"{prefix}_extracted_faults.json",
        "analysis_json": OUTPUT_DIR / f"{prefix}_analysis.json",
        "analysis_txt": OUTPUT_DIR / f"{prefix}_analysis.txt",
        "review_json": OUTPUT_DIR / f"{prefix}_draft_review.json",
        "review_txt": OUTPUT_DIR / f"{prefix}_draft_review.txt",
    }


def _parse_bool_form(value: str, default: bool) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "y", "on"}


def _resolve_chat_records_file(output_dir: Path) -> Optional[Path]:
    for name in ["kb_corrected_v2.json", "kb_cleaned.json"]:
        preferred = output_dir / name
        if preferred.exists():
            return preferred
    return find_latest_records_file(output_dir)


def _merge_ranked_hits(doc_hits: List[Dict[str, Any]], graph_hits: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen_keys = set()

    for item in doc_hits + graph_hits:
        if not isinstance(item, dict):
            continue
        code = str(item.get("fault_code", "")).strip().upper()
        desc = str(item.get("description", "")).strip().lower()
        key = code or desc
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(item)
        if len(merged) >= top_k:
            break

    return merged


def _is_low_confidence_answer(text: str) -> bool:
    content = (text or "").strip()
    if not content:
        return True

    low_conf_markers = [
        "证据不足",
        "信息不足",
        "无法判断",
        "未提供",
        "未检索到",
    ]
    return any(marker in content for marker in low_conf_markers)


def _tree_context_to_doc(tree_context: Optional[str]) -> Optional[Dict[str, Any]]:
    text = (tree_context or "").strip()
    if not text:
        return None

    # Keep prompt context bounded to avoid oversized requests.
    max_len = 5000
    if len(text) > max_len:
        text = text[:max_len] + "\n...（已截断）"

    return {
        "fault_code": "",
        "component": "当前故障树",
        "description": "用户当前编辑/生成的故障树结构",
        "causes": [],
        "parameters": [],
        "text": f"来源：当前故障树\n{text}",
    }


def _merge_multi_source_text(chunks: List[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for idx, item in enumerate(chunks, start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("filename") or f"file_{idx}").strip()
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        blocks.append(f"[数据源{idx}: {name}]\n{text}")
    return "\n\n".join(blocks)


def _graph_hits_to_docs(question: str, events: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    import re as _re

    tokens = [t.lower() for t in _re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", question or "") if len(t) >= 2]
    if not tokens:
        return []

    ranked = []
    for item in events:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        causes = item.get("causes", []) if isinstance(item.get("causes"), list) else []
        cause_names = [str(c.get("name", "")).strip() for c in causes if isinstance(c, dict)]
        text = " ".join([name] + cause_names).lower()
        score = sum(1 for t in tokens if t in text)
        if score <= 0:
            continue

        ranked.append(
            {
                "score": score,
                "doc": {
                    "fault_code": "",
                    "component": "",
                    "description": name,
                    "causes": [c for c in cause_names if c],
                    "parameters": [],
                    "text": (
                        f"故障描述：{name}\n"
                        f"可能原因：{'、'.join([c for c in cause_names if c]) or '未提供'}\n"
                        "来源：Neo4j关系查询\n"
                    ),
                },
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return [item["doc"] for item in ranked[:top_k]]


def _structure_to_items(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(structure, dict):
        return []

    events = structure.get("intermediate_events", [])
    if not isinstance(events, list):
        return []

    items: List[Dict[str, Any]] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        causes_raw = ev.get("causes", []) if isinstance(ev.get("causes"), list) else []
        causes = [str(c.get("name", "")).strip() for c in causes_raw if isinstance(c, dict) and str(c.get("name", "")).strip()]
        items.append(
            {
                "name": str(ev.get("name", "")).strip(),
                "logic": str(ev.get("logic", "OR")).upper(),
                "probability": ev.get("probability"),
                "causes": causes,
            }
        )
    return items


def _render_analysis_text(report: Dict[str, Any]) -> str:
    lines = [
        "# FTA 分析报告",
        "",
        f"顶事件分析: {report.get('top_event_analysis', '')}",
        "",
        "## 关键路径",
    ]
    for item in report.get("key_paths", []):
        lines.append(
            f"- {item.get('path', '')} | 风险: {item.get('risk_level', '')} | 原因: {item.get('reason', '')}"
        )

    lines.append("")
    lines.append("## 薄弱环节")
    for item in report.get("weak_links", []):
        lines.append(
            f"- {item.get('component', '')} | 严重度: {item.get('severity', '')} | 原因: {item.get('reason', '')}"
        )

    lines.append("")
    lines.append("## 改进建议")
    for item in report.get("recommended_actions", []):
        lines.append(
            f"- {item.get('priority', '')}: {item.get('action', '')} | 预期效果: {item.get('expected_effect', '')}"
        )

    lines.append("")
    lines.append("## 验证计划")
    for item in report.get("verification_plan", []):
        lines.append(
            f"- 任务: {item.get('task', '')} | 方法: {item.get('method', '')} | 通过标准: {item.get('pass_criteria', '')}"
        )

    return "\n".join(lines)


def _render_review_text(review: Dict[str, Any]) -> str:
    lines = [
        "# FTA 初稿检验报告",
        "",
        f"总体评分: {review.get('overall_score', '')}",
        f"总结: {review.get('summary', '')}",
        "",
        "## 不足项",
    ]

    for item in review.get("deficiencies", []):
        lines.append(
            f"- [{item.get('id', '')}] {item.get('title', '')} | 严重度: {item.get('severity', '')} | 位置: {item.get('location', '')}"
        )
        lines.append(
            f"  问题: {item.get('issue', '')} | 影响: {item.get('impact', '')} | 建议: {item.get('suggestion', '')}"
        )

    lines.append("")
    lines.append("## 建议补充事件")
    for event in review.get("missing_events", []):
        lines.append(f"- {event}")

    lines.append("")
    lines.append("## 门逻辑调整建议")
    for item in review.get("gate_adjustments", []):
        lines.append(
            f"- 节点: {item.get('node', '')} | 当前: {item.get('current_gate', '')} -> 建议: {item.get('recommended_gate', '')} | 理由: {item.get('reason', '')}"
        )

    lines.append("")
    lines.append("## 概率问题说明")
    for item in review.get("probability_notes", []):
        lines.append(
            f"- 节点: {item.get('node', '')} | 问题: {item.get('problem', '')} | 建议: {item.get('suggestion', '')}"
        )

    lines.append("")
    lines.append("## 下一步工作")
    for item in review.get("next_steps", []):
        lines.append(
            f"- {item.get('priority', '')}: {item.get('task', '')} | 产出: {item.get('output', '')}"
        )

    return "\n".join(lines)


def _empty_fta_dot() -> str:
    return "\n".join(
        [
            "digraph FTA {",
            "  rankdir=TB;",
            "  graph [fontname=Helvetica];",
            "  node [fontname=Helvetica];",
            "  edge [fontname=Helvetica];",
            '  top [label="EMPTY_FTA", shape=doubleoctagon, style=filled, fillcolor=lightcoral];',
            "}",
        ]
    )


def validate_fta(dot: str) -> Dict[str, Any]:
    text = (dot or "").strip()
    if not text:
        return {"valid": False, "reason": "DOT为空"}
    if not text.startswith("digraph"):
        return {"valid": False, "reason": "DOT未以digraph开头"}
    if text.count("{") != text.count("}"):
        return {"valid": False, "reason": "花括号不匹配"}
    if "->" not in text and "top [" in text:
        return {"valid": True, "reason": "仅包含顶事件（空树）"}
    return {"valid": True, "reason": "ok"}


def _is_placeholder_dot(dot: str) -> bool:
    text = (dot or "").strip()
    if not text:
        return True
    return ('label="系统级故障"' in text) and ('label="未命名故障"' in text)


def _semantic_key(text: str) -> str:
    import re as _re

    s = (text or "").strip().lower()
    s = _re.sub(r"\s+", "", s)
    s = _re.sub(r"[，。；：、,.!?:;\-_/()（）\[\]{}\"'`]+", "", s)
    return s


def _repair_fta_payload(
    fta: Dict[str, Any],
    text: str,
    req: FullGenerateRequest,
    preserve_extracted_causes: bool = False,
) -> Dict[str, Any]:
    fixed = dict(fta or {})

    top = str(fixed.get("top") or "").strip()
    if not top or top == "系统级故障":
        if isinstance(req.top_event, str) and req.top_event.strip():
            top = req.top_event.strip()
        elif isinstance(req.system, str) and req.system.strip():
            top = f"{req.system.strip()}故障"
        else:
            top = "系统关键功能失效"

    fault = str(fixed.get("fault") or "").strip()
    if not fault or fault == "未命名故障":
        parsed = extract_fault_event(text)
        fault = parsed if parsed and parsed != "未命名故障" else "关键故障事件"

    causes = fixed.get("causes")
    if not isinstance(causes, list):
        causes = []
    causes = [c for c in causes if isinstance(c, str) and c.strip()]
    if preserve_extracted_causes:
        dedup_causes: List[str] = []
        seen_keys = set()
        for c in causes:
            cc = str(c or "").strip()
            if not cc:
                continue
            ck = _semantic_key(cc)
            if not ck or ck in seen_keys:
                continue
            seen_keys.add(ck)
            dedup_causes.append(cc)
        causes = dedup_causes
    else:
        causes = deduplicate_causes(causes)

    top_key = _semantic_key(top)
    fault_key = _semantic_key(fault)
    cleaned_causes: List[str] = []
    seen = set()
    for c in causes:
        ck = _semantic_key(c)
        if not ck:
            continue
        if top_key and (ck == top_key or ck in top_key or top_key in ck):
            continue
        if fault_key and (ck == fault_key or ck in fault_key or fault_key in ck):
            continue
        if ck in seen:
            continue
        seen.add(ck)
        cleaned_causes.append(c.strip())

    if len(cleaned_causes) == 0:
        cleaned_causes = generate_fallback_causes(fault)

    fixed["top"] = top
    fixed["fault"] = fault
    fixed["gate"] = str(fixed.get("gate") or "OR").upper()
    if fixed["gate"] not in {"OR", "AND"}:
        fixed["gate"] = "OR"
    fixed["causes"] = cleaned_causes
    return fixed


def extract_faults(
    text: str,
    system: Optional[str] = None,
    prompt_profile: Optional[str] = "strict",
    text_chunk_size_chars: int = 6000,
    text_chunk_overlap_chars: int = 300,
) -> List[Dict[str, Any]]:
    extracted = extract_fault_records_from_text(
        text,
        chunk_size_chars=text_chunk_size_chars,
        overlap_chars=text_chunk_overlap_chars,
        prompt_profile=prompt_profile,
        custom_instructions=(
            "仅保留可作为FTA因果事件的内容；将观测告警与管理元数据排除在causes之外。"
        ),
    )
    records = extracted.get("records", []) if isinstance(extracted, dict) else []
    if not isinstance(records, list):
        records = []

    # Attach system hint for top-event derivation in build_fta.
    if system:
        for item in records:
            if isinstance(item, dict) and not item.get("top_event"):
                item["top_event"] = f"{system}故障"

    return records


def _looks_like_dot(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    low = s.lower()
    return ("digraph" in low) and ("{" in s) and ("}" in s)


def _parse_dot_attrs(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for key, val in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\"(?:\\.|[^\"])*\"|[^,\]]+)", attr_text):
        value = val.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        attrs[key.strip().lower()] = value.strip()
    return attrs


def _normalize_fault_label(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return s

    # 兼容编号前缀："9） 顶事件：..."
    s = re.sub(r"^\s*\d+\s*[\)）.、]\s*", "", s)

    # 兼容历史标签："顶事件：... 故障树核心路径：..." / "顶事件：... 故障树分支"
    cleaned = re.sub(r"^\s*顶事件\s*[：:]\s*", "", s)
    cleaned = re.sub(r"\s*故障树核心路径\s*[：:].*$", "", cleaned).strip()
    cleaned = re.sub(r"\s*故障树分支\s*[：:]?.*$", "", cleaned).strip()
    return cleaned or s


def _normalize_top_label(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return s

    # 清理常见前缀，避免标题性文本污染顶事件。
    cleaned = re.sub(r"^\s*顶事件\s*[：:]\s*", "", s)

    # 若标签是因果链（A -> B -> C），优先取最后一段作为顶事件。
    parts = [p.strip() for p in re.split(r"\s*(?:->|→|⇒|➜|⟶|—>)\s*", cleaned) if p.strip()]
    if len(parts) >= 2:
        cleaned = parts[-1]

    return cleaned.strip() or s


def _extract_top_from_fault_label(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    s = re.sub(r"^\s*\d+\s*[\)）.、]\s*", "", s)

    m = re.search(r"顶事件\s*[：:]\s*(.+)", s)
    if not m:
        return ""

    candidate = m.group(1).strip()
    candidate = re.sub(r"\s*故障树分支\s*[：:]?.*$", "", candidate).strip()
    candidate = re.sub(r"\s*故障树核心路径\s*[：:]?.*$", "", candidate).strip()
    return candidate


def _split_causal_chain(text: str) -> List[str]:
    s = str(text or "").strip()
    if not s:
        return []

    normalized = re.sub(r"\s*(?:->|→|⇒|➜|⟶|—>)\s*", " -> ", s)
    parts = [p.strip() for p in re.split(r"\s*->\s*", normalized) if p.strip()]
    if len(parts) >= 2:
        return parts

    # 兼容复制过程丢箭头，退化用多空格切链。
    fallback = [p.strip() for p in re.split(r"\s{2,}", s) if p.strip()]
    return fallback if len(fallback) >= 2 else []


def _fta_from_dot_text(text: str, req: FullGenerateRequest) -> Optional[Dict[str, Any]]:
    if not _looks_like_dot(text):
        return None

    node_re = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[(.*?)\]\s*;\s*$")
    edge_re = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$")

    nodes: Dict[str, Dict[str, str]] = {}
    edges: List[tuple[str, str]] = []
    for line in text.splitlines():
        ln = line.strip()
        if not ln:
            continue
        nm = node_re.match(ln)
        if nm:
            nid = nm.group(1)
            attrs = _parse_dot_attrs(nm.group(2))
            nodes[nid] = attrs
            continue
        em = edge_re.match(ln)
        if em:
            edges.append((em.group(1), em.group(2)))

    if not nodes:
        return None

    def _label(nid: str) -> str:
        return str(nodes.get(nid, {}).get("label") or nid).strip()

    def _shape(nid: str) -> str:
        return str(nodes.get(nid, {}).get("shape") or "").strip().lower()

    top_id = "top" if "top" in nodes else ""
    if not top_id:
        for nid in nodes:
            if _shape(nid) == "doubleoctagon":
                top_id = nid
                break

    gate_id = "gate" if "gate" in nodes else ""
    if not gate_id:
        for nid in nodes:
            if _shape(nid) == "diamond":
                gate_id = nid
                break

    fault_id = "fault" if "fault" in nodes else ""
    if not fault_id:
        for nid in nodes:
            if _shape(nid) == "box" and nid != top_id:
                fault_id = nid
                break

    raw_top = _label(top_id) if top_id else ""
    top = _normalize_top_label(raw_top)
    if not top and isinstance(req.top_event, str) and req.top_event.strip():
        top = req.top_event.strip()
    if not top:
        top = f"{(req.system or '生产系统').strip()}故障"

    raw_fault = _label(fault_id) if fault_id else ""
    fault = _normalize_fault_label(raw_fault)

    top_from_fault = _extract_top_from_fault_label(raw_fault)
    if top in {"生产系统故障", "系统级故障", "设备故障"} and top_from_fault:
        top = top_from_fault
    if not fault:
        fault = extract_fault_event(text)

    gate = str(nodes.get(gate_id, {}).get("label") or "OR").upper() if gate_id else "OR"
    if gate not in {"OR", "AND"}:
        gate = "OR"

    causes: List[str] = []
    for nid in nodes:
        if nid in {top_id, gate_id, fault_id}:
            continue
        if _shape(nid) == "ellipse":
            causes.append(_label(nid))

    if not causes and gate_id:
        neighbors = set()
        for src, dst in edges:
            if src == gate_id and dst not in {top_id, fault_id}:
                neighbors.add(dst)
            if dst == gate_id and src not in {top_id, fault_id}:
                neighbors.add(src)
        causes.extend(_label(nid) for nid in neighbors if nid in nodes)

    inferred_fault = ""
    expanded_causes: List[str] = []
    for cause in causes:
        chain = _split_causal_chain(cause)
        if len(chain) >= 2:
            if not inferred_fault:
                inferred_fault = chain[-1]
            lead = " + ".join(chain[:-1])
            atoms = [p.strip() for p in re.split(r"\s*[+＋/、，,；;]\s*", lead) if p.strip()]
            if atoms:
                expanded_causes.extend(atoms)
            continue
        expanded_causes.append(cause)

    causes = expanded_causes

    # 若fault标签实际是顶事件说明，则优先用链尾作为故障事件。
    if top_from_fault and (not fault or fault == top_from_fault or fault == top):
        if inferred_fault:
            fault = inferred_fault

    if fault == top and inferred_fault:
        fault = inferred_fault

    return _repair_fta_payload(
        {
            "top": top,
            "fault": fault,
            "gate": gate,
            "causes": causes,
        },
        text,
        req,
    )


def _looks_like_structured_case_text(text: str) -> bool:
    s = str(text or "").strip()
    if not s:
        return False
    has_top = re.search(r"顶事件\s*[：:]", s) is not None
    has_logic_marker = re.search(r"(?:关键逻辑|故障树(?:分支|核心路径)|逻辑链路|路径)\s*[：:]?", s) is not None
    has_chain = re.search(r"(?:->|→|⇒|➜|⟶|—>)", s) is not None
    has_gate_tree = re.search(r"\b(?:AND|OR)\s*门\b", s, flags=re.IGNORECASE) is not None
    has_basic_event = re.search(r"基本事件\s*[：:]", s) is not None
    has_causal_sentence = re.search(r"(?:导致|引发|致使|造成)", s) is not None and re.search(r"[，,；;。]", s) is not None
    return (has_chain and (has_top or has_logic_marker)) or (has_top and has_gate_tree and has_basic_event) or has_causal_sentence


def _strip_dot_blocks(text: str) -> str:
    s = str(text or "")
    # 常见输入是“案例文本 + 一段digraph”，这里直接移除DOT块以免污染链路抽取。
    return re.sub(r"digraph\s+[A-Za-z_][A-Za-z0-9_]*\s*\{[\s\S]*\}\s*$", "", s, flags=re.IGNORECASE).strip()


def _clean_chain_segment(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    s = re.sub(r"^(?:关键逻辑|故障树(?:分支|核心路径)|逻辑链路|路径)\s*[：:]\s*", "", s)
    s = re.sub(r"^[\-•*\d\)）.、\s]+", "", s)
    return s.strip()


def _is_meta_line(line: str) -> bool:
    s = str(line or "").strip()
    if not s:
        return True
    return bool(re.match(r"^(?:教训|启示|经验|结论|建议|技术关键|备注)\s*[：:]", s))


def _collect_chain_segments(text: str) -> List[str]:
    lines = [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
    if not lines:
        return []

    out: List[str] = []
    collect_following = False

    for ln in lines:
        if _is_meta_line(ln):
            collect_following = False
            continue

        marker_match = re.match(r"^(?:关键逻辑|故障树(?:分支|核心路径)|逻辑链路|路径)\s*[：:]?\s*(.*)$", ln)
        if not marker_match:
            marker_match = re.match(r"^[^：:]{2,32}?树\s*[：:]\s*(.*)$", ln)
        if marker_match:
            tail = _clean_chain_segment(marker_match.group(1))
            if tail:
                out.append(tail)
                collect_following = False
            else:
                collect_following = True
            continue

        if re.search(r"(?:->|→|⇒|➜|⟶|—>)", ln):
            out.append(_clean_chain_segment(ln))
            collect_following = False
            continue

        if collect_following:
            out.append(_clean_chain_segment(ln))

    return [s for s in out if s]


def _extract_fault_hint_from_marker(lines: List[str]) -> str:
    for ln in lines:
        s = str(ln or "").strip()
        if not s:
            continue
        if re.match(r"^顶事件\s*[：:]", s):
            continue

        m = re.match(r"^([^：:]{2,32}?)(?:故障树(?:分支|核心路径)|逻辑链路|关键逻辑|路径|树)\s*[：:]\s*$", s)
        if not m:
            continue

        hint = m.group(1).strip()
        hint = re.sub(r"^(?:制造过程|流程管控)\s*", "", hint).strip() if len(hint) > 8 else hint
        if hint:
            return hint

    return ""


def _parse_gate_tree_style(lines: List[str], req: FullGenerateRequest) -> Optional[Dict[str, Any]]:
    if not lines:
        return None

    top = ""
    if isinstance(req.top_event, str) and req.top_event.strip():
        top = req.top_event.strip()
    if not top:
        for ln in lines:
            m = re.search(r"顶事件\s*[：:]\s*(.+)", ln)
            if m:
                top = m.group(1).strip()
                break
    if not top:
        return None

    gate = "OR"
    for ln in lines:
        gm = re.search(r"\b(AND|OR)\s*门\b", ln, flags=re.IGNORECASE)
        if gm:
            gate = gm.group(1).upper()
            break

    causes: List[str] = []
    for ln in lines:
        bm = re.search(r"基本事件\s*[：:]\s*(.+)", ln)
        if not bm:
            continue
        raw = bm.group(1).strip()
        raw = re.sub(r"^[├└│─\-\s]+", "", raw).strip()
        if not raw:
            continue
        causes.append(raw)

    if not causes:
        return None

    # 该输入通常是“顶事件+门+基本事件”直接表达，故障节点使用顶事件可避免错误中间层。
    return _repair_fta_payload(
        {
            "top": top,
            "fault": top,
            "gate": gate,
            "causes": causes,
        },
        "\n".join(lines),
        req,
        preserve_extracted_causes=True,
    )


def _split_cn_items(text: str) -> List[str]:
    parts = re.split(r"\s*(?:、|，|,|或|以及|和|及)\s*", str(text or ""))
    out: List[str] = []
    for p in parts:
        s = str(p or "").strip()
        s = re.sub(r"^(?:其一|其二|其三|其四|首先|其次|此外|另外|例如|比如)\s*[：:]?\s*", "", s)
        s = re.sub(r"[。；;]+$", "", s).strip()
        if s:
            out.append(s)
    return out


def _extract_middle_events(text: str) -> List[str]:
    s = str(text or "")
    mids: List[str] = []

    m = re.search(r"可能由(.+?)引起", s)
    if m:
        for item in _split_cn_items(m.group(1)):
            if re.search(r"(?:失效|异常|中断|故障|不足|失稳)$", item):
                mids.append(item)

    if not mids:
        preset = ["动力系统失效", "飞行控制系统失效", "通信链路中断", "能源系统异常"]
        mids = [p for p in preset if p in s]

    out: List[str] = []
    seen = set()
    for mname in mids:
        key = _semantic_key(mname)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(mname)
    return out


def _extract_basic_events_from_paragraph(paragraph: str) -> List[str]:
    p = str(paragraph or "").replace("\n", " ")
    if not p.strip():
        return []

    cands: List[str] = []

    for m in re.finditer(r"其[一二三四五六七八九十]\s*[，,]\s*([^；;。]+)", p):
        seg = m.group(1).strip()
        seg = re.sub(r"\s*(?:导致|造成|引起|使得|会导致|会造成|可能导致|可能造成).*$", "", seg)
        seg = re.sub(r"^(?:若|如果|当|在|并且|此外)\s*", "", seg).strip()
        if 2 <= len(seg) <= 24:
            cands.append(seg)

    has_cn_enum = re.search(r"其[一二三四五六七八九十]", p) is not None

    for seg in re.split(r"[；;。]\s*", p):
        s = str(seg or "").strip()
        if not s:
            continue
        if re.search(r"(?:包括|可能由|主要包括)", s) and not has_cn_enum:
            s = re.sub(r"^.*?(?:包括|可能由|主要包括)", "", s).strip()
            for atom in _split_cn_items(s):
                atom = re.sub(r"\s*(?:导致|造成|引起|使得|会导致|会造成|可能导致|可能造成).*$", "", atom).strip()
                if 2 <= len(atom) <= 24:
                    cands.append(atom)
            continue

        m_cond = re.match(r"^(?:如果|若|当|此外|例如)\s*(.+)$", s)
        if m_cond:
            cond = m_cond.group(1).strip()
            first_clause = cond.split("，", 1)[0].strip()
            atoms = re.split(r"\s*(?:或|和|及)\s*", first_clause)
            for atom in atoms:
                atom = atom.strip(" ，,：:")
                if 2 <= len(atom) <= 24 and re.search(r"(?:故障|失效|异常|中断|损坏|松动|过热|漂移|骤降|耗尽|触发|干扰|老化|不稳定)", atom):
                    cands.append(atom)

        cut = re.split(r"(?:导致|造成|引起|使得|会导致|会造成|可能导致|可能造成|则可能|也可能)", s, maxsplit=1)[0]
        cut = re.sub(r"^(?:若|如果|当|在|并且|此外)\s*", "", cut).strip(" ，,：:")
        if 2 <= len(cut) <= 28 and re.search(r"(?:故障|失效|异常|中断|损坏|松动|过热|漂移|骤降|耗尽|触发|干扰|老化|不稳定)", cut):
            cands.append(cut)

    out: List[str] = []
    seen = set()
    for c in cands:
        cc = str(c or "").strip()
        if not cc:
            continue
        cc = re.sub(r"^(?:例如|比如)\s*[，,:：]?\s*", "", cc).strip()
        if "，" in cc and len(cc) > 14:
            cc = cc.split("，", 1)[0].strip()
        cc = re.sub(r"^(?:若|如果|当|在)\s*", "", cc).strip(" ，,：:")
        if re.search(r"(?:其[一二三四五六七八九十]|几类原因|主要包括以下)", cc):
            continue
        if re.fullmatch(r".{0,10}时", cc):
            continue
        ck = _semantic_key(cc)
        if not ck or ck in seen:
            continue
        seen.add(ck)
        out.append(cc)

    # 包含关系去重：优先保留更短、更原子化的事件。
    final_out: List[str] = []
    keys = [_semantic_key(x) for x in out]
    for i, cc in enumerate(out):
        ki = keys[i]
        drop = False
        for j, kk in enumerate(keys):
            if i == j:
                continue
            if ki and kk and (ki in kk) and len(ki) < len(kk):
                drop = True
                break
        if not drop:
            final_out.append(cc)
    out = final_out
    return out


def _fta_from_sectioned_risk_text(text: str, req: FullGenerateRequest) -> Optional[Dict[str, Any]]:
    plain_text = _strip_dot_blocks(text)
    if not plain_text:
        return None

    # 针对“总述 + 分段中间事件 + 每段列举底层原因”的叙述体文本。
    if len(plain_text) < 120:
        return None

    mids = _extract_middle_events(plain_text)
    if len(mids) < 3:
        return None

    top = ""
    if isinstance(req.top_event, str) and req.top_event.strip():
        top = req.top_event.strip()
    if not top:
        m_top2 = re.search(r"([^，。；;\n]{2,24}事故)可能由", plain_text)
        if m_top2:
            top = m_top2.group(1).strip()
    if not top:
        m_top = re.search(r"将[“\"]?(.+?)[”\"]?作为顶事件", plain_text)
        if m_top:
            top = m_top.group(1).strip()
    if not top:
        top = f"{(req.system or '生产系统').strip()}故障"

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", plain_text) if p.strip()]
    if len(paragraphs) < 2:
        compact = re.sub(r"\s+", " ", plain_text).strip()
        def _best_mid_pos(src: str, mid_name: str) -> int:
            pos_list = [m.start() for m in re.finditer(re.escape(mid_name), src)]
            if not pos_list:
                return -1
            best = pos_list[0]
            best_score = -10
            for pos in pos_list:
                window = src[pos : pos + 48]
                score = 0
                if re.search(r"(?:主要包括|可能由|也是重要风险因素|主要包括以下)", window):
                    score += 5
                if re.search(r"(?:其一|其二|其三|例如|如果|若)", window):
                    score += 2
                # 优先选择后续的详细段落，而非首句总述枚举。
                score += int(pos / 200)
                if score >= best_score:
                    best_score = score
                    best = pos
            return best

        pos_pairs: List[tuple[int, str]] = []
        for mid in mids:
            idx = _best_mid_pos(compact, mid)
            if idx >= 0:
                pos_pairs.append((idx, mid))
        pos_pairs.sort(key=lambda x: x[0])
        if pos_pairs:
            rebuilt: List[str] = []
            for i, (start, _mid) in enumerate(pos_pairs):
                end = pos_pairs[i + 1][0] if i + 1 < len(pos_pairs) else len(compact)
                seg = compact[start:end].strip()
                if seg:
                    rebuilt.append(seg)
            if rebuilt:
                paragraphs = rebuilt

    intermediates: List[Dict[str, Any]] = []
    for mid in mids:
        para = ""
        for p in paragraphs:
            if re.match(rf"^\s*{re.escape(mid)}", p):
                para = p
                break
        if para:
            causes = _extract_basic_events_from_paragraph(para)
            if len(causes) >= 2:
                intermediates.append({
                    "name": mid,
                    "gate": "OR",
                    "causes": causes,
                })
            continue

        for p in paragraphs:
            if mid in p and re.search(r"(?:包括|可能由|主要包括)", p):
                para = p
                break
        if not para:
            for p in paragraphs:
                if mid in p:
                    para = p
                    break

        causes = _extract_basic_events_from_paragraph(para)
        if len(causes) < 2:
            continue

        intermediates.append({
            "name": mid,
            "gate": "OR",
            "causes": causes,
        })

    if len(intermediates) < 2:
        return None

    fta = _repair_fta_payload(
        {
            "top": top,
            "fault": top,
            "gate": "OR",
            "causes": [it.get("name", "") for it in intermediates],
        },
        plain_text,
        req,
        preserve_extracted_causes=True,
    )
    fta["intermediates"] = intermediates
    return fta


def _score_fault_candidate(candidate: str, top: str) -> int:
    s = str(candidate or "").strip()
    if not s:
        return -10

    score = 0
    if re.search(r"(?:失效|泄漏|故障|异常|断裂|破裂|失灵|偏差)", s):
        score += 4
    if re.search(r"(?:爆炸|坠毁|伤亡|停机|事故)", s):
        score -= 3

    top_key = _semantic_key(top)
    cand_key = _semantic_key(s)
    if top_key and cand_key and (cand_key in top_key or top_key in cand_key):
        score += 2

    if 2 <= len(s) <= 18:
        score += 1

    return score


def _normalize_cause_atom(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    s = s.strip("'\"“”‘’")
    s = re.sub(r"^(?:由于|因为|因|以及|并且|且|同时)\s*", "", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^[，。；：、,.!?:;()（）\[\]{}\-_/\s]+|[，。；：、,.!?:;()（）\[\]{}\-_/\s]+$", "", s)
    s = s.strip("'\"“”‘’")
    return s


def _fta_from_causal_sentence(text: str, req: FullGenerateRequest) -> Optional[Dict[str, Any]]:
    s = _strip_dot_blocks(text)
    if not s:
        return None
    # 长叙述文本不应走“单因果句”解析，避免退化成 c1..cN 句子列表。
    if len(s) > 260 or s.count("\n") >= 2:
        return None
    if len(re.findall(r"(?:导致|引发|致使|造成)", s)) > 2:
        return None
    if re.search(r"(?:顶事件\s*[：:]|\b(?:AND|OR)\s*门\b|基本事件\s*[：:])", s, flags=re.IGNORECASE):
        return None
    if re.search(r"(?:->|→|⇒|➜|⟶|—>)", s):
        return None
    if re.search(r"(?:导致|引发|致使|造成)", s) is None:
        return None

    parts = [p.strip() for p in re.split(r"[，,；;。]\s*", s) if p.strip()]
    if len(parts) < 2:
        return None

    top = req.top_event.strip() if isinstance(req.top_event, str) and req.top_event.strip() else ""
    causes: List[str] = []
    fault = ""

    first = parts[0].strip("'\"“”‘’")
    m = re.match(r"^(.*?)\s*(?:导致|引发|致使|造成)\s*(.+)$", first)
    intermediate = ""
    if m:
        left = _normalize_cause_atom(m.group(1))
        right = _normalize_cause_atom(m.group(2))
        if left:
            causes.append(left)
        if right:
            intermediate = right
    else:
        atom = _normalize_cause_atom(first)
        if atom:
            causes.append(atom)

    if len(parts) >= 2:
        for mid in parts[1:-1]:
            atom = _normalize_cause_atom(mid)
            if atom:
                causes.append(atom)

        tail = _normalize_cause_atom(parts[-1])
        if tail:
            fault = tail

    if not fault:
        fault = intermediate or extract_fault_event(s)
    if not fault:
        return None

    if intermediate and _semantic_key(intermediate) not in {_semantic_key(fault), _semantic_key(top)}:
        causes.append(intermediate)

    gate = "AND" if len(causes) >= 3 else "OR"
    if not top:
        top = fault

    return _repair_fta_payload(
        {
            "top": top,
            "fault": fault,
            "gate": gate,
            "causes": causes,
        },
        s,
        req,
        preserve_extracted_causes=True,
    )


def _is_noise_cause(text: str) -> bool:
    s = str(text or "").strip()
    if not s:
        return True
    if re.match(r"^(?:教训|启示|经验|结论|建议|技术关键)", s):
        return True
    if re.search(r"(?:忽视|耦合效应|组织管理|流程缺陷的耦合)", s) and len(s) > 14:
        return True
    if len(s) > 28 and not re.search(r"(?:故障|失效|异常|泄漏|脆化|缺陷|老化|失灵)", s):
        return True
    return False


def _fta_from_structured_case_text(text: str, req: FullGenerateRequest) -> Optional[Dict[str, Any]]:
    plain_text = _strip_dot_blocks(text)
    if not _looks_like_structured_case_text(plain_text):
        return None

    lines = [ln.strip() for ln in str(plain_text or "").splitlines() if ln.strip()]
    if not lines:
        return None

    gate_tree_fta = _parse_gate_tree_style(lines, req)
    if gate_tree_fta:
        return gate_tree_fta

    top = ""
    if isinstance(req.top_event, str) and req.top_event.strip():
        top = req.top_event.strip()
    if not top:
        for ln in lines:
            m = re.search(r"顶事件\s*[：:]\s*(.+)", ln)
            if m:
                top = m.group(1).strip()
                break
    if not top:
        top = f"{(req.system or '生产系统').strip()}故障"

    branch_candidates = _collect_chain_segments(plain_text)

    if not branch_candidates:
        return None

    fault_candidates: List[str] = []
    causes: List[str] = []
    fault_hint = _extract_fault_hint_from_marker(lines)

    for raw in branch_candidates:
        normalized = _clean_chain_segment(raw)
        chain = _split_causal_chain(normalized)

        if len(chain) >= 2:
            if len(chain) == 2 and re.search(r"[+＋/、，,；;]", chain[-1]):
                # 二段链 A -> (B + C)：B/C 应拆成低事件，fault 优先使用标题提示（如“制造过程失控树”）。
                if fault_hint:
                    fault_candidates.append(fault_hint)
                else:
                    fault_candidates.append(chain[0])

                left_atom = _normalize_cause_atom(chain[0])
                if left_atom and not _is_noise_cause(left_atom):
                    causes.append(left_atom)

                rhs_atoms = [
                    _normalize_cause_atom(p)
                    for p in re.split(r"\s*[+＋/、，,；;]\s*", chain[-1])
                    if p.strip()
                ]
                for atom in rhs_atoms:
                    if atom and not _is_noise_cause(atom):
                        causes.append(atom)
                continue

            # 经验规则：
            # - 3段链(A -> B -> C)里 C 往往是故障结果，B常为中间原因簇；
            # - 4段及以上链里倒数第二段更接近故障事件。
            local_fault = chain[-2] if len(chain) >= 4 else chain[-1]
            fault_candidates.append(local_fault)

            lead_parts = chain[:-2] if len(chain) >= 4 else chain[:-1]
            lead = " + ".join(lead_parts)
            atoms = [_normalize_cause_atom(p) for p in re.split(r"\s*[+＋/、，,；;]\s*", lead) if p.strip()]
            for atom in atoms:
                if atom and not _is_noise_cause(atom):
                    causes.append(atom)
        else:
            parts = [_normalize_cause_atom(p) for p in re.split(r"\s*[+＋/、，,；;]\s*", normalized) if p.strip()]
            for part in parts:
                if part and not _is_noise_cause(part):
                    causes.append(part)

    fault = ""
    if fault_candidates:
        scored = sorted(
            ((cand, _score_fault_candidate(cand, top)) for cand in fault_candidates),
            key=lambda x: x[1],
            reverse=True,
        )
        fault = str(scored[0][0]).strip()

    if not fault:
        fault = extract_fault_event(plain_text)
    if fault_hint and (not fault or fault == "关键故障事件"):
        fault = fault_hint
    if not fault or fault == "未命名故障":
        fault = "关键故障事件"

    deduped: List[str] = []
    seen_keys = set()
    for c in causes:
        cc = str(c or "").strip()
        if not cc:
            continue
        ck = _semantic_key(cc)
        if not ck or ck in seen_keys:
            continue
        seen_keys.add(ck)
        deduped.append(cc)
    causes = deduped
    if not causes:
        causes = generate_fallback_causes(fault)

    return _repair_fta_payload(
        {
            "top": top,
            "fault": fault,
            "gate": "OR",
            "causes": causes,
        },
        plain_text,
        req,
        preserve_extracted_causes=True,
    )


def _looks_like_generic_cause(cause: str) -> bool:
    s = str(cause or "").strip()
    if not s:
        return True
    generic_terms = {
        "传感器故障",
        "信号线路异常",
        "控制模块故障",
        "系统故障",
        "模块故障",
    }
    if s in generic_terms:
        return True
    if re.fullmatch(r"c\d+", s.lower()):
        return True
    return False


def _count_meaningful_causes(fta: Optional[Dict[str, Any]]) -> int:
    if not isinstance(fta, dict):
        return 0
    causes = fta.get("causes") if isinstance(fta.get("causes"), list) else []
    count = 0
    for c in causes:
        s = str(c or "").strip()
        if not s:
            continue
        if _looks_like_generic_cause(s):
            continue
        count += 1
    return count


def _prefer_structured_over_dot(dot_fta: Optional[Dict[str, Any]], structured_fta: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(structured_fta, dict):
        return False
    if not isinstance(dot_fta, dict):
        return True

    dot_meaningful = _count_meaningful_causes(dot_fta)
    structured_meaningful = _count_meaningful_causes(structured_fta)

    # 规则：DOT若明显是模板化低事件，而结构化文本可抽到更具体原因，则优先结构化结果。
    if structured_meaningful >= max(2, dot_meaningful + 1):
        return True

    # 规则：DOT fault 仍为泛化词时，也优先结构化结果。
    dot_fault = str(dot_fta.get("fault") or "").strip()
    if dot_fault in {"关键故障事件", "未命名故障", "系统故障", "姿态控制异常"} and structured_meaningful > 0:
        return True

    return False


def _is_mixed_dot_and_case_text(text: str) -> bool:
    s = str(text or "")
    if not _looks_like_dot(s):
        return False
    has_case_marker = re.search(r"(?:顶事件|关键逻辑|故障树(?:分支|核心路径))\s*[：:]", s) is not None
    has_chain = re.search(r"(?:->|→|⇒|➜|⟶|—>)", s) is not None
    return has_case_marker and has_chain


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "build": "2026-04-15-template-parser-v12"}


@app.post("/api/fta/extract")
def extract_text_for_review(req: ExtractTextRequest) -> Dict[str, Any]:
    """Extract text into persisted reviewable records without building a tree."""
    try:
        if req.text_chunk_overlap_chars >= req.text_chunk_size_chars:
            raise ValueError(
                "text_chunk_overlap_chars must be smaller than text_chunk_size_chars"
            )

        extractor = build_text_extraction_adapter(
            chunk_size_chars=req.text_chunk_size_chars,
            overlap_chars=req.text_chunk_overlap_chars,
            prompt_profile=req.prompt_profile,
            custom_instructions=req.custom_instructions,
        )
        service = ExtractionApplicationService(
            extractor,
            app.state.extraction_workflow_repository,
        )
        bundle = service.extract(req.text)
        return _reviewable_extraction_to_api_dict(bundle)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="extraction workflow failed") from exc


@app.get("/api/fta/reviews/pending")
def list_pending_review_tasks() -> Dict[str, Any]:
    """List individual fault records that currently need human review."""
    try:
        pending_items = (
            app.state.extraction_workflow_repository.list_pending_review_items()
        )
        items = [_pending_review_item_to_api_dict(item) for item in pending_items]
        return {"items": items, "count": len(items)}
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="pending review query failed") from exc


def _apply_review_decision(
    req: ReviewDecisionRequest,
    action: str,
) -> Dict[str, Any]:
    service = ReviewDecisionService(app.state.extraction_workflow_repository)
    try:
        decision_method = getattr(service, action)
        decision = decision_method(
            record_id=req.record_id,
            reviewer=req.reviewer,
            reason=req.reason,
        )
        return _review_to_api_dict(decision)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="review decision failed") from exc


@app.post("/api/fta/reviews/approve")
def approve_fault_record(req: ReviewDecisionRequest) -> Dict[str, Any]:
    """Record a human approval without changing the extracted fact."""
    return _apply_review_decision(req, "approve")


@app.post("/api/fta/reviews/reject")
def reject_fault_record(req: ReviewDecisionRequest) -> Dict[str, Any]:
    """Record a human rejection with a required reason."""
    return _apply_review_decision(req, "reject")


@app.post("/api/fta/reviews/revision")
def request_fault_record_revision(req: ReviewDecisionRequest) -> Dict[str, Any]:
    """Record that a human reviewer requests more work on the record."""
    return _apply_review_decision(req, "request_revision")


@app.post("/api/fta/release")
def release_extraction(req: ReleaseExtractionRequest) -> Dict[str, Any]:
    """Release only records whose persisted current review is approved."""
    repository = app.state.extraction_workflow_repository
    try:
        extraction = repository.get(req.result_id)
        if extraction is None:
            raise HTTPException(status_code=404, detail="extraction result not found")

        current_reviews = []
        missing_record_ids = []
        for record in extraction.records:
            review = repository.get_current(record.record_id)
            if review is None:
                missing_record_ids.append(record.record_id)
            else:
                current_reviews.append(review)

        if missing_record_ids:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "extraction has records without persisted review state",
                    "record_ids": missing_record_ids,
                },
            )

        reviewable = ReviewableExtractionResult(
            extraction=extraction,
            reviews=tuple(current_reviews),
        )
        allowed_statuses = [ReviewStatus.APPROVED]
        if ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE:
            allowed_statuses.append(ReviewStatus.NOT_REQUIRED)
        released = FaultRecordReleaseService(
            repository,
            allowed_statuses=allowed_statuses,
        ).release(reviewable)
        repository.save_release(released)
        return _released_extraction_to_api_dict(released)
    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="extraction release failed") from exc


@app.post("/api/fta/build_released")
def build_released_extraction(
    req: BuildReleasedExtractionRequest,
) -> Dict[str, Any]:
    """Build one persisted release and append exactly one attempt record."""
    repository = app.state.extraction_workflow_repository
    try:
        release = repository.get_release(req.release_id)
        if release is None:
            raise HTTPException(status_code=404, detail="release not found")

        attempt = FaultTreeBuildService(repository).build(
            release,
            req.top_event,
        )
        return _build_attempt_to_api_dict(attempt)
    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="fault tree build failed") from exc


@app.get("/api/fta/build_attempts/{release_id}")
def list_build_attempts(release_id: str) -> Dict[str, Any]:
    """Return the append-only build history for one release."""
    repository = app.state.extraction_workflow_repository
    try:
        if repository.get_release(release_id) is None:
            raise HTTPException(status_code=404, detail="release not found")
        attempts = repository.list_build_attempts(release_id)
        items = [_build_attempt_to_api_dict(attempt) for attempt in attempts]
        return {"items": items, "count": len(items)}
    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="build attempt query failed") from exc


@app.post("/api/fta/build_dot")
def build_dot(req: BuildDotRequest) -> Dict[str, Any]:
    try:
        items = req.items or []
        log(f"[build_dot] input items: {items}")

        if not items:
            dot = _empty_fta_dot()
            valid = validate_fta(dot)
            return {
                "dot": dot,
                "message": "items为空，返回空树",
                "debug": {"item_count": 0},
                "validation": valid,
            }

        fta = build_fta(items)
        if isinstance(fta, dict):
            gate = str(fta.get("gate") or "OR").upper()
            fta["gate"] = gate if gate in {"AND", "OR"} else "OR"
        dot = build_dot_from_fta(fta)
        log(f"[build_dot] output dot:\n{dot}")
        valid = validate_fta(dot)
        return {
            "dot": dot,
            "debug": {
                "item_count": len(items),
                "sample": items[:2],
                "fta": fta,
            },
            "validation": valid,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"build_dot失败: {exc}") from exc


@app.post("/api/fta/full_generate")
def full_generate(req: FullGenerateRequest) -> Dict[str, Any]:
    try:
        text = (req.text or "").strip()
        if not text:
            raise ValueError("text不能为空")

        dot_fta = _fta_from_dot_text(text, req)
        sectioned_fta = _fta_from_sectioned_risk_text(text, req)
        structured_fta = _fta_from_structured_case_text(text, req)
        causal_fta = _fta_from_causal_sentence(text, req)
        preferred_fta = sectioned_fta or structured_fta or causal_fta

        if preferred_fta and _is_mixed_dot_and_case_text(text):
            dot = build_dot_from_fta(preferred_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "mixed-text-force-structured",
                    "fta": preferred_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        if dot_fta and _prefer_structured_over_dot(dot_fta, preferred_fta):
            dot = build_dot_from_fta(preferred_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "mixed-text-prefer-structured",
                    "fta": preferred_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        if dot_fta:
            dot = build_dot_from_fta(dot_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "dot-parser",
                    "fta": dot_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        if sectioned_fta:
            dot = build_dot_from_fta(sectioned_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "text-sectioned-parser",
                    "fta": sectioned_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        if structured_fta:
            dot = build_dot_from_fta(structured_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "text-template-parser",
                    "fta": structured_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        if causal_fta:
            dot = build_dot_from_fta(causal_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "debug": {
                    "mode": "causal-sentence-parser",
                    "fta": causal_fta,
                    "item_count": 0,
                },
                "validation": valid,
            }

        mode = req.mode or "hybrid"

        if mode in {"hybrid", "llm"}:
            try:
                force_llm = mode == "llm"
                structure = extract_fta_structure(text, force_llm=force_llm)
                if req.top_event and req.top_event.strip():
                    structure["top_event"] = req.top_event.strip()
                elif req.system and req.system.strip() and not structure.get("top_event"):
                    structure["top_event"] = f"{req.system.strip()}故障"
                dot = generate_dot(structure, allow_fallback=(mode != "llm"))
                valid = validate_fta(dot)
                if mode == "llm" and _is_placeholder_dot(dot):
                    raise ValueError("LLM返回占位故障树，请检查模型输出质量")

                if valid.get("valid") and not _is_placeholder_dot(dot):
                    llm_items = _structure_to_items(structure)
                    return {
                        "items": llm_items,
                        "dot": dot,
                        "debug": {
                            "mode": "llm_strict" if mode == "llm" else "llm",
                            "structure": structure,
                            "item_count": len(llm_items),
                        },
                        "validation": valid,
                    }
            except Exception as llm_exc:
                log(f"[full_generate] llm pipeline failed, fallback to deterministic: {llm_exc}")
                if mode == "llm":
                    raise

        items = extract_faults(
            text=text,
            system=req.system,
            prompt_profile=req.prompt_profile,
            text_chunk_size_chars=req.text_chunk_size_chars,
            text_chunk_overlap_chars=req.text_chunk_overlap_chars,
        )

        context_item = {
            "text": text,
            "description": text,
        }
        if req.top_event and req.top_event.strip():
            context_item["top_event"] = req.top_event.strip()
        elif req.system and req.system.strip():
            context_item["top_event"] = f"{req.system.strip()}故障"
        items.append(context_item)

        if req.top_event and req.top_event.strip():
            for item in items:
                if isinstance(item, dict):
                    item["top_event"] = req.top_event.strip()

        log(f"[full_generate] extracted items: {items}")

        if not items:
            fallback_fault = extract_fault_event(text)
            if fallback_fault == "未命名故障":
                fallback_fault = "姿态控制异常"
            fallback_top = (
                req.top_event.strip()
                if isinstance(req.top_event, str) and req.top_event.strip()
                else f"{(req.system or '生产系统').strip()}故障"
            )
            fallback_fta = {
                "top": fallback_top,
                "fault": fallback_fault,
                "gate": "OR",
                "causes": generate_fallback_causes(fallback_fault),
            }
            dot = build_dot_from_fta(fallback_fta)
            valid = validate_fta(dot)
            return {
                "items": [],
                "dot": dot,
                "message": "未抽取到有效故障记录，已使用Fallback生成故障树",
                "debug": {"item_count": 0, "mode": "deterministic-fallback", "fta": fallback_fta},
                "validation": valid,
            }

        fta = build_fta(items)

        if not isinstance(fta, dict):
            fta = {}

        top_val = str(fta.get("top") or "").strip()
        if not top_val or top_val == "系统级故障":
            if req.top_event and req.top_event.strip():
                fta["top"] = req.top_event.strip()
            elif req.system and req.system.strip():
                fta["top"] = f"{req.system.strip()}故障"

        fault_val = str(fta.get("fault") or "").strip()
        if not fault_val or fault_val == "未命名故障":
            parsed_fault = extract_fault_event(text)
            if parsed_fault == "未命名故障":
                parsed_fault = "姿态控制异常"
            fta["fault"] = parsed_fault

        causes_val = fta.get("causes") if isinstance(fta.get("causes"), list) else []
        if len(causes_val) == 0:
            fta["causes"] = generate_fallback_causes(str(fta.get("fault") or ""))

        dot = build_dot_from_fta(fta)
        log(f"[full_generate] output dot:\n{dot}")
        valid = validate_fta(dot)
        return {
            "items": items,
            "dot": dot,
            "debug": {
                "item_count": len(items),
                "prompt_profile": req.prompt_profile,
                "fta": fta,
                "mode": "deterministic",
            },
            "validation": valid,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"full_generate失败: {exc}") from exc


@app.post("/api/fta/generate")
def generate_fta(req: GenerateFTARequest) -> Dict[str, Any]:
    try:
        extracted_faults = None

        if req.source == "manual":
            failures = _failure_models_to_dict(req.manual_failures)
            if not failures:
                raise ValueError("manual_failures不能为空")
        elif req.source == "text":
            if not req.raw_text or not req.raw_text.strip():
                raise ValueError("source=text时，raw_text不能为空")

            extracted_faults = extract_fault_records_from_text(
                req.raw_text,
                chunk_size_chars=req.text_chunk_size_chars,
                overlap_chars=req.text_chunk_overlap_chars,
                prompt_profile=req.prompt_profile,
                custom_instructions=req.custom_instructions,
            )
            failures = convert_fault_records_to_failures(extracted_faults.get("records", []))
        else:
            failures = generate_failure_events(
                req.system,
                prompt_profile=req.prompt_profile,
                custom_instructions=req.custom_instructions,
            )

        kg_enabled = False
        kg_error: Optional[str] = None
        if req.use_knowledge_graph:
            try:
                create_failure_nodes(req.system, failures)
                events = get_failure_paths(req.system)
                kg_enabled = True
            except Exception as exc:
                kg_error = str(exc)
                events = failures
                log(f"[generate_fta] knowledge graph unavailable, fallback to local events: {exc}")
        else:
            events = failures

        tree = build_fault_tree(req.top_event, events)

        prefix = _sanitize_prefix(req.output_prefix)
        paths = _build_output_paths(prefix)

        if extracted_faults:
            save_json(extracted_faults, str(paths["extracted_json"]))

        export_xml(tree, str(paths["xml"]))
        visuals = export_visuals(tree, str(paths["dot"]), str(paths["png"]))
        dot_content = paths["dot"].read_text(encoding="utf-8") if paths["dot"].exists() else None

        analysis_report = None
        review_report = None

        if req.run_analysis_report:
            analysis_report = analyze_fault_tree_report(
                req.system,
                req.top_event,
                tree,
                prompt_profile=req.prompt_profile,
                custom_instructions=req.custom_instructions,
            )
            save_json(analysis_report, str(paths["analysis_json"]))
            save_text(_render_analysis_text(analysis_report), str(paths["analysis_txt"]))

        if req.run_draft_review:
            review_report = review_fault_tree_draft(
                req.system,
                req.top_event,
                tree,
                prompt_profile=req.prompt_profile,
                custom_instructions=req.custom_instructions,
            )
            save_json(review_report, str(paths["review_json"]))
            save_text(_render_review_text(review_report), str(paths["review_txt"]))

        return {
            "success": True,
            "system": req.system,
            "top_event": req.top_event,
            "source": req.source,
            "prompt_profile": req.prompt_profile,
            "knowledge_graph": {
                "requested": req.use_knowledge_graph,
                "enabled": kg_enabled,
                "fallback_used": bool(kg_error),
                "message": kg_error,
            },
            "tree": tree,
            "events": events,
            "dot_content": dot_content,
            "extracted_faults": extracted_faults,
            "analysis_report": analysis_report,
            "draft_review": review_report,
            "files": {
                "xml": str(paths["xml"]),
                "dot": str(paths["dot"]),
                "png": visuals.get("png"),
                "extracted_json": str(paths["extracted_json"]) if extracted_faults else None,
                "analysis_json": str(paths["analysis_json"]) if analysis_report else None,
                "analysis_txt": str(paths["analysis_txt"]) if analysis_report else None,
                "review_json": str(paths["review_json"]) if review_report else None,
                "review_txt": str(paths["review_txt"]) if review_report else None,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/fta/review")
def review_fta(req: ReviewFTARequest) -> Dict[str, Any]:
    try:
        analysis_report = analyze_fault_tree_report(
            req.system,
            req.top_event,
            req.tree,
            prompt_profile=req.prompt_profile,
            custom_instructions=req.custom_instructions,
        )
        review_report = review_fault_tree_draft(
            req.system,
            req.top_event,
            req.tree,
            prompt_profile=req.prompt_profile,
            custom_instructions=req.custom_instructions,
        )
        return {
            "success": True,
            "analysis_report": analysis_report,
            "draft_review": review_report,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/kg/query")
def query_kg(req: KGQueryRequest) -> Dict[str, Any]:
    try:
        result = query_knowledge_graph(req.cypher, req.params, req.limit)
        return {
            "success": True,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    try:
        question = req.question.strip()

        records_file = _resolve_chat_records_file(OUTPUT_DIR)
        kb_records: List[Dict[str, Any]] = []
        if records_file:
            kb_records = load_records_from_file(records_file)

        docs = build_docs(kb_records)
        hits = simple_search(question, docs, top_k=req.top_k)

        graph_hits: List[Dict[str, Any]] = []
        if req.use_knowledge_graph and req.system and req.system.strip():
            try:
                events = get_failure_paths(req.system.strip())
                graph_hits = _graph_hits_to_docs(question, events, req.top_k)
            except Exception as exc:
                log(f"[chat] graph query failed: {exc}")

        context_hits: List[Dict[str, Any]] = []
        tree_doc = _tree_context_to_doc(req.tree_context)
        if tree_doc:
            context_hits = [tree_doc]

        final_hits = _merge_ranked_hits(context_hits + hits, graph_hits, req.top_k)
        template_answer = compose_answer(question, final_hits)

        answer = template_answer
        answer_source = "template"

        kb_answer = ""
        if final_hits:
            try:
                kb_answer = answer_question_with_context(question, final_hits, req.system)
                answer = kb_answer
                answer_source = "llm_kb"
            except Exception as exc:
                log(f"[chat] llm_kb failed: {exc}")

        need_general = (not final_hits) or _is_low_confidence_answer(kb_answer)
        if need_general:
            try:
                general_answer = answer_general_question(question, req.system)
                if answer_source == "llm_kb" and kb_answer:
                    answer = kb_answer + "\n\n【补充说明】\n" + general_answer
                    answer_source = "llm_kb_plus_general"
                else:
                    answer = general_answer
                    answer_source = "llm_general"
            except Exception as exc:
                log(f"[chat] llm_general failed, fallback to template: {exc}")

        return {
            "success": True,
            "answer": answer,
            "hits": final_hits,
            "meta": {
                "question": question,
                "kb_records": len(kb_records),
                "doc_hits": len(hits),
                "graph_hits": len(graph_hits),
                "tree_context_used": bool(tree_doc),
                "answer_source": answer_source,
                "records_file": str(records_file) if records_file else None,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/fta/generate_agent")
def generate_fta_agent(req: GenerateFTARequest) -> Dict[str, Any]:
    try:
        workflow_result = run_agent_workflow(
            system=req.system,
            top_event=req.top_event,
            source=req.source,
            manual_failures=_failure_models_to_dict(req.manual_failures),
            raw_text=req.raw_text,
            text_chunk_size_chars=req.text_chunk_size_chars,
            text_chunk_overlap_chars=req.text_chunk_overlap_chars,
            use_knowledge_graph=req.use_knowledge_graph,
            run_analysis_report=req.run_analysis_report,
            run_draft_review=req.run_draft_review,
            prompt_profile=req.prompt_profile,
            custom_instructions=req.custom_instructions,
        )

        prefix = _sanitize_prefix(req.output_prefix)
        paths = _build_output_paths(prefix)

        tree = workflow_result["tree"]
        export_xml(tree, str(paths["xml"]))
        visuals = export_visuals(tree, str(paths["dot"]), str(paths["png"]))
        dot_content = paths["dot"].read_text(encoding="utf-8") if paths["dot"].exists() else None

        if workflow_result.get("extracted_faults"):
            save_json(workflow_result["extracted_faults"], str(paths["extracted_json"]))

        if workflow_result.get("analysis_report"):
            save_json(workflow_result["analysis_report"], str(paths["analysis_json"]))
            save_text(_render_analysis_text(workflow_result["analysis_report"]), str(paths["analysis_txt"]))

        if workflow_result.get("draft_review"):
            save_json(workflow_result["draft_review"], str(paths["review_json"]))
            save_text(_render_review_text(workflow_result["draft_review"]), str(paths["review_txt"]))

        return {
            "success": True,
            "system": req.system,
            "top_event": req.top_event,
            "source": req.source,
            "prompt_profile": req.prompt_profile,
            "stages": workflow_result.get("stages", []),
            "tree": tree,
            "events": workflow_result.get("events", []),
            "dot_content": dot_content,
            "extracted_faults": workflow_result.get("extracted_faults"),
            "analysis_report": workflow_result.get("analysis_report"),
            "draft_review": workflow_result.get("draft_review"),
            "files": {
                "xml": str(paths["xml"]),
                "dot": str(paths["dot"]),
                "png": visuals.get("png"),
                "extracted_json": str(paths["extracted_json"]) if workflow_result.get("extracted_faults") else None,
                "analysis_json": str(paths["analysis_json"]) if workflow_result.get("analysis_report") else None,
                "analysis_txt": str(paths["analysis_txt"]) if workflow_result.get("analysis_report") else None,
                "review_json": str(paths["review_json"]) if workflow_result.get("draft_review") else None,
                "review_txt": str(paths["review_txt"]) if workflow_result.get("draft_review") else None,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/fta/generate_from_file")
async def generate_fta_from_file(
    file: UploadFile = File(...),
    system: str = Form(...),
    top_event: str = Form(...),
    text_chunk_size_chars: int = Form(6000),
    text_chunk_overlap_chars: int = Form(300),
    use_knowledge_graph: str = Form("true"),
    run_analysis_report: str = Form("true"),
    run_draft_review: str = Form("true"),
    output_prefix: Optional[str] = Form(None),
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = Form("balanced"),
    custom_instructions: Optional[str] = Form(None),
) -> Dict[str, Any]:
    try:
        raw = await file.read()
        manual_text = extract_text_from_uploaded_file(file.filename or "", raw)

        req = GenerateFTARequest(
            system=system,
            top_event=top_event,
            source="text",
            raw_text=manual_text,
            text_chunk_size_chars=text_chunk_size_chars,
            text_chunk_overlap_chars=text_chunk_overlap_chars,
            use_knowledge_graph=_parse_bool_form(use_knowledge_graph, True),
            run_analysis_report=_parse_bool_form(run_analysis_report, True),
            run_draft_review=_parse_bool_form(run_draft_review, True),
            output_prefix=output_prefix,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )

        result = generate_fta(req)
        result["upload"] = {
            "filename": file.filename,
            "size_bytes": len(raw),
            "source": "uploaded_file",
        }
        return result
    except FileTextExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/fta/generate_from_files")
async def generate_fta_from_files(
    files: List[UploadFile] = File(...),
    system: str = Form(...),
    top_event: str = Form(...),
    text_chunk_size_chars: int = Form(6000),
    text_chunk_overlap_chars: int = Form(300),
    use_knowledge_graph: str = Form("true"),
    run_analysis_report: str = Form("true"),
    run_draft_review: str = Form("true"),
    output_prefix: Optional[str] = Form(None),
    prompt_profile: Optional[Literal["balanced", "strict", "exploratory"]] = Form("balanced"),
    custom_instructions: Optional[str] = Form(None),
) -> Dict[str, Any]:
    try:
        if not files:
            raise HTTPException(status_code=400, detail="files不能为空")

        source_chunks: List[Dict[str, Any]] = []
        upload_meta: List[Dict[str, Any]] = []
        for file in files:
            raw = await file.read()
            text = extract_text_from_uploaded_file(file.filename or "", raw)
            source_chunks.append({"filename": file.filename or "", "text": text})
            upload_meta.append(
                {
                    "filename": file.filename,
                    "size_bytes": len(raw),
                    "text_chars": len(text),
                }
            )

        merged_text = _merge_multi_source_text(source_chunks)
        if not merged_text.strip():
            raise HTTPException(status_code=400, detail="上传文件中未提取到有效文本")

        req = GenerateFTARequest(
            system=system,
            top_event=top_event,
            source="text",
            raw_text=merged_text,
            text_chunk_size_chars=text_chunk_size_chars,
            text_chunk_overlap_chars=text_chunk_overlap_chars,
            use_knowledge_graph=_parse_bool_form(use_knowledge_graph, True),
            run_analysis_report=_parse_bool_form(run_analysis_report, True),
            run_draft_review=_parse_bool_form(run_draft_review, True),
            output_prefix=output_prefix,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )

        result = generate_fta(req)
        result["upload"] = {
            "source": "uploaded_files",
            "files_count": len(upload_meta),
            "files": upload_meta,
            "merged_text_chars": len(merged_text),
        }
        return result
    except FileTextExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
