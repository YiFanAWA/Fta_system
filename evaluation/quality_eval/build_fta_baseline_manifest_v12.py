#!/usr/bin/env python3
"""Build the v12 FTA baseline with an offline top-event-restatement boundary."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V11_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v11.json"
V12_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v12.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v11.json": (
        "fta-baseline-manifest-v11-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v11 snapshot; records the historical F01681 v3 online development replay.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v3-live-run", "online_model_development_probe", "historical_development_evidence",
        "Historical v3 replay preserved unchanged; it is not a v4 run or semantic pass.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v3_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v3-live-run-report", "online_model_development_report", "historical_development_evidence",
        "Historical report for the v3 replay; not evidence of v4 model behavior.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v3-ai-review", "independent_ai_role_review", "historical_development_review",
        "Historical read-only AI role review; flags possible top-event restatement and is not human expert approval.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v3_independent_ai_review_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v3-ai-review-report", "independent_ai_role_review_report", "historical_development_review",
        "Historical AI role-review report; no expert sign-off or v4 model result.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v12.py": (
        "fta-baseline-manifest-v12-builder", "reproducibility_tool", "current",
        "Builds v12 from immutable v11 and records only the offline prompt/contract regression.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v12.py": (
        "fta-baseline-manifest-v12-tests", "manifest_regression_tests", "current",
        "Checks the v11 snapshot, v4 boundary status, actual hashes, and unchanged readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v12-default", "validation_tool", "current",
        "Validates manifest paths and hashes; defaults to the active v12 snapshot.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v12-default", "validation_tool_tests", "current",
        "Verifies manifest validation and the active v12 baseline.",
    ),
    "backend-python/fta/cause_disposition_service.py": (
        "fta-cause-disposition-v4-service", "semantic_policy_owner", "current",
        "Compares each cause proposition to top_event; pure restatements are summaries, not independent tree events.",
    ),
    "backend-python/tests/test_fta_cause_disposition.py": (
        "fta-cause-disposition-v4-tests", "semantic_policy_regression_tests", "current",
        "Covers top-event paraphrase, independent candidate preservation, evidence, and fail-closed role guards.",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-cause-edge-policy-v4-tests", "candidate_fta_contract_tests", "current",
        "Checks the candidate service consumes the active v4 cause-disposition prompt and preserves mapping boundaries.",
    ),
    "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py": (
        "candidate-fta-raw-source-probe-v4-tests", "model_probe_regression_tests", "current",
        "Asserts newly built artifacts identify the active v4 cause-disposition prompt.",
    ),
    "docs/README.md": (
        "fta-v12-doc-index", "current_truth_index", "current", "Points to active FTA baseline v12.",
    ),
    "docs/current-state-audit.md": (
        "fta-v12-current-state-audit", "current_state_document", "current",
        "Records the offline cause-vs-top-event refinement and keeps FTA readiness closed.",
    ),
    "docs/acceptance.md": (
        "fta-v12-acceptance-record", "acceptance_document", "current",
        "Records the offline v4 regressions and active manifest checks; no new model call.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v12-candidate-generation-policy", "candidate_fta_policy_document", "current",
        "Documents cause v4: a restatement of top_event does not create an independent candidate edge.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v12-validation-plan-policy", "validation_plan_document", "current",
        "Tracks the top-event restatement finding and offline-only acceptance evidence.",
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


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V11_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v11":
        raise ValueError("v12 must extend the frozen v11 manifest snapshot")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v12"
    manifest["baseline_version"] = "v12"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "cause disposition v4 compares each cause proposition with the top event; paraphrase/definition without distinct upstream information is a summary, not an independent tree event"
    )
    manifest["scope"]["excludes"].append(
        "online-model semantic accuracy for prompt v4, expert Gold, database writes, production integration, gate calibration, and FTA readiness"
    )
    manifest["active_baseline"]["cause_disposition_prompt"] = "fta-cause-disposition-v4"
    manifest["active_baseline"]["historical_f01681_v3_development_run"] = manifest["active_baseline"].pop(
        "f01681_v3_development_run"
    )
    manifest["active_baseline"]["f01681_v4_online_model_replay"] = None
    manifest["active_baseline"]["cause_disposition_policy_regression"] = (
        "compare_cause_proposition_to_top_event; pure_restatement_is_summary_relation_only; ambiguous_is_unresolved"
    )
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v11"],
        "current_version": "v12",
        "reason": "v12 adds an offline-only cause-vs-top-event-restatement policy regression; v11 and its online v3 replay remain immutable historical evidence.",
    })
    manifest["cause_disposition_v4_policy_regression"] = {
        "status": "offline_prompt_and_contract_regression_passed",
        "prompt_version": "fta-cause-disposition-v4",
        "policy": {
            "independent_upstream_condition_or_mechanism": "may_remain_an_ai_proposed_candidate_when_directly_source_supported",
            "top_event_paraphrase_or_definition_without_new_upstream_information": "causal_summary_and_relation_only_with_summary_not_independent_event",
            "semantic_ambiguity": "unresolved_with_semantic_role_uncertain",
            "diagnostic_mapping": "unchanged_relation_only_unless_separate_direct_causal_evidence_exists",
        },
        "offline_regressions": [
            "backend-python/tests/test_fta_cause_disposition.py::test_top_event_restatement_can_be_recorded_as_summary_not_tree_event",
            "backend-python/tests/test_fta_cause_disposition.py::test_host_downgrades_top_event_summary_mislabelled_as_tree_candidate",
            "backend-python/tests/test_fta_cause_disposition.py::test_proposes_total_indexed_ledger_and_preserves_source_text",
            "backend-python/tests/test_candidate_fta_extraction_service.py",
            "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py",
        ],
        "online_model_rerun": False,
        "v3_online_replay_preserved_unchanged": True,
        "formal_gold": False,
        "database_written": False,
        "accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    }

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
        current = V12_PATH.read_text(encoding="utf-8") if V12_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v12 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v12",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V12_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V12_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
