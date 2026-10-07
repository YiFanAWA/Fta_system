#!/usr/bin/env python3
"""Build v20 by registering one source-pinned NASA event-scope Dev case."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V19_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v19.json"
V20_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v20.json"
PACKET = "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
GOLD = "evaluation/quality_eval/datasets/fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"
SOURCE_SCREEN = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29.json"
PACKET_BUILDER = "evaluation/quality_eval/public_sources/build_nasa_battery_fig7_event_scope_dev_v1.py"
PACKET_TEST = "evaluation/quality_eval/public_sources/test_nasa_battery_fig7_event_scope_dev_v1.py"
AI_REVIEW = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_ai_role_review_v1_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v19.json": (
        "fta-baseline-manifest-v19-snapshot", "baseline_manifest_snapshot", "historical",
        "Immutable v19 baseline snapshot before the NASA battery Figure 7 development packet.",
    ),
    PACKET: (
        "nasa-battery-fig7-model-input-dev-v1", "event_scope_model_input_packet", "current",
        "One bounded source-text-only event-scope input; Figure 7, gate labels, and reference Gold are excluded from model input.",
    ),
    GOLD: (
        "nasa-battery-fig7-reference-gold-v1", "event_scope_reference_gold", "current",
        "Separate six-node Figure 7 reference graph and text-authorized gate review; AI-role review is explicitly distinguished from human expert Gold.",
    ),
    SOURCE_SCREEN: (
        "nasa-battery-fig7-source-screen-v1", "whole_document_source_screen", "current",
        "Official NASA source metadata, rights note, full-text/figure screen, known overlap limitations, and Dev-only allocation.",
    ),
    PACKET_BUILDER: (
        "nasa-battery-fig7-dev-case-builder-v1", "reproducibility_tool", "current",
        "Reproducibly generates the bounded model-input packet, separate reference Gold, and source-screen report.",
    ),
    PACKET_TEST: (
        "nasa-battery-fig7-dev-case-tests-v1", "event_scope_packet_contract_tests", "current",
        "Checks model-input/Gold isolation, cross-artifact contract, diagram/text gate separation, and non-Final claims.",
    ),
    AI_REVIEW: (
        "nasa-battery-fig7-ai-role-review-v1", "independent_ai_role_review", "current",
        "Read-only AI role review of Figure 7 gate operators and node/scope transcription; explicitly not human expert signoff or formal Gold.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v20.py": (
        "fta-baseline-manifest-v20-builder", "reproducibility_tool", "current",
        "Builds v20 from immutable v19 and records exactly one seen-source development case; Final and readiness remain blocked.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v20.py": (
        "fta-baseline-manifest-v20-tests", "manifest_regression_tests", "current",
        "Checks Dev-only counts, source allocation, readiness guards, artifact registration, and v19 immutability.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v20-default", "validation_tool", "current",
        "Validates repository paths and SHA-256 fingerprints; defaults to active v20.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v20-default", "validation_tool_tests", "current",
        "Validates active v20 and generic path/hash failure cases.",
    ),
    "docs/README.md": (
        "fta-v20-doc-index", "current_truth_index", "current", "Points to active FTA baseline v20 and the bounded NASA battery Dev case.",
    ),
    "docs/current-state-audit.md": (
        "fta-v20-current-state-audit", "current_state_document", "current", "Records one seen development case; model inference, Final, and readiness remain false.",
    ),
    "docs/acceptance.md": (
        "fta-v20-acceptance-record", "acceptance_document", "current", "Records packet/GOLD contract tests, manifest regeneration, hash validation, and unchanged production/readiness boundaries.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v20-candidate-generation-policy", "candidate_fta_policy_document", "current", "Points to v20 and records the one-case source-text gate assessment limits.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v20-validation-plan-policy", "validation_plan_document", "current", "Records the seen Dev sample and the remaining model-run/independent-Final gates.",
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
    previous = json.loads(V19_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v19":
        raise ValueError("v20 must extend the frozen v19 manifest snapshot")
    packet = json.loads((ROOT / PACKET).read_text(encoding="utf-8"))
    gold = json.loads((ROOT / GOLD).read_text(encoding="utf-8"))
    screen = json.loads((ROOT / SOURCE_SCREEN).read_text(encoding="utf-8"))
    if packet["packet_id"] != gold["packet_id"] or gold["packet_id"] != screen["model_gold_separation"]["packet_id"]:
        raise ValueError("packet, Gold, and source screen must identify the same case")
    if screen["evaluation_suitability"]["model_inference_run"] is not False:
        raise ValueError("the source case must not be represented as a model run")
    if screen["evaluation_suitability"]["eligible_for_independent_final"] is not False:
        raise ValueError("the seen source must remain ineligible for independent Final")
    if screen["evaluation_suitability"]["production_or_formal_gold_use_allowed"] is not False:
        raise ValueError("the development case cannot be promoted to production or formal Gold")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v20"
    manifest["baseline_version"] = "v20"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "one bounded, source-pinned NASA spacecraft battery Figure 7 event-scope development packet with a separate diagram-reference graph and text-authorized gate labels"
    )
    manifest["scope"]["excludes"].extend([
        "model inference, current-model accuracy/calibration claims, human expert signoff, formal Gold promotion, production FTA/API/database writes",
        "independent Final validation using the opened NASA battery report or its source family",
    ])
    manifest["active_baseline"]["event_scope_source_screen"] = "fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29"
    manifest["active_baseline"]["event_scope_dev_packet"] = packet["packet_id"]

    manifest["event_scope_packet_contract"] = {
        **manifest["event_scope_packet_contract"],
        "status": "populated_seen_development_only",
        "input_packet_count": 1,
        "reference_gold_count": 1,
        "model_inference_run": False,
        "production_api_changed": False,
        "dev_packet_path": PACKET,
        "reference_gold_path": GOLD,
        "source_screen_path": SOURCE_SCREEN,
        "diagram_reference_gate_count": len(gold["diagram_gates"]),
        "text_gate_review_status": sorted({item["review_provenance"]["review_status"] for item in gold["text_gate_reviews"]}),
        "text_gate_review_role": sorted({item["review_provenance"]["reviewer_role"] for item in gold["text_gate_reviews"]}),
        "text_authorized_gate_counts": {
            label: sum(item["text_authorized_gate"] == label for item in gold["text_gate_reviews"])
            for label in ("AND", "OR", "unknown")
        },
        "human_expert_reviewed": False,
        "ai_role_review_path": AI_REVIEW,
    }
    manifest["event_scope_dev_case"] = {
        "packet_id": packet["packet_id"],
        "source_cluster_id": packet["source_provenance"]["source_cluster_id"],
        "packet_path": PACKET,
        "reference_gold_path": GOLD,
        "source_screen_path": SOURCE_SCREEN,
        "source_document_sha256": packet["source_provenance"]["document_sha256"],
        "model_input_sha256": gold["model_input_sha256"],
        "event_scope_count": 1,
        "diagram_node_count": len(gold["nodes"]),
        "diagram_gate_count": len(gold["diagram_gates"]),
        "model_inference_run": False,
        "eligible_for_independent_final": False,
        "formal_gold": False,
        "production_or_database_write": False,
    }
    manifest["independent_final_validation"] = {
        **manifest["independent_final_validation"],
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "The NASA 1987 spacecraft battery report and Figure 7 were opened and allocated Dev-only. One source-text input packet, a separate reference graph, and an independent AI-role review exist, but no model inference or independent validation has run; source-family semantic overlap remains incomplete. This single event cannot establish accuracy, calibration, or generalization.",
    }
    allocation = manifest["source_cluster_allocation"]
    dev_cluster = packet["source_provenance"]["source_cluster_id"]
    if dev_cluster not in allocation["development_clusters"]:
        allocation["development_clusters"].append(dev_cluster)
    allocation["development_cluster_count"] = len(allocation["development_clusters"])
    if dev_cluster not in allocation["screened_seen_development_only_clusters"]:
        allocation["screened_seen_development_only_clusters"].append(dev_cluster)
    allocation["nasa_battery_fig7_seen_development_clusters"] = 1
    allocation["nasa_battery_fig7_dev_packets"] = 1
    allocation["nasa_battery_fig7_reference_gold"] = 1
    allocation["nasa_battery_fig7_final_eligible"] = False
    allocation["nasa_battery_fig7_semantic_overlap_audit_complete"] = False
    allocation["nasa_battery_fig7_allocation_note"] = "Assigned as one indivisible source-document cluster to development only; related-family semantic overlap review is incomplete."
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v19"],
        "current_version": "v20",
        "reason": "v20 adds exactly one seen-development event-scope input and separate reference artifact for NASA Figure 7; no model run, independent Final, formal Gold promotion, production write, or readiness change.",
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
        current = V20_PATH.read_text(encoding="utf-8") if V20_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v20 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v20",
            "dev_case_count": payload["event_scope_dev_case"]["event_scope_count"],
            "model_inference_run": payload["event_scope_dev_case"]["model_inference_run"],
            "final_status": payload["independent_final_validation"]["status"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V20_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V20_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
