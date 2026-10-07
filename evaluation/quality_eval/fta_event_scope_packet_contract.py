"""Validation and safe projection for evaluation-only, single-event FTA packets.

The model receives only ``packet["model_input"]``. Diagram-derived reference
gates and their review labels belong in a separate Gold artifact.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_INPUT_KEYS = {"event_scope_id", "top_event", "source_segments"}
_SEGMENT_KEYS = {"segment_id", "page_number", "section_locator", "text"}
_GOLD_GATE_KEYS = {"AND", "OR", "unknown"}
_DIAGRAM_GATE_KEYS = {"AND", "OR", "NOT", "VOTING", "OTHER", "UNREADABLE"}
_UNKNOWN_REASONS = {
    "no_direct_logic_evidence",
    "incomplete_child_set",
    "scope_ambiguity",
    "input_context_unavailable",
}
_REVIEWER_ROLES = {"human_expert", "ai_role_review", "engineering_review", "unreviewed"}
_NODE_TYPES = {"top_event", "intermediate_event", "basic_event", "undeveloped_event"}
_MODEL_INPUT_FORBIDDEN_KEYS = {
    "gold", "reference_graph", "diagram_reference_gate", "text_authorized_gate",
    "expected_gate", "gate_label", "review_provenance", "reviewer_role",
}


class ScopePacketValidationError(ValueError):
    """Raised when an evaluation packet or its separate Gold violates contract."""


def _model_input_sha256(model_input: dict[str, Any]) -> str:
    canonical = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScopePacketValidationError(f"{path} must be an object")
    return value


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScopePacketValidationError(f"{path} must be a non-empty string")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], path: str) -> None:
    if value.keys() != expected:
        missing = sorted(expected - value.keys())
        extra = sorted(value.keys() - expected)
        raise ScopePacketValidationError(f"{path} keys mismatch; missing={missing}, extra={extra}")


def _reject_label_keys(value: Any, path: str = "model_input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _MODEL_INPUT_FORBIDDEN_KEYS:
                raise ScopePacketValidationError(f"{path}.{key} is forbidden in model-visible input")
            _reject_label_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_label_keys(child, f"{path}[{index}]")


def validate_input_packet(packet: Any) -> dict[str, Any]:
    """Validate packet provenance and bounded one-event model input."""
    root = _require_object(packet, "packet")
    _require_exact_keys(root, {"packet_schema", "packet_id", "source_provenance", "model_input"}, "packet")
    if root["packet_schema"] != "fta_event_scope_input_packet_v1":
        raise ScopePacketValidationError("unsupported packet_schema")
    _require_string(root["packet_id"], "packet.packet_id")

    provenance = _require_object(root["source_provenance"], "packet.source_provenance")
    _require_exact_keys(
        provenance,
        {"document_id", "source_cluster_id", "official_record_url", "document_sha256", "page_count", "rights_status", "exposure_status"},
        "packet.source_provenance",
    )
    for key in ("document_id", "source_cluster_id", "official_record_url"):
        _require_string(provenance[key], f"packet.source_provenance.{key}")
    parsed_url = urlparse(provenance["official_record_url"])
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ScopePacketValidationError("source_provenance.official_record_url must be an HTTPS URL")
    if not isinstance(provenance["document_sha256"], str) or not _SHA256.fullmatch(provenance["document_sha256"]):
        raise ScopePacketValidationError("source_provenance.document_sha256 must be lowercase SHA-256")
    if isinstance(provenance["page_count"], bool) or not isinstance(provenance["page_count"], int) or provenance["page_count"] < 1:
        raise ScopePacketValidationError("source_provenance.page_count must be a positive integer")
    if not isinstance(provenance["rights_status"], str) or provenance["rights_status"] not in {"public_use_permitted", "public_distribution", "unknown", "restricted"}:
        raise ScopePacketValidationError("unsupported source rights_status")
    if not isinstance(provenance["exposure_status"], str) or provenance["exposure_status"] not in {"unseen_candidate", "seen_development_only", "final_locked"}:
        raise ScopePacketValidationError("unsupported source exposure_status")

    model_input = _require_object(root["model_input"], "packet.model_input")
    _require_exact_keys(model_input, _INPUT_KEYS, "packet.model_input")
    _reject_label_keys(model_input)
    _require_string(model_input["event_scope_id"], "model_input.event_scope_id")
    top_event = _require_object(model_input["top_event"], "model_input.top_event")
    _require_exact_keys(top_event, {"text", "evidence"}, "model_input.top_event")
    _require_string(top_event["text"], "model_input.top_event.text")
    evidence = _require_object(top_event["evidence"], "model_input.top_event.evidence")
    _require_exact_keys(evidence, {"segment_id", "quote"}, "model_input.top_event.evidence")
    _require_string(evidence["segment_id"], "model_input.top_event.evidence.segment_id")
    _require_string(evidence["quote"], "model_input.top_event.evidence.quote")

    segments = model_input["source_segments"]
    if not isinstance(segments, list) or not 1 <= len(segments) <= 30:
        raise ScopePacketValidationError("model_input.source_segments must contain 1..30 segments")
    by_id: dict[str, dict[str, Any]] = {}
    total_chars = 0
    for index, raw_segment in enumerate(segments):
        segment = _require_object(raw_segment, f"model_input.source_segments[{index}]")
        _require_exact_keys(segment, _SEGMENT_KEYS, f"model_input.source_segments[{index}]")
        segment_id = _require_string(segment["segment_id"], f"source_segments[{index}].segment_id")
        if segment_id in by_id:
            raise ScopePacketValidationError(f"duplicate segment_id: {segment_id}")
        page = segment["page_number"]
        if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= provenance["page_count"]:
            raise ScopePacketValidationError(f"source_segments[{index}].page_number is outside source")
        _require_string(segment["section_locator"], f"source_segments[{index}].section_locator")
        text = _require_string(segment["text"], f"source_segments[{index}].text")
        if len(text) > 12000:
            raise ScopePacketValidationError(f"source_segments[{index}].text exceeds 12000 characters")
        total_chars += len(text)
        by_id[segment_id] = segment
    if total_chars > 50000:
        raise ScopePacketValidationError("model-visible source text exceeds 50000 characters")

    evidence_segment = by_id.get(evidence["segment_id"])
    if evidence_segment is None:
        raise ScopePacketValidationError("top-event evidence references an unknown segment")
    quote = evidence["quote"]
    if evidence_segment["text"].count(quote) != 1:
        raise ScopePacketValidationError("top-event quote must occur exactly once in its cited segment")
    if quote not in top_event["text"] and top_event["text"] not in quote:
        raise ScopePacketValidationError("top-event text must match or be contained by its source quote")
    return root


def model_input_payload(packet: Any) -> dict[str, Any]:
    """Return only the validated model-visible payload, excluding provenance/GOLD."""
    validated = validate_input_packet(packet)
    payload = validated["model_input"]
    _reject_label_keys(payload)
    return deepcopy(payload)


def validate_reference_gold(packet: Any, gold: Any) -> dict[str, Any]:
    """Validate graph identity, diagram gates, and separate text-authorized labels."""
    validated_packet = validate_input_packet(packet)
    root = _require_object(gold, "gold")
    _require_exact_keys(
        root,
        {"gold_schema", "packet_id", "model_input_sha256", "source_cluster_id", "source_document_id", "source_document_sha256", "root_node_id", "nodes", "diagram_gates", "text_gate_reviews"},
        "gold",
    )
    if root["gold_schema"] != "fta_event_scope_reference_gold_v1":
        raise ScopePacketValidationError("unsupported gold_schema")
    for key in ("packet_id", "source_cluster_id", "source_document_id", "root_node_id"):
        _require_string(root[key], f"gold.{key}")
    provenance = validated_packet["source_provenance"]
    if root["packet_id"] != validated_packet["packet_id"]:
        raise ScopePacketValidationError("gold.packet_id does not match input packet")
    if root["source_cluster_id"] != provenance["source_cluster_id"]:
        raise ScopePacketValidationError("gold.source_cluster_id does not match packet provenance")
    if root["source_document_id"] != provenance["document_id"] or root["source_document_sha256"] != provenance["document_sha256"]:
        raise ScopePacketValidationError("gold source document identity/hash does not match input packet")
    if root["model_input_sha256"] != _model_input_sha256(validated_packet["model_input"]):
        raise ScopePacketValidationError("gold model_input_sha256 does not match exact model-visible packet")
    if not isinstance(root["source_document_sha256"], str) or not _SHA256.fullmatch(root["source_document_sha256"]):
        raise ScopePacketValidationError("gold.source_document_sha256 must be lowercase SHA-256")

    nodes = root["nodes"]
    if not isinstance(nodes, list) or not 3 <= len(nodes) <= 500:
        raise ScopePacketValidationError("gold.nodes must contain 3..500 graph nodes")
    node_by_id: dict[str, dict[str, Any]] = {}
    for index, raw_node in enumerate(nodes):
        node = _require_object(raw_node, f"gold.nodes[{index}]")
        _require_exact_keys(node, {"node_id", "text", "node_type", "page_number", "figure_id"}, f"gold.nodes[{index}]")
        node_id = _require_string(node["node_id"], f"gold.nodes[{index}].node_id")
        if node_id in node_by_id:
            raise ScopePacketValidationError(f"duplicate gold node_id: {node_id}")
        node_text = _require_string(node["text"], f"gold.nodes[{index}].text")
        if len(node_text) > 12000:
            raise ScopePacketValidationError(f"gold.nodes[{index}].text exceeds 12000 characters")
        if not isinstance(node["node_type"], str) or node["node_type"] not in _NODE_TYPES:
            raise ScopePacketValidationError(f"unsupported node type: {node['node_type']}")
        if isinstance(node["page_number"], bool) or not isinstance(node["page_number"], int) or not 1 <= node["page_number"] <= provenance["page_count"]:
            raise ScopePacketValidationError(f"gold.nodes[{index}].page_number is outside source")
        _require_string(node["figure_id"], f"gold.nodes[{index}].figure_id")
        node_by_id[node_id] = node

    root_node_id = root["root_node_id"]
    if root_node_id not in node_by_id or node_by_id[root_node_id]["node_type"] != "top_event":
        raise ScopePacketValidationError("root_node_id must reference a top_event node")
    if sum(node["node_type"] == "top_event" for node in nodes) != 1:
        raise ScopePacketValidationError("a single-event Gold graph must have exactly one top_event")

    diagram_gates = root["diagram_gates"]
    reviews = root["text_gate_reviews"]
    if not isinstance(diagram_gates, list) or not 1 <= len(diagram_gates) <= 250 or not isinstance(reviews, list) or not 1 <= len(reviews) <= 250:
        raise ScopePacketValidationError("diagram_gates and text_gate_reviews must contain 1..250 entries")
    gates_by_scope: dict[str, dict[str, Any]] = {}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_by_id}
    for index, raw_gate in enumerate(diagram_gates):
        gate = _require_object(raw_gate, f"gold.diagram_gates[{index}]")
        _require_exact_keys(gate, {"scope_id", "output_node_id", "child_node_ids", "diagram_reference_gate", "page_number", "figure_id"}, f"gold.diagram_gates[{index}]")
        scope_id = _require_string(gate["scope_id"], f"gold.diagram_gates[{index}].scope_id")
        if scope_id in gates_by_scope:
            raise ScopePacketValidationError(f"duplicate gate scope_id: {scope_id}")
        output = gate["output_node_id"]
        children = gate["child_node_ids"]
        if not isinstance(output, str) or output not in node_by_id or not isinstance(children, list) or len(children) < 2:
            raise ScopePacketValidationError(f"invalid output/children for gate scope {scope_id}")
        if any(not isinstance(child, str) for child in children) or len(set(children)) != len(children):
            raise ScopePacketValidationError(f"gate scope {scope_id} children must be unique node IDs")
        if any(child not in node_by_id or child == output for child in children):
            raise ScopePacketValidationError(f"gate scope {scope_id} references invalid child")
        if not isinstance(gate["diagram_reference_gate"], str) or gate["diagram_reference_gate"] not in _DIAGRAM_GATE_KEYS:
            raise ScopePacketValidationError(f"unsupported diagram gate at scope {scope_id}")
        if isinstance(gate["page_number"], bool) or not isinstance(gate["page_number"], int) or not 1 <= gate["page_number"] <= provenance["page_count"]:
            raise ScopePacketValidationError(f"diagram gate page outside source at scope {scope_id}")
        _require_string(gate["figure_id"], f"gold.diagram_gates[{index}].figure_id")
        gates_by_scope[scope_id] = gate
        adjacency[output].extend(children)

    if not isinstance(reviews, list) or len(reviews) != len(gates_by_scope):
        raise ScopePacketValidationError("every diagram gate scope must have exactly one text-gate review")
    seen_review_scopes: set[str] = set()
    packet_segments = {segment["segment_id"]: segment for segment in validated_packet["model_input"]["source_segments"]}
    for index, raw_review in enumerate(reviews):
        review = _require_object(raw_review, f"gold.text_gate_reviews[{index}]")
        _require_exact_keys(review, {"scope_id", "text_authorized_gate", "unknown_reason", "evidence", "review_provenance"}, f"gold.text_gate_reviews[{index}]")
        scope_id = _require_string(review["scope_id"], f"gold.text_gate_reviews[{index}].scope_id")
        if scope_id not in gates_by_scope or scope_id in seen_review_scopes:
            raise ScopePacketValidationError(f"missing, unknown, or duplicate text review scope: {scope_id}")
        seen_review_scopes.add(scope_id)
        label = review["text_authorized_gate"]
        evidence_ref = review["evidence"]
        reason = review["unknown_reason"]
        if not isinstance(label, str) or label not in _GOLD_GATE_KEYS:
            raise ScopePacketValidationError(f"unsupported text_authorized_gate at scope {scope_id}")
        if label == "unknown":
            if not isinstance(reason, str) or reason not in _UNKNOWN_REASONS or evidence_ref is not None:
                raise ScopePacketValidationError(f"unknown gate requires a reason and no decisive gate evidence at scope {scope_id}")
        else:
            if reason is not None or not isinstance(evidence_ref, dict):
                raise ScopePacketValidationError(f"AND/OR text label requires direct evidence and no unknown_reason at scope {scope_id}")
            _require_exact_keys(evidence_ref, {"segment_id", "quote"}, f"text_gate_reviews[{index}].evidence")
            _require_string(evidence_ref["segment_id"], f"text_gate_reviews[{index}].evidence.segment_id")
            segment = packet_segments.get(evidence_ref["segment_id"])
            quote = _require_string(evidence_ref["quote"], f"text_gate_reviews[{index}].evidence.quote")
            if segment is None or segment["text"].count(quote) != 1:
                raise ScopePacketValidationError(f"decisive text-gate quote must be unique in model input at scope {scope_id}")

        provenance_item = _require_object(review["review_provenance"], f"text_gate_reviews[{index}].review_provenance")
        _require_exact_keys(provenance_item, {"reviewer_role", "reviewer_id", "review_status", "reviewed_at"}, f"text_gate_reviews[{index}].review_provenance")
        if not isinstance(provenance_item["reviewer_role"], str) or provenance_item["reviewer_role"] not in _REVIEWER_ROLES:
            raise ScopePacketValidationError(f"invalid reviewer role at scope {scope_id}")
        if not isinstance(provenance_item["review_status"], str) or provenance_item["review_status"] not in {"pending", "reviewed"}:
            raise ScopePacketValidationError(f"invalid review provenance at scope {scope_id}")
        reviewer_id = provenance_item["reviewer_id"]
        reviewed_at_value = provenance_item["reviewed_at"]
        if reviewer_id is not None and (not isinstance(reviewer_id, str) or not reviewer_id.strip()):
            raise ScopePacketValidationError(f"reviewer_id must be a non-empty string or null at scope {scope_id}")
        if reviewed_at_value is not None and not isinstance(reviewed_at_value, str):
            raise ScopePacketValidationError(f"reviewed_at must be a date string or null at scope {scope_id}")
        if provenance_item["review_status"] == "reviewed":
            if provenance_item["reviewer_role"] == "unreviewed":
                raise ScopePacketValidationError(f"reviewed status requires a reviewer role at scope {scope_id}")
            reviewed_at = _require_string(reviewed_at_value, f"text_gate_reviews[{index}].review_provenance.reviewed_at")
            try:
                parsed_date = date.fromisoformat(reviewed_at)
            except ValueError as exc:
                raise ScopePacketValidationError(f"invalid reviewed_at date at scope {scope_id}") from exc
            if parsed_date.isoformat() != reviewed_at:
                raise ScopePacketValidationError(f"reviewed_at must use YYYY-MM-DD at scope {scope_id}")
        elif provenance_item["reviewed_at"] is not None:
            raise ScopePacketValidationError(f"pending review cannot have reviewed_at at scope {scope_id}")

    reachable: set[str] = set()
    visiting: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ScopePacketValidationError("reference graph contains a cycle")
        if node_id in reachable:
            return
        visiting.add(node_id)
        for child in adjacency[node_id]:
            visit(child)
        visiting.remove(node_id)
        reachable.add(node_id)

    visit(root_node_id)
    if reachable != set(node_by_id):
        raise ScopePacketValidationError("reference graph contains nodes disconnected from the single top event")
    return root


__all__ = ["ScopePacketValidationError", "model_input_payload", "validate_input_packet", "validate_reference_gold"]
