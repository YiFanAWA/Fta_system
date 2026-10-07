#!/usr/bin/env python3
"""Compare one saved semantic-smoke response to its separate non-Gold expectation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = ROOT / "evaluation/quality_eval/datasets/fta_event_scope_semantic_smoke_reference_v1.json"
RUNS_DIR = ROOT / "evaluation/quality_eval/runs"
CASE_ID_PATTERN = re.compile(r"^SMOKE-\d{3}$")


class ComparisonError(ValueError):
    """Raised when a saved run cannot be compared safely."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_paths(case_id: str) -> tuple[Path, Path, Path]:
    if not CASE_ID_PATTERN.fullmatch(case_id):
        raise ComparisonError("case_id must use the fixed SMOKE-NNN format")
    stem = f"fta_event_scope_semantic_smoke_{case_id.lower()}_v1_2026-09-29"
    return (
        RUNS_DIR / f"{stem}.json",
        RUNS_DIR / f"{stem}_assessment.json",
        RUNS_DIR / f"{stem}_offline_comparison.json",
    )


def compare_saved_run(
    case_id: str,
    *,
    run_path: Path | None = None,
    assessment_path: Path | None = None,
    reference_path: Path = REFERENCE_PATH,
) -> dict[str, Any]:
    default_run, default_assessment, _ = _run_paths(case_id)
    run_path = run_path or default_run
    assessment_path = assessment_path or default_assessment
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    if run.get("artifact_type") != "fta_event_scope_semantic_smoke_run" or run.get("status") != "response_received":
        raise ComparisonError("comparison requires a saved successful response_received run")
    if run.get("case", {}).get("case_id") != case_id or assessment.get("case_id") != case_id:
        raise ComparisonError("run and assessment case ids must match the requested case")
    if reference.get("reference_status") != "authored_policy_reference_not_expert_reviewed":
        raise ComparisonError("reference must remain explicitly non-expert policy expectations")
    if reference.get("human_expert_gold") is not False or reference.get("accuracy_claim_allowed") is not False:
        raise ComparisonError("reference cannot be used as expert Gold or accuracy data")

    reference_cases = [item for item in reference.get("cases", []) if item.get("case_id") == case_id]
    if len(reference_cases) != 1:
        raise ComparisonError("reference must contain exactly one case matching the run")
    parsed = run.get("model_output", {}).get("parsed_json")
    if not isinstance(parsed, dict):
        raise ComparisonError("saved run does not contain a parsed JSON object")
    gates = parsed.get("gates")
    if not isinstance(gates, list) or len(gates) != 1 or not isinstance(gates[0], dict):
        raise ComparisonError("this smoke comparison expects exactly one gate scope")

    expected = reference_cases[0]
    observed_gate = gates[0].get("gate")
    expected_gate = expected.get("expected_candidate_gate")
    observed_evidence = gates[0].get("logic_evidence")
    observed_quote = observed_evidence.get("quote") if isinstance(observed_evidence, dict) else None
    quote_match = observed_quote == expected.get("decisive_source_quote")
    structure = assessment.get("output_assessment", {}).get("structure_contract", {})
    evidence_check = assessment.get("output_assessment", {}).get("evidence_location_check", {})
    structure_valid = structure.get("valid") is True
    evidence_valid = (
        isinstance(evidence_check.get("checked"), int)
        and evidence_check.get("checked") > 0
        and evidence_check.get("valid") == evidence_check.get("checked")
        and not evidence_check.get("blockers")
    )
    matched = observed_gate == expected_gate
    qualitative_match = matched and quote_match and structure_valid and evidence_valid
    run_resolved = run_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    assessment_resolved = assessment_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    reference_resolved = reference_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()

    return {
        "artifact_type": "fta_event_scope_semantic_smoke_offline_comparison",
        "artifact_version": "v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case_id": case_id,
        "status": "matched_authored_policy_expectation_not_expert_validation" if qualitative_match else "requires_review",
        "comparison": {
            "expected_gate": expected_gate,
            "observed_gate": observed_gate,
            "gate_matches_policy_expectation": matched,
            "logic_evidence_exactly_matches_decisive_quote": quote_match,
            "structure_contract_valid": structure_valid,
            "evidence_locations_checked": evidence_check.get("checked", 0),
            "evidence_locations_valid": evidence_check.get("valid", 0),
            "qualitative_smoke_match": qualitative_match,
        },
        "provenance": {
            "run_path": run_resolved,
            "run_sha256": _sha256(run_path),
            "assessment_path": assessment_resolved,
            "assessment_sha256": _sha256(assessment_path),
            "reference_path": reference_resolved,
            "reference_sha256": _sha256(reference_path),
            "reference_status": reference["reference_status"],
        },
        "claim_boundaries": {
            "synthetic_behavioral_smoke_only": True,
            "source_corpus_evaluation": False,
            "human_expert_gold": False,
            "semantic_correctness_expert_assessed": False,
            "accuracy_or_calibration_claim_allowed": False,
            "aggregate_metric_claim_allowed": False,
            "gold_or_database_written": False,
            "production_or_readiness_changed": False,
            "fta_ready": False,
            "production_ready": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="compare a previously saved SMOKE-NNN response; makes no provider request")
    args = parser.parse_args()
    try:
        _run, _assessment, output_path = _run_paths(args.case_id)
        if output_path.exists():
            raise ComparisonError("comparison artifact already exists; refusing to overwrite")
        result = compare_saved_run(args.case_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, json.JSONDecodeError, ComparisonError, ValueError) as exc:
        parser.exit(2, f"offline comparison failed: {exc}\n")
    print(json.dumps({
        "case_id": result["case_id"],
        "status": result["status"],
        **result["comparison"],
        "report_path": output_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "accuracy_or_calibration_claim_allowed": result["claim_boundaries"]["accuracy_or_calibration_claim_allowed"],
        "live_request_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "matched_authored_policy_expectation_not_expert_validation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
