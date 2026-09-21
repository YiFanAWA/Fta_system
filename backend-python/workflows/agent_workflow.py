from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from workflows.ai_module import (
    analyze_fault_tree_report,
    convert_fault_records_to_failures,
    extract_fault_records_from_text,
    generate_failure_events,
    review_fault_tree_draft,
)
from fta.fta_generator import build_fault_tree
from fta.kg_builder import create_failure_nodes
from fta.kg_reasoner import get_failure_paths


@dataclass
class AgentStageResult:
    stage: str
    status: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "stage": self.stage,
            "status": self.status,
            "detail": self.detail,
        }


def run_agent_workflow(
    *,
    system: str,
    top_event: str,
    source: str,
    manual_failures: Optional[List[Dict[str, Any]]] = None,
    raw_text: Optional[str] = None,
    text_chunk_size_chars: int = 6000,
    text_chunk_overlap_chars: int = 300,
    use_knowledge_graph: bool = True,
    run_analysis_report: bool = True,
    run_draft_review: bool = True,
    prompt_profile: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> Dict[str, Any]:
    stages: List[AgentStageResult] = []
    started_at = datetime.utcnow().isoformat() + "Z"

    def mark(stage: str, status: str, detail: str) -> None:
        stages.append(AgentStageResult(stage, status, detail))

    extracted_faults = None

    mark("TextParserAgent", "running", f"source={source}")
    if source == "manual":
        failures = manual_failures or []
        if not failures:
            raise ValueError("manual_failures不能为空")
    elif source == "text":
        if not raw_text or not raw_text.strip():
            raise ValueError("source=text时，raw_text不能为空")

        extracted_faults = extract_fault_records_from_text(
            raw_text,
            chunk_size_chars=text_chunk_size_chars,
            overlap_chars=text_chunk_overlap_chars,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )
        failures = convert_fault_records_to_failures(extracted_faults.get("records", []))
    else:
        failures = generate_failure_events(
            system,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )
    mark("TextParserAgent", "done", f"failures={len(failures)}")

    if use_knowledge_graph:
        mark("KnowledgeGraphAgent", "running", "upsert failures into Neo4j")
        create_failure_nodes(system, failures)
        mark("KnowledgeGraphAgent", "done", "graph updated")

        mark("ReasoningAgent", "running", "read inferred failure paths")
        events = get_failure_paths(system)
        mark("ReasoningAgent", "done", f"events={len(events)}")
    else:
        events = failures
        mark("KnowledgeGraphAgent", "skipped", "use_knowledge_graph=False")
        mark("ReasoningAgent", "skipped", "use_knowledge_graph=False")

    mark("FTAAgent", "running", "build fault tree")
    tree = build_fault_tree(top_event, events)
    mark("FTAAgent", "done", "tree generated")

    analysis_report = None
    draft_review = None

    if run_analysis_report:
        mark("ReportAgent", "running", "analysis report")
        analysis_report = analyze_fault_tree_report(
            system,
            top_event,
            tree,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )
        mark("ReportAgent", "done", "analysis report generated")
    else:
        mark("ReportAgent", "skipped", "run_analysis_report=False")

    if run_draft_review:
        mark("ReviewAgent", "running", "draft review")
        draft_review = review_fault_tree_draft(
            system,
            top_event,
            tree,
            prompt_profile=prompt_profile,
            custom_instructions=custom_instructions,
        )
        mark("ReviewAgent", "done", "draft review generated")
    else:
        mark("ReviewAgent", "skipped", "run_draft_review=False")

    finished_at = datetime.utcnow().isoformat() + "Z"

    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "stages": [s.to_dict() for s in stages],
        "extracted_faults": extracted_faults,
        "events": events,
        "tree": tree,
        "analysis_report": analysis_report,
        "draft_review": draft_review,
    }
