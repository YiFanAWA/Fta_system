#!/usr/bin/env python3
"""Build v19 by recording the screened XVS source without allocating Final cases."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V18_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v18.json"
V19_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v19.json"
SOURCE_SCREEN = "evaluation/quality_eval/runs/fta_event_scope_xvs_source_screen_v1_2026-09-29.json"
SOURCE_SCREEN_TEST = "evaluation/quality_eval/test_fta_event_scope_xvs_source_screen.py"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v18.json": (
        "fta-baseline-manifest-v18-snapshot", "baseline_manifest_snapshot", "historical_snapshot",
        "Immutable v18 snapshot from before the XVS PDF screen; its metadata-only state remains historically correct.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v18.py": (
        "fta-baseline-manifest-v18-builder", "reproducibility_tool", "historical",
        "Historical builder retained to reproduce v18; v19 is the active baseline.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v18.py": (
        "fta-baseline-manifest-v18-tests", "manifest_regression_tests", "historical",
        "Historical v18 tests retained; v19 has the active source-screen snapshot.",
    ),
    SOURCE_SCREEN: (
        "fta-event-scope-xvs-source-screen-v1", "whole_document_source_screen", "current",
        "XVS whole-document text/rights and Appendix D visual screen; marked seen development only, not positive text-to-FTA Final.",
    ),
    SOURCE_SCREEN_TEST: (
        "fta-event-scope-xvs-source-screen-tests-v1", "source_screen_contract_tests", "current",
        "Checks source identity/page/figure accounting and prevents this seen source from being promoted to Final or Gold.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v19.py": (
        "fta-baseline-manifest-v19-builder", "reproducibility_tool", "current",
        "Builds v19 from immutable v18 and records the seen XVS screen without creating packets, Gold, or model runs.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v19.py": (
        "fta-baseline-manifest-v19-tests", "manifest_regression_tests", "current",
        "Checks v19 source-screen registration, v18 immutability, zero evaluation population, and false readiness flags.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v19-default", "validation_tool", "current",
        "Validates repository paths and SHA-256 fingerprints; defaults to active v19.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v19-default", "validation_tool_tests", "current",
        "Validates active v19 and generic path/hash failure cases.",
    ),
    "docs/README.md": (
        "fta-v19-doc-index", "current_truth_index", "current", "Points to active FTA baseline v19 and the XVS source-screen result.",
    ),
    "docs/current-state-audit.md": (
        "fta-v19-current-state-audit", "current_state_document", "current", "Records that XVS is seen development-only and Final remains uncreated.",
    ),
    "docs/acceptance.md": (
        "fta-v19-acceptance-record", "acceptance_document", "current", "Records v19 reproducibility, source-screen tests, and unchanged production/readiness boundaries.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v19-candidate-generation-policy", "candidate_fta_policy_document", "current", "Points to v19 and records the XVS text-to-tree evidence limitation.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v19-validation-plan-policy", "validation_plan_document", "current", "Records the completed XVS source screen and next safe blind-source stop condition.",
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
    previous = json.loads(V18_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v18":
        raise ValueError("v19 must extend the frozen v18 manifest snapshot")
    screen = json.loads((ROOT / SOURCE_SCREEN).read_text(encoding="utf-8"))
    if screen.get("evaluation_suitability", {}).get("eligible_for_independent_final") is not False:
        raise ValueError("the opened XVS source must remain ineligible for independent Final")
    if screen.get("evaluation_suitability", {}).get("model_inference_run") is not False:
        raise ValueError("the source screen must not be misrepresented as a model run")
    if screen.get("readiness", {}).get("fta_ready") is not False or screen.get("readiness", {}).get("production_ready") is not False:
        raise ValueError("source screening cannot promote global readiness")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v19"
    manifest["baseline_version"] = "v19"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "whole-document rights/content/page/figure screen of one XVS source family; the opened family is seen development-only and not allocated to independent Final"
    )
    manifest["scope"]["excludes"].extend([
        "XVS-derived model input packets, reference Gold, diagram gate labels, and model inference",
        "any independent Final claim based on the inspected XVS report or its related source family",
    ])
    manifest["active_baseline"]["event_scope_source_screen"] = "fta_event_scope_xvs_source_screen_v1_2026-09-29"
    manifest["event_scope_source_screening"] = {
        "status": screen["evaluation_suitability"]["status"],
        "report_path": SOURCE_SCREEN,
        "report_sha256": _sha256(ROOT / SOURCE_SCREEN),
        "source_cluster_id": screen["source_document"]["source_cluster_id"],
        "document_sha256": screen["source_document"]["downloaded_pdf_sha256"],
        "page_count": screen["source_document"]["page_count"],
        "diagram_count": screen["content_screen"]["fault_tree_appendix"]["tree_count"],
        "input_packet_created": False,
        "reference_gold_created": False,
        "eligible_for_independent_final": False,
        "rights_review_is_legal_or_human": False,
        "semantic_overlap_audit_complete": False,
    }
    manifest["independent_final_validation"] = {
        **manifest["independent_final_validation"],
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "The v19 XVS source was downloaded and its tree appendix visually inspected, so it is seen development-only. Its prose provides high-level failure conditions but not the full Appendix D causal decomposition; the 1998 predecessor and related XVS concept report were not content-compared. No input packet, reference Gold, model inference, or blind Final case has been created.",
        "required_before_creation": [
            "find a different complete source family by metadata-only screening and keep its PDF/tree pages unopened until the evaluation configuration and source split are locked",
            "complete whole-document rights, page-availability, family, and overlap audit before opening any reference tree labels",
            "assemble bounded, page-addressed one-event input packets from allowed prose/FHA/FMECA context; exclude diagrams, gate symbols, and answer-revealing result tables from model input",
            "create separate diagram-reference graph and text-authorized gate labels with exact provenance and reviewer role",
            "freeze model, prompt, policy, parser, and evaluation adapter before unsealing Final labels",
            "keep all events from a source-document family in one indivisible source cluster",
            "report source-holdout scope, population, provenance, per-class support, selective risk/coverage, and failure cases",
        ],
    }
    manifest["source_cluster_allocation"]["xvs_screened_seen_development_clusters"] = 1
    manifest["source_cluster_allocation"]["xvs_allocated_packets"] = 0
    manifest["source_cluster_allocation"]["xvs_allocated_reference_gold"] = 0
    manifest["source_cluster_allocation"]["xvs_final_eligible"] = False
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v18"],
        "current_version": "v19",
        "reason": "v19 adds the complete XVS source-screen outcome and classifies the opened source family as seen development-only; it creates no packets, Gold, inference, or Final allocation.",
    })

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
    root = ROOT.resolve(strict=True)
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
        current = V19_PATH.read_text(encoding="utf-8") if V19_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v19 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v19",
            "xvs_screen": payload["event_scope_source_screening"]["status"],
            "xvs_packets": payload["event_scope_source_screening"]["input_packet_created"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V19_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V19_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
