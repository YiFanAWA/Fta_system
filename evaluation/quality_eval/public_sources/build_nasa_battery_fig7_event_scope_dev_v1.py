#!/usr/bin/env python3
"""Build a bounded development packet and separate reference Gold for NASA Figure 7."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PACKET_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_event_scope_nasa_battery_fig7_module_failure_dev_v1.json"
GOLD_PATH = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_event_scope_nasa_battery_fig7_module_failure_reference_gold_v1.json"
SOURCE_SCREEN_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29.json"
AI_REVIEW_PATH = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_event_scope_nasa_battery_fig7_ai_role_review_v1_2026-09-29.json"
SOURCE_URL = "https://ntrs.nasa.gov/citations/19880001643"
DOCUMENT_ID = "NASA_NTRS_19880001643"
SOURCE_CLUSTER_ID = "NASA_GSFC_LISOCL2_BATTERY_SAFETY_ANALYSIS_1987"
DOCUMENT_SHA256 = "15ed643797e80ddca990e4c74bc4767bb073898ff7d144e3bbadc7a76b993a29"
PACKET_ID = "NASA_GSFC_BATTERY_FIG7_MODULE_FAILURE_DEV_001"
CAPTURED_AT = "2026-09-29"
AI_REVIEWER_ID = "Tesla the 2nd (AI role reviewer)"

SOURCE_TEXT = (
    "5.0 DEVELOPMENT OF FAULT TREE ANALYSIS\n\n"
    "In the fault tree the Top Event whose occurrence is potentially catastrophic leading to mission failure is the explosion or structural fragmentation of a battery module originated by the explosion of one or more cells in the battery pack. A single cell explosion may lead to the Top Event if the module container fails to operate as designed and relieve the overpressure condition; thus, a primary explosion may cause the Top Event. In addition, a single cell explosion may cause the Top Event to occur by creating overpressure and overtemperature conditions inside the battery pack which damage or make other neighboring batteries unstable leading to a second sympathetic explosion of such speed (less than 100 milliseconds) and force that not enough venting can occur soon enough even with the module vents functioning as designed (see Figures 7 and 8).\n\n"
    "Basic events which either initiate the Top Event or enable it to occur are shown as ovals in the fault tree diagrams. AND gates in the tree are marked with A; OR gates with O. Intermediate and Top Events are shown as rectangles. Due to the size of the fault tree, it has been split into two figures with the intermediate event, single cell explodes, common to each main branch in Figures 7 and 8 and shown in detail in Figure 9. Figures 7 and 8 show that a single cell exploding and the failure of the module vents or a single cell exploding and the module operating nominally but with a sympathetic secondary explosion occurring can lead to the Top Event."
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _model_input_sha256(model_input: dict[str, Any]) -> str:
    canonical = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_text(canonical)


def build_artifacts() -> dict[Path, dict[str, Any]]:
    packet = {
        "packet_schema": "fta_event_scope_input_packet_v1",
        "packet_id": PACKET_ID,
        "source_provenance": {
            "document_id": DOCUMENT_ID,
            "source_cluster_id": SOURCE_CLUSTER_ID,
            "official_record_url": SOURCE_URL,
            "document_sha256": DOCUMENT_SHA256,
            "page_count": 26,
            "rights_status": "public_use_permitted",
            "exposure_status": "seen_development_only",
        },
        "model_input": {
            "event_scope_id": "scope-001",
            "top_event": {
                "text": "explosion or structural fragmentation of a battery module",
                "evidence": {
                    "segment_id": "source-pdf-p3-p4-section-5",
                    "quote": "the explosion or structural fragmentation of a battery module",
                },
            },
            "source_segments": [
                {
                    "segment_id": "source-pdf-p3-p4-section-5",
                    "page_number": 3,
                    "section_locator": "Section 5.0; PDF pp. 3-4; printed pp. 96-97 (continuous passage across page break)",
                    "text": SOURCE_TEXT,
                }
            ],
        },
    }

    provenance = {
        "reviewer_role": "ai_role_review",
        "reviewer_id": AI_REVIEWER_ID,
        "review_status": "reviewed",
        "reviewed_at": CAPTURED_AT,
    }
    evidence_segment_id = "source-pdf-p3-p4-section-5"
    gold = {
        "gold_schema": "fta_event_scope_reference_gold_v1",
        "packet_id": PACKET_ID,
        "model_input_sha256": _model_input_sha256(packet["model_input"]),
        "source_cluster_id": SOURCE_CLUSTER_ID,
        "source_document_id": DOCUMENT_ID,
        "source_document_sha256": DOCUMENT_SHA256,
        "root_node_id": "module-failure",
        "nodes": [
            {"node_id": "module-failure", "text": "Module failure", "node_type": "top_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "secondary-explosion", "text": "Secondary explosion", "node_type": "intermediate_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "module-structural-failure", "text": "Module structural failure", "node_type": "intermediate_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "module-operates-nominally", "text": "Module operates nominally", "node_type": "basic_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "single-cell-explodes-secondary-branch", "text": "Single cell explodes", "node_type": "intermediate_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "two-module-vents-clog", "text": "Two module vents clog", "node_type": "basic_event", "page_number": 20, "figure_id": "Figure 7"},
            {"node_id": "single-cell-explodes-structural-branch", "text": "Single cell explodes", "node_type": "intermediate_event", "page_number": 20, "figure_id": "Figure 7"},
        ],
        "diagram_gates": [
            {
                "scope_id": "module-failure-gate",
                "output_node_id": "module-failure",
                "child_node_ids": ["secondary-explosion", "module-structural-failure"],
                "diagram_reference_gate": "OR",
                "page_number": 20,
                "figure_id": "Figure 7",
            },
            {
                "scope_id": "secondary-explosion-gate",
                "output_node_id": "secondary-explosion",
                "child_node_ids": ["module-operates-nominally", "single-cell-explodes-secondary-branch"],
                "diagram_reference_gate": "AND",
                "page_number": 20,
                "figure_id": "Figure 7",
            },
            {
                "scope_id": "module-structural-failure-gate",
                "output_node_id": "module-structural-failure",
                "child_node_ids": ["two-module-vents-clog", "single-cell-explodes-structural-branch"],
                "diagram_reference_gate": "AND",
                "page_number": 20,
                "figure_id": "Figure 7",
            },
        ],
        "text_gate_reviews": [
            {
                "scope_id": "module-failure-gate",
                "text_authorized_gate": "OR",
                "unknown_reason": None,
                "evidence": {
                    "segment_id": evidence_segment_id,
                    "quote": "Figures 7 and 8 show that a single cell exploding and the failure of the module vents or a single cell exploding and the module operating nominally but with a sympathetic secondary explosion occurring can lead to the Top Event.",
                },
                "review_provenance": dict(provenance),
            },
            {
                "scope_id": "secondary-explosion-gate",
                "text_authorized_gate": "AND",
                "unknown_reason": None,
                "evidence": {
                    "segment_id": evidence_segment_id,
                    "quote": "a single cell exploding and the module operating nominally but with a sympathetic secondary explosion occurring",
                },
                "review_provenance": dict(provenance),
            },
            {
                "scope_id": "module-structural-failure-gate",
                "text_authorized_gate": "unknown",
                "unknown_reason": "scope_ambiguity",
                "evidence": None,
                "review_provenance": dict(provenance),
            },
        ],
    }

    screen = {
        "audit_id": "fta_event_scope_nasa_battery_fig7_source_screen_v1_2026-09-29",
        "captured_at": CAPTURED_AT,
        "purpose": "Whole-document source suitability and provenance screen for one evaluation-only, bounded single-event development case.",
        "source_document": {
            "document_id": DOCUMENT_ID,
            "title": "Fault tree safety analysis of a large Li/SOCl2 spacecraft battery",
            "authors": ["O. Manuel Uy", "R. H. Maurer"],
            "publication_date": "1987-09-01",
            "ntrs_acquired_date": "2013-09-05",
            "official_record_url": SOURCE_URL,
            "download_url": "https://ntrs.nasa.gov/api/citations/19880001643/downloads/19880001643.pdf?attachment=true",
            "document_sha256": DOCUMENT_SHA256,
            "page_count": 26,
            "pdf_downloaded": True,
            "whole_document_text_scanned": True,
            "cover_visually_checked": True,
            "visual_pages_checked": [20, 21, 22, 23, 24, 25, 26],
            "rights_status": "public_use_permitted",
            "rights_evidence": "Official NASA NTRS record lists Distribution Limits: Public and Copyright: Work of the US Gov. Public Use Permitted.",
            "rights_review": "metadata-based internal-evaluation screening only; not legal review and does not authorize redistribution",
        },
        "source_cluster": {
            "source_cluster_id": SOURCE_CLUSTER_ID,
            "preexisting_exact_identifier_and_title_scan": {
                "search_scope": ["evaluation/", "docs/", "README.md"],
                "found": False,
            },
            "semantic_overlap_audit_complete": False,
            "allocation": "development_only",
        },
        "content_screen": {
            "candidate_scope": "Figure 7, Module failure (spacecraft battery module)",
            "prose_pages": [3, 4],
            "prose_printed_pages": [96, 97],
            "diagram_pdf_page": 20,
            "diagram_printed_page": 113,
            "diagram_reference_gate_count": 3,
            "tree_nodes": 7,
            "suitability_reason": "Section 5.0 explicitly names the top event and describes two alternative paths plus conjunctive conditions. For the structural-failure path, however, the prose only says 'failure of the module vents', not the diagram's more specific 'Two module vents clog'; the exact gate scope is therefore left unknown. Figure 7 gives a small, readable reference graph for testing evidence-bound gate authorization.",
            "transcription_method": "Manual visual transcription of source prose; line wraps and scan/OCR artifacts normalized while wording was checked against the page images.",
            "known_limitations": [
                "The PDF and Figures 7-13 were opened by the evaluator; the entire source cluster is seen development-only and is not eligible for independent Final.",
                "The packet is a single event from one 1987 battery report; one case cannot establish accuracy, calibration, or generalization.",
                "The packet and Gold are separate files, but both are curator-visible; only the validated model_input projection may be sent to the model.",
                "The independent AI role reviewer found direct textual AND/OR operators for all three diagram scopes; only two exact scopes receive text-authorized labels because 'Two module vents clog' is diagram-only while the prose supports only the broader 'failure of the module vents'.",
                "Figure 7 contains two separate 'Single cell explodes' occurrences; reference Gold preserves them as separate graph nodes rather than a shared node.",
                "Figure 7 root label 'Module failure' is retained as a diagram label; it is not asserted to be an exact textual synonym for the prose top event.",
                "Text-gate review is AI-role review only, not human expert signoff or formal Gold.",
                "Source-family semantic overlap has not been fully audited; do not claim independent holdout status.",
                "Rights status is based on NTRS metadata; no legal review or redistribution permission is asserted."
            ]
        },
        "evaluation_suitability": {
            "status": "seen_development_only",
            "eligible_for_independent_final": False,
            "input_packet_created": True,
            "reference_gold_created": True,
            "model_inference_run": False,
            "accuracy_claim_allowed": False,
            "production_or_formal_gold_use_allowed": False
        },
        "model_gold_separation": {
            "packet_id": PACKET_ID,
            "model_input_artifact": str(PACKET_PATH.relative_to(ROOT)).replace("\\", "/"),
            "reference_gold_artifact": str(GOLD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "ai_role_review_artifact": str(AI_REVIEW_PATH.relative_to(ROOT)).replace("\\", "/"),
            "packet_schema_projection": "model_input_only",
            "diagram_reference_gate_labels_in_model_input": False,
            "text_authorized_gate_labels_in_model_input": False,
            "source_diagram_pages_in_model_input": False,
            "gold_review_status": "ai_role_reviewed_not_human_expert_gold"
        }
    }
    ai_review = {
        "review_schema": "fta_event_scope_ai_role_review_v1",
        "review_id": "fta_event_scope_nasa_battery_fig7_ai_role_review_v1_2026-09-29",
        "packet_id": PACKET_ID,
        "source_cluster_id": SOURCE_CLUSTER_ID,
        "reviewer": {
            "role": "ai_role_review",
            "reviewer_id": AI_REVIEWER_ID,
            "human_expert": False,
            "reviewed_at": CAPTURED_AT,
        },
        "overall_disposition": "reviewed_with_reference_graph_occurrence_correction",
        "gate_operator_findings": [
            {"scope_id": "module-failure-gate", "diagram_gate": "OR", "text_observed_operator": "OR", "text_authorized_gate": "OR", "text_operator_directly_supported": True, "exact_scope_authorized": True, "unknown_reason": None, "evidence_quote": "a single cell exploding and the failure of the module vents or a single cell exploding and the module operating nominally"},
            {"scope_id": "secondary-explosion-gate", "diagram_gate": "AND", "text_observed_operator": "AND", "text_authorized_gate": "AND", "text_operator_directly_supported": True, "exact_scope_authorized": True, "unknown_reason": None, "evidence_quote": "a single cell exploding and the module operating nominally"},
            {"scope_id": "module-structural-failure-gate", "diagram_gate": "AND", "text_observed_operator": "AND", "text_authorized_gate": "unknown", "text_operator_directly_supported": True, "exact_scope_authorized": False, "unknown_reason": "scope_ambiguity", "evidence_quote": "a single cell exploding and the failure of the module vents"},
        ],
        "reference_graph_findings": [
            {
                "finding": "duplicate_event_occurrences_must_remain_distinct_nodes",
                "detail": "Figure 7 draws two separate 'Single cell explodes' event boxes under different branches. The reference graph now uses separate occurrence node IDs.",
                "status": "corrected",
            },
            {
                "finding": "diagram_child_label_is_more_specific_than_text",
                "detail": "The diagram's 'Two module vents clog' oval is retained as a diagram-reference basic event. The provided prose says 'failure of the module vents' and does not establish that exactly two vents clog. Although an AND operator is explicitly observed for the broader prose conditions, the exact output/child scope is not text-authorized; the text label is therefore unknown with scope_ambiguity.",
                "status": "scope_difference_recorded",
            },
            {
                "finding": "diagram_root_label_differs_from_prose_top_event_wording",
                "detail": "The diagram label 'Module failure' remains a reference-graph label; the prose top event is 'explosion or structural fragmentation of a battery module'. No exact synonym equivalence is asserted.",
                "status": "scope_difference_recorded",
            },
        ],
        "review_limitations": [
            "This is an AI-role review, not human domain-expert signoff and not formal Gold.",
            "Review checks the three Boolean operators and diagram transcription for one seen-development case only; it does not establish model performance, calibration, or generalization.",
            "The model input did not contain the Figure 7 image, graph, expected gates, or reviewer labels.",
        ],
    }
    return {
        PACKET_PATH: packet,
        GOLD_PATH: gold,
        SOURCE_SCREEN_PATH: screen,
        AI_REVIEW_PATH: ai_review,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated artifacts without writing")
    args = parser.parse_args()
    artifacts = build_artifacts()
    mismatches: list[str] = []
    for path, payload in artifacts.items():
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            existing = path.read_text(encoding="utf-8") if path.exists() else None
            if existing != rendered:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(rendered, encoding="utf-8", newline="\n")
    if args.check and mismatches:
        parser.exit(1, "development case artifacts differ: " + ", ".join(mismatches) + "\n")
    print(json.dumps({
        "status": "current" if args.check else "written",
        "packet_count": 1,
        "reference_gold_count": 1,
        "source_screen": "seen_development_only",
        "model_inference_run": False,
        "independent_final_eligible": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
