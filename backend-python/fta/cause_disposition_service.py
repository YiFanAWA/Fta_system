"""Propose evidence-bound semantic dispositions for extracted causes."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from contracts.extraction_contract import EvidenceField, EvidenceSpan, ExtractionResult
from contracts.evidence_locator_review_contract import (
    EvidenceLocatorTargetField,
    EvidenceOccurrenceLocatorReview,
)
from contracts.fta_cause_disposition_contract import (
    CauseDisposition,
    CauseDispositionEvidence,
    CauseDispositionReasonCode,
    CauseSemanticRole,
    FtaCauseDispositionBatch,
    FtaCauseDispositionKind,
    HOST_DISPOSITION_NORMALIZATION_PROVENANCE,
)
from core.model_client import ModelClient
from fta.evidence_locator_review_service import EvidenceLocatorReviewResolver


class CauseDispositionValidationError(ValueError):
    """Raised when the model response cannot be represented safely."""


CAUSE_DISPOSITION_PROMPT_VERSION = "fta-cause-disposition-v6"


def build_cause_disposition_prompt(
    extraction: ExtractionResult,
    record_id: str,
    source_text: str,
    locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
) -> str:
    record = next(
        (item for item in extraction.records if item.record_id == record_id),
        None,
    )
    if record is None:
        raise ValueError("record_id is not present in the extraction result")
    cause_evidence = []
    for index, cause in enumerate(record.causes):
        spans = [
            span
            for span in extraction.evidence_spans
            if span.record_id == record.record_id
            and span.field is EvidenceField.CAUSE
            and span.value_index == index
            and span.matches(source_text)
        ]
        cause_evidence.append(
            {
                "source_cause_index": index,
                "source_cause_text": cause,
                "attached_extraction_evidence": [
                    {
                        "citation_id": (
                            f"{span.record_id}:{span.field.value}:{span.start}-{span.end}"
                        ),
                        "quote": span.quote,
                        "start": span.start,
                        "end": span.end,
                    }
                    for span in spans
                ],
            }
        )
    locator_resolver = EvidenceLocatorReviewResolver(
        extraction,
        record.record_id,
        source_text,
        locator_reviews,
    )
    payload = {
        "task": "fta_cause_semantic_disposition",
        "prompt_version": CAUSE_DISPOSITION_PROMPT_VERSION,
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "top_event": record.description,
        "causes": cause_evidence,
        "reviewed_locator_decisions": locator_resolver.prompt_payload(),
        "complete_source_text": source_text,
    }
    return (
        "你只对抽取出的每条 causes 原文逐项分类，不创建故障树、不判断 AND/OR，也不生成因果边。"
        "每个 source_cause_index 必须且只能输出一项；不要按文本去重，重复短语也按索引分别处理。"
        "semantic_role 只能是 causal_condition、diagnostic_mapping、fault_value_mode、consequence、"
        "state、causal_summary、remedy、other、mixed_unresolved 之一。"
        "fta_disposition 只能是 fta_event_candidate、detached_observation、relation_only、exclude_from_tree、unresolved 之一。"
        "causal_condition/state 才可能是 fta_event_candidate；诊断映射、故障值位义、后果、摘要和处理动作不能仅凭字段名变成树事件。"
        "按命题语义与该段落的交际功能分类，不按句子是否流畅或是否出现在 Cause 标题下分类。"
        "必须把每条原因命题与 payload 中的 top_event 做语义比较：判断它是否提供了一个可区分的上游事件、条件、机制或触发过程。"
        "如果它只是在定义、释义、同义改写或重复 top_event，且没有增加独立的前因信息，标为 causal_summary + relation_only，"
        "reason_code 使用 summary_not_independent_event；不能因为它位于 Cause 段或是自然语言就升级为树事件候选。"
        "如果无法确定该句是否包含独立上游信息，标 unresolved + semantic_role_uncertain；不得猜测或把顶事件自身接成它的原因。"
        "只有原文直接支持、且语义上不同于顶事件本身的上游条件/机制，才可成为 fta_event_candidate。"
        "在原文中被明确列为该故障可能原因的自然语言故障条件/场景，可以标为 causal_condition + fta_event_candidate；"
        "它只代表有原文依据的候选原因/候选边，不代表现场实例已经发生，也不代表因果关系已由专家确认。"
        "若原文明确报告了一个状态/报警观察，但只说明共现、记录顺序或时间先后，没有说它导致当前顶事件或与其他 child 共同必要，"
        "标为 state + detached_observation + descriptive_association。宿主会将其作为有证据的独立 observation_candidate 保留在断开的候选区，"
        "阻断整棵树；它不是 FTA event，不得连接到顶事件，也不得参与 AND/OR。"
        "诊断映射必须与自然语言原因区分：由 fault code、fault value、参数号、位号或索引映射到解释文本的条目，"
        "其首要功能是说明诊断值/消息代表什么；即使解释文本写成完整自然语言、描述配置冲突或条件，也不得仅凭这条映射自动连到当前顶事件。"
        "这类条目标为 diagnostic_mapping 或 fault_value_mode + relation_only，并完整保留在审计账。"
        "只有原文在该映射之外另有直接证据，明确把相应自然语言条件列为该故障的可能原因/触发条件，才可据该独立证据将其作为 causal_condition 候选；"
        "不得把映射表中的解释句本身当作独立因果边证据。"
        "例如：‘Possible causes: valve stuck’可作为候选原因；‘xxxx=12 means parameter/configuration conflict’仍是诊断映射，不能只凭该行连到顶事件。"
        "上述原因候选的 AND/OR 门仍须由独立直接逻辑证据判断，不能从候选原因清单自动推出。"
        "处理动作（检查、更换、复位、升级等）不是上游故障事件。下游后果不是当前顶事件的上游原因。"
        "一个完整因果句可以同时写出中间状态及其成因（如‘电阻器过热，因为单位时间内预充次数过多’）；若整句在原因范围内明确表达因果条件，应保留整句作为一个 causal_condition 候选，不要仅因包含状态和因果子句就判 mixed_unresolved，也不要自动拆句。"
        "只有当同一抽取项确实混合互不相同且无法安全归为单一因果命题的角色（例如原因与处理动作拼在一起），才用 mixed_unresolved。"
        "只有原文证据支持语义角色和处置时才能给出确定处置；角色无法区分、缺证据或证据短语重复且无法唯一定位，一律 unresolved。"
        "已审核的 reviewed_locator_decisions 只确认某个原文出现位置，不代表原因语义审核、领域专家签署或 Gold。若某原因有已确认 locator，"
        "其 selected_extraction_evidence.quote 是唯一可用的 evidence_quote；必须逐字返回该引文，不得扩写成跨越 scope 的上下文，也不得把定位结论当作因果结论。"
        "每项提供 evidence_quote：必须是原文中直接支持该项判断的连续精确短引文。对已审核 locator，唯一性以审核 scope 为准且必须精确采用 selected_extraction_evidence.quote；没有 locator 时，引文必须在全文只出现一次。"
        "若没有 locator 且找不到全文唯一引文，evidence_quote 置空并选 unresolved。不要猜字符位置。"
        "reason_code 只能是 direct_causal_or_condition_statement、diagnostic_mapping_without_instance_evidence、"
        "fault_value_mode_without_instance_evidence、downstream_consequence、remedy_action、"
        "summary_not_independent_event、descriptive_association、mixed_semantics、semantic_role_uncertain、"
        "evidence_missing_or_ambiguous、classification_missing、semantic_disposition_conflict、"
        "other_non_causal_content 之一。rationale 用简短中文说明；模型结果始终只是 ai_proposed，不是 Gold 或专家签署。"
        "严格输出 JSON："
        '{"cause_dispositions":[{"source_cause_index":0,"semantic_role":"causal_condition",'
        '"fta_disposition":"fta_event_candidate","evidence_quote":"...",'
        '"reason_code":"direct_causal_or_condition_statement","rationale":"..."}]}\n\n'
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


class CauseDispositionService:
    """Turn one model proposal into a total, evidence-checked cause ledger."""

    def __init__(self, model_client: ModelClient) -> None:
        if not hasattr(model_client, "complete"):
            raise TypeError("model_client must implement complete(prompt)")
        self._model_client = model_client

    def propose(
        self,
        extraction: ExtractionResult,
        record_id: str,
        source_text: str,
        locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> FtaCauseDispositionBatch:
        if not isinstance(extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must be a non-empty string")
        record = next(
            (item for item in extraction.records if item.record_id == record_id),
            None,
        )
        if record is None:
            raise ValueError("record_id is not present in the extraction result")

        locator_resolver = EvidenceLocatorReviewResolver(
            extraction,
            record.record_id,
            source_text,
            locator_reviews,
        )

        extraction_cause_spans: dict[int, list[EvidenceSpan]] = {}
        for span in extraction.evidence_spans:
            if (
                span.record_id == record.record_id
                and span.field is EvidenceField.CAUSE
                and span.value_index is not None
                and span.matches(source_text)
            ):
                extraction_cause_spans.setdefault(span.value_index, []).append(span)

        raw = self._model_client.complete(
            build_cause_disposition_prompt(
                extraction, record_id, source_text, locator_reviews
            )
        )
        payload = self._parse_payload(raw)
        proposed = payload.get("cause_dispositions")
        if proposed is None:
            proposed = []
        if not isinstance(proposed, list):
            raise CauseDispositionValidationError(
                "cause_dispositions must be a list"
            )

        by_index: dict[int, dict[str, Any]] = {}
        duplicate_indices: set[int] = set()
        for item in proposed:
            if not isinstance(item, dict):
                raise CauseDispositionValidationError(
                    "each cause disposition must be an object"
                )
            index = item.get("source_cause_index")
            if isinstance(index, bool) or not isinstance(index, int):
                raise CauseDispositionValidationError(
                    "source_cause_index must be an integer"
                )
            if not 0 <= index < len(record.causes):
                raise CauseDispositionValidationError(
                    "source_cause_index is outside the extracted cause list"
                )
            if index in by_index:
                duplicate_indices.add(index)
            by_index[index] = item

        results: list[CauseDisposition] = []
        for index, source_cause in enumerate(record.causes):
            attached_extraction_spans = extraction_cause_spans.get(index, [])
            reviewed_span = locator_resolver.selected_span(
                EvidenceLocatorTargetField.CAUSE, index
            )
            effective_extraction_spans = (
                [reviewed_span]
                if reviewed_span is not None
                else attached_extraction_spans
            )
            if len(effective_extraction_spans) != 1:
                span_state = "缺失" if not effective_extraction_spans else "多重/歧义"
                results.append(
                    self._unresolved(
                        index,
                        source_cause,
                        reason_code=CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS,
                        rationale=(
                            f"抽取阶段的该原因证据跨度{span_state}"
                            f"（有效跨度数={len(attached_extraction_spans)}，"
                            f"审核定位后跨度数={len(effective_extraction_spans)}）。"
                            "处置阶段从全文另行绑定的引文不能替代抽取证据；需人工补证或定位。"
                        ),
                    )
                )
                continue

            item = by_index.get(index)
            if item is None or index in duplicate_indices:
                results.append(
                    self._unresolved(
                        index,
                        source_cause,
                        reason_code=CauseDispositionReasonCode.CLASSIFICATION_MISSING,
                        rationale=(
                            "模型未返回该原因的分类。原始抽取已保留；该项未决并阻断候选树放行。"
                            if item is None
                            else "模型对同一原因索引返回了多项冲突分类。原文已保留；该项未决并阻断候选树放行。"
                        ),
                    )
                )
                continue

            try:
                role = CauseSemanticRole(item.get("semantic_role"))
                proposed_disposition = FtaCauseDispositionKind(
                    item.get("fta_disposition")
                )
                reason_code = CauseDispositionReasonCode(item.get("reason_code"))
            except (TypeError, ValueError) as exc:
                raise CauseDispositionValidationError(
                    f"cause index {index} contains an unsupported semantic label"
                ) from exc
            rationale = item.get("rationale")
            quote = item.get("evidence_quote")
            if not isinstance(rationale, str) or not rationale.strip():
                raise CauseDispositionValidationError(
                    f"cause index {index} requires a rationale"
                )
            if not isinstance(quote, str):
                raise CauseDispositionValidationError(
                    f"cause index {index} evidence_quote must be a string"
                )

            if reviewed_span is not None:
                bound = locator_resolver.bind_model_quote(
                    quote, EvidenceLocatorTargetField.CAUSE, index
                )
                evidence = (
                    CauseDispositionEvidence(
                        citation_id=f"input_text:cause_disposition:{bound[0]}-{bound[1]}",
                        source_id="input_text",
                        quote=quote,
                        start=bound[0],
                        end=bound[1],
                    )
                    if bound is not None
                    else None
                )
            else:
                evidence = self._bind_unique_quote(quote, source_text)
            disposition = proposed_disposition
            provenance = "fta_cause_disposition_model"
            if proposed_disposition is not FtaCauseDispositionKind.UNRESOLVED and evidence is None:
                disposition = FtaCauseDispositionKind.UNRESOLVED
                reason_code = CauseDispositionReasonCode.EVIDENCE_MISSING_OR_AMBIGUOUS
                rationale = (
                    rationale.strip()
                    + " 宿主无法将证据引文唯一绑定到原文，因此保留为未决。"
                )
            elif not self._role_allows_disposition(role, proposed_disposition):
                disposition = FtaCauseDispositionKind.UNRESOLVED
                reason_code = CauseDispositionReasonCode.SEMANTIC_DISPOSITION_CONFLICT
                rationale = (
                    rationale.strip()
                    + " 角色与建树处置不相容，宿主改为未决，不将其送入树结构。"
                )
            elif (
                role is CauseSemanticRole.STATE
                and proposed_disposition is FtaCauseDispositionKind.RELATION_ONLY
                and reason_code is CauseDispositionReasonCode.DESCRIPTIVE_ASSOCIATION
            ):
                disposition = FtaCauseDispositionKind.DETACHED_OBSERVATION
                provenance = HOST_DISPOSITION_NORMALIZATION_PROVENANCE
                rationale = (
                    rationale.strip()
                    + " 宿主依据 state + descriptive_association + relation_only 的窄规则，"
                    "规范化为 detached_observation；保留独立观察，不创建因果边或逻辑门。"
                )

            results.append(
                CauseDisposition(
                    source_cause_index=index,
                    source_cause_text=source_cause,
                    semantic_role=role,
                    proposed_disposition=proposed_disposition,
                    disposition=disposition,
                    reason_code=reason_code,
                    rationale=rationale.strip(),
                    evidence=(evidence,) if evidence is not None else (),
                    provenance=provenance,
                )
            )

        return FtaCauseDispositionBatch(
            extraction_result_id=extraction.result_id,
            record_id=record.record_id,
            source_text_sha256=sha256(source_text.encode("utf-8")).hexdigest(),
            dispositions=tuple(results),
            locator_reviews=locator_reviews,
        )

    @staticmethod
    def _role_allows_disposition(
        role: CauseSemanticRole,
        disposition: FtaCauseDispositionKind,
    ) -> bool:
        allowed = {
            CauseSemanticRole.CAUSAL_CONDITION: {
                FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.STATE: {
                FtaCauseDispositionKind.FTA_EVENT_CANDIDATE,
                FtaCauseDispositionKind.DETACHED_OBSERVATION,
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.DIAGNOSTIC_MAPPING: {
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.FAULT_VALUE_MODE: {
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.CONSEQUENCE: {
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.CAUSAL_SUMMARY: {
                FtaCauseDispositionKind.RELATION_ONLY,
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.REMEDY: {
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.OTHER: {
                FtaCauseDispositionKind.EXCLUDE_FROM_TREE,
                FtaCauseDispositionKind.UNRESOLVED,
            },
            CauseSemanticRole.MIXED_UNRESOLVED: {
                FtaCauseDispositionKind.UNRESOLVED,
            },
        }
        return disposition in allowed[role]

    @staticmethod
    def _bind_unique_quote(
        quote: str, source_text: str
    ) -> CauseDispositionEvidence | None:
        if not quote or not quote.strip():
            return None
        first = source_text.find(quote)
        if first < 0 or source_text.find(quote, first + 1) >= 0:
            return None
        return CauseDispositionEvidence(
            citation_id=f"input_text:cause_disposition:{first}-{first + len(quote)}",
            source_id="input_text",
            quote=quote,
            start=first,
            end=first + len(quote),
        )

    @staticmethod
    def _parse_payload(raw: str) -> dict[str, Any]:
        if not isinstance(raw, str):
            raise CauseDispositionValidationError("model response must be a string")
        stripped = raw.strip()
        if stripped.startswith("```"):
            parts = stripped.split("```", 2)
            if len(parts) == 3:
                stripped = parts[1]
                if stripped.lstrip().startswith("json"):
                    stripped = stripped.lstrip()[4:]
                stripped = stripped.strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise CauseDispositionValidationError(
                "model response is not valid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise CauseDispositionValidationError(
                "model response must be a JSON object"
            )
        return payload

    @staticmethod
    def _unresolved(
        index: int,
        source_cause: str,
        *,
        reason_code: CauseDispositionReasonCode,
        rationale: str,
    ) -> CauseDisposition:
        return CauseDisposition(
            source_cause_index=index,
            source_cause_text=source_cause,
            semantic_role=CauseSemanticRole.OTHER,
            proposed_disposition=FtaCauseDispositionKind.UNRESOLVED,
            disposition=FtaCauseDispositionKind.UNRESOLVED,
            reason_code=reason_code,
            rationale=rationale,
        )


__all__ = [
    "CauseDispositionService",
    "CauseDispositionValidationError",
    "build_cause_disposition_prompt",
]
