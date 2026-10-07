#!/usr/bin/env python3
"""Build the v14 baseline with the F01681 Remedy 9507 scope reconciliation."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V13_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v13.json"
V14_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v14.json"
REVIEW_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.json"
CORPUS_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "siemens_s210_public_fault_corpus_v1.jsonl"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v13.json": (
        "fta-baseline-manifest-v13-snapshot", "baseline_manifest_snapshot", "superseded_snapshot",
        "Immutable v13 snapshot; records the bounded F01681 v4 live replay and AI-only review.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v14.py": (
        "fta-baseline-manifest-v14-builder", "reproducibility_tool", "current",
        "Builds v14 from v13 and validates the F01681 Remedy 9507 scope review against the pinned corpus.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v14.py": (
        "fta-baseline-manifest-v14-tests", "manifest_regression_tests", "current",
        "Checks scope status, source offsets, AI-only provenance, immutable v13, and readiness boundaries.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v14-default", "validation_tool", "current",
        "Validates repository paths and hashes; defaults to active v14.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v14-default", "validation_tool_tests", "current",
        "Validates active v14 and general path/hash failure cases.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.json": (
        "siemens-s210-f01681-remedy-9507-scope-review", "source_scope_reconciliation_review", "current_development_review",
        "Read-only review: Remedy-only evidence; no candidate event; cause-scope completeness remains unresolved.",
    ),
    "evaluation/quality_eval/runs/siemens_s210_f01681_remedy_9507_scope_review_v1_2026-09-28.md": (
        "siemens-s210-f01681-remedy-9507-scope-review-report", "source_scope_reconciliation_report", "current_development_review",
        "Human-readable evidence and limits for the F01681 Remedy 9507 scope reconciliation.",
    ),
    "docs/README.md": (
        "fta-v14-doc-index", "current_truth_index", "current", "Points to active FTA baseline v14.",
    ),
    "docs/current-state-audit.md": (
        "fta-v14-current-state-audit", "current_state_document", "current",
        "Records F01681 Remedy 9507 as remedy-only and keeps cause-scope completeness unresolved.",
    ),
    "docs/acceptance.md": (
        "fta-v14-acceptance-record", "acceptance_document", "current",
        "Records v14 scope reconciliation validation and readiness boundaries.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v14-candidate-generation-policy", "candidate_fta_policy_document", "current",
        "Documents the source-grounded F01681 Remedy scope finding without adding a tree event.",
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "fta-v14-validation-plan-policy", "validation_plan_document", "current",
        "Tracks the F01681 cause/remedy scope discrepancy and unresolved completeness blocker.",
    ),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upsert(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def _load_review_and_validate_source() -> tuple[dict[str, Any], str]:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sample_id = "SIEMENS_S210_2019_F01681"
    source = next((row for row in rows if row.get("sample_id") == sample_id), None)
    if source is None:
        raise ValueError("F01681 sample is missing from the pinned public corpus")
    text = source.get("input_text")
    if not isinstance(text, str):
        raise ValueError("F01681 input_text must be a string")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if review.get("source", {}).get("input_text_sha256") != digest:
        raise ValueError("review source hash does not match the pinned F01681 corpus text")
    if review.get("source", {}).get("sample_id") != sample_id:
        raise ValueError("review targets the wrong F01681 sample")
    for evidence in review.get("evidence", []):
        start, end, quote = evidence.get("start"), evidence.get("end"), evidence.get("quote")
        if not isinstance(start, int) or not isinstance(end, int) or text[start:end] != quote:
            raise ValueError("review evidence offset is not an exact source slice")
        if text.count(quote) != evidence.get("occurrence_count"):
            raise ValueError("review evidence occurrence count does not match the pinned source")

    remedy_start = text.index("Remedy: Correct parameters:")
    token = "xxxx = 9507:"
    if text.count(token) != 1 or text[:remedy_start].count(token) != 0:
        raise ValueError("xxxx=9507 must appear exactly once, in the Remedy section only")
    if review.get("assessment", {}).get("candidate_event_added") is not False:
        raise ValueError("the Remedy branch must not be promoted to an FTA event")
    if review.get("assessment", {}).get("cause_set_completeness") != "unresolved":
        raise ValueError("cause-set completeness must remain unresolved")
    reviewer = review.get("reviewer", {})
    if reviewer.get("human_expert") is not False or reviewer.get("human_signature") is not False:
        raise ValueError("AI role review must not be represented as a human expert signature")
    mutations = review.get("mutations", {})
    if any(mutations.get(key) is not False for key in (
        "gold_changed", "database_written", "production_api_changed", "fta_readiness_changed"
    )):
        raise ValueError("scope review must not modify Gold, database, production API, or readiness")
    return review, text


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = json.loads(V13_PATH.read_text(encoding="utf-8"))
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v13":
        raise ValueError("v14 must extend the frozen v13 manifest snapshot")
    review, _ = _load_review_and_validate_source()

    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v14"
    manifest["baseline_version"] = "v14"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["scope"]["includes"].append(
        "one source-pinned F01681 Remedy xxxx=9507 scope reconciliation; treat as remedy-only, add no cause/tree event, and keep cause-set completeness unresolved"
    )
    manifest["scope"]["excludes"].append(
        "causal event or causal edge inferred from the F01681 Remedy xxxx=9507 instruction; closed cause-scope/completeness claim from this single branch"
    )
    manifest["active_baseline"]["f01681_remedy_9507_scope_review"] = REVIEW_PATH.relative_to(ROOT).as_posix()
    manifest["f01681_remedy_9507_scope_reconciliation"] = {
        "status": "reviewed_remedy_only_scope_completeness_unresolved",
        "sample_id": review["source"]["sample_id"],
        "source_input_sha256": review["source"]["input_text_sha256"],
        "review_artifact": REVIEW_PATH.relative_to(ROOT).as_posix(),
        "review_conclusion": review["reviewer"]["conclusion"],
        "evidence_offsets": [
            {"start": item["start"], "end": item["end"], "section": item["section"]}
            for item in review["evidence"]
        ],
        "source_occurrence_audit": review["scope_audit"],
        "candidate_event_added": False,
        "causal_edge_supported": False,
        "cause_set_completeness": "unresolved",
        "review_provenance": "ai_subagent_read_only_role_review_not_human_expert",
        "formal_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v13"],
        "current_version": "v14",
        "reason": "v14 adds a source-grounded F01681 Remedy 9507 scope review; v13 and earlier manifest files are left unchanged.",
    })

    root = ROOT.resolve(strict=True)
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
    for artifact in manifest["artifacts"]:
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        artifact["sha256"] = sha256_file(target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic regeneration")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V14_PATH.read_text(encoding="utf-8") if V14_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v14 differs from generated content\n")
        print(json.dumps({
            "status": "current",
            "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v14",
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V14_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V14_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
