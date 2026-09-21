"""Evidence-bound RAG application service for Siemens S210 fault entities.

The service owns orchestration only:

    query -> retriever -> fault context loader -> evidence-bound generator

Retrieval and model-provider implementations are injected through ports from
``rag_contract.py``.  The API layer is intentionally not an owner of this
workflow; it will be added in the later API integration phase.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Sequence

from model_client import ModelClient
from rag_contract import (
    AnswerGenerator,
    EvidenceCitation,
    FaultContext,
    FaultContextLoader,
    FaultRelation,
    FaultRetriever,
    GeneratedAnswer,
    RagResponse,
    RetrievedFault,
)
from fault_relation_expansion import FaultRelationRegistry
from response_policy import RagBoundaryDecision, ResponsePolicyLayer, boundary_message


class RagServiceError(ValueError):
    """A safe, structured application error for the RAG pipeline."""

    def __init__(self, code: str, message: str) -> None:
        if not code.strip() or not message.strip():
            raise ValueError("RAG error code and message must be non-empty")
        super().__init__(message)
        self.code = code
        self.message = message


_SECTION_RE = re.compile(
    r"(?im)^(?P<header>Reaction|Acknowledge|Cause|Alarm value|Fault value|Remedy|Note|See also)\b[^\n]*:"
)
_CITATION_RE = re.compile(r"\[([A-Z]\d{5}:E\d+)\]")
_MULTI_FAULT_QUERY_RE = re.compile(
    r"(?:哪些|有哪些|分别|多个|多种|可能对应|which|what\s+faults?)",
    re.IGNORECASE,
)


def _as_clean_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values: Iterable[Any] = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = []
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return tuple(result)


def _extract_section_with_span(
    text: str,
    labels: tuple[str, ...],
) -> tuple[str, int | None, int | None]:
    """Return a manual section and its source offsets."""

    matches = list(_SECTION_RE.finditer(text or ""))
    wanted = {label.casefold() for label in labels}
    for index, match in enumerate(matches):
        header = match.group("header").casefold()
        if header not in wanted:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.start():end].strip()
        if not section:
            return "", None, None
        start = match.start()
        # The section is stripped only at the boundaries, so keep citation
        # offsets aligned with the exact quoted text.
        leading = len(text[match.start():end]) - len(text[match.start():end].lstrip())
        trailing = len(text[match.start():end].rstrip())
        return section, start + leading, start + trailing
    return "", None, None


def _extract_section(text: str, labels: tuple[str, ...]) -> str:
    """Return a manual section including its header, bounded by the next header."""

    return _extract_section_with_span(text, labels)[0]


def _evidence_for_sample(
    sample: dict[str, Any],
    fault_code: str,
) -> tuple[EvidenceCitation, ...]:
    raw_spans = sample.get("evidence_spans", [])
    if not isinstance(raw_spans, list):
        raw_spans = []

    source_file = str(
        sample.get("source_file")
        or sample.get("provenance", {}).get("source_file_declared", "")
        or ""
    ).strip()
    result: list[EvidenceCitation] = []
    seen: set[tuple[str, str, Any, Any]] = set()
    for index, raw in enumerate(raw_spans, start=1):
        if not isinstance(raw, dict):
            continue
        quote = str(raw.get("quote") or "").strip()
        field = str(raw.get("field") or "").strip() or "source"
        if not quote:
            continue
        key = (field, quote, raw.get("start"), raw.get("end"))
        if key in seen:
            continue
        seen.add(key)
        result.append(
            EvidenceCitation(
                citation_id=f"{fault_code}:E{len(result) + 1}",
                field=field,
                quote=quote,
                source_id=str(raw.get("source_id") or "input_text"),
                source_file=source_file,
                start=raw.get("start") if isinstance(raw.get("start"), int) else None,
                end=raw.get("end") if isinstance(raw.get("end"), int) else None,
            )
        )
    input_text = str(sample.get("input_text") or "")
    for field, labels in (
        ("alarm_value", ("Alarm value", "Fault value")),
        ("remedy", ("Remedy",)),
    ):
        section, start, end = _extract_section_with_span(input_text, labels)
        if not section:
            continue
        result.append(
            EvidenceCitation(
                citation_id=f"{fault_code}:E{len(result) + 1}",
                field=field,
                quote=section,
                source_id="input_text",
                source_file=source_file,
                start=start,
                end=end,
            )
        )
    return tuple(result)


class GoldFaultContextStore(FaultContextLoader):
    """Load complete fault contexts and evidence from the frozen Gold JSON."""

    def __init__(self, gold_path: str | Path) -> None:
        path = Path(gold_path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise RagServiceError("gold_unavailable", f"无法读取 Gold 数据：{path}") from exc
        except json.JSONDecodeError as exc:
            raise RagServiceError("gold_invalid", f"Gold JSON 无法解析：{path}") from exc
        self._load_payload(payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "GoldFaultContextStore":
        instance = cls.__new__(cls)
        instance._load_payload(payload)
        return instance

    def _load_payload(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
            raise RagServiceError("gold_invalid", "Gold 数据缺少 samples 列表")

        contexts: dict[str, FaultContext] = {}
        for sample in payload["samples"]:
            if not isinstance(sample, dict):
                continue
            input_text = str(sample.get("input_text") or "")
            source_file = str(
                sample.get("source_file")
                or sample.get("provenance", {}).get("source_file_declared", "")
                or ""
            ).strip()
            records = sample.get("gold_records", [])
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                code = str(record.get("fault_code") or "").strip().upper()
                description = str(record.get("description") or "").strip()
                if not code or not description:
                    continue
                contexts[code] = FaultContext(
                    fault_code=code,
                    description=description,
                    component=str(record.get("component") or "").strip(),
                    related_components=_as_clean_strings(record.get("related_components")),
                    causes=_as_clean_strings(record.get("causes")),
                    parameters=_as_clean_strings(record.get("parameters")),
                    alarm_value=_extract_section(input_text, ("Alarm value", "Fault value")),
                    remedy=_extract_section(input_text, ("Remedy",)),
                    evidence=_evidence_for_sample(sample, code),
                    source_file=source_file,
                    raw_text=input_text,
                )
        self._contexts = contexts

    def load(self, fault_codes: Sequence[str]) -> Sequence[FaultContext]:
        requested: list[str] = []
        seen: set[str] = set()
        for raw_code in fault_codes:
            code = str(raw_code or "").strip().upper()
            if code and code not in seen:
                requested.append(code)
                seen.add(code)
        missing = [code for code in requested if code not in self._contexts]
        if missing:
            raise RagServiceError(
                "fault_context_missing",
                f"Gold 中不存在检索到的故障记录：{', '.join(missing)}",
            )
        return tuple(self._contexts[code] for code in requested)

    def all_contexts(self) -> Sequence[FaultContext]:
        """Return all loaded contexts for an index-building adapter."""

        return tuple(self._contexts[code] for code in sorted(self._contexts))


class EvidenceBoundPromptBuilder:
    """Build a prompt that only permits claims supported by supplied spans."""

    def build(
        self,
        question: str,
        contexts: Sequence[FaultContext],
        *,
        response_policy: str = "normal",
        missing_information: Sequence[str] = (),
    ) -> str:
        blocks: list[str] = []
        for context in contexts:
            evidence_lines = []
            for evidence in context.evidence:
                location = ""
                if evidence.start is not None and evidence.end is not None:
                    location = f"; offset={evidence.start}-{evidence.end}"
                evidence_lines.append(
                    f"[{evidence.citation_id}] field={evidence.field}; source={evidence.source_file or evidence.source_id}"
                    f"{location}; quote={evidence.quote}"
                )
            blocks.append(
                "\n".join(
                    [
                        f"Fault code: {context.fault_code}",
                        f"Description: {context.description}",
                        f"Component: {context.component or '(none)'}",
                        f"Related components: {', '.join(context.related_components) or '(none)'}",
                        f"Causes: {' | '.join(context.causes) or '(none)'}",
                        f"Parameters: {', '.join(context.parameters) or '(none)'}",
                        f"Alarm value section:\n{context.alarm_value or '(none)'}",
                        f"Remedy section:\n{context.remedy or '(none)'}",
                        "Evidence spans:\n" + ("\n".join(evidence_lines) or "(none)"),
                        self._relation_block(context.relations),
                    ]
                )
            )

        policy_instruction = {
            "warning": (
                "当前问题缺少明确的 S210 故障码或设备型号。可以根据证据回答，但必须降低确定性，"
                "明确说明这是可能相关的故障，并提示用户补充："
                + ("、".join(missing_information) or "故障码或设备型号")
                + "。"
            ),
            "normal": "当前问题可以基于证据正常回答。",
        }.get(
            response_policy,
            "当前证据不足，不得给出确定性诊断。",
        )
        return (
            "你是 Siemens S210 工业故障诊断助手。只能使用下方故障记录和 Evidence spans 回答。\n"
            "要求：\n"
            "1. 用中文回答，按‘结论、依据、原因、建议处理’组织。\n"
            "2. 每个具体事实后引用对应证据，格式必须是 [FAULT_CODE:EX]；结论第一行必须同时引用故障码和故障现象的证据。\n"
            "3. 不得把一个 fault 的原因、参数或处理措施混到另一个 fault。\n"
            "4. 原文没有支持的内容必须明确写‘当前证据未说明’，不得补造参数、原因或维修结论。\n"
            "5. 默认只回答上下文中的首位候选故障；只有用户明确询问多个故障，或上下文已标记为同描述且排名接近时，才并列回答多个故障。\n"
            "6. 不要为了展示候选而主动扩展其他故障；未纳入回答范围的候选不得在回答中引用。\n"
            "7. 若上下文提供了有证据的 Fault Relation，且用户问题命中该关系触发词，必须说明主故障与关联故障/消息码的关系；不能把关系证据扩展成未被原文支持的参数含义。\n\n"
            f"回答策略：{policy_instruction}\n\n"
            f"用户问题：{question.strip()}\n\n"
            "候选故障上下文：\n"
            + "\n\n---\n\n".join(blocks)
        )

    @staticmethod
    def _relation_block(relations: Sequence[FaultRelation]) -> str:
        if not relations:
            return "Fault relations:\n(none)"
        lines = ["Fault relations:"]
        for relation in relations:
            lines.append(
                f"- relation_id={relation.relation_id}; primary={relation.primary_fault_code}; "
                f"related={relation.related_fault_code}; type={relation.relation_type}; "
                f"review_status={relation.review_status}; note={relation.relation_note}"
            )
            for evidence in relation.evidence:
                lines.append(
                    f"  [{evidence.citation_id}] relation_field={evidence.field}; "
                    f"quote={evidence.quote}"
                )
        return "\n".join(lines)


class PromptAnswerGenerator(AnswerGenerator):
    """Generate an answer through the provider-neutral ModelClient port."""

    def __init__(
        self,
        client: ModelClient,
        *,
        model_name: str = "",
        prompt_builder: EvidenceBoundPromptBuilder | None = None,
    ) -> None:
        self._client = client
        self._model_name = model_name
        self._prompt_builder = prompt_builder or EvidenceBoundPromptBuilder()

    def generate(
        self,
        question: str,
        contexts: Sequence[FaultContext],
    ) -> GeneratedAnswer:
        if not contexts:
            raise RagServiceError("answer_context_empty", "没有可用于回答的故障上下文")
        return self._generate_with_policy(
            question,
            contexts,
            response_policy="normal",
            missing_information=(),
        )

    def generate_with_policy(
        self,
        question: str,
        contexts: Sequence[FaultContext],
        *,
        response_policy: str,
        missing_information: Sequence[str] = (),
    ) -> GeneratedAnswer:
        return self._generate_with_policy(
            question,
            contexts,
            response_policy=response_policy,
            missing_information=missing_information,
        )

    def _generate_with_policy(
        self,
        question: str,
        contexts: Sequence[FaultContext],
        *,
        response_policy: str,
        missing_information: Sequence[str],
    ) -> GeneratedAnswer:
        text = self._client.complete(
            self._prompt_builder.build(
                question,
                contexts,
                response_policy=response_policy,
                missing_information=missing_information,
            )
        ).strip()
        if not text:
            raise RagServiceError("answer_empty", "模型未返回有效回答")
        citations = tuple(dict.fromkeys(_CITATION_RE.findall(text)))
        available = {
            evidence.citation_id
            for context in contexts
            for evidence in context.evidence
        }
        unknown = [citation for citation in citations if citation not in available]
        if unknown:
            raise RagServiceError(
                "answer_unknown_evidence",
                f"模型引用了上下文之外的证据：{', '.join(unknown)}",
            )
        if not citations:
            raise RagServiceError(
                "answer_missing_evidence_citation",
                "模型回答没有引用任何原始证据，已拒绝作为可信回答返回",
            )
        return GeneratedAnswer(text=text, citations=citations, model=self._model_name)


def build_boundary_rag_response(
    question: str,
    boundary: RagBoundaryDecision,
) -> RagResponse:
    """Build a safe non-answer without constructing the heavy retriever."""

    return RagResponse(
        question=str(question or "").strip(),
        answer=GeneratedAnswer(
            text=boundary_message(boundary),
            citations=(),
            model="boundary-policy",
        ),
        retrieved=(),
        contexts=(),
        evidence_status="not_answered",
        boundary=boundary,
    )


class FaultRagService:
    """Orchestrate retrieval, full-context loading and evidence-bound generation."""

    def __init__(
        self,
        retriever: FaultRetriever,
        context_loader: FaultContextLoader,
        answer_generator: AnswerGenerator,
        relation_registry: FaultRelationRegistry | None = None,
        response_policy_layer: ResponsePolicyLayer | None = None,
    ) -> None:
        self._retriever = retriever
        self._context_loader = context_loader
        self._answer_generator = answer_generator
        self._relation_registry = relation_registry or FaultRelationRegistry()
        self._response_policy_layer = response_policy_layer or ResponsePolicyLayer()

    @staticmethod
    def _boundary_answer(boundary: RagBoundaryDecision) -> GeneratedAnswer:
        return GeneratedAnswer(
            text=boundary_message(boundary),
            citations=(),
            model="boundary-policy",
        )

    @staticmethod
    def _generation_contexts(
        question: str,
        candidates: Sequence[RetrievedFault],
        contexts: Sequence[FaultContext],
    ) -> tuple[FaultContext, ...]:
        """Scope generation to the primary fault unless ambiguity is evidenced.

        Retrieval may return a broad candidate set for UI/debugging.  Passing
        every candidate to the answer model makes it likely to mix valid facts
        from unrelated faults.  Multiple contexts are retained only when the
        user asks for multiple faults or the next candidate is a near-tied
        duplicate description, which is the meaningful ambiguity case.
        """

        if len(contexts) <= 1 or len(candidates) <= 1:
            return tuple(contexts)

        candidate_by_code = {
            str(candidate.fault_code).strip().upper(): candidate
            for candidate in candidates
        }
        top_context = contexts[0]
        top_candidate = candidate_by_code.get(top_context.fault_code.upper())
        top_score = top_candidate.score if top_candidate else None
        explicit_multi = _MULTI_FAULT_QUERY_RE.search(question) is not None
        selected: list[FaultContext] = [top_context]

        def close_to_top(candidate: RetrievedFault | None) -> bool:
            if candidate is None or top_score is None or candidate.score is None:
                return False
            return float(top_score) - float(candidate.score) <= 0.05

        top_description = " ".join(top_context.description.casefold().split())
        for context in contexts[1:]:
            candidate = candidate_by_code.get(context.fault_code.upper())
            same_description = (
                bool(top_description)
                and " ".join(context.description.casefold().split()) == top_description
            )
            if (explicit_multi or same_description) and close_to_top(candidate):
                selected.append(context)
            else:
                break
        return tuple(selected)

    def answer(self, question: str, *, top_k: int = 5) -> RagResponse:
        safe_question = str(question or "").strip()
        if not safe_question:
            raise RagServiceError("question_empty", "问题不能为空")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
            raise RagServiceError("top_k_invalid", "top_k 必须是 1 到 10 之间的整数")

        # An explicit external-domain query can be rejected before loading the
        # heavy retriever. Low-information and technical queries still proceed
        # to retrieval and are assessed again once evidence contexts exist.
        preflight_boundary = self._response_policy_layer.assess_boundary(
            question=safe_question,
            contexts=(),
        )
        if preflight_boundary.knowledge_status == "out_of_domain":
            return RagResponse(
                question=safe_question,
                answer=self._boundary_answer(preflight_boundary),
                retrieved=(),
                contexts=(),
                evidence_status="not_answered",
                boundary=preflight_boundary,
            )

        raw_candidates = self._retriever.retrieve(safe_question, limit=top_k)
        candidates: list[RetrievedFault] = []
        seen: set[str] = set()
        for candidate in raw_candidates:
            code = str(candidate.fault_code or "").strip().upper()
            if not code or code in seen:
                continue
            candidates.append(
                RetrievedFault(
                    fault_code=code,
                    score=candidate.score,
                    rank=candidate.rank or len(candidates) + 1,
                    signals=candidate.signals,
                )
            )
            seen.add(code)
        if not candidates:
            raise RagServiceError("retrieval_empty", "当前问题没有召回候选故障")

        candidate_contexts = tuple(
            self._context_loader.load([candidate.fault_code for candidate in candidates])
        )
        if not candidate_contexts:
            raise RagServiceError("context_empty", "候选故障没有可加载的完整上下文")
        boundary = self._response_policy_layer.assess_boundary(
            question=safe_question,
            contexts=candidate_contexts,
        )
        if not boundary.answer_allowed:
            return RagResponse(
                question=safe_question,
                answer=self._boundary_answer(boundary),
                retrieved=tuple(candidates),
                contexts=tuple(candidate_contexts),
                evidence_status="not_answered",
                boundary=boundary,
            )
        primary_code = candidate_contexts[0].fault_code.upper()
        related_codes = self._relation_registry.triggered_related_codes(
            safe_question,
            primary_code,
        )
        related_contexts: tuple[FaultContext, ...] = ()
        if related_codes:
            try:
                related_contexts = tuple(self._context_loader.load(related_codes))
            except RagServiceError:
                # A stale optional registry must not take down the base RAG path.
                related_contexts = ()
        all_contexts: list[FaultContext] = list(candidate_contexts)
        loaded_codes = {context.fault_code.upper() for context in all_contexts}
        for context in related_contexts:
            if context.fault_code.upper() not in loaded_codes:
                all_contexts.append(context)
                loaded_codes.add(context.fault_code.upper())
        relations = self._relation_registry.expand(
            safe_question,
            primary_code,
            tuple(all_contexts),
        )
        generation_contexts = self._generation_contexts(
            safe_question,
            candidates,
            candidate_contexts,
        )
        if relations:
            generation_contexts = tuple(
                replace(context, relations=relations)
                if context.fault_code.upper() == primary_code
                else context
                for context in generation_contexts
            )
            generation_codes = {context.fault_code.upper() for context in generation_contexts}
            generation_contexts = generation_contexts + tuple(
                context
                for context in related_contexts
                if context.fault_code.upper() not in generation_codes
            )
        generate_with_policy = getattr(self._answer_generator, "generate_with_policy", None)
        if callable(generate_with_policy):
            generated = generate_with_policy(
                safe_question,
                generation_contexts,
                response_policy=boundary.response_policy,
                missing_information=boundary.missing_information,
            )
        else:
            generated = self._answer_generator.generate(safe_question, generation_contexts)
        expected_citations = {
            evidence.citation_id
            for context in generation_contexts
            for evidence in context.evidence
        }
        evidence_status = "cited" if set(generated.citations) <= expected_citations else "invalid"
        if evidence_status != "cited":
            raise RagServiceError("evidence_contract_failed", "回答证据引用不在候选上下文中")
        return RagResponse(
            question=safe_question,
            answer=generated,
            retrieved=tuple(candidates),
            contexts=tuple(all_contexts),
            relations=relations,
            evidence_status=evidence_status,
            boundary=boundary,
        )


def rag_response_to_dict(response: RagResponse) -> dict[str, Any]:
    """Serialize the service response for a future HTTP adapter."""

    return asdict(response)
