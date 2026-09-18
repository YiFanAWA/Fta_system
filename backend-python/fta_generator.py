from fta_tree_contract import (
    attach_source_record_ids,
    merge_source_record_ids,
    normalize_source_record_ids,
    validate_fault_tree,
)


def _to_probability(value):
    if value is None:
        return None

    try:
        prob = float(value)
    except (TypeError, ValueError):
        return None

    if prob < 0:
        return 0.0

    if prob > 1:
        return 1.0

    return prob


def _build_basic_node(name, probability=None, source_record_ids=None):
    return attach_source_record_ids(
        {
            "name": name,
            "type": "basic",
            "probability": _to_probability(probability),
        },
        source_record_ids,
    )


def _build_intermediate_node(item):
    if isinstance(item, str):
        name = item.strip()
        if not name:
            return None
        return _build_basic_node(name)

    if not isinstance(item, dict):
        return None

    raw_name = item.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return None

    name = raw_name.strip()
    probability = _to_probability(item.get("probability"))
    source_record_ids = normalize_source_record_ids(item.get("source_record_ids"))
    if not source_record_ids and item.get("record_id") is not None:
        source_record_ids = normalize_source_record_ids(item.get("record_id"))

    causes_raw = item.get("causes", [])
    if not isinstance(causes_raw, list):
        causes_raw = []

    children = []
    seen = {}
    for cause in causes_raw:
        child = _build_intermediate_node(cause)
        if not child:
            continue
        child_name = child["name"]
        if child_name in seen:
            merge_source_record_ids(seen[child_name], child)
            continue
        seen[child_name] = child
        children.append(child)

    if not children:
        return _build_basic_node(name, probability, source_record_ids)

    gate = item.get("gate", "OR")
    if not isinstance(gate, str) or gate.upper() not in {"AND", "OR"}:
        gate = "OR"

    return attach_source_record_ids(
        {
            "name": name,
            "type": "intermediate",
            "probability": probability,
            "gate": gate.upper(),
            "children": children,
        },
        source_record_ids,
    )

def build_fault_tree(top_event, failures):
    if not isinstance(top_event, str) or not top_event.strip():
        raise ValueError("top_event不能为空")

    if not isinstance(failures, list):
        raise ValueError("failures必须是列表")

    children = []
    seen = {}

    for item in failures:
        node = _build_intermediate_node(item)
        if not node:
            continue

        name = node["name"]
        if name in seen:
            merge_source_record_ids(seen[name], node)
            continue

        seen[name] = node
        children.append(node)

    if not children:
        raise ValueError("没有可用于构建故障树的事件")

    tree = {
        "top": top_event.strip(),
        "gate": "OR",
        "children": children
    }

    return validate_fault_tree(tree)
