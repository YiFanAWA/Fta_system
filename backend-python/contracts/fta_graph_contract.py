"""Evidence-bound contract for restricted FTA graph previews."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ALLOWED_GATES = {"AND", "OR"}
ALLOWED_DIRECTIONS = {"source_to_target"}
ALLOWED_RELATIONS = {"causes"}


def validate_fta_preview(payload: Any) -> list[str]:
    """Return contract violations for an evidence-bound FTA preview.

    The contract deliberately validates a preview projection, not a complete
    production tree registry. ``preview_only`` and the production readiness
    guards prevent a partial expert Gold from being consumed as a full FTA.
    """

    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["FTA preview must be an object"]

    info = payload.get("dataset_info")
    if not isinstance(info, Mapping):
        errors.append("dataset_info must be an object")
        info = {}
    if info.get("status") != "preview_only":
        errors.append("dataset_info.status must be preview_only")
    if info.get("production_ready") is not False:
        errors.append("dataset_info.production_ready must be false")
    if info.get("fta_ready") is not False:
        errors.append("dataset_info.fta_ready must be false")
    if info.get("automatic_causal_inference") is not False:
        errors.append("dataset_info.automatic_causal_inference must be false")
    if info.get("evidence_required") is not True:
        errors.append("dataset_info.evidence_required must be true")

    trees = payload.get("trees")
    if not isinstance(trees, list):
        errors.append("trees must be a list")
        trees = []
    if info.get("tree_count") != len(trees):
        errors.append("dataset_info.tree_count does not match trees length")

    tree_ids: set[str] = set()
    for tree_index, tree in enumerate(trees):
        path = f"trees[{tree_index}]"
        if not isinstance(tree, Mapping):
            errors.append(f"{path} must be an object")
            continue
        tree_id = tree.get("preview_tree_id")
        if not isinstance(tree_id, str) or not tree_id.strip():
            errors.append(f"{path}.preview_tree_id must be non-empty")
            tree_id = f"<tree-{tree_index}>"
        elif tree_id in tree_ids:
            errors.append(f"{path}.preview_tree_id must be unique")
        else:
            tree_ids.add(tree_id)

        if tree.get("status") != "preview_only":
            errors.append(f"{path}.status must be preview_only")
        top = tree.get("top_event")
        if not isinstance(top, Mapping):
            errors.append(f"{path}.top_event must be an object")
        else:
            for key in ("fault_code", "description"):
                if not isinstance(top.get(key), str) or not top[key].strip():
                    errors.append(f"{path}.top_event.{key} must be non-empty")

        if tree.get("gate") not in ALLOWED_GATES:
            errors.append(f"{path}.gate must be AND or OR")
        provenance = tree.get("gate_provenance")
        if not isinstance(provenance, Mapping):
            errors.append(f"{path}.gate_provenance must be an object")
        else:
            if provenance.get("review_status") != "expert_reviewed":
                errors.append(f"{path}.gate_provenance.review_status must be expert_reviewed")
            if provenance.get("evidence_support") != "supported":
                errors.append(f"{path}.gate_provenance.evidence_support must be supported")

        children = tree.get("children")
        if not isinstance(children, list) or not children:
            errors.append(f"{path}.children must be a non-empty list")
            continue
        relation_ids: set[str] = set()
        node_ids: set[str] = set()
        for child_index, child in enumerate(children):
            child_path = f"{path}.children[{child_index}]"
            if not isinstance(child, Mapping):
                errors.append(f"{child_path} must be an object")
                continue
            relation_id = child.get("relation_id")
            if not isinstance(relation_id, str) or not relation_id.strip():
                errors.append(f"{child_path}.relation_id must be non-empty")
            elif relation_id in relation_ids:
                errors.append(f"{child_path}.relation_id must be unique within a tree")
            else:
                relation_ids.add(relation_id)
            node = child.get("node")
            if not isinstance(node, Mapping):
                errors.append(f"{child_path}.node must be an object")
            else:
                node_id = node.get("node_id")
                if not isinstance(node_id, str) or not node_id.strip():
                    errors.append(f"{child_path}.node.node_id must be non-empty")
                elif node_id in node_ids:
                    errors.append(f"{child_path}.node.node_id must be unique within a tree")
                else:
                    node_ids.add(node_id)
                if not isinstance(node.get("text"), str) or not node["text"].strip():
                    errors.append(f"{child_path}.node.text must be non-empty")
            if child.get("relation_type") not in ALLOWED_RELATIONS:
                errors.append(f"{child_path}.relation_type must be causes")
            if child.get("direction") not in ALLOWED_DIRECTIONS:
                errors.append(f"{child_path}.direction must be source_to_target")
            evidence = child.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{child_path}.evidence must be non-empty")
                continue
            citation_ids: set[str] = set()
            for evidence_index, citation in enumerate(evidence):
                evidence_path = f"{child_path}.evidence[{evidence_index}]"
                if not isinstance(citation, Mapping):
                    errors.append(f"{evidence_path} must be an object")
                    continue
                citation_id = citation.get("citation_id")
                if not isinstance(citation_id, str) or not citation_id.strip():
                    errors.append(f"{evidence_path}.citation_id must be non-empty")
                elif citation_id in citation_ids:
                    errors.append(f"{evidence_path}.citation_id must be unique within a child")
                else:
                    citation_ids.add(citation_id)
                for key in ("source_id", "quote"):
                    if not isinstance(citation.get(key), str) or not citation[key].strip():
                        errors.append(f"{evidence_path}.{key} must be non-empty")

    excluded = payload.get("excluded_events")
    if not isinstance(excluded, list):
        errors.append("excluded_events must be a list")
        excluded = []
    if info.get("excluded_event_count") != len(excluded):
        errors.append("dataset_info.excluded_event_count does not match excluded_events length")
    return errors


__all__ = ["validate_fta_preview"]
