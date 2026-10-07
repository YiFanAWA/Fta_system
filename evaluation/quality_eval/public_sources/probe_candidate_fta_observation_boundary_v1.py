"""Run one bounded production Candidate FTA pass on a synthetic observation case."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.candidate_fta_contract import (  # noqa: E402
    CandidateFtaStatus,
    find_disconnected_candidate_node_ids,
)
from contracts.extraction_contract import (  # noqa: E402
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from core.config import (  # noqa: E402
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from core.model_client import ModelClientError  # noqa: E402
from core.openai_model_client import OpenAICompatibleModelClient  # noqa: E402
from fta.candidate_fta_extraction_service import (  # noqa: E402
    CandidateFtaExtractionService,
    CandidateFtaValidationError,
)


CASE_ID = "OBSERVATION-COOCCURRENCE-001"
SOURCE_ID = "synthetic:fta-observation-cooccurrence-v1"
SOURCE_TEXT = (
    "In incident 17, alarm A was logged and alarm B was logged before pump shutdown. "
    "The report does not state that either alarm caused the shutdown or that both were required. "
    "The panel indicator may show red or amber as a separate display choice."
)
TOP_EVENT = "pump shutdown"
OBSERVATIONS = ("alarm A was logged", "alarm B was logged")
MODEL_STAGES = ("cause_disposition", "structure_decomposition", "gate_assessment")
MAX_MODEL_CALLS = 1
DEFAULT_OUTPUT = ROOT / "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.json"


class ModelRequestBudgetExceeded(RuntimeError):
    """A pipeline stage was blocked before exceeding this probe's request budget."""

    def __init__(self, *, attempted_request_index: int, max_model_calls: int) -> None:
        self.attempted_request_index = attempted_request_index
        self.max_model_calls = max_model_calls
        stage_index = attempted_request_index - 1
        self.stage = (
            MODEL_STAGES[stage_index]
            if stage_index < len(MODEL_STAGES)
            else "additional_candidate_fta_stage"
        )
        super().__init__(
            f"model request budget exceeded before provider call: "
            f"stage={self.stage}, max_model_calls={max_model_calls}"
        )


class CountingRecordingClient:
    """Count actual completion attempts and retain raw successful responses."""

    def __init__(self, delegate: OpenAICompatibleModelClient) -> None:
        self._delegate = delegate
        self.request_attempt_count = 0
        self.prompt_sha256: list[str] = []
        self.responses: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        if self.request_attempt_count >= MAX_MODEL_CALLS:
            raise ModelRequestBudgetExceeded(
                attempted_request_index=self.request_attempt_count + 1,
                max_model_calls=MAX_MODEL_CALLS,
            )
        self.request_attempt_count += 1
        self.prompt_sha256.append(sha256(prompt.encode("utf-8")).hexdigest())
        stage = MODEL_STAGES[self.request_attempt_count - 1]
        response = self._delegate.complete(prompt)
        self.responses.append({
            "request_index": self.request_attempt_count,
            "stage": stage,
            "response": response,
            "response_sha256": sha256(response.encode("utf-8")).hexdigest(),
        })
        return response


def build_fixture() -> tuple[ExtractionResult, FaultRecord]:
    record = FaultRecord(description=TOP_EVENT, causes=OBSERVATIONS)
    spans = []
    for field, quote, value_index in (
        (EvidenceField.DESCRIPTION, TOP_EVENT, None),
        (EvidenceField.CAUSE, OBSERVATIONS[0], 0),
        (EvidenceField.CAUSE, OBSERVATIONS[1], 1),
    ):
        start = SOURCE_TEXT.index(quote)
        spans.append(EvidenceSpan(
            record_id=record.record_id,
            field=field,
            source_id=SOURCE_ID,
            quote=quote,
            start=start,
            end=start + len(quote),
            value_index=value_index,
        ))
    extraction = ExtractionResult(
        status=ExtractionStatus.SUCCESS,
        records=(record,),
        evidence_spans=tuple(spans),
    )
    return extraction, record


