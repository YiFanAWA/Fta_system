#!/usr/bin/env python3
"""Build the immutable v2 FTA research baseline snapshot from v1 plus current changes."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V1_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v1.json"
V2_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v2.json"

NEW_ARTIFACTS: tuple[dict[str, str], ...] = (
    {
        "artifact_id": "cause-disposition-contract-v1",
        "kind": "runtime_contract",
        "lifecycle": "current_preview_only",
        "path": "backend-python/contracts/fta_cause_disposition_contract.py",
        "note": "Complete per-source-cause semantic role/disposition audit contract; unresolved entries are fail-closed.",
    },
    {
        "artifact_id": "cause-disposition-service-v1",
        "kind": "runtime_implementation",
        "lifecycle": "current_preview_only",
        "path": "backend-python/fta/cause_disposition_service.py",
        "note": "AI-proposed cause classification; unique exact source binding only; missing/ambiguous evidence remains unresolved.",
    },
    {
        "artifact_id": "cause-disposition-contract-tests-v1",
        "kind": "contract_regression_tests",
        "lifecycle": "current",
        "path": "backend-python/tests/test_fta_cause_disposition.py",
        "note": "Covers completeness, duplicate/missing classifications, evidence ambiguity, and role/disposition conflicts.",
    },
    {
        "artifact_id": "fta-reliability-plan-current",
        "kind": "engineering_plan",
        "lifecycle": "current_execution_plan",
        "path": "docs/fta-validation-reliability-plan-v1.md",
        "note": "Status ledger and ordered execution plan; work item 2 is implemented and verified.",
    },
    {
        "artifact_id": "fta-internal-doc-index-current",
        "kind": "internal_document_index",
        "lifecycle": "current",
        "path": "docs/README.md",
        "note": "Internal source-of-truth index points to the active FTA baseline manifest.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v1-snapshot",
        "kind": "baseline_manifest_snapshot",
        "lifecycle": "immutable_superseded_snapshot",
        "path": "evaluation/quality_eval/fta_baseline_manifest_v1.json",
        "note": "Original v1 manifest retained byte-for-byte as the historical pre-disposition baseline.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v2-builder",
        "kind": "reproducibility_tool",
        "lifecycle": "current",
        "path": "evaluation/quality_eval/build_fta_baseline_manifest_v2.py",
        "note": "Rebuilds v2 by refreshing fingerprints for the inherited v1 artifact set and recording additive v2 artifacts.",
    },
    {
        "artifact_id": "fta-baseline-manifest-validation-tests",
        "kind": "reproducibility_tests",
        "lifecycle": "current",
        "path": "evaluation/quality_eval/test_validate_fta_baseline_manifest.py",
        "note": "Validates exact artifact fingerprints and the active repository manifest.",
    },
)

UPDATED_NOTES = {
    "docs/candidate-fta-generation-v1.md": (
        "Current candidate FTA narrative; tree output contract v4 includes the complete cause-disposition audit ledger."
    ),
    "backend-python/contracts/candidate_fta_contract.py": (
        "Owns candidate tree v4, cause disposition ledger, gate, relation, blocker, and non-production readiness projection."
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "Runs cause disposition before structure/gate stages; only eligible source causes enter the tree; unresolved blocks release."
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "Validates repository-relative artifact paths and SHA-256 fingerprints; defaults to the active v2 snapshot."
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _upsert_artifact(
    artifacts: list[dict[str, Any]], entry: dict[str, Any]
) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    original = json.loads(V1_PATH.read_text(encoding="utf-8"))
    manifest = deepcopy(original)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v2"
    manifest["baseline_version"] = "v2"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["supersedes_manifest"] = {
        "manifest_id": original["manifest_id"],
        "path": V1_PATH.relative_to(ROOT).as_posix(),
        "reason": "Candidate tree v4 adds evidence-bound cause role/disposition and fail-closed unresolved handling.",
    }

    includes = manifest["scope"]["includes"]
    includes[0] = "candidate FTA tree output contract v4 and offline preview implementation"
    includes.append("cause semantic role/disposition contract and complete per-cause preview audit ledger")
    active = manifest["active_baseline"]
    active.update(
        {
            "candidate_contract": "candidate_fta_tree_v4",
            "cause_disposition_contract": "fta_cause_disposition_v1",
            "cause_disposition_prompt": "fta-cause-disposition-v1",
            "unresolved_cause_policy": "retain_in_audit_ledger_and_block_whole_candidate_tree",
            "preview_only": True,
            "fta_ready": False,
            "production_ready": False,
        }
    )

    artifacts = manifest["artifacts"]
    for artifact in artifacts:
        path = ROOT / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest artifact is missing: {artifact['path']}")
        artifact["sha256"] = sha256_file(path)
        if artifact["path"] in UPDATED_NOTES:
            artifact["note"] = UPDATED_NOTES[artifact["path"]]

    for addition in NEW_ARTIFACTS:
        path = ROOT / addition["path"]
        if not path.is_file():
            raise FileNotFoundError(f"new manifest artifact is missing: {addition['path']}")
        _upsert_artifact(
            artifacts,
            {
                **addition,
                "sha256": sha256_file(path),
            },
        )

    superseded = manifest["superseded"]
    superseded.append(
        {
            "artifact_family": "candidate_fta_tree_contract",
            "superseded_versions": ["v3"],
            "current_version": "v4",
            "reason": "v4 adds a complete auditable cause role/disposition ledger; non-tree and unresolved causes are no longer forced into nodes.",
        }
    )
    superseded.append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v1"],
            "current_version": "v2",
            "reason": "v1 remains an immutable historical snapshot; v2 fingerprints the current cause-disposition contract and implementation.",
        }
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic snapshot regeneration")
    parser.add_argument("--check", action="store_true", help="compare generated content without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V2_PATH.read_text(encoding="utf-8") if V2_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v2 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"])}, ensure_ascii=False))
        return 0
    V2_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V2_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
