#!/usr/bin/env python3
"""Build the v11 FTA research baseline with one F01681 v3 model replay."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V10_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v10.json"
V11_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v11.json"
F01681_V3_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v10.json": (
        "fta-baseline-manifest-v10-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v10 research baseline; v11 records one live F01681 development replay.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v10.py": (
        "fta-baseline-manifest-v10-builder", "reproducibility_tool", "superseded",
        "Historical builder for the v10 snapshot.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v10.py": (
        "fta-baseline-manifest-v10-tests", "manifest_regression_tests", "historical",
        "Regression tests for the v10 snapshot.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v11.py": (
        "fta-baseline-manifest-v11-builder", "reproducibility_tool", "current",
        "Builds v11 from immutable v10 and records the source-pinned F01681 prompt-v3 online replay.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v11.py": (
        "fta-baseline-manifest-v11-tests", "manifest_regression_tests", "current",
        "Checks replay counts, evidence and non-readiness boundaries, v10 immutability and artifact hashes.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v11-default", "validation_tool", "current",
        "Validates manifest paths and hashes; defaults to the active v11 snapshot.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v11-default", "validation_tool_tests", "current",
        "Verifies manifest validation and the active v11 baseline.",
    ),
    "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py": (
        "v8-current-evaluation-quality_eval-public_sources-test_probe_candidate_fta_raw_source_v1-py", "model_probe_regression_tests", "current",
        "Asserts stage attribution and the current cause disposition v3 prompt version; 10 offline tests pass.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v3-live-run", "online_model_development_probe", "current_development_evidence",
        "One four-stage DeepSeek Flash replay with retries disabled; not Gold, accuracy evidence, database input or production output.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v3-live-run-report", "online_model_development_report", "current_development_evidence",
        "Human-readable summary of the same F01681 development replay.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v3-ai-review", "independent_ai_role_review", "current_development_review",
        "Read-only AI subagent review; flags the only Cause candidate as a possible tautological restatement; not human expert approval.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v3-ai-review-report", "independent_ai_role_review_report", "current_development_review",
        "Human-readable AI role-review result; no file edits or additional model calls.",
    ),
    "docs/README.md": (
        "fta-v11-doc-index", "current_truth_index", "current", "Points to active FTA baseline v11.",
    ),
    "docs/current-state-audit.md": (
        "fta-v11-current-state-audit", "current_state_document", "current",
        "Records the one online F01681 v3 development replay and its semantic limitation.",
    ),
    "docs/acceptance.md": (
        "fta-v11-acceptance-record", "acceptance_document", "current",
        "Records the actual one-sample model command, output and verification boundaries.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v11-candidate-generation-policy", "candidate_fta_policy_document", "current",
        "Documents the F01681 prompt-v3 replay and keeps its candidate-only status explicit.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v11-validation-plan-policy", "validation_plan_document", "current",
        "Records the prompt-v3 raw-text replay as development evidence, not final validation.",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def _load_and_validate_replay() -> dict[str, Any]:
    payload = json.loads(F01681_V3_PATH.read_text(encoding="utf-8"))
    if payload.get("source", {}).get("sample_id") != "SIEMENS_S210_2019_F01681":
        raise ValueError("v11 replay must be the source-pinned S210 F01681 sample")
    if payload.get("prompt_versions", {}).get("cause_disposition") != "fta-cause-disposition-v3":
        raise ValueError("v11 replay must use cause disposition prompt v3")
    if payload.get("model", {}).get("request_attempt_count") != 4:
        raise ValueError("v11 replay must record the four expected pipeline requests")
    if payload.get("model", {}).get("successful_response_count") != 4:
        raise ValueError("v11 replay did not complete all four model stages")
    if payload.get("model", {}).get("configured_max_retries") != 0:
        raise ValueError("v11 replay must have model retries disabled")
    if payload.get("fta_ready") or payload.get("production_ready") or payload.get("formal_gold") or payload.get("database_written"):
        raise ValueError("development replay must not be promoted to Gold, database, or readiness")
    return payload


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V10_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v10":
        raise ValueError("v11 must extend the frozen v10 manifest snapshot")
    replay = _load_and_validate_replay()
    outcome = replay["result"]["outcomes"][0]
    tree = outcome["tree"]
    dispositions = tree["cause_dispositions"]
    disposition_counts = dict(sorted(Counter(item["disposition"] for item in dispositions).items()))

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v11"
    manifest["baseline_version"] = "v11"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "one source-pinned online F01681 replay under cause disposition v3; 15 diagnostic mappings remain relation-only and the explicit Cause statement is a single review-only candidate"
    )
    manifest["scope"]["excludes"].append(
        "semantic correctness/general accuracy claims from the single F01681 replay, expert Gold, database writes, production integration, gate calibration, and FTA readiness"
    )
    manifest["active_baseline"]["f01681_v3_development_run"] = str(
        F01681_V3_PATH.relative_to(ROOT).as_posix()
    )
    manifest["cause_disposition_v3_online_model_replay"] = {
        "status": "one_case_development_replay_completed",
        "prompt_version": replay["prompt_versions"]["cause_disposition"],
        "sample_id": replay["source"]["sample_id"],
        "source_input_sha256": replay["source"]["input_text_sha256"],
        "model_id": replay["model"]["model_id"],
        "provider_host": replay["model"]["provider_host"],
        "request_attempt_count": replay["model"]["request_attempt_count"],
        "successful_response_count": replay["model"]["successful_response_count"],
        "configured_max_retries": replay["model"]["configured_max_retries"],
        "stages": [item["stage"] for item in replay["model_stage_responses"]],
        "cause_disposition_counts": disposition_counts,
        "candidate_tree_status": tree["status"],
        "candidate_tree_blockers": tree["blockers"],
        "candidate_tree_node_count": len(tree["nodes"]),
        "candidate_tree_gate_values": [item["gate"] for item in tree["gate_assessments"]],
        "candidate_tree_relation_count": len(tree["relations"]),
        "evidence_integrity": replay["evidence_integrity"],
        "semantic_review_note": "cause index 0 is an AI-proposed direct Cause condition but may be a generic restatement of the top-event description; candidate-only and not semantically validated",
        "independent_ai_review": {
            "path": "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.json",
            "provenance": "ai_subagent_role_review_not_human_expert",
            "conclusion": "needs_revision",
            "blocking_finding": "cause_index_0_semantic_restatement_risk",
        },
        "remedy_xxxx_9507_scope_reconciled": False,
        "reviewer_provenance": replay["reviewer_provenance"],
        "formal_gold": False,
        "database_written": False,
        "accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v10"],
        "current_version": "v11",
        "reason": "v11 records a single online F01681 replay under the already approved v3 policy; v10 remains an immutable historical research snapshot.",
    })

    for path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": path,
            "note": note,
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    root = ROOT.resolve(strict=True)
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids:
            raise ValueError(f"duplicate artifact id: {artifact_id}")
        if relative_path in seen_paths:
            raise ValueError(f"duplicate artifact path: {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        artifact["sha256"] = sha256_file(target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic snapshot regeneration")
    parser.add_argument("--check", action="store_true", help="compare generated content without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V11_PATH.read_text(encoding="utf-8") if V11_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v11 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v11",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V11_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V11_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
