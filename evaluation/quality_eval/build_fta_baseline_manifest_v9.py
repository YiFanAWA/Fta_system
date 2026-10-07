#!/usr/bin/env python3
"""Build the v9 FTA research baseline from the frozen v8 snapshot."""

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
V8_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v8.json"
V9_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v9.json"
RUNS = (
    {
        "path": "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
        "sample_id": "SIEMENS_S210_2019_F30021",
        "fault_code": "F30021",
        "dataset": "siemens_s210_public_fault_corpus_v1",
        "source_pdf": "S210_Manual_2019.pdf",
        "outcome_status": "blocked",
        "tree_status": "blocked",
        "node_count": 5,
        "dispositions": {"fta_event_candidate": 4},
        "gate_count": 1,
        "candidate_tree_evidence_exact": True,
        "candidate_tree_evidence_unique": False,
    },
    {
        "path": "evaluation/quality_eval/runs/siemens_s120_s150_f35400_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
        "sample_id": "SIEMENS_S120_S150_2023_F35400_P3271_N001",
        "fault_code": "F35400",
        "dataset": "siemens_s120_s150_2023_public_fault_corpus_holdout_v2",
        "source_pdf": "SINAMICS_S120_S150_List_Manual_11-2023_EN.pdf",
        "outcome_status": "proposed",
        "tree_status": "candidate_ready_for_review",
        "node_count": 3,
        "dispositions": {"fta_event_candidate": 2},
        "gate_count": 1,
        "candidate_tree_evidence_exact": True,
        "candidate_tree_evidence_unique": True,
    },
    {
        "path": "evaluation/quality_eval/runs/siemens_s120_s150_f06000_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
        "sample_id": "SIEMENS_S120_S150_2023_F06000_P2792_N001",
        "fault_code": "F06000",
        "dataset": "siemens_s120_s150_2023_public_fault_corpus_holdout_v2",
        "source_pdf": "SINAMICS_S120_S150_List_Manual_11-2023_EN.pdf",
        "outcome_status": "proposed",
        "tree_status": "candidate_ready_for_review",
        "node_count": 15,
        "dispositions": {"fta_event_candidate": 11},
        "gate_count": 4,
        "candidate_tree_evidence_exact": True,
        "candidate_tree_evidence_unique": True,
    },
)


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


