#!/usr/bin/env python3
"""Build the v7 FTA research baseline from the frozen v6 snapshot."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V6_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v6.json"
V7_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v7.json"


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


def _raw_preview_case(
    relative_path: str,
    *,
    expected_sample_id: str,
    expected_fault_code: str,
    expected_node_count: int,
    expected_dispositions: dict[str, int],
) -> dict[str, Any]:
    run = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if run.get("artifact_type") != "candidate_fta_raw_source_development_probe":
        raise ValueError(f"unexpected raw-source artifact type: {relative_path}")
    if run.get("source", {}).get("sample_id") != expected_sample_id:
        raise ValueError(f"raw-source sample identity mismatch: {relative_path}")
    if run.get("outcome_summary", {}).get("fault_code") != expected_fault_code:
        raise ValueError(f"fault-code mismatch: {relative_path}")
    if any(run.get(flag) is not False for flag in ("formal_gold", "database_written", "fta_ready", "production_ready")):
        raise ValueError(f"raw-source run crossed a prohibited readiness/persistence boundary: {relative_path}")

    stages = {item.get("stage") for item in run.get("model_stage_responses", [])}
    required_stages = {"fault_extraction", "cause_disposition", "structure_decomposition", "gate_assessment"}
    if stages != required_stages:
        raise ValueError(f"raw-source model stage set is incomplete: {relative_path}")
    outcomes = run.get("result", {}).get("outcomes", [])
    if len(outcomes) != 1:
        raise ValueError(f"raw-source run must have exactly one outcome: {relative_path}")
    tree = outcomes[0].get("tree", {})
    if tree.get("status") != "candidate_ready_for_review" or tree.get("blockers") != []:
        raise ValueError(f"raw-source tree is not a blocker-free review candidate: {relative_path}")
    if len(tree.get("nodes", [])) != expected_node_count:
        raise ValueError(f"raw-source node count changed: {relative_path}")

    actual_dispositions = Counter(item.get("disposition") for item in tree.get("cause_dispositions", []))
    if dict(actual_dispositions) != expected_dispositions:
        raise ValueError(f"raw-source cause dispositions changed: {relative_path}")
    gates = tree.get("gate_assessments", [])
    if not gates or any(
        gate.get("gate") != "unknown"
        or gate.get("unknown_reason_code") != "confidence_policy_unavailable"
        or gate.get("cause_set_complete") is not True
        or gate.get("cause_set_leaf_normalized") is not True
        or gate.get("blockers") != ["gate_confidence_policy_unavailable"]
        for gate in gates
    ):
        raise ValueError(f"raw-source gates no longer satisfy the v7 fail-closed contract: {relative_path}")
    integrity = run.get("evidence_integrity", {}).get("candidate_tree", {})
    if (
        integrity.get("all_offsets_exact") is not True
        or integrity.get("all_quotes_unique") is not True
        or integrity.get("failures") != []
    ):
        raise ValueError(f"raw-source tree evidence is invalid: {relative_path}")

    return {
        "sample_id": expected_sample_id,
        "fault_code": expected_fault_code,
        "path": relative_path,
        "node_count": len(tree["nodes"]),
        "disposition_counts": dict(actual_dispositions),
        "gate_scope_count": len(gates),
        "all_gate_scopes_complete": all(gate["cause_set_complete"] for gate in gates),
        "all_gate_scopes_leaf_normalized": all(gate["cause_set_leaf_normalized"] for gate in gates),
        "all_gates_unknown": all(gate["gate"] == "unknown" for gate in gates),
        "all_unknown_reasons_policy_unavailable": all(
            gate["unknown_reason_code"] == "confidence_policy_unavailable" for gate in gates
        ),
        "candidate_tree_evidence_count": integrity["reference_count"],
        "candidate_tree_evidence_exact_and_unique": True,
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V6_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v6":
        raise ValueError("v7 must extend the frozen v6 manifest")
    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v7"
    manifest["baseline_version"] = "v7"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "closed-enumeration cause-set completeness semantics, qualitative trigger-condition structure, and two source-pinned full-raw-text development regressions"
    )
    manifest["scope"]["excludes"].append(
        "generalized accuracy claims from the two full-raw-text development regressions"
    )
    manifest["active_baseline"]["structure_prompt_semantics"] = (
        "source_scope_closed_enumeration_completeness_v1"
    )
    manifest["active_baseline"]["raw_text_preview_regressions"] = [
        "SIEMENS_S120_S150_2023_F35400_P3271_N001",
        "SIEMENS_S120_S150_2023_F06000_P2792_N001",
    ]
    manifest["active_baseline"]["preview_only"] = True
    manifest["active_baseline"]["fta_ready"] = False
    manifest["active_baseline"]["production_ready"] = False
    raw_cases = [
        _raw_preview_case(
            "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.json",
            expected_sample_id="SIEMENS_S120_S150_2023_F35400_P3271_N001",
            expected_fault_code="F35400",
            expected_node_count=3,
            expected_dispositions={"fta_event_candidate": 2},
        ),
        _raw_preview_case(
            "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.json",
            expected_sample_id="SIEMENS_S120_S150_2023_F06000_P2792_N001",
            expected_fault_code="F06000",
            expected_node_count=13,
            expected_dispositions={"fta_event_candidate": 10, "exclude_from_tree": 1},
        ),
    ]
    if raw_cases[1]["gate_scope_count"] != 2:
        raise ValueError("F06000 must preserve its two nested gate scopes")
    manifest["raw_text_preview_regressions"] = {
        "status": "development_regression_only_not_gold",
        "model_stages": [
            "fault_extraction",
            "cause_disposition",
            "structure_decomposition",
            "gate_assessment",
        ],
        "cases": raw_cases,
        "formal_gold": False,
        "database_written": False,
        "independent_final_validation": False,
        "accuracy_claim_allowed": False,
    }
    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v6"],
            "current_version": "v7",
            "reason": "v7 freezes the corrected source-scope completeness semantics and two full-raw-text development regressions while keeping the gate-confidence policy unavailable and readiness false.",
        }
    )

    additions = [
        {
            "artifact_id": "fta-baseline-manifest-v6-snapshot",
            "kind": "baseline_manifest_snapshot",
            "lifecycle": "immutable_superseded_snapshot",
            "path": "evaluation/quality_eval/fta_baseline_manifest_v6.json",
            "note": "Previous active research baseline; retained unchanged as v7 history.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v7-builder",
            "kind": "reproducibility_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/build_fta_baseline_manifest_v7.py",
            "note": "Builds v7 from the stored v6 manifest and source-pinned full-text development run artifacts.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v7-tests",
            "kind": "manifest_regression_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v7.py",
            "note": "Checks v6 inheritance, scope, evidence, readiness boundary, and artifact hashes.",
        },
        {
            "artifact_id": "fta-raw-source-probe-runner-v1",
            "kind": "development_probe_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py",
            "note": "Runs or offline-revalidates one pinned public raw fault record through the current candidate application service.",
        },
        {
            "artifact_id": "fta-raw-source-probe-runner-v1-tests",
            "kind": "probe_contract_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py",
            "note": "Tests stage classification, evidence offsets, unique tree citations, and offline artifact revalidation.",
        },
        {
            "artifact_id": "fta-raw-source-f35400-scope-completeness-run",
            "kind": "full_raw_text_development_run",
            "lifecycle": "development_regression_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.json",
            "note": "F35400 full-source run after closed-enumeration scope semantics; gate remains unknown because no confidence policy is available.",
        },
        {
            "artifact_id": "fta-raw-source-f35400-scope-completeness-report",
            "kind": "development_run_report",
            "lifecycle": "development_regression_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_after_scope_completeness_fix_2026-09-28.md",
            "note": "Human-readable report for the pinned F35400 full-source development run.",
        },
        {
            "artifact_id": "fta-raw-source-f06000-prompt-fix-run",
            "kind": "full_raw_text_development_run",
            "lifecycle": "development_regression_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.json",
            "note": "F06000 full-source rerun through the current four-stage application; gate scopes remain unknown without a confidence policy.",
        },
        {
            "artifact_id": "fta-raw-source-f06000-prompt-fix-report",
            "kind": "development_run_report",
            "lifecycle": "development_regression_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_after_prompt_fix_2026-09-28.md",
            "note": "Human-readable report for the pinned F06000 full-source development run.",
        },
    ]
    for entry in additions:
        _upsert(manifest["artifacts"], entry)

    current_notes = {
        "backend-python/fta/candidate_fta_extraction_service.py": "Current candidate structure prompt semantics include source-scope closed-enumeration completeness; qualitative trigger conditions do not require instance readings.",
        "backend-python/tests/test_candidate_fta_extraction_service.py": "Regression coverage for disposition-vs-structure indices and source-scope completeness semantics.",
        "evaluation/quality_eval/validate_fta_baseline_manifest.py": "Validates manifest-relative paths and SHA-256; defaults to active v7.",
        "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": "Tests safe repository-relative artifact resolution and the active v7 baseline.",
        "docs/README.md": "Internal source-of-truth index points to active FTA research baseline v7.",
        "docs/current-state-audit.md": "Current project audit including the two raw-text preview regressions and Preview-only boundary.",
        "docs/acceptance.md": "Current acceptance log with local tests and the two dated full-raw-text development runs.",
        "docs/candidate-fta-generation-v1.md": "Current candidate FTA semantics, active v7 manifest, historical runs, and readiness boundary.",
        "docs/fta-validation-reliability-plan-v1.md": "Reliability plan and dated work log; independent Final and calibrated gate policy remain outstanding.",
    }
    for path, note in current_notes.items():
        _upsert(
            manifest["artifacts"],
            {
                "artifact_id": "v7-current-" + path.replace("/", "-").replace(".", "-"),
                "kind": "current_source_or_test",
                "lifecycle": "current",
                "path": path,
                "note": note,
            },
        )

    for artifact in manifest["artifacts"]:
        target = (ROOT / artifact["path"]).resolve(strict=True)
        if not target.is_relative_to(ROOT.resolve()):
            raise ValueError(f"artifact escapes repository: {artifact['path']}")
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
        current = V7_PATH.read_text(encoding="utf-8") if V7_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v7 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"]), "raw_text_regressions": len(payload["raw_text_preview_regressions"]["cases"]), "final_status": payload["independent_final_validation"]["status"]}, ensure_ascii=False))
        return 0
    V7_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V7_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
