"""Exploratory gate classification probe against explicit FAA FTA diagrams.

This is a separate diagram-derived evaluation path, not a production parser,
text-evidence verifier, calibration run, or project Gold dataset.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "faa_ast_gate_diagram_external_test_v1.json"
RUNS = ROOT / "evaluation" / "quality_eval" / "runs"
SOURCE_PDF = Path.home() / "Downloads" / "FAA_AST_Guide_to_Reliability_Analysis_v1.pdf"
DEFAULT_OUTPUT = RUNS / "faa_ast_fta_gate_external_probe_v1_2026-09-27.json"
EXPECTED_SOURCE_SHA256 = "66a4a55f6d030f73b9a4bcff0746a38338225d548d7c5c1f37e3b39226a68c94"

sys.path.insert(0, str(BACKEND))
from core.model_client import ModelClientError  # noqa: E402
from fta_gate_external_probe_core import (  # noqa: E402
    build_prompt,
    parse_probabilities,
    summarize,
    top_gate,
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_fixture(path: Path = DATASET) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    fixture = json.loads(raw.decode("utf-8"))
    if not isinstance(fixture, dict) or fixture.get("artifact_type") != "external_diagram_gate_classification_fixture":
        raise ValueError("invalid FAA diagram fixture")
    if fixture.get("formal_gold") is not False or fixture.get("in_project_gold") is not False:
        raise ValueError("external fixture must not be promoted to project Gold")
    rows = fixture.get("gate_nodes")
    if not isinstance(rows, list) or len(rows) != 13:
        raise ValueError("expected exactly 13 explicitly diagram-labeled nodes")
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("gate node must be an object")
        node_id = row.get("gate_node_id")
        if not isinstance(node_id, str) or not node_id or node_id in ids:
            raise ValueError("gate_node_id must be unique and non-empty")
        ids.add(node_id)
        if row.get("expected_gate") not in {"AND", "OR"}:
            raise ValueError(f"invalid explicit diagram label for {node_id}")
        if not isinstance(row.get("parent_event"), str) or not row["parent_event"].strip():
            raise ValueError(f"missing parent event for {node_id}")
        children = row.get("children")
        if not isinstance(children, list) or len(children) < 2 or not all(isinstance(x, str) and x.strip() for x in children):
            raise ValueError(f"invalid direct child set for {node_id}")
    counts = Counter(row["expected_gate"] for row in rows)
    if counts != Counter({"AND": 3, "OR": 10}):
        raise ValueError(f"unexpected label distribution: {dict(counts)}")
    return fixture, raw


def run_probe(fixture: Mapping[str, Any], model_client: Any, *, model_id: str, provider_host: str | None) -> dict[str, Any]:
    predictions: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for row in fixture["gate_nodes"]:
        prompt = build_prompt(row)
        try:
            probabilities, reason = parse_probabilities(model_client.complete(prompt))
            pred, confidence, margin = top_gate(probabilities)
            predictions.append({
                "gate_node_id": row["gate_node_id"],
                "figure_id": row["figure_id"],
                "pdf_page": row["pdf_page"],
                "expected_gate": row["expected_gate"],
                "predicted_gate": pred,
                "gate_probabilities": probabilities,
                "top_probability": confidence,
                "top_margin": margin,
                "correct": pred == row["expected_gate"],
                "prompt_sha256": sha256(prompt.encode("utf-8")),
                "reason_summary": reason,
            })
        except ModelClientError as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "model_provider", "error_code": exc.code})
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "response_validation", "error_code": type(exc).__name__})
    summary = summarize(predictions) if predictions else None
    return {
        "artifact_type": "external_diagram_gate_classification_probe",
        "artifact_version": "v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if not failures and len(predictions) == len(fixture["gate_nodes"]) else "partial",
        "formal_gold": False,
        "in_project_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": "gate classification from parent/child event wording only; no diagram gate labels or visual evidence are sent to the model",
        "confidence_semantics": "raw uncalibrated model self-assessment, not event probability",
        "metadata": {
            "model_id": model_id,
            "provider_host": provider_host,
            "temperature": 0,
            "requests_planned": len(fixture["gate_nodes"]),
            "requests_succeeded": len(predictions),
            "requests_failed": len(failures),
            "source_cluster_count": fixture["source_cluster_count"],
            "source_pdf_sha256": fixture["source_pdf_sha256"],
            "fixture_sha256": None,
        },
        "summary": summary,
        "predictions": predictions,
        "failures": failures,
        "limitations": [
            "13 nodes from one illustrative FAA guide are an external structural probe, not independent-source calibration.",
            "This test does not evaluate text evidence binding, cause extraction, candidate-tree construction, or production integration.",
            "Unknown abstention is counted as not-correct for exact gate-label accuracy; selective metrics are reported separately.",
            "Brier score is descriptive only and cannot establish calibration on this small single-source sample.",
        ],
    }


def safe_output_path(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(RUNS.resolve())
    except ValueError as exc:
        raise ValueError("output must remain under evaluation/quality_eval/runs") from exc
    if resolved.exists():
        raise FileExistsError(f"refusing to overwrite existing run artifact: {resolved}")
    return resolved


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--source-pdf", type=Path, default=SOURCE_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = safe_output_path(args.output)
    fixture, fixture_bytes = load_fixture(args.dataset)
    pdf_bytes = args.source_pdf.read_bytes()
    pdf_sha = sha256(pdf_bytes)
    if pdf_sha != EXPECTED_SOURCE_SHA256 or pdf_sha != fixture.get("source_pdf_sha256"):
        raise ValueError("source PDF digest does not match the reviewed FAA fixture")

    from core.config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS
    from core.openai_model_client import OpenAICompatibleModelClient

    if not OPENAI_API_KEY:
        raise RuntimeError("configured model-provider credentials are unavailable")
    client = OpenAICompatibleModelClient(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        timeout_seconds=OPENAI_TIMEOUT_SECONDS,
        base_url=OPENAI_API_BASE or None,
    )
    host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None
    artifact = run_probe(fixture, client, model_id=OPENAI_MODEL, provider_host=host)
    artifact["metadata"]["fixture_sha256"] = sha256(fixture_bytes)
    artifact["metadata"]["source_pdf_path"] = str(args.source_pdf.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(artifact, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "status": artifact["status"], "model_id": OPENAI_MODEL, "provider_host": host, "summary": artifact["summary"], "failure_count": len(artifact["failures"])}, ensure_ascii=False))
    return 0 if artifact["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
