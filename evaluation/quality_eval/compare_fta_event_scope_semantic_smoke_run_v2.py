#!/usr/bin/env python3
"""Compare saved semantic-smoke runs using gate-specific evidence contracts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evaluation.quality_eval.compare_fta_event_scope_semantic_smoke_run_v1 import (  # noqa: E402
    CASE_ID_PATTERN,
    ComparisonError,
    REFERENCE_PATH,
    RUNS_DIR,
    _run_paths,
    _sha256,
)


ALLOWED_UNKNOWN_REASONS = {
    "no_direct_logic_evidence",
    "incomplete_child_set",
    "scope_ambiguity",
    "input_context_unavailable",
}


def _gate_logic_check(expected_gate: str, gate_object: dict[str, Any]) -> dict[str, Any]:
    observed_gate = gate_object.get("gate")
    if expected_gate in {"AND", "OR"}:
        evidence = gate_object.get("logic_evidence")
        quote = evidence.get("quote") if isinstance(evidence, dict) else None
        return {
            "known_gate_logic_evidence_matches_decisive_quote": isinstance(quote, str) and bool(quote),
            "unknown_gate_contract_valid": None,
            "unknown_reason": gate_object.get("unknown_reason"),
            "expected_quote_to_bind": True,
        }
    if expected_gate == "unknown":
        evidence_absent = gate_object.get("logic_evidence") is None
        reason = gate_object.get("unknown_reason")
        return {
            "known_gate_logic_evidence_matches_decisive_quote": None,
            "unknown_gate_contract_valid": (
                observed_gate == "unknown"
                and evidence_absent
                and isinstance(reason, str)
                and reason in ALLOWED_UNKNOWN_REASONS
            ),
            "unknown_reason": reason,
            "expected_quote_to_bind": False,
        }
    raise ComparisonError(f"unsupported authored expected gate: {expected_gate}")


def compare_saved_run_v2(
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
    gate = gates[0]
    expected_gate = expected.get("expected_candidate_gate")
    observed_gate = gate.get("gate")
    gate_match = observed_gate == expected_gate
    source_texts = [
        segment.get("text", "")
        for segment in run.get("case", {}).get("model_input", {}).get("source_segments", [])
        if isinstance(segment, dict)
    ]
    decisive_quote = expected.get("decisive_source_quote")
    source_quote_present = isinstance(decisive_quote, str) and any(decisive_quote in text for text in source_texts)
    gate_evidence = _gate_logic_check(expected_gate, gate)
    if expected_gate in {"AND", "OR"}:
        evidence = gate.get("logic_evidence")
        observed_quote = evidence.get("quote") if isinstance(evidence, dict) else None
        exact_quote_match = observed_quote == decisive_quote
        gate_evidence["known_gate_logic_evidence_matches_decisive_quote"] = exact_quote_match
        gate_evidence_valid = exact_quote_match
    else:
        gate_evidence_valid = gate_evidence["unknown_gate_contract_valid"] is True

    output_assessment = assessment.get("output_assessment", {})
    structure_valid = output_assessment.get("structure_contract", {}).get("valid") is True
    evidence_check = output_assessment.get("evidence_location_check", {})
    evidence_valid = (
        isinstance(evidence_check.get("checked"), int)
        and evidence_check.get("checked") > 0
        and evidence_check.get("valid") == evidence_check.get("checked")
        and not evidence_check.get("blockers")
    )
    qualitative_match = gate_match and gate_evidence_valid and source_quote_present and structure_valid and evidence_valid
    run_resolved = run_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    assessment_resolved = assessment_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    reference_resolved = reference_path.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()

    return {
        "artifact_type": "fta_event_scope_semantic_smoke_offline_comparison",
        "artifact_version": "v2",
        "comparator_policy": "gate_specific_evidence_contract_v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case_id": case_id,
        "status": "matched_authored_policy_expectation_not_expert_validation" if qualitative_match else "requires_review",
        "comparison": {
            "expected_gate": expected_gate,
            "observed_gate": observed_gate,
            "gate_matches_policy_expectation": gate_match,
            **gate_evidence,
            "decisive_source_quote_present_in_input": source_quote_present,
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
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="compare a saved SMOKE-NNN response; makes no provider request")
    args = parser.parse_args()
    if not CASE_ID_PATTERN.fullmatch(args.case_id):
        parser.error("case_id must use the fixed SMOKE-NNN format")
    run_path, assessment_path, _ = _run_paths(args.case_id)
    output_path = RUNS_DIR / f"fta_event_scope_semantic_smoke_{args.case_id.lower()}_v1_2026-09-29_offline_comparison_v2.json"
    if output_path.exists():
        parser.error("v2 comparison artifact already exists; refusing to overwrite")
    try:
        result = compare_saved_run_v2(args.case_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, json.JSONDecodeError, ComparisonError, ValueError) as exc:
        parser.exit(2, f"offline comparison v2 failed: {exc}\n")
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