def _evidence_audit(tree_payload: dict[str, Any]) -> dict[str, Any]:
    references: list[dict[str, Any]] = []
    for node in tree_payload.get("nodes", []):
        references.extend(node.get("evidence", []))
    for gate in tree_payload.get("gate_assessments", []):
        references.extend(gate.get("scope_evidence", []))
        references.extend(gate.get("gate_evidence", []))
    for relation in tree_payload.get("relations", []):
        references.extend(relation.get("scope_evidence", []))
        references.extend(relation.get("evidence", []))
    offset_errors = [
        item for item in references
        if SOURCE_TEXT[item.get("start", -1):item.get("end", -1)] != item.get("quote")
    ]
    duplicate_quotes = [
        item for item in references if isinstance(item.get("quote"), str)
        and SOURCE_TEXT.count(item["quote"]) != 1
    ]
    return {
        "reference_count": len(references),
        "all_offsets_exact": not offset_errors,
        "all_quotes_unique": not duplicate_quotes,
        "offset_errors": offset_errors,
        "duplicate_quotes": duplicate_quotes,
    }


def assess_policy(tree: Any) -> dict[str, Any]:
    disconnected_ids = set(find_disconnected_candidate_node_ids(
        tree.top_event_id, tree.nodes, tree.gate_assessments, tree.relations
    ))
    observation_node_ids: dict[str, list[str]] = {}
    for index, observation in enumerate(OBSERVATIONS):
        observation_node_ids[observation] = [
            node.node_id for node in tree.nodes
            if index in node.source_cause_indices and node.node_type != "top_event_candidate"
        ]
    retained_ids = {
        node_id for node_ids in observation_node_ids.values() for node_id in node_ids
    }
    scope_touches_observation = any(
        gate.output_node_id in retained_ids
        or bool(retained_ids.intersection(gate.child_node_ids))
        for gate in tree.gate_assessments
    )
    relation_touches_observation = any(
        relation.source_node_id in retained_ids or relation.target_node_id in retained_ids
        for relation in tree.relations
    )
    observations_distinct = all(observation_node_ids.values()) and all(
        not set(observation_node_ids[left]).intersection(observation_node_ids[right])
        for left, right in (
            (OBSERVATIONS[0], OBSERVATIONS[1]),
        )
    )
    all_disconnected = bool(retained_ids) and retained_ids <= disconnected_ids
    matched = (
        tree.status is CandidateFtaStatus.BLOCKED
        and observations_distinct
        and all_disconnected
        and not scope_touches_observation
        and not relation_touches_observation
    )
    return {
        "expected_boundary": "retain alarm observations as separate disconnected candidates; block the whole tree; do not link observations into a gate or relation",
        "tree_status": tree.status.value,
        "blockers": list(tree.blockers),
        "observation_candidate_node_ids": observation_node_ids,
        "disconnected_observation_node_ids": sorted(retained_ids & disconnected_ids),
        "all_observations_retained_as_distinct_nodes": bool(observations_distinct),
        "all_observation_nodes_disconnected": all_disconnected,
        "any_gate_scope_touches_observation_nodes": scope_touches_observation,
        "any_relation_touches_observation_nodes": relation_touches_observation,
        "policy_boundary_match": bool(matched),
    }


def render_markdown(artifact: dict[str, Any]) -> str:
    policy = artifact.get("policy_assessment") or {}
    lines = [
        "# Candidate FTA 观察共现边界受控运行", "",
        f"- 案例：`{CASE_ID}`（合成、非 Gold）",
        f"- 运行状态：`{artifact['run_status']}`；候选树：`{artifact.get('tree_status')}`",
        f"- 模型请求：{artifact['request_attempt_count']}；SDK 自动重试：{artifact['model']['sdk_max_retries']}；外层重试：0",
        f"- 观察节点分开保留：{policy.get('all_observations_retained_as_distinct_nodes')}",
        f"- 观察节点均断开：{policy.get('all_observation_nodes_disconnected')}",
        f"- Gate scope 接触观察节点：{policy.get('any_gate_scope_touches_observation_nodes')}",
        f"- Relation 接触观察节点：{policy.get('any_relation_touches_observation_nodes')}",
        f"- 规则匹配：{policy.get('policy_boundary_match')}",
        "", "## 边界说明", "",
        "此运行仅验证生产 Candidate FTA 三阶段服务对一条合成共现输入的行为；不读取 Gold/参考标签，不写数据库或生产 API。它不是专家审核、准确率或泛化成绩。模型失败或政策不匹配时保留响应，不自动修复或重试。", "",
    ]
    if artifact.get("failure"):
        lines.extend(["## 失败信息", "", f"- 阶段：`{artifact['failure'].get('stage')}`", f"- 类型：`{artifact['failure'].get('error_type')}`", f"- 代码：`{artifact['failure'].get('error_code')}`", ""])
    return "\n".join(lines)


