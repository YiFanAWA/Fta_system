"""Build an evidence-verified, AI-role-only recursive FTA Preview v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.fta_graph_contract import validate_fta_preview  # noqa: E402
from fta.ai_authorized_fta_preview_service import (  # noqa: E402
    build_ai_authorized_fta_preview,
)


DEFAULT_SOURCE = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
DEFAULT_OVERLAY = ROOT / "evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_review_overlay_v1_2026-09-26.json"
DEFAULT_OUTPUT = ROOT / "evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_v2_2026-09-26.json"
DEFAULT_MARKDOWN = ROOT / "evaluation/quality_eval/runs/siemens_s210_recursive_fta_preview_v2_2026-09-26.md"
EXPECTED_SOURCE_SHA256 = "ffbeafa7d9e997a413ae44c1becc953e6319f41ace9ada83885cad6f1b96ac38"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _citation_list(value: Any, location: str):
    if not isinstance(value, list):
        return
    for index, citation in enumerate(value):
        if isinstance(citation, Mapping):
            yield f"{location}[{index}]", citation


def _tree_citations(tree: Mapping[str, Any]):
    yield from _citation_list(tree.get("gate_evidence"), "gate_evidence")

    def visit_relation(relation: Any, path: str):
        if not isinstance(relation, Mapping):
            return
        yield from _citation_list(relation.get("evidence"), f"{path}.evidence")
        node = relation.get("node")
        if not isinstance(node, Mapping):
            return
        yield from _citation_list(node.get("gate_evidence"), f"{path}.node.gate_evidence")
        children = node.get("children", [])
        if isinstance(children, list):
            for child_index, child in enumerate(children):
                yield from visit_relation(child, f"{path}.node.children[{child_index}]")

    children = tree.get("children", [])
    if isinstance(children, list):
        for index, relation in enumerate(children):
            yield from visit_relation(relation, f"children[{index}]")


def _verify_citation(
    fault_code: str,
    location: str,
    citation: Mapping[str, Any],
    source_by_id: Mapping[str, Mapping[str, Any]],
    matching_samples: list[Mapping[str, Any]],
) -> None:
    sample_id = citation.get("source_id")
    sample = source_by_id.get(sample_id)
    if sample is None:
        raise ValueError(f"{fault_code} {location} references unknown source_id {sample_id!r}")
    if sample not in matching_samples:
        raise ValueError(f"{fault_code} {location} cites a different fault sample")
    text = sample.get("input_text")
    start, end, quote = citation.get("start"), citation.get("end"), citation.get("quote")
    if not isinstance(text, str) or not isinstance(start, int) or isinstance(start, bool):
        raise ValueError(f"{fault_code} {location} has invalid source text or start offset")
    if not isinstance(end, int) or isinstance(end, bool) or start < 0 or end <= start or end > len(text):
        raise ValueError(f"{fault_code} {location} has invalid source bounds")
    if not isinstance(quote, str) or text[start:end] != quote:
        raise ValueError(f"{fault_code} {location} quote does not exactly match source offsets")
    if text.count(quote) != 1:
        raise ValueError(f"{fault_code} {location} quote is not unique in the source")


def _verified_decisions(
    source_dataset: Mapping[str, Any], overlay: Mapping[str, Any]
) -> tuple[dict[str, Any], int, int, int]:
    if overlay.get("reviewer_provenance") != "user_authorized_ai_expert_role":
        raise ValueError("overlay reviewer provenance must identify the user-authorized AI role")
    if overlay.get("human_expert_signature") is not False:
        raise ValueError("overlay must not claim a human expert signature")
    for flag in ("formal_gold_mutated", "database_written", "fta_ready", "production_ready"):
        if overlay.get(flag) is not False:
            raise ValueError(f"overlay.{flag} must be false")

    source_by_id: dict[str, Mapping[str, Any]] = {}
    for sample in source_dataset.get("samples", []):
        if isinstance(sample, Mapping) and isinstance(sample.get("sample_id"), str):
            if sample["sample_id"] in source_by_id:
                raise ValueError(f"duplicate source sample_id: {sample['sample_id']}")
            source_by_id[sample["sample_id"]] = sample

    decisions = overlay.get("gate_decisions")
    if not isinstance(decisions, list):
        raise ValueError("overlay.gate_decisions must be a list")
    seen_codes: set[str] = set()
    verified_span_count = 0
    verified_tree_span_count = 0
    verified_exclusion_span_count = 0
    expected_codes = {"F01911", "F07900", "F07901", "F30655"}
    actual_codes = {item.get("fault_code") for item in decisions if isinstance(item, Mapping)}
    if actual_codes != expected_codes:
        raise ValueError(f"overlay fault-code scope mismatch: expected {sorted(expected_codes)}, got {sorted(actual_codes)}")

    for item in decisions:
        if not isinstance(item, dict):
            raise ValueError("every gate decision must be an object")
        fault_code = item.get("fault_code")
        if not isinstance(fault_code, str) or fault_code in seen_codes:
            raise ValueError(f"missing or duplicate fault code in overlay: {fault_code!r}")
        seen_codes.add(fault_code)
        event = item.get("event_node")
        if not isinstance(event, Mapping) or event.get("fault_code") != fault_code:
            raise ValueError(f"{fault_code} top-event identity does not match the decision")
        matching_samples = [
            sample
            for sample in source_by_id.values()
            if any(
                isinstance(record, Mapping) and record.get("fault_code") == fault_code
                for record in sample.get("gold_records", [])
            )
        ]
        if len(matching_samples) != 1:
            raise ValueError(f"{fault_code} must resolve to exactly one source sample")

        reviewed_tree = item.get("reviewed_tree")
        if reviewed_tree is None:
            if fault_code != "F30655" or item.get("build_allowed") is not False:
                raise ValueError(f"{fault_code} has no reviewed tree but is not an explicit exclusion")
            exclusion_evidence = item.get("exclusion_evidence", [])
            if not isinstance(exclusion_evidence, list) or not exclusion_evidence:
                raise ValueError(f"{fault_code} exclusion must cite the unresolved source phrase")
            for index, citation in enumerate(exclusion_evidence):
                if not isinstance(citation, Mapping):
                    raise ValueError(f"{fault_code} exclusion evidence[{index}] must be an object")
                _verify_citation(
                    fault_code,
                    f"exclusion_evidence[{index}]",
                    citation,
                    source_by_id,
                    matching_samples,
                )
                verified_span_count += 1
                verified_exclusion_span_count += 1
            continue
        if item.get("build_allowed") is not True or item.get("preview_scope_complete") is not True:
            raise ValueError(f"{fault_code} recursive preview is not explicitly approved within its scope")
        if item.get("unresolved_blockers") != []:
            raise ValueError(f"{fault_code} has unresolved blockers")

        for location, citation in _tree_citations(reviewed_tree):
            _verify_citation(fault_code, location, citation, source_by_id, matching_samples)
            verified_span_count += 1
            verified_tree_span_count += 1

    return {"gate_decisions": decisions}, verified_span_count, verified_tree_span_count, verified_exclusion_span_count


def build_preview(source_dataset: Mapping[str, Any], overlay: Mapping[str, Any], source_sha256: str) -> dict[str, Any]:
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError("source dataset fingerprint differs from the reviewed source version")
    logic_review, verified_spans, verified_tree_spans, verified_exclusion_spans = _verified_decisions(source_dataset, overlay)
    logic_review.update(
        {
            "artifact_type": overlay.get("artifact_type"),
            "reviewer_provenance": overlay.get("reviewer_provenance"),
            "reviewed_at": overlay.get("reviewed_at"),
        }
    )
    preview = build_ai_authorized_fta_preview({"rows": []}, logic_review)
    preview["dataset_info"].update(
        {
            "source_dataset": overlay.get("source_dataset"),
            "source_dataset_sha256": source_sha256,
            "source_overlay": overlay.get("artifact_type"),
            "source_overlay_schema_version": overlay.get("schema_version"),
            "source_overlay_canonical_sha256": hashlib.sha256(
                json.dumps(overlay, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "human_expert_signature": False,
            "formal_gold_mutated": False,
            "database_written": False,
            "verified_source_span_count": verified_spans,
            "verified_tree_span_count": verified_tree_spans,
            "verified_exclusion_span_count": verified_exclusion_spans,
            "preview_scope": "manual-documented-trigger-conditions-only",
        }
    )
    preview["reviewer_provenance"] = "user_authorized_ai_expert_role"
    preview["review_note"] = (
        "AI-authorized expert-role review preview only; not a human Siemens expert sign-off, "
        "not an instance diagnosis, and not a production FTA."
    )
    errors = validate_fta_preview(preview)
    if errors:
        raise ValueError("generated FTA preview violates contract: " + "; ".join(errors))
    return preview


def _render_evidence(citations: list[Mapping[str, Any]]) -> list[str]:
    return [
        f"原文 `{item['source_id']}[{item['start']}:{item['end']}]`：{item['quote'].replace(chr(10), ' ')}"
        for item in citations
    ]


def render_markdown(preview: Mapping[str, Any]) -> str:
    info = preview["dataset_info"]
    lines = [
        "# Siemens S210 递归证据型 FTA Preview v2",
        "",
        "> AI 授权专家角色审核预览，不是真人 Siemens 专家签署；表达的是手册中的触发条件，不代表设备实例根因或生产可用故障树。",
        "",
        f"- 递归 Preview 树：{info['tree_count']}",
        f"- 排除事件：{info['excluded_event_count']}",
        f"- 已逐字校验原文跨度：{info['verified_source_span_count']}",
        "- 正式 Gold / 数据库写入：否 / 否",
        "- FTA 就绪 / 生产就绪：否 / 否",
        "",
    ]

    def render_relation(relation: Mapping[str, Any], depth: int) -> None:
        node = relation["node"]
        indent = "  " * depth
        node_children = node.get("children", [])
        if node_children:
            lines.append(f"{indent}- **{node['gate']}** `{node['node_type']}`：{node['text']}")
            lines.append(f"{indent}  - 门证据：")
            lines.extend(f"{indent}    - {line}" for line in _render_evidence(node["gate_evidence"]))
            for child in node_children:
                render_relation(child, depth + 1)
        else:
            lines.append(f"{indent}- `{node['node_type']}`：{node['text']}")
            for evidence in relation["evidence"]:
                lines.append(
                    f"{indent}  - 关系证据：{evidence['source_id']}[{evidence['start']}:{evidence['end']}] "
                    f"“{evidence['quote'].replace(chr(10), ' ')}”"
                )

    for tree in preview["trees"]:
        event = tree["top_event"]
        lines.extend(
            [
                f"## {event['fault_code']} · {event['description']}",
                "",
                f"- 根逻辑门：**{tree['gate']}**（AI 审核的文档触发条件结构，非现场根因判断）",
                "- 根门证据：",
            ]
        )
        lines.extend(f"  - {line}" for line in _render_evidence(tree["gate_evidence"]))
        for relation in tree["children"]:
            render_relation(relation, 0)
        lines.extend([""])

    if preview["excluded_events"]:
        lines.extend(["## 保持排除的事件", ""])
        for event in preview["excluded_events"]:
            lines.append(f"- **{event.get('fault_code')}**：{event.get('reason')}")
            for evidence in event.get("evidence", []):
                lines.append(
                    f"  - 依据 `{evidence.get('source_id')}[{evidence.get('start')}:{evidence.get('end')}]`："
                    f"{str(evidence.get('quote', '')).replace(chr(10), ' ')}"
                )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    source_bytes = args.source.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    source_dataset = json.loads(source_bytes.decode("utf-8"))
    overlay = _read_json(args.overlay)
    preview = build_preview(source_dataset, overlay, source_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(preview), encoding="utf-8")
    print(
        json.dumps(
            {
                "trees": preview["dataset_info"]["tree_count"],
                "excluded": preview["dataset_info"]["excluded_event_count"],
                "verified_source_spans": preview["dataset_info"]["verified_source_span_count"],
                "fta_ready": preview["dataset_info"]["fta_ready"],
                "production_ready": preview["dataset_info"]["production_ready"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
