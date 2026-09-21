"""Shared contract and validation for JSON fault-tree values."""

from typing import Any


def normalize_source_record_ids(value: Any) -> list[str]:
    """Normalize optional provenance IDs without inventing identifiers."""
    if value is None:
        return []
    raw_values = [value] if isinstance(value, str) else value
    if not isinstance(raw_values, (list, tuple)):
        return []

    source_record_ids: list[str] = []
    seen: set[str] = set()
    for source_record_id in raw_values:
        if not isinstance(source_record_id, str):
            continue
        source_record_id = source_record_id.strip()
        if not source_record_id or source_record_id in seen:
            continue
        seen.add(source_record_id)
        source_record_ids.append(source_record_id)
    return source_record_ids


def attach_source_record_ids(
    node: dict[str, Any],
    source_record_ids: Any,
) -> dict[str, Any]:
    normalized = normalize_source_record_ids(source_record_ids)
    if normalized:
        node["source_record_ids"] = normalized
    return node


def merge_source_record_ids(
    target: dict[str, Any],
    source: dict[str, Any],
) -> None:
    """Merge provenance when two equal event names share one tree node."""
    merged = normalize_source_record_ids(target.get("source_record_ids"))
    for source_record_id in normalize_source_record_ids(
        source.get("source_record_ids")
    ):
        if source_record_id not in merged:
            merged.append(source_record_id)
    if merged:
        target["source_record_ids"] = merged


def validate_fault_tree(tree: Any) -> dict[str, Any]:
    """Validate the JSON tree contract before persistence or export."""
    if not isinstance(tree, dict):
        raise ValueError("tree必须是字典")

    top = tree.get("top")
    if not isinstance(top, str) or not top.strip():
        raise ValueError("tree.top不能为空")

    gate = tree.get("gate", "OR")
    if not isinstance(gate, str) or gate.upper() not in {"AND", "OR"}:
        raise ValueError("tree.gate仅支持AND/OR")

    children = tree.get("children")
    if not isinstance(children, list) or not children:
        raise ValueError("tree.children必须是非空列表")

    def validate_node(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            raise ValueError(f"{path}必须是对象")

        name = node.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{path}.name不能为空")

        source_record_ids = node.get("source_record_ids")
        if source_record_ids is not None:
            if not isinstance(source_record_ids, list):
                raise ValueError(f"{path}.source_record_ids必须是列表")
            normalized = normalize_source_record_ids(source_record_ids)
            if not normalized or len(normalized) != len(source_record_ids):
                raise ValueError(
                    f"{path}.source_record_ids必须是非空字符串列表"
                )

        node_children = node.get("children", [])
        if not isinstance(node_children, list):
            raise ValueError(f"{path}.children必须是列表")
        if not node_children:
            return

        node_gate = node.get("gate", "OR")
        if not isinstance(node_gate, str) or node_gate.upper() not in {"AND", "OR"}:
            raise ValueError(f"{path}.gate仅支持AND/OR")
        for index, child in enumerate(node_children):
            validate_node(child, f"{path}.children[{index}]")

    for index, child in enumerate(children):
        validate_node(child, f"tree.children[{index}]")

    tree["top"] = top.strip()
    tree["gate"] = gate.upper()
    return tree
