#!/usr/bin/env python3
"""Build the v5 FTA baseline with previously-seen gate probes frozen as regressions."""

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
V4_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v4.json"
V5_PATH = ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v5.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

DATASET_SPECS: tuple[dict[str, str], ...] = (
    {
        "suite_id": "text-evidence-ablation-v1",
        "path": "evaluation/quality_eval/datasets/fta_gate_text_evidence_ablation_v1.json",
        "evidence_mode": "decisive_text_evidence_withheld_control",
        "invariant_family": "withheld_evidence_must_abstain",
        "probe_path": "evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1",
        "run_path": "evaluation/quality_eval/runs/fta_gate_text_evidence_ablation_v1_2026-09-27.json",
    },
    {
        "suite_id": "multisource-diagram-v1",
        "path": "evaluation/quality_eval/datasets/fta_gate_multisource_diagram_external_test_v1.json",
        "evidence_mode": "explicit_diagram_or_caption_label",
        "invariant_family": "match_explicit_source_gate",
        "probe_path": "evaluation/quality_eval/public_sources/probe_multisource_fta_gate_external_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_multisource_fta_gate_external_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_multisource_fta_gate_external_v1",
        "run_path": "evaluation/quality_eval/runs/fta_gate_multisource_external_probe_v1_2026-09-27.json",
    },
    {
        "suite_id": "faa-ast-diagram-v1",
        "path": "evaluation/quality_eval/datasets/faa_ast_gate_diagram_external_test_v1.json",
        "evidence_mode": "explicit_diagram_gate_symbol",
        "invariant_family": "match_explicit_source_gate",
        "probe_path": "evaluation/quality_eval/public_sources/probe_faa_ast_fta_gate_external_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_faa_ast_fta_gate_external_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_faa_ast_fta_gate_external_v1",
        "run_path": "evaluation/quality_eval/runs/faa_ast_fta_gate_external_probe_v1_2026-09-27.json",
    },
    {
        "suite_id": "text-abstention-external-v1",
        "path": "evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_external_test_v1.json",
        "evidence_mode": "direct_text_gate_evidence_or_insufficient_scope",
        "invariant_family": "text_gate_evidence_and_abstention",
        "probe_path": "evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1",
        "run_path": "evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_probe_v1_2026-09-27.json",
    },
    {
        "suite_id": "text-abstention-extension-v1",
        "path": "evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v1.json",
        "evidence_mode": "direct_text_gate_evidence_or_insufficient_scope",
        "invariant_family": "text_gate_evidence_and_abstention",
        "probe_path": "evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1",
        "run_path": "evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v1_2026-09-27.json",
    },
    {
        "suite_id": "text-abstention-extension-v2",
        "path": "evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v2.json",
        "evidence_mode": "direct_text_gate_evidence_or_insufficient_scope",
        "invariant_family": "text_gate_evidence_and_abstention",
        "probe_path": "evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py",
        "test_path": "evaluation/quality_eval/public_sources/test_probe_fta_gate_text_evidence_abstention_v1.py",
        "test_module": "evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1",
        "run_path": "evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v2_2026-09-27.json",
    },
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _valid_digest(value: Any, *, context: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value.lower()):
        raise ValueError(f"missing valid SHA-256 for {context}")
    return value.lower()


def _source_records(fixture: dict[str, Any], spec: dict[str, str]) -> list[dict[str, Any]]:
    sources = fixture.get("sources")
    if isinstance(sources, list) and sources:
        records: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError(f"source entries must be objects in {spec['path']}")
            source_id = source.get("source_id")
            cluster_id = source.get("source_cluster_id")
            if not isinstance(source_id, str) or not source_id.strip() or source_id in seen_ids:
                raise ValueError(f"source IDs must be unique non-empty strings in {spec['path']}")
            if not isinstance(cluster_id, str) or not cluster_id.strip():
                raise ValueError(f"source cluster is required for {source_id}")
            seen_ids.add(source_id)
            digest_field = "source_pdf_sha256" if source.get("source_pdf_sha256") else "source_text_sha256"
            digest = _valid_digest(source.get(digest_field), context=source_id)
            records.append(
                {
                    "source_id": source_id,
                    "source_cluster_id": cluster_id,
                    "document_title": source.get("document_title"),
                    "source_hash_type": digest_field,
                    "source_sha256": digest,
                    "source_location": source.get("source_location"),
                }
            )
        declared_sources = fixture.get("source_document_count")
        declared_clusters = fixture.get("source_cluster_count")
        if declared_sources != len(records):
            raise ValueError(f"source_document_count mismatch in {spec['path']}")
        if declared_clusters != len({record["source_cluster_id"] for record in records}):
            raise ValueError(f"source_cluster_count mismatch in {spec['path']}")
        return records

    # The FAA AST fixture represents one source document at fixture level rather than
    # repeating source identity on every gate node. Its PDF fingerprint is the stable
    # source-cluster identity for this inventory.
    title = fixture.get("source_document")
    digest = _valid_digest(fixture.get("source_pdf_sha256"), context=spec["path"])
    if not isinstance(title, str) or not title.strip() or fixture.get("source_cluster_count") != 1:
        raise ValueError(f"single-document source metadata is incomplete in {spec['path']}")
    return [
        {
            "source_id": "faa_ast_guide_v1",
            "source_cluster_id": f"source-sha256:{digest}",
            "document_title": title,
            "source_hash_type": "source_pdf_sha256",
            "source_sha256": digest,
            "source_location": fixture.get("source_figures"),
        }
    ]


def _case_evidence_reference(
    row: dict[str, Any], source: dict[str, Any], *, evidence_mode: str
) -> dict[str, Any]:
    expected_quote = row.get("expected_gate_evidence")
    label_evidence = row.get("label_evidence")
    if isinstance(expected_quote, str) and expected_quote.strip():
        return {
            "reference_type": "direct_text_quote",
            "field": "expected_gate_evidence",
            "quote_sha256": sha256_bytes(expected_quote.encode("utf-8")),
            "quote_length_chars": len(expected_quote),
        }
    if isinstance(label_evidence, dict) and label_evidence:
        quote = label_evidence.get("quote")
        return {
            "reference_type": "source_label_evidence",
            "field": "label_evidence",
            "evidence_kind": label_evidence.get("kind"),
            "quote_sha256": sha256_bytes(quote.encode("utf-8")) if isinstance(quote, str) else None,
            "locator": {
                key: label_evidence[key]
                for key in ("figure_id", "printed_page", "pdf_page")
                if key in label_evidence
            },
        }
    if row.get("figure_id"):
        return {
            "reference_type": "explicit_diagram_gate_symbol",
            "field": "source_figure",
            "locator": {
                key: row[key]
                for key in ("figure_id", "printed_page", "pdf_page")
                if key in row
            },
        }
    return {
        "reference_type": "no_decisive_gate_quote_in_model_visible_scope",
        "field": "expected_gate_evidence",
        "quote_sha256": None,
        "ablation_control": evidence_mode == "decisive_text_evidence_withheld_control",
        "source_sha256": source["source_sha256"],
    }


def build_regression_suite(repo_root: Path = ROOT) -> dict[str, Any]:
    suites: list[dict[str, Any]] = []
    all_cases: list[dict[str, Any]] = []
    source_index: dict[str, dict[str, Any]] = {}
    source_cluster_by_hash: dict[str, str] = {}
    source_hash_by_cluster: dict[str, str] = {}
    seen_case_ids: set[str] = set()

    for spec in DATASET_SPECS:
        fixture_path = repo_root / spec["path"]
        fixture_raw = fixture_path.read_bytes()
        fixture = json.loads(fixture_raw.decode("utf-8"))
        if not isinstance(fixture, dict):
            raise ValueError(f"fixture must be an object: {spec['path']}")
        if fixture.get("formal_gold") is not False or fixture.get("in_project_gold") is not False:
            raise ValueError(f"previously used fixture must remain non-Gold: {spec['path']}")
        rows = fixture.get("gate_nodes")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"fixture has no gate_nodes: {spec['path']}")

        sources = _source_records(fixture, spec)
        # A fixture may express source identity with a document-specific cluster ID,
        # while another fixture can only expose the same source's immutable content
        # hash. Canonicalize these aliases by the hash before counting clusters.
        for source in sources:
            digest = source["source_sha256"]
            declared_cluster = source["source_cluster_id"]
            prior_cluster = source_cluster_by_hash.get(digest)
            if prior_cluster is not None:
                source["source_cluster_id"] = prior_cluster
            else:
                source_cluster_by_hash[digest] = declared_cluster
            canonical_cluster = source["source_cluster_id"]
            prior_digest = source_hash_by_cluster.get(canonical_cluster)
            if prior_digest is not None and prior_digest != digest:
                raise ValueError(f"source-cluster hash conflict: {canonical_cluster}")
            source_hash_by_cluster[canonical_cluster] = digest

        source_by_id = {source["source_id"]: source for source in sources}
        for source in sources:
            cluster_id = source["source_cluster_id"]
            prior = source_index.get(cluster_id)
            if prior and prior["source_sha256"] != source["source_sha256"]:
                raise ValueError(f"source-cluster hash conflict: {cluster_id}")
            if prior:
                prior["fixture_paths"].append(spec["path"])
            else:
                source_index[cluster_id] = {
                    **source,
                    "fixture_paths": [spec["path"]],
                }

        suite_counts: Counter[str] = Counter()
        case_ids: set[str] = set()
        case_records: list[dict[str, Any]] = []
        for row in rows:
            case_id = row.get("gate_node_id")
            gate = row.get("expected_gate")
            if not isinstance(case_id, str) or not case_id.strip() or case_id in case_ids or case_id in seen_case_ids:
                raise ValueError(f"gate_node_id must be unique across all fixtures: {case_id}")
            if gate not in {"AND", "OR", "unknown"}:
                raise ValueError(f"invalid expected gate for {case_id}: {gate}")
            case_ids.add(case_id)
            seen_case_ids.add(case_id)
            suite_counts[gate] += 1

            source_id = row.get("source_id")
            if source_id is None and len(sources) == 1:
                source = sources[0]
                source_id = source["source_id"]
            else:
                source = source_by_id.get(source_id)
            if source is None:
                raise ValueError(f"unknown or ambiguous source for {case_id}")
            row_cluster = row.get("source_cluster_id")
            if row_cluster is not None and row_cluster != source["source_cluster_id"]:
                raise ValueError(f"source cluster mismatch for {case_id}")

            reference = _case_evidence_reference(row, source, evidence_mode=spec["evidence_mode"])
            if gate in {"AND", "OR"} and reference["reference_type"] == "no_decisive_gate_quote_in_model_visible_scope":
                raise ValueError(f"positive gate lacks a source evidence reference: {case_id}")
            if gate == "unknown" and reference["reference_type"] != "no_decisive_gate_quote_in_model_visible_scope":
                raise ValueError(f"unknown gate unexpectedly has decisive evidence: {case_id}")

            invariants = ["gate_node_identity_preserved", "source_cluster_identity_preserved"]
            if gate == "unknown":
                invariants.append("do_not_force_and_or_without_direct_gate_evidence")
            else:
                invariants.append("gate_label_must_be_supported_by_pinned_source_reference")
            if spec["invariant_family"] == "withheld_evidence_must_abstain":
                if gate != "unknown":
                    raise ValueError(f"evidence-ablation controls must expect unknown: {case_id}")
                invariants.append("withheld_decisive_evidence_must_remain_unknown")
            if reference["reference_type"] == "explicit_diagram_gate_symbol":
                invariants.append("use_figure_gate_symbol_not_parent_child_wording_as_label_evidence")

            case_record = {
                "gate_node_id": case_id,
                "source_id": source_id,
                "source_cluster_id": source["source_cluster_id"],
                "expected_gate": gate,
                "evidence_mode": spec["evidence_mode"],
                "source_reference": {
                    "dataset_path": spec["path"],
                    "source_document_title": source.get("document_title"),
                    "source_hash_type": source["source_hash_type"],
                    "source_sha256": source["source_sha256"],
                    **reference,
                },
                "expected_invariants": invariants,
            }
            if row.get("scope_type"):
                case_record["scope_type"] = row["scope_type"]
            if row.get("paired_original_node_id"):
                case_record["paired_original_node_id"] = row["paired_original_node_id"]
            case_records.append(case_record)
            all_cases.append(case_record)

        probe_path = repo_root / spec["probe_path"]
        test_path = repo_root / spec["test_path"]
        run_path = repo_root / spec["run_path"]
        for required in (probe_path, test_path, run_path):
            if not required.is_file():
                raise FileNotFoundError(f"regression evidence is missing: {required.relative_to(repo_root)}")

        provenance = fixture.get("label_provenance")
        suites.append(
            {
                "suite_id": spec["suite_id"],
                "dataset_path": spec["path"],
                "dataset_sha256": sha256_bytes(fixture_raw),
                "artifact_type": fixture.get("artifact_type"),
                "artifact_version": fixture.get("artifact_version"),
                "sample_count": len(case_records),
                "source_cluster_count": len({case["source_cluster_id"] for case in case_records}),
                "label_counts": dict(sorted(suite_counts.items())),
                "label_provenance": provenance,
                "formal_gold": False,
                "in_project_gold": False,
                "previously_used_in_probe": True,
                "final_test_eligible": False,
                "evidence_mode": spec["evidence_mode"],
                "invariant_family": spec["invariant_family"],
                "offline_test_command": f"python -m unittest {spec['test_module']} -v",
                "probe_script_path": spec["probe_path"],
                "test_file_path": spec["test_path"],
                "historical_probe_run": {
                    "path": spec["run_path"],
                    "sha256": sha256_file(run_path),
                    "role": "historical_model_probe_output_not_accuracy_claim",
                },
                "cases": case_records,
            }
        )

    counts = Counter(case["expected_gate"] for case in all_cases)
    if len(all_cases) != 36 or len(seen_case_ids) != 36:
        raise ValueError(f"expected 36 unique previously-used cases, found {len(all_cases)}")
    if dict(counts) != {"AND": 9, "OR": 15, "unknown": 12}:
        raise ValueError(f"regression label counts changed: {dict(counts)}")
    if len(source_index) != 15:
        raise ValueError(f"expected 15 distinct source clusters, found {len(source_index)}")

    return {
        "suite_id": "fta_gate_behavior_regression_v1",
        "status": "frozen_seen_behavior_regression",
        "purpose": "Protect known evidence, abstention, diagram-label, and scope behaviors; not an independent accuracy estimate.",
        "formal_gold": False,
        "training_set": False,
        "accuracy_claim_allowed": False,
        "sample_count": len(all_cases),
        "unique_case_count": len(seen_case_ids),
        "source_cluster_count": len(source_index),
        "label_counts": {label: counts.get(label, 0) for label in ("AND", "OR", "unknown")},
        "source_clusters": [source_index[key] for key in sorted(source_index)],
        "dataset_suites": suites,
        "cases": all_cases,
        "future_split_policy": {
            "split_unit": "source_cluster",
            "existing_cases_are_seen": True,
            "new_development_source_clusters_must_be_disjoint_from_final": True,
            "final_test_must_be_sealed_until_model_prompt_and_rules_are_frozen": True,
            "if_final_results_are_used_for_tuning": "reclassify_as_development_or_regression_and_collect_a_new_final_set",
            "source_cluster_overlap_with_this_regression_suite_for_final": "forbidden",
        },
    }


