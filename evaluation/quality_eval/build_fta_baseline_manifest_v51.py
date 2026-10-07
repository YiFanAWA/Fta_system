#!/usr/bin/env python3
"""Build active FTA baseline v51 with offline F30021 locator reconciliation."""

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


V50_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v50.json"
V51_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v51.json"
EXPECTED_V50_SHA256 = "95ac10426235ddadd51f876147b22f93130576722dda5134a1c27ad57a5b7868"

RECONCILIATION_JSON = "evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.json"
RECONCILIATION_MD = "evaluation/quality_eval/runs/fta_f30021_occurrence_review_reconciliation_v1_2026-10-07.md"

ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v50.json": ("fta-baseline-manifest-v50-snapshot", "historical_baseline_manifest", "historical"),
    "evaluation/quality_eval/build_fta_baseline_manifest_v50.py": ("fta-baseline-manifest-v50-builder", "reproducibility_tool", "historical"),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v50.py": ("fta-baseline-manifest-v50-tests", "manifest_regression_tests", "historical"),
    "evaluation/quality_eval/build_fta_baseline_manifest_v51.py": ("fta-baseline-manifest-v51-builder", "reproducibility_tool", "current"),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v51.py": ("fta-baseline-manifest-v51-tests", "manifest_regression_tests", "current"),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-v51-default", "validation_tool", "current"),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": ("fta-baseline-manifest-validator-tests-v51-default", "validation_tool_tests", "current"),
    "evaluation/quality_eval/public_sources/reconcile_f30021_occurrence_review_v1.py": ("f30021-occurrence-review-reconciler-v1", "offline_reconciliation_tool", "current"),
    "evaluation/quality_eval/public_sources/test_reconcile_f30021_occurrence_review_v1.py": ("f30021-occurrence-review-reconciliation-tests-v1", "offline_reconciliation_tests", "current"),
    RECONCILIATION_JSON: ("f30021-occurrence-review-reconciliation-v1-json", "engineering_audit_artifact", "current"),
    RECONCILIATION_MD: ("f30021-occurrence-review-reconciliation-v1-report", "engineering_audit_report", "current"),
    "evaluation/quality_eval/runs/siemens_s210_F30021_C04_locator_ai_review_v1_2026-09-27.json": ("f30021-c04-ai-locator-review-source", "historical_ai_review_artifact", "historical"),
    "evaluation/quality_eval/datasets/siemens_s210_public_fault_corpus_v1.jsonl": ("siemens-s210-public-fault-corpus-v1", "source_corpus", "current"),
    "docs/README.md": ("fta-v51-doc-index", "current_truth_index", "current"),
    "docs/current-state-audit.md": ("fta-v51-current-state-audit", "current_state_document", "current"),
    "docs/acceptance.md": ("fta-v51-acceptance-record", "acceptance_document", "current"),
    "docs/fta-validation-reliability-plan-v1.md": ("fta-v51-validation-plan", "active_validation_plan", "current"),
    "docs/candidate-fta-generation-v1.md": ("fta-v51-candidate-generation-policy", "current_fta_policy_document", "current"),
}


def _load_json(relative_path: str) -> dict:
    payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {relative_path}")
    return payload


