from lxml import etree


def _is_valid_gate(gate):
    return isinstance(gate, str) and gate.upper() in {"OR", "AND"}


def _as_probability_text(probability):
    if probability is None:
        return None

    try:
        p = float(probability)
    except (TypeError, ValueError):
        return None

    if p < 0:
        p = 0.0
    if p > 1:
        p = 1.0

    return f"{p:.6f}".rstrip("0").rstrip(".")


def _write_node(parent, node):
    name = node.get("name")
    if not isinstance(name, str) or not name.strip():
        return

    event = etree.SubElement(parent, "event")
    event.set("name", name.strip())

    probability_text = _as_probability_text(node.get("probability"))
    if probability_text is not None:
        event.set("probability", probability_text)

    children = node.get("children", []) if isinstance(node, dict) else []
    if isinstance(children, list) and children:
        event.set("type", "intermediate")
        gate_type = node.get("gate", "OR")
        if not _is_valid_gate(gate_type):
            gate_type = "OR"
        gate = etree.SubElement(event, "gate")
        gate.set("type", gate_type.upper())

        for child in children:
            if isinstance(child, dict):
                _write_node(gate, child)
    else:
        event.set("type", "basic")


def export_xml(tree, filename="fault_tree.xml"):
    if not isinstance(tree, dict):
        raise ValueError("tree必须是字典")

    top_name = tree.get("top")
    gate_type = tree.get("gate", "OR")
    children = tree.get("children", [])

    if not isinstance(top_name, str) or not top_name.strip():
        raise ValueError("tree.top不能为空")

    if not _is_valid_gate(gate_type):
        raise ValueError("tree.gate仅支持AND/OR")

    if not isinstance(children, list) or not children:
        raise ValueError("tree.children必须是非空列表")

    clean_children = []
    seen = set()
    for item in children:
        if isinstance(item, str) and item.strip():
            clean_children.append({"name": item.strip(), "type": "basic"})
            continue
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or name.strip() in seen:
            continue

        seen.add(name.strip())
        clean_children.append(item)

    if not clean_children:
        raise ValueError("tree.children中没有有效事件")

    root = etree.Element("faulttree")

    top = etree.SubElement(root, "event")
    top.set("name", top_name.strip())
    top.set("type", "top")

    gate = etree.SubElement(top, "gate")
    gate.set("type", gate_type.upper())

    for node in clean_children:
        _write_node(gate, node)

    xml = etree.ElementTree(root)

    try:
        xml.write(
            filename,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8"
        )
    except Exception as exc:
        raise RuntimeError(f"写入XML失败: {exc}") from exc