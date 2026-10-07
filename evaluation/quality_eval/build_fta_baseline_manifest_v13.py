#!/usr/bin/env python3
"""Build the v13 FTA baseline with the F01681 cause-v4 development replay."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V12_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v12.json"
V13_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v13.json"
RUN_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.json"
REVIEW_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.json"
CORPUS_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_public_fault_corpus_v1.jsonl"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v12.json": (
        "fta-baseline-manifest-v12-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v12 snapshot; records the offline cause-vs-top-event prompt/contract regression.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v13.py": (
        "fta-baseline-manifest-v13-builder", "reproducibility_tool", "current",
        "Builds v13 from immutable v12 and validates one bounded F01681 v4 replay and AI role review.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v13.py": (
        "fta-baseline-manifest-v13-tests", "manifest_regression_tests", "current",
        "Checks sample disposition counts, evidence offsets, AI-only provenance, hashes, and non-readiness.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v13-default", "validation_tool", "current",
        "Validates manifest paths and hashes; defaults to the active v13 snapshot.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v13-default", "validation_tool_tests", "current",
        "Verifies manifest validation and the active v13 baseline.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v4-live-run", "online_model_development_probe", "current_development_evidence",
        "One bounded F01681 v4 run: two model stages, 16 relation-only causes, no tree candidate; not Gold or accuracy evidence.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_raw_candidate_fta_cause_disposition_v4_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v4-live-run-report", "online_model_development_report", "current_development_evidence",
        "Human-readable report for the two-stage F01681 v4 run; no structure/gate stage ran because candidate count was zero.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.json": (
        "siemens-s210-f01681-cause-disposition-v4-ai-review", "independent_ai_role_review", "current_development_review",
        "Read-only AI subagent review; not a human expert signature or formal Gold.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_cause_disposition_v4_independent_ai_review_2026-09-28.md": (
        "siemens-s210-f01681-cause-disposition-v4-ai-review-report", "independent_ai_role_review_report", "current_development_review",
        "Human-readable summary of the AI-only review and its limits.",
    ),
    "docs/README.md": (
        "fta-v13-doc-index", "current_truth_index", "current", "Points to active FTA baseline v13.",
    ),
    "docs/current-state-audit.md": (
        "fta-v13-current-state-audit", "current_state_document", "current",
        "Records the F01681 v4 run, evidence checks, AI role review, and unchanged readiness.",
    ),
    "docs/acceptance.md": (
        "fta-v13-acceptance-record", "acceptance_document", "current",
        "Records v4 replay commands/results and active manifest validation.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v13-candidate-generation-policy", "candidate_fta_policy_document", "current",
        "Documents the single-sample v4 live replay as development evidence only.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v13-validation-plan-policy", "validation_plan_document", "current",
        "Tracks offline and single-sample online evidence while keeping independent Final absent.",
    ),
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def _load_and_validate_run() -> tuple[dict[str, Any], dict[str, Any]]:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if run.get("source", {}).get("sample_id") != "SIEMENS_S210_2019_F01681":
        raise ValueError("v13 run must be the source-pinned S210 F01681 sample")
    if run.get("prompt_versions", {}).get("cause_disposition") != "fta-cause-disposition-v4":
        raise ValueError("v13 run must use cause disposition prompt v4")
    model = run.get("model", {})
    if model.get("request_attempt_count") != 2 or model.get("successful_response_count") != 2:
        raise ValueError("v13 run must contain the two successful stages before candidate short-circuit")
    if model.get("configured_max_retries") != 0:
        raise ValueError("v13 run must have retries disabled")
    if run.get("formal_gold") or run.get("database_written") or run.get("fta_ready") or run.get("production_ready"):
        raise ValueError("v13 development run must not be promoted to Gold, database, or readiness")

    tree = run["result"]["outcomes"][0]["tree"]
    if tree.get("status") != "blocked" or "no_fta_event_candidates" not in tree.get("blockers", []):
        raise ValueError("v13 run must fail closed when no cause candidates remain")
    dispositions = tree.get("cause_dispositions", [])
    if len(dispositions) != 16:
        raise ValueError("v13 F01681 run must disposition all 16 extracted causes")
    first = dispositions[0]
    if (
        first.get("semantic_role") != "causal_summary"
        or first.get("disposition") != "relation_only"
        or first.get("reason_code") != "summary_not_independent_event"
    ):
        raise ValueError("v13 run must keep the top-event restatement out of the candidate tree")
    if any(
        item.get("semantic_role") != "diagnostic_mapping"
        or item.get("disposition") != "relation_only"
        for item in dispositions[1:]
    ):
        raise ValueError("v13 run must keep all 15 diagnostic mappings relation-only")
    if len(run.get("model_stage_responses", [])) != 2:
        raise ValueError("v13 run must stop after fault extraction and cause disposition")

    corpus_rows = [
        json.loads(line)
        for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    source = next(
        (row for row in corpus_rows if row.get("sample_id") == run["source"]["sample_id"]),
        None,
    )
    if source is None:
        raise ValueError("v13 run sample is absent from the registered corpus")
    input_text = source.get("input_text")
    if not isinstance(input_text, str) or _sha256_bytes(input_text.encode("utf-8")) != run["source"].get("input_text_sha256"):
        raise ValueError("v13 run input hash does not match the pinned corpus sample")
    for disposition in dispositions:
        for evidence in disposition.get("evidence", []):
            if input_text[evidence["start"]:evidence["end"]] != evidence["quote"]:
                raise ValueError("v13 cause evidence offset is not an exact source slice")

    integrity = run.get("evidence_integrity", {})
    if integrity.get("extraction", {}).get("all_offsets_exact") is not True:
        raise ValueError("v13 extraction evidence offsets did not all validate")
    if integrity.get("extraction", {}).get("failures"):
        raise ValueError("v13 extraction evidence has integrity failures")
    if review.get("review_target", {}).get("run_artifact") != RUN_PATH.relative_to(ROOT).as_posix():
        raise ValueError("independent review does not reference the v13 run")
    if review.get("conclusion") != "PASS" or review.get("reviewer", {}).get("human_expert") is not False:
        raise ValueError("v13 review must be an AI-only PASS, not presented as human expert review")
    if review.get("mutations", {}).get("online_model_calls") != 0 or review.get("mutations", {}).get("files_changed_by_reviewer") is not False:
        raise ValueError("independent review must be read-only and must not call the model")
    review_findings = review.get("findings", {})
    expected_reference_count = (
        integrity["extraction"]["reference_count"]
        + integrity["candidate_tree"]["reference_count"]
        + len(dispositions)
    )
    if review_findings.get("cause_disposition_count") != len(dispositions):
        raise ValueError("AI review cause count does not match the replay")
    if review_findings.get("evidence_integrity", {}).get("reference_count") != expected_reference_count:
        raise ValueError("AI review evidence count does not match the replay evidence ledger")
    if review_findings.get("evidence_integrity", {}).get("offsets_exact") is not True or review_findings.get("evidence_integrity", {}).get("failures"):
        raise ValueError("AI review reports evidence offset failures")
    return run, review


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V12_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v12":
        raise ValueError("v13 must extend the frozen v12 manifest snapshot")
    run, review = _load_and_validate_run()
    tree = run["result"]["outcomes"][0]["tree"]
    counts = {
        "total": len(tree["cause_dispositions"]),
        "causal_summary_relation_only": sum(
            1 for item in tree["cause_dispositions"]
            if item["semantic_role"] == "causal_summary" and item["disposition"] == "relation_only"
        ),
        "diagnostic_mapping_relation_only": sum(
            1 for item in tree["cause_dispositions"]
            if item["semantic_role"] == "diagnostic_mapping" and item["disposition"] == "relation_only"
        ),
    }

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v13"
    manifest["baseline_version"] = "v13"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "one bounded F01681 online development replay under cause disposition v4; all 16 causes remain relation-only and the tree correctly blocks with no eligible event candidates"
    )
    manifest["scope"]["excludes"].append(
        "general accuracy or semantic generalization claims from one F01681 replay and AI-only review, formal expert Gold, database writes, production integration, gate calibration, and FTA readiness"
    )
    manifest["active_baseline"]["f01681_v4_online_model_replay"] = RUN_PATH.relative_to(ROOT).as_posix()
    manifest["active_baseline"]["f01681_v4_independent_ai_review"] = REVIEW_PATH.relative_to(ROOT).as_posix()
    manifest["cause_disposition_v4_policy_regression"]["online_model_rerun"] = True
    manifest["cause_disposition_v4_policy_regression"]["online_model_replay_scope"] = "one F01681 development sample; no accuracy claim"
    manifest["cause_disposition_v4_policy_regression"]["ai_role_review_conclusion"] = "PASS; not a human expert signature"
    manifest["cause_disposition_v4_online_model_replay"] = {
        "status": "single_sample_development_replay_completed_and_ai_role_reviewed",
        "prompt_version": run["prompt_versions"]["cause_disposition"],
        "sample_id": run["source"]["sample_id"],
        "source_input_sha256": run["source"]["input_text_sha256"],
        "model_id": run["model"]["model_id"],
        "provider_host": run["model"]["provider_host"],
        "request_attempt_count": run["model"]["request_attempt_count"],
        "successful_response_count": run["model"]["successful_response_count"],
        "configured_max_retries": run["model"]["configured_max_retries"],
        "stages": [item["stage"] for item in run["model_stage_responses"]],
        "stages_skipped": ["structure_decomposition", "gate_assessment"],
        "cause_disposition_counts": counts,
        "candidate_tree_status": tree["status"],
        "candidate_tree_blockers": tree["blockers"],
        "candidate_tree_node_count": len(tree["nodes"]),
        "candidate_tree_relation_count": len(tree["relations"]),
        "evidence_integrity": run["evidence_integrity"],
        "independent_ai_review": {
            "path": REVIEW_PATH.relative_to(ROOT).as_posix(),
            "conclusion": review["conclusion"],
            "provenance": "ai_subagent_read_only_role_review_not_human_expert",
            "reference_count": review["findings"]["evidence_integrity"]["reference_count"],
            "offsets_exact": review["findings"]["evidence_integrity"]["offsets_exact"],
        },
        "reviewer_provenance": run["reviewer_provenance"],
        "formal_gold": False,
        "database_written": False,
        "accuracy_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v12"],
        "current_version": "v13",
        "reason": "v13 records one F01681 v4 online development replay and an AI-only read-only review; v12 and prior snapshots remain unchanged.",
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
        current = V13_PATH.read_text(encoding="utf-8") if V13_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v13 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v13",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V13_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "written",
        "artifact_count": len(payload["artifacts"]),
        "path": str(V13_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
