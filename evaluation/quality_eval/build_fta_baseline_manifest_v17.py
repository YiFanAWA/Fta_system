#!/usr/bin/env python3
"""Build v17 with the external FTA source-screen audit, without creating Final."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V16_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v16.json"
V17_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v17.json"
SOURCE_SCREEN_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_independent_final_source_screen_v1_2026-09-28.json"
SOURCE_SCREEN_RELATIVE_PATH = "evaluation/quality_eval/runs/fta_independent_final_source_screen_v1_2026-09-28.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v16.json": (
        "fta-baseline-manifest-v16-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v16 snapshot; v17 adds a source-screen audit while keeping independent Final uncreated.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v16.py": (
        "fta-baseline-manifest-v16-builder", "reproducibility_tool", "historical",
        "Historical builder retained to reproduce v16; v17 is the active manifest.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v16.py": (
        "fta-baseline-manifest-v16-tests", "manifest_regression_tests", "historical",
        "Historical v16 snapshot regression tests; v17 is the active manifest.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v17.py": (
        "fta-baseline-manifest-v17-builder", "reproducibility_tool", "current",
        "Builds v17 from immutable v16 and records screened source candidates without allocating or creating Final.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v17.py": (
        "fta-baseline-manifest-v17-tests", "manifest_regression_tests", "current",
        "Checks source-screen accounting, v16 immutability, unallocated source candidates, and global false flags.",
    ),
    SOURCE_SCREEN_RELATIVE_PATH: (
        "fta-independent-final-source-screen-v1-2026-09-28", "external_source_suitability_audit", "current",
        "Screens four public whole documents; two conditional candidates, one secondary source, one excluded artifact; no dataset, labels, model call, or source allocation.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v17-default", "validation_tool", "current",
        "Validates repository paths and SHA-256 fingerprints; defaults to active v17.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v17-default", "validation_tool_tests", "current",
        "Validates active v17 and generic path/hash failure cases.",
    ),
    "docs/README.md": (
        "fta-v17-doc-index", "current_truth_index", "current", "Points to active FTA baseline v17 and the external source-screen audit.",
    ),
    "docs/current-state-audit.md": (
        "fta-v17-current-state-audit", "current_state_document", "current", "Records the source-screen outcome and preserves blocked readiness/Preview-only limits.",
    ),
    "docs/acceptance.md": (
        "fta-v17-acceptance-record", "acceptance_document", "current", "Records v17 source-screen checks and current limits.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v17-candidate-generation-policy", "candidate_fta_policy_document", "current", "Points to v17 without changing Preview-only semantics.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v17-validation-plan-policy", "validation_plan_document", "current", "Records screened whole-document candidates and the required scope adapter before Final assembly.",
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
    previous = json.loads(V16_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v16":
        raise ValueError("v17 must extend the frozen v16 manifest snapshot")
    screen = json.loads(SOURCE_SCREEN_PATH.read_text(encoding="utf-8"))
    if screen.get("baseline", {}).get("manifest_sha256") != _sha256(V16_PATH):
        raise ValueError("source-screen audit must pin the exact v16 manifest bytes")
    if screen.get("independent_final_validation", {}).get("status") != "not_created":
        raise ValueError("source-screen audit must not claim Final creation")
    if screen.get("independent_final_validation", {}).get("model_inference_run") is not False:
        raise ValueError("source-screen audit must not claim model inference")
    seen_dev_only = [
        item for item in screen.get("sources", [])
        if item.get("screening_role") == "seen_development_candidate_only_not_blind_final"
    ]
    if len(seen_dev_only) != 2 or any(item.get("blind_final_eligible") is not False for item in seen_dev_only):
        raise ValueError("expected exactly two seen development-only sources, none blind-Final eligible")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v17"
    manifest["baseline_version"] = "v17"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "whole-document external source suitability screen for four public reports; two suitable documents are already seen and development-only, and no blind Final source is available from this screen"
    )
    manifest["scope"]["excludes"].append(
        "independent Final dataset/labels/model run, allocation of seen sources to a blind Final, and claims that diagram gates are directly authorized by prose"
    )
    manifest["active_baseline"]["external_source_screen"] = SOURCE_SCREEN_RELATIVE_PATH
    manifest["source_screen"] = {
        "report_path": SOURCE_SCREEN_RELATIVE_PATH,
        "report_sha256": _sha256(SOURCE_SCREEN_PATH),
        "screened_document_count": len(screen.get("sources", [])),
        "seen_development_only_source_count": len(seen_dev_only),
        "blind_final_eligible_source_count": sum(item.get("blind_final_eligible") is True for item in screen.get("sources", [])),
        "seen_development_only_source_clusters": [item["source_cluster_id"] for item in seen_dev_only],
        "evaluation_adapter_required": True,
        "model_inference_run": False,
        "final_dataset_created": False,
    }
    manifest["independent_final_validation"] = {
        **manifest["independent_final_validation"],
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "The two most suitable screened reports have already had representative tree pages inspected and are development-only, so this screen contributes no blind-eligible Final source. No bounded event-scope input packets or reference graph dataset have been assembled. The current per-FaultRecord service cannot directly consume system-level reports as one tree; acquire a new unseen whole-document source and build/validate an evaluation-only scope adapter before opening blind Final labels.",
        "required_before_creation": [
            "approve bounded top-event scope and model-visible input packet rules",
            "keep each full source document as one indivisible cluster and separate diagram/reference outputs from model input",
            "freeze model, prompt, policy, parser, and evaluation adapter before unsealing Final labels",
            "record both diagram reference gates and text-authorized gate labels; absent direct text evidence must permit unknown/abstention",
            "report source-holdout scope, population, provenance, per-class support, selective risk/coverage, and failure cases",
        ],
    }
    allocation = manifest.get("source_cluster_allocation")
    if isinstance(allocation, dict):
        allocation["screened_seen_development_only_clusters"] = [item["source_cluster_id"] for item in seen_dev_only]
        allocation["screened_blind_final_eligible_count"] = 0
        allocation["screen_does_not_allocate_or_create_final"] = True
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v16"],
        "current_version": "v17",
        "reason": "v17 registers a whole-document external source screen and contract-fit blocker; no source is allocated and independent Final remains uncreated.",
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
        current = V17_PATH.read_text(encoding="utf-8") if V17_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v17 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v17",
            "screened_documents": payload["source_screen"]["screened_document_count"],
            "seen_development_only_sources": payload["source_screen"]["seen_development_only_source_count"],
            "blind_final_eligible_sources": payload["source_screen"]["blind_final_eligible_source_count"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V17_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V17_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
