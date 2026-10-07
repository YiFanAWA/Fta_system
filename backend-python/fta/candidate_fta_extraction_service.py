"""Propose a recursive, source-bound FTA preview from an extracted record."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from contracts.candidate_fta_contract import (
    CandidateFtaEvidence,
    CandidateFtaGateAssessment,
    CandidateFtaNode,
    CandidateFtaRelation,
    CandidateFtaStatus,
    CandidateFtaTree,
    find_disconnected_candidate_node_ids,
    normalize_blockers,
)
from contracts.fta_cause_disposition_contract import (
    CauseDisposition,
    FtaCauseDispositionBatch,
    FtaCauseDispositionKind,
    candidate_source_indices,
)
from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from contracts.evidence_locator_review_contract import (
    EvidenceLocatorTargetField,
    EvidenceOccurrenceLocatorReview,
)
from core.model_client import ModelClient
from fta.cause_disposition_service import (
    CauseDispositionService,
    CauseDispositionValidationError,
)
from fta.evidence_locator_review_service import EvidenceLocatorReviewResolver
from fta.gate_confidence_policy import GateConfidencePolicy
from fta.unknown_gate_reason_policy import resolve_unknown_gate_reason


_GATES = ("AND", "OR", "unknown")
_TOP_EVENT_ALIAS = "__top_event__"


class CandidateFtaValidationError(ValueError):
    """Raised when a model response violates the recursive candidate contract."""


def build_candidate_fta_prompt(
    record: FaultRecord,
    source_text: str,
    cause_ids: tuple[str, ...],
    evidence: tuple[dict[str, Any], ...],
    top_event_evidence: tuple[dict[str, Any], ...],
) -> str:
    """Build the historical single-scope gate probe used by offline evaluation only."""

    payload = {
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "top_event_id": _TOP_EVENT_ALIAS,
        "top_event": record.description,
        "top_event_evidence": list(top_event_evidence),
        "extracted_causes": [
            {"cause_id": cause_id, "cause_index": index, "text": cause}
            for index, (cause_id, cause) in enumerate(zip(cause_ids, record.causes))
        ],
        "attached_extraction_evidence": list(evidence),
        "complete_source_text": source_text,
    }
    return (
        "你负责生成可审计的递归候选 FTA Preview，不得声称已批准、已校准或可生产使用。\n"
        "仅根据原文建立事件/条件节点、逻辑门和有向关系。每个新节点必须给出精确连续原文引文，"
        "并映射到一个或多个 extracted_causes.cause_index；同一抽取原因可拆成多个叶项或父子层级，"
        "但所有输入 cause_index 都必须至少被一个节点引用，不能静默丢弃。\n"
        "顶事件由系统提供，ID 为 __top_event__。中间事件可作门输出或因果关系端点；"
        "cause_candidate 是叶/条件节点。逻辑门仅表示同一输出事件的多个 child 如何组合；"
        "causes/may_cause 是独立的有向关系边，二者不可互相替代。\n"
        "每个 gate_assessment 必须有独立 gate_id、scope_type、output_node_id、child_node_ids、"
        "scope_quote、gate_evidence_quote、原因集合完整性/叶归一化状态和理由。"
        "通常还要输出 AND/OR/unknown 概率分布；但如果该作用域恰好只有一个 child，且原因集合明确完整并已叶归一化，"
        "它没有需要分类的布尔门：省略 gate_probabilities、gate_evidence_quote 留空，宿主会标记 not_applicable，"
        "不把它计入门类型校准。若完整性或叶归一化不确定/为 false，则不能标 not_applicable，必须输出分布并保持 unknown。"
        "scope_quote 必须是包含该门所有 child 与 output 证据的同一局部原文范围。"
        "只有原文明示组合逻辑且原因集合完整、同级、叶归一化时才允许 AND/OR；"
        "概率高不能代替原文证据，根因集合不完整时必须 unknown。\n"
        "gate_evidence_quote 是直接支持逻辑关系的原文，可与 scope_quote 相同；unknown/not_applicable 时置空。"
        "relations 中每条 causes/may_cause/associated_with 边都要有自己的 relation_scope_quote，"
        "该作用域同时包含边两端节点证据；evidence_quote 必须在该关系作用域内并直接支持关系方向。"
        "不要推断原文未声明的逻辑关系，不要从多个列举项自动推 OR。\n"
        "如果某个短引文在原文重复出现、位置不明确，仍可返回引文文本；宿主会阻断并交人工定位，"
        "不得猜选其中一次。模型概率是门类型判断置信度，不是故障发生概率。\n"
        "输出严格 JSON，形状如下："
        '{"nodes":[{"node_id":"local-id","node_type":"intermediate_event_candidate|cause_candidate",'
        '"text":"...","source_cause_indices":[0],"evidence_quote":"..."}],'
        '"gate_assessments":[{"gate_id":"local-gate-id","output_node_id":"local-id|__top_event__",'
        '"child_node_ids":["local-id"],"scope_type":"...",'
        '"gate_probabilities":{"AND":0.0,"OR":0.0,"unknown":1.0},'
        '"scope_quote":"...","gate_evidence_quote":"",'
        '"cause_set_complete":false,"cause_set_leaf_normalized":false,"reason":"..."}],'
        '"relations":[{"source_node_id":"local-id","target_node_id":"__top_event__",'
        '"relation_type":"may_cause","relation_scope_quote":"...",'
        '"evidence_quote":"..."}],'
        '"cause_set_complete":false,"reason":"..."}.\n\n'
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def build_candidate_fta_structure_prompt(
    record: FaultRecord,
    source_text: str,
    cause_ids: tuple[str, ...],
    cause_indices: tuple[int, ...],
    cause_dispositions: FtaCauseDispositionBatch,
    evidence: tuple[dict[str, Any], ...],
    top_event_evidence: tuple[dict[str, Any], ...],
    reviewed_locator_decisions: tuple[dict[str, object], ...] = (),
) -> str:
    """Ask only for an evidence-bound event hierarchy and Boolean scopes."""

    payload = {
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "top_event_id": _TOP_EVENT_ALIAS,
        "top_event": record.description,
        "top_event_evidence": list(top_event_evidence),
        "fta_event_candidates": [
            {
                "cause_id": cause_id,
                "source_cause_index": cause_index,
                "text": record.causes[cause_index],
            }
            for cause_id, cause_index in zip(cause_ids, cause_indices)
        ],
        "cause_disposition_ledger": [
            item.to_payload() for item in cause_dispositions.dispositions
        ],
        "reviewed_locator_decisions": list(reviewed_locator_decisions),
        "attached_extraction_evidence": list(evidence),
        "complete_source_text": source_text,
    }
    return (
        "你负责生成可审计的候选 FTA 事件结构，不得声称已批准、已校准或可生产使用。\n"
        "本阶段只做结构分解，不判断 AND/OR 概率，也不生成因果/关联边。\n"
        "cause_disposition_ledger 是所有抽取原因的完整审计账；每项已明确标出是否可作为候选树事件。"
        "只允许为 fta_event_candidates 中列出的 source_cause_index 建树节点；relation_only 与 exclude_from_tree 只保留在审计账中，"
        "不得映射成树节点；detached_observation 由宿主单独生成为带原文证据的 observation_candidate，"
        "它保持断开，不得纳入 gate_scope 或 relations；unresolved 项已由宿主阻断放行，也不得擅自改成可建树原因。\n"
        "抽取到的 cause 候选只是未确认输入，不因字段名就等于已验证因果。参数值/故障值查表是条件映射，"
        "不证明该状态已在某台设备实例中发生；若文本只是通用 Cause 摘要/故障释义，不要将它拆成顶事件的独立基本原因。\n"
        "自然语言原因边界：若处置账将某索引标为 causal_condition/state，且原文在 Cause/Possible causes 等明确范围内把该命题列为当前故障的可能原因或触发条件，"
        "可生成到顶事件的候选连接；这是待审核的候选边，不是已确认因果，也不要求现场实例读数。"
        "诊断映射边界：由 fault code、fault value、参数/位/索引到解释文本构成的映射，即使解释文字是自然语言，也不得仅凭映射本身生成顶事件节点连接或 causes/may_cause 边；"
        "此类 relation_only 项留在审计账，不映射成树节点。只有映射之外存在独立、直接的原文因果证据，并且对应 cause index 已被处置账允许为候选时，才可建立候选连接。\n"
        "从顶事件及抽取原因出发，保留原文的嵌套作用域。局部组合必须作为父节点的子组，"
        "不得摊平成外层兄弟项；普通因果解释、时间条件或单一复合描述不得自动拆成 AND/OR 条件组。"
        "只有原文支持一组子事件共同构成同一输出事件时，才建立 gate_scope。\n"
        "必须逐条扫描每个原因内部是否还含有独立的布尔组合；发现内层组合时，建立中间事件/组节点和"
        "独立局部 gate_scope，不能只把整句留作一个 cause_candidate。例：原文为‘事件因以下原因之一发生："
        "原因A；原因B；原因C存在 either 状态X or 状态Y’，应有外层 scope（A、B、C组），并另有"
        "C组的局部 scope（X、Y）；X/Y 不得提升为外层同级项。反过来，‘过热 as 压力过高’或"
        "‘故障 because 温度过高’是因果/解释子句，不因连接词就自动建门。\n"
        "分解命题时，必须保留每个命题的肯定/否定极性、条件前件和可能/禁止等情态；不得只抽取名词或参数项、"
        "丢掉原句谓词与否定。不得将\"C or D is not possible\"改写为正向叶节点\"C\"和\"D\"。"
        "若无法保留极性或情态，则保留完整命题并标记 unresolved，不创建误导的子节点、门或关系。"
        "该例只说明极性保留，不表示任何 AND/OR 门型结论。\n"
        "每个节点必须给出精确连续原文引文，并映射到一个或多个 fta_event_candidates.source_cause_index；"
        "一个可建树 cause index 可以映射到原子子项和其组节点；拆分后的兄弟子项应继续引用同一个原始索引。"
        "每个列出的可建树 cause index 至少映射到一个有证据的节点。不能确认某个可建树索引的结构完整时，将该索引列入"
        "unresolved_cause_indices，不能自行补全。此数组只能包含 fta_event_candidates 中列出的索引；"
        "处置账已标为 unresolved、relation_only 或 exclude_from_tree 的索引已由宿主单独记录，不得重复列入或映射成树节点。\n"
        "所有候选节点必须能通过 gate_scope 的 child→output 层级或明确的 causes/may_cause 关系，"
        "沿结构路径到达系统提供的顶事件；associated_with 不是 FTA 连通路径。"
        "多个报警/观察状态在同一段落共现、同时记录、先后出现或被并列列出，只能支持各自作为观察候选，不能单独证明它们导致顶事件，也不能据此把它们接成顶事件的 AND/OR 子节点。"
        "此类节点必须各自保留为有证据的断开候选，不得合并或删除；宿主应阻断整棵候选树并列明断开节点。节点证据不等于节点间关系证据。"
        "若原文不足以支持连接，不得编造关系或删除节点；保留有证据的断开节点，宿主将阻断整棵候选树并列明节点。\n"
        "每个 gate_scope 必须含独立 gate_id、output_node_id、child_node_ids、scope_type、"
        "scope_quote、cause_set_complete、cause_set_leaf_normalized 和 reason。leaf_normalized 表示"
        "该 scope 的直接子项已在本层原子化；允许某个直接子项是另一个嵌套 gate 的组输出。scope_quote 必须是"
        "一个连续原文范围，并包含该 scope 的输出节点及所有直接 child 的完整证据引文。"
        "cause_set_complete 只表示：在该 scope 的原文限定范围内，所有被明示列出的直接子事件是否都已纳入；"
        "它不表示这些事件已在某台具体设备上发生，也不要求现场参数读数。若原文以‘以下条件’、"
        "‘at least one of the following’等封闭枚举引出完整项目，并且 scope_quote 覆盖该枚举的全部子项及结尾，"
        "且每个子项均映射到对应 child，则可据此标记 complete=true；若原文明确表示节选、不完整、"
        "仍有未列项目，或无法确认完整枚举边界，才标记 false。"
        "可以包含一个 child 的顶事件 scope；它不是 AND/OR 门，后续阶段会根据完整性处理为"
        "not_applicable 或 unknown。若局部门有两个及以上 child，必须单独建立对应 scope。\n"
        "如果短引文在原文重复出现且没有对应的 reviewed_locator_decisions，照样给出引文文本；宿主会阻断并交人工定位，不得猜位置。\n"
        "若 payload 提供 reviewed_locator_decisions，它只确认同一来源中应绑定的出现位置，不代表语义审核、专家签署或 Gold。"
        "被审核定位的节点必须使用 selected_extraction_evidence.quote 原文，不得把 review 当作因果或门型证据。\n"
        "严格输出 JSON："
        '{"structure_status":"complete|unresolved",'
        '"nodes":[{"node_id":"local-id",'
        '"node_type":"intermediate_event_candidate|cause_candidate",'
        '"text":"...","source_cause_indices":[0],"evidence_quote":"..."}],'
        '"gate_scopes":[{"gate_id":"local-scope-id",'
        '"output_node_id":"local-id|__top_event__","child_node_ids":["local-id"],'
        '"scope_type":"...","scope_quote":"...",'
        '"cause_set_complete":false,"cause_set_leaf_normalized":false,"reason":"..."}],'
        '"unresolved_cause_indices":[],"reason":"..."}.\n\n'
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def build_candidate_fta_gate_assessment_prompt(
    record: FaultRecord,
    source_text: str,
    nodes: list[dict[str, Any]],
    gate_scopes: list[dict[str, Any]],
) -> str:
    """Ask for gate estimates over a fixed structure without allowing restructuring."""

    payload = {
        "record_id": record.record_id,
        "fault_code": record.fault_code,
        "top_event_id": _TOP_EVENT_ALIAS,
        "top_event": record.description,
        "nodes": nodes,
        "gate_scopes": gate_scopes,
        "complete_source_text": source_text,
    }
    return (
        "你负责对已给定的候选 FTA 结构逐个判断局部门型。结构节点、父子关系、"
        "scope_quote 和原因集合状态已经由前一阶段给出：不得增加、删除、改名或摊平任何节点/scope。\n"
        "每个输入 gate_scope 必须恰好返回一个同 gate_id 的 assessment。只有该 scope 的原文"
        "直接支持、其 child 集合完整且已叶归一化时，才给 AND/OR 较高概率；否则 unknown 应占优。"
        "单 child 且完整、已叶归一化的 scope 不适用布尔门：gate_probabilities 可省略，"
        "gate_evidence_quote 留空。不要从发生概率推导门型；门概率是你对此 scope 门型的估计。\n"
        "门型依据完整命题之间的语义关系判断，不要求原文出现 AND/OR、and/or 或固定连接词。"
        "只有证据表明多个 child 是通向同一个 output 的独立替代路径（每条路径可各自导致该 output）时才判 OR；"
        "只有证据表明这些 child 必须共同成立/共同作用才产生同一 output 时才判 AND。"
        "仅共同出现、同时记录、时间先后或原因列表不能证明 OR/AND；如果不能从原文区分替代关系、共同必要关系或单纯共现，必须判 unknown。\n"
        "gate_evidence_quote 必须是 scope_quote 内直接支持该门型的精确连续原文；若无直接证据，"
        "该证据必须同时支持 child 间的替代/联合关系及其指向同一 output，而非只证明各 child 单独存在；若无此证据，留空并将 unknown 设为最高概率。\n"
        "relations 仅输出原文明示、且未被 gate_scope 的父子结构重复表达的 causes/may_cause/associated_with 有向边，"
        "不得仅因原因列在‘one of the following reasons’或 gate child 中就逐条复制成 causes 边。"
        "通用 Cause 摘要或故障释义不能仅凭 Cause 标题连成顶事件的独立基本原因。"
        "自然语言原因只有在原文 Cause/Possible causes 范围明确将其列为当前故障的可能原因/触发条件时，才允许保留候选结构连接；"
        "诊断映射（fault code/value、参数号、位号或索引到解释文本）本身不构成因果边证据，即使映射后的解释是自然语言，也不得仅凭该映射生成 gate child 或关系边。"
        "只有映射之外另有独立、直接原文证据明确连接相应原因与该故障时，才可补充候选关系；"
        "每条边提供 relation_scope_quote 与直接关系证据，scope_quote 必须同时包含两端节点的完整证据及关系证据。"
        "不能唯一绑定或不能同时覆盖两端节点时，宁可返回空 relations。不能确定方向时不要猜。\n"
        "严格输出 JSON："
        '{"gate_assessments":[{"gate_id":"same-local-scope-id",'
        '"gate_probabilities":{"AND":0.0,"OR":0.0,"unknown":1.0},'
        '"gate_evidence_quote":"...","reason":"..."}],'
        '"relations":[{"source_node_id":"local-id","target_node_id":"local-id|__top_event__",'
        '"relation_type":"causes|may_cause|associated_with",'
        '"relation_scope_quote":"...","evidence_quote":"..."}],'
        '"reason":"..."}.\n\n'
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


class CandidateFtaExtractionService:
    """Generate recursive candidates without persisting or approving them.

    Extraction evidence is retained as input provenance, while each proposed
    FTA node, gate scope and relation is independently rebound to the original
    text. Unlocatable/ambiguous evidence blocks the preview rather than being
    guessed. Unknown gates can remain in a reviewable preview.
    """

    def __init__(
        self,
        model_client: ModelClient,
        confidence_policy: GateConfidencePolicy | None = None,
    ) -> None:
        if not hasattr(model_client, "complete"):
            raise TypeError("model_client must implement complete(prompt)")
        if confidence_policy is not None and not isinstance(
            confidence_policy, GateConfidencePolicy
        ):
            raise TypeError("confidence_policy must be a GateConfidencePolicy or None")
        self._model_client = model_client
        self._cause_disposition_service = CauseDispositionService(model_client)
        self._confidence_policy = confidence_policy

    def propose(
        self,
        extraction: ExtractionResult,
        record_id: str,
        source_text: str,
        locator_reviews: tuple[EvidenceOccurrenceLocatorReview, ...] = (),
    ) -> CandidateFtaTree:
        if not isinstance(extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")
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

        try:
            disposition_batch = self._cause_disposition_service.propose(
                extraction, record.record_id, source_text, locator_reviews
            )
        except CauseDispositionValidationError as exc:
            raise CandidateFtaValidationError(
                f"cause disposition stage failed: {exc}"
            ) from exc
        if (
            disposition_batch.extraction_result_id != extraction.result_id
            or disposition_batch.record_id != record.record_id
            or disposition_batch.source_text_sha256
            != sha256(source_text.encode("utf-8")).hexdigest()
        ):
            raise CauseDispositionValidationError(
                "cause disposition batch does not match this extraction/source"
            )
        cause_dispositions = disposition_batch.dispositions
        eligible_indices = candidate_source_indices(cause_dispositions)
        detached_observation_nodes = self._detached_observation_nodes(
            cause_dispositions, record.record_id
        )

        top_evidence = self._record_evidence(
            extraction.evidence_spans,
            record.record_id,
            EvidenceField.DESCRIPTION,
            None,
            source_text,
            locator_resolver=locator_resolver,
        )
        top_event_id = f"event:{record.record_id}"
        nodes: list[CandidateFtaNode] = [
            CandidateFtaNode(
                node_id=top_event_id,
                node_type="top_event_candidate",
                text=record.description,
                evidence=tuple(top_evidence),
            )
        ]
        blockers: list[str] = []
        if not top_evidence:
            blockers.append("top_event_evidence_unavailable")
        elif any(
            self._bind_target_quote(
                item.quote,
                EvidenceLocatorTargetField.DESCRIPTION,
                None,
                source_text,
                locator_resolver,
            )
            is None
            for item in top_evidence
        ):
            blockers.append("top_event_evidence_ambiguous")
        if extraction.status is not ExtractionStatus.SUCCESS:
            blockers.append(f"extraction_status_not_complete:{extraction.status.value}")
        if not record.causes:
            blockers.append("extracted_cause_set_empty")
        blockers.extend(
            f"cause_disposition_unresolved:{item.source_cause_index}"
            for item in cause_dispositions
            if item.disposition is FtaCauseDispositionKind.UNRESOLVED
        )

        if not eligible_indices:
            if record.causes:
                blockers.append("no_fta_event_candidates")
            nodes.extend(detached_observation_nodes)
            blockers.extend(
                f"node_disconnected_from_top_event:{node_id}"
                for node_id in find_disconnected_candidate_node_ids(
                    top_event_id, nodes, (), ()
                )
            )
            return CandidateFtaTree(
                extraction_result_id=extraction.result_id,
                record_id=record.record_id,
                fault_code=record.fault_code,
                source_text_sha256=sha256(source_text.encode("utf-8")).hexdigest(),
                top_event_id=top_event_id,
                nodes=tuple(nodes),
                cause_dispositions=cause_dispositions,
                locator_reviews=locator_reviews,
                status=CandidateFtaStatus.BLOCKED,
                blockers=normalize_blockers(blockers),
                decision_reason=(
                    "No source cause was admitted as a candidate tree event; "
                    "detached observations remain separately evidenced and disconnected."
                ),
                reviewer_provenance="user_authorized_ai_expert_role",
            )

        cause_ids = tuple(f"cause:{record.record_id}:{index}" for index in eligible_indices)
        attached_evidence = tuple(
            {
                "cause_id": cause_id,
                "cause_index": cause_index,
                "evidence": [
                    self._evidence_payload(item)
                    for item in self._record_evidence(
                        extraction.evidence_spans,
                        record.record_id,
                        EvidenceField.CAUSE,
                        cause_index,
                        source_text,
                        locator_resolver=locator_resolver,
                    )
                ],
            }
            for cause_index, cause_id in zip(eligible_indices, cause_ids)
        )
        structure_raw = self._model_client.complete(
            build_candidate_fta_structure_prompt(
                record,
                source_text,
                cause_ids,
                eligible_indices,
                disposition_batch,
                attached_evidence,
                tuple(self._evidence_payload(item) for item in top_evidence),
                tuple(locator_resolver.prompt_payload()),
            )
        )
        structure_payload = self._parse_payload(structure_raw)
        structure_status = structure_payload.get("structure_status")
        if not isinstance(structure_status, str) or structure_status not in {
            "complete",
            "unresolved",
        }:
            raise CandidateFtaValidationError(
                "structure_status must be complete or unresolved"
            )
        unresolved_indices = structure_payload.get("unresolved_cause_indices")
        if not isinstance(unresolved_indices, list) or any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index not in eligible_indices
            for index in unresolved_indices
        ):
            raise CandidateFtaValidationError(
                "unresolved_cause_indices must contain known cause indexes"
            )
        if len(set(unresolved_indices)) != len(unresolved_indices):
            raise CandidateFtaValidationError(
                "unresolved_cause_indices must not contain duplicates"
            )
        if structure_status == "complete" and unresolved_indices:
            raise CandidateFtaValidationError(
                "complete structure cannot contain unresolved cause indexes"
            )
        if structure_status == "unresolved" and not unresolved_indices:
            blockers.append("cause_structure_unresolved")
        blockers.extend(
            f"cause_structure_unresolved:{index}"
            for index in unresolved_indices
        )

        proposed_nodes, local_to_global, node_blockers = self._parse_nodes(
            structure_payload.get("nodes"),
            record,
            source_text,
            len(record.causes),
            locator_resolver,
        )
        nodes.extend(proposed_nodes)
        blockers.extend(node_blockers)

        mapped_causes = {
            cause_index
            for node in proposed_nodes
            for cause_index in node.source_cause_indices
        }
        if mapped_causes != set(eligible_indices):
            blockers.append("source_cause_mapping_incomplete")
        blockers.extend(
            f"cause_disposition_conflict:{index}"
            for index in mapped_causes - set(eligible_indices)
        )

        structural_scopes = structure_payload.get("gate_scopes")
        self._validate_structure_scopes(structural_scopes, local_to_global)
        assessment_raw = self._model_client.complete(
            build_candidate_fta_gate_assessment_prompt(
                record,
                source_text,
                list(structure_payload.get("nodes", [])),
                list(structural_scopes) if isinstance(structural_scopes, list) else [],
            )
        )
        assessment_payload = self._parse_payload(assessment_raw)
        gate_payload = self._merge_gate_assessments(
            structural_scopes,
            assessment_payload.get("gate_assessments"),
        )
        gate_assessments, gate_blockers = self._parse_gates(
            gate_payload,
            record,
            source_text,
            nodes,
            local_to_global,
            top_event_id,
        )
        blockers.extend(gate_blockers)
        relations, relation_blockers = self._parse_relations(
            assessment_payload.get("relations"),
            record,
            source_text,
            local_to_global,
            nodes,
        )
        blockers.extend(relation_blockers)
        nodes.extend(detached_observation_nodes)
        blockers.extend(
            f"node_disconnected_from_top_event:{node_id}"
            for node_id in find_disconnected_candidate_node_ids(
                top_event_id,
                nodes,
                gate_assessments,
                relations,
            )
        )

        structure_reason = structure_payload.get("reason", "")
        assessment_reason = assessment_payload.get("reason", "")
        if not isinstance(structure_reason, str) or not isinstance(
            assessment_reason, str
        ):
            raise CandidateFtaValidationError("stage reasons must be strings")
        reason = "; ".join(
            reason.strip()
            for reason in (structure_reason, assessment_reason)
            if reason.strip()
        )
        if not gate_assessments:
            blockers.append("gate_assessments_unavailable")
        status = (
            CandidateFtaStatus.BLOCKED
            if blockers
            else CandidateFtaStatus.CANDIDATE_READY_FOR_REVIEW
        )
        try:
            return CandidateFtaTree(
                extraction_result_id=extraction.result_id,
                record_id=record.record_id,
                fault_code=record.fault_code,
                source_text_sha256=sha256(source_text.encode("utf-8")).hexdigest(),
                top_event_id=top_event_id,
                nodes=tuple(nodes),
                gate_assessments=tuple(gate_assessments),
                relations=tuple(relations),
                cause_dispositions=cause_dispositions,
                locator_reviews=locator_reviews,
                status=status,
                blockers=normalize_blockers(blockers),
                decision_reason=reason.strip(),
                reviewer_provenance="user_authorized_ai_expert_role",
            )
        except (TypeError, ValueError) as exc:
            raise CandidateFtaValidationError(
                f"recursive candidate graph violates its contract: {exc}"
            ) from exc

    @staticmethod
    def _detached_observation_nodes(
        dispositions: tuple[CauseDisposition, ...], record_id: str
    ) -> list[CandidateFtaNode]:
        nodes: list[CandidateFtaNode] = []
        for item in dispositions:
            if item.disposition is not FtaCauseDispositionKind.DETACHED_OBSERVATION:
                continue
            evidence = tuple(
                CandidateFtaEvidence(
                    citation_id=span.citation_id,
                    source_id=span.source_id,
                    quote=span.quote,
                    start=span.start,
                    end=span.end,
                )
                for span in item.evidence
            )
            nodes.append(
                CandidateFtaNode(
                    node_id=f"observation:{record_id}:{item.source_cause_index}",
                    node_type="observation_candidate",
                    text=item.source_cause_text,
                    evidence=evidence,
                    source_cause_indices=(item.source_cause_index,),
                )
            )
        return nodes

    @staticmethod
    def _parse_payload(raw: str) -> dict[str, Any]:
        try:
            payload = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise CandidateFtaValidationError("model response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise CandidateFtaValidationError("model response must be a JSON object")
        return payload

    @staticmethod
    def _validate_structure_scopes(
        structural_scopes: Any,
        local_to_global: dict[str, str],
    ) -> None:
        if not isinstance(structural_scopes, list) or not structural_scopes:
            raise CandidateFtaValidationError(
                "gate_scopes must be a non-empty JSON list"
            )
        seen_gate_ids: set[str] = set()
        for scope in structural_scopes:
            if not isinstance(scope, dict):
                raise CandidateFtaValidationError(
                    "each gate scope must be a JSON object"
                )
            gate_id = scope.get("gate_id")
            output_id = scope.get("output_node_id")
            child_ids = scope.get("child_node_ids")
            scope_type = scope.get("scope_type")
            quote = scope.get("scope_quote")
            if not isinstance(gate_id, str) or not gate_id.strip():
                raise CandidateFtaValidationError(
                    "gate scope gate_id must be non-empty"
                )
            if gate_id in seen_gate_ids:
                raise CandidateFtaValidationError("gate scope IDs must be unique")
            seen_gate_ids.add(gate_id)
            if not isinstance(output_id, str) or output_id not in local_to_global:
                raise CandidateFtaValidationError(
                    "gate scope output references an unknown node"
                )
            if not isinstance(child_ids, list) or not child_ids or any(
                not isinstance(child_id, str) or child_id not in local_to_global
                for child_id in child_ids
            ):
                raise CandidateFtaValidationError(
                    "gate scope children must reference known nodes"
                )
            if output_id in child_ids or len(set(child_ids)) != len(child_ids):
                raise CandidateFtaValidationError(
                    "gate scope contains self/duplicate children"
                )
            if not isinstance(scope_type, str) or not scope_type.strip():
                raise CandidateFtaValidationError(
                    "gate scope scope_type must be non-empty"
                )
            if not isinstance(quote, str) or not quote.strip():
                raise CandidateFtaValidationError(
                    "gate scope scope_quote must be non-empty"
                )
            if not isinstance(scope.get("cause_set_complete"), bool) or not isinstance(
                scope.get("cause_set_leaf_normalized"), bool
            ):
                raise CandidateFtaValidationError(
                    "gate scope cause-set flags must be booleans"
                )

    @staticmethod
    def _merge_gate_assessments(
        structural_scopes: Any,
        assessments: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(structural_scopes, list) or not structural_scopes:
            raise CandidateFtaValidationError("gate_scopes must be a non-empty JSON list")
        if not isinstance(assessments, list):
            raise CandidateFtaValidationError("gate_assessments must be a JSON list")

        scopes_by_id: dict[str, dict[str, Any]] = {}
        for scope in structural_scopes:
            if not isinstance(scope, dict):
                raise CandidateFtaValidationError("each gate scope must be a JSON object")
            gate_id = scope.get("gate_id")
            if not isinstance(gate_id, str) or not gate_id.strip():
                raise CandidateFtaValidationError("gate scope gate_id must be non-empty")
            if gate_id in scopes_by_id:
                raise CandidateFtaValidationError("gate scope IDs must be unique")
            scopes_by_id[gate_id] = scope

        assessments_by_id: dict[str, dict[str, Any]] = {}
        for assessment in assessments:
            if not isinstance(assessment, dict):
                raise CandidateFtaValidationError(
                    "each gate assessment must be a JSON object"
                )
            gate_id = assessment.get("gate_id")
            if not isinstance(gate_id, str) or not gate_id.strip():
                raise CandidateFtaValidationError(
                    "gate assessment gate_id must be non-empty"
                )
            if gate_id in assessments_by_id:
                raise CandidateFtaValidationError("gate assessment IDs must be unique")
            assessments_by_id[gate_id] = assessment

        if scopes_by_id.keys() != assessments_by_id.keys():
            missing = sorted(scopes_by_id.keys() - assessments_by_id.keys())
            extra = sorted(assessments_by_id.keys() - scopes_by_id.keys())
            raise CandidateFtaValidationError(
                f"gate assessment scopes do not match structure (missing={missing}, extra={extra})"
            )

        merged: list[dict[str, Any]] = []
        for gate_id, scope in scopes_by_id.items():
            assessment = assessments_by_id[gate_id]
            probabilities = assessment.get("gate_probabilities")
            gate_evidence_quote = assessment.get("gate_evidence_quote", "")
            reason = assessment.get("reason", "")
            if not isinstance(gate_evidence_quote, str) or not isinstance(reason, str):
                raise CandidateFtaValidationError(
                    "gate assessment evidence and reason must be strings"
                )
            item = dict(scope)
            item["gate_probabilities"] = probabilities
            item["gate_evidence_quote"] = gate_evidence_quote
            item["reason"] = reason
            merged.append(item)
        return merged

    def _parse_nodes(
        self,
        value: Any,
        record: FaultRecord,
        source_text: str,
        cause_count: int,
        locator_resolver: EvidenceLocatorReviewResolver,
    ) -> tuple[list[CandidateFtaNode], dict[str, str], list[str]]:
        if not isinstance(value, list):
            raise CandidateFtaValidationError("nodes must be a JSON list")
        nodes: list[CandidateFtaNode] = []
        local_to_global: dict[str, str] = {_TOP_EVENT_ALIAS: f"event:{record.record_id}"}
        blockers: list[str] = []
        raw_nodes: list[tuple[dict[str, Any], str]] = []
        for item in value:
            if not isinstance(item, dict):
                raise CandidateFtaValidationError("each node must be a JSON object")
            local_id = item.get("node_id")
            node_type = item.get("node_type")
            text = item.get("text")
            if not isinstance(local_id, str) or not local_id.strip() or local_id == _TOP_EVENT_ALIAS:
                raise CandidateFtaValidationError("node_id must be a non-empty local ID")
            if local_id in local_to_global:
                raise CandidateFtaValidationError("node_id values must be unique")
            if node_type not in {"intermediate_event_candidate", "cause_candidate"}:
                raise CandidateFtaValidationError("unsupported proposed node_type")
            if not isinstance(text, str) or not text.strip():
                raise CandidateFtaValidationError("node text must be non-empty")
            cause_indices = item.get("source_cause_indices")
            if not isinstance(cause_indices, list) or not cause_indices:
                raise CandidateFtaValidationError("source_cause_indices must be a non-empty list")
            if any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or not 0 <= index < cause_count
                for index in cause_indices
            ):
                raise CandidateFtaValidationError("source_cause_indices reference an unknown cause")
            if len(set(cause_indices)) != len(cause_indices):
                raise CandidateFtaValidationError("source_cause_indices must not contain duplicates")
            global_id = f"{node_type.removesuffix('_candidate')}:{record.record_id}:{local_id}"
            local_to_global[local_id] = global_id
            raw_nodes.append((item, global_id))

        for item, global_id in raw_nodes:
            quote = item.get("evidence_quote")
            evidence: tuple[CandidateFtaEvidence, ...] = ()
            if not isinstance(quote, str):
                raise CandidateFtaValidationError("node evidence_quote must be a string")
            reviewed_indices = [
                index
                for index in item["source_cause_indices"]
                if locator_resolver.review_for(
                    EvidenceLocatorTargetField.CAUSE, index
                )
                is not None
            ]
            if len(reviewed_indices) == 1:
                bound = self._bind_target_quote(
                    quote,
                    EvidenceLocatorTargetField.CAUSE,
                    reviewed_indices[0],
                    source_text,
                    locator_resolver,
                )
            elif reviewed_indices:
                bound = None
            else:
                bound = self._bind_unique_quote(quote, source_text)
            if bound is None:
                blockers.append(f"node_evidence_missing_or_ambiguous:{item['node_id']}")
            else:
                start, end = bound
                evidence = (
                    CandidateFtaEvidence(
                        citation_id=f"input_text:node:{start}-{end}",
                        source_id="input_text",
                        quote=quote,
                        start=start,
                        end=end,
                    ),
                )
            nodes.append(
                CandidateFtaNode(
                    node_id=global_id,
                    node_type=item["node_type"],
                    text=item["text"].strip(),
                    evidence=evidence,
                    source_cause_indices=tuple(item["source_cause_indices"]),
                )
            )
        return nodes, local_to_global, blockers

    def _parse_gates(
        self,
        value: Any,
        record: FaultRecord,
        source_text: str,
        nodes: list[CandidateFtaNode],
        local_to_global: dict[str, str],
        top_event_id: str,
    ) -> tuple[list[CandidateFtaGateAssessment], list[str]]:
        if not isinstance(value, list):
            raise CandidateFtaValidationError("gate_assessments must be a JSON list")
        node_by_id = {node.node_id: node for node in nodes}
        gates: list[CandidateFtaGateAssessment] = []
        blockers: list[str] = []
        seen_gate_ids: set[str] = set()
        for item in value:
            if not isinstance(item, dict):
                raise CandidateFtaValidationError("each gate assessment must be a JSON object")
            local_gate_id = item.get("gate_id")
            local_output_id = item.get("output_node_id")
            local_children = item.get("child_node_ids")
            scope_type = item.get("scope_type")
            if not isinstance(local_gate_id, str) or not local_gate_id.strip():
                raise CandidateFtaValidationError("gate_id must be a non-empty local ID")
            if local_gate_id in seen_gate_ids:
                raise CandidateFtaValidationError("gate_id values must be unique")
            seen_gate_ids.add(local_gate_id)
            if local_output_id not in local_to_global:
                raise CandidateFtaValidationError("gate output references an unknown node")
            if not isinstance(local_children, list) or not local_children or not all(
                isinstance(child, str) and child in local_to_global for child in local_children
            ):
                raise CandidateFtaValidationError("gate child_node_ids reference unknown nodes")
            output_id = local_to_global[local_output_id]
            child_ids = tuple(local_to_global[child] for child in local_children)
            if output_id in child_ids or len(set(child_ids)) != len(child_ids):
                raise CandidateFtaValidationError("gate graph contains self/duplicate children")
            if not isinstance(scope_type, str) or not scope_type.strip():
                raise CandidateFtaValidationError("scope_type must be a non-empty string")
            scope_quote = item.get("scope_quote")
            gate_quote = item.get("gate_evidence_quote", "")
            if not isinstance(scope_quote, str) or not isinstance(gate_quote, str):
                raise CandidateFtaValidationError("scope and gate evidence quotes must be strings")
            scope_bound = self._bind_unique_quote(scope_quote, source_text)
            if scope_bound is None:
                blockers.append(f"gate_scope_missing_or_ambiguous:{local_gate_id}")
                continue
            scope_start, scope_end = scope_bound
            child_evidence = [
                evidence
                for child_id in child_ids
                for evidence in node_by_id[child_id].evidence
            ]
            output_evidence = list(node_by_id[output_id].evidence)
            contained_evidence = child_evidence + output_evidence
            gate_blockers: list[str] = []
            if not contained_evidence or any(
                evidence.start < scope_start or evidence.end > scope_end
                for evidence in contained_evidence
            ):
                gate_blockers.append("gate_scope_does_not_contain_all_node_evidence")
                blockers.append(f"gate_scope_does_not_contain_all_node_evidence:{local_gate_id}")

            scope_evidence = (
                CandidateFtaEvidence(
                    citation_id=f"input_text:scope:{scope_start}-{scope_end}",
                    source_id="input_text",
                    quote=scope_quote,
                    start=scope_start,
                    end=scope_end,
                ),
            )
            gate_evidence: tuple[CandidateFtaEvidence, ...] = ()
            decision_reason = item.get("reason", "")
            if not isinstance(decision_reason, str):
                raise CandidateFtaValidationError("gate reason must be a string")
            complete = item.get("cause_set_complete")
            normalized = item.get("cause_set_leaf_normalized")
            if not isinstance(complete, bool) or not isinstance(normalized, bool):
                raise CandidateFtaValidationError("gate cause-set flags must be booleans")

            no_gate_applies = len(child_ids) == 1 and complete and normalized
            probabilities = (
                {}
                if no_gate_applies
                else CandidateFtaExtractionService._validate_probabilities(
                    item.get("gate_probabilities")
                )
            )
            if no_gate_applies:
                chosen_gate = "not_applicable"
                confidence_reason = "single_complete_child_scope_has_no_boolean_gate"
            else:
                chosen_gate, confidence_reason = self._select_gate(probabilities)
                if len(child_ids) < 2:
                    chosen_gate = "unknown"
                    gate_blockers.append("gate_requires_multiple_children")
                if not complete or not normalized:
                    chosen_gate = "unknown"
                    gate_blockers.append("cause_set_incomplete_or_not_leaf_normalized")
            retain_gate_evidence = chosen_gate in {"AND", "OR"} or (
                chosen_gate == "unknown" and bool(gate_quote.strip())
            )
            if retain_gate_evidence:
                gate_bound = self._bind_unique_quote(gate_quote, source_text)
                if gate_bound is None:
                    gate_blockers.append("gate_evidence_missing_or_ambiguous")
                    if chosen_gate in {"AND", "OR"}:
                        chosen_gate = "unknown"
                else:
                    gate_start, gate_end = gate_bound
                    if gate_start < scope_start or gate_end > scope_end:
                        gate_blockers.append("gate_evidence_outside_scope")
                        blockers.append(f"gate_evidence_outside_scope:{local_gate_id}")
                        if chosen_gate in {"AND", "OR"}:
                            chosen_gate = "unknown"
                    elif any(
                        evidence.start < scope_start or evidence.end > scope_end
                        for evidence in child_evidence
                    ):
                        gate_blockers.append("gate_children_outside_scope")
                        if chosen_gate in {"AND", "OR"}:
                            chosen_gate = "unknown"
                    else:
                        gate_evidence = (
                            CandidateFtaEvidence(
                                citation_id=f"input_text:gate:{gate_start}-{gate_end}",
                                source_id="input_text",
                                quote=gate_quote,
                                start=gate_start,
                                end=gate_end,
                            ),
                        )
            if (
                chosen_gate == "unknown"
                and confidence_reason != "gate_confidence_policy_accepted"
            ):
                gate_blockers.append(confidence_reason)

            unknown_reason_code = (
                resolve_unknown_gate_reason(
                    blockers=gate_blockers,
                    confidence_reason=confidence_reason,
                    gate_quote_present=bool(gate_quote.strip()),
                    gate_evidence_bound=bool(gate_evidence),
                    child_count=len(child_ids),
                    cause_set_complete=complete,
                    cause_set_leaf_normalized=normalized,
                )
                if chosen_gate == "unknown"
                else None
            )

            stable_gate_id = self._stable_gate_id(
                record.fault_code or record.description,
                sha256(source_text.encode("utf-8")).hexdigest(),
                scope_type.strip(),
                scope_start,
                scope_end,
            )
            if stable_gate_id in seen_gate_ids:
                raise CandidateFtaValidationError(
                    "multiple gate proposals resolve to the same stable source scope"
                )
            seen_gate_ids.add(stable_gate_id)
            decision_reason_parts = [confidence_reason]
            if len(child_ids) < 2 and not no_gate_applies:
                decision_reason_parts.append("gate_requires_multiple_children")
            if chosen_gate == "unknown" and not no_gate_applies:
                decision_reason_parts.append("model gate proposal is not accepted")
            if decision_reason.strip():
                decision_reason_parts.append(
                    f"model rationale: {decision_reason.strip()}"
                    if chosen_gate == "unknown"
                    else decision_reason.strip()
                )
            gates.append(
                CandidateFtaGateAssessment(
                    gate_node_id=stable_gate_id,
                    output_node_id=output_id,
                    child_node_ids=child_ids,
                    scope_type=scope_type.strip(),
                    gate=chosen_gate,
                    gate_probabilities=tuple(probabilities.items()),
                    scope_evidence=scope_evidence,
                    gate_evidence=gate_evidence,
                    cause_set_complete=complete,
                    cause_set_leaf_normalized=normalized,
                    confidence_policy_id=(
                        self._confidence_policy.policy_id
                        if self._confidence_policy is not None and not no_gate_applies
                        else None
                    ),
                    confidence_policy_basis=(
                        self._confidence_policy.basis
                        if self._confidence_policy is not None and not no_gate_applies
                        else None
                    ),
                    minimum_gate_probability=(
                        self._confidence_policy.minimum_probability
                        if self._confidence_policy is not None and not no_gate_applies
                        else None
                    ),
                    minimum_gate_margin=(
                        self._confidence_policy.minimum_margin
                        if self._confidence_policy is not None and not no_gate_applies
                        else None
                    ),
                    decision_reason="; ".join(decision_reason_parts),
                    unknown_reason_code=unknown_reason_code,
                    blockers=normalize_blockers(gate_blockers),
                )
            )

        # Ensure the system-owned top event participates as an explicit node.
        if top_event_id not in node_by_id:
            blockers.append("top_event_node_unavailable")
        return gates, blockers

    def _parse_relations(
        self,
        value: Any,
        record: FaultRecord,
        source_text: str,
        local_to_global: dict[str, str],
        nodes: list[CandidateFtaNode],
    ) -> tuple[list[CandidateFtaRelation], list[str]]:
        if not isinstance(value, list):
            raise CandidateFtaValidationError("relations must be a JSON list")
        relations: list[CandidateFtaRelation] = []
        blockers: list[str] = []
        seen_pairs: set[tuple[str, str, str]] = set()
        node_by_id = {node.node_id: node for node in nodes}
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                raise CandidateFtaValidationError("each relation must be a JSON object")
            local_source = item.get("source_node_id")
            local_target = item.get("target_node_id")
            relation_type = item.get("relation_type")
            quote = item.get("evidence_quote")
            scope_quote = item.get("relation_scope_quote")
            if local_source not in local_to_global or local_target not in local_to_global:
                raise CandidateFtaValidationError("relation references an unknown node")
            if not isinstance(relation_type, str) or not isinstance(quote, str):
                raise CandidateFtaValidationError("relation type and evidence quote must be strings")
            if not isinstance(scope_quote, str):
                raise CandidateFtaValidationError("relation_scope_quote must be a string")
            if relation_type not in {"causes", "may_cause", "associated_with"}:
                raise CandidateFtaValidationError("unsupported candidate relation_type")
            source_id = local_to_global[local_source]
            target_id = local_to_global[local_target]
            pair = (source_id, target_id, relation_type)
            if pair in seen_pairs:
                raise CandidateFtaValidationError("duplicate candidate relation")
            seen_pairs.add(pair)
            scope_bound = self._bind_unique_quote(scope_quote, source_text)
            if scope_bound is None:
                blockers.append(f"relation_scope_missing_or_ambiguous:{index}")
                continue
            scope_start, scope_end = scope_bound
            endpoint_evidence = (
                *node_by_id[source_id].evidence,
                *node_by_id[target_id].evidence,
            )
            if not endpoint_evidence or any(
                evidence.start < scope_start or evidence.end > scope_end
                for evidence in endpoint_evidence
            ):
                blockers.append(f"relation_scope_does_not_contain_endpoints:{index}")
            bound = self._bind_unique_quote(quote, source_text)
            if bound is None:
                blockers.append(f"relation_evidence_missing_or_ambiguous:{index}")
                continue
            start, end = bound
            if start < scope_start or end > scope_end:
                blockers.append(f"relation_evidence_outside_scope:{index}")
                continue
            relations.append(
                CandidateFtaRelation(
                    relation_id=f"relation:{record.record_id}:{index}",
                    source_node_id=source_id,
                    target_node_id=target_id,
                    relation_type=relation_type,
                    scope_evidence=(
                        CandidateFtaEvidence(
                            citation_id=f"input_text:relation_scope:{scope_start}-{scope_end}",
                            source_id="input_text",
                            quote=scope_quote,
                            start=scope_start,
                            end=scope_end,
                        ),
                    ),
                    evidence=(
                        CandidateFtaEvidence(
                            citation_id=f"input_text:relation:{start}-{end}",
                            source_id="input_text",
                            quote=quote,
                            start=start,
                            end=end,
                        ),
                    ),
                )
            )
        return relations, blockers

    @staticmethod
    def _stable_gate_id(
        fault_identity: str,
        source_text_sha256: str,
        scope_type: str,
        scope_start: int,
        scope_end: int,
    ) -> str:
        identity = (
            f"{fault_identity}|{source_text_sha256}|{scope_type}|"
            f"{scope_start}|{scope_end}"
        )
        return f"gate:{sha256(identity.encode('utf-8')).hexdigest()[:24]}"

    @staticmethod
    def _record_evidence(
        spans: tuple[EvidenceSpan, ...],
        record_id: str,
        field: EvidenceField,
        value_index: int | None,
        source_text: str,
        *,
        locator_resolver: EvidenceLocatorReviewResolver | None = None,
    ) -> list[CandidateFtaEvidence]:
        matches = [
            span
            for span in spans
            if span.record_id == record_id
            and span.field is field
            and span.value_index == value_index
        ]
        valid = [span for span in matches if span.matches(source_text)]
        if locator_resolver is not None and field in {
            EvidenceField.DESCRIPTION,
            EvidenceField.CAUSE,
        }:
            target_field = EvidenceLocatorTargetField(field.value)
            reviewed_span = locator_resolver.selected_span(target_field, value_index)
            if reviewed_span is not None:
                return [CandidateFtaExtractionService._span_payload(reviewed_span)]
        if field is EvidenceField.CAUSE and (len(matches) != 1 or len(valid) != 1):
            return []
        return [CandidateFtaExtractionService._span_payload(span) for span in valid]

    @staticmethod
    def _bind_target_quote(
        quote: str,
        target_field: EvidenceLocatorTargetField,
        value_index: int | None,
        source_text: str,
        locator_resolver: EvidenceLocatorReviewResolver,
    ) -> tuple[int, int] | None:
        if locator_resolver.review_for(target_field, value_index) is not None:
            return locator_resolver.bind_model_quote(
                quote, target_field, value_index
            )
        return CandidateFtaExtractionService._bind_unique_quote(quote, source_text)

    @staticmethod
    def _span_payload(span: EvidenceSpan) -> CandidateFtaEvidence:
        return CandidateFtaEvidence(
            citation_id=f"{span.record_id}:{span.field.value}:{span.start}-{span.end}",
            source_id=span.source_id,
            quote=span.quote,
            start=span.start,
            end=span.end,
        )

    @staticmethod
    def _evidence_payload(evidence: CandidateFtaEvidence) -> dict[str, object]:
        return {
            "citation_id": evidence.citation_id,
            "source_id": evidence.source_id,
            "quote": evidence.quote,
            "start": evidence.start,
            "end": evidence.end,
        }

    @staticmethod
    def _validate_probabilities(value: Any) -> dict[str, float]:
        if not isinstance(value, dict) or set(value) != set(_GATES):
            raise CandidateFtaValidationError(
                "gate_probabilities must contain exactly AND, OR, and unknown"
            )
        probabilities: dict[str, float] = {}
        for gate in _GATES:
            raw_probability = value[gate]
            if isinstance(raw_probability, bool) or not isinstance(raw_probability, (int, float)):
                raise CandidateFtaValidationError("gate probabilities must be numeric")
            probability = float(raw_probability)
            if not 0.0 <= probability <= 1.0:
                raise CandidateFtaValidationError("gate probabilities must be in [0, 1]")
            probabilities[gate] = probability
        if abs(sum(probabilities.values()) - 1.0) > 0.02:
            raise CandidateFtaValidationError("gate probabilities must sum to 1.0")
        return probabilities

    def _select_gate(self, probabilities: dict[str, float]) -> tuple[str, str]:
        if self._confidence_policy is None:
            return "unknown", "gate_confidence_policy_unavailable"
        return self._confidence_policy.decide(probabilities)

    @staticmethod
    def _bind_unique_quote(quote: str, source_text: str) -> tuple[int, int] | None:
        """Bind only globally unique exact quotes; repeated text needs human location."""
        if not quote or not quote.strip():
            return None
        first = source_text.find(quote)
        if first < 0 or source_text.find(quote, first + 1) >= 0:
            return None
        return first, first + len(quote)


__all__ = [
    "CandidateFtaExtractionService",
    "CandidateFtaValidationError",
    "build_candidate_fta_prompt",
]
