#!/usr/bin/env python3
"""Build the v8 FTA research baseline from the frozen v7 snapshot."""

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
V7_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v7.json"
V8_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v8.json"
RAW_RUNS = {
    "F01681": "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json",
    "F30027": "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_provenance_audit_2026-09-28.json",
}
MODEL_RUNS = {
    "F01681": "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
    "F30027": "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
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


def _raw_preview_case(
    relative_path: str,
    *,
    sample_id: str,
    fault_code: str,
    expected_node_count: int,
    expected_dispositions: dict[str, int],
    expected_gate_count: int,
    expected_complete_gate_count: int,
) -> dict[str, Any]:
    run = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if run.get("artifact_type") != "candidate_fta_raw_source_development_probe":
        raise ValueError(f"unexpected raw-source artifact type: {relative_path}")
    if run.get("source", {}).get("dataset") != "siemens_s210_public_fault_corpus_v1":
        raise ValueError(f"raw-source corpus identity mismatch: {relative_path}")
    source = run.get("source", {})
    if (
        not source.get("source_pdf")
        or not source.get("source_section")
        or not isinstance(source.get("source_document_sha256"), str)
        or len(source["source_document_sha256"]) != 64
        or not isinstance(source.get("pdf_page_start"), int)
        or not isinstance(source.get("pdf_page_end"), int)
        or not isinstance(source.get("source_offset_start"), int)
        or not isinstance(source.get("source_offset_end"), int)
    ):
        raise ValueError(f"raw-source PDF and section provenance is incomplete: {relative_path}")
    if run.get("source", {}).get("sample_id") != sample_id:
        raise ValueError(f"raw-source sample identity mismatch: {relative_path}")
    if run.get("outcome_summary", {}).get("fault_code") != fault_code:
        raise ValueError(f"fault-code mismatch: {relative_path}")
    if run.get("prompt_versions", {}).get("cause_disposition") != "fta-cause-disposition-v2":
        raise ValueError(f"unexpected cause-disposition prompt version: {relative_path}")
    if any(
        run.get(flag) is not False
        for flag in ("formal_gold", "database_written", "fta_ready", "production_ready")
    ):
        raise ValueError(f"raw-source run crossed a prohibited readiness/persistence boundary: {relative_path}")

    stages = {item.get("stage") for item in run.get("model_stage_responses", [])}
    required_stages = {
        "fault_extraction",
        "cause_disposition",
        "structure_decomposition",
        "gate_assessment",
    }
    if stages != required_stages:
        raise ValueError(f"raw-source model stage set is incomplete: {relative_path}")
    outcomes = run.get("result", {}).get("outcomes", [])
    if len(outcomes) != 1:
        raise ValueError(f"raw-source run must have exactly one outcome: {relative_path}")
    tree = outcomes[0].get("tree", {})
    if outcomes[0].get("status") != "proposed" or tree.get("status") != "candidate_ready_for_review":
        raise ValueError(f"raw-source result is not a review-only Preview: {relative_path}")
    if tree.get("blockers") != [] or tree.get("fta_ready") is not False:
        raise ValueError(f"raw-source tree crossed its review-only boundary: {relative_path}")
    if len(tree.get("nodes", [])) != expected_node_count:
        raise ValueError(f"raw-source node count changed: {relative_path}")
    extraction_records = run.get("result", {}).get("extraction", {}).get("records", [])
    if len(extraction_records) != 1:
        raise ValueError(f"raw-source extraction must contain one record: {relative_path}")
    if len(tree.get("cause_dispositions", [])) != len(extraction_records[0].get("causes", [])):
        raise ValueError(f"cause disposition ledger does not cover the extraction: {relative_path}")

    actual_dispositions = Counter(
        item.get("disposition") for item in tree.get("cause_dispositions", [])
    )
    if dict(actual_dispositions) != expected_dispositions:
        raise ValueError(f"raw-source cause dispositions changed: {relative_path}")
    gates = tree.get("gate_assessments", [])
    if len(gates) != expected_gate_count or not gates:
        raise ValueError(f"raw-source gate-scope count changed: {relative_path}")
    if any(
        gate.get("gate") != "unknown"
        or "gate_confidence_policy_unavailable" not in gate.get("blockers", [])
        for gate in gates
    ):
        raise ValueError(f"raw-source gate was accepted without an available policy: {relative_path}")
    complete_count = sum(
        gate.get("cause_set_complete") is True
        and gate.get("cause_set_leaf_normalized") is True
        for gate in gates
    )
    if complete_count != expected_complete_gate_count:
        raise ValueError(f"raw-source cause-scope completeness changed: {relative_path}")

    integrity = run.get("evidence_integrity", {}).get("candidate_tree", {})
    if (
        integrity.get("all_offsets_exact") is not True
        or integrity.get("all_quotes_unique") is not True
        or integrity.get("failures") != []
    ):
        raise ValueError(f"raw-source tree evidence is invalid: {relative_path}")

    return {
        "sample_id": sample_id,
        "fault_code": fault_code,
        "dataset": run["source"]["dataset"],
        "source_pdf": source["source_pdf"],
        "source_pdf_sha256": source["source_document_sha256"],
        "source_section": source["source_section"],
        "pdf_pages": [source["pdf_page_start"], source["pdf_page_end"]],
        "path": relative_path,
        "outcome_status": outcomes[0]["status"],
        "tree_status": tree["status"],
        "node_count": len(tree["nodes"]),
        "disposition_counts": dict(actual_dispositions),
        "gate_scope_count": len(gates),
        "all_gates_unknown": all(gate["gate"] == "unknown" for gate in gates),
        "complete_and_leaf_normalized_gate_count": complete_count,
        "incomplete_or_unresolved_scope_count": len(gates) - complete_count,
        "candidate_tree_evidence_count": integrity["reference_count"],
        "candidate_tree_evidence_exact_and_unique": True,
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V7_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v7":
        raise ValueError("v8 must extend the frozen v7 manifest")
    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v8"
    manifest["baseline_version"] = "v8"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "cause-disposition v2 distinction between manual-listed generic causal conditions and instance-specific fault-value diagnosis, plus two source-pinned full-S210 raw-text development regressions"
    )
    manifest["scope"]["excludes"].append(
        "expert Gold, calibrated gate decisions, accuracy claims, and production readiness inferred from the two v2 prompt regressions"
    )
    manifest["active_baseline"]["cause_disposition_prompt"] = "fta-cause-disposition-v2"
    manifest["active_baseline"]["raw_text_preview_regressions"] = [
        "SIEMENS_S120_S150_2023_F35400_P3271_N001",
        "SIEMENS_S120_S150_2023_F06000_P2792_N001",
        "SIEMENS_S210_2019_F01681",
        "SIEMENS_S210_2019_F30027",
    ]
    f01681 = _raw_preview_case(
        RAW_RUNS["F01681"],
        sample_id="SIEMENS_S210_2019_F01681",
        fault_code="F01681",
        expected_node_count=38,
        expected_dispositions={"exclude_from_tree": 1, "fta_event_candidate": 15},
        expected_gate_count=12,
        expected_complete_gate_count=10,
    )
    f30027 = _raw_preview_case(
        RAW_RUNS["F30027"],
        sample_id="SIEMENS_S210_2019_F30027",
        fault_code="F30027",
        expected_node_count=12,
        expected_dispositions={"fta_event_candidate": 9},
        expected_gate_count=2,
        expected_complete_gate_count=2,
    )
    manifest["cause_disposition_v2_raw_text_regressions"] = {
        "prompt_version": "fta-cause-disposition-v2",
        "status": "development_regression_only_not_gold",
        "cases": [f01681, f30027],
        "formal_gold": False,
        "database_written": False,
        "independent_final_validation": False,
        "accuracy_claim_allowed": False,
    }
    previous_cases = manifest["raw_text_preview_regressions"]["cases"]
    manifest["raw_text_preview_regressions"]["cases"] = previous_cases + [f01681, f30027]
    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v7"],
            "current_version": "v8",
            "reason": "v8 records the corrected generic-cause versus instance-diagnostic boundary and two full-S210 raw-source v2 prompt regressions; all gate decisions remain unknown and readiness stays false.",
        }
    )

    additions = [
        {
            "artifact_id": "fta-baseline-manifest-v7-snapshot",
            "kind": "baseline_manifest_snapshot",
            "lifecycle": "immutable_superseded_snapshot",
            "path": "evaluation/quality_eval/fta_baseline_manifest_v7.json",
            "note": "Previous active research baseline; retained unchanged as v8 history.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v8-builder",
            "kind": "reproducibility_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/build_fta_baseline_manifest_v8.py",
            "note": "Builds v8 from the stored v7 manifest and source-pinned v2 raw-text development runs.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v8-tests",
            "kind": "manifest_regression_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v8.py",
            "note": "Checks v7 immutability, case-level gates/evidence, source identity, prompt version, and readiness boundaries.",
        },
        {
            "artifact_id": "fta-cause-disposition-prompt-v2",
            "kind": "current_prompt_owner",
            "lifecycle": "current",
            "path": "backend-python/fta/cause_disposition_service.py",
            "note": "Separates manual-listed possible causal conditions from instance-specific fault-value diagnosis without inferring gate type.",
        },
        {
            "artifact_id": "fta-cause-disposition-prompt-v2-tests",
            "kind": "prompt_contract_tests",
            "lifecycle": "current",
            "path": "backend-python/tests/test_fta_cause_disposition.py",
            "note": "Pins the prompt distinctions for fault-value causes, instance occurrence, and intact causal clauses.",
        },
        {
            "artifact_id": "fta-raw-probe-corpus-identity-fix",
            "kind": "development_probe_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py",
            "note": "Records the actual input corpus name and the cause-disposition prompt version in each artifact.",
        },
        {
            "artifact_id": "fta-raw-probe-corpus-identity-tests",
            "kind": "probe_contract_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py",
            "note": "Tests corpus identity recording in generated and offline-revalidated probe artifacts.",
        },
        {
            "artifact_id": "fta-s210-f01681-cause-v2-model-run",
            "kind": "full_s210_raw_text_model_run",
            "lifecycle": "development_regression_not_gold",
            "path": MODEL_RUNS["F01681"],
            "note": "Original full-source four-stage model response artifact for F01681 before offline provenance re-audit.",
        },
        {
            "artifact_id": "fta-s210-f30027-cause-v2-model-run",
            "kind": "full_s210_raw_text_model_run",
            "lifecycle": "development_regression_not_gold",
            "path": MODEL_RUNS["F30027"],
            "note": "Original full-source four-stage model response artifact for F30027 before offline provenance re-audit.",
        },
        {
            "artifact_id": "fta-s210-f01681-cause-v1-diagnostic",
            "kind": "superseded_prompt_diagnostic_run",
            "lifecycle": "historical_prompt_diagnostic_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_dev_regression_2026-09-28.json",
            "note": "Preserved first-run evidence that v1 over-excluded fifteen fault-value causal conditions.",
        },
        {
            "artifact_id": "fta-s210-f01681-cause-v1-diagnostic-report",
            "kind": "development_run_report",
            "lifecycle": "historical_prompt_diagnostic_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_dev_regression_2026-09-28.md",
            "note": "Human-readable report of the F01681 prompt-v1 over-exclusion diagnostic.",
        },
        {
            "artifact_id": "fta-s210-f30027-cause-v1-diagnostic",
            "kind": "superseded_prompt_diagnostic_run",
            "lifecycle": "historical_prompt_diagnostic_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_dev_regression_2026-09-28.json",
            "note": "Preserved first-run evidence that v1 marked complete causal statements as mixed unresolved.",
        },
        {
            "artifact_id": "fta-s210-f30027-cause-v1-diagnostic-report",
            "kind": "development_run_report",
            "lifecycle": "historical_prompt_diagnostic_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f30027_raw_candidate_fta_dev_regression_2026-09-28.md",
            "note": "Human-readable report of the F30027 prompt-v1 over-exclusion diagnostic.",
        },
    ]
    for fault_code, relative_path in RAW_RUNS.items():
        additions.extend(
            [
                {
                    "artifact_id": f"fta-s210-{fault_code.lower()}-cause-v2-provenance-audit",
                    "kind": "offline_provenance_reaudit",
                    "lifecycle": "development_regression_audited_not_gold",
                    "path": relative_path,
                    "note": f"Offline source-provenance re-audit of {fault_code} prompt-v2 output; no model call, unknown gates and readiness false.",
                },
                {
                    "artifact_id": f"fta-s210-{fault_code.lower()}-cause-v2-provenance-audit-report",
                    "kind": "development_run_report",
                    "lifecycle": "development_regression_audited_not_gold",
                    "path": str(Path(relative_path).with_suffix(".md")).replace("\\", "/"),
                    "note": f"Human-readable report for the {fault_code} prompt-v2 full-source development regression.",
                },
            ]
        )
    for entry in additions:
        _upsert(manifest["artifacts"], entry)

    current_notes = {
        "backend-python/fta/cause_disposition_service.py": "Active cause-disposition prompt v2 distinguishes explicit possible causes from diagnostic-only value mappings; does not infer AND/OR or instance occurrence.",
        "backend-python/tests/test_fta_cause_disposition.py": "Prompt regressions for the v2 generic-cause versus instance-diagnosis boundary.",
        "evaluation/quality_eval/public_sources/probe_candidate_fta_raw_source_v1.py": "Raw-source runner records actual corpus identity and active cause-disposition prompt version.",
        "evaluation/quality_eval/public_sources/test_probe_candidate_fta_raw_source_v1.py": "Tests corpus identity and prompt-version provenance in development artifacts.",
        "evaluation/quality_eval/validate_fta_baseline_manifest.py": "Validates manifest paths and hashes; defaults to active v8.",
        "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": "Validates exact artifact hashes in the active v8 manifest.",
        "docs/README.md": "Internal source-of-truth index points to active FTA research baseline v8.",
        "docs/current-state-audit.md": "Current audit includes v2 cause-boundary regressions and preserves Preview-only readiness.",
        "docs/acceptance.md": "Records actual tests and full-S210 v2 development runs with unknown gate outcomes.",
        "docs/candidate-fta-generation-v1.md": "Current candidate FTA semantics and v2 raw-source regressions; no Gold or readiness promotion.",
        "docs/fta-validation-reliability-plan-v1.md": "Reliability plan records prompt-v2 cause/instance boundary and regression evidence.",
    }
    for path, note in current_notes.items():
        _upsert(
            manifest["artifacts"],
            {
                "artifact_id": "v8-current-" + path.replace("/", "-").replace(".", "-"),
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
        current = V8_PATH.read_text(encoding="utf-8") if V8_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v8 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "raw_text_regressions": len(payload["raw_text_preview_regressions"]["cases"]),
            "cause_disposition_v2_cases": len(payload["cause_disposition_v2_raw_text_regressions"]["cases"]),
            "final_status": payload["independent_final_validation"]["status"],
        }, ensure_ascii=False))
        return 0
    V8_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V8_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
