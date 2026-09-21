import shutil
import subprocess


def _format_event_label(name, probability=None):
    if probability is None:
        return name

    try:
        p = float(probability)
    except (TypeError, ValueError):
        return name

    if p < 0:
        p = 0.0
    if p > 1:
        p = 1.0

    return f"{name}\nP={p:.3f}"


def _append_node(lines, node, parent_id, counter):
    event_id = f"e{counter[0]}"
    counter[0] += 1

    name = node.get("name", "Unnamed")
    probability = node.get("probability")
    node_type = node.get("type", "basic")

    label = _format_event_label(name, probability)
    shape = "ellipse" if node_type == "basic" else "box"

    lines.append(f'  {event_id} [label="{label}", shape={shape}];')
    lines.append(f"  {parent_id} -> {event_id};")

    children = node.get("children", [])
    if not isinstance(children, list) or not children:
        return

    # Single-child branch does not need a logic gate in FTA visualization.
    if len(children) == 1:
        child = children[0]
        if isinstance(child, dict):
            _append_node(lines, child, event_id, counter)
        return

    gate = node.get("gate", "OR")
    if not isinstance(gate, str) or gate.upper() not in {"AND", "OR"}:
        gate = "OR"

    gate_id = f"g{counter[0]}"
    counter[0] += 1

    lines.append(
        f'  {gate_id} [label="{gate.upper()}", shape=diamond, width=0.5, height=0.5, fixedsize=true];'
    )
    lines.append(f"  {event_id} -> {gate_id};")

    for child in children:
        if isinstance(child, dict):
            _append_node(lines, child, gate_id, counter)


def export_dot(tree, filename="fault_tree.dot"):
    if not isinstance(tree, dict):
        raise ValueError("tree必须是字典")

    top_name = tree.get("top")
    if not isinstance(top_name, str) or not top_name.strip():
        raise ValueError("tree.top不能为空")

    top_gate = tree.get("gate", "OR")
    if not isinstance(top_gate, str) or top_gate.upper() not in {"AND", "OR"}:
        top_gate = "OR"

    children = tree.get("children", [])
    if not isinstance(children, list) or not children:
        raise ValueError("tree.children必须是非空列表")

    lines = [
        "digraph FTA {",
        "  rankdir=TB;",
        "  graph [fontname=Helvetica];",
        "  node [fontname=Helvetica];",
        "  edge [fontname=Helvetica];",
        f'  top [label="{top_name.strip()}", shape=doubleoctagon, style=filled, fillcolor=lightcoral];',
    ]

    counter = [1]
    if len(children) == 1 and isinstance(children[0], dict):
        _append_node(lines, children[0], "top", counter)
    else:
        lines.extend([
            f'  top_gate [label="{top_gate.upper()}", shape=diamond, width=0.5, height=0.5, fixedsize=true];',
            "  top -> top_gate;",
        ])
        for child in children:
            if isinstance(child, dict):
                _append_node(lines, child, "top_gate", counter)

    lines.append("}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename


def export_png_from_dot(dot_file="fault_tree.dot", png_file="fault_tree.png"):
    if not shutil.which("dot"):
        return None

    subprocess.run(
        ["dot", "-Tpng", dot_file, "-o", png_file],
        check=True,
        capture_output=True,
        text=True
    )

    return png_file


def export_visuals(tree, dot_file="fault_tree.dot", png_file="fault_tree.png"):
    dot_path = export_dot(tree, dot_file)
    png_path = export_png_from_dot(dot_path, png_file)
    return {"dot": dot_path, "png": png_path}
