"""Evaluate evidence-bound S210 RAG answer responses.

This evaluator intentionally does not score retrieval ranking.  It checks the
answer contract after a response has already been generated:

* an expected fault code is stated;
* citations are present and known;
* citations belong to an expected fault;
* required evidence fields have citations.

Semantic cause/remedy correctness and hallucination remain manual-review
dimensions and are reported as such instead of being guessed by string rules.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


FAULT_CODE_RE = re.compile(r"\b[A-Z]\d{5}\b", re.IGNORECASE)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _answer_payload(response: dict[str, Any]) -> dict[str, Any]:
    answer = response.get("answer")
    return answer if isinstance(answer, dict) else {}


def _citation_owner(citation_id: str) -> str:
    return citation_id.split(":", 1)[0].strip().upper()


def _known_citations(response: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for context in _as_list(response.get("contexts")):
        if not isinstance(context, dict):
            continue
        code = str(context.get("fault_code") or "").strip().upper()
        for evidence in _as_list(context.get("evidence")):
            if not isinstance(evidence, dict):
                continue
            citation_id = str(evidence.get("citation_id") or "").strip()
            field = str(evidence.get("field") or "").strip()
            if citation_id and field:
                result[citation_id] = field
                if not code:
                    result[citation_id] = field
    return result


def _response_citations(answer: dict[str, Any]) -> list[str]:
    explicit = [str(item).strip() for item in _as_list(answer.get("citations"))]
    explicit = [item for item in explicit if item]
    if explicit:
        return list(dict.fromkeys(explicit))
    text = str(answer.get("text") or "")
    return list(dict.fromkeys(re.findall(r"[A-Z]\d{5}:E\d+", text, re.IGNORECASE)))


def evaluate_response(query: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic contract metrics for one generated answer."""

    answer = _answer_payload(response)
    text = str(answer.get("text") or "")
    expected_codes = {
        str(code).strip().upper()
        for code in _as_list(query.get("expected_fault_codes"))
        if str(code).strip()
    }
    mentioned_codes = {
        code.upper() for code in FAULT_CODE_RE.findall(text)
    }
    fault_code_hit = bool(expected_codes & mentioned_codes)

    citations = _response_citations(answer)
    known = _known_citations(response)
    valid_citations = [citation for citation in citations if citation in known]
    aligned_citations = [
        citation
        for citation in valid_citations
        if _citation_owner(citation) in expected_codes
    ]
    cited_fields = {known[citation] for citation in aligned_citations}
    required_fields = {
        str(field).strip()
        for field in _as_list(query.get("required_evidence_fields"))
        if str(field).strip()
    }
    missing_fields = sorted(required_fields - cited_fields)

    citations_valid = bool(citations) and len(valid_citations) == len(citations)
    citations_aligned = bool(valid_citations) and len(aligned_citations) == len(valid_citations)
    answer_contract_pass = (
        fault_code_hit
        and citations_valid
        and citations_aligned
        and not missing_fields
    )
    return {
        "query_id": str(query.get("query_id") or ""),
        "fault_code_hit": fault_code_hit,
        "mentioned_fault_codes": sorted(mentioned_codes),
        "expected_fault_codes": sorted(expected_codes),
        "citations": citations,
        "valid_citations": valid_citations,
        "aligned_citations": aligned_citations,
        "citations_valid": citations_valid,
        "citations_aligned": citations_aligned,
        "cited_evidence_fields": sorted(cited_fields),
        "required_evidence_fields": sorted(required_fields),
        "missing_evidence_fields": missing_fields,
        "answer_contract_pass": answer_contract_pass,
        "manual_review_required": [
            "unsupported_claims",
            "cause_semantic_correctness",
            "remedy_semantic_correctness",
            "cross_fault_contamination",
        ],
    }


def _mean(values: Iterable[bool]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def evaluate_dataset(
    dataset: dict[str, Any],
    responses: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    queries = {
        str(query.get("query_id")): query
        for query in _as_list(dataset.get("queries"))
        if isinstance(query, dict) and query.get("query_id")
    }
    rows: list[dict[str, Any]] = []
    unknown_response_ids: list[str] = []
    for response in responses:
        if not isinstance(response, dict):
            continue
        query_id = str(response.get("query_id") or "")
        query = queries.get(query_id)
        if query is None:
            unknown_response_ids.append(query_id)
            continue
        rows.append(evaluate_response(query, response))

    return {
        "dataset": dataset.get("dataset_info", {}).get("name", ""),
        "query_count": len(queries),
        "response_count": len(rows),
        "missing_response_ids": sorted(set(queries) - {row["query_id"] for row in rows}),
        "unknown_response_ids": sorted(set(unknown_response_ids)),
        "metrics": {
            "fault_code_accuracy": _mean(row["fault_code_hit"] for row in rows),
            "citation_validity": _mean(row["citations_valid"] for row in rows),
            "citation_alignment": _mean(row["citations_aligned"] for row in rows),
            "answer_contract_pass_rate": _mean(
                row["answer_contract_pass"] for row in rows
            ),
        },
        "manual_review_required": [
            "unsupported_claims",
            "cause_semantic_correctness",
            "remedy_semantic_correctness",
            "cross_fault_contamination",
        ],
        "per_query": rows,
    }


def _load_responses(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        return [item for item in payload["responses"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = evaluate_dataset(
        load_json(args.dataset),
        _load_responses(args.responses),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