def _upsert_artifact(artifacts: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if artifact.get("path") == entry["path"]:
            artifacts[index] = {**artifact, **entry}
            return
    artifacts.append(entry)


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    previous = _load_json(V4_PATH)
    if previous.get("manifest_id") != "candidate_fta_research_baseline_v4":
        raise ValueError("v5 must be based on the immutable active v4 manifest")
    manifest = deepcopy(previous)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v5"
    manifest["baseline_version"] = "v5"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["lifecycle_status"] = "active_research_reference_baseline"
    manifest["supersedes_manifest"] = {
        "manifest_id": previous["manifest_id"],
        "path": V4_PATH.relative_to(ROOT).as_posix(),
        "reason": "Freezes all previously-used public gate probes as a source-pinned behavior regression corpus and explicitly keeps independent final validation uncreated until new untouched source clusters are acquired.",
    }
    manifest["scope"]["includes"].append(
        "36 previously-used public gate probes frozen as source-pinned behavior regressions; independent final validation remains uncreated"
    )
    manifest["scope"]["excludes"].append("unseen independent final gate validation results")
    manifest["behavior_regression_suite"] = build_regression_suite()
    manifest["independent_final_validation"] = {
        "status": "not_created",
        "sample_count": 0,
        "source_cluster_count": 0,
        "reason": "All currently available 36 labeled gate cases have already been used in exploratory probes; no untouched source-cluster holdout exists.",
        "required_before_creation": [
            "acquire new source documents/clusters not present in the frozen regression suite",
            "freeze model, prompt, policy, and parser before opening final labels",
            "record population, source hashes, provenance, per-class support, selective risk/coverage, and failure cases",
        ],
    }

    regression_specs_by_path = {spec["path"]: spec for spec in DATASET_SPECS}
    suites_by_path = {suite["dataset_path"]: suite for suite in manifest["behavior_regression_suite"]["dataset_suites"]}
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest artifact is missing: {artifact['path']}")
        artifact["sha256"] = sha256_file(path)
        if artifact["path"] in regression_specs_by_path:
            suite = suites_by_path[artifact["path"]]
            artifact["lifecycle"] = "seen_behavior_regression_input_not_final_test"
            artifact["note"] = (
                f"Frozen previously-used fixture: {suite['sample_count']} cases, {suite['source_cluster_count']} source clusters; "
                "not project Gold and not eligible as independent final validation."
            )
        if artifact["path"] in {
            suite["historical_probe_run"]["path"]
            for suite in manifest["behavior_regression_suite"]["dataset_suites"]
        }:
            artifact["lifecycle"] = "historical_probe_output_not_accuracy_claim"
            artifact["note"] = "Prior exploratory model output retained as regression history; not an independent accuracy result."

    additions: list[dict[str, str]] = [
        {
            "artifact_id": "fta-baseline-manifest-v4-snapshot",
            "kind": "baseline_manifest_snapshot",
            "lifecycle": "immutable_superseded_snapshot",
            "path": "evaluation/quality_eval/fta_baseline_manifest_v4.json",
            "note": "Retained unchanged as the previous active baseline; v5 adds the seen-case regression inventory and keeps Final Test explicitly uncreated.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v5-builder",
            "kind": "reproducibility_tool",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/build_fta_baseline_manifest_v5.py",
            "note": "Builds the v5 baseline and source-pinned regression inventory from immutable v4 plus the six current fixture inputs.",
        },
        {
            "artifact_id": "fta-baseline-manifest-v5-tests",
            "kind": "manifest_regression_tests",
            "lifecycle": "current",
            "path": "evaluation/quality_eval/test_build_fta_baseline_manifest_v5.py",
            "note": "Checks counts, source clusters, evidence-mode invariants, seen/final separation, and hashes for the regression inventory.",
        },
    ]
    for artifact in additions:
        path = ROOT / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(f"new manifest artifact is missing: {artifact['path']}")
        _upsert_artifact(manifest["artifacts"], {**artifact, "sha256": sha256_file(path)})

    for suite in manifest["behavior_regression_suite"]["dataset_suites"]:
        spec = next(spec for spec in DATASET_SPECS if spec["path"] == suite["dataset_path"])
        for kind, path in (
            ("behavior_regression_input", spec["path"]),
            ("probe_script", spec["probe_path"]),
            ("fixture_regression_test", spec["test_path"]),
            ("historical_probe_run", spec["run_path"]),
        ):
            entry = {
                "artifact_id": f"regression-v1-{kind}-{hashlib.sha256(path.encode('utf-8')).hexdigest()[:12]}",
                "kind": kind,
                "lifecycle": "seen_behavior_regression_input_not_final_test" if kind == "behavior_regression_input" else (
                    "historical_probe_output_not_accuracy_claim" if kind == "historical_probe_run" else "current_regression_support"
                ),
                "path": path,
                "note": f"Regression suite {suite['suite_id']}; {suite['sample_count']} cases; not independent Final Test.",
                "sha256": sha256_file(ROOT / path),
            }
            _upsert_artifact(manifest["artifacts"], entry)

    for path, note in (
        ("evaluation/quality_eval/validate_fta_baseline_manifest.py", "Validates repository-relative artifact paths and SHA-256 fingerprints; defaults to active v5 snapshot."),
        ("evaluation/quality_eval/test_validate_fta_baseline_manifest.py", "Tests the active v5 manifest path and rejects missing, duplicate, escaped, or changed artifacts."),
        ("docs/README.md", "Internal source-of-truth index points to active FTA baseline manifest v5 and the frozen seen-case regression boundary."),
        ("docs/candidate-fta-generation-v1.md", "Current candidate FTA narrative; links active manifest v5 and preserves preview-only boundaries."),
        ("docs/fta-validation-reliability-plan-v1.md", "Status ledger records the frozen 36-case seen regression corpus and the still-uncreated independent Final Test."),
    ):
        artifact = next((item for item in manifest["artifacts"] if item["path"] == path), None)
        if artifact is not None:
            artifact["sha256"] = sha256_file(ROOT / path)
            artifact["note"] = note

    manifest["superseded"].append(
        {
            "artifact_family": "fta_baseline_manifest",
            "superseded_versions": ["v4"],
            "current_version": "v5",
            "reason": "v5 explicitly freezes the 36 previously-used labeled gate probes as behavior regression data, records their source/evidence identity, and states that an independent Final Test has not yet been created.",
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
        current = V5_PATH.read_text(encoding="utf-8") if V5_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v5 differs from generated content\n")
        print(json.dumps({"status": "current", "artifact_count": len(payload["artifacts"]), "regression_cases": payload["behavior_regression_suite"]["sample_count"]}, ensure_ascii=False))
        return 0
    V5_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "regression_cases": payload["behavior_regression_suite"]["sample_count"], "path": str(V5_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
