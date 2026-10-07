#!/usr/bin/env python3
"""Validate scoped FTA readiness assessments without changing production readiness."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
    ROOT
    / "evaluation"
    / "quality_eval"
    / "runs"
    / "fta_scoped_readiness_assessment_v1_2026-09-28.json"
)
STATUSES = {"ready_within_scope", "not_ready", "blocked", "not_assessed", "not_applicable"}
CRITERION_RESULTS = {"met", "unmet", "unknown", "not_applicable"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReadinessReportValidationError(ValueError):
    """Raised when a scoped readiness report is malformed or overclaims readiness."""


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReadinessReportValidationError(f"{field} must be a non-empty string")
    return value


def _resolve_json_pointer(payload: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ReadinessReportValidationError("manifest_ref must contain a JSON Pointer")
    current = payload
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ReadinessReportValidationError(f"manifest_ref does not resolve: {pointer}")
    return current


def _validate_track(track: Any, *, name: str) -> dict[str, int]:
    if not isinstance(track, dict):
        raise ReadinessReportValidationError(f"{name} must be an object")
    status = track.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ReadinessReportValidationError(f"{name}.status is unsupported")
    criteria = track.get("criteria")
    blockers = track.get("blockers")
    if not isinstance(criteria, list) or not criteria:
        raise ReadinessReportValidationError(f"{name}.criteria must be a non-empty list")
    if not isinstance(blockers, list) or any(not isinstance(item, str) or not item.strip() for item in blockers):
        raise ReadinessReportValidationError(f"{name}.blockers must be a list of non-empty strings")

    ids: set[str] = set()
    results: list[str] = []
    evidence_count = 0
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            raise ReadinessReportValidationError(f"{name}.criteria[{index}] must be an object")
        criterion_id = _require_nonempty_string(criterion.get("criterion_id"), f"{name}.criteria[{index}].criterion_id")
        if criterion_id in ids:
            raise ReadinessReportValidationError(f"{name} has duplicate criterion_id: {criterion_id}")
        ids.add(criterion_id)
        result = criterion.get("result")
        if not isinstance(result, str) or result not in CRITERION_RESULTS:
            raise ReadinessReportValidationError(f"{name}.criteria[{index}].result is unsupported")
        references = criterion.get("evidence_refs")
        if not isinstance(references, list) or not references or any(not isinstance(ref, str) or not ref.strip() for ref in references):
            raise ReadinessReportValidationError(f"{name}.criteria[{index}].evidence_refs must be a list of non-empty strings")
        evidence_count += len(references)
        results.append(result)

    if status == "ready_within_scope":
        if any(result not in {"met", "not_applicable"} for result in results):
            raise ReadinessReportValidationError(f"{name} cannot be ready with unmet or unassessed criteria")
        if blockers:
            raise ReadinessReportValidationError(f"{name} cannot be ready with blockers")
        if evidence_count == 0:
            raise ReadinessReportValidationError(f"{name} cannot be ready without evidence references")
    elif status == "not_ready" and "unmet" not in results:
        raise ReadinessReportValidationError(f"{name} not_ready requires an unmet criterion")
    elif status == "blocked" and not (blockers or "unknown" in results or "unmet" in results):
        raise ReadinessReportValidationError(f"{name} blocked requires a blocker or unresolved criterion")
    elif status == "not_assessed" and any(result != "unknown" for result in results):
        raise ReadinessReportValidationError(f"{name} not_assessed may only contain unknown criteria")
    elif status == "not_applicable" and any(result != "not_applicable" for result in results):
        raise ReadinessReportValidationError(f"{name} not_applicable may only contain not_applicable criteria")

    return {
        "status": status,
        "criterion_count": len(criteria),
        "evidence_ref_count": evidence_count,
        "blocker_count": len(blockers),
    }


def validate_readiness_report(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ReadinessReportValidationError("report root must be an object")
    if payload.get("schema") != "fta_scoped_readiness_report_v1":
        raise ReadinessReportValidationError("unsupported scoped FTA readiness report schema")
    _require_nonempty_string(payload.get("assessment_id"), "assessment_id")
    try:
        date.fromisoformat(_require_nonempty_string(payload.get("assessed_at"), "assessed_at"))
    except ValueError as exc:
        raise ReadinessReportValidationError("assessed_at must be an ISO date") from exc

    baseline = payload.get("baseline")
    if not isinstance(baseline, dict):
        raise ReadinessReportValidationError("baseline must be an object")
    for field in ("manifest_id", "version", "path"):
        _require_nonempty_string(baseline.get(field), f"baseline.{field}")
    if not isinstance(baseline.get("sha256"), str) or not _SHA256.fullmatch(baseline["sha256"]):
        raise ReadinessReportValidationError("baseline.sha256 must be lowercase SHA-256")
    baseline_path = Path(baseline["path"])
    if baseline_path.is_absolute() or ".." in baseline_path.parts:
        raise ReadinessReportValidationError("baseline.path must stay repo-relative")
    baseline_target = (ROOT / baseline_path).resolve(strict=False)
    if not baseline_target.is_relative_to(ROOT.resolve(strict=True)) or not baseline_target.is_file():
        raise ReadinessReportValidationError("baseline.path must resolve to a repository file")
    actual_hash = hashlib.sha256(baseline_target.read_bytes()).hexdigest()
    if actual_hash != baseline["sha256"]:
        raise ReadinessReportValidationError("baseline.sha256 does not match the pinned manifest")
    try:
        baseline_payload = json.loads(baseline_target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReadinessReportValidationError("pinned baseline manifest is invalid JSON") from exc

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        raise ReadinessReportValidationError("scope must be an object")
    for field in ("scope_id", "domain", "description", "inclusion_rule", "source_split_policy"):
        _require_nonempty_string(scope.get(field), f"scope.{field}")
    boundary_notes = scope.get("scope_boundary_notes")
    if not isinstance(boundary_notes, list) or not boundary_notes or any(not isinstance(note, str) or not note.strip() for note in boundary_notes):
        raise ReadinessReportValidationError("scope.scope_boundary_notes must be a non-empty list of strings")
    for field in ("case_count", "source_cluster_count"):
        value = scope.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ReadinessReportValidationError(f"scope.{field} must be a non-negative integer")
    included_sets = scope.get("included_sets")
    if not isinstance(included_sets, list) or not included_sets:
        raise ReadinessReportValidationError("scope.included_sets must be a non-empty list")
    included_ids: set[str] = set()
    included_cluster_ids: dict[str, set[str]] = {}
    pinned_sources_by_set: dict[str, dict[str, dict[str, str]]] = {}
    for index, item in enumerate(included_sets):
        if not isinstance(item, dict):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}] must be an object")
        set_id = _require_nonempty_string(item.get("set_id"), f"scope.included_sets[{index}].set_id")
        _require_nonempty_string(item.get("role"), f"scope.included_sets[{index}].role")
        if set_id in included_ids:
            raise ReadinessReportValidationError(f"scope has duplicate set_id: {set_id}")
        included_ids.add(set_id)
        for field in ("case_count", "source_cluster_count"):
            value = item.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ReadinessReportValidationError(f"scope.included_sets[{index}].{field} must be a non-negative integer")
        manifest_ref = _require_nonempty_string(item.get("manifest_ref"), f"scope.included_sets[{index}].manifest_ref")
        expected_prefix = f"{baseline['path']}#"
        if not manifest_ref.startswith(expected_prefix):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].manifest_ref must point into the pinned baseline")
        source_manifest_item = _resolve_json_pointer(baseline_payload, manifest_ref[len(expected_prefix):])
        if not isinstance(source_manifest_item, dict):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].manifest_ref must resolve to an object")
        dataset_artifacts = item.get("dataset_artifacts")
        if not isinstance(dataset_artifacts, list) or not dataset_artifacts:
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].dataset_artifacts must be a non-empty list")
        dataset_case_count = 0
        dataset_paths: set[str] = set()
        for artifact_index, artifact in enumerate(dataset_artifacts):
            if not isinstance(artifact, dict):
                raise ReadinessReportValidationError(
                    f"scope.included_sets[{index}].dataset_artifacts[{artifact_index}] must be an object"
                )
            for field in ("dataset_path", "dataset_sha256"):
                _require_nonempty_string(
                    artifact.get(field),
                    f"scope.included_sets[{index}].dataset_artifacts[{artifact_index}].{field}",
                )
            if not _SHA256.fullmatch(artifact["dataset_sha256"]):
                raise ReadinessReportValidationError(
                    f"scope.included_sets[{index}].dataset_artifacts[{artifact_index}].dataset_sha256 must be lowercase SHA-256"
                )
            if artifact["dataset_path"] in dataset_paths:
                raise ReadinessReportValidationError(f"scope.included_sets[{index}] has duplicate dataset paths")
            dataset_paths.add(artifact["dataset_path"])
            dataset_relative_path = Path(artifact["dataset_path"])
            if dataset_relative_path.is_absolute() or ".." in dataset_relative_path.parts:
                raise ReadinessReportValidationError("included dataset paths must stay repo-relative")
            dataset_target = (ROOT / dataset_relative_path).resolve(strict=False)
            if not dataset_target.is_relative_to(ROOT.resolve(strict=True)) or not dataset_target.is_file():
                raise ReadinessReportValidationError(f"included dataset does not resolve within repo: {artifact['dataset_path']}")
            if hashlib.sha256(dataset_target.read_bytes()).hexdigest() != artifact["dataset_sha256"]:
                raise ReadinessReportValidationError(f"included dataset hash mismatch: {artifact['dataset_path']}")
            artifact_case_count = artifact.get("case_count")
            if isinstance(artifact_case_count, bool) or not isinstance(artifact_case_count, int) or artifact_case_count < 0:
                raise ReadinessReportValidationError(
                    f"scope.included_sets[{index}].dataset_artifacts[{artifact_index}].case_count must be a non-negative integer"
                )
            dataset_case_count += artifact_case_count
        if dataset_case_count != item["case_count"]:
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].case_count must equal dataset artifact counts")
        manifest_datasets = source_manifest_item.get("dataset_suites")
        if isinstance(manifest_datasets, list):
            expected_dataset_artifacts = [
                {
                    "dataset_path": dataset.get("dataset_path"),
                    "dataset_sha256": dataset.get("dataset_sha256"),
                    "case_count": dataset.get("sample_count"),
                }
                for dataset in manifest_datasets
            ]
        else:
            dataset_path = source_manifest_item.get("dataset_path")
            manifest_artifact = next(
                (artifact for artifact in baseline_payload.get("artifacts", []) if artifact.get("path") == dataset_path),
                None,
            )
            expected_dataset_artifacts = [{
                "dataset_path": dataset_path,
                "dataset_sha256": manifest_artifact.get("sha256") if isinstance(manifest_artifact, dict) else None,
                "case_count": source_manifest_item.get("sample_count"),
            }]
        if sorted(dataset_artifacts, key=lambda artifact: artifact["dataset_path"]) != sorted(
            expected_dataset_artifacts, key=lambda artifact: artifact["dataset_path"] or ""
        ):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].dataset_artifacts differ from the pinned manifest")
        if item["case_count"] != source_manifest_item.get("sample_count"):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].case_count differs from the pinned manifest")
        cluster_ids = item.get("source_cluster_ids")
        if not isinstance(cluster_ids, list) or len(cluster_ids) != item["source_cluster_count"]:
            raise ReadinessReportValidationError(
                f"scope.included_sets[{index}].source_cluster_ids must match source_cluster_count"
            )
        if any(not isinstance(cluster_id, str) or not cluster_id.strip() for cluster_id in cluster_ids):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].source_cluster_ids must contain non-empty strings")
        if len(set(cluster_ids)) != len(cluster_ids):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}] has duplicate source cluster ids")
        manifest_clusters = source_manifest_item.get("source_clusters")
        if not isinstance(manifest_clusters, list):
            raise ReadinessReportValidationError(f"scope.included_sets[{index}] pinned manifest lacks source_clusters")
        if set(cluster_ids) != {source.get("source_cluster_id") for source in manifest_clusters if isinstance(source, dict)}:
            raise ReadinessReportValidationError(f"scope.included_sets[{index}].source_cluster_ids differ from the pinned manifest")
        included_cluster_ids[set_id] = set(cluster_ids)
        pinned_sources_by_set[set_id] = {
            source["source_cluster_id"]: {
                "source_id": source.get("source_id"),
                "source_hash_type": source.get("source_hash_type") or ("source_pdf_sha256" if source.get("source_pdf_sha256") else None),
                "source_sha256": source.get("source_sha256") or source.get("source_pdf_sha256"),
            }
            for source in manifest_clusters
            if isinstance(source, dict) and isinstance(source.get("source_cluster_id"), str)
        }
    if sum(item["case_count"] for item in included_sets) != scope["case_count"]:
        raise ReadinessReportValidationError("scope.case_count must equal included set counts")
    if sum(item["source_cluster_count"] for item in included_sets) != scope["source_cluster_count"]:
        raise ReadinessReportValidationError("scope.source_cluster_count must equal included set counts")

    excluded_sets = scope.get("excluded_sets")
    if not isinstance(excluded_sets, list):
        raise ReadinessReportValidationError("scope.excluded_sets must be a list")
    all_set_ids = set(included_ids)
    for index, item in enumerate(excluded_sets):
        if not isinstance(item, dict):
            raise ReadinessReportValidationError(f"scope.excluded_sets[{index}] must be an object")
        set_id = _require_nonempty_string(item.get("set_id"), f"scope.excluded_sets[{index}].set_id")
        if set_id in all_set_ids:
            raise ReadinessReportValidationError(f"scope has duplicate included/excluded set_id: {set_id}")
        all_set_ids.add(set_id)
        _require_nonempty_string(item.get("status"), f"scope.excluded_sets[{index}].status")
        _require_nonempty_string(item.get("reason"), f"scope.excluded_sets[{index}].reason")
        for field in ("case_count", "source_cluster_count"):
            value = item.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ReadinessReportValidationError(f"scope.excluded_sets[{index}].{field} must be a non-negative integer")

    source_clusters = scope.get("source_clusters")
    if not isinstance(source_clusters, list) or len(source_clusters) != scope["source_cluster_count"]:
        raise ReadinessReportValidationError("scope.source_clusters must account for every included source cluster")
    cluster_ids_seen: set[str] = set()
    allocated_clusters: dict[str, set[str]] = {set_id: set() for set_id in included_ids}
    for index, source in enumerate(source_clusters):
        if not isinstance(source, dict):
            raise ReadinessReportValidationError(f"scope.source_clusters[{index}] must be an object")
        source_id = _require_nonempty_string(source.get("source_id"), f"scope.source_clusters[{index}].source_id")
        cluster_id = _require_nonempty_string(source.get("source_cluster_id"), f"scope.source_clusters[{index}].source_cluster_id")
        allocation = _require_nonempty_string(source.get("allocation_set_id"), f"scope.source_clusters[{index}].allocation_set_id")
        _require_nonempty_string(source.get("source_hash_type"), f"scope.source_clusters[{index}].source_hash_type")
        source_hash = source.get("source_sha256")
        if not isinstance(source_hash, str) or not _SHA256.fullmatch(source_hash):
            raise ReadinessReportValidationError(f"scope.source_clusters[{index}].source_sha256 must be lowercase SHA-256")
        if cluster_id in cluster_ids_seen:
            raise ReadinessReportValidationError("scope.source_clusters contains duplicate source cluster ids")
        if allocation not in included_cluster_ids:
            raise ReadinessReportValidationError(f"scope.source_clusters[{index}] has unknown allocation_set_id")
        pinned_source = pinned_sources_by_set[allocation].get(cluster_id)
        if pinned_source is None or pinned_source != {
            "source_id": source_id,
            "source_hash_type": source["source_hash_type"],
            "source_sha256": source_hash,
        }:
            raise ReadinessReportValidationError(f"scope.source_clusters[{index}] differs from the pinned source provenance")
        cluster_ids_seen.add(cluster_id)
        allocated_clusters[allocation].add(cluster_id)
    if allocated_clusters != included_cluster_ids:
        raise ReadinessReportValidationError("scope source-cluster allocations do not match included set declarations")

    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, dict):
        raise ReadinessReportValidationError("assessment_provenance must be an object")
    _require_nonempty_string(provenance.get("method"), "assessment_provenance.method")
    for field in ("model_inference_run", "human_expert_reviewed"):
        if not isinstance(provenance.get(field), bool):
            raise ReadinessReportValidationError(f"assessment_provenance.{field} must be boolean")
    _require_nonempty_string(provenance.get("reviewer_role"), "assessment_provenance.reviewer_role")
    _require_nonempty_string(provenance.get("reviewer_provenance"), "assessment_provenance.reviewer_provenance")
    if provenance["human_expert_reviewed"] and provenance["reviewer_role"] != "domain_expert":
        raise ReadinessReportValidationError("human_expert_reviewed requires reviewer_role=domain_expert")

    configuration = payload.get("evaluation_configuration")
    if not isinstance(configuration, dict):
        raise ReadinessReportValidationError("evaluation_configuration must be an object")
    for field in ("candidate_contract", "cause_disposition_prompt", "model_inference_status", "code_scope"):
        _require_nonempty_string(configuration.get(field), f"evaluation_configuration.{field}")
    if configuration["model_inference_status"] == "not_run" and provenance["model_inference_run"]:
        raise ReadinessReportValidationError("model inference provenance conflicts with evaluation_configuration")

    structure = _validate_track(payload.get("structure_readiness"), name="structure_readiness")
    quantitative = _validate_track(payload.get("quantitative_readiness"), name="quantitative_readiness")
    if quantitative["status"] == "ready_within_scope" and structure["status"] != "ready_within_scope":
        raise ReadinessReportValidationError("quantitative readiness requires structure readiness in the same scope")

    global_readiness = payload.get("global_readiness")
    if not isinstance(global_readiness, dict):
        raise ReadinessReportValidationError("global_readiness must be an object")
    if global_readiness.get("fta_ready") is not False or global_readiness.get("production_ready") is not False:
        raise ReadinessReportValidationError("scoped assessment must not change global FTA/production readiness")
    if global_readiness.get("scope_can_promote_global_readiness") is not False:
        raise ReadinessReportValidationError("a scoped assessment cannot promote global readiness")

    return {
        "assessment_id": payload["assessment_id"],
        "scope_id": scope["scope_id"],
        "case_count": scope["case_count"],
        "source_cluster_count": scope["source_cluster_count"],
        "excluded_set_count": len(excluded_sets),
        "structure_status": payload["structure_readiness"]["status"],
        "quantitative_status": payload["quantitative_readiness"]["status"],
        "fta_ready": False,
        "production_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
        result = validate_readiness_report(payload)
    except (OSError, json.JSONDecodeError, ReadinessReportValidationError) as exc:
        parser.exit(1, f"FTA scoped readiness report invalid: {exc}\n")
    print(json.dumps({"status": "valid", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
