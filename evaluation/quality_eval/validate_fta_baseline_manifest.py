#!/usr/bin/env python3
"""Validate repository paths and SHA-256 fingerprints in the FTA baseline manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v52.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ManifestValidationError(ValueError):
    """Raised when the manifest is malformed, escapes the repo, or has drifted."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(payload: dict[str, Any], *, repo_root: Path) -> dict[str, int]:
    if payload.get("manifest_schema") != "fta_baseline_manifest_v1":
        raise ManifestValidationError("unsupported FTA baseline manifest schema")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ManifestValidationError("artifacts must be a non-empty list")

    seen_ids: set[str] = set()
    verified = 0
    root = repo_root.resolve(strict=True)
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ManifestValidationError(f"artifacts[{index}] must be an object")
        artifact_id = artifact.get("artifact_id")
        relative_path = artifact.get("path")
        expected_hash = artifact.get("sha256")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise ManifestValidationError(f"artifacts[{index}].artifact_id is required")
        if artifact_id in seen_ids:
            raise ManifestValidationError(f"duplicate artifact_id: {artifact_id}")
        seen_ids.add(artifact_id)
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ManifestValidationError(f"artifacts[{index}].path is required")
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ManifestValidationError(f"artifact path must stay repo-relative: {relative_path}")
        if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
            raise ManifestValidationError(f"artifacts[{index}].sha256 must be lowercase SHA-256")

        target = (root / relative).resolve(strict=False)
        if not target.is_relative_to(root):
            raise ManifestValidationError(f"artifact path escapes repository: {relative_path}")
        if not target.is_file():
            raise ManifestValidationError(f"artifact file is missing: {relative_path}")
        actual_hash = sha256_file(target)
        if actual_hash != expected_hash:
            raise ManifestValidationError(
                f"artifact hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )
        verified += 1

    return {"artifact_count": len(artifacts), "verified_count": verified}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ManifestValidationError("manifest root must be an object")
        result = validate_manifest(payload, repo_root=args.repo_root)
    except (OSError, json.JSONDecodeError, ManifestValidationError) as exc:
        parser.exit(1, f"FTA baseline manifest invalid: {exc}\n")
    print(json.dumps({"status": "valid", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
