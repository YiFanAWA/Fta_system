"""Run a descriptive, source-aware probe on explicit public FTA diagrams."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_gate_multisource_diagram_external_test_v1.json"
RUNS = ROOT / "evaluation" / "quality_eval" / "runs"
DEFAULT_OUTPUT = RUNS / "fta_gate_multisource_external_probe_v1_2026-09-27.json"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.model_client import ModelClientError  # noqa: E402
from fta_gate_external_probe_core import build_prompt, parse_probabilities, summarize, top_gate  # noqa: E402


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_fixture(path: Path = DATASET) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    fixture = json.loads(raw.decode("utf-8"))
    if not isinstance(fixture, dict) or fixture.get("artifact_type") != "external_diagram_gate_classification_fixture":
        raise ValueError("invalid external diagram fixture")
    if fixture.get("formal_gold") is not False or fixture.get("in_project_gold") is not False:
        raise ValueError("external fixture must not be promoted to project Gold")
    sources = fixture.get("sources")
    rows = fixture.get("gate_nodes")
    if not isinstance(sources, list) or not sources or not isinstance(rows, list) or not rows:
        raise ValueError("fixture must contain sources and gate_nodes")
    source_map: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source must be an object")
        source_id = source.get("source_id")
        digest = source.get("source_pdf_sha256")
        if not isinstance(source_id, str) or not source_id or source_id in source_map:
            raise ValueError("source_id must be unique and non-empty")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid PDF digest for {source_id}")
        source_map[source_id] = source
    if fixture.get("source_document_count") != len(sources):
        raise ValueError("source_document_count does not match sources")
    if fixture.get("source_cluster_count") != len({s.get("source_cluster_id") for s in sources}):
        raise ValueError("source_cluster_count does not match sources")
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("gate node must be an object")
        node_id = row.get("gate_node_id")
        if not isinstance(node_id, str) or not node_id or node_id in ids:
            raise ValueError("gate_node_id must be unique and non-empty")
        ids.add(node_id)
        if row.get("expected_gate") not in {"AND", "OR"}:
            raise ValueError(f"expected_gate must come from an explicit diagram for {node_id}")
        source = source_map.get(row.get("source_id"))
        if source is None:
            raise ValueError(f"unknown source_id for {node_id}")
        if row.get("source_cluster_id") != source.get("source_cluster_id"):
            raise ValueError(f"source cluster mismatch for {node_id}")
        if not isinstance(row.get("label_evidence"), dict) or not row["label_evidence"]:
            raise ValueError(f"missing label provenance for {node_id}")
        build_prompt(row)
    if len({row["source_cluster_id"] for row in rows}) != fixture["source_cluster_count"]:
        raise ValueError("every declared source cluster must contribute at least one node")
    if Counter(row["expected_gate"] for row in rows) != Counter({"AND": 2, "OR": 3}):
        raise ValueError("unexpected curated label distribution")
    return fixture, raw


def source_pdf_map(items: Sequence[str], sources: Sequence[Mapping[str, Any]]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for item in items:
        source_id, sep, raw_path = item.partition("=")
        if not sep or not source_id or not raw_path:
            raise ValueError("--source-pdf must be SOURCE_ID=PATH")
        if source_id in parsed:
            raise ValueError(f"duplicate --source-pdf for {source_id}")
        parsed[source_id] = Path(raw_path)
    expected_ids = {str(source["source_id"]) for source in sources}
    if set(parsed) != expected_ids:
        raise ValueError("provide exactly one --source-pdf for each fixture source")
    return parsed


def verify_source_pdfs(fixture: Mapping[str, Any], paths: Mapping[str, Path]) -> dict[str, str]:
    verified: dict[str, str] = {}
    for source in fixture["sources"]:
        source_id = str(source["source_id"])
        digest = sha256(paths[source_id].read_bytes())
        if digest != source["source_pdf_sha256"]:
            raise ValueError(f"source PDF digest mismatch for {source_id}")
        verified[source_id] = digest
    return verified


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
                "source_id": row["source_id"],
                "source_cluster_id": row["source_cluster_id"],
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
    by_source = {
        source["source_id"]: summarize([row for row in predictions if row["source_id"] == source["source_id"]])
        for source in fixture["sources"]
    }
    return {
        "artifact_type": "external_multisource_diagram_gate_classification_probe",
        "artifact_version": "v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if not failures and len(predictions) == len(fixture["gate_nodes"]) else "partial",
        "formal_gold": False,
        "in_project_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": fixture["scope_note"],
        "confidence_semantics": "raw uncalibrated model self-assessment, not event probability",
        "metadata": {
            "model_id": model_id,
            "provider_host": provider_host,
            "temperature": 0,
            "requests_planned": len(fixture["gate_nodes"]),
            "requests_succeeded": len(predictions),
            "requests_failed": len(failures),
            "source_document_count": fixture["source_document_count"],
            "source_cluster_count": fixture["source_cluster_count"],
            "fixture_sha256": None,
            "verified_source_pdf_sha256": {},
        },
        "summary": summarize(predictions) if predictions else None,
        "per_source_summary": by_source,
        "predictions": predictions,
        "failures": failures,
        "limitations": [
            "Only five gate nodes from three document clusters; this is a descriptive smoke test, not calibration or a representative accuracy estimate.",
            "All labels are AND/OR transcribed from explicit source diagrams; there are no unknown/insufficient-evidence examples in this fixture.",
            "A diagram's true gate is not proof that the original fault prose alone supports that gate. This is not an evidence-backed text-to-FTA test.",
            "The HERMES paper cites the NASA handbook and includes two gates from one tree; rows are clustered, not independent observations.",
            "This probe does not evaluate event completeness, evidence binding, source-text extraction, candidate-tree generation, or production policy.",
            "Raw model self-reported probabilities and the descriptive Brier score do not establish calibration or justify a runtime threshold.",
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
    parser.add_argument("--source-pdf", action="append", default=[], metavar="SOURCE_ID=PATH")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = safe_output_path(args.output)
    fixture, fixture_bytes = load_fixture(args.dataset)
    paths = source_pdf_map(args.source_pdf, fixture["sources"])
    verified_hashes = verify_source_pdfs(fixture, paths)

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
    artifact["metadata"]["verified_source_pdf_sha256"] = verified_hashes
    artifact["metadata"]["source_pdf_paths"] = {key: str(value.resolve()) for key, value in paths.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(artifact, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "status": artifact["status"], "model_id": OPENAI_MODEL, "provider_host": host, "summary": artifact["summary"], "failure_count": len(artifact["failures"])}, ensure_ascii=False))
    return 0 if artifact["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
