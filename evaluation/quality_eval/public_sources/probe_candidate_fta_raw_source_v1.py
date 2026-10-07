"""Run the current candidate-FTA application on one public raw source record."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend-python"))

from core.config import (  # noqa: E402
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from core.model_client import ModelClientError, RetryingModelClient  # noqa: E402
from core.openai_model_client import OpenAICompatibleModelClient  # noqa: E402
from fta.cause_disposition_service import CAUSE_DISPOSITION_PROMPT_VERSION  # noqa: E402
from fta.candidate_fta_application_service import CandidateFtaApplicationService  # noqa: E402
from fta.candidate_fta_extraction_service import CandidateFtaExtractionService  # noqa: E402
from workflows.ai_module import build_text_extraction_adapter  # noqa: E402


DEFAULT_CORPUS = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s120_s150_2023_public_fault_corpus_holdout_v2.jsonl"
DEFAULT_SAMPLE_ID = "SIEMENS_S120_S150_2023_F35400_P3271_N001"
DEFAULT_OUTPUT = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s120_s150_f35400_raw_candidate_fta_v1_2026-09-28.json"
REQUEST_BUDGET_MAX_MODEL_CALLS = 4


class CountingClient:
    def __init__(self, delegate: OpenAICompatibleModelClient) -> None:
        self._delegate = delegate
        self.complete_calls = 0

    def complete(self, prompt: str) -> str:
        self.complete_calls += 1
        return self._delegate.complete(prompt)


class RequestBudgetClient:
    """Hard-stop an evaluation run before it can exceed its authorized call cap."""

    def __init__(self, delegate: CountingClient, *, max_model_calls: int) -> None:
        if not isinstance(max_model_calls, int) or isinstance(max_model_calls, bool):
            raise TypeError("max_model_calls must be an integer")
        if max_model_calls <= 0:
            raise ValueError("max_model_calls must be greater than zero")
        self._delegate = delegate
        self.max_model_calls = max_model_calls
        self.calls_started = 0
        self.budget_exhausted = False

    def complete(self, prompt: str) -> str:
        if self.calls_started >= self.max_model_calls:
            self.budget_exhausted = True
            raise ModelClientError(
                "evaluation_model_call_budget_exhausted",
                f"evaluation run reached its {self.max_model_calls}-call limit",
            )
        self.calls_started += 1
        return self._delegate.complete(prompt)


class RecordingClient:
    def __init__(self, delegate: RetryingModelClient) -> None:
        self._delegate = delegate
        self.responses: list[str] = []

    def complete(self, prompt: str) -> str:
        response = self._delegate.complete(prompt)
        self.responses.append(response)
        return response


def load_sample(corpus_path: Path, sample_id: str) -> dict[str, Any]:
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("sample_id") == sample_id:
            if not isinstance(row.get("input_text"), str) or not row["input_text"].strip():
                raise ValueError(f"sample {sample_id} has no input_text")
            return row
    raise ValueError(f"sample_id {sample_id!r} was not found in {corpus_path}")


def _response_payload(response: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        start, end = response.find("{"), response.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            payload = json.loads(response[start : end + 1])
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, dict) else None


def classify_response_stage(response: str) -> str:
    """Classify a model response by its output contract, not call position."""
    payload = _response_payload(response)
    if payload is None:
        return "unclassified_model_response"
    keys = set(payload)
    if "cause_dispositions" in keys:
        return "cause_disposition"
    if "structure_status" in keys and "nodes" in keys and "gate_scopes" in keys:
        return "structure_decomposition"
    if "gate_assessments" in keys:
        return "gate_assessment"
    if "items" in keys:
        return "fault_extraction"
    return "unclassified_model_response"


def _references(tree: dict[str, Any]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for node in tree.get("nodes", []):
        references.extend(node.get("evidence", []))
    for gate in tree.get("gate_assessments", []):
        references.extend(gate.get("scope_evidence", []))
        references.extend(gate.get("gate_evidence", []))
    for relation in tree.get("relations", []):
        references.extend(relation.get("scope_evidence", []))
        references.extend(relation.get("evidence", []))
    return references


def source_metadata(sample: dict[str, Any], dataset_id: str) -> dict[str, Any]:
    provenance = sample.get("provenance", {})
    return {
        "sample_id": sample["sample_id"],
        "dataset": dataset_id,
        "source_document": provenance.get("source_document"),
        "edition": provenance.get("edition"),
        "source_pdf": provenance.get("source_pdf"),
        "source_document_sha256": (
            provenance.get("source_pdf_sha256") or provenance.get("source_sha256")
        ),
        "source_section": provenance.get("section"),
        "source_url": provenance.get("source_url"),
        "official_reference_url": provenance.get("official_reference_url"),
        "pdf_page_start": provenance.get("pdf_page_start"),
        "pdf_page_end": provenance.get("pdf_page_end"),
        "source_offset_start": provenance.get("source_offset_start"),
        "source_offset_end": provenance.get("source_offset_end"),
        "input_text_sha256": sha256(sample["input_text"].encode("utf-8")).hexdigest(),
        "input_text_char_count": len(sample["input_text"]),
    }


def check_text_references(
    references: list[dict[str, Any]], source_text: str, *, require_unique_quotes: bool = True
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    non_unique_source_quote_count = 0
    for item in references:
        start, end, quote = item.get("start"), item.get("end"), item.get("quote")
        if (isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool)
                or not isinstance(end, int) or not isinstance(quote, str)):
            failures.append({"citation_id": item.get("citation_id"), "reason": "invalid_reference_shape"})
            continue
        if source_text[start:end] != quote:
            failures.append({"citation_id": item.get("citation_id"), "reason": "offset_mismatch"})
        if source_text.count(quote) != 1:
            non_unique_source_quote_count += 1
            if require_unique_quotes:
                failures.append({"citation_id": item.get("citation_id"), "reason": "quote_not_unique"})
    reasons = {item["reason"] for item in failures}
    return {
        "reference_count": len(references),
        "all_offsets_exact": "offset_mismatch" not in reasons and "invalid_reference_shape" not in reasons,
        "quote_uniqueness_required": require_unique_quotes,
        "all_quotes_unique": "quote_not_unique" not in reasons if require_unique_quotes else None,
        "non_unique_source_quote_count": non_unique_source_quote_count,
        "failures": failures,
    }


def evidence_integrity(result_payload: dict[str, Any], source_text: str) -> dict[str, Any]:
    extraction = result_payload.get("extraction", {})
    extraction_check = check_text_references(
        extraction.get("evidence_spans", []), source_text, require_unique_quotes=False
    )
    outcomes = result_payload.get("outcomes", [])
    tree = outcomes[0].get("tree") if outcomes else None
    if not isinstance(tree, dict):
        return {
            "extraction": extraction_check,
            "candidate_tree_available": False,
            "candidate_tree": {"reference_count": 0, "all_offsets_exact": False,
                               "all_quotes_unique": False, "failures": ["candidate_tree_unavailable"]},
            "cause_dispositions_available": False,
            "cause_dispositions": {
                "disposition_count": 0,
                "unresolved_without_evidence_count": 0,
                **check_text_references([], source_text),
            },
        }
    dispositions = tree.get("cause_dispositions", [])
    disposition_references = [
        evidence
        for disposition in dispositions
        for evidence in disposition.get("evidence", [])
    ]
    return {
        "extraction": extraction_check,
        "candidate_tree_available": True,
        "candidate_tree": check_text_references(_references(tree), source_text),
        "cause_dispositions_available": True,
        "cause_dispositions": {
            "disposition_count": len(dispositions),
            "unresolved_without_evidence_count": sum(
                disposition.get("disposition") == "unresolved"
                and not disposition.get("evidence")
                for disposition in dispositions
            ),
            **check_text_references(disposition_references, source_text),
        },
    }


def build_artifact(sample: dict[str, Any], result_payload: dict[str, Any],
                   responses: list[str], request_attempt_count: int,
                   dataset_id: str = "unspecified_corpus", *,
                   max_model_calls: int = REQUEST_BUDGET_MAX_MODEL_CALLS,
                   outer_max_retries: int = 0,
                   sdk_max_retries: int = 0,
                   budget_exhausted: bool = False) -> dict[str, Any]:
    source_text = sample["input_text"]
    source = source_metadata(sample, dataset_id)
    outcomes = result_payload.get("outcomes", [])
    outcome = outcomes[0] if outcomes else {}
    tree = outcome.get("tree") or {}
    stages = [classify_response_stage(response) for response in responses]
    stage_responses = [
        {"request_index": index, "stage": stage, "response": response,
         "response_sha256": sha256(response.encode("utf-8")).hexdigest()}
        for index, (stage, response) in enumerate(zip(stages, responses), start=1)
    ]
    cause_stage = next(
        (_response_payload(response) for response, stage in zip(responses, stages)
         if stage == "cause_disposition"), {}
    ) or {}
    proposed_disposition_counts = Counter(
        item.get("fta_disposition", "unknown")
        for item in cause_stage.get("cause_dispositions", [])
    )
    effective_dispositions = tree.get("cause_dispositions", [])
    effective_disposition_counts = Counter(
        item.get("disposition", "unknown")
        for item in effective_dispositions
    )
    return {
        "artifact_type": "candidate_fta_raw_source_development_probe",
        "artifact_version": "v1",
        "reviewer_provenance": "live_model_development_probe_not_expert_review",
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": "one public raw fault record through the current CandidateFtaApplicationService; development-path observation only, not a blind final test",
        "source": source,
        "model": {
            "model_id": OPENAI_MODEL,
            "provider_host": urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None,
            "temperature": 0,
            "request_attempt_count": request_attempt_count,
            "successful_response_count": len(responses),
            "outer_max_retries": outer_max_retries,
            "sdk_max_retries": sdk_max_retries,
            "configured_timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        },
        "request_budget": {
            "max_model_calls": max_model_calls,
            "calls_started": request_attempt_count,
            "budget_exhausted": budget_exhausted,
        },
        "prompt_versions": {"cause_disposition": CAUSE_DISPOSITION_PROMPT_VERSION},
        "model_stage_responses": stage_responses,
        "cause_disposition_counts": dict(sorted(effective_disposition_counts.items())),
        "model_proposed_cause_disposition_counts": dict(
            sorted(proposed_disposition_counts.items())
        ),
        "evidence_integrity": evidence_integrity(result_payload, source_text),
        "result": result_payload,
        "outcome_summary": {
            "status": outcome.get("status"),
            "fault_code": outcome.get("fault_code"),
            "tree_available": bool(tree),
            "node_count": len(tree.get("nodes", [])),
            "gate_scopes": [
                {"scope_type": item.get("scope_type"), "gate": item.get("gate"),
                 "child_count": len(item.get("child_node_ids", [])),
                 "blockers": item.get("blockers", [])}
                for item in tree.get("gate_assessments", [])
            ],
            "diagnostics": [
                {"code": item.get("code"), "stage": item.get("stage"),
                 "message": item.get("message")}
                for item in outcome.get("diagnostics", [])
            ],
        },
    }


def revalidate_existing_artifact(
    input_path: Path, corpus_path: Path, output_path: Path
) -> dict[str, Any]:
    """Recompute stage labels and evidence checks without making model calls."""
    markdown_path = output_path.with_suffix(".md")
    if output_path.exists() or markdown_path.exists():
        raise FileExistsError(f"refusing to overwrite output: {output_path}")
    artifact = json.loads(input_path.read_text(encoding="utf-8"))
    sample_id = artifact.get("source", {}).get("sample_id")
    sample = load_sample(corpus_path, sample_id)
    actual_hash = sha256(sample["input_text"].encode("utf-8")).hexdigest()
    if actual_hash != artifact.get("source", {}).get("input_text_sha256"):
        raise ValueError("source sample hash does not match the retained run artifact")
    responses = [
        item["response"]
        for item in artifact.get("model_stage_responses", [])
        if isinstance(item.get("response"), str)
    ]
    stages = [classify_response_stage(response) for response in responses]
    artifact["artifact_version"] = "v1.1"
    artifact["artifact_supersedes"] = str(input_path)
    artifact["audit_note"] = (
        "Offline re-audit only: response stages were classified from response contracts; "
        "extraction spans are checked by exact offsets, while uniqueness is required only "
        "for candidate-tree quotations. No model call was made."
    )
    artifact["model_stage_responses"] = [
        {
            "request_index": index,
            "stage": stage,
            "response": response,
            "response_sha256": sha256(response.encode("utf-8")).hexdigest(),
        }
        for index, (stage, response) in enumerate(zip(stages, responses), start=1)
    ]
    cause_stage = next(
        (_response_payload(response) for response, stage in zip(responses, stages)
         if stage == "cause_disposition"), {}
    ) or {}
    proposed_disposition_counts = Counter(
        item.get("fta_disposition", "unknown")
        for item in cause_stage.get("cause_dispositions", [])
    )
    outcomes = artifact.get("result", {}).get("outcomes", [])
    tree = outcomes[0].get("tree") if outcomes else None
    effective_disposition_counts = Counter(
        item.get("disposition", "unknown")
        for item in (tree.get("cause_dispositions", []) if isinstance(tree, dict) else [])
    )
    artifact["cause_disposition_counts"] = dict(
        sorted(effective_disposition_counts.items())
    )
    artifact["model_proposed_cause_disposition_counts"] = dict(
        sorted(proposed_disposition_counts.items())
    )
    artifact["evidence_integrity"] = evidence_integrity(
        artifact["result"], sample["input_text"]
    )
    artifact["source"].update(source_metadata(sample, corpus_path.stem))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_markdown(artifact), encoding="utf-8")
    return artifact


def render_markdown(artifact: dict[str, Any]) -> str:
    summary = artifact["outcome_summary"]
    evidence = artifact["evidence_integrity"]
    extraction = artifact["result"].get("extraction", {})
    lines = [
        "# Candidate FTA 原始公开文本端到端开发探针", "",
        f"- 样本：`{artifact['source']['sample_id']}`",
        f"- 故障码：`{summary.get('fault_code')}`",
        f"- 来源：{artifact['source'].get('source_document')}（{artifact['source'].get('edition')}），PDF 页 {artifact['source'].get('pdf_page_start')}–{artifact['source'].get('pdf_page_end')}",
        f"- 原始 PDF：`{artifact['source'].get('source_pdf')}`；章节：`{artifact['source'].get('source_section')}`；PDF SHA-256：`{artifact['source'].get('source_document_sha256')}`",
        f"- 原文字符数：{artifact['source']['input_text_char_count']}",
        f"- 模型阶段：{', '.join(item['stage'] for item in artifact['model_stage_responses']) or '无成功响应'}",
        f"- 请求尝试：{artifact['model']['request_attempt_count']}；成功响应：{artifact['model']['successful_response_count']}",
        f"- 抽取：`{extraction.get('status')}`，{len(extraction.get('records', []))} 条记录",
        f"- 模型提议处置（原始响应）：`{json.dumps(artifact['model_proposed_cause_disposition_counts'], ensure_ascii=False)}`",
        f"- 宿主最终处置（含证据门禁规范化）：`{json.dumps(artifact['cause_disposition_counts'], ensure_ascii=False)}`",
        f"- 候选结果：`{summary.get('status')}`；树={summary.get('tree_available')}；节点={summary.get('node_count')}",
        f"- 抽取证据：{evidence['extraction']['reference_count']} 条，offset 精确={evidence['extraction']['all_offsets_exact']}，源文重复短引文数={evidence['extraction']['non_unique_source_quote_count']}（以明确 offset 定位，不要求引文在全文唯一）",
        f"- 树证据：{evidence['candidate_tree']['reference_count']} 条，offset 精确={evidence['candidate_tree']['all_offsets_exact']}，引文唯一={evidence['candidate_tree']['all_quotes_unique']}",
        f"- 原因处置账证据：{evidence['cause_dispositions']['reference_count']} 条，offset 精确={evidence['cause_dispositions']['all_offsets_exact']}，引文唯一={evidence['cause_dispositions']['all_quotes_unique']}；未决且无证据 {evidence['cause_dispositions']['unresolved_without_evidence_count']} 项",
        "", "## 门与阻断", "",
    ]
    if artifact.get("audit_note"):
        lines.extend([f"- 再核验说明：{artifact['audit_note']}", ""])
    if summary["gate_scopes"]:
        for gate in summary["gate_scopes"]:
            lines.append(f"- `{gate['scope_type']}`：{gate['gate']}，子项 {gate['child_count']}；阻断：{', '.join(gate['blockers']) or '无'}")
    else:
        lines.append("- 未到门评估阶段，或没有可用候选树。")
    if summary["diagnostics"]:
        lines.extend(["", "## 诊断", ""])
        for item in summary["diagnostics"]:
            lines.append(f"- `{item['code']}`（{item['stage']}）：{item['message']}")
    lines.extend([
        "", "## 解释边界", "",
        "这是单条公开原文的开发探针，不是盲测成绩、专家 Gold、正式数据库写入或生产验收。模型 gate 概率未经校准；`proposed` 仅表示候选可供审核。`fta_ready=false`、`production_ready=false` 保持不变。", "",
        f"本次调用约束：最多 {artifact['request_budget']['max_model_calls']} 次；外层重试 {artifact['model']['outer_max_retries']} 次；SDK 重试 {artifact['model']['sdk_max_retries']} 次；预算耗尽={artifact['request_budget']['budget_exhausted']}。", "",
    ])
    return "\n".join(lines)


def run(corpus_path: Path, sample_id: str, output_path: Path) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("No configured model API key is available")
    markdown_path = output_path.with_suffix(".md")
    if output_path.exists() or markdown_path.exists():
        raise FileExistsError(f"refusing to overwrite output: {output_path}")
    sample = load_sample(corpus_path, sample_id)
    provider = CountingClient(OpenAICompatibleModelClient(
        api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE or None,
        model=OPENAI_MODEL, timeout_seconds=OPENAI_TIMEOUT_SECONDS,
        sdk_max_retries=0,
    ))
    budgeted_provider = RequestBudgetClient(
        provider, max_model_calls=REQUEST_BUDGET_MAX_MODEL_CALLS
    )
    model_client = RetryingModelClient(budgeted_provider, max_retries=0)
    recording_client = RecordingClient(model_client)
    application = CandidateFtaApplicationService(
        build_text_extraction_adapter(model_client=recording_client),
        CandidateFtaExtractionService(recording_client),
    )
    result = application.generate(sample["input_text"])
    artifact = build_artifact(
        sample,
        result.to_payload(),
        recording_client.responses,
        provider.complete_calls,
        dataset_id=corpus_path.stem,
        max_model_calls=budgeted_provider.max_model_calls,
        outer_max_retries=0,
        sdk_max_retries=0,
        budget_exhausted=budgeted_provider.budget_exhausted,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(artifact), encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--sample-id", default=DEFAULT_SAMPLE_ID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--revalidate-artifact", type=Path)
    args = parser.parse_args()
    artifact = (
        revalidate_existing_artifact(args.revalidate_artifact, args.corpus, args.output)
        if args.revalidate_artifact
        else run(args.corpus, args.sample_id, args.output)
    )
    print(json.dumps({
        "output": str(args.output), "markdown": str(args.output.with_suffix(".md")),
        **artifact["outcome_summary"],
        "model_stages": [item["stage"] for item in artifact["model_stage_responses"]],
        "evidence_integrity": artifact["evidence_integrity"],
        "fta_ready": artifact["fta_ready"], "production_ready": artifact["production_ready"],
    }, ensure_ascii=False, indent=2))
    return 1 if artifact["outcome_summary"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