def build_manifest(*, captured_at: str | None = None) -> dict:
    if _sha256(V50_PATH) != EXPECTED_V50_SHA256:
        raise ValueError("v50 snapshot hash changed; refusing to derive v51")
    source = _load_json("evaluation/quality_eval/fta_baseline_manifest_v50.json")
    if source.get("manifest_id") != "candidate_fta_research_baseline_v50":
        raise ValueError("v51 must derive from the preserved v50 snapshot")
    if source.get("active_baseline", {}).get("fta_ready") is not False or source.get("active_baseline", {}).get("production_ready") is not False:
        raise ValueError("v51 must preserve false global readiness")

    reconciliation = _load_json(RECONCILIATION_JSON)
    expected = {
        "artifact_type": "fta_f30021_occurrence_review_reconciliation",
        "artifact_version": "v1",
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "model_requests_performed": 0,
    }
    if any(reconciliation.get(key) != value for key, value in expected.items()):
        raise ValueError("F30021 reconciliation artifact has an unexpected provenance/readiness state")
    checks = reconciliation.get("reconciliation_result", {})
    run = reconciliation.get("latest_raw_run", {})
    if (
        checks.get("scope_and_offsets_consistent") is not True
        or checks.get("prior_locator_decision_applied_to_latest_run") is not False
        or checks.get("latest_raw_run_remains_blocked") is not True
        or checks.get("semantic_defects_closed") != 0
        or run.get("current_disposition") != "unresolved"
        or run.get("current_disposition_evidence") != []
        or run.get("tree_status") != "blocked"
        or run.get("gate") != "unknown"
        or run.get("cause_set_complete") is not False
    ):
        raise ValueError("F30021 reconciliation must preserve unresolved/blocked and unknown gate state")
    if reconciliation.get("locator_review", {}).get("reviewer_is_human_expert") is not False:
        raise ValueError("AI locator provenance must not be promoted to human expert review")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v51"
    manifest["baseline_version"] = "v51"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": source["manifest_id"],
        "path": V50_PATH.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_V50_SHA256,
        "reason": "Adds an offline, source-pinned reconciliation of the existing AI locator review against the F30021 raw v5 run; the decision is not applied, the run stays blocked, and no semantic defect or readiness is promoted.",
    }
    manifest["scope"]["includes"].append(
        "offline reconciliation of F30021-C04 duplicate quote occurrences, unique Possible causes scope, historical AI locator review provenance, and unchanged current raw-run blocker state"
    )
    manifest["scope"]["excludes"].append(
        "applying the prior locator choice to the immutable v5 run, shared evidence/API contract changes, human expert signoff, formal Gold, model accuracy, and readiness promotion"
    )
    manifest["active_baseline"].update({
        "latest_real_source_development_run": "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_current_prompt_v5_2026-10-07.json",
        "latest_real_source_development_run_status": "blocked_on_ambiguous_evidence_and_incomplete_child_set",
        "latest_real_source_semantic_acceptance": False,
        "latest_locator_reconciliation": RECONCILIATION_JSON,
        "latest_locator_reconciliation_status": "scope_and_offsets_consistent_not_applied_to_raw_run",
        "fta_ready": False,
        "production_ready": False,
    })

    plan = manifest.setdefault("next_stage_plan_v1", {})
    plan.update({
        "path": "docs/fta-validation-reliability-plan-v1.md",
        "status": "in_progress_P2_occurrence_scope_reconciled_runtime_consumption_and_other_blockers_pending",
        "p2_occurrence_review_reconciliation_status": "passed_offline_scope_hash_and_offset_checks_not_applied_to_latest_raw_run",
        "p2_occurrence_review_reconciliation_artifact": RECONCILIATION_JSON,
        "p2_occurrence_review_regression_test_count": 7,
        "p2_semantic_defects_closed": 0,
        "p2_current_run_status": "blocked",
        "p2_shared_evidence_contract_changed": False,
        "p2_next_action": "design the audit-to-runtime consumption boundary and separately address top-event ambiguity, incomplete child set, and unavailable gate confidence policy; no new model request without fresh explicit authorization",
        "runtime_behavior_changed": False,
        "gold_or_database_changed": False,
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v50"],
        "current_version": "v51",
        "reason": "v51 records offline reconciliation of the historical C04 locator review; the decision is not consumed by the latest raw run and all blockers/readiness remain unchanged.",
    })

    for relative_path, (artifact_id, kind, lifecycle) in ARTIFACTS.items():
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "note": "v51 pins F30021 locator reconciliation without applying the historical decision or changing shared contracts, Gold, or readiness.",
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
        if not V51_PATH.exists() or V51_PATH.read_text(encoding="utf-8") != rendered:
            parser.exit(1, "FTA baseline manifest v51 differs from generated content\n")
        status = "current"
    else:
        V51_PATH.write_text(rendered, encoding="utf-8", newline="\n")
        status = "written"
    print(json.dumps({
        "status": status,
        "baseline_version": "v51",
        "artifact_count": len(payload["artifacts"]),
        "fta_ready": payload["active_baseline"]["fta_ready"],
        "production_ready": payload["active_baseline"]["production_ready"],
        "p2_current_run": payload["next_stage_plan_v1"]["p2_current_run_status"],
        "p2_locator_reconciliation": payload["next_stage_plan_v1"]["p2_occurrence_review_reconciliation_status"],
        "p2_semantic_defects_closed": payload["next_stage_plan_v1"]["p2_semantic_defects_closed"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
