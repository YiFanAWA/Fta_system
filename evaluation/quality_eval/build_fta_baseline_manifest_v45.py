#!/usr/bin/env python3
"""Build active FTA baseline v45 with reconciled review-scope accounting."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V44_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v44.json"
V45_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v45.json"
EXPECTED_V44_SHA256 = "3facadb17917ad2077e6d8190102f5e16a2fd8fe533be5b262420c85edef7ee5"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v44.json": (
        "fta-baseline-manifest-v44-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v44 snapshot; superseded as active by v45 review-scope reconciliation.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v44.py": (
        "fta-baseline-manifest-v44-builder", "reproducibility_tool", "historical",
        "Historical builder for v44; retained for reproducibility.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v44.py": (
        "fta-baseline-manifest-v44-tests", "manifest_regression_tests", "historical",
        "Historical v44 baseline tests.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v45.py": (
        "fta-baseline-manifest-v45-builder", "reproducibility_tool", "current",
        "Builds v45 from immutable v44 and records non-additive review scopes without promoting readiness.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v45.py": (
        "fta-baseline-manifest-v45-tests", "manifest_regression_tests", "current",
        "Protects v44 immutability, scope counts, provenance separation, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v45-default", "validation_tool", "current",
        "Validates active v45 by default; historical manifests remain selectable explicitly.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v45-default", "validation_tool_tests", "current",
        "Covers manifest integrity and active v45 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v45-doc-index", "current_truth_index", "current",
        "Points to v45 and names v44 as an immutable historical snapshot.",
    ),
    "docs/current-state-audit.md": (
        "fta-v45-current-state-audit", "current_state_document", "current",
        "Reconciles named-expert causal Gold, AI review, event-scope, gate-node, and provisional view counts.",
    ),
    "docs/acceptance.md": (
        "fta-v45-acceptance-record", "acceptance_document", "current",
        "Records v45 scope-reconciliation tests, deterministic build, and active artifact hash validation.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v45-validation-plan-status", "active_validation_plan", "current",
        "Records completed offline role-contract regression and pending separately authorized live validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v45-candidate-generation-policy", "current_fta_policy_document", "current",
        "Points to reconciled v45 and retains disconnected-observation/fail-closed policy.",
    ),
    "docs/causal-relation-gold-v1.md": (
        "fta-v45-causal-gold-scope-reference", "review_scope_reference", "current",
        "Named-review causal Gold scope and exclusions; not merged with AI-role review.",
    ),
    "docs/siemens-s210-ai-authorized-review-v1.md": (
        "fta-v45-ai-review-scope-reference", "review_scope_reference", "current",
        "AI-authorized event/candidate audit coverage and its non-Gold boundary.",
    ),
    "evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v7.json": (
        "siemens-s210-causal-relation-gold-v7", "named-review-gold", "current",
        "205 approved causal relations; 296 documented decisions in scope; not full-corpus review.",
    ),
    "evaluation/quality_eval/datasets/siemens_s210_causal_relation_gold_v7_ai_provisional.json": (
        "siemens-s210-causal-relation-gold-v7-ai-provisional", "non_gold_provisional_view", "current",
        "Overlapping provisional view; includes 2 AI-proposed relations and is not additive to formal Gold.",
    ),
    "evaluation/quality_eval/datasets/siemens_s210_and_or_logic_gold_v1.json": (
        "siemens-s210-and-or-logic-gold-v1", "named-review-logic-gold", "current",
        "Six named-review events: five OR and one unknown; no AND example.",
    ),
    "evaluation/quality_eval/datasets/siemens_s210_gate_node_review_dataset_v6_locator_reconciled_ai_role_review.json": (
        "siemens-s210-gate-node-review-v6", "ai_role_review_dataset", "current",
        "55 AI-role-reviewed gate nodes; not human Gold or production authorization.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_event_scope_gate_primary_ai_role_review_v8_2026-09-27.json": (
        "siemens-s210-event-scope-review-v8", "ai_role_review_artifact", "current",
        "39 selected event-cause scopes; separate from the 281-event aggregate and 55 gate-node set.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_causal_event_gate_review_consolidated_v1_2026-09-26.json": (
        "siemens-s210-ai-review-consolidated-v1", "ai_role_review_aggregate", "current",
        "98 AI-role batches covering 281 events and 1041 candidate IDs; not formal Gold.",
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


def _review_scope_reconciliation() -> dict[str, Any]:
    return {
        "artifact_version": "v1",
        "rule": "Review scopes use different populations and provenance; never sum them into one reviewed count.",
        "source_universe": {"fault_record_count": 281, "cause_candidate_count": 1041},
        "tracks": {
            "named_expert_causal_gold_v7": {
                "reviewer_provenance": "named_reviewer_as_recorded_in_source_artifacts",
                "formal_gold": True,
                "decision_count": 296,
                "approved_relation_count": 205,
                "excluded_or_pending_count": 91,
                "excluded_or_pending_decisions": {"revise": 40, "cannot_determine": 40, "reject": 11},
                "unreviewed_candidate_count": 745,
                "validation_scope": "reviewed_candidates_only",
                "counts_partition_source_candidates": True,
            },
            "named_expert_and_or_gold_v1": {
                "reviewer_provenance": "named_reviewer_as_recorded_in_source_artifact",
                "formal_gold": True,
                "event_count": 6,
                "gate_counts": {"AND": 0, "OR": 5, "unknown": 1},
                "logic_gates_complete": False,
            },
            "ai_authorized_batches_02_99": {
                "reviewer_is_human_expert": False,
                "formal_gold": False,
                "batch_count": 98,
                "unique_event_count": 281,
                "duplicate_event_count": 0,
                "unique_candidate_count": 1041,
                "duplicate_candidate_count": 0,
                "event_gate_counts": {"AND": 0, "OR": 17, "not_applicable": 60, "unknown": 204},
                "candidate_category_counts": {
                    "causal": 707,
                    "causal_summary": 137,
                    "associated_only": 175,
                    "cannot_determine": 18,
                    "causal_trigger_condition": 1,
                    "diagnostic_subtype": 1,
                    "not_supported": 2,
                },
                "build_allowed_event_count": 11,
                "build_blocked_event_count": 270,
                "database_written": False,
            },
            "event_scope_primary_review_v8": {
                "reviewer_is_human_expert": False,
                "formal_gold": False,
                "scope_count": 39,
                "reviewed_count": 37,
                "not_applicable_count": 2,
                "pending_count": 0,
                "gate_counts_reviewed_only": {"AND": 0, "OR": 1, "unknown": 36},
            },
            "gate_node_review_v6": {
                "reviewer_is_human_expert": False,
                "formal_gold": False,
                "gate_node_count": 55,
                "reviewed_count": 55,
                "pending_count": 0,
                "unique_fault_count": 47,
                "source_cluster_count": 48,
                "gate_counts": {"AND": 12, "OR": 17, "unknown": 26},
                "companion_non_gate_scope_count": 5,
            },
            "causal_gold_v7_ai_provisional_view": {
                "reviewer_is_human_expert": False,
                "formal_gold": False,
                "candidate_scope_count": 246,
                "relation_count": 165,
                "preexisting_named_review_relation_count": 163,
                "ai_provisional_relation_count": 2,
                "excluded_or_pending_count": 81,
                "overlaps_formal_gold": True,
                "additive_to_other_tracks": False,
            },
        },
        "global_readiness": {"fta_ready": False, "production_ready": False},
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    if _sha256(V44_PATH) != EXPECTED_V44_SHA256:
        raise ValueError("v44 historical snapshot hash changed; refusing to derive v45")
    source = json.loads(V44_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v44":
        raise ValueError("v45 must derive from the preserved v44 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v45 must preserve false FTA and production readiness")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v45"
    manifest["baseline_version"] = "v45"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v44",
        "path": V44_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V44_SHA256,
        "reason": "v45 establishes a non-additive reconciliation of named-review Gold, AI-role review, event-scope review, and gate-node review counts; no Gold or runtime behavior is changed.",
    }
    manifest["scope"]["includes"].append(
        "verified non-additive review-scope reconciliation for causal Gold, logic Gold, AI-authorized aggregate review, event-scope review, gate-node review, and AI provisional view"
    )
    manifest["scope"]["excludes"].append(
        "new live-model validation, semantic accuracy claims, Gold/database writes, production API changes, and readiness promotion"
    )
    manifest["review_scope_reconciliation_v1"] = _review_scope_reconciliation()
    manifest["active_baseline"].update({
        "review_scope_reconciliation_version": "v1",
        "cause_semantic_role_contract_status": "implemented_offline_regression_passed",
        "detached_observation_live_validation": "pending_explicit_request_authorization",
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v44"],
        "current_version": "v45",
        "reason": "v45 clarifies the current review-scope ledgers and records offline regression evidence; v44 remains immutable history.",
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
            raise ValueError(f"artifact path escapes repository: {relative_path}")
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
        current = V45_PATH.read_text(encoding="utf-8") if V45_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v45 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v45",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V45_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "baseline_version": "v45",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
