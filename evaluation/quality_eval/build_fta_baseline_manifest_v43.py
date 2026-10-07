#!/usr/bin/env python3
"""Build active FTA baseline v43 for explicit observation and gate semantics."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V42_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v42.json"
V43_PATH = ROOT / "evaluation/quality_eval/fta_baseline_manifest_v43.json"

CURRENT_ARTIFACTS = {
    "evaluation/quality_eval/fta_baseline_manifest_v42.json": (
        "fta-baseline-manifest-v42-snapshot", "historical_baseline_manifest", "historical",
        "Immutable v42 snapshot; superseded as active by v43.",
    ),
    "evaluation/quality_eval/build_fta_baseline_manifest_v43.py": (
        "fta-baseline-manifest-v43-builder", "reproducibility_tool", "current",
        "Builds v43 from v42 and records prompt semantic boundaries without a model request.",
    ),
    "evaluation/quality_eval/test_build_fta_baseline_manifest_v43.py": (
        "fta-baseline-manifest-v43-tests", "manifest_regression_tests", "current",
        "Protects v42 immutability, v43 scope, policy source registration, and false readiness.",
    ),
    "backend-python/fta/candidate_fta_extraction_service.py": (
        "candidate-fta-service-semantic-boundary-v1", "production_candidate_service", "current",
        "Makes observation-versus-causation and semantic (not keyword) gate rules explicit; no live model run is included.",
    ),
    "backend-python/tests/test_candidate_fta_extraction_service.py": (
        "candidate-fta-semantic-boundary-tests-v1", "service_regression_tests", "current",
        "Asserts prompt policy boundaries; does not establish model semantic accuracy.",
    ),
    "evaluation/quality_eval/validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-v43-default", "validation_tool", "current",
        "Validates active v43 artifact paths and SHA-256 values.",
    ),
    "evaluation/quality_eval/test_validate_fta_baseline_manifest.py": (
        "fta-baseline-manifest-validator-tests-v43-default", "validation_tool_tests", "current",
        "Covers manifest integrity and active v43 repository snapshot.",
    ),
    "docs/README.md": (
        "fta-v43-doc-index", "current_truth_index", "current",
        "Points to v43 and distinguishes offline prompt policy from live semantic validation.",
    ),
    "docs/current-state-audit.md": (
        "fta-v43-current-state-audit", "current_state_document", "current",
        "Records the disconnected-observation policy and semantic gate decision boundary.",
    ),
    "docs/acceptance.md": (
        "fta-v43-acceptance-record", "acceptance_document", "current",
        "Records offline regression and manifest validation without a live-model accuracy claim.",
    ),
    "docs/candidate-fta-generation-v1.md": (
        "fta-v43-candidate-generation-policy", "current_fta_policy_document", "current",
        "Documents that co-observation is not causal linkage and AND/OR may be inferred semantically with direct evidence.",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register(artifacts: list[dict[str, Any]], relative_path: str, metadata: dict[str, str]) -> None:
    existing = next((item for item in artifacts if item.get("path") == relative_path), None)
    entry = {**(existing or {}), **metadata, "path": relative_path}
    if existing is None:
        artifacts.append(entry)
    else:
        artifacts[artifacts.index(existing)] = entry


def build_manifest(*, captured_at: str | None = None) -> dict[str, Any]:
    source = json.loads(V42_PATH.read_text(encoding="utf-8"))
    if source.get("manifest_id") != "candidate_fta_research_baseline_v42":
        raise ValueError("v43 must derive from the preserved v42 snapshot")
    active = source.get("active_baseline", {})
    if active.get("fta_ready") is not False or active.get("production_ready") is not False:
        raise ValueError("v43 must preserve false FTA and production readiness")

    manifest = deepcopy(source)
    manifest["manifest_id"] = "candidate_fta_research_baseline_v43"
    manifest["baseline_version"] = "v43"
    manifest["captured_at"] = captured_at or date.today().isoformat()
    manifest["supersedes_manifest"] = {
        "manifest_id": "candidate_fta_research_baseline_v42",
        "path": V42_PATH.relative_to(ROOT).as_posix(),
        "reason": "v43 records explicit production candidate-FTA rules for disconnected observations and semantic gate inference; no live-model validation or readiness promotion.",
    }
    manifest["scope"]["includes"].append(
        "offline candidate-FTA prompt rules: preserve co-observed alarms as disconnected review candidates, prohibit unsupported links, and infer AND/OR from directly evidenced proposition semantics rather than keyword presence"
    )
    manifest["scope"]["excludes"].append(
        "live model behavior, semantic accuracy, calibration, expert Gold, formal tree acceptance, database/API changes, and any readiness promotion inferred from offline prompt regression"
    )
    manifest["active_baseline"].update({
        "candidate_fta_observation_link_policy": "retain_disconnected_observation_nodes_and_block_whole_tree_without_causal_evidence_v1",
        "candidate_fta_gate_semantics_policy": "infer_from_complete_propositions_not_operator_keywords_v1",
        "candidate_fta_semantic_prompt_live_validation": False,
        "fta_ready": False,
        "production_ready": False,
    })
    manifest["candidate_fta_semantic_policy_v1"] = {
        "status": "offline_prompt_and_regression_implemented_live_validation_pending",
        "observation_policy": "co-occurrence, simultaneous logging, sequence, or listing does not establish a causal edge or AND/OR membership; preserve evidenced disconnected nodes and block the whole candidate tree",
        "gate_policy": "AND/OR may be inferred without literal operator tokens only when source semantics directly support joint necessity or independent alternative paths to the same output; otherwise unknown",
        "model_request_performed": False,
        "human_expert_gold": False,
        "accuracy_or_calibration_claim_allowed": False,
        "fta_ready": False,
        "production_ready": False,
    }
    manifest["superseded"].append({
        "artifact_family": "fta_baseline_manifest",
        "superseded_versions": ["v42"],
        "current_version": "v43",
        "reason": "v43 registers the offline prompt semantic boundary and regressions; it does not claim live semantic acceptance.",
    })

    repo_root = ROOT.resolve(strict=True)
    for relative_path, (artifact_id, kind, lifecycle, note) in CURRENT_ARTIFACTS.items():
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        _register(manifest["artifacts"], relative_path, {
            "artifact_id": artifact_id, "kind": kind, "lifecycle": lifecycle,
            "note": note, "sha256": _sha256(target),
        })

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in manifest["artifacts"]:
        artifact_id, relative_path = artifact.get("artifact_id"), artifact.get("path")
        if artifact_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"duplicate artifact id or path: {artifact_id} / {relative_path}")
        seen_ids.add(artifact_id)
        seen_paths.add(relative_path)
        target = (ROOT / relative_path).resolve(strict=True)
        if not target.is_relative_to(repo_root):
            raise ValueError(f"artifact escapes repository: {relative_path}")
        artifact["sha256"] = _sha256(target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captured-at", help="ISO date for deterministic regeneration")
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    payload = build_manifest(captured_at=args.captured_at)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = V43_PATH.read_text(encoding="utf-8") if V43_PATH.exists() else None
        if current != rendered:
            parser.exit(1, "FTA baseline manifest v43 differs from generated content\n")
        print(json.dumps({
            "status": "current", "artifact_count": len(payload["artifacts"]),
            "baseline_version": "v43", "model_request_performed": False,
            "fta_ready": payload["active_baseline"]["fta_ready"],
            "production_ready": payload["active_baseline"]["production_ready"],
        }, ensure_ascii=False))
        return 0
    V43_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "artifact_count": len(payload["artifacts"]), "path": str(V43_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
