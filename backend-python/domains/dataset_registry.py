"""Dataset registry contract and validation helpers.

The registry is the single read model for dataset lifecycle and evaluation
scope. Dataset artifacts remain the source of truth for their own labels;
SQLite ``dataset_imports`` remains the source of truth for actual database
imports. This module only joins and validates those facts.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping


REGISTRY_SCHEMA_VERSION = 1
_REQUIRED_ENTRY_FIELDS = {
    "dataset_id",
    "artifact_path",
    "role",
    "split",
    "population",
    "label_status",
    "expert_status",
    "training_eligible",
    "lifecycle_status",
}
_DATABASE_STATUSES = {"completed", "not_applicable", "not_verified", "inconsistent"}


class DatasetRegistryError(ValueError):
    """Raised when a registry or its linked state is invalid."""


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load a JSON object and reject non-object payloads."""

    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DatasetRegistryError(f"cannot read JSON artifact: {source}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetRegistryError(f"invalid JSON artifact: {source}") from exc
    if not isinstance(value, dict):
        raise DatasetRegistryError(f"JSON artifact must be an object: {source}")
    return value


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of a local artifact."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_population(artifact: Mapping[str, Any], population: str) -> int:
    """Count the declared population in a dataset artifact."""

    if population not in {"samples", "queries"}:
        raise DatasetRegistryError(f"unsupported population: {population!r}")
    values = artifact.get(population)
    if not isinstance(values, list):
        raise DatasetRegistryError(f"artifact has no list population: {population}")
    return len(values)


def verify_database_import(
    database_path: str | Path,
    *,
    dataset_name: str,
    dataset_version: str,
    expected_count: int,
) -> dict[str, Any]:
    """Verify actual import state from SQLite without changing the database."""

    path = Path(database_path)
    result: dict[str, Any] = {
        "status": "not_verified",
        "database_path": str(path),
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "import_id": None,
        "record_count": None,
        "reason": None,
    }
    if not path.exists():
        result["reason"] = "database_file_missing"
        return result

    try:
        connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        result["reason"] = f"database_open_failed:{type(exc).__name__}"
        return result
    try:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'dataset_imports'"
        ).fetchone()
        if table is None:
            result["reason"] = "dataset_imports_table_missing"
            return result
        row = connection.execute(
            "SELECT import_id, status, record_count FROM dataset_imports "
            "WHERE dataset_name = ? AND dataset_version = ?",
            (dataset_name, dataset_version),
        ).fetchone()
        if row is None:
            result["reason"] = "dataset_import_row_missing"
            return result
        import_id, status, record_count = row
        result.update(
            {
                "import_id": import_id,
                "record_count": int(record_count),
                "source_status": status,
            }
        )
        if status == "completed" and int(record_count) == expected_count:
            result["status"] = "completed"
            return result
        result["status"] = "inconsistent"
        result["reason"] = "database_import_status_or_count_mismatch"
        return result
    except sqlite3.Error as exc:
        result["reason"] = f"database_query_failed:{type(exc).__name__}"
        return result
    finally:
        connection.close()


def validate_registry(
    registry: Mapping[str, Any],
    *,
    repo_root: str | Path,
    require_artifacts: bool = True,
) -> list[str]:
    """Return validation errors; an empty list means the registry is valid."""

    errors: list[str] = []
    if registry.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        errors.append("unsupported registry_schema_version")
    entries = registry.get("datasets")
    if not isinstance(entries, list) or not entries:
        errors.append("datasets must be a non-empty list")
        return errors

    root = Path(repo_root).resolve()
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"datasets[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = _REQUIRED_ENTRY_FIELDS - set(entry)
        errors.extend(f"{prefix} missing {field}" for field in sorted(missing))
        dataset_id = entry.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}.dataset_id must be non-empty")
        elif dataset_id in seen_ids:
            errors.append(f"duplicate dataset_id: {dataset_id}")
        else:
            seen_ids.add(dataset_id)

        artifact_path = entry.get("artifact_path")
        if not isinstance(artifact_path, str) or Path(artifact_path).is_absolute():
            errors.append(f"{prefix}.artifact_path must be a relative path")
        elif require_artifacts and not (root / artifact_path).exists():
            errors.append(f"{prefix}.artifact_path does not exist: {artifact_path}")

        if not isinstance(entry.get("population"), dict):
            errors.append(f"{prefix}.population must be an object")
        if not isinstance(entry.get("training_eligible"), bool):
            errors.append(f"{prefix}.training_eligible must be boolean")
        database_import = entry.get("database_import")
        if not isinstance(database_import, dict):
            errors.append(f"{prefix}.database_import must be an object")
        elif database_import.get("status") not in _DATABASE_STATUSES:
            errors.append(f"{prefix}.database_import.status is invalid")

    return errors


def assert_valid_registry(
    registry: Mapping[str, Any],
    *,
    repo_root: str | Path,
    require_artifacts: bool = True,
) -> None:
    """Raise a single actionable error when registry validation fails."""

    errors = validate_registry(registry, repo_root=repo_root, require_artifacts=require_artifacts)
    if errors:
        raise DatasetRegistryError("invalid dataset registry:\n- " + "\n- ".join(errors))
