"""Run a development-only text probe on source-pinned FTA diagram gate labels."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
QUALITY_EVAL = ROOT / "evaluation" / "quality_eval"
DATASET = QUALITY_EVAL / "datasets" / "fta_gate_diagram_development_v1.json"
MANIFEST = QUALITY_EVAL / "fta_baseline_manifest_v15.json"
RUNS = QUALITY_EVAL / "runs"
DEFAULT_OUTPUT = RUNS / "fta_gate_diagram_development_probe_v1_2026-09-28.json"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model_client import ModelClientError  # noqa: E402
from fta_gate_external_probe_core import (  # noqa: E402
    build_prompt,
    parse_probabilities,
    summarize,
    top_gate,
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value, raw


def load_fixture(path: Path = DATASET, manifest_path: Path = MANIFEST) -> tuple[dict[str, Any], bytes, dict[str, str]]:
    fixture, fixture_bytes = _read_json(path)
    manifest, _ = _read_json(manifest_path)
    if fixture.get("artifact_type") != "external_diagram_gate_classification_fixture":
        raise ValueError("invalid development fixture artifact_type")
    if fixture.get("dataset_role") != "development_only":
        raise ValueError("gate probe only accepts the frozen development partition")
    if fixture.get("formal_gold") is not False or fixture.get("in_project_gold") is not False:
        raise ValueError("development fixture must not be promoted to Gold")
    if fixture.get("fta_ready") is not False or fixture.get("production_ready") is not False:
        raise ValueError("development fixture cannot assert FTA or production readiness")

    policy = fixture.get("partition_policy")
    if not isinstance(policy, dict) or policy.get("split_unit") != "source_document_cluster":
        raise ValueError("development allocation must keep whole source-document clusters together")
    if policy.get("allocated_partition") != "development" or policy.get("source_cluster_splitting_allowed") is not False:
        raise ValueError("fixture has an invalid source-cluster allocation policy")
    if policy.get("independent_final_validation_status") != "not_created":
        raise ValueError("this experiment expects the independent Final set to remain sealed/uncreated")

    sources = fixture.get("sources")
    rows = fixture.get("gate_nodes")
    if not isinstance(sources, list) or not sources or not isinstance(rows, list) or not rows:
        raise ValueError("fixture requires non-empty sources and gate_nodes")
    if fixture.get("source_document_count") != len(sources):
        raise ValueError("source_document_count mismatch")
    source_map: dict[str, Mapping[str, Any]] = {}
    verified_hashes: dict[str, str] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source entries must be objects")
        source_id = source.get("source_id")
        cluster_id = source.get("source_cluster_id")
        relative_path = source.get("source_pdf_path")
        declared_hash = source.get("source_pdf_sha256")
        if not all(isinstance(value, str) and value.strip() for value in (source_id, cluster_id, relative_path)):
            raise ValueError("each source needs an id, cluster id, and repo-relative PDF path")
        if source_id in source_map:
            raise ValueError(f"duplicate source id: {source_id}")
        pdf_path = (ROOT / relative_path).resolve(strict=True)
        if not pdf_path.is_relative_to(ROOT.resolve()):
            raise ValueError(f"PDF path escapes repository: {relative_path}")
        actual_hash = sha256(pdf_path.read_bytes())
        if actual_hash != declared_hash:
            raise ValueError(f"source PDF fingerprint mismatch: {source_id}")
        source_map[source_id] = source
        verified_hashes[source_id] = actual_hash

    clusters = {source["source_cluster_id"] for source in sources}
    if fixture.get("source_cluster_count") != len(clusters) or len(clusters) != len(sources):
        raise ValueError("each complete source document must be represented by one distinct cluster")
    if len(rows) != 11 or len({row.get("gate_node_id") for row in rows}) != len(rows):
        raise ValueError("the frozen development fixture must contain 11 unique gate nodes")
    label_counts = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("gate node entries must be objects")
        source = source_map.get(row.get("source_id"))
        if source is None or row.get("source_cluster_id") != source.get("source_cluster_id"):
            raise ValueError(f"source/cluster mismatch for {row.get('gate_node_id')}")
        if row.get("expected_gate") not in {"AND", "OR"}:
            raise ValueError("diagram development fixture only permits explicit AND/OR labels")
        if not isinstance(row.get("label_evidence"), dict) or not row["label_evidence"].get("quote"):
            raise ValueError(f"missing label evidence for {row.get('gate_node_id')}")
        prompt = build_prompt(row)
        prompt_payload = json.loads(prompt[prompt.rfind("{") : prompt.rfind("}") + 1])
        if set(prompt_payload) != {"parent_event", "direct_child_events"}:
            raise ValueError("inference input must contain only parent and direct child event text")
        label_counts[row["expected_gate"]] += 1
    if label_counts != Counter({"AND": 5, "OR": 6}):
        raise ValueError(f"unexpected frozen development label counts: {dict(label_counts)}")
    if {row["source_cluster_id"] for row in rows} != clusters:
        raise ValueError("every allocated development source cluster must contribute samples")

    suite = manifest.get("development_gate_suite")
    if not isinstance(suite, dict) or suite.get("dataset_path") != path.resolve().relative_to(ROOT).as_posix():
        raise ValueError("manifest v6 does not name this development fixture")
    manifest_clusters = {item["source_cluster_id"] for item in suite.get("source_clusters", [])}
    regression_suite = manifest.get("seen_case_regression_suite")
    if not isinstance(regression_suite, dict):
        raise ValueError("active manifest is missing the seen-case contract/boundary regression allocation")
    regression_clusters = {item["source_cluster_id"] for item in regression_suite.get("source_clusters", [])}
    if clusters != manifest_clusters or not clusters.isdisjoint(regression_clusters):
        raise ValueError("development cluster allocation disagrees with active manifest or overlaps regression")
    final = manifest.get("independent_final_validation", {})
    if final.get("status") != "not_created" or final.get("source_cluster_count") != 0:
        raise ValueError("this run must not consume or alter an independent Final set")
    return fixture, fixture_bytes, verified_hashes


def run_probe(
    fixture: Mapping[str, Any],
    model_client: Any,
    *,
    model_id: str,
    provider_host: str | None,
    progress: Callable[[int, int, str, bool], None] | None = None,
) -> dict[str, Any]:
    predictions: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    rows = fixture["gate_nodes"]
    for index, row in enumerate(rows, start=1):
        prompt = build_prompt(row)
        try:
            probabilities, reason = parse_probabilities(model_client.complete(prompt))
            prediction, confidence, margin = top_gate(probabilities)
            predictions.append({
                "gate_node_id": row["gate_node_id"],
                "source_id": row["source_id"],
                "source_cluster_id": row["source_cluster_id"],
                "expected_gate": row["expected_gate"],
                "predicted_gate": prediction,
                "gate_probabilities": probabilities,
                "top_probability": confidence,
                "top_margin": margin,
                "correct": prediction == row["expected_gate"],
                "prompt_sha256": sha256(prompt.encode("utf-8")),
                "reason_summary": reason,
            })
            success = True
        except ModelClientError as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "model_provider", "error_code": exc.code})
            success = False
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            failures.append({"gate_node_id": row["gate_node_id"], "stage": "response_validation", "error_code": type(exc).__name__})
            success = False
        if progress is not None:
            progress(index, len(rows), row["gate_node_id"], success)

    per_source: dict[str, Any] = {}
    for source in fixture["sources"]:
        source_rows = [row for row in predictions if row["source_id"] == source["source_id"]]
        per_source[source["source_id"]] = {
            "source_cluster_id": source["source_cluster_id"],
            "summary": summarize(source_rows) if source_rows else None,
        }
    return {
        "artifact_type": "fta_gate_diagram_development_probe",
        "artifact_version": "v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if not failures and len(predictions) == len(rows) else "partial",
        "dataset_role": "development_only",
        "formal_gold": False,
        "in_project_gold": False,
        "database_written": False,
        "fta_ready": False,
        "production_ready": False,
        "evaluation_scope": (
            "Text-only classification of AND/OR labels already present in public FTA diagrams. "
            "The model receives only parent_event and direct_child_events; source, diagram, gate symbol, "
            "label evidence, and expected label are withheld. This does not test evidence-backed gate "
            "authorization from fault source prose or production candidate-tree construction."
        ),
        "confidence_semantics": "raw uncalibrated model self-assessment, not event probability",
        "metadata": {
            "model_id": model_id,
            "provider_host": provider_host,
            "temperature": 0,
            "prompt_builder": "fta_gate_external_probe_core.build_prompt",
            "requests_planned": len(rows),
            "requests_succeeded": len(predictions),
            "requests_failed": len(failures),
            "sample_count": len(rows),
            "source_document_count": fixture["source_document_count"],
            "source_cluster_count": fixture["source_cluster_count"],
            "label_counts": {label: sum(row["expected_gate"] == label for row in rows) for label in ("AND", "OR")},
        },
        "summary": summarize(predictions) if predictions else None,
        "per_source_summary": per_source,
        "predictions": predictions,
        "failures": failures,
        "limitations": [
            "Only 11 curated nodes from three complete source documents; observations are clustered and not an independent representative accuracy estimate.",
            "This is a development probe; results may guide error analysis but must not be reported as held-out Final performance or expert Gold accuracy.",
            "All labels are transcribed from already-drawn public diagrams; no unknown/insufficient-evidence gate labels are present.",
            "The probe tests event-text gate classification only, not causal extraction, source-evidence sufficiency, event completeness, candidate-tree construction, or production policy.",
            "Raw model self-reported probabilities and descriptive Brier score do not establish calibration or justify a runtime threshold.",
        ],
    }


def safe_output_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(RUNS.resolve()):
        raise ValueError("output must remain under evaluation/quality_eval/runs")
    if resolved.exists():
        raise FileExistsError(f"refusing to overwrite existing run artifact: {resolved}")
    return resolved


def render_markdown(artifact: Mapping[str, Any], fixture: Mapping[str, Any]) -> str:
    summary = artifact.get("summary") or {}
    def metric(value: Any) -> str:
        return f"{value:.4f}" if isinstance(value, (int, float)) else "N/A"

    lines = [
        "# FTA 图示门型开发集探针 v1",
        "",
        "> 开发集结果，不是专家 Gold、独立 Final 成绩或生产 FTA 准确率。",
        "",
        f"- 状态：`{artifact['status']}`",
        f"- 模型：`{artifact['metadata']['model_id']}`（温度 0）",
        f"- 样本：{artifact['metadata']['sample_count']} 条；来源文档/簇：{artifact['metadata']['source_document_count']}/{artifact['metadata']['source_cluster_count']}",
        f"- 标签：AND={artifact['metadata']['label_counts']['AND']}，OR={artifact['metadata']['label_counts']['OR']}",
        f"- 请求：成功 {artifact['metadata']['requests_succeeded']}，失败 {artifact['metadata']['requests_failed']}",
        "- 独立 Final：仍未创建；同一本来源文档不拆分到多个集合。",
        "",
        "## 结果",
        "",
    ]
    if summary:
        lines.extend([
            f"- 成功预测子集准确率（n={summary.get('sample_count', 0)}）：{metric(summary.get('exact_accuracy'))}",
            f"- Always-OR 基线准确率：{metric(summary.get('always_OR_baseline_accuracy'))}",
            f"- AND/OR balanced accuracy：{metric(summary.get('balanced_accuracy_and_or'))}",
            f"- AND/OR macro-F1：{metric(summary.get('macro_f1_and_or'))}",
            f"- 确定输出覆盖率：{metric(summary.get('decisive_coverage'))}；确定输出准确率：{metric(summary.get('selective_accuracy'))}",
            f"- `unknown` 弃判数：{summary.get('unknown_count')}",
            "",
            "| 样本 | 来源簇 | Gold | 预测 | AND | OR | unknown | 正误 |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ])
        prediction_map = {row["gate_node_id"]: row for row in artifact["predictions"]}
        for node in fixture["gate_nodes"]:
            pred = prediction_map.get(node["gate_node_id"])
            if pred is None:
                lines.append(f"| {node['gate_node_id']} | {node['source_cluster_id']} | {node['expected_gate']} | — | — | — | — | 请求/解析失败 |")
            else:
                probs = pred["gate_probabilities"]
                mark = "是" if pred["correct"] else "否"
                lines.append(
                    f"| {pred['gate_node_id']} | {pred['source_cluster_id']} | {pred['expected_gate']} | {pred['predicted_gate']} | "
                    f"{probs['AND']:.3f} | {probs['OR']:.3f} | {probs['unknown']:.3f} | {mark} |"
                )
    else:
        lines.append("没有成功响应可计算指标。")
    lines.extend(["", "## 错误与弃判分析", ""])
    prediction_map = {row["gate_node_id"]: row for row in artifact["predictions"]}
    incorrect = [row for row in artifact["predictions"] if not row["correct"]]
    node_map = {row["gate_node_id"]: row for row in fixture["gate_nodes"]}
    if not incorrect:
        lines.append("完整样本中没有与图示门标签不一致的输出；这仍只是开发集观察。")
    for prediction in incorrect:
        node = node_map[prediction["gate_node_id"]]
        if prediction["predicted_gate"] == "unknown":
            explanation = (
                "模型只看到了父/子事件文字，没有收到来源中的逻辑说明；因此这是对图示门标签的弃判。"
                "当前数据没有单独标注‘仅凭输入文字是否足以判门’，不能将它直接解释成不安全错误或正确命中。"
            )
        else:
            explanation = (
                "模型给出了确定门型，但父/子事件列表本身没有说明这些事件必须同时发生或任一单独发生。"
                "这属于需按证据门禁复核的确定性误判风险，不应据此自动接受门型。"
            )
        lines.append(
            f"- `{prediction['gate_node_id']}`：图示标签 `{prediction['expected_gate']}`，模型 `{prediction['predicted_gate']}`；"
            f"父事件“{node['parent_event']}”。{explanation}"
        )
    correct_count = sum(bool(row["correct"]) for row in artifact["predictions"])
    and_to_or = sum(
        row["expected_gate"] == "AND" and row["predicted_gate"] == "OR"
        for row in artifact["predictions"]
    )
    unknown_count = sum(row["predicted_gate"] == "unknown" for row in artifact["predictions"])
    lines.extend([
        "",
        f"解读：成功预测中 {correct_count} 条与图示标签一致；{and_to_or} 条 AND 被确定地判成 OR，"
        f"{unknown_count} 条被判为 unknown。来源材料中的部分图示节点有额外逻辑说明，但这些说明按实验设计没有发给模型。"
        "因此本实验暴露的是‘事件名称文字是否足以恢复图示逻辑’的限制，不是对生产候选 FTA 完整链路的验收。",
        "",
        "## 来源簇结果",
        "",
    ])
    for source_id, value in artifact["per_source_summary"].items():
        source_summary = value["summary"]
        if source_summary is None:
            lines.append(f"- `{source_id}`：无成功预测")
        else:
            lines.append(
                f"- `{source_id}`：{source_summary['sample_count']} 条，准确率 {source_summary['exact_accuracy']:.4f}"
            )
    lines.extend(["", "## 限制与解释", ""])
    limitations_zh = [
        "仅 3 份完整来源文档中的 11 个精选节点；同文档样本相关，不是独立、代表性的准确率估计。",
        "这是开发集，只能用于错误分析；不能报告为独立 Final 成绩或专家 Gold 准确率。",
        "标签来自已绘制的公开图示，没有 unknown/证据不足标签。",
        "本探针只测事件文字门型分类，不测因果抽取、源文证据充分性、事件完整性、候选树生成或生产策略。",
        "模型自报分数及描述性 Brier 值未经校准，不能作为运行时门型阈值或真实事件概率。",
    ]
    lines.extend(f"- {item}" for item in limitations_zh)
    if artifact["failures"]:
        lines.extend(["", "## 失败请求", ""])
        lines.extend(f"- `{item['gate_node_id']}`：{item['stage']} / `{item['error_code']}`" for item in artifact["failures"])
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--render-existing-run", type=Path, help="regenerate only the Markdown report from an existing JSON run; makes no model calls")
    args = parser.parse_args(argv)
    if args.render_existing_run is not None:
        existing_json = args.render_existing_run.resolve(strict=True)
        if not existing_json.is_relative_to(RUNS.resolve()) or existing_json.suffix.lower() != ".json":
            raise ValueError("existing run JSON must be inside evaluation/quality_eval/runs")
        fixture, fixture_bytes, _ = load_fixture(args.dataset, args.manifest)
        artifact, _ = _read_json(existing_json)
        metadata = artifact.get("metadata", {})
        if metadata.get("fixture_sha256") != sha256(fixture_bytes):
            raise ValueError("existing run does not belong to the selected development fixture")
        if metadata.get("manifest_sha256") != sha256(args.manifest.read_bytes()):
            raise ValueError("existing run does not reference the selected baseline manifest")
        report_path = existing_json.with_suffix(".md")
        with report_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(render_markdown(artifact, fixture))
        print(json.dumps({"report": str(report_path), "model_calls": 0, "status": "rendered"}, ensure_ascii=False))
        return 0

    output = safe_output_path(args.output)
    report_path = output.with_suffix(".md")
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {report_path}")
    fixture, fixture_bytes, verified_hashes = load_fixture(args.dataset, args.manifest)

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
    provider_host = urlparse(OPENAI_API_BASE).hostname if OPENAI_API_BASE else None

    def report_progress(index: int, total: int, node_id: str, succeeded: bool) -> None:
        print(f"[{index}/{total}] {node_id}: {'ok' if succeeded else 'failed'}", flush=True)

    artifact = run_probe(
        fixture,
        client,
        model_id=OPENAI_MODEL,
        provider_host=provider_host,
        progress=report_progress,
    )
    artifact["metadata"]["fixture_sha256"] = sha256(fixture_bytes)
    artifact["metadata"]["verified_source_pdf_sha256"] = verified_hashes
    artifact["metadata"]["manifest_path"] = args.manifest.resolve().relative_to(ROOT).as_posix()
    artifact["metadata"]["manifest_sha256"] = sha256(args.manifest.read_bytes())
    artifact["metadata"]["prompt_input_fields"] = ["parent_event", "direct_child_events"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(artifact, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(artifact, fixture))
    print(json.dumps({
        "output_json": str(output),
        "output_markdown": str(report_path),
        "status": artifact["status"],
        "model_id": OPENAI_MODEL,
        "provider_host": provider_host,
        "summary": artifact["summary"],
        "failure_count": len(artifact["failures"]),
    }, ensure_ascii=False))
    return 0 if artifact["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
