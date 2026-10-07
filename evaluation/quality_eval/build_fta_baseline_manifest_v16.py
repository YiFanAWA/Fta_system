#!/usr/bin/env python3
"""Build v16, registering the scoped readiness report without promoting global readiness."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V15_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v15.json"
V16_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v16.json"
READINESS_REPORT_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_scoped_readiness_assessment_v1_2026-09-28.json"
READINESS_REPORT_RELATIVE_PATH = "evaluation/quality_eval/runs/fta_scoped_readiness_assessment_v1_2026-09-28.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v15.json": (
        "fta-baseline-manifest-v15-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v15 snapshot pinned as the evidence baseline for scoped readiness assessment v1.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v16.py": (
        "fta-baseline-manifest-v16-builder", "reproducibility_tool", "current",
        "Builds the active v16 manifest from v15 and records scoped readiness without promoting global readiness.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v16.py": (
        "fta-baseline-manifest-v16-tests", "manifest_regression_tests", "current",
        "Checks scoped readiness registration, pinned report/baseline hashes, immutable v15, and global false flags.",
    ),
    "evaluation/quality_eval/build_fta_scoped_readiness_report_v1.py": (
        "fta-scoped-readiness-report-v1-builder", "reproducibility_tool", "current",
        "Builds the scoped structure/quantitative readiness report from the pinned v15 evidence inventory.",
    ),
    "evaluation/quality_eval/fta_readiness_report_v1.py": (
        "fta-scoped-readiness-report-v1-validator", "validation_tool", "current",
        "Validates scope arithmetic, source cluster provenance, criteria evidence, pinned baseline hash and no-promotion invariants.",
    ),
    "evaluation/quality_eval/test_fta_readiness_report_v1.py": (
        "fta-scoped-readiness-report-v1-tests", "validation_tool_tests", "current",
        "Checks blocked status, source/scope integrity, status evidence, and prevention of global-readiness promotion.",
    ),
    "evaluation/quality_eval/fta_generation_eval_lock_v1.json": (
        "fta-generation-eval-lock-v1", "evaluation_configuration_lock", "current",
        "Pins the observed DeepSeek Flash alias, runtime settings, and prompt/parser/contract source hashes; no model run or Final dataset is claimed.",
    ),
    "evaluation/quality_eval/build_fta_generation_eval_lock_v1.py": (
        "fta-generation-eval-lock-v1-builder", "reproducibility_tool", "current",
        "Rebuilds/checks the evaluation configuration snapshot without printing credentials or calling the model provider.",
    ),
    "evaluation/quality_eval/test_build_fta_generation_eval_lock_v1.py": (
        "fta-generation-eval-lock-v1-tests", "reproducibility_tool_tests", "current",
        "Checks source hashes, safe endpoint recording, credential redaction, and not-run/not-created evaluation states.",
    ),
    "backend-python/tests/test_fta_graph_contract.py": (
        "fta-preview-contract-tests-current", "contract_tests", "current",
        "Covers Preview contract validation, including direct rejection of both fta_ready=true and production_ready=true.",
    ),
    READINESS_REPORT_RELATIVE_PATH: (
        "fta-scoped-readiness-assessment-v1-2026-09-28", "scoped_readiness_assessment", "current",
        "Evidence-bounded readiness assessment for 47 cases and 18 source clusters; both tracks are blocked and global flags remain false.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v16-default", "validation_tool", "current",
        "Validates repository paths and SHA-256 fingerprints; defaults to active v16.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v16-default", "validation_tool_tests", "current",
        "Validates active v16 and general path/hash failure cases.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v15.py": (
        "fta-baseline-manifest-v15-builder", "reproducibility_tool", "historical",
        "Historical builder retained to reproduce v15; v16 is the active manifest.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v15.py": (
        "fta-baseline-manifest-v15-tests", "manifest_regression_tests", "historical",
        "Historical v15 snapshot regression tests; v16 is the active manifest.",
    ),
    "docs/README.md": (
        "fta-v16-doc-index", "current_truth_index", "current", "Points to active FTA baseline v16 and its scoped readiness report.",
    ),
    "docs/current-state-audit.md": (
        "fta-v16-current-state-audit", "current_state_document", "current", "Records v16 readiness assessment and preserves Preview-only/global-false limits.",
    ),
    "docs/acceptance.md": (
        "fta-v16-acceptance-record", "acceptance_document", "current", "Records readiness report contract tests and manifest verification commands.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v16-candidate-generation-policy", "candidate_fta_policy_document", "current", "Points to v16 without changing Preview-only semantics.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v16-validation-plan-policy", "validation_plan_document", "current", "Records scoped readiness contract implementation and remaining blockers.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V15_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v15":
        raise ValueError("v16 must extend the frozen v15 manifest snapshot")
    report = json.loads(READINESS_REPORT_PATH.read_text(encoding="utf-8"))
    if report.get("baseline", {}).get("sha256") != _sha256(V15_PATH):
        raise ValueError("scoped readiness report must pin the exact v15 manifest bytes")
    if report.get("global_readiness") != {
        "fta_ready": False,
        "production_ready": False,
        "scope_can_promote_global_readiness": False,
    }:
        raise ValueError("scoped readiness report cannot promote global readiness")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v16"
    manifest["baseline_version"] = "v16"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "scoped FTA-Structure/FTA-Quantitative readiness assessment v1 over the explicitly enumerated 47-case/18-source-cluster scope"
    )
    manifest["scope"]["excludes"].append(
        "promoting scoped readiness findings into CandidateFtaTree, formal Gold, database, global FTA readiness, or production readiness"
    )
    manifest["active_baseline"]["scoped_readiness_report"] = READINESS_REPORT_RELATIVE_PATH
    if manifest["active_baseline"].get("fta_ready") is not False or manifest["active_baseline"].get("production_ready") is not False:
        raise ValueError("v15 global readiness must remain false")
    manifest["scoped_readiness_assessment"] = {
        "report_path": READINESS_REPORT_RELATIVE_PATH,
        "report_sha256": _sha256(READINESS_REPORT_PATH),
        "scope_id": report["scope"]["scope_id"],
        "case_count": report["scope"]["case_count"],
        "source_cluster_count": report["scope"]["source_cluster_count"],
        "structure_status": report["structure_readiness"]["status"],
        "quantitative_status": report["quantitative_readiness"]["status"],
        "assessment_provenance": report["assessment_provenance"]["reviewer_provenance"],
        "human_expert_reviewed": report["assessment_provenance"]["human_expert_reviewed"],
        "scope_can_promote_global_readiness": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v15"],
        "current_version": "v16",
        "reason": "v16 registers the independently scoped readiness assessment; the pinned v15 baseline remains immutable.",
    })

    root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": relative_path,
            "note": note,
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(root):
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
        current = V16_PATH.read_text(encoding="utf-8") if V16_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v16 differs from generated content\n")
        assessment = payload["scoped_readiness_assessment"]
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v16",
            "structure_status": assessment["structure_status"],
            "quantitative_status": assessment["quantitative_status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V16_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V16_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
