"""Regenerate the five expert-flagged answers without rerunning retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from config import (  # noqa: E402
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
    S210_GOLD_PATH,
)
from fault_relation_expansion import FaultRelationRegistry  # noqa: E402
from openai_model_client import OpenAICompatibleModelClient  # noqa: E402
from rag_service import (  # noqa: E402
    EvidenceBoundPromptBuilder,
    GoldFaultContextStore,
    PromptAnswerGenerator,
    rag_response_to_dict,
)
from rag_contract import RagResponse, RetrievedFault  # noqa: E402


TARGET_QUERY_IDS = ("RAG-021", "RAG-027", "RAG-028", "RAG-029", "RAG-030")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _candidate_codes(response: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for item in response.get("retrieved", []):
        if not isinstance(item, dict):
            continue
        code = str(item.get("fault_code") or "").strip().upper()
        if code and code not in result:
            result.append(code)
    return result


def run_targeted(
    source_responses: dict[str, Any],
    dataset: dict[str, Any],
    gold_path: str | Path,
    relation_path: str | Path,
) -> dict[str, Any]:
    questions = {
        str(item.get("query_id")): str(item.get("question") or "")
        for item in dataset.get("queries", [])
        if isinstance(item, dict)
    }
    source_by_id = {
        str(item.get("query_id")): item
        for item in source_responses.get("responses", [])
        if isinstance(item, dict)
    }
    if any(query_id not in source_by_id for query_id in TARGET_QUERY_IDS):
        raise ValueError("source responses do not contain all five target queries")

    store = GoldFaultContextStore(gold_path)
    registry = FaultRelationRegistry.from_path(relation_path)
    generator = PromptAnswerGenerator(
        OpenAICompatibleModelClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            timeout_seconds=OPENAI_TIMEOUT_SECONDS,
            base_url=OPENAI_API_BASE or None,
        ),
        model_name=OPENAI_MODEL,
        prompt_builder=EvidenceBoundPromptBuilder(),
    )

    results: list[dict[str, Any]] = []
    for query_id in TARGET_QUERY_IDS:
        source = source_by_id[query_id]
        question = questions[query_id] or str(source.get("question") or "")
        codes = _candidate_codes(source)
        candidates = tuple(
            RetrievedFault(
                fault_code=str(item.get("fault_code") or "").strip().upper(),
                score=item.get("score"),
                rank=item.get("rank"),
                signals=item.get("signals") or {},
            )
            for item in source.get("retrieved", [])
            if isinstance(item, dict) and str(item.get("fault_code") or "").strip()
        )
        candidate_contexts = tuple(store.load(codes))
        primary_code = candidate_contexts[0].fault_code
        related_codes = registry.triggered_related_codes(question, primary_code)
        related_contexts = tuple(store.load(related_codes)) if related_codes else ()
        all_contexts = list(candidate_contexts)
        loaded = {context.fault_code for context in all_contexts}
        for context in related_contexts:
            if context.fault_code not in loaded:
                all_contexts.append(context)
                loaded.add(context.fault_code)
        relations = registry.expand(question, primary_code, tuple(all_contexts))
        primary = replace(candidate_contexts[0], relations=relations)
        generation_contexts = (primary,)
        generation_contexts += tuple(
            context for context in related_contexts if context.fault_code != primary_code
        )
        generated = generator.generate(question, generation_contexts)
        results.append(
            {
                "query_id": query_id,
                "http_status": 200,
                "question": question,
                "answer": {
                    "text": generated.text,
                    "citations": list(generated.citations),
                    "model": generated.model,
                },
                "retrieved": [
                    {
                        "fault_code": candidate.fault_code,
                        "score": candidate.score,
                        "rank": candidate.rank,
                        "signals": dict(candidate.signals),
                    }
                    for candidate in candidates
                ],
                "contexts": [
                    {
                        "fault_code": context.fault_code,
                        "description": context.description,
                        "component": context.component,
                        "related_components": list(context.related_components),
                        "causes": list(context.causes),
                        "parameters": list(context.parameters),
                        "alarm_value": context.alarm_value,
                        "remedy": context.remedy,
                        "evidence": [
                            {
                                "citation_id": evidence.citation_id,
                                "field": evidence.field,
                                "quote": evidence.quote,
                                "source_id": evidence.source_id,
                                "source_file": evidence.source_file,
                                "start": evidence.start,
                                "end": evidence.end,
                            }
                            for evidence in context.evidence
                        ],
                        "source_file": context.source_file,
                    }
                    for context in all_contexts
                ],
                "relations": [
                    {
                        "relation_id": relation.relation_id,
                        "primary_fault_code": relation.primary_fault_code,
                        "related_fault_code": relation.related_fault_code,
                        "relation_type": relation.relation_type,
                        "relation_note": relation.relation_note,
                        "review_status": relation.review_status,
                        "evidence": [
                            {
                                "fault_code": evidence.fault_code,
                                "citation_id": evidence.citation_id,
                                "field": evidence.field,
                                "quote": evidence.quote,
                            }
                            for evidence in relation.evidence
                        ],
                    }
                    for relation in relations
                ],
                "retrieval_reused_from": "siemens_s210_rag_semantic_responses_v1_2026-09-21",
                "pipeline_change": "relation_expansion_only; retrieval/reranker/router unchanged",
                "evidence_status": "cited",
            }
        )
    return {
        "run_type": "s210_fault_relation_targeted_regression_v1",
        "created_at": "2026-09-21",
        "status": "ready_for_expert_targeted_rereview",
        "query_ids": list(TARGET_QUERY_IDS),
        "responses": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-responses", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--gold", default=S210_GOLD_PATH)
    parser.add_argument("--relations", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_targeted(
        load_json(args.source_responses),
        load_json(args.dataset),
        args.gold,
        args.relations,
    )
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"responses": len(result["responses"]), "query_ids": result["query_ids"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
