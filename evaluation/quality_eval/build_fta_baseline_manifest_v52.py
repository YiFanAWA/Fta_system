#!/usr/bin/env python3
"""Build active FTA baseline v52 with an offline internal locator overlay."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.build_fta_baseline_manifest_v45 import _register, _sha256  # noqa: E402


V51_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v51.json"
V52_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v52.json"
EXPECTED_V51_SHA256 = "6c68c4edc96e028a26654886fb00613511defd7c3fcd625c77a3146f826caeb7"

ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v51.json": (
        "fta-baseline-manifest-v51-snapshot", "historical_baseline_manifest", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v51.py": (
        "fta-baseline-manifest-v51-builder", "reproducibility_tool", "historical",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v51.py": (
        "fta-baseline-manifest-v51-tests", "manifest_regression_tests", "historical",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v52.py": (
        "fta-baseline-manifest-v52-builder", "reproducibility_tool", "current",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v52.py": (
        "fta-baseline-manifest-v52-tests", "manifest_regression_tests", "current",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v52-default", "validation_tool", "current",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v52-default", "validation_tool_tests", "current",
    ),
    "backend-python/contracts/evidence_locator_review_contract.py": (
        "evidence-occurrence-locator-review-contract-v1", "internal_review_contract", "current",
    ),
    "backend-python/fta/evidence_locator_review_service.py": (
        "evidence-occurrence-locator-resolver-v1", "internal_evidence_binding_service", "current",
    ),
    "backend-python/contracts/fta_cause_disposition_contract.py": (
        "fta-cause-disposition-batch-contract-v3", "internal_artifact_contract", "current",
    ),
    "backend-python/fta/cause_disposition_service.py": (
        "fta-cause-disposition-service-v6", "internal_fta_service", "current",
    ),
    "backend-python/contracts/candidate_fta_contract.py": (
        "candidate-fta-tree-contract-v7", "internal_preview_contract", "current",
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "candidate-fta-extraction-service-locator-v1", "internal_preview_service", "current",
    ),
    "backend-python/fta/candidate_fta_application_service.py": (
        "candidate-fta-application-locator-forwarding-v1", "internal_application_service", "current",
    ),
    "backend-python/tests/test_fta_evidence_locator_review.py": (
        "evidence-occurrence-locator-tests-v1", "offline_contract_regression_tests", "current",
    ),
    "backend-python/tests/test_fta_cause_disposition.py": (
        "fta-cause-disposition-locator-regression-tests", "offline_service_regression_tests", "current",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-locator-regression-tests", "offline_service_regression_tests", "current",
    ),
    "backend-python/tests/test_candidate_fta_application_service.py": (
        "candidate-fta-application-locator-forwarding-tests", "offline_service_regression_tests", "current",
    ),
    "backend-python/tests/test_recursive_candidate_fta_extraction_service.py": (
        "recursive-candidate-fta-contract-v7-tests", "offline_contract_regression_tests", "current",
    ),
    "docs/README.md": ("fta-v52-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": ("fta-v52-current-state-audit", "current_state_document", "current"),
    "docs/fta-validation-reliability-plan-v1.md": ("fta-v52-validation-plan", "active_validation_plan", "current"),
    "docs/acceptance.md": ("fta-v52-acceptance-record", "acceptance_document", "current"),
    "docs/candidate-fta-generation-v1.md": ("fta-v52-candidate-generation-policy", "current_fta_policy_document", "current"),
}


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object at {path}")
    return payload


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V51_PATH) != EXPECTED_V51_SHA256:
        raise ValueError("v51 snapshot hash changed; refusing to derive v52")
    source = _load_json(V51_PATH)
    if source.get("manifest_id") != "candidate_fta_research_baseline_v51":
        raise ValueError("v52 must derive from the preserved v51 snapshot")
    baseline = source.get("active_baseline", {})
    plan = source.get("next_stage_plan_v1", {})
    if baseline.get("fta_ready") is not False or baseline.get("production_ready") is not False:
        raise ValueError("v52 must preserve false global readiness")
    if plan.get("p2_current_run_status") != "blocked" or plan.get("p2_semantic_defects_closed") != 0:
        raise ValueError("v52 must preserve the blocked historical F30021 run and zero semantic closures")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v52"
    manifest["baseline_version"] = "v52"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V51_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V51_SHA256,
        "reason": "Adds an internal, source-pinned occurrence-locator review overlay with offline fail-closed regressions; no model run, public API, database, Gold, historical response, or readiness change.",
    }
    manifest["scope"]["includes"].append(
        "internal occurrence-locator review overlay with source hash, record/field/index identity, exact offsets, unique scope validation, provenance preservation, and explicit service pass-through"
    )
    manifest["scope"]["excludes"].append(
        "public/API exposure, database persistence, formal Gold or human-expert promotion, semantic acceptance, applying a locator to immutable historical model output, and readiness promotion"
    )
    manifest["active_baseline"].update({
        "cause_disposition_prompt_version": "fta-cause-disposition-v6",
        "locator_review_contract": "EvidenceOccurrenceLocatorReview-v1",
        "locator_review_resolver": "EvidenceLocatorReviewResolver-v1",
        "locator_review_overlay_status": "implemented_and_offline_verified_internal_only",
        "latest_real_source_development_run": "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json",
        "latest_real_source_development_run_status": "blocked_immutable_historical_v5_not_replayed_with_locator_overlay",
        "latest_real_source_semantic_acceptance": False,
        "fta_ready": False,
        "production_ready": False,
    })

    current_plan = manifest.setdefault("next_stage_plan_v1", {})
    current_plan.update({
        "path": "docs/fta-validation-reliability-plan-v1.md",
        "status": "in_progress_internal_locator_overlay_offline_verified_live_semantics_pending",
        "p2_current_cause_disposition_prompt_version": "fta-cause-disposition-v6",
        "p2e_locator_overlay_contract_status": "implemented_offline_verified_internal_only",
        "p2e_locator_overlay_contract": "backend-python/contracts/evidence_locator_review_contract.py",
        "p2e_locator_resolver": "backend-python/fta/evidence_locator_review_service.py",
        "p2e_locator_review_metadata_serialized": True,
        "p2e_review_is_formal_gold": False,
        "p2e_model_requests_performed": 0,
        "p2e_public_api_changed": False,
        "p2e_database_changed": False,
        "p2e_gold_changed": False,
        "p2e_historical_run_rewritten": False,
        "p2e_semantic_defects_closed": 0,
        "p2e_next_action": "after separate explicit authorization, run a new bounded real-source preview; preserve v5 raw output and separately audit repeated-cause binding, top-event identity, child-set completeness, relations, scope evidence, and gate policy",
        "runtime_behavior_changed": True,
        "gold_or_database_changed": False,
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v51"],
        "current_version": "v52",
        "reason": "v52 records internal explicit locator-overlay wiring and offline contract verification; the historical F30021 run remains unchanged and blocked, and no semantic defect/readiness is promoted.",
    })

    for relative_path, (artifact_id, kind, lifecycle) in ARTIFACTS.items():
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v52 tracks only internal occurrence locator review and offline verification; no public API, database, Gold, historical run, or readiness change.",
        })

    repo_root = ROOT.resolve(strict=True)
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id, relative_path = artifact["artifact_id"], artifact["path"]
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact identity: {artifact_id} / {relative_path}")
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
        if not V52_PATH.exists() or V52_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v52 differs from generated content\n")
        status = "current"
    else:
        V52_PATH.write_text(rendered, encoding="utf-8", newline="\n")
        status = "written"
    print(json.dumps({
        "status": status,
        "baseline_version": "v52",
        "artifact_count": len(payload["artifacts"]),
        "locator_overlay": payload["next_stage_plan_v1"]["p2e_locator_overlay_contract_status"],
        "semantic_defects_closed": payload["next_stage_plan_v1"]["p2e_semantic_defects_closed"],
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
