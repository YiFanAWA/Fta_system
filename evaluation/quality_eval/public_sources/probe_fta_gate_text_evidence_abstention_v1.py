"""Exploratory text-evidence probe for AND/OR decisions and unknown abstention."""

from __future__ import annotations

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
DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_gate_text_evidence_abstention_external_test_v1.json"
RUNS = ROOT / "evaluation" / "quality_eval" / "runs"
DEFAULT_OUTPUT = RUNS / "fta_gate_text_evidence_abstention_probe_v1_2026-09-27.json"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model_client import ModelClientError  # noqa: E402
from fta_gate_external_probe_core import parse_probabilities, top_gate  # noqa: E402


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build_prompt(row: Mapping[str, Any]) -> str:
    parent = row.get("parent_event")
    children = row.get("children")
    if not isinstance(parent, str) or not parent.strip():
        raise ValueError("parent_event is required")
    if not isinstance(children, list) or len(children) < 2 or not all(isinstance(x, str) and x.strip() for x in children):
        raise ValueError("at least two direct child events are required")
    evidence: dict[str, Any] = {"parent_scope_text": row.get("parent_evidence", "")}
    if row.get("candidate_set_heading"):
        evidence["candidate_set_heading"] = row["candidate_set_heading"]
    if row.get("candidate_set_evidence"):
        evidence["candidate_set_text"] = row["candidate_set_evidence"]
    visible = {
        "parent_event": parent,
        "direct_child_events": children,
        "source_scope_evidence": evidence,
    }
    return (
        "你在做保守的文本证据判门任务，不是根据领域常识猜最可能的故障树。"
        "只有当给定原文在这些同级子事件之间直接表达逻辑关系时，才判 AND 或 OR。"
        "表格/清单列出多个 possible causes 本身不等于 OR；列举句末尾的 and 也不等于 AND。"
        "父事件描述中出现的 or 不能证明子原因之间是 OR。若原文没有清楚说明任一子原因可单独导致父事件，"
        "或多个子事件必须共同发生，必须判 unknown。"
        "若判 AND/OR，gate_evidence_quote 必须是 source_scope_evidence 中直接表达子事件组合逻辑的最短逐字引文；"
        "若判 unknown，gate_evidence_quote 必须为 null。不要补造证据或增加、删除、合并事件。"
        "只返回 JSON：gate_probabilities 必须含 AND、OR、unknown 三项并合计为 1；另含 gate_evidence_quote 和简短 reason。"
        "这里的概率是模型自评，不是事件发生概率或校准概率。\n"
        + json.dumps(visible, ensure_ascii=False, indent=2)
    )


def parse_model_output(response: str) -> tuple[dict[str, float], str | None, str]:
    probabilities, reason = parse_probabilities(response)
    start, end = response.find("{"), response.rfind("}")
    payload = json.loads(response[start : end + 1])
    quote = payload.get("gate_evidence_quote")
    if quote is not None and (not isinstance(quote, str) or not quote.strip()):
        raise ValueError("gate_evidence_quote must be null or non-empty text")
    return probabilities, quote, reason


