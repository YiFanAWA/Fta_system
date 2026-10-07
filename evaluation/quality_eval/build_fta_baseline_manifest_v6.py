#!/usr/bin/env python3
"""Build the v6 FTA baseline with source-disjoint public diagram development data."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V5_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v5.json"
V6_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v6.json"
DEV_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_gate_diagram_development_v1.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _upsert_artifact(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_development_suite(previous: dict[str, Any]) -> dict[str, Any]:
    fixture = _load_json(DEV_PATH)
    if fixture.get("dataset_role") != "development_only" or fixture.get("formal_gold") is not False:
        raise ValueError("new public diagram fixture must remain development-only and non-Gold")
    if fixture.get("in_project_gold") is not False or fixture.get("fta_ready") is not False:
        raise ValueError("development fixture cannot promote project Gold or FTA readiness")

    sources = fixture.get("sources")
    nodes = fixture.get("gate_nodes")
    if not isinstance(sources, list) or not isinstance(nodes, list) or not nodes:
        raise ValueError("development fixture must contain sources and gate_nodes")
    if fixture.get("source_document_count") != len(sources):
        raise ValueError("development source document count mismatch")
    source_map: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = source.get("source_id")
        cluster_id = source.get("source_cluster_id")
        relative_path = source.get("source_pdf_path")
        declared_hash = source.get("source_pdf_sha256")
        if not all(isinstance(value, str) and value.strip() for value in (source_id, cluster_id, relative_path)):
            raise ValueError("each development source requires source, cluster, and repo-relative PDF paths")
        if not isinstance(declared_hash, str) or not SHA256_RE.fullmatch(declared_hash):
            raise ValueError(f"invalid declared source hash for {source_id}")
        pdf_path = (ROOT / relative_path).resolve(strict=True)
        if not pdf_path.is_relative_to(ROOT.resolve()):
            raise ValueError(f"source PDF path escapes repository: {relative_path}")
        if sha256_file(pdf_path) != declared_hash:
            raise ValueError(f"source PDF fingerprint mismatch: {relative_path}")
        if source_id in source_map:
            raise ValueError(f"duplicate development source id: {source_id}")
        source_map[source_id] = source

    source_clusters = {source["source_cluster_id"] for source in sources}
    if fixture.get("source_cluster_count") != len(source_clusters) or len(source_clusters) != len(sources):
        raise ValueError("development fixture must declare one distinct source cluster per source document")
    regression_clusters = {
        item["source_cluster_id"]
        for item in previous["behavior_regression_suite"]["source_clusters"]
    }
    if not source_clusters.isdisjoint(regression_clusters):
        raise ValueError("development source cluster overlaps the frozen seen regression suite")

    seen_node_ids: set[str] = set()
    label_counts: Counter[str] = Counter()
    counts_by_source: dict[str, Counter[str]] = {source_id: Counter() for source_id in source_map}
    for node in nodes:
        node_id = node.get("gate_node_id")
        source = source_map.get(node.get("source_id"))
        if not isinstance(node_id, str) or not node_id or node_id in seen_node_ids:
            raise ValueError("development gate node ids must be unique and non-empty")
        seen_node_ids.add(node_id)
        if source is None or node.get("source_cluster_id") != source["source_cluster_id"]:
            raise ValueError(f"source/cluster mismatch for {node_id}")
        if node.get("expected_gate") not in {"AND", "OR"}:
            raise ValueError(f"diagram fixture labels must be explicit AND/OR values: {node_id}")
        if not isinstance(node.get("label_evidence"), dict) or not node["label_evidence"].get("quote"):
            raise ValueError(f"label evidence quote is required for {node_id}")
        if not isinstance(node.get("children"), list) or len(node["children"]) < 2:
            raise ValueError(f"at least two direct child events are required for {node_id}")
        label_counts[node["expected_gate"]] += 1
        counts_by_source[source["source_id"]][node["expected_gate"]] += 1

    if {node["source_cluster_id"] for node in nodes} != source_clusters:
        raise ValueError("every development source cluster must contribute at least one gate node")

    return {
        "suite_id": "public-diagram-gate-development-v1",
        "status": "allocated_development_not_formal_gold",
        "purpose": "Development and failure analysis on source-pinned public FTA diagram labels.",
        "dataset_path": DEV_PATH.relative_to(ROOT).as_posix(),
        "sample_count": len(nodes),
        "unique_case_count": len(seen_node_ids),
        "source_document_count": len(sources),
        "source_cluster_count": len(source_clusters),
        "label_counts": {label: label_counts[label] for label in ("AND", "OR")},
        "formal_gold": False,
        "training_set": False,
        "accuracy_claim_allowed": False,
        "inference_input_fields": ["parent_event", "direct_child_events"],
        "source_clusters": [
            {
                "source_id": source["source_id"],
                "source_cluster_id": source["source_cluster_id"],
                "source_pdf_path": source["source_pdf_path"],
                "source_pdf_sha256": source["source_pdf_sha256"],
                "gate_node_count": sum(node["source_id"] == source["source_id"] for node in nodes),
                "label_counts": {label: counts_by_source[source["source_id"]][label] for label in ("AND", "OR")},
            }
            for source in sources
        ],
        "overlap_with_seen_behavior_regression": False,
        "final_test_eligible": False,
        "scope_note": fixture["scope_note"],
    }


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = _load_json(V5_PATH)
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v5":
        raise ValueError("v6 must extend the immutable active v5 manifest")
    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v6"
    manifest["baseline_version"] = "v6"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["supersedes_manifest"] = {
        "manifest_id": previous["manifest_id"],
        "path": V5_PATH.relative_to(ROOT).as_posix(),
        "reason": "v6 keeps the 36 seen cases as regression, adds an 11-node public diagram development set from three entirely new source-document clusters, and keeps independent Final uncreated.",
    }
    manifest["scope"]["includes"].append(
        "11 public FTA diagram gate-label development cases from three source-document clusters disjoint from the 36-case seen regression suite"
    )
    manifest["scope"]["excludes"].append("independent final validation results; all newly acquired source documents are allocated to development")
    development = build_development_suite(previous)
    manifest["development_gate_suite"] = development
    manifest["active_baseline"]["development_gate_suite"] = development["suite_id"]
    manifest["independent_final_validation"] = {
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "The new DOE, FAA SRM, and NASA documents are allocated wholly to development. No unseen source clusters remain allocated to an independent Final; acquire different whole documents only after model, prompt, policy, and parser freeze.",
        "required_before_creation": [
            "acquire new complete source documents/clusters not present in seen regression or development",
            "freeze model, prompt, policy, and parser before opening final labels",
            "record population, source hashes, provenance, per-class support, selective risk/coverage, and failure cases",
        ],
    }
    manifest["source_cluster_allocation"] = {
        "split_unit": "source_document_cluster",
        "seen_behavior_regression_cluster_count": previous["behavior_regression_suite"]["source_cluster_count"],
        "development_cluster_count": development["source_cluster_count"],
        "development_clusters": [item["source_cluster_id"] for item in development["source_clusters"]],
        "independent_final_validation": {"status": "not_created", "source_clusters": []},
        "development_overlaps_seen_regression": False,
        "same_document_may_be_split_across_partitions": False,
        "allocation_rule": "All gate nodes from one complete source document belong to one partition; do not split a manual across development and final validation.",
    }

    additions: list[dict[str, str]] = [
        {
            "artifact_id": "fta-baseline-manifest-v5-snapshot",
            "kind": "baseline_manifest_snapshot",
            "lifecycle": "immutable_superseded_snapshot",
            "path": "evaluation/quality_eval/fta_baseline_manifest_v5.json",
            "note": "Retained unchanged as the previous active baseline; v6 adds source-disjoint development material while preserving the seen regression and uncreated Final boundary.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v6-builder",
            "kind": "reproducibility_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/build_fta_baseline_manifest_v6.py",
            "note": "Builds v6 from immutable v5 plus the source-pinned development fixture and verifies new PDF fingerprints and source-cluster separation.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v6-tests",
            "kind": "manifest_regression_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v6.py",
            "note": "Checks the new development scope, counts, source-cluster separation, Final boundary, and artifact hashes.",
        },
        {
            "artifact_id": "fta-gate-diagram-development-v1-fixture",
            "kind": "development_input_not_gold",
            "lifecycle": "development_only_not_final_test",
            "path": DEV_PATH.relative_to(ROOT).as_posix(),
            "note": "11 explicit diagram-gate cases across three complete source-document clusters; not project Gold and not independent Final Test.",
        },
        {
            "artifact_id": "fta-gate-diagram-development-v1-tests",
            "kind": "fixture_regression_tests",
            "lifecycle": "current_regression_support",
            "path": "evaluation/quality_eval/public_sources/test_fta_gate_diagram_development_v1.py",
            "note": "Verifies pinned PDF hashes, exact evidence quotes, source-cluster split integrity, and prompt-label/provenance withholding.",
        },
        {
            "artifact_id": "fta-gate-source-doe-hdbk-1100-2022",
            "kind": "public_source_pdf",
            "lifecycle": "development_source",
            "path": "evaluation/quality_eval/public_sources/source_pdfs/DOE-HDBK-1100-2004-ReaffOct2022.pdf",
            "note": "DOE chemical process hazard analysis handbook, reaffirmed 2022; development source cluster only.",
        },
        {
            "artifact_id": "fta-gate-source-faa-srm-2024",
            "kind": "public_source_pdf",
            "lifecycle": "development_source",
            "path": "evaluation/quality_eval/public_sources/source_pdfs/FAA-SRM-Guidance-2024.pdf",
            "note": "FAA Safety Risk Management Guidance, June 2024; development source cluster only.",
        },
        {
            "artifact_id": "fta-gate-source-nasa-tm-103953",
            "kind": "public_source_pdf",
            "lifecycle": "development_source",
            "path": "evaluation/quality_eval/public_sources/source_pdfs/NASA-FDIR-Report-1994.pdf",
            "note": "NASA Technical Memorandum 103953; development source cluster only.",
        },
    ]
    for entry in additions:
        path = ROOT / entry["path"]
        if not path.is_file():
            raise FileNotFoundError(f"new v6 artifact is missing: {entry['path']}")
        _upsert_artifact(manifest["artifacts"], {**entry, "sha256": sha256_file(path)})

    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest artifact is missing: {artifact['path']}")
        artifact["sha256"] = sha256_file(path)

    for path, note in (
        ("evaluation/quality_eval/validate_fta_baseline_manifest.py", "Validates repository-relative artifact paths and SHA-256 fingerprints; defaults to active v6 snapshot."),
        ("evaluation/quality_eval/test_validate_fta_baseline_manifest.py", "Tests the active v6 manifest path and rejects missing, duplicate, escaped, or changed artifacts."),
        ("docs/README.md", "Internal source-of-truth index points to active FTA baseline manifest v6 and its source-cluster-separated development set."),
        ("docs/candidate-fta-generation-v1.md", "Current candidate FTA narrative; links active manifest v6 and preserves preview-only boundaries."),
        ("docs/fta-validation-reliability-plan-v1.md", "Status ledger records the 36-case regression, 11-case/3-cluster development set, and still-uncreated independent Final Test."),
    ):
        artifact = next((item for item in manifest["artifacts"] if item["path"] == path), None)
        if artifact is not None:
            artifact["sha256"] = sha256_file(ROOT / path)
            artifact["note"] = note

    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v5"],
            "current_version": "v6",
            "reason": "v6 adds a fully source-pinned development set from three unseen source documents, verifies it is disjoint from the frozen 15-cluster regression suite, and retains the independent Final status as not_created.",
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
        current = V6_PATH.read_text(encoding="utf-8") if V6_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v6 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"]), "development_cases": payload["development_gate_suite"]["sample_count"], "development_source_clusters": payload["development_gate_suite"]["source_cluster_count"], "final_status": payload["independent_final_validation"]["status"]}, ensure_ascii=False))
        return 0
    V6_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "development_cases": payload["development_gate_suite"]["sample_count"], "development_source_clusters": payload["development_gate_suite"]["source_cluster_count"], "final_status": payload["independent_final_validation"]["status"], "path": str(V6_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
