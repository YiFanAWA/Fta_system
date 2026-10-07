#!/usr/bin/env python3
"""Pin the current FTA raw-text generation runtime before independent evaluation."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "evaluation" / "quality_eval" / "fta_generation_eval_lock_v1.json"

PINNED_SOURCES = (
    ("evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py", "evaluation_runner"),
    ("backend-python/core/config.py", "runtime_configuration_resolution"),
    ("backend-python/core/model_client.py", "retry_policy"),
    ("backend-python/core/openai_model_client.py", "provider_adapter_and_request_parameters"),
    ("backend-python/core/prompt_templates.py", "fault_extraction_prompt_templates"),
    ("backend-python/extraction/fault_extractor.py", "fault_extraction_and_response_parsing"),
    ("backend-python/workflows/ai_module.py", "fault_extraction_adapter_wiring"),
    ("backend-python/fta/cause_disposition_service.py", "cause_disposition_prompt_v4_and_parser"),
    ("backend-python/fta/candidate_fta_application_service.py", "raw_text_pipeline_orchestration"),
    ("backend-python/fta/candidate_fta_extraction_service.py", "structure_gate_prompts_and_response_parsing"),
    ("backend-python/fta/gate_confidence_policy.py", "gate_acceptance_policy"),
    ("backend-python/fta/unknown_gate_reason_policy.py", "unknown_gate_reason_policy"),
    ("backend-python/contracts/candidate_fta_contract.py", "candidate_tree_contract"),
    ("backend-python/contracts/fta_cause_disposition_contract.py", "cause_disposition_contract"),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_endpoint(base_url: str) -> dict[str, Any]:
    parsed = urlsplit(base_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("configured model endpoint must include a scheme and host")
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path.rstrip("/"),
    }


def _validate_runtime(runtime: dict[str, Any]) -> None:
    model_id = runtime.get("model_id")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model_id must be a non-empty string")
    if not isinstance(runtime.get("base_url"), str) or not runtime["base_url"].strip():
        raise ValueError("base_url must be a non-empty string")
    timeout = runtime.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("timeout_seconds must be positive")
    retries = runtime.get("max_retries")
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ValueError("max_retries must be a non-negative integer")
    if not isinstance(runtime.get("credential_configured"), bool):
        raise ValueError("credential_configured must be boolean")


def build_lock(*, runtime: dict[str, Any], captured_at: str | None = None) -> dict[str, Any]:
    _validate_runtime(runtime)
    root = ROOT.resolve(strict=True)
    source_files = []
    for relative_path, role in PINNED_SOURCES:
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(root):
            raise ValueError(f"pinned source escapes repository: {relative_path}")
        source_files.append({
            "path": relative_path,
            "role": role,
            "sha256": _sha256(target),
        })

    try:
        openai_version = importlib.metadata.version("openai")
    except importlib.metadata.PackageNotFoundError:
        openai_version = None

    return {
        "schema": "fta_generation_eval_lock_v1",
        "lock_id": "fta_generation_eval_lock_v1",
        "captured_at": captured_at or date.today().isoformat(),
        "configuration_status": "pinned_candidate_eval_configuration",
        "model_inference_status": "not_run",
        "evaluation_runner": "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py",
        "model": {
            "model_id": runtime["model_id"],
            "endpoint": _safe_endpoint(runtime["base_url"]),
            "temperature": 0,
            "timeout_seconds": runtime["timeout_seconds"],
            "max_retries": runtime["max_retries"],
            "retry_delay_seconds": 2.0,
            "credential_configured": runtime["credential_configured"],
            "credential_value_recorded": False,
            "provider_revision": "not_exposed_by_configured_model_alias",
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "openai_package_version": openai_version,
        },
        "prompt_parser_and_contract_sources": source_files,
        "known_limits": [
            "The provider model identifier is an alias; this lock cannot prove the provider served immutable weights.",
            "A pinned source/runtime configuration is not an evaluation result or a semantic accuracy claim.",
            "Independent complete raw-text-to-tree Final data and labels do not yet exist; no model request was made while creating this lock.",
        ],
        "independent_final_validation": {
            "status": "not_created",
            "sample_count": 0,
            "source_cluster_count": 0,
        },
    }


def load_runtime_snapshot() -> dict[str, Any]:
    backend = str(ROOT / "backend-python")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from core.config import (  # noqa: PLC0415
        OPENAI_API_BASE,
        OPENAI_API_KEY,
        OPENAI_MAX_RETRIES,
        OPENAI_MODEL,
        OPENAI_TIMEOUT_SECONDS,
    )

    return {
        "model_id": OPENAI_MODEL,
        "base_url": OPENAI_API_BASE,
        "timeout_seconds": OPENAI_TIMEOUT_SECONDS,
        "max_retries": OPENAI_MAX_RETRIES,
        "credential_configured": bool(OPENAI_API_KEY),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic generation")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()

    payload = build_lock(runtime=load_runtime_snapshot(), captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = LOCK_PATH.read_text(encoding="utf-8") if LOCK_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA generation evaluation lock differs from current config or pinned sources\n")
        print(json.dumps({
            "status": "current",
            "model_id": payload["model"]["model_id"],
            "source_count": len(payload["prompt_parser_and_contract_sources"]),
            "model_inference_status": payload["model_inference_status"],
            "independent_final_validation": payload["independent_final_validation"]["status"],
        }, ensure_ascii=False))
        return 0

    LOCK_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "path": str(LOCK_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