def build_attempt_artifact(
    client: CountingRecordingClient,
    *,
    extraction: ExtractionResult,
    record: FaultRecord,
    started_at: str,
    run_status: str,
    tree: Any | None = None,
    failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tree_payload = tree.to_payload() if tree is not None else None
    policy = assess_policy(tree) if tree is not None else None
    return {
        "artifact_type": "candidate_fta_observation_boundary_model_run",
        "artifact_version": "v1",
        "case_id": CASE_ID,
        "run_status": run_status,
        "started_at_utc": started_at,
        "formal_gold": False,
        "human_expert_gold": False,
        "database_written": False,
        "production_api_called": False,
        "fta_ready": False,
        "production_ready": False,
        "model": {
            "model_id": OPENAI_MODEL,
            "provider_host": urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None,
            "temperature": 0,
            "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
            "sdk_max_retries": 0,
            "outer_retries": 0,
            "max_model_calls": MAX_MODEL_CALLS,
        },
        "request_attempt_count": client.request_attempt_count,
        "successful_response_count": len(client.responses),
        "prompt_sha256_by_call": client.prompt_sha256,
        "model_stage_responses": client.responses,
        "synthetic_input": {
            "source_id": SOURCE_ID,
            "source_text": SOURCE_TEXT,
            "source_text_sha256": sha256(SOURCE_TEXT.encode("utf-8")).hexdigest(),
            "record": {
                "record_id": record.record_id,
                "fault_code": record.fault_code,
                "description": record.description,
                "causes": list(record.causes),
            },
            "extraction_status": extraction.status.value,
            "evidence_spans": [
                {
                    "record_id": span.record_id,
                    "field": span.field.value,
                    "source_id": span.source_id,
                    "quote": span.quote,
                    "start": span.start,
                    "end": span.end,
                    "value_index": span.value_index,
                }
                for span in extraction.evidence_spans
            ],
            "reference_labels_loaded": False,
            "gold_included_in_model_input": False,
        },
        "tree_status": tree.status.value if tree is not None else None,
        "tree": tree_payload,
        "policy_assessment": policy,
        "failure": failure,
    }


def budget_failure_payload(exc: ModelRequestBudgetExceeded) -> dict[str, Any]:
    return {
        "stage": exc.stage,
        "error_type": type(exc).__name__,
        "error_code": "model_request_budget_exceeded",
        "retryable": False,
        "blocked_before_provider_call": True,
        "attempted_request_index": exc.attempted_request_index,
        "max_model_calls": exc.max_model_calls,
        "error_message": str(exc),
    }


def run_once(output_path: Path) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("No configured model API key is available")
    json_path = output_path.resolve()
    markdown_path = json_path.with_suffix(".md")
    if json_path.exists() or markdown_path.exists():
        raise FileExistsError(f"refusing to overwrite existing run artifacts: {json_path}")

    started_at = datetime.now(timezone.utc).isoformat()
    provider = OpenAICompatibleModelClient(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE or None,
        model=OPENAI_MODEL,
        timeout_seconds=OPENAI_TIMEOUT_SECONDS,
        sdk_max_retries=0,
    )
    client = CountingRecordingClient(provider)
    extraction, record = build_fixture()
    failure = None
    tree = None
    try:
        tree = CandidateFtaExtractionService(client).propose(
            extraction, record.record_id, SOURCE_TEXT
        )
        run_status = "response_received"
    except ModelRequestBudgetExceeded as exc:
        run_status = "blocked"
        failure = budget_failure_payload(exc)
    except ModelClientError as exc:
        call_index = max(client.request_attempt_count - 1, 0)
        stage = ("cause_disposition", "structure_decomposition", "gate_assessment")[call_index]
        run_status = "blocked"
        failure = {
            "stage": stage,
            "error_type": type(exc).__name__,
            "error_code": exc.code,
            "retryable": exc.retryable,
            "error_message": exc.message,
        }
    except CandidateFtaValidationError as exc:
        run_status = "blocked"
        failure = {
            "stage": "candidate_fta_contract_validation",
            "error_type": type(exc).__name__,
            "error_code": "candidate_fta_validation_error",
            "retryable": False,
            "error_message": "candidate output failed contract validation; raw model responses are retained separately",
        }
    except Exception as exc:
        run_status = "blocked"
        failure = {
            "stage": "candidate_fta_run",
            "error_type": type(exc).__name__,
            "error_code": "unexpected_single_run_failure",
            "retryable": False,
            "error_message": "unexpected failure details are suppressed; raw model responses are retained separately",
        }

    artifact = build_attempt_artifact(
        client,
        extraction=extraction,
        record=record,
        started_at=started_at,
        run_status=run_status,
        tree=tree,
        failure=failure,
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(artifact), encoding="utf-8")
    return artifact


def preflight(output_path: Path) -> dict[str, Any]:
    json_path = output_path.resolve()
    markdown_path = json_path.with_suffix(".md")
    return {
        "status": "preflight_only",
        "model_request_performed": False,
        "credentials_configured": bool(OPENAI_API_KEY),
        "provider_host": urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None,
        "model_id": OPENAI_MODEL,
        "planned_max_model_calls": MAX_MODEL_CALLS,
        "sdk_max_retries": 0,
        "outer_retries": 0,
        "reference_labels_loaded": False,
        "gold_included_in_model_input": False,
        "database_write": False,
        "production_api_call": False,
        "output_paths_available": not json_path.exists() and not markdown_path.exists(),
        "output_json": str(json_path),
        "output_markdown": str(markdown_path),
    }


def render_existing_artifact(output_path: Path) -> dict[str, Any]:
    json_path = output_path.resolve()
    markdown_path = json_path.with_suffix(".md")
    if not json_path.is_file():
        raise FileNotFoundError(f"run JSON does not exist: {json_path}")
    if markdown_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {markdown_path}")
    artifact = json.loads(json_path.read_text(encoding="utf-8"))
    if (
        not isinstance(artifact, dict)
        or artifact.get("artifact_type") != "candidate_fta_observation_boundary_model_run"
        or artifact.get("case_id") != CASE_ID
        or not isinstance(artifact.get("model_stage_responses"), list)
    ):
        raise ValueError("existing JSON is not a compatible preserved model-run artifact")
    markdown_path.write_text(render_markdown(artifact), encoding="utf-8")
    return {
        "status": "report_rendered_from_preserved_response",
        "model_request_performed": False,
        "raw_response_modified": False,
        "output_json": str(json_path),
        "output_markdown": str(markdown_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--authorize-single-run", action="store_true")
    action.add_argument("--render-existing", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight(args.output)
    elif args.render_existing:
        result = render_existing_artifact(args.output)
    else:
        if not OPENAI_API_KEY:
            parser.exit(2, "No configured model API key is available\n")
        if args.output.exists() or args.output.with_suffix(".md").exists():
            parser.exit(2, f"Refusing to overwrite existing output: {args.output}\n")
        result = run_once(args.output)
    print(json.dumps({
        key: value for key, value in result.items()
        if key not in {"model_stage_responses", "tree", "synthetic_input"}
    }, ensure_ascii=False, indent=2))
    return 0 if (
        result.get("run_status") == "response_received"
        or result.get("status") in {"preflight_only", "report_rendered_from_preserved_response"}
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