def load_fixture(path: Path = DATASET) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    fixture = json.loads(raw.decode("utf-8"))
    if fixture.get("artifact_type") != "external_text_evidence_gate_abstention_fixture":
        raise ValueError("invalid text-evidence fixture")
    if fixture.get("formal_gold") is not False or fixture.get("in_project_gold") is not False:
        raise ValueError("external fixture must not be promoted to project Gold")
    sources = fixture.get("sources")
    rows = fixture.get("gate_nodes")
    if not isinstance(sources, list) or not isinstance(rows, list) or not rows:
        raise ValueError("fixture must contain source metadata and gate nodes")
    source_map: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        source_id = source.get("source_id")
        digest = source.get("source_pdf_sha256") or source.get("source_text_sha256")
        if not isinstance(source_id, str) or source_id in source_map:
            raise ValueError("source IDs must be unique strings")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in digest)
        ):
            raise ValueError(f"missing valid source PDF/text SHA-256 for {source_id}")
        source_map[source_id] = source
    seen: set[str] = set()
    for row in rows:
        node_id = row.get("gate_node_id")
        if not isinstance(node_id, str) or not node_id or node_id in seen:
            raise ValueError("gate node IDs must be unique and non-empty")
        seen.add(node_id)
        if row.get("source_id") not in source_map:
            raise ValueError(f"unknown source for {node_id}")
        source = source_map[row["source_id"]]
        if row.get("source_cluster_id") != source.get("source_cluster_id"):
            raise ValueError(f"source cluster mismatch for {node_id}")
        if row.get("expected_gate") not in {"AND", "OR", "unknown"}:
            raise ValueError(f"invalid label for {node_id}")
        if row["expected_gate"] == "unknown" and row.get("expected_gate_evidence") is not None:
            raise ValueError(f"unknown node cannot carry decisive gate evidence: {node_id}")
        if row["expected_gate"] in {"AND", "OR"}:
            quote = row.get("expected_gate_evidence")
            if not isinstance(quote, str) or quote not in row.get("candidate_set_evidence", ""):
                raise ValueError(f"decisive gate evidence must be present in the child-set excerpt: {node_id}")
        build_prompt(row)
    if fixture.get("source_document_count") != len(sources):
        raise ValueError("source_document_count mismatch")
    if fixture.get("source_cluster_count") != len({s.get("source_cluster_id") for s in sources}):
        raise ValueError("source_cluster_count mismatch")
    return fixture, raw


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unknown_gold = [row for row in rows if row["expected_gate"] == "unknown"]
    decisive = [row for row in rows if row["predicted_gate"] in {"AND", "OR"}]
    correct = sum(row["expected_gate"] == row["predicted_gate"] for row in rows)
    known = [row for row in rows if row["expected_gate"] in {"AND", "OR"}]
    return {
        "sample_count": len(rows),
        "top1_accuracy": correct / len(rows) if rows else None,
        "unknown_gold_count": len(unknown_gold),
        "unknown_correct_count": sum(row["predicted_gate"] == "unknown" for row in unknown_gold),
        "unknown_recall": sum(row["predicted_gate"] == "unknown" for row in unknown_gold) / len(unknown_gold) if unknown_gold else None,
        "unknown_unsafe_accept_count": sum(row["predicted_gate"] in {"AND", "OR"} for row in unknown_gold),
        "known_gate_count": len(known),
        "known_gate_correct_count": sum(row["predicted_gate"] == row["expected_gate"] for row in known),
        "decisive_coverage": len(decisive) / len(rows) if rows else None,
        "decisive_quote_substring_match_count": sum(row.get("quote_is_exact_substring_of_child_evidence") is True for row in decisive),
        "decisive_quote_count": sum(bool(row.get("gate_evidence_quote")) for row in decisive),
        "label_counts": dict(Counter(row["expected_gate"] for row in rows)),
        "prediction_counts": dict(Counter(row["predicted_gate"] for row in rows)),
    }


def run_probe(fixture: Mapping[str, Any], model_client: Any, *, model_id: str, provider_host: str | None) -> dict[str, Any]:
    predictions: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for row in fixture["gate_nodes"]:
        prompt = build_prompt(row)
        try:
            probabilities, quote, reason = parse_model_output(model_client.complete(prompt))
            predicted, confidence, margin = top_gate(probabilities)
            evidence_source_text = row.get("candidate_set_evidence", "")
            predictions.append({
                "gate_node_id": row["gate_node_id"],
                "expected_gate": row["expected_gate"],
                "predicted_gate": predicted,
                "gate_probabilities": probabilities,
                "top_probability": confidence,
                "top_margin": margin,
                "gate_evidence_quote": quote,
                "quote_is_exact_substring_of_child_evidence": quote in evidence_source_text if quote is not None else None,
                "correct": predicted == row["expected_gate"],
                "prompt_sha256": sha256(prompt.encode("utf-8")),
                "reason": reason,
            })
        except ModelClientError as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "model_provider", "error_code": exc.code})
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "response_validation", "error_code": type(exc).__name__})
    return {
        "artifact_type": "external_text_evidence_gate_abstention_probe",
        "artifact_version": "v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if len(predictions) == len(fixture["gate_nodes"]) and not failures else "partial",
        "formal_gold": False,
        "in_project_gold": False,
        "database_written": False,
        "gate_policy_applied": False,
        "threshold_selected": False,
        "probability_calibrated": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": fixture["scope_note"],
        "reviewer_provenance": fixture["label_provenance"]["reviewer_role"],
        "reviewer_is_human_expert": False,
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
        },
        "summary": summarize(predictions) if predictions else None,
        "predictions": predictions,
        "failures": failures,
        "limitations": fixture["limitations"],
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
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = safe_output_path(args.output)
    fixture, fixture_bytes = load_fixture(args.dataset)

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
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(artifact, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "status": artifact["status"], "model_id": OPENAI_MODEL, "provider_host": host, "summary": artifact["summary"], "failure_count": len(artifact["failures"])}, ensure_ascii=False))
    return 0 if artifact["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
