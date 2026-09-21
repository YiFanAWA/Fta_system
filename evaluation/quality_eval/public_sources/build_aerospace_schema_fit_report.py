"""Generate the Phase G FAA SDR -> Common Fault Schema fit report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402


DEFAULT_SAMPLE = ROOT / "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"
DEFAULT_JSON = ROOT / "evaluation/quality_eval/runs/aerospace_schema_fit_report_v1_2026-09-21.json"
DEFAULT_MD = ROOT / "evaluation/quality_eval/runs/aerospace_schema_fit_report_v1_2026-09-21.md"


MAPPING_ROWS = (
    {
        "source_field": "OperatorControlNumber",
        "target": "FaultEntity.fault_code + domain_specific.source_record_id",
        "retrieval_role": "identity / metadata",
        "loss_status": "adapted",
        "note": "FAA SDR has no native fault-code column; the source record identifier fills the required identity slot and is explicitly typed. Generic v1 exact ranking uses JASC as the single adapter exact identifier; record-id exact ranking is not claimed.",
    },
    {
        "source_field": "JASCCode",
        "target": "domain_specific.jasc_code + RetrievalFieldValues.exact_identifier",
        "retrieval_role": "exact_identifier",
        "loss_status": "preserved",
        "note": "JASC is not promoted to a unique fault entity because multiple reports can share one JASC code.",
    },
    {
        "source_field": "Discrepancy",
        "target": "FaultEntity.description + raw_text + evidence",
        "retrieval_role": "semantic_primary",
        "loss_status": "preserved",
        "note": "The original narrative is retained; an explicit C/A: suffix is separately exposed as remedy.",
    },
    {
        "source_field": "PartCondition",
        "target": "FaultEntity.symptoms + domain_specific.part_condition",
        "retrieval_role": "semantic condition / reranker",
        "loss_status": "preserved",
        "note": "Condition is not relabeled as a cause.",
    },
    {
        "source_field": "PartName / ComponentName",
        "target": "FaultEntity.components + domain_specific component fields",
        "retrieval_role": "metadata / reranker",
        "loss_status": "preserved",
        "note": "UNKNOWN placeholders are not promoted to components.",
    },
    {
        "source_field": "PartNumber / ComponentPartNumber",
        "target": "FaultEntity.parameters",
        "retrieval_role": "exact_parameters",
        "loss_status": "preserved",
        "note": "Part numbers are kept as exact values; they are not treated as Siemens-style parameters.",
    },
    {
        "source_field": "AircraftMake / AircraftModel",
        "target": "domain_specific.aircraft_make/model + metadata",
        "retrieval_role": "metadata / reranker",
        "loss_status": "preserved",
        "note": "Aircraft identity is available to the parent document without changing generic ranking.",
    },
    {
        "source_field": "NatureOfConditionA-C",
        "target": "domain_specific.nature_of_condition_codes",
        "retrieval_role": "metadata",
        "loss_status": "preserved",
        "note": "Codes are retained as codes; no unsupported natural-language cause is invented.",
    },
    {
        "source_field": "PrecautionaryProcedureA-D",
        "target": "domain_specific.precautionary_procedure_codes",
        "retrieval_role": "metadata",
        "loss_status": "preserved",
        "note": "The CSV contains procedure codes, not a complete free-text maintenance action field.",
    },
    {
        "source_field": "StageOfOperationCode / HowDiscoveredCode",
        "target": "domain_specific stage/how-discovered fields",
        "retrieval_role": "metadata",
        "loss_status": "preserved",
        "note": "These are source codes, not a derived flight phase or causal label.",
    },
    {
        "source_field": "C/A: text embedded in Discrepancy",
        "target": "FaultEntity.remedies",
        "retrieval_role": "semantic_auxiliary",
        "loss_status": "partial",
        "note": "Only explicit C/A: text is parsed; the source has no dedicated structured corrective-action column.",
    },
    {
        "source_field": "BIT code",
        "target": "not present in FAA SDR 2024 sample",
        "retrieval_role": "not available",
        "loss_status": "absent",
        "note": "Must not be fabricated; add only when a later aerospace source provides it.",
    },
    {
        "source_field": "ATA chapter",
        "target": "not explicit; JASC retained instead",
        "retrieval_role": "not available",
        "loss_status": "absent",
        "note": "No derived ATA chapter is created in this adapter.",
    },
    {
        "source_field": "flight phase",
        "target": "not explicit; StageOfOperationCode retained",
        "retrieval_role": "not available",
        "loss_status": "absent",
        "note": "The adapter does not reinterpret a source stage code as a standardized flight phase.",
    },
    {
        "source_field": "relations / AND-OR gates",
        "target": "FaultEntity.relations=empty; review_status unknown",
        "retrieval_role": "not available",
        "loss_status": "absent",
        "note": "This Phase G sample is entity/evidence/retrieval validation only, not FTA labeling.",
    },
)


def build(sample_path: Path) -> dict[str, Any]:
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    adapter = FaaSdrAerospaceAdapter()
    entities = adapter.parse_source(payload)
    raw_records = [sample.get("raw_record", {}) for sample in payload.get("samples", [])]
    required_fields = (
        "OperatorControlNumber",
        "JASCCode",
        "AircraftModel",
        "Discrepancy",
    )
    field_coverage = {
        field: sum(bool(str(row.get(field) or "").strip()) for row in raw_records)
        for field in required_fields
    }
    evidence_valid = 0
    for entity in entities:
        if all(
            evidence.start is not None
            and evidence.end is not None
            and entity.raw_text[evidence.start : evidence.end] == evidence.quote
            for evidence in entity.evidence
        ):
            evidence_valid += 1

    report = {
        "report_id": "aerospace_schema_fit_report_v1",
        "generated_date": "2026-09-21",
        "dataset_id": payload.get("dataset_id"),
        "dataset_role": payload.get("dataset_role"),
        "source": payload.get("source", {}),
        "adapter": "FaaSdrAerospaceAdapter",
        "common_schema_contract": "Common Fault Schema v1",
        "summary": {
            "raw_records": len(raw_records),
            "entities": len(entities),
            "unique_entity_ids": len({entity.entity_id for entity in entities}),
            "unique_source_record_ids": len({entity.fault_code for entity in entities}),
            "evidence_complete_entities": evidence_valid,
            "retrieval_chunk_count": len(adapter.build_retrieval_chunks(entities)),
            "native_fault_code_present": False,
            "lossless_raw_record_preservation": all("raw_record" in entity.domain_specific for entity in entities),
        },
        "field_coverage": field_coverage,
        "mapping_rows": list(MAPPING_ROWS),
        "missing_or_not_derived": [
            "BIT code",
            "explicit ATA chapter",
            "standardized flight phase",
            "native structured fault code",
            "expert cause labels",
            "fault relations and AND/OR gates",
        ],
        "decision": "fit_with_explicit_adaptations",
        "next_gate": "Build Aerospace Retrieval Dev v1; do not change Generic Pipeline unless an error taxonomy shows a public contract gap.",
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aerospace Schema Fit Report v1",
        "",
        "## 结论",
        "",
        "> FAA SDR 2024 的 40 条公开样本可以进入 Common Fault Schema v1，但存在明确的领域适配：原始记录没有原生 fault code，当前使用 OperatorControlNumber 作为唯一记录身份；JASCCode 作为 exact identifier 保留。该样本不是专家金标，也不能证明航空检索泛化。",
        "",
        "## 样本与证据",
        "",
        f"- 原始样本：{report['summary']['raw_records']} 条。",
        f"- Common Fault Entity：{report['summary']['entities']} 条；唯一 entity_id：{report['summary']['unique_entity_ids']} 条。",
        f"- RetrievalChunk：{report['summary']['retrieval_chunk_count']} 个。",
        f"- 字符证据可回溯实体：{report['summary']['evidence_complete_entities']}/{report['summary']['entities']}。",
        "- 原始 CSV 字段保存在每个 entity 的 `domain_specific.raw_record`，不把缺失字段推断成标签。",
        "",
        "## 字段映射",
        "",
        "| 原始字段 | Common Schema 目标 | 检索角色 | 状态 | 说明 |",
        "|---|---|---|---|---|",
    ]
    for row in report["mapping_rows"]:
        lines.append(
            f"| `{row['source_field']}` | `{row['target']}` | `{row['retrieval_role']}` | **{row['loss_status']}** | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## 明确缺失或暂不派生",
            "",
            *[f"- {item}" for item in report["missing_or_not_derived"]],
            "",
            "## 边界",
            "",
            "- 当前只完成 G1（公开样本）和 G2/G3（Adapter + Fit Report）。",
            "- 未修改 Generic Retrieval Pipeline，未实现 Domain Router，未建立航空专家 Gold。",
            "- 下一步是建立 Aerospace Retrieval Dev v1，并先做错误分类；不能直接把 Dev 结果当 Final Test 或生产结论。",
            "",
            "## 来源",
            "",
            f"- {report['source'].get('source_url', '')}",
            "- 来源：FAA Service Difficulty Reports 2024 CSV；具体条款和再利用边界仍应按 FAA 页面与下载说明核对。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    report = build(args.sample)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"json": str(args.output_json), "markdown": str(args.output_md), "decision": report["decision"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
