import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


NOISE_CAUSE_RE = re.compile(
    r'^(?:[:：%\s].*|.*bin["\'”’)]?.*|检查.*|重新.*|请.*|见.*)$',
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _canonical_key(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def _is_noise_cause(text: str) -> bool:
    name = _safe_text(text)
    if len(name) < 2:
        return True
    if NOISE_CAUSE_RE.match(name):
        return True
    if not TOKEN_RE.search(name):
        return True
    return False


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
    name = _safe_text(p)
    return name.lower() if name else ""


def normalize_records(records: List[Dict[str, Any]], source_name: str, version: str) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for item in records:
        if not isinstance(item, dict):
            continue

        code = _safe_text(item.get("fault_code")).upper()
        desc = _safe_text(item.get("description"))
        if not code or not desc:
            continue

        comp = _safe_text(item.get("component")) or "未知组件"

        causes_raw = item.get("causes", []) if isinstance(item.get("causes"), list) else []
        causes = [_safe_text(c) for c in causes_raw if isinstance(c, str)]
        causes = [c for c in causes if not _is_noise_cause(c)]
        causes = _dedup_keep_order(causes)

        params_raw = item.get("parameters", []) if isinstance(item.get("parameters"), list) else []
        params = [_normalize_param(p) for p in params_raw if isinstance(p, str)]
        params = _dedup_keep_order([p for p in params if p])

        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        if code not in merged:
            merged[code] = {
                "fault_code": code,
                "component": comp,
                "description": desc,
                "causes": causes,
                "parameters": params,
                "source": source_name,
                "version": version,
                "updated_at": now_iso,
            }
            continue

        target = merged[code]
        if target.get("component") == "未知组件" and comp != "未知组件":
            target["component"] = comp
        if len(desc) > len(target.get("description", "")):
            target["description"] = desc

        target["causes"] = _dedup_keep_order(target.get("causes", []) + causes)
        target["parameters"] = _dedup_keep_order(target.get("parameters", []) + params)

    return sorted(merged.values(), key=lambda x: x["fault_code"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean extracted FTA records into KB-ready JSON")
    parser.add_argument("--input", required=True, help="Path to *_extracted_faults.json")
    parser.add_argument("--output", required=True, help="Path to output cleaned JSON")
    parser.add_argument("--version", default=datetime.now().strftime("%Y-%m-%d"), help="KB version label")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    raw_records = payload.get("records", []) if isinstance(payload, dict) else []
    if not isinstance(raw_records, list):
        raw_records = []

    cleaned = normalize_records(raw_records, in_path.name, args.version)

    out = {
        "schema_version": "kb-v1",
        "source_file": in_path.name,
        "record_count": len(cleaned),
        "records": cleaned,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"cleaned_records={len(cleaned)}")
    print(f"output={out_path}")


if __name__ == "__main__":
    main()
