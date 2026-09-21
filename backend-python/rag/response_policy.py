"""Post-retrieval response-risk policy.

This layer does not decide retrieval scope or ranking. It controls how a
retrieved, evidence-grounded answer may be presented to the user.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Sequence


@dataclass(frozen=True)
class ResponsePolicyDecision:
    response_policy: str
    retrieval_policy: str
    reason: str
    sufficiency_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResponsePolicyV2Decision:
    """Structured answer contract for the v2 policy Gold."""

    policy: str
    answer_allowed: bool
    confidence_level: str
    need_additional_info: bool
    warning_required: bool
    retrieval_policy: str
    reason: str
    sufficiency_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RagBoundaryDecision:
    """Post-retrieval knowledge-boundary decision.

    This is deliberately separate from retrieval ranking.  A candidate can be
    retrieved for diagnostics while the answer layer still refuses to make a
    definitive claim when the query is outside the S210 scope or the evidence
    is insufficient.
    """

    knowledge_status: str
    response_policy: str
    answer_allowed: bool
    confidence_level: str
    need_additional_info: bool
    warning_required: bool
    reason: str
    missing_information: tuple[str, ...] = ()
    matched_scope_signals: tuple[str, ...] = ()
    matched_external_signals: tuple[str, ...] = ()
    matched_context_evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def boundary_message(boundary: RagBoundaryDecision) -> str:
    """Return the safe user-facing message for a non-answer decision."""

    if boundary.knowledge_status == "out_of_domain":
        return (
            "当前系统仅支持 Siemens S210 及已接入的工业故障知识库，"
            "未找到能够支持该问题的证据，因此无法给出可靠诊断。"
        )
    missing = "、".join(boundary.missing_information) or "故障码、设备型号或原始报警文本"
    return (
        "当前信息不足，无法基于 Siemens S210 知识库给出确定诊断。"
        f"请补充{missing}。"
    )


_S210_SCOPE_SIGNALS = (
    "siemens",
    "sinamics",
    "s210",
    "drive-cliq",
    "profinet",
    "profisafe",
    "siemens s210",
)
_S210_IDENTIFIER_RE = re.compile(
    r"(?<![A-Z0-9])(?:[AFN]\d{5}|[PR]\d{4,5}(?:\[\d+\])?)(?![A-Z0-9])",
    re.IGNORECASE,
)
_QUOTED_QUERY_RE = re.compile(r"[\"“](.+?)[\"”]")
_SPECIFIC_TECHNICAL_SIGNALS = (
    "temperature",
    "overheat",
    "communication",
    "voltage",
    "parameter",
    "温度",
    "过热",
    "通信",
    "电压",
    "同步",
    "参数",
    "信号",
    "sto",
    "si motion",
    "编码器",
    "电机",
    "控制单元",
    "驱动器",
    "驱动",
)
_EXTERNAL_SCOPE_SIGNALS = (
    "天气",
    "股票",
    "基金",
    "食谱",
    "旅游",
    "新闻",
    "法律咨询",
    "写诗",
    "写一首诗",
    "翻译",
    "航空",
    "飞机",
    "航空器",
    "aerospace",
    "aircraft",
    "ata",
    "lru",
    "jasc",
)


def _matched_terms(text: str, terms: Sequence[str]) -> tuple[str, ...]:
    normalized = str(text or "").casefold()
    matched: list[str] = []
    for term in terms:
        candidate = term.casefold()
        if re.fullmatch(r"[a-z0-9][a-z0-9 -]*", candidate):
            pattern = rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])"
            if re.search(pattern, normalized):
                matched.append(term)
        elif candidate in normalized:
            matched.append(term)
    return tuple(matched)


def _context_texts(contexts: Sequence[Any]) -> tuple[str, ...]:
    texts: list[str] = []
    for context in contexts:
        values = [
            getattr(context, "fault_code", ""),
            getattr(context, "description", ""),
            getattr(context, "component", ""),
            getattr(context, "alarm_value", ""),
            getattr(context, "remedy", ""),
            " ".join(getattr(context, "causes", ()) or ()),
            " ".join(getattr(context, "parameters", ()) or ()),
            getattr(context, "raw_text", ""),
        ]
        texts.append(" ".join(str(value or "") for value in values))
    return tuple(texts)


def _direct_context_evidence(question: str, contexts: Sequence[Any]) -> tuple[str, ...]:
    """Return quoted query fragments found verbatim in loaded source context."""

    context_text = " ".join(_context_texts(contexts)).casefold()
    matches: list[str] = []
    for raw in _QUOTED_QUERY_RE.findall(question):
        fragment = " ".join(str(raw).split()).strip()
        if len(fragment) >= 6 and fragment.casefold() in context_text:
            matches.append(fragment)
    return tuple(dict.fromkeys(matches))


class ResponsePolicyLayer:
    """Map query-analysis risk to answer behavior after retrieval."""

    def decide(self, *, sufficiency_level: str) -> ResponsePolicyDecision:
        if sufficiency_level not in {"sufficient", "partially_sufficient", "insufficient", "cannot_determine"}:
            raise ValueError(f"unsupported sufficiency_level: {sufficiency_level}")
        if sufficiency_level == "insufficient":
            return ResponsePolicyDecision(
                response_policy="clarify",
                retrieval_policy="allow",
                reason="retrieval may inform the clarification, but no definitive answer should be produced",
                sufficiency_level=sufficiency_level,
            )
        if sufficiency_level in {"partially_sufficient", "cannot_determine"}:
            return ResponsePolicyDecision(
                response_policy="warning",
                retrieval_policy="allow",
                reason="answer should state uncertainty and request missing context or domain context",
                sufficiency_level=sufficiency_level,
            )
        return ResponsePolicyDecision(
            response_policy="normal",
            retrieval_policy="allow",
            reason="query context is sufficient for a normal evidence-grounded answer",
            sufficiency_level=sufficiency_level,
        )

    def decide_v2(self, *, sufficiency_level: str) -> ResponsePolicyV2Decision:
        """Return an explicit answer-allowed/confidence contract.

        Retrieval remains allowed for every policy.  The v2 fields only control
        whether and how a definitive answer may be presented.
        """

        if sufficiency_level not in {"sufficient", "partially_sufficient", "insufficient", "cannot_determine"}:
            raise ValueError(f"unsupported sufficiency_level: {sufficiency_level}")
        if sufficiency_level == "insufficient":
            return ResponsePolicyV2Decision(
                policy="P2_ASK_BEFORE_DEFINITIVE_ANSWER",
                answer_allowed=False,
                confidence_level="low",
                need_additional_info=True,
                warning_required=False,
                retrieval_policy="allow",
                reason="retrieve candidates if useful, then ask for missing context before a definitive answer",
                sufficiency_level=sufficiency_level,
            )
        if sufficiency_level in {"partially_sufficient", "cannot_determine"}:
            return ResponsePolicyV2Decision(
                policy="P1_ANSWER_WITH_WARNING",
                answer_allowed=True,
                confidence_level="medium",
                need_additional_info=True,
                warning_required=True,
                retrieval_policy="allow",
                reason="answer from evidence with reduced certainty and request missing context",
                sufficiency_level=sufficiency_level,
            )
        return ResponsePolicyV2Decision(
            policy="P0_DIRECT_ANSWER",
            answer_allowed=True,
            confidence_level="high",
            need_additional_info=False,
            warning_required=False,
            retrieval_policy="allow",
            reason="query context is sufficient for a direct evidence-grounded answer",
            sufficiency_level=sufficiency_level,
        )

    def assess_boundary(
        self,
        *,
        question: str,
        contexts: Sequence[Any],
    ) -> RagBoundaryDecision:
        """Assess whether a retrieved answer is safe within the S210 scope.

        The method is intentionally conservative and explainable.  Explicit
        non-S210 topics are rejected; low-information industrial queries are
        not treated as out-of-domain, but they cannot receive a definitive
        answer.  Exact identifiers or explicit S210 signals allow a normal
        answer, while technical queries without a strong identity signal are
        answered with a warning.
        """

        text = str(question or "").strip()
        if not text:
            raise ValueError("question cannot be empty")
        scope_signals = _matched_terms(text, _S210_SCOPE_SIGNALS)
        external_signals = _matched_terms(text, _EXTERNAL_SCOPE_SIGNALS)
        has_identifier = bool(_S210_IDENTIFIER_RE.search(text))
        specific_technical_signals = _matched_terms(text, _SPECIFIC_TECHNICAL_SIGNALS)
        has_context = bool(contexts)
        context_evidence = _direct_context_evidence(text, contexts)

        if (
            external_signals
            and not scope_signals
            and not has_identifier
            and not context_evidence
        ):
            return RagBoundaryDecision(
                knowledge_status="out_of_domain",
                response_policy="out_of_domain",
                answer_allowed=False,
                confidence_level="low",
                need_additional_info=False,
                warning_required=False,
                reason="query contains explicit signals for a domain outside the S210 knowledge base",
                matched_external_signals=external_signals,
            )

        if not has_context:
            return RagBoundaryDecision(
                knowledge_status="insufficient_evidence",
                response_policy="clarify",
                answer_allowed=False,
                confidence_level="low",
                need_additional_info=True,
                warning_required=False,
                reason="no complete fault context was available after retrieval",
                missing_information=("fault_code_or_supported_evidence",),
                matched_scope_signals=scope_signals,
                matched_external_signals=external_signals,
            )

        if has_identifier or scope_signals or context_evidence:
            return RagBoundaryDecision(
                knowledge_status="supported",
                response_policy="normal",
                answer_allowed=True,
                confidence_level="high",
                need_additional_info=False,
                warning_required=False,
                reason=(
                    "query contains an S210 identifier or explicit supported-scope signal"
                    if not context_evidence
                    else "quoted query evidence was found in the loaded S210 source context"
                ),
                matched_scope_signals=scope_signals,
                matched_context_evidence=context_evidence,
            )

        if specific_technical_signals:
            return RagBoundaryDecision(
                knowledge_status="supported_with_warning",
                response_policy="warning",
                answer_allowed=True,
                confidence_level="medium",
                need_additional_info=True,
                warning_required=True,
                reason="technical query lacks an explicit S210 identity signal",
                missing_information=("fault_code_or_device_model",),
                matched_scope_signals=scope_signals,
            )

        return RagBoundaryDecision(
            knowledge_status="insufficient_evidence",
            response_policy="clarify",
            answer_allowed=False,
            confidence_level="low",
            need_additional_info=True,
            warning_required=False,
            reason="query does not provide enough technical or S210 context for a reliable answer",
            missing_information=("device_model", "fault_code_or_symptom"),
            matched_scope_signals=scope_signals,
        )
