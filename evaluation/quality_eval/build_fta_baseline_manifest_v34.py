#!/usr/bin/env python3
"""Build active FTA baseline v34 with a non-Gold semantic review regression."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V33_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v33.json"
V34_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v34.json"
POLICY_PATH = "evaluation/quality_eval/fta_event_scope_semantic_review_policy_v1.md"
CASES_PATH = "evaluation/quality_eval/datasets/fta_event_scope_semantic_review_cases_v1.json"
REGRESSION_TEST_PATH = "evaluation/quality_eval/test_fta_event_scope_semantic_review_regression_v1.py"
V6_ASSESSMENT_PATH = "evaluation/quality_eval/runs/fta_event_scope_nasa_battery_fig7_model_run_assessment_v6_2026-09-29.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v33.json": (
        "fta-baseline-manifest-v33-snapshot", "historical_baseline_manifest", "historical",
        "Frozen state after the authorized v6 run and before formalizing its semantic-review regression policy.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v33.py": (
        "fta-baseline-manifest-v33-builder", "reproducibility_tool", "historical",
        "Reproduces the v6 run snapshot; superseded as the active manifest builder by v34.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v33.py": (
        "fta-baseline-manifest-v33-tests", "manifest_regression_tests", "historical",
        "Protects the v33 state that records v6 as structurally valid but semantically unaccepted.",
    ),
    POLICY_PATH: (
        "event-scope-semantic-review-policy-v1", "evaluation_policy", "current",
        "Defines evidence-bound gate candidates, co-occurrence handling, and manual review boundaries; not production logic or Gold.",
    ),
    CASES_PATH: (
        "event-scope-semantic-review-cases-v1", "development_regression_cases", "current_non_gold",
        "Three authored policy examples and three observed v6 review findings; explicitly not expert Gold or accuracy samples.",
    ),
    REGRESSION_TEST_PATH: (
        "event-scope-semantic-review-regression-v1-tests", "evaluation_tests", "current",
        "Protects policy distinctions and keeps known v6 semantic issues pending without auto-correction.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v34.py": (
        "fta-baseline-manifest-v34-builder", "reproducibility_tool", "current",
        "Builds v34 from immutable v33 and registers the semantic review policy, non-Gold cases, tests, and current truth.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v34.py": (
        "fta-baseline-manifest-v34-tests", "manifest_regression_tests", "current",
        "Protects v33 history, non-Gold scope, known v6 semantic blockers, and false readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v34-default", "validation_tool", "current",
        "Validates repository artifact paths and SHA-256 fingerprints; defaults to active manifest v34.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v34-default", "validation_tool_tests", "current",
        "Covers artifact hashes and the active v34 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v34-doc-index", "current_truth_index", "current",
        "Points to v34 and its non-Gold semantic-review policy/regression cases.",
    ),
    "docs/current-state-audit.md": (
        "fta-v34-current-state-audit", "current_state_document", "current",
        "Records v6's structural pass and semantic blockers plus the local regression policy.",
    ),
    "docs/acceptance.md": (
        "fta-v34-acceptance-record", "acceptance_document", "current",
        "Records semantic policy regression tests and the manifest integrity checks.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v34-candidate-generation-policy", "current_fta_policy_document", "current",
        "Links active v34 and separates text-supported gate candidates from accepted Gold and production trees.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v34-validation-plan-policy", "current_validation_plan_document", "current",
        "Tracks semantic-review regression as a completed local step while preserving remaining validation blockers.",
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
    v33 = json.loads(V33_PATH.read_text(encoding="utf-8"))
    if v33.get("manifest_id") != "candidate_fta_research_baseline_v33":
        raise ValueError("v34 must extend the v33 manifest")
    active = v33.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v34 must preserve false FTA/production readiness")
    if active.get("event_scope_model_v6_semantic_acceptance") is not False:
        raise ValueError("v34 expects the v6 semantic result to remain unaccepted")

    cases = json.loads((ROOT / CASES_PATH).read_text(encoding="utf-8"))
    assessment = json.loads((ROOT / V6_ASSESSMENT_PATH).read_text(encoding="utf-8"))
    case_ids = {case.get("case_id") for case in cases.get("cases", [])}
    required_cases = {
        "POLICY-OR-001",
        "POLICY-AND-001",
        "POLICY-COOCCURRENCE-001",
        "FIG7-V6-S1-OR-NOT-BOUND",
        "FIG7-V6-SHARED-CELL-EVENT",
        "FIG7-V6-COMPOSITE-EVENT-BOUNDARY",
    }
    if cases.get("dataset_status") != "development_policy_cases_not_gold" or cases.get("human_expert_gold") is not False:
        raise ValueError("v34 cases must remain explicitly non-Gold policy/regression material")
    if not required_cases.issubset(case_ids):
        raise ValueError("v34 semantic regression cases are incomplete")
    if assessment.get("output_assessment", {}).get("semantic_correctness") != "not_assessed":
        raise ValueError("v34 must preserve v6 semantic correctness as not assessed")

    manifest = deepcopy(v33)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v34"
    manifest["baseline_version"] = "v34"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v33",
        "path": V33_PATH.relative_to(ROOT).as_posix(),
        "reason": "v34 formalizes evidence-bound AND/OR candidate review and non-Gold regression handling for known v6 semantic risks; it changes no model, Gold, or production behavior.",
    }
    manifest["scope"]["includes"].append(
        "evaluation-only semantic review policy and six non-Gold regression cases for direct logic evidence, co-occurrence, shared event identity, and composite event granularity"
    )
    manifest["scope"]["excludes"].extend([
        "using authored policy examples or seen Figure 7 findings as human expert Gold or quantitative model evaluation",
        "automatically parsing arbitrary natural-language logic, repairing v6 outputs, changing production prompts/services, or promoting semantic/FTA readiness",
    ])
    manifest["active_baseline"].update({
        "event_scope_semantic_review_policy": "event_scope_semantic_review_policy_v1",
        "event_scope_semantic_review_policy_path": POLICY_PATH,
        "event_scope_semantic_review_cases_path": CASES_PATH,
        "event_scope_semantic_review_test_path": REGRESSION_TEST_PATH,
        "event_scope_semantic_review_case_status": "development_policy_cases_not_gold",
        "event_scope_v6_known_semantic_findings": [
            "explicit_alternative_logic_evidence_not_bound",
            "shared_event_identity_requires_manual_review",
            "composite_event_granularity_requires_manual_review",
        ],
        "event_scope_v6_semantic_regression_status": "findings_preserved_not_cleared",
        "event_scope_model_v6_semantic_acceptance": False,
        "event_scope_model_v6_accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["event_scope_prompt_v6"].update({
        "semantic_review_policy_path": POLICY_PATH,
        "semantic_review_cases_path": CASES_PATH,
        "semantic_review_test_path": REGRESSION_TEST_PATH,
        "semantic_review_case_status": "development_policy_cases_not_gold",
        "known_semantic_findings_preserved": True,
        "semantic_acceptance": False,
    })
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v33"],
        "current_version": "v34",
        "reason": "v34 records the semantic-review policy and regression cases without modifying the observed v6 output or making a semantic accuracy/readiness claim.",
    })

    _upsert(manifest["artifacts"], {
        "artifact_id": "fta-baseline-manifest-v33-snapshot",
        "kind": "historical_baseline_manifest",
        "lifecycle": "historical",
        "path": V33_PATH.relative_to(ROOT).as_posix(),
        "note": "Immutable baseline after the one-shot v6 run and before formalizing its semantic regression policy.",
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
    repo_root = ROOT.resolve(strict=True)
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
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
        current = V34_PATH.read_text(encoding="utf-8") if V34_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v34 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v34",
            "semantic_policy_cases": len(cases_from_manifest_files(payload)),
            "v6_semantic_regression_status": payload["active_baseline"]["event_scope_v6_semantic_regression_status"],
            "v6_semantic_acceptance": payload["active_baseline"]["event_scope_model_v6_semantic_acceptance"],
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V34_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V34_PATH)}, ensure_ascii=False))
    return 0


def cases_from_manifest_files(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cases_path = ROOT / payload["active_baseline"]["event_scope_semantic_review_cases_path"]
    return json.loads(cases_path.read_text(encoding="utf-8"))["cases"]


if __name__ == "__main__":
    raise SystemExit(main())
