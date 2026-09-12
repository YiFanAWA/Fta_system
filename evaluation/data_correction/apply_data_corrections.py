import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _canonical_key(text: str) -> str:
    s = _safe_text(text)
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def _dedup_keep_order(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        key = _canonical_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _normalize_param(p: str) -> str:
    return _safe_text(p).lower()


def _load_payload(input_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload, [r for r in payload.get("records", []) if isinstance(r, dict)]

    if isinstance(payload, list):
        return {"records": payload}, [r for r in payload if isinstance(r, dict)]

    raise ValueError("input must be either {'records': [...]} or a list of records")


def _load_rules(rules_path: Path) -> Dict[str, Any]:
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("rules file must be a JSON object")
    return data


def _apply_global_field_map(value: str, mapping: Dict[str, str]) -> str:
    if not mapping:
        return value
    key = _canonical_key(value)
    if key in mapping:
        return mapping[key]
    return value


def _apply_list_replacements(items: List[str], mapping: Dict[str, str]) -> List[str]:
    if not mapping:
        return items
    out = []
    for item in items:
        key = _canonical_key(item)
        out.append(mapping.get(key, item))
    return out


def _compile_regex_rules(rules: Any) -> List[Tuple[re.Pattern, str]]:
    out: List[Tuple[re.Pattern, str]] = []
    if not isinstance(rules, list):
        return out

    for item in rules:
        if not isinstance(item, dict):
            continue
        pattern = str(item.get("pattern") or "").strip()
        replace = str(item.get("replace") or "")
        if not pattern:
            continue
        try:
            out.append((re.compile(pattern), replace))
        except re.error:
            continue
    return out


def _apply_regex_text(value: str, compiled_rules: List[Tuple[re.Pattern, str]]) -> str:
    text = value
    for pattern, replace in compiled_rules:
        text = pattern.sub(replace, text)
    return _safe_text(text)


def _apply_regex_list(items: List[str], compiled_rules: List[Tuple[re.Pattern, str]]) -> List[str]:
    if not compiled_rules:
        return items
    out: List[str] = []
    for item in items:
        v = _apply_regex_text(item, compiled_rules)
        if v:
            out.append(v)
    return out


def _compile_drop_regex_list(patterns: Any) -> List[re.Pattern]:
    out: List[re.Pattern] = []
    if not isinstance(patterns, list):
        return out
    for p in patterns:
        text = str(p or "").strip()
        if not text:
            continue
        try:
            out.append(re.compile(text))
        except re.error:
            continue
    return out


def _drop_by_regex(items: List[str], drop_patterns: List[re.Pattern]) -> List[str]:
    if not drop_patterns:
        return items
    out: List[str] = []
    for item in items:
        if any(p.search(item) for p in drop_patterns):
            continue
        out.append(item)
    return out


def _remove_items(items: List[str], remove_list: List[str]) -> List[str]:
    if not remove_list:
        return items
    to_remove = {_canonical_key(x) for x in remove_list if _canonical_key(x)}
    return [x for x in items if _canonical_key(x) not in to_remove]


def _build_global_mappings(rules: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    global_replacements = rules.get("global_replacements", {})
    if not isinstance(global_replacements, dict):
        global_replacements = {}

    def _norm_map(obj: Any) -> Dict[str, str]:
        if not isinstance(obj, dict):
            return {}
        out: Dict[str, str] = {}
        for old, new in obj.items():
            old_key = _canonical_key(str(old))
            if old_key:
                out[old_key] = str(new).strip()
        return out

    return {
        "component": _norm_map(global_replacements.get("component")),
        "description": _norm_map(global_replacements.get("description")),
        "causes": _norm_map(global_replacements.get("causes")),
        "parameters": _norm_map(global_replacements.get("parameters")),
    }


def _record_override_for(code: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    overrides = rules.get("record_overrides", {})
    if not isinstance(overrides, dict):
        return {}

    direct = overrides.get(code)
    if isinstance(direct, dict):
        return direct

    upper_key = code.upper()
    upper = overrides.get(upper_key)
    if isinstance(upper, dict):
        return upper

    return {}


def apply_corrections(records: List[Dict[str, Any]], rules: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    drop_codes = {str(x).upper() for x in rules.get("drop_fault_codes", []) if str(x).strip()}

    merge_map_raw = rules.get("merge_fault_codes", {})
    merge_map: Dict[str, str] = {}
    if isinstance(merge_map_raw, dict):
        for old, new in merge_map_raw.items():
            old_u = str(old).upper().strip()
            new_u = str(new).upper().strip()
            if old_u and new_u:
                merge_map[old_u] = new_u

    global_map = _build_global_mappings(rules)

    regex_replacements = rules.get("regex_replacements", {})
    if not isinstance(regex_replacements, dict):
        regex_replacements = {}

    desc_regex = _compile_regex_rules(regex_replacements.get("description"))
    cause_regex = _compile_regex_rules(regex_replacements.get("causes"))
    param_regex = _compile_regex_rules(regex_replacements.get("parameters"))

    global_drop = rules.get("global_drop", {})
    if not isinstance(global_drop, dict):
        global_drop = {}
    cause_drop_regex = _compile_drop_regex_list(global_drop.get("causes_regex"))
    param_drop_regex = _compile_drop_regex_list(global_drop.get("parameters_regex"))

    corrected: Dict[str, Dict[str, Any]] = {}
    stats = {
        "input_records": len(records),
        "dropped_records": 0,
        "changed_records": 0,
        "merged_records": 0,
    }

    for item in records:
        code = _safe_text(item.get("fault_code")).upper()
        if not code:
            continue

        code = merge_map.get(code, code)
        if code in drop_codes:
            stats["dropped_records"] += 1
            continue

        component = _safe_text(item.get("component"))
        description = _safe_text(item.get("description"))

        causes_raw = item.get("causes", []) if isinstance(item.get("causes"), list) else []
        parameters_raw = item.get("parameters", []) if isinstance(item.get("parameters"), list) else []

        causes = [_safe_text(c) for c in causes_raw if _safe_text(c)]
        parameters = [_normalize_param(p) for p in parameters_raw if _normalize_param(p)]

        component = _apply_global_field_map(component, global_map["component"])
        description = _apply_global_field_map(description, global_map["description"])
        causes = _apply_list_replacements(causes, global_map["causes"])
        parameters = _apply_list_replacements(parameters, global_map["parameters"])

        description = _apply_regex_text(description, desc_regex)
        causes = _apply_regex_list(causes, cause_regex)
        parameters = _apply_regex_list(parameters, param_regex)

        causes = _drop_by_regex(causes, cause_drop_regex)
        parameters = _drop_by_regex(parameters, param_drop_regex)

        override = _record_override_for(code, rules)
        if override:
            if isinstance(override.get("component"), str) and override.get("component").strip():
                component = override.get("component").strip()
            if isinstance(override.get("description"), str) and override.get("description").strip():
                description = override.get("description").strip()

            causes = _remove_items(causes, override.get("remove_causes", []))
            parameters = _remove_items(parameters, override.get("remove_parameters", []))

            add_causes = override.get("add_causes", []) if isinstance(override.get("add_causes"), list) else []
            add_params = override.get("add_parameters", []) if isinstance(override.get("add_parameters"), list) else []
            causes.extend([_safe_text(c) for c in add_causes if _safe_text(c)])
            parameters.extend([_normalize_param(p) for p in add_params if _normalize_param(p)])

            if isinstance(override.get("set_causes"), list):
                causes = [_safe_text(c) for c in override.get("set_causes", []) if _safe_text(c)]
            if isinstance(override.get("set_parameters"), list):
                parameters = [_normalize_param(p) for p in override.get("set_parameters", []) if _normalize_param(p)]

        causes = _apply_regex_list(causes, cause_regex)
        parameters = _apply_regex_list(parameters, param_regex)
        causes = _drop_by_regex(causes, cause_drop_regex)
        parameters = _drop_by_regex(parameters, param_drop_regex)

        causes = _dedup_keep_order(causes)
        parameters = _dedup_keep_order(parameters)

        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        current = {
            "fault_code": code,
            "component": component,
            "description": description,
            "causes": causes,
            "parameters": parameters,
            "updated_at": now_iso,
        }

        prev = corrected.get(code)
        if prev is None:
            corrected[code] = current
            continue

        # Merge repeated records with same code.
        stats["merged_records"] += 1
        prev["component"] = prev["component"] or current["component"]
        if len(current["description"]) > len(prev["description"]):
            prev["description"] = current["description"]
        prev["causes"] = _dedup_keep_order(prev["causes"] + current["causes"])
        prev["parameters"] = _dedup_keep_order(prev["parameters"] + current["parameters"])
        prev["updated_at"] = now_iso

    corrected_records = sorted(corrected.values(), key=lambda x: x["fault_code"])

    stats["output_records"] = len(corrected_records)
    stats["changed_records"] = stats["output_records"]
    return corrected_records, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply correction rules to extracted/cleaned FTA records")
    parser.add_argument("--input", required=True, help="Path to input json (records list or {'records': [...]})")
    parser.add_argument("--rules", required=True, help="Path to correction rules json")
    parser.add_argument("--output", required=True, help="Path to corrected output json")
    parser.add_argument("--report", required=False, help="Optional path to report json")
    args = parser.parse_args()

    input_path = Path(args.input)
    rules_path = Path(args.rules)
    output_path = Path(args.output)
    report_path = Path(args.report) if args.report else None

    payload, records = _load_payload(input_path)
    rules = _load_rules(rules_path)

    corrected_records, stats = apply_corrections(records, rules)

    out_payload = dict(payload)
    out_payload["records"] = corrected_records
    out_payload["record_count"] = len(corrected_records)
    out_payload["correction"] = {
        "rules_file": str(rules_path),
        "applied_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stats": stats,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if report_path:
        report = {
            "input": str(input_path),
            "output": str(output_path),
            "rules": str(rules_path),
            "stats": stats,
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"input_records={stats['input_records']}")
    print(f"output_records={stats['output_records']}")
    print(f"dropped_records={stats['dropped_records']}")
    print(f"merged_records={stats['merged_records']}")
    print(f"output={output_path}")


if __name__ == "__main__":
    main()
