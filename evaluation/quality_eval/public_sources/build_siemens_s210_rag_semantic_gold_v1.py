"""Build a new 30-query S210 RAG semantic-evaluation draft.

The queries are new phrasings derived from the frozen 281-record Gold.  The
artifact is an evaluation draft, not expert semantic Gold; cause/remedy
quality and unsupported-claim labels remain blank for human review.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


EXCLUDED_CODES_DEFAULT = {
    "A01009", "F30002", "F01005", "A01006", "A01019", "F01611",
    "A01631", "F01033", "F01012", "A30502",
}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _record(sample: dict[str, Any]) -> dict[str, Any] | None:
    records = sample.get("gold_records")
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        return None
    record = records[0]
    code = str(record.get("fault_code") or "").strip().upper()
    if not code or not record.get("description"):
        return None
    return record


def _make_query(query_id: str, query_type: str, record: dict[str, Any], sample_id: str) -> dict[str, Any]:
    code = str(record["fault_code"])
    description = str(record["description"])
    causes = [str(item) for item in record.get("causes", []) if str(item).strip()]
    parameters = [str(item) for item in record.get("parameters", []) if str(item).strip()]
    cause = causes[0] if causes else ""
    parameter = parameters[0] if parameters else ""
    if query_type == "fault_code":
        question = f"故障码 {code} 在手册中表示什么故障？请说明故障现象、可能原因和证据。"
        required = ["fault_code", "description", "cause"]
    elif query_type == "symptom":
        question = f"如果出现“{description}”，对应哪个故障码？请说明判断依据。"
        required = ["fault_code", "description"]
    elif query_type == "cause":
        question = f"手册中提到“{cause}”，它对应哪个故障记录？请说明原因证据。"
        required = ["fault_code", "cause"]
    elif query_type == "remedy":
        question = f"针对“{description}”，手册建议采取哪些处理措施？请引用原文依据。"
        required = ["fault_code", "description", "remedy"]
    elif query_type == "parameter":
        question = f"参数 {parameter} 与哪个故障记录相关？请说明故障含义和参数证据。"
        required = ["fault_code", "description", "parameter"]
    else:
        raise ValueError(query_type)
    return {
        "query_id": query_id,
        "question": question,
        "query_type": query_type,
        "difficulty": "medium" if query_type in {"cause", "parameter"} else "easy",
        "expected_fault_codes": [code],
        "required_evidence_fields": required,
        "ambiguity": "none",
        "relevance_policy": "any_relevant_in_top_k",
        "gold_source": "frozen_siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20",
        "source_sample_id": sample_id,
        "semantic_review_status": "pending_human_review",
        "review_note": "fault-code relevance is projected from frozen Gold; cause/remedy semantics, unsupported claims, and citation support require separate human review",
    }


def build(source: dict[str, Any], excluded_codes: set[str], count: int) -> dict[str, Any]:
    candidates: dict[str, list[tuple[str, dict[str, Any]]]] = {
        "fault_code": [], "symptom": [], "cause": [], "remedy": [], "parameter": []
    }
    descriptions = Counter(
        str(record.get("description"))
        for sample in source.get("samples", [])
        for record in ([ _record(sample) ] if _record(sample) else [])
    )
    seen_codes: set[str] = set()
    for sample in source.get("samples", []):
        record = _record(sample)
        if record is None:
            continue
        code = str(record["fault_code"]).strip().upper()
        if code in excluded_codes or code in seen_codes:
            continue
        sample_id = str(sample.get("sample_id") or "")
        candidates["fault_code"].append((sample_id, record))
        if descriptions[str(record["description"])] == 1:
            candidates["symptom"].append((sample_id, record))
        if record.get("causes"):
            candidates["cause"].append((sample_id, record))
        if record.get("parameters"):
            candidates["parameter"].append((sample_id, record))
        candidates["remedy"].append((sample_id, record))
        seen_codes.add(code)

    quota = {"fault_code": 8, "symptom": 7, "cause": 6, "remedy": 5, "parameter": 4}
    queries: list[dict[str, Any]] = []
    used: set[str] = set()
    for query_type, target in quota.items():
        for sample_id, record in candidates[query_type]:
            code = str(record["fault_code"]).strip().upper()
            if code in used:
                continue
            queries.append(_make_query(f"RAG-{len(queries)+1:03d}", query_type, record, sample_id))
            used.add(code)
            if sum(1 for row in queries if row["query_type"] == query_type) >= target:
                break
    if len(queries) < count:
        raise ValueError(f"only built {len(queries)} queries, requested {count}")
    queries = queries[:count]
    return {
        "dataset_info": {
            "name": "siemens_s210_rag_semantic_gold_v1",
            "version": date.today().isoformat(),
            "query_count": len(queries),
            "source_gold": "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20",
            "source_gold_count": 281,
            "split": "rag_semantic_review_draft",
            "status": "draft_pending_human_semantic_review",
            "expert_gold": False,
            "production_claim": False,
            "reuse_policy": "do_not_use_to_tune_retrieval_or_claim_rag_semantic_accuracy_before_review",
            "query_type_counts": dict(Counter(row["query_type"] for row in queries)),
            "evaluation_dimensions": [
                "fault_identification",
                "cause_correctness",
                "remedy_correctness",
                "citation_support",
                "unsupported_claims",
                "cross_fault_contamination",
            ],
        },
        "queries": queries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--exclude-code", action="append", default=[])
    args = parser.parse_args()
    source = _read(args.source)
    payload = build(source, EXCLUDED_CODES_DEFAULT | {value.upper() for value in args.exclude_code}, args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["dataset_info"]["query_type_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
