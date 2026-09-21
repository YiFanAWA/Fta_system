#!/usr/bin/env python3
"""Build and validate the current dataset lifecycle registry."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from domains.dataset_registry import (  # noqa: E402
    DatasetRegistryError,
    REGISTRY_SCHEMA_VERSION,
    assert_valid_registry,
    count_population,
    load_json_object,
    sha256_file,
    verify_database_import,
)


def _dataset_info(artifact: dict[str, Any]) -> dict[str, Any]:
    value = artifact.get("dataset_info")
    return value if isinstance(value, dict) else {}


def build_registry(source_manifest: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    if source_manifest.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise DatasetRegistryError("unsupported source registry schema version")
    source_entries = source_manifest.get("datasets")
    if not isinstance(source_entries, list) or not source_entries:
        raise DatasetRegistryError("source manifest datasets must be a non-empty list")

    entries: list[dict[str, Any]] = []
    for source_entry in source_entries:
        if not isinstance(source_entry, dict):
            raise DatasetRegistryError("source manifest dataset entry must be an object")
        artifact_path = str(source_entry.get("artifact_path") or "")
        artifact_file = repo_root / artifact_path
        artifact = load_json_object(artifact_file)
        info = _dataset_info(artifact)
        population = str(source_entry.get("population") or "")
        count = count_population(artifact, population)
        database_binding = source_entry.get("database_import")
        if database_binding is None:
            database_import = {
                "status": "not_applicable",
                "database_path": None,
                "dataset_name": None,
                "dataset_version": None,
                "import_id": None,
                "record_count": None,
                "reason": None,
            }
        else:
            database_path = repo_root / str(database_binding["database_path"])
            database_import = verify_database_import(
                database_path,
                dataset_name=str(database_binding["dataset_name"]),
                dataset_version=str(database_binding["dataset_version"]),
                expected_count=count,
            )
            database_import["database_path"] = str(database_binding["database_path"])

        entry = {
            "dataset_id": str(source_entry["dataset_id"]),
            "artifact_path": artifact_path,
            "artifact_sha256": sha256_file(artifact_file),
            "role": str(source_entry["role"]),
            "split": str(source_entry["split"]),
            "population": {"kind": population, "count": count},
            "label_status": info.get("label_status", "unspecified"),
            "expert_status": {
                "human_expert_reviewed": (
                    info.get("human_expert_reviewed")
                    if info.get("human_expert_reviewed") is not None
                    else False
                    if "ai_assisted" in str(info.get("review_authority") or "")
                    else None
                ),
                "review_kind": (
                    "human_expert"
                    if info.get("human_expert_reviewed") is True
                    else "ai_assisted"
                    if "ai_assisted" in str(info.get("review_authority") or "")
                    else "unspecified"
                ),
                "review_authority": info.get("review_authority"),
                "confirmed_records": info.get("confirmed_expert_records"),
            },
            "training_eligible": bool(
                source_entry.get("training_eligible", info.get("training_eligible", False))
            ),
            "logic_status": info.get("logic_policy") or info.get("logic_status"),
            "lifecycle_status": info.get("lifecycle_status") or info.get("split") or "unspecified",
            "gold_source": info.get("source_gold"),
            "metrics": list(source_entry.get("metrics") or []),
            "database_import": database_import,
        }
        entries.append(entry)

    registry = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_id": source_manifest.get("registry_id", "fta_dataset_registry"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "authority": {
            "artifact_labels": "linked dataset artifact dataset_info and samples/queries",
            "database_import_status": "SQLite dataset_imports table",
            "metric_scope": "linked evaluation artifact dataset_info and registry entry metrics",
            "legacy_database_written": "informational_only",
        },
        "datasets": entries,
    }
    assert_valid_registry(registry, repo_root=repo_root, require_artifacts=True)
    return registry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        type=Path,
        default=ROOT / "evaluation" / "quality_eval" / "dataset_registry_sources_v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation" / "quality_eval" / "runs" / "dataset_registry_v1.json",
    )
    args = parser.parse_args()
    try:
        registry = build_registry(load_json_object(args.sources), repo_root=ROOT)
    except DatasetRegistryError as exc:
        raise SystemExit(str(exc)) from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "datasets": len(registry["datasets"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
