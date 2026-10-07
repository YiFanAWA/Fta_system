#!/usr/bin/env python3
"""Build a scoped FTA readiness assessment from the immutable v15 baseline."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v15.json"
REPORT_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_scoped_readiness_assessment_v1_2026-09-28.json"
BASELINE_RELATIVE_PATH = "evaluation/quality_eval/fta_baseline_manifest_v15.json"
REPORT_RELATIVE_PATH = "evaluation/quality_eval/runs/fta_scoped_readiness_assessment_v1_2026-09-28.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dataset_artifact(dataset: dict[str, Any]) -> dict[str, Any]:
    path = dataset.get("dataset_path")
    if not isinstance(path, str):
        raise ValueError("baseline dataset suite is missing dataset_path")
    target = (ROOT / path).resolve(strict=True)
    if not target.is_relative_to(ROOT.resolve(strict=True)):
        raise ValueError(f"dataset path escapes repository: {path}")
    actual_hash = _sha256(target)
    if actual_hash != dataset.get("dataset_sha256"):
        raise ValueError(f"dataset hash differs from pinned baseline: {path}")
    return {
        "dataset_path": path,
        "dataset_sha256": actual_hash,
        "case_count": dataset.get("sample_count"),
    }


def _source_cluster(source: dict[str, Any], *, allocation_set_id: str) -> dict[str, str]:
    source_hash = source.get("source_sha256") or source.get("source_pdf_sha256")
    hash_type = source.get("source_hash_type") or ("source_pdf_sha256" if source.get("source_pdf_sha256") else None)
    if not isinstance(source_hash, str) or not isinstance(hash_type, str):
        raise ValueError("source cluster must carry a source hash and hash type")
    return {
        "source_id": source["source_id"],
        "source_cluster_id": source["source_cluster_id"],
        "source_hash_type": hash_type,
        "source_sha256": source_hash,
        "allocation_set_id": allocation_set_id,
    }


def _criterion(criterion_id: str, result: str, *evidence_refs: str) -> dict[str, Any]:
    return {"criterion_id": criterion_id, "result": result, "evidence_refs": list(evidence_refs)}


def build_report(*, assessed_at: str | None = None) -> dict[str, Any]:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    if baseline.get("manifest_id") != "candidate_fta_research_baseline_v15":
        raise ValueError("readiness report v1 must be assessed against the frozen v15 manifest")

    regression_id = "fta_gate_contract_boundary_regression_v1"
    development_id = "public-diagram-gate-development-v1"
    regression = baseline.get("seen_case_regression_suite")
    development = baseline.get("development_gate_suite")
    if not isinstance(regression, dict) or regression.get("suite_id") != regression_id:
        raise ValueError("v15 baseline is missing the expected seen-case regression suite")
    if not isinstance(development, dict) or development.get("suite_id") != development_id:
        raise ValueError("v15 baseline is missing the expected development suite")

    regression_sources = regression.get("source_clusters")
    development_sources = development.get("source_clusters")
    if not isinstance(regression_sources, list) or not isinstance(development_sources, list):
        raise ValueError("both included sets must provide source cluster inventories")
    regression_clusters = [_source_cluster(item, allocation_set_id=regression_id) for item in regression_sources]
    development_clusters = [_source_cluster(item, allocation_set_id=development_id) for item in development_sources]
    sources = regression_clusters + development_clusters
    if len({item["source_cluster_id"] for item in sources}) != len(sources):
        raise ValueError("included source clusters overlap or are duplicated")

    regression_datasets = regression.get("dataset_suites")
    if not isinstance(regression_datasets, list):
        raise ValueError("regression suite must provide dataset_suites")
    regression_artifacts = [_dataset_artifact(item) for item in regression_datasets]
    development_dataset_sha = next(
        (
            artifact.get("sha256")
            for artifact in baseline.get("artifacts", [])
            if artifact.get("path") == development.get("dataset_path")
        ),
        None,
    )
    if not isinstance(development_dataset_sha, str):
        raise ValueError("pinned v15 manifest is missing the development dataset artifact hash")
    development_artifacts = [{
        "dataset_path": development["dataset_path"],
        "dataset_sha256": _sha256((ROOT / development["dataset_path"]).resolve(strict=True)),
        "case_count": development["sample_count"],
    }]
    if development_artifacts[0]["dataset_sha256"] != development_dataset_sha:
        raise ValueError("development dataset hash differs from v15 baseline artifact")

    baseline_hash = _sha256(BASELINE_PATH)
    baseline_ref = BASELINE_RELATIVE_PATH
    regression_case_count = regression.get("sample_count")
    development_case_count = development.get("sample_count")
    if sum(item["case_count"] for item in regression_artifacts) != regression_case_count:
        raise ValueError("regression dataset counts do not account for all frozen cases")

    return {
        "schema": "fta_scoped_readiness_report_v1",
        "assessment_id": "fta_scoped_readiness_assessment_v1_2026-09-28",
        "assessed_at": assessed_at or date.today().isoformat(),
        "baseline": {
            "manifest_id": baseline["manifest_id"],
            "version": baseline["baseline_version"],
            "path": BASELINE_RELATIVE_PATH,
            "sha256": baseline_hash,
        },
        "scope": {
            "scope_id": "fta_v15_seen_regression_and_public_diagram_development",
            "domain": "cross-source FTA gate evidence and contract evaluation",
            "description": (
                "Only the 36 seen-case fixture/contract/evidence-boundary regression cases and 11 public-diagram "
                "development cases are assessed. This is not current-model accuracy, complete causal-structure, "
                "full S210, independent-final, or production acceptance."
            ),
            "inclusion_rule": "Include exactly the two pinned sets below; do not generalize their results outside this scope.",
            "case_count": regression_case_count + development_case_count,
            "source_cluster_count": len(sources),
            "included_sets": [
                {
                    "set_id": regression_id,
                    "role": "seen_case_contract_boundary_regression_not_model_accuracy",
                    "case_count": regression_case_count,
                    "source_cluster_count": len(regression_clusters),
                    "source_cluster_ids": [item["source_cluster_id"] for item in regression_clusters],
                    "dataset_artifacts": regression_artifacts,
                    "manifest_ref": f"{baseline_ref}#/seen_case_regression_suite",
                },
                {
                    "set_id": development_id,
                    "role": "public_diagram_development_not_raw_text_fta_validation",
                    "case_count": development_case_count,
                    "source_cluster_count": len(development_clusters),
                    "source_cluster_ids": [item["source_cluster_id"] for item in development_clusters],
                    "dataset_artifacts": development_artifacts,
                    "manifest_ref": f"{baseline_ref}#/development_gate_suite",
                },
            ],
            "excluded_sets": [
                {
                    "set_id": "independent_final_validation",
                    "status": "not_created",
                    "case_count": 0,
                    "source_cluster_count": 0,
                    "reason": "All currently acquired source documents are allocated to regression or development; no independent Final source is available.",
                },
                {
                    "set_id": "live_model_gate_behavior_evaluation",
                    "status": "not_run",
                    "case_count": 0,
                    "source_cluster_count": 0,
                    "reason": "This report audits evidence availability and readiness only; no model inference was run.",
                },
                {
                    "set_id": "real_device_probability_observations",
                    "status": "not_available",
                    "case_count": 0,
                    "source_cluster_count": 0,
                    "reason": "No S210 field event-rate/probability dataset with exposure denominator and observation window is available.",
                },
            ],
            "source_clusters": sources,
            "scope_boundary_notes": [
                "The six-event named-human logic Gold is separately reported and is not part of the 47-case readiness denominator; it has zero AND examples and insufficient calibration support.",
                "AI-role event/gate reviews are not human expert Gold and do not become human-reviewed evidence in this report.",
                "The 11 development cases are already-labelled gates in public diagrams; they do not validate extraction of complete trees from raw fault text.",
                "Unknown, blocked, and excluded evidence is not removed from the declared scope to improve readiness status.",
            ],
            "source_split_policy": "Whole source documents/source clusters stay in one allocation; no case-level split is used.",
        },
        "assessment_provenance": {
            "method": "read_only_manifest_contract_and_acceptance_audit",
            "model_inference_run": False,
            "human_expert_reviewed": False,
            "reviewer_role": "engineering_audit",
            "reviewer_provenance": "primary_agent_read_only_audit_with_independent_ai_read_only_contract_review",
            "note": "This records readiness evidence and blockers; AI review is not represented as human domain-expert approval.",
        },
        "evaluation_configuration": {
            "candidate_contract": baseline["active_baseline"]["candidate_contract"],
            "cause_disposition_prompt": baseline["active_baseline"]["cause_disposition_prompt"],
            "model_inference_status": "not_run",
            "model_id": None,
            "code_scope": "read-only evaluation of pinned baseline and its artifacts; no runtime/API path was exercised",
        },
        "structure_readiness": {
            "status": "blocked",
            "criteria": [
                _criterion("scope_datasets_and_source_clusters_are_pinned", "met", f"{baseline_ref}#/seen_case_regression_suite", f"{baseline_ref}#/development_gate_suite"),
                _criterion("source_cluster_split_has_no_seen_regression_development_overlap", "met", f"{baseline_ref}#/development_gate_suite/overlap_with_seen_case_regression", f"{baseline_ref}#/source_cluster_allocation"),
                _criterion("candidate_model_currently_evaluated_on_the_declared_structure_scope", "unknown", f"{baseline_ref}#/seen_case_regression_suite/verification_scope", f"{baseline_ref}#/independent_final_validation"),
                _criterion("complete_cause_disposition_and_relation_connectivity_assessed_for_each_fault_tree_scope", "unknown", "docs/candidate-fta-generation-v1.md", "docs/fta-validation-reliability-plan-v1.md"),
                _criterion("direct_gate_evidence_and_complete_child_sets_reviewed_for_each_claimed_gate", "unknown", "docs/candidate-fta-generation-v1.md", f"{baseline_ref}#/label_and_evaluation_scope/human_logic_gold"),
                _criterion("reviewer_provenance_is_explicit_and_not_mislabeled_as_human", "met", f"{baseline_ref}#/label_and_evaluation_scope/event_scope_v8", f"{baseline_ref}#/label_and_evaluation_scope/gate_node_v6", f"{baseline_ref}#/label_and_evaluation_scope/human_logic_gold"),
                _criterion("preview_and_contract_boundary_tests_are_present", "met", "docs/acceptance.md", f"{baseline_ref}#/artifacts"),
            ],
            "blockers": [
                "no live model run evaluates the declared structure scope",
                "the declared sets do not contain complete raw-text causal structures for each fault-tree scope",
                "available gate labels do not provide sufficient class-complete calibration truth: the separate six-event named-human Gold has zero AND examples, while other review labels are explicitly AI-role or pre-labelled development data",
                "independent final source validation has not been created",
            ],
        },
        "quantitative_readiness": {
            "status": "blocked",
            "criteria": [
                _criterion("structure_readiness_is_met_in_the_same_scope", "unmet", f"{baseline_ref}#/active_baseline/fta_ready", f"{REPORT_RELATIVE_PATH}#/structure_readiness"),
                _criterion("real_event_rates_or_probabilities_have_exposure_denominators", "unmet", "docs/fta-validation-reliability-plan-v1.md", f"{baseline_ref}#/independent_final_validation"),
                _criterion("population_and_observation_window_are_defined", "unmet", "docs/fta-validation-reliability-plan-v1.md"),
                _criterion("event_dependencies_and_uncertainty_propagation_are_validated", "unknown", "docs/fta-validation-reliability-plan-v1.md"),
                _criterion("probability_calculation_is_verified_against_independent_examples", "unknown", "docs/fta-validation-reliability-plan-v1.md"),
            ],
            "blockers": [
                "structure readiness is blocked for the same declared scope",
                "real device event-rate/probability data, population denominator, and observation window are unavailable",
                "dependency assumptions, calculation validation, and uncertainty propagation have not been assessed",
            ],
        },
        "related_non_readiness_gaps": [
            {
                "gap_id": "fta_preview_fta_ready_flag_negative_test",
                "status": "resolved_in_current_worktree",
                "evidence_refs": [
                    "backend-python/contracts/fta_graph_contract.py",
                    "backend-python/tests/test_fta_graph_contract.py",
                ],
                "note": "The validator rejects dataset_info.fta_ready=true, and test_preview_cannot_be_marked_fta_ready directly asserts that rejection in the current worktree. This closes the contract-test coverage gap; it does not establish semantic FTA generation accuracy or readiness.",
            },
            {
                "gap_id": "gate_confidence_calibration",
                "status": "insufficient_evidence",
                "evidence_refs": [f"{baseline_ref}#/label_and_evaluation_scope/gate_node_split_v6/calibration_status", f"{baseline_ref}#/label_and_evaluation_scope/human_logic_gold"],
                "note": "Model gate confidence is a structural decision signal, not an event probability; it cannot satisfy quantitative readiness.",
            },
            {
                "gap_id": "independent_final_source_validation",
                "status": "not_created",
                "evidence_refs": [f"{baseline_ref}#/independent_final_validation"],
            },
        ],
        "global_readiness": {
            "fta_ready": False,
            "production_ready": False,
            "scope_can_promote_global_readiness": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessed-at", help="ISO date for deterministic generation")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    payload = build_report(assessed_at=args.assessed_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA scoped readiness report differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "assessment_id": payload["assessment_id"],
            "case_count": payload["scope"]["case_count"],
            "source_cluster_count": payload["scope"]["source_cluster_count"],
            "structure_status": payload["structure_readiness"]["status"],
            "quantitative_status": payload["quantitative_readiness"]["status"],
            "fta_ready": payload["global_readiness"]["fta_ready"],
            "production_ready": payload["global_readiness"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    REPORT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "path": str(REPORT_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
