"""Validate the restricted, evidence-bound FTA preview contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


BACKEND = Path(__file__).resolve().parents[3] / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.fta_graph_contract import validate_fta_preview  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(payload: Mapping[str, Any]) -> list[str]:
    return validate_fta_preview(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = load(Path(args.input))
    errors = validate(payload)
    report = {
        "status": "fta_preview_validated" if not errors else "validation_failed",
        "preview_only": payload.get("dataset_info", {}).get("status") == "preview_only",
        "tree_count": len(payload.get("trees", [])),
        "excluded_event_count": len(payload.get("excluded_events", [])),
        "production_ready": payload.get("dataset_info", {}).get("production_ready"),
        "fta_ready": payload.get("dataset_info", {}).get("fta_ready"),
        "errors": errors,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
