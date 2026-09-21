"""Build a deterministic, non-expert FAA SDR adapter-development sample."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SOURCE_URL = "https://external.apic4e.faa.gov/sdrs/retrieve/SDR-2024.csv"
DEFAULT_INPUT = Path("tmp/SDR-2024.csv")
DEFAULT_OUTPUT = Path(
    "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _eligible(row: dict[str, str]) -> bool:
    return bool(
        _clean(row.get("OperatorControlNumber"))
        and _clean(row.get("JASCCode"))
        and _clean(row.get("AircraftModel"))
        and _clean(row.get("Discrepancy"))
        and (
            _clean(row.get("PartName"))
            or _clean(row.get("ComponentName"))
            or _clean(row.get("PartNumber"))
            or _clean(row.get("ComponentPartNumber"))
        )
    )


def _bucket(row: dict[str, str]) -> tuple[str, str, str, str]:
    has_remedy = "c/a:" in _clean(row.get("Discrepancy")).casefold()
    has_component = bool(_clean(row.get("ComponentName")) and _clean(row.get("ComponentName")).casefold() != "unknown")
    return (
        _clean(row.get("JASCCode")),
        _clean(row.get("PartCondition")),
        "remedy" if has_remedy else "observation",
        "component" if has_component else "part",
    )


def select_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    eligible = sorted(
        (row for row in rows if _eligible(row)),
        key=lambda row: _clean(row.get("OperatorControlNumber")),
    )
    chosen: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_buckets: set[tuple[str, str, str, str]] = set()

    def add_if_new(row: dict[str, str]) -> bool:
        record_id = _clean(row.get("OperatorControlNumber"))
        if record_id in seen_ids:
            return False
        chosen.append(row)
        seen_ids.add(record_id)
        seen_buckets.add(_bucket(row))
        return True

    # Guarantee that the first development sample covers the source roles we
    # intend to test.  Without quotas, stable lexical ordering can fill the
    # sample with observational rows and accidentally omit C/A maintenance
    # narratives entirely.
    role_predicates = (
        lambda row: "c/a:" in _clean(row.get("Discrepancy")).casefold(),
        lambda row: bool(_clean(row.get("ComponentName")) and _clean(row.get("ComponentName")).casefold() != "unknown"),
        lambda row: bool(_clean(row.get("PartNumber")) or _clean(row.get("ComponentPartNumber"))),
        lambda row: bool(_clean(row.get("PartCondition")) and _clean(row.get("PartCondition")).casefold() != "unknown"),
    )
    per_role = max(1, min(8, limit // len(role_predicates)))
    for predicate in role_predicates:
        added = 0
        for row in eligible:
            if predicate(row) and add_if_new(row):
                added += 1
            if added >= per_role or len(chosen) >= limit:
                break
        if len(chosen) >= limit:
            return chosen[:limit]

    for row in eligible:
        bucket = _bucket(row)
        record_id = _clean(row.get("OperatorControlNumber"))
        if bucket in seen_buckets or record_id in seen_ids:
            continue
        add_if_new(row)
        if len(chosen) >= limit:
            return chosen
    for row in eligible:
        record_id = _clean(row.get("OperatorControlNumber"))
        if record_id in seen_ids:
            continue
        add_if_new(row)
        if len(chosen) >= limit:
            break
    return chosen


def _input_text(row: dict[str, str]) -> str:
    fields = (
        "OperatorControlNumber",
        "JASCCode",
        "AircraftMake",
        "AircraftModel",
        "PartName",
        "PartNumber",
        "PartCondition",
        "ComponentName",
        "ComponentPartNumber",
        "Discrepancy",
    )
    return "\n".join(f"{name}: {_clean(row.get(name))}" for name in fields if _clean(row.get(name)))


def build(input_path: Path, output_path: Path, limit: int) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        rows = list(csv.DictReader(handle))
    selected = select_rows(rows, limit)
    if len(selected) != limit:
        raise RuntimeError(f"only selected {len(selected)} eligible rows; expected {limit}")
    samples = [
        {
            "sample_id": f"FAA-SDR-2024-{index:03d}",
            "source_record_id": _clean(row["OperatorControlNumber"]),
            "input_text": _input_text(row),
            "raw_record": row,
        }
        for index, row in enumerate(selected, start=1)
    ]
    payload = {
        "dataset_id": "aerospace_faa_sdr_public_sample_v1",
        "dataset_role": "adapter_development_only",
        "lifecycle_status": "sealed_development_sample",
        "eligible_for_expert_gold": False,
        "eligible_for_final_generalization_claim": False,
        "sample_size": len(samples),
        "source": {
            "provider": "Federal Aviation Administration",
            "dataset_name": "Service Difficulty Reports",
            "source_url": SOURCE_URL,
            "source_year": 2024,
            "retrieved_date": "2026-09-21",
            "local_source_file": str(input_path),
            "license_note": "Public FAA download; retain source URL and terms review. This sample is not an expert gold set.",
            "selection_rule": "Deterministic first-per-structure bucket, then stable record-id fill; no semantic filtering or labeling.",
        },
        "samples": samples,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()
    payload = build(args.input, args.output, args.limit)
    print(json.dumps({"output": str(args.output), "sample_size": payload["sample_size"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
