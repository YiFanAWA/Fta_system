"""Run a raw-text, preview-only FTA probe for the public S210 F30021 sample."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import sys
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend-python"))

from core.config import (  # noqa: E402
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MAX_RETRIES,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from core.model_client import RetryingModelClient  # noqa: E402
from core.openai_model_client import OpenAICompatibleModelClient  # noqa: E402
from fta.candidate_fta_application_service import CandidateFtaApplicationService  # noqa: E402
from fta.candidate_fta_extraction_service import CandidateFtaExtractionService  # noqa: E402
from workflows.ai_module import build_text_extraction_adapter  # noqa: E402


DEFAULT_CORPUS = (
    ROOT
    / "evaluation"
    / "quality_eval"
    / "datasets"
    / "siemens_s210_public_fault_corpus_v1.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "evaluation"
    / "quality_eval"
    / "runs"
    / "siemens_s210_f30021_candidate_fta_preview_v1_2026-09-27.json"
)
DEFAULT_REAUDIT_OUTPUT = (
    ROOT
    / "evaluation"
    / "quality_eval"
    / "runs"
    / "siemens_s210_f30021_candidate_fta_preview_v1_1_2026-09-27.json"
)
SAMPLE_ID = "SIEMENS_S210_2019_F30021"


class CountingClient:
    def __init__(self, delegate: OpenAICompatibleModelClient) -> None:
        self._delegate = delegate
        self.complete_calls = 0

    def complete(self, prompt: str) -> str:
        self.complete_calls += 1
        return self._delegate.complete(prompt)


class RecordingClient:
    def __init__(self, delegate: RetryingModelClient) -> None:
        self._delegate = delegate
        self.responses: list[str] = []

    def complete(self, prompt: str) -> str:
        response = self._delegate.complete(prompt)
        self.responses.append(response)
        return response


def _load_sample(corpus_path: Path, sample_id: str = SAMPLE_ID) -> dict[str, Any]:
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("sample_id") == sample_id:
            if not isinstance(row.get("input_text"), str) or not row["input_text"].strip():
                raise ValueError(f"sample {sample_id} has no input_text")
            return row
    raise ValueError(f"sample_id {sample_id!r} was not found in {corpus_path}")


def _audit_evidence(payload: dict[str, Any], source_text: str) -> dict[str, Any]:
    extraction_refs: list[dict[str, Any]] = []
    candidate_refs: list[dict[str, Any]] = []
    extraction = payload.get("extraction", {})
    for index, item in enumerate(extraction.get("evidence_spans", [])):
        extraction_refs.append(
            {"ref": f"extraction:{index}", "binding_origin": "extraction_span", **item}
        )

    for outcome in payload.get("outcomes", []):
        tree = outcome.get("tree")
        if not isinstance(tree, dict):
            continue
        for node in tree.get("nodes", []):
            candidate_refs.extend(
                {
                    "ref": f"node:{node.get('node_id')}:{index}",
                    "binding_origin": "model_quote"
                    if str(item.get("citation_id", "")).startswith("input_text:")
                    else "inherited_extraction_span",
                    **item,
                }
                for index, item in enumerate(node.get("evidence", []))
            )
        for gate in tree.get("gate_assessments", []):
            candidate_refs.extend(
                {
                    "ref": f"gate-scope:{gate.get('gate_node_id')}:{index}",
                    "binding_origin": "model_quote",
                    **item,
                }
                for index, item in enumerate(gate.get("scope_evidence", []))
            )
            candidate_refs.extend(
                {
                    "ref": f"gate-evidence:{gate.get('gate_node_id')}:{index}",
                    "binding_origin": "model_quote",
                    **item,
                }
                for index, item in enumerate(gate.get("gate_evidence", []))
            )
        for relation in tree.get("relations", []):
            candidate_refs.extend(
                {
                    "ref": f"relation-scope:{relation.get('relation_id')}:{index}",
                    "binding_origin": "model_quote",
                    **item,
                }
                for index, item in enumerate(relation.get("scope_evidence", []))
            )
            candidate_refs.extend(
                {
                    "ref": f"relation-evidence:{relation.get('relation_id')}:{index}",
                    "binding_origin": "model_quote",
                    **item,
                }
                for index, item in enumerate(relation.get("evidence", []))
            )

    def inspect(
        references: list[dict[str, Any]], *, check_model_quote_uniqueness: bool
    ) -> dict[str, Any]:
        issues = []
        model_quotes = [
            item for item in references if item.get("binding_origin") == "model_quote"
        ]
        for item in references:
            start, end, quote = item.get("start"), item.get("end"), item.get("quote")
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or not isinstance(quote, str)
                or source_text[start:end] != quote
            ):
                issues.append({"ref": item.get("ref"), "reason": "offset_mismatch"})
            elif (
                check_model_quote_uniqueness
                and item.get("binding_origin") == "model_quote"
                and source_text.count(quote) != 1
            ):
                issues.append({"ref": item.get("ref"), "reason": "quote_not_unique"})
        return {
            "reference_count": len(references),
            "all_offsets_exact": not any(x["reason"] == "offset_mismatch" for x in issues),
            "model_bound_quote_count": len(model_quotes),
            "all_model_bound_quotes_unique": not any(
                x["reason"] == "quote_not_unique" for x in issues
            ),
            "issues": issues,
        }

    missing_evidence_nodes = []
    for outcome in payload.get("outcomes", []):
        tree = outcome.get("tree") or {}
        missing_evidence_nodes.extend(
            node.get("node_id")
            for node in tree.get("nodes", [])
            if node.get("source_cause_indices") and not node.get("evidence")
        )

    return {
        "extraction": inspect(extraction_refs, check_model_quote_uniqueness=False),
        "candidate_tree": {
            **inspect(candidate_refs, check_model_quote_uniqueness=True),
            "nodes_missing_evidence": missing_evidence_nodes,
        },
    }


def reaudit_existing(
    corpus_path: Path,
    existing_artifact_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    sample = _load_sample(corpus_path)
    source_text = sample["input_text"]
    artifact = json.loads(existing_artifact_path.read_text(encoding="utf-8"))
    if artifact.get("source", {}).get("sample_id") != SAMPLE_ID:
        raise ValueError("existing artifact is not the expected F30021 sample")
    expected_hash = sha256(source_text.encode("utf-8")).hexdigest()
    if artifact.get("source", {}).get("input_text_sha256") != expected_hash:
        raise ValueError("existing artifact does not match the current raw source text")
    corrected = deepcopy(artifact)
    corrected["artifact_version"] = "v1.1"
    corrected["audit_revision"] = {
        "supersedes_artifact": str(existing_artifact_path),
        "reason": (
            "The initial audit incorrectly required inherited extraction-span quotations "
            "to be globally unique; this revision checks exact offsets for inherited spans "
            "and uniqueness only for model-bound quotations."
        ),
    }
    corrected["evidence_audit"] = _audit_evidence(corrected["result"], source_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(corrected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return corrected


def run(
    corpus_path: Path,
    output_path: Path,
    sample_id: str = SAMPLE_ID,
) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("No configured model API key is available")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")

    sample = _load_sample(corpus_path, sample_id)
    source_text = sample["input_text"]
    provider = CountingClient(
        OpenAICompatibleModelClient(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE or None,
            model=OPENAI_MODEL,
            timeout_seconds=OPENAI_TIMEOUT_SECONDS,
        )
    )
    retrying = RetryingModelClient(
        provider,
        max_retries=OPENAI_MAX_RETRIES,
        delay_seconds=2.0,
    )
    extraction_recorder = RecordingClient(retrying)
    candidate_recorder = RecordingClient(retrying)
    extractor = build_text_extraction_adapter(model_client=extraction_recorder)
    candidate_service = CandidateFtaExtractionService(candidate_recorder)
    application = CandidateFtaApplicationService(extractor, candidate_service)

    result = application.generate(source_text)
    result_payload = result.to_payload()
    evidence_audit = _audit_evidence(result_payload, source_text)
    outcome_summaries = []
    for outcome in result_payload.get("outcomes", []):
        tree = outcome.get("tree") or {}
        outcome_summaries.append(
            {
                "fault_code": outcome.get("fault_code"),
                "status": outcome.get("status"),
                "tree_status": tree.get("status"),
                "node_count": len(tree.get("nodes", [])),
                "gate_assessments": [
                    {
                        "scope_type": gate.get("scope_type"),
                        "gate": gate.get("gate"),
                        "child_count": len(gate.get("child_node_ids", [])),
                        "decision_reason": gate.get("decision_reason"),
                        "blockers": gate.get("blockers", []),
                    }
                    for gate in tree.get("gate_assessments", [])
                ],
                "tree_blockers": tree.get("blockers", []),
            }
        )

    artifact = {
        "artifact_type": "candidate_fta_real_source_preview_probe",
        "artifact_version": "v1",
        "reviewer_provenance": "live_model_development_probe_not_expert_review",
        "formal_gold": False,
        "database_written": False,
        "gate_policy_selected": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": (
            f"single public Siemens S210 {sample['weak_record'].get('fault_code')} raw fault text "
            "through extraction and recursive candidate FTA preview"
        ),
        "source": {
            "sample_id": sample["sample_id"],
            "dataset": corpus_path.name,
            "corpus_sha256": sha256(corpus_path.read_bytes()).hexdigest(),
            "input_text_sha256": sha256(source_text.encode("utf-8")).hexdigest(),
            "provenance": sample.get("provenance", {}),
        },
        "model": {
            "model_id": OPENAI_MODEL,
            "provider_host": urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None,
            "temperature": 0,
            "request_attempt_count": provider.complete_calls,
            "note": (
                "The configured model receives only the raw source text and extracted payload; "
                "no gate label or review result is supplied. Retries count as extra attempts."
            ),
        },
        "model_stage_responses": [
            {"stage": "fault_extraction", "responses": extraction_recorder.responses},
            {"stage": "structure_decomposition_and_gate_assessment", "responses": candidate_recorder.responses},
        ],
        "outcome_summaries": outcome_summaries,
        "evidence_audit": evidence_audit,
        "result": result_payload,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--sample-id", default=SAMPLE_ID)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reaudit-existing", type=Path)
    args = parser.parse_args()
    if args.reaudit_existing:
        output_path = args.output or DEFAULT_REAUDIT_OUTPUT
        artifact = reaudit_existing(args.corpus, args.reaudit_existing, output_path)
    else:
        safe_sample_id = "".join(
            char.lower() if char.isalnum() else "_" for char in args.sample_id
        ).strip("_")
        output_path = args.output or (
            DEFAULT_OUTPUT
            if args.sample_id == SAMPLE_ID
            else ROOT
            / "evaluation"
            / "quality_eval"
            / "runs"
            / f"{safe_sample_id}_candidate_fta_preview_v1_2026-09-27.json"
        )
        artifact = run(args.corpus, output_path, args.sample_id)
    summary = {
        "output": str(output_path),
        "sample_id": artifact["source"]["sample_id"],
        "outcomes": artifact["outcome_summaries"],
        "evidence_audit": artifact["evidence_audit"],
        "request_attempt_count": artifact["model"]["request_attempt_count"],
        "formal_gold": artifact["formal_gold"],
        "database_written": artifact["database_written"],
        "fta_ready": artifact["fta_ready"],
        "production_ready": artifact["production_ready"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
