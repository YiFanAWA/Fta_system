#!/usr/bin/env python3
"""Build the v3 FTA research baseline from the immutable v2 snapshot."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V2_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v2.json"
V3_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v3.json"

NEW_ARTIFACTS: tuple[dict[str, str], ...] = (
    {
        "artifact_id": "unknown-gate-reason-policy-v1",
        "kind": "runtime_policy",
        "lifecycle": "current_preview_only",
        "path": "backend-python/fta/unknown_gate_reason_policy.py",
        "note": "Maps structured gate blockers and policy outcomes to one deterministic primary unknown reason; never parses free text.",
    },
    {
        "artifact_id": "unknown-gate-reason-policy-tests-v1",
        "kind": "contract_regression_tests",
        "lifecycle": "current",
        "path": "backend-python/tests/test_unknown_gate_reason_policy.py",
        "note": "Covers precedence, known legacy blocker mappings, and explicit legacy_unspecified fallback.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v2-snapshot",
        "kind": "baseline_manifest_snapshot",
        "lifecycle": "immutable_superseded_snapshot",
        "path": "evaluation/quality_eval/fta_baseline_manifest_v2.json",
        "note": "Retained byte-for-byte as the cause-disposition baseline preceding the unknown-gate reason contract.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v2-builder",
        "kind": "reproducibility_tool",
        "lifecycle": "superseded_historical_tool",
        "path": "evaluation/quality_eval/build_fta_baseline_manifest_v2.py",
        "note": "Historical v2 builder; v3 is the current manifest builder and validator target.",
    },
    {
        "artifact_id": "fta-baseline-manifest-v3-builder",
        "kind": "reproducibility_tool",
        "lifecycle": "current",
        "path": "evaluation/quality_eval/build_fta_baseline_manifest_v3.py",
        "note": "Refreshes inherited v2 artifact fingerprints and records the v5 gate reason contract and policy.",
    },
)

UPDATED_NOTES = {
    "backend-python/contracts/candidate_fta_contract.py": (
        "Owns candidate tree v5, the cause disposition ledger, and exactly one validated primary reason for every unknown gate."
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "Runs cause disposition before structure/gate stages and derives unknown gate reason codes from structured evidence, blockers, and policy outcomes."
    ),
    "docs/candidate-fta-generation-v1.md": (
        "Current candidate FTA narrative; tree output contract v5 includes normalized unknown gate reasons."
    ),
    "docs/fta-validation-reliability-plan-v1.md": (
        "Status ledger and ordered execution plan; work items 1-3 are implemented and verified."
    ),
    "docs/README.md": (
        "Internal source-of-truth index points to the active FTA baseline manifest v3."
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "Validates repository-relative artifact paths and SHA-256 fingerprints; defaults to the active v3 snapshot."
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _upsert_artifact(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    original = json.loads(V2_PATH.read_text(encoding="utf-8"))
    manifest = deepcopy(original)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v3"
    manifest["baseline_version"] = "v3"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["supersedes_manifest"] = {
        "manifest_id": original["manifest_id"],
        "path": V2_PATH.relative_to(ROOT).as_posix(),
        "reason": "Candidate tree v5 adds one validated machine-readable primary reason to every unknown gate, with deterministic precedence and explicit legacy mapping.",
    }

    includes = manifest["scope"]["includes"]
    includes[0] = "candidate FTA tree output contract v5 and offline preview implementation"
    includes.append("deterministic unknown-gate reason contract, policy, and legacy blocker mapping")

    active = manifest["active_baseline"]
    active.update(
        {
            "candidate_contract": "candidate_fta_tree_v5",
            "unknown_gate_reason_policy": "unknown_gate_reason_policy_v1",
            "legacy_unknown_reason_policy": "map_known_structured_blockers_else_legacy_unspecified",
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
            {**addition, "sha256": sha256_file(path)},
        )

    manifest["superseded"].append(
        {
            "artifact_family": "candidate_fta_tree_contract",
            "superseded_versions": ["v4"],
            "current_version": "v5",
            "reason": "v5 adds exactly one machine-validated primary reason code for each unknown gate; existing blockers remain secondary details and free-text decision_reason is not parsed.",
        }
    )
    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v2"],
            "current_version": "v3",
            "reason": "v2 remains an immutable historical snapshot; v3 fingerprints the current unknown-gate reason contract and implementation.",
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
        current = V3_PATH.read_text(encoding="utf-8") if V3_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v3 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"])}, ensure_ascii=False))
        return 0
    V3_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V3_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
