#!/usr/bin/env python3
"""Build v18 with an isolated single-event packet contract; do not create Final."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V17_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v17.json"
V18_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v18.json"

INPUT_SCHEMA = "evaluation/quality_eval/schemas/fta_event_scope_input_packet_v1.schema.json"
GOLD_SCHEMA = "evaluation/quality_eval/schemas/fta_event_scope_reference_gold_v1.schema.json"
CONTRACT = "evaluation/quality_eval/fta_event_scope_packet_contract.py"
CONTRACT_TEST = "evaluation/quality_eval/test_fta_event_scope_packet_contract.py"
SOURCE_LEADS = "evaluation/quality_eval/runs/fta_event_scope_source_leads_v1_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v17.json": (
        "fta-baseline-manifest-v17-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v17 snapshot; v18 adds the bounded single-event packet contract and source metadata lead without creating evaluation cases.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v17.py": (
        "fta-baseline-manifest-v17-builder", "reproducibility_tool", "historical",
        "Historical v17 builder retained to reproduce its source-screen snapshot.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v17.py": (
        "fta-baseline-manifest-v17-tests", "manifest_regression_tests", "historical",
        "Historical v17 tests retained; current manifest is v18.",
    ),
    "evaluation/quality_eval/runs/fta_independent_final_source_screen_v1_2026-09-28.json": (
        "fta-independent-final-source-screen-v1", "external_source_suitability_audit", "historical",
        "Closed metadata/source screen for four documents; retained as v17 evidence, not a dataset or Gold.",
    ),
    INPUT_SCHEMA: (
        "fta-event-scope-input-packet-schema-v1", "evaluation_input_schema", "current",
        "Model-visible bounded event packet shape; exact source segments only, with no reference gate labels.",
    ),
    GOLD_SCHEMA: (
        "fta-event-scope-reference-gold-schema-v1", "evaluation_gold_schema", "current",
        "Separate reference graph and text-authorized gate review shape; preserves reviewer provenance.",
    ),
    CONTRACT: (
        "fta-event-scope-packet-validator-v1", "evaluation_contract_validator", "current",
        "Validates bounded input, safe model projection, exact unique evidence, graph connectivity, and separate label consistency.",
    ),
    CONTRACT_TEST: (
        "fta-event-scope-packet-validator-tests-v1", "evaluation_contract_tests", "current",
        "Synthetic contract tests only; no public-source samples and no model inference.",
    ),
    SOURCE_LEADS: (
        "fta-event-scope-source-leads-v1-2026-09-29", "metadata_only_source_lead_register", "current",
        "One official NASA NTRS metadata lead; PDF/tree pages not inspected, no source allocation or Final eligibility.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v18.py": (
        "fta-baseline-manifest-v18-builder", "reproducibility_tool", "current",
        "Builds v18 from immutable v17, registers the packet contract, and keeps independent Final uncreated.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v18.py": (
        "fta-baseline-manifest-v18-tests", "manifest_regression_tests", "current",
        "Checks packet-contract registration, empty evaluation population, v17 immutability, and false readiness flags.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v18-default", "validation_tool", "current",
        "Validates repository paths and SHA-256 fingerprints; defaults to active v18.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v18-default", "validation_tool_tests", "current",
        "Validates active v18 and generic path/hash failure cases.",
    ),
    "docs/README.md": (
        "fta-v18-doc-index", "current_truth_index", "current", "Points to active FTA baseline v18 and the isolated event-scope packet contract.",
    ),
    "docs/current-state-audit.md": (
        "fta-v18-current-state-audit", "current_state_document", "current", "Records contract-only progress; no packet population, model evaluation, or readiness change.",
    ),
    "docs/acceptance.md": (
        "fta-v18-acceptance-record", "acceptance_document", "current", "Records packet contract tests and the exact non-claims for this phase.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v18-candidate-generation-policy", "candidate_fta_policy_document", "current", "Points to v18 and documents strict input/Gold separation.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v18-validation-plan-policy", "validation_plan_document", "current", "Records the evaluation-only contract milestone and its stop condition.",
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
    previous = json.loads(V17_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v17":
        raise ValueError("v18 must extend the frozen v17 manifest snapshot")
    leads = json.loads((ROOT / SOURCE_LEADS).read_text(encoding="utf-8"))
    if leads.get("search_policy", {}).get("eligible_for_final") is not False:
        raise ValueError("metadata-only leads must not claim Final eligibility")
    if any(item.get("exposure_status") != "metadata_only_unseen_pages" for item in leads.get("leads", [])):
        raise ValueError("v18 source leads must remain metadata-only and unseen at page level")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v18"
    manifest["baseline_version"] = "v18"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "evaluation-only bounded single-top-event packet contract, separate diagram-reference and text-authorized gate labels, cross-artifact validation, and metadata-only source lead search"
    )
    manifest["scope"]["excludes"].extend([
        "actual event-scope packets or reference Gold cases, model inference, accuracy/calibration metrics, and Final source allocation",
        "production service/API changes, database writes, formal Gold updates, and any promotion of global readiness",
    ])
    manifest["active_baseline"]["event_scope_packet_contract"] = "fta_event_scope_packet_contract_v1"
    manifest["event_scope_packet_contract"] = {
        "status": "contract_defined_not_populated",
        "input_schema_path": INPUT_SCHEMA,
        "reference_gold_schema_path": GOLD_SCHEMA,
        "validator_path": CONTRACT,
        "model_projection": "validated_model_input_only",
        "diagram_reference_gate_and_text_authorized_gate_are_separate": True,
        "input_packet_count": 0,
        "reference_gold_count": 0,
        "model_inference_run": False,
        "production_api_changed": False,
    }
    manifest["metadata_only_source_leads"] = {
        "report_path": SOURCE_LEADS,
        "report_sha256": _sha256(ROOT / SOURCE_LEADS),
        "lead_count": len(leads.get("leads", [])),
        "pdfs_downloaded_or_hashed": 0,
        "page_level_tree_content_opened": False,
        "overlap_audit_complete": False,
        "final_eligible_count": 0,
    }
    manifest["independent_final_validation"] = {
        **manifest["independent_final_validation"],
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "The v1 event-scope packet contract and cross-artifact validator now exist, but no source packet or reference graph cases have been assembled. The only new NASA lead is metadata-only; its PDF, rights notices, source overlap, and tree pages remain unaudited. The current per-FaultRecord service still cannot directly consume a system-level report as one tree.",
        "required_before_creation": [
            "complete whole-document source, rights, page-availability, and overlap audit for a fresh source cluster before opening any tree labels",
            "assemble bounded, page-addressed one-event input packets from allowed prose/FHA/FMECA context; exclude diagrams, gate symbols, and result tables from model input",
            "create separate diagram-reference graph and text-authorized gate labels with exact provenance and reviewer role",
            "freeze model, prompt, policy, parser, and evaluation adapter before unsealing Final labels",
            "keep all events from a source document in one indivisible source cluster",
            "report source-holdout scope, population, provenance, per-class support, selective risk/coverage, and failure cases",
        ],
    }
    manifest["source_cluster_allocation"]["metadata_only_lead_final_eligible_count"] = 0
    manifest["source_cluster_allocation"]["new_event_scope_packets_allocated"] = 0
    manifest["source_cluster_allocation"]["source_lead_metadata_only"] = True
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v17"],
        "current_version": "v18",
        "reason": "v18 establishes a validated evaluation-only event-scope packet contract and records one metadata-only source lead; it creates no cases, labels, model run, or Final allocation.",
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
        current = V18_PATH.read_text(encoding="utf-8") if V18_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v18 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v18",
            "packet_contract_status": payload["event_scope_packet_contract"]["status"],
            "input_packets": payload["event_scope_packet_contract"]["input_packet_count"],
            "reference_gold": payload["event_scope_packet_contract"]["reference_gold_count"],
            "metadata_leads": payload["metadata_only_source_leads"]["lead_count"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V18_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V18_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
