"""Evaluation-only structural contract for single-event scope-tree outputs.

Gate scopes are the sole source of hierarchy. A legacy ``parent_id`` field is
accepted only as a checked projection; this validator never rewrites output.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


_NODE_TYPES = {"top_event", "intermediate_event", "basic_event", "undeveloped_event"}
_GATES = {"AND", "OR", "unknown"}


def validate_event_scope_tree(output: Any) -> dict[str, Any]:
    """Validate a model tree without normalizing, repairing, or discarding it."""
    blockers: list[dict[str, Any]] = []

    def block(code: str, **details: Any) -> None:
        blockers.append({"code": code, **details})

    if not isinstance(output, dict):
        return {"valid": False, "blockers": [{"code": "output_must_be_object"}], "derived_parent_ids": {}}

    nodes = output.get("nodes")
    gates = output.get("gates")
    if not isinstance(nodes, list) or not isinstance(gates, list):
        return {"valid": False, "blockers": [{"code": "nodes_and_gates_must_be_arrays"}], "derived_parent_ids": {}}
    structure_status = output.get("structure_status")
    if not isinstance(structure_status, str) or structure_status not in {"complete", "unresolved"}:
        block("unsupported_structure_status", structure_status=structure_status)

    node_by_id: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            block("node_must_be_object", index=index)
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            block("node_id_required", index=index)
            continue
        if node_id in node_by_id:
            block("duplicate_node_id", node_id=node_id)
            continue
        node_by_id[node_id] = node
        node_type = node.get("type")
        if not isinstance(node_type, str) or node_type not in _NODE_TYPES:
            block("unsupported_node_type", node_id=node_id, node_type=node.get("type"))

    top_ids = [node_id for node_id, node in node_by_id.items() if node.get("type") == "top_event"]
    if len(top_ids) != 1:
        block("exactly_one_top_event_required", top_event_ids=top_ids)
    root_id = top_ids[0] if len(top_ids) == 1 else None

    gate_ids: set[str] = set()
    output_scope_by_node: dict[str, str] = {}
    parents_by_child: dict[str, set[str]] = defaultdict(set)
    edges: dict[str, set[str]] = defaultdict(set)
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            block("gate_scope_must_be_object", index=index)
            continue
        scope_id = gate.get("scope_id")
        if not isinstance(scope_id, str) or not scope_id.strip():
            block("gate_scope_id_required", index=index)
        elif scope_id in gate_ids:
            block("duplicate_gate_scope_id", scope_id=scope_id)
        else:
            gate_ids.add(scope_id)

        output_id = gate.get("output_node_id")
        child_ids = gate.get("child_node_ids")
        output_id_is_valid = isinstance(output_id, str) and output_id in node_by_id
        if not isinstance(output_id, str) or not output_id.strip():
            block("gate_output_node_id_required", scope_id=scope_id)
        elif not output_id_is_valid:
            block("gate_output_node_unknown", scope_id=scope_id, output_node_id=output_id)
        else:
            previous_scope = output_scope_by_node.get(output_id)
            if previous_scope is not None:
                block(
                    "node_has_multiple_output_scopes",
                    node_id=output_id,
                    scope_ids=[previous_scope, scope_id],
                )
            else:
                output_scope_by_node[output_id] = scope_id
        gate_label = gate.get("gate")
        if not isinstance(gate_label, str) or gate_label not in _GATES:
            block("unsupported_gate_label", scope_id=scope_id, gate=gate.get("gate"))
        if not isinstance(child_ids, list):
            block("gate_children_must_be_array", scope_id=scope_id)
            continue
        if len(child_ids) < 2:
            block("gate_scope_requires_at_least_two_children", scope_id=scope_id, child_count=len(child_ids))
        valid_child_ids = [child_id for child_id in child_ids if isinstance(child_id, str)]
        if len(valid_child_ids) != len(child_ids):
            block("gate_child_node_id_must_be_string", scope_id=scope_id)
        if len(set(valid_child_ids)) != len(valid_child_ids):
            block("duplicate_child_in_gate_scope", scope_id=scope_id)
        for child_id in child_ids:
            if not isinstance(child_id, str):
                continue
            if child_id not in node_by_id:
                block("gate_child_node_unknown", scope_id=scope_id, child_node_id=child_id)
                continue
            if child_id == output_id:
                block("gate_output_cannot_be_own_child", scope_id=scope_id, node_id=child_id)
                continue
            if output_id_is_valid:
                parents_by_child[child_id].add(output_id)
                edges[output_id].add(child_id)

    for node_id, parent_ids in sorted(parents_by_child.items()):
        if len(parent_ids) > 1:
            block("node_has_multiple_parent_scopes", node_id=node_id, parent_node_ids=sorted(parent_ids))

    derived_parent_ids: dict[str, str | None] = {
        node_id: next(iter(parents_by_child[node_id])) if len(parents_by_child[node_id]) == 1 else None
        for node_id in node_by_id
    }
    if root_id is not None and parents_by_child.get(root_id):
        block("top_event_cannot_have_parent_scope", node_id=root_id, parent_node_ids=sorted(parents_by_child[root_id]))
    for node_id in sorted(node_by_id):
        if node_id != root_id and len(parents_by_child.get(node_id, set())) == 0:
            block("non_root_node_missing_parent_scope", node_id=node_id)

    # Legacy parent_id is never authoritative: if present, compare it to the
    # unique parent derived from gate scopes and report disagreement unchanged.
    for node_id, node in node_by_id.items():
        if "parent_id" not in node:
            continue
        expected = derived_parent_ids[node_id]
        if node.get("parent_id") != expected or len(parents_by_child.get(node_id, set())) > 1:
            block(
                "parent_id_conflicts_with_gate_scope",
                node_id=node_id,
                declared_parent_id=node.get("parent_id"),
                gate_scope_parent_node_ids=sorted(parents_by_child.get(node_id, set())),
            )

    if root_id is not None:
        reachable: set[str] = set()
        queue = deque([root_id])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(sorted(edges.get(current, set()) - reachable))
        for node_id in sorted(set(node_by_id) - reachable):
            block("node_not_reachable_from_top_event", node_id=node_id, top_event_id=root_id)

    # A valid hierarchy is a rooted tree, not merely a set of reachable links.
    # Kahn's algorithm detects cycles without recursion-depth assumptions.
    indegree = {node_id: 0 for node_id in node_by_id}
    for child_ids in edges.values():
        for child_id in child_ids:
            indegree[child_id] += 1
    acyclic_queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited_count = 0
    while acyclic_queue:
        current = acyclic_queue.popleft()
        visited_count += 1
        for child_id in sorted(edges.get(current, set())):
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                acyclic_queue.append(child_id)
    if visited_count != len(node_by_id):
        block("gate_scope_hierarchy_contains_cycle", node_ids=sorted(node_id for node_id, degree in indegree.items() if degree > 0))
    if structure_status == "complete" and blockers:
        block("complete_structure_status_has_blockers")

    return {
        "valid": not blockers,
        "blockers": blockers,
        "root_node_id": root_id,
        "derived_parent_ids": derived_parent_ids,
        "hierarchy_owner": "gate_scopes",
        "output_mutated": False,
    }
