#!/usr/bin/env python3
"""Build the v10 FTA baseline with the user-approved cause-to-event policy."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V9_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v9.json"
V10_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v10.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v9.json": (
        "fta-baseline-manifest-v9-snapshot",
        "baseline_manifest_snapshot",
        "superseded_snapshot",
        "Immutable v9 research-baseline snapshot; v10 is active.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v10.py": (
        "fta-baseline-manifest-v10-builder",
        "reproducibility_tool",
        "current",
        "Builds v10 from the immutable v9 snapshot and fingerprints current policy, tests and documentation.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v10.py": (
        "fta-baseline-manifest-v10-tests",
        "manifest_regression_tests",
        "current",
        "Checks v9 immutability, v3 policy declaration, artifact hashes and non-readiness boundaries.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v10-default",
        "validation_tool",
        "current",
        "Validates manifest artifacts and defaults to the active v10 snapshot.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v10-default",
        "validation_tool_tests",
        "current",
        "Verifies local manifest validation and the active v10 baseline fingerprints.",
    ),
    "backend-python/fta/cause_disposition_service.py": (
        "fta-cause-disposition-v3-service",
        "current_fta_policy_source",
        "current",
        "Cause disposition v3 separates explicit natural-language possible causes from diagnostic lookup mappings.",
    ),
    "backend-python/tests/test_fta_cause_disposition.py": (
        "fta-cause-disposition-v3-tests",
        "current_fta_policy_tests",
        "current",
        "Covers natural-language candidate allowance, mapping exclusion, evidence uniqueness and fail-closed classification.",
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "candidate-fta-cause-edge-policy-v3",
        "current_fta_structure_source",
        "current",
        "Structure and gate prompts prohibit connecting diagnostic mappings solely from lookup explanations.",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-cause-edge-policy-v3-tests",
        "current_fta_structure_tests",
        "current",
        "Positive natural-cause and negative F01681-style mapping regressions; historical artifacts are not rewritten.",
    ),
    "docs/README.md": (
        "fta-v10-doc-index",
        "current_truth_index",
        "current",
        "Points to active FTA baseline v10.",
    ),
    "docs/current-state-audit.md": (
        "fta-v10-current-state-audit",
        "current_state_document",
        "current",
        "Records v3 as current and v2 F01681 edges as superseded historical proposals.",
    ),
    "docs/acceptance.md": (
        "fta-v10-acceptance-record",
        "acceptance_document",
        "current",
        "Records v3 policy tests and explicitly states no online model rerun or readiness change.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v10-candidate-generation-policy",
        "candidate_fta_policy_document",
        "current",
        "Documents the user-confirmed natural-language-cause versus diagnostic-mapping edge boundary.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v10-validation-plan-policy",
        "validation_plan_document",
        "current",
        "Records the approved v3 causal-edge policy and leaves Final/Gold/production gates open.",
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
    previous = json.loads(V9_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v9":
        raise ValueError("v10 must extend the frozen v9 manifest snapshot")

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v10"
    manifest["baseline_version"] = "v10"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "cause disposition v3 policy: explicit natural-language possible causes may become review-only candidate edges; diagnostic lookup mappings do not auto-connect to the top event"
    )
    manifest["scope"]["excludes"].append(
        "online-model semantic accuracy claims, rewriting historical v2 runs, formal Gold, database writes, production API integration, and FTA readiness inferred from policy-contract tests"
    )
    manifest["active_baseline"]["cause_disposition_prompt"] = "fta-cause-disposition-v3"
    manifest["active_baseline"]["cause_to_top_event_edge_policy"] = (
        "natural_language_possible_cause_candidate_only; diagnostic_mapping_requires_independent_direct_source_causal_evidence; no automatic mapping edge"
    )
    manifest["active_baseline"]["f01681_v2_status"] = (
        "historical_superseded_policy_snapshot; its 15 fault-value mapping candidates are not accepted as current causal edges"
    )
    manifest["cause_disposition_v3_policy_regression"] = {
        "prompt_version": "fta-cause-disposition-v3",
        "status": "offline_contract_tests_passed_no_online_model_rerun",
        "user_decision": "natural_language_causes_may_be_candidate_edges; diagnostic_mappings_do_not_auto_connect",
        "natural_language_possible_cause": "may_enter_candidate_structure_as_ai_proposed_review_only_edge_when_source_scope_explicitly_identifies_possible_cause_or_trigger",
        "diagnostic_mapping": "fault/value/parameter/bit/index-to-explanation mapping stays relation_only unless independent direct source evidence outside the mapping supports the corresponding causal condition",
        "f01681_v2_run": "retained_unchanged_historical_diagnostic_artifact_not_current_policy_pass_evidence",
        "offline_regressions": [
            "backend-python/tests/test_fta_cause_disposition.py",
            "backend-python/tests/test_candidate_fta_extraction_service.py::test_f01681_fault_value_modes_stay_out_of_candidate_tree_and_are_audited",
            "backend-python/tests/test_candidate_fta_extraction_service.py::test_structure_mapping_of_non_candidate_cause_is_blocked",
        ],
        "formal_gold": False,
        "database_written": False,
        "online_model_rerun": False,
        "fta_ready": False,
        "production_ready": False,
        "accuracy_claim_allowed": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v9"],
        "current_version": "v10",
        "reason": "v10 makes the user-approved distinction between review-only natural-language cause edges and diagnostic mappings that cannot auto-connect; v9 remains an immutable historical snapshot.",
    })

    for path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": artifact_id,
            "kind": kind,
            "lifecycle": lifecycle,
            "path": path,
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
        current = V10_PATH.read_text(encoding="utf-8") if V10_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v10 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v10",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V10_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V10_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
