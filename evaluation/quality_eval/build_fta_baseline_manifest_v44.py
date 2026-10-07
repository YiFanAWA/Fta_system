#!/usr/bin/env python3
"""Build active FTA baseline v44 for detached observation preservation."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V43_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v43.json"
V44_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v44.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v43.json": (
        "fta-baseline-manifest-v43-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v43 snapshot; superseded as active by v44.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v43.py": (
        "fta-baseline-manifest-v43-builder", "reproducibility_tool", "historical",
        "Historical builder for v43; retained for reproducibility.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v43.py": (
        "fta-baseline-manifest-v43-tests", "manifest_regression_tests", "historical",
        "Historical v43 baseline tests.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v44.py": (
        "fta-baseline-manifest-v44-builder", "reproducibility_tool", "current",
        "Builds v44 from immutable v43 and records the live mismatch plus offline detached-observation contract; no new model request.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v44.py": (
        "fta-baseline-manifest-v44-tests", "manifest_regression_tests", "current",
        "Protects v43 immutability, observed mismatch status, source registration, and false readiness.",
    ),
    "backend-python/contracts/fta_cause_disposition_contract.py": (
        "fta-cause-disposition-contract-v2", "domain_contract", "current",
        "Adds detached_observation and permits only the explicit host normalization from state/relation_only/descriptive_association with host provenance.",
    ),
    "backend-python/fta/cause_disposition_service.py": (
        "fta-cause-disposition-service-v5", "domain_service", "current",
        "Narrowly normalizes state + relation_only + descriptive_association to detached_observation when source evidence uniquely binds; prompt v5 has not been live-validated.",
    ),
    "backend-python/contracts/candidate_fta_contract.py": (
        "candidate-fta-tree-contract-v6", "domain_contract", "current",
        "Adds evidence-bearing observation_candidate nodes and prohibits gate/relation attachment.",
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "candidate-fta-service-detached-observation-v2", "domain_service", "current",
        "Host-preserves detached observations as separate evidence-bound nodes and blocks the whole tree.",
    ),
    "backend-python/tests/test_fta_cause_disposition.py": (
        "fta-cause-disposition-contract-v2-tests", "service_regression_tests", "current",
        "Tests exact host normalization, detached-state validity, and existing non-tree distinctions.",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-detached-observation-tests", "service_regression_tests", "current",
        "Asserts detached nodes remain distinct, evidenced, disconnected, and excluded from gates/relations; includes the previously observed relation_only classification.",
    ),
    "backend-python/tests/test_recursive_candidate_fta_extraction_service.py": (
        "candidate-fta-tree-contract-v6-tests", "contract_regression_tests", "current",
        "Covers recursive tree behavior with candidate tree artifact version v6.",
    ),
    "backend-python/core/openai_model_client.py": (
        "openai-compatible-client-explicit-retry-limit", "model_client_adapter", "current",
        "Exposes bounded SDK retry configuration; default behavior remains unchanged and probe passes zero.",
    ),
    "backend-python/tests/test_openai_model_client.py": (
        "openai-compatible-client-retry-limit-tests", "adapter_regression_tests", "current",
        "Verifies explicit SDK retry limit and zero-retry configuration.",
    ),
    "evaluation/quality_eval/public_sources/probe_candidate_fta_observation_boundary_v1.py": (
        "candidate-fta-observation-boundary-probe-v1", "bounded_model_probe_tool", "current",
        "Single bounded synthetic probe runner; can render preserved JSON without contacting a provider.",
    ),
    "evaluation/quality_eval/public_sources/test_probe_candidate_fta_observation_boundary_v1.py": (
        "candidate-fta-observation-boundary-probe-tests", "probe_regression_tests", "current",
        "Tests synthetic-only inputs, retry ceiling, artifact identity, offline report rendering, and replay of the preserved live response without a provider call.",
    ),
    "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.json": (
        "candidate-fta-observation-boundary-live-run-json", "raw_model_run", "current",
        "Preserved exact successful provider response from one synthetic request; old contract failed to materialize detached observation nodes.",
    ),
    "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.md": (
        "candidate-fta-observation-boundary-live-run-report", "model_run_report", "current",
        "Renders the saved live run and its policy mismatch; no second request was made.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v44-default", "validation_tool", "current",
        "Validates active v44 artifact paths and SHA-256 values by default.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v44-default", "validation_tool_tests", "current",
        "Covers manifest integrity and active v44 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v44-doc-index", "current_truth_index", "current",
        "Points to v44 and summarizes the observed mismatch and pending live validation.",
    ),
    "docs/current-state-audit.md": (
        "fta-v44-current-state-audit", "current_state_document", "current",
        "Records one live mismatch, the offline contract correction, and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v44-acceptance-record", "acceptance_document", "current",
        "Records live run outcome, offline tests, and the exact boundary of claims.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v44-candidate-generation-policy", "current_fta_policy_document", "current",
        "Documents detached observation candidates as evidence-bound, disconnected, and non-gating.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register(
    artifacts: list[dict[str, Any]], relative_path: str, metadata: dict[str, str]
) -> None:
    existing = next((item for item in artifacts if item.get("path") == relative_path), None)
    entry = {**(existing or {}), **metadata, "path": relative_path}
    if existing is None:
        artifacts.append(entry)
    else:
        artifacts[artifacts.index(existing)] = entry


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    source = json.loads(V43_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v43":
        raise ValueError("v44 must derive from the preserved v43 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v44 must preserve false FTA and production readiness")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v44"
    manifest["baseline_version"] = "v44"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v43",
        "path": V43_PATH.relative_to(ROOT).as_posix(),
        "reason": "v44 records one pre-fix live mismatch and an offline contract correction that preserves descriptive observations as detached, evidenced nodes; the correction has not been live-rerun.",
    }
    manifest["scope"]["includes"].append(
        "detached observation disposition and host-generated evidence-bound observation_candidate nodes that remain disconnected from the FTA graph and block whole-tree readiness"
    )
    manifest["scope"]["excludes"].append(
        "live validation of the corrected detached-observation behavior, expert semantic accuracy, Gold changes, database/API writes, and any FTA or production readiness promotion"
    )
    manifest["active_baseline"].update({
        "candidate_fta_observation_link_policy": "preserve_detached_observation_candidates_without_graph_links_v2",
        "candidate_fta_observation_contract_version": "v2",
        "candidate_fta_observation_live_validation": "pending_after_pre_fix_policy_mismatch",
        "candidate_fta_semantic_prompt_live_validation": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["candidate_fta_observation_boundary_v2"] = {
        "status": "preserved_response_offline_replay_passed_live_validation_pending",
        "user_boundary": "preserve evidenced observations as separate disconnected candidates; do not connect them to the top event or AND/OR without causal evidence",
        "pre_fix_live_run": {
            "path": "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.json",
            "model_request_count": 1,
            "sdk_retries": 0,
            "outer_retries": 0,
            "observed_disposition": "relation_only",
            "observed_observation_candidate_nodes": 0,
            "policy_boundary_match": False,
            "cause": "relation_only remained only in the disposition ledger and the service early-returned before materializing disconnected observation nodes",
        },
        "corrected_behavior_offline_contract": {
            "disposition": "detached_observation",
            "host_normalization": {
                "when": ["semantic_role=state", "proposed_disposition=relation_only", "reason_code=descriptive_association", "unique_source_evidence_bound"],
                "proposed_disposition_preserved": True,
                "final_disposition": "detached_observation",
                "provenance": "fta_cause_disposition_host_policy",
            },
            "node_type": "observation_candidate",
            "evidence_required": True,
            "gate_or_relation_attachment_allowed": False,
            "whole_tree_blocked": True,
        },
        "preserved_response_offline_replay": {
            "path": "evaluation/quality_eval/runs/fta_candidate_observation_boundary_v1_2026-09-29.json",
            "raw_response_sha256": "8a88673eb8d26d2e5ae23a3a6919baa25c96333c8201e070e781f76b54749d08",
            "provider_requests": 0,
            "raw_response_modified": False,
            "distinct_observation_nodes": 2,
            "all_nodes_disconnected": True,
            "gate_scopes": 0,
            "relations": 0,
            "whole_tree_status": "blocked",
            "policy_boundary_match": True,
        },
        "corrected_behavior_live_validation_performed": False,
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v43"],
        "current_version": "v44",
        "reason": "v44 records the observed pre-fix live mismatch and offline detached-observation contract correction without claiming corrected live behavior or promoting readiness.",
    })

    repo_root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": note,
            "sha256": _sha256(target),
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id, relative_path = artifact.get("artifact_id"), artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        artifact["sha256"] = _sha256(target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic regeneration")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V44_PATH.read_text(encoding="utf-8") if V44_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v44 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v44",
            "pre_fix_policy_boundary_match": payload[
                "candidate_fta_observation_boundary_v2"
            ]["pre_fix_live_run"]["policy_boundary_match"],
            "corrected_behavior_live_validated": False,
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V44_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V44_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