def _case(spec: dict[str, Any]) -> dict[str, Any]:
    path = spec["path"]
    run = json.loads((ROOT / path).read_text(encoding="utf-8"))
    source = run.get("source", {})
    if run.get("artifact_type") != "candidate_fta_raw_source_development_probe":
        raise ValueError(f"unexpected raw-source artifact type: {path}")
    if source.get("sample_id") != spec["sample_id"]:
        raise ValueError(f"sample identity mismatch: {path}")
    if source.get("dataset") != spec["dataset"]:
        raise ValueError(f"dataset identity mismatch: {path}")
    if source.get("source_pdf") != spec["source_pdf"]:
        raise ValueError(f"source PDF mismatch: {path}")
    if not isinstance(source.get("source_document_sha256"), str) or len(source["source_document_sha256"]) != 64:
        raise ValueError(f"source-document hash missing: {path}")
    if not isinstance(source.get("input_text_sha256"), str) or len(source["input_text_sha256"]) != 64:
        raise ValueError(f"input-text hash missing: {path}")
    if run.get("prompt_versions", {}).get("cause_disposition") != "fta-cause-disposition-v2":
        raise ValueError(f"cause-disposition prompt mismatch: {path}")
    if any(run.get(key) is not False for key in ("formal_gold", "database_written", "fta_ready", "production_ready")):
        raise ValueError(f"run crossed a prohibited persistence/readiness boundary: {path}")
    stages = {item.get("stage") for item in run.get("model_stage_responses", [])}
    if stages != {"fault_extraction", "cause_disposition", "structure_decomposition", "gate_assessment"}:
        raise ValueError(f"incomplete model stages: {path}")

    outcomes = run.get("result", {}).get("outcomes", [])
    if len(outcomes) != 1 or outcomes[0].get("fault_code") != spec["fault_code"]:
        raise ValueError(f"outcome identity mismatch: {path}")
    tree = outcomes[0].get("tree", {})
    if outcomes[0].get("status") != spec["outcome_status"] or tree.get("status") != spec["tree_status"]:
        raise ValueError(f"tree status mismatch: {path}")
    if tree.get("fta_ready") is not False or tree.get("production_ready") is not False:
        raise ValueError(f"tree crossed readiness boundary: {path}")
    if len(tree.get("nodes", [])) != spec["node_count"]:
        raise ValueError(f"node count mismatch: {path}")
    causes = tree.get("cause_dispositions", [])
    extraction = run.get("result", {}).get("extraction", {}).get("records", [])
    if len(extraction) != 1 or len(causes) != len(extraction[0].get("causes", [])):
        raise ValueError(f"cause ledger does not cover extraction: {path}")
    counts = dict(Counter(item.get("disposition") for item in causes))
    if counts != spec["dispositions"]:
        raise ValueError(f"cause disposition counts changed: {path}")

    gates = tree.get("gate_assessments", [])
    if len(gates) != spec["gate_count"]:
        raise ValueError(f"gate scope count mismatch: {path}")
    if any(gate.get("gate") not in {"unknown", "not_applicable"} for gate in gates):
        raise ValueError(f"unaccepted gate in development run: {path}")
    if any(gate.get("gate") == "unknown" and gate.get("gate_confidence_semantics") not in {None, "uncalibrated_model_estimate"} for gate in gates):
        raise ValueError(f"gate proposal semantics changed: {path}")

    integrity = run.get("evidence_integrity", {}).get("candidate_tree", {})
    exact = integrity.get("all_offsets_exact") is True
    unique = integrity.get("all_quotes_unique") is True
    if exact != spec["candidate_tree_evidence_exact"] or unique != spec["candidate_tree_evidence_unique"]:
        raise ValueError(f"candidate evidence integrity changed: {path}")
    if spec["fault_code"] == "F30021":
        if tree.get("status") != "blocked" or "node_evidence_missing_or_ambiguous:cause-3" not in tree.get("blockers", []):
            raise ValueError("F30021 must remain blocked on the repeated braking-resistor cause quote")
        if not integrity.get("failures"):
            raise ValueError("F30021 non-unique title quote must remain visible in evidence audit")

    return {
        "sample_id": spec["sample_id"],
        "fault_code": spec["fault_code"],
        "dataset": source["dataset"],
        "source_pdf": source["source_pdf"],
        "source_pdf_sha256": source["source_document_sha256"],
        "source_section": source.get("source_section"),
        "pdf_pages": [source.get("pdf_page_start"), source.get("pdf_page_end")],
        "source_offset": [source.get("source_offset_start"), source.get("source_offset_end")],
        "input_text_sha256": source["input_text_sha256"],
        "path": path,
        "outcome_status": outcomes[0]["status"],
        "tree_status": tree["status"],
        "tree_blockers": tree.get("blockers", []),
        "node_count": len(tree["nodes"]),
        "disposition_counts": counts,
        "gate_count": len(gates),
        "gate_values": [gate["gate"] for gate in gates],
        "all_boolean_gates_unknown": all(gate["gate"] == "unknown" for gate in gates if gate.get("gate") != "not_applicable"),
        "unknown_gate_reason_counts": tree.get("unknown_gate_reason_counts", {}),
        "candidate_tree_evidence_count": integrity.get("reference_count"),
        "candidate_tree_evidence_exact": exact,
        "candidate_tree_evidence_unique": unique,
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V8_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v8":
        raise ValueError("v9 must extend the stored v8 manifest")
    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v9"
    manifest["baseline_version"] = "v9"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["scope"]["includes"].append(
        "three additional cause-disposition v2 full-source regressions across S210 and same-vendor S120/S150 manuals, fail-closed guards for repeated evidence, and cause evidence mapping regression for normalized quote/whitespace variants"
    )
    manifest["scope"]["excludes"].append(
        "formal expert Gold, independent Final Test, AND/OR acceptance, calibrated gate probabilities, and production readiness inferred from these development cases"
    )
    manifest["active_baseline"]["raw_top_event_evidence_policy"] = "ambiguous exact source quotes add a blocking candidate-tree issue; no automatic locator choice"
    manifest["active_baseline"]["raw_text_v2_regression_additions"] = [spec["sample_id"] for spec in RUNS]
    manifest["active_baseline"]["f01681_causal_edge_review_status"] = "ai_review_found_mapping_to_causality_and_extraction_evidence_gaps; do_not_accept_current_edges"

    cases = [_case(spec) for spec in RUNS]
    manifest["cause_disposition_v2_extended_raw_text_regressions"] = {
        "prompt_version": "fta-cause-disposition-v2",
        "status": "development_regression_only_not_gold",
        "source_scope": "S210 plus same-vendor S120/S150 near-transfer; not independent cross-domain validation",
        "cases": cases,
        "formal_gold": False,
        "database_written": False,
        "independent_final_validation": False,
        "accuracy_claim_allowed": False,
    }
    manifest["top_event_evidence_ambiguity_guard"] = {
        "status": "implemented_and_unit_tested",
        "trigger": "top-event evidence quote is not globally unique in exact source text",
        "blocker": "top_event_evidence_ambiguous",
        "example_run": "evaluation/quality_eval/runs/siemens_s210_f30021_raw_candidate_fta_cause_disposition_v2_2026-09-28.json",
        "example_run_predates_guard": True,
        "example_run_remains_blocked_for_own_cause_evidence_ambiguity": True,
        "guard_test": "backend-python/tests/test_candidate_fta_extraction_service.py::test_repeated_top_event_quote_blocks_candidate_tree",
        "does_not_auto_select_offsets": True,
    }
    manifest["f01681_independent_ai_semantic_review"] = {
        "status": "blocking_findings_recorded_not_gold",
        "review_artifact": "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json",
        "review_report": "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md",
        "human_reviewed": False,
        "formal_gold": False,
        "finding_codes": [
            "fault_value_mapping_is_not_direct_causality",
            "extraction_cause_index_1_missing_evidence_span",
            "candidate_edges_conflict_with_mapping_policy",
            "top_level_scope_completeness_unresolved",
        ],
        "finding_resolution": {
            "extraction_cause_index_1_missing_evidence_span": "offline_replay_of_the_saved_f01681_extraction_response_maps_all_16_causes_to_one_indexed_source_span_including_index_1; historical_v2_preview_remains_unchanged; this_does_not_prove_causal_semantics",
        },
        "required_follow_up": "separate diagnostic mappings from causal edges; reconcile Remedy xxxx=9507 with scope without auto-promoting it",
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v8"],
        "current_version": "v9",
        "reason": "v9 records three additional source-pinned cause-disposition v2 regressions, closes the top-event repeated-quote blocking gap, and records F01681 causal/evidence review findings; unknown gates and all Gold/database/readiness boundaries remain unchanged.",
    })

    additions: list[dict[str, Any]] = [
        {
            "artifact_id": "fta-baseline-manifest-v8-snapshot",
            "kind": "baseline_manifest_snapshot",
            "lifecycle": "superseded_snapshot",
            "path": "evaluation/quality_eval/fta_baseline_manifest_v8.json",
            "note": "Previous active baseline; retained unchanged as v8 history.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v9-builder",
            "kind": "reproducibility_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/build_fta_baseline_manifest_v9.py",
            "note": "Extends the stored v8 baseline and verifies the three v2 regression artifacts, F01681 AI review findings, and repeated top-event evidence guard.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v9-tests",
            "kind": "manifest_regression_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v9.py",
            "note": "Checks v8 immutability, raw regression outcomes, evidence integrity, and readiness boundaries.",
        },
        {
            "artifact_id": "fta-top-event-evidence-ambiguity-service",
            "kind": "candidate_fta_owner_change",
            "lifecycle": "current",
            "path": "backend-python/fta/candidate_fta_extraction_service.py",
            "note": "Repeated top-event evidence quotes create a blocker; source locations are not auto-selected.",
        },
        {
            "artifact_id": "fta-top-event-evidence-ambiguity-tests",
            "kind": "candidate_fta_regression_tests",
            "lifecycle": "current",
            "path": "backend-python/tests/test_candidate_fta_extraction_service.py",
            "note": "Covers ambiguous top-event evidence and the resulting fail-closed candidate status.",
        },
        {
            "artifact_id": "fta-cause-evidence-mapper",
            "kind": "shared_extraction_evidence_owner_change",
            "lifecycle": "current",
            "path": "backend-python/extraction/text_extraction_adapter.py",
            "note": "Cause evidence matching normalizes whitespace and quote style, retains all source occurrences, and does not silently choose repeated locations.",
        },
        {
            "artifact_id": "fta-cause-evidence-mapper-tests",
            "kind": "shared_extraction_evidence_regression_tests",
            "lifecycle": "current",
            "path": "backend-python/tests/test_evidence_mapping.py",
            "note": "Covers F01681-like quote normalization and verifies repeated cause matches remain ambiguous for manual location.",
        },
        {
            "artifact_id": "fta-cause-disposition-extraction-evidence-gate",
            "kind": "fta_specific_evidence_gate_owner_change",
            "lifecycle": "current",
            "path": "backend-python/fta/cause_disposition_service.py",
            "note": "Requires exactly one indexed extraction-stage cause span; disposition-stage full-text quotes cannot replace missing or ambiguous extraction evidence.",
        },
        {
            "artifact_id": "fta-cause-disposition-extraction-evidence-tests",
            "kind": "fta_evidence_gate_regression_tests",
            "lifecycle": "current",
            "path": "backend-python/tests/test_fta_cause_disposition.py",
            "note": "Covers missing and multiple extraction cause spans, including rejection of model-bound replacement evidence.",
        },
        {
            "artifact_id": "fta-recursive-source-evidence-fixtures",
            "kind": "candidate_fta_contract_regression_tests",
            "lifecycle": "current",
            "path": "backend-python/tests/test_recursive_candidate_fta_extraction_service.py",
            "note": "Provides explicit indexed extraction cause evidence in success fixtures and preserves missing-evidence cases as blocked.",
        },
        {
            "artifact_id": "fta-f01681-independent-ai-review-json",
            "kind": "independent_ai_role_semantic_review",
            "lifecycle": "development_audit_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json",
            "note": "Records why fault-value mappings do not establish top-event causality, one extraction evidence gap, and an unresolved cause-set omission.",
        },
        {
            "artifact_id": "fta-f01681-independent-ai-review-report",
            "kind": "development_audit_report",
            "lifecycle": "development_audit_not_gold",
            "path": "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md",
            "note": "Human-readable independent AI-role review; explicitly not a human expert review or Gold label.",
        },
    ]
    for spec in RUNS:
        code = spec["fault_code"].lower()
        additions.extend([
            {
                "artifact_id": f"fta-raw-v2-{code}-model-run",
                "kind": "full_source_model_run",
                "lifecycle": "development_regression_not_gold",
                "path": spec["path"],
                "note": "Four-stage source-pinned raw-text v2 run; outcome and evidence state are encoded in the regression section.",
            },
            {
                "artifact_id": f"fta-raw-v2-{code}-report",
                "kind": "development_run_report",
                "lifecycle": "development_regression_not_gold",
                "path": str(Path(spec["path"]).with_suffix(".md")).replace("\\", "/"),
                "note": "Human-readable report for the source-pinned raw-text v2 development run.",
            },
        ])

    for entry in additions:
        _upsert(manifest["artifacts"], entry)

    current_notes = {
        "evaluation/quality_eval/build_fta_baseline_manifest_v9.py": "Active v9 reproducibility builder; preserves v8 as input snapshot.",
        "evaluation/quality_eval/test_build_fta_baseline_manifest_v9.py": "Regression tests for v9 source runs, blockers, evidence and readiness boundaries.",
        "evaluation/quality_eval/validate_fta_baseline_manifest.py": "Manifest path/hash validator defaults to active v9.",
        "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": "Checks the active v9 artifact fingerprints.",
        "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.json": "Records the F01681 semantic and evidence follow-up; not Gold.",
        "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v2_independent_ai_review_2026-09-28.md": "Explains why exact citations do not by themselves prove causal edges.",
        "backend-python/fta/candidate_fta_extraction_service.py": "Top-event evidence must not have an ambiguous repeated quote; ambiguous evidence adds a tree blocker.",
        "backend-python/tests/test_candidate_fta_extraction_service.py": "Includes regression for repeated top-event evidence blocking.",
        "backend-python/extraction/text_extraction_adapter.py": "Cause evidence matching preserves all source positions; it normalizes whitespace/quote style and only relaxes omitted inline parameter annotations or terminal punctuation while retaining original source spans.",
        "backend-python/tests/test_evidence_mapping.py": "Covers quote/whitespace and inline parameter annotation normalization, plus manual-review status for repeated source matches.",
        "backend-python/fta/cause_disposition_service.py": "Cause disposition is unresolved unless extraction supplied exactly one valid indexed cause span; later model quotes cannot substitute.",
        "backend-python/tests/test_fta_cause_disposition.py": "Covers strict extraction-evidence requirements and ambiguous-span fail-closed behavior.",
        "backend-python/tests/test_recursive_candidate_fta_extraction_service.py": "Success fixtures now include indexed cause evidence; missing source-cause mappings remain blocked.",
        "docs/README.md": "Internal source-of-truth index points to active FTA baseline v9.",
        "docs/current-state-audit.md": "Records v9 full-source regressions, evidence guard, and preview-only boundaries.",
        "docs/acceptance.md": "Records executed v9 tests and regression outcomes without Gold or accuracy claims.",
        "docs/candidate-fta-generation-v1.md": "Records the v9 raw-source development extension and top-event evidence rule.",
        "docs/fta-validation-reliability-plan-v1.md": "Records the latest regression tranche and evidence ambiguity guard.",
    }
    for path, note in current_notes.items():
        _upsert(manifest["artifacts"], {
            "artifact_id": "v9-current-" + path.replace("/", "-").replace(".", "-"),
            "kind": "current_source_or_test",
            "lifecycle": "current",
            "path": path,
            "note": note,
        })
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
        current = V9_PATH.read_text(encoding="utf-8") if V9_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v9 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "new_raw_source_cases": len(cases := payload["cause_disposition_v2_extended_raw_text_regressions"]["cases"]),
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V9_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V9_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
