"""Prepare an allowlisted local-only candidate; never install, launch or publish it."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from local_demo_runtime import (ROOT, IDENTITIES, DemoError, digest, load_inputs,
                                plain_path, read_json, repo_path)

BASELINE = "evaluation/quality_eval/fta_baseline_manifest_v118.json"
BASELINE_SHA = "a1c17832ba36b6eb12c8fdf454923a52e1c6d59105d711050464326cf409ccd1"
MANIFEST = "delivery-manifest.json"
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILES = 256
GUIDE = "scripts/assets/local-demo-package-readme-v1.md"
PINNED = {
    "scripts/start_local_demo.py": "launcher",
    "scripts/local_demo_runtime.py": "host",
    "scripts/local_demo_windows.py": "windows_lifecycle",
    "backend-python/requirements.txt": "base_dependencies",
    "evaluation/quality_eval/public_sources/retrieval_environment.yml": "optional_retrieval_reference",
}


def relative_name(name):
    if not isinstance(name, str) or len(name) > 512 or not name or "\\" in name or ":" in name:
        raise DemoError("package_invalid_relative_path")
    parts = name.split("/")
    if len(parts) > 16 or PurePosixPath(name).is_absolute() or any(
        part in ("", ".", "..") or part[-1:] in (" ", ".")
        or re.search(r'[<>"|?*\x00-\x1f]', part)
        or part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        for part in parts
    ):
        raise DemoError("package_invalid_relative_path")
    return name


def describe(root, name, role, *, target=None, expected=None):
    relative_name(name)
    path = repo_path(root, name)
    row = {"path": relative_name(target or name), "source_path": name, "role": role,
           "size_bytes": path.stat().st_size, "sha256": digest(path)}
    if expected is not None and row["sha256"] != expected:
        raise DemoError("package_frozen_member_drift")
    return row


def source_inventory():
    """Consume M3 frozen facts, not its evaluation Python runners or live reports."""
    baseline = read_json(ROOT / BASELINE, expected=BASELINE_SHA)
    known = {row["path"]: row["sha256"] for row in baseline["artifacts"]}
    inputs = load_inputs()
    rows = []
    for group, role in ((inputs.sources, "backend_source"), (inputs.build, "frontend_build"),
                        (inputs.inputs, "frozen_input")):
        rows.extend(describe(ROOT, row["path"], role, expected=row["sha256"]) for row in group)
    rows.extend(describe(ROOT, name, "frozen_input_ledger", expected=identity) for name, identity in IDENTITIES.items())
    for name, role in PINNED.items():
        row = describe(ROOT, name, role)
        if row["sha256"] != known.get(name):
            raise DemoError("package_baseline_member_drift")
        rows.append(row)
    rows.append(describe(ROOT, GUIDE, "user_guide", target="README.local-demo.md"))
    validate_rows(rows)
    return tuple(sorted(rows, key=lambda row: row["path"]))


def validate_rows(rows):
    if not rows or len(rows) > MAX_FILES:
        raise DemoError("package_file_limit")
    seen, total = set(), 0
    for row in rows:
        name = relative_name(row["path"])
        relative_name(row["source_path"])
        if name.casefold() in seen or name.casefold() == MANIFEST.casefold():
            raise DemoError("package_duplicate_path")
        seen.add(name.casefold())
        size = row["size_bytes"]
        if type(size) is not int or not 0 <= size <= 32 * 1024 * 1024:
            raise DemoError("package_size_limit")
        total += size
        if total > MAX_TOTAL or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"]):
            raise DemoError("package_size_or_identity_limit")


def manifest_for(rows):
    validate_rows(rows)
    return {"kind": "local_demo_candidate_package_v1", "status": "prepared_not_runtime_accepted",
        "baseline": {"path": BASELINE, "sha256": BASELINE_SHA},
        "scope": "same_user_local_research_demo_only_no_public_distribution",
        "provider_enabled": False, "m4_complete": False, "first_delivery_accepted": False,
        "fta_ready": False, "production_ready": False, "public_distribution_authorized": False,
        "clean_environment_verified": False, "file_count_excluding_manifest": len(rows),
        "total_bytes_excluding_manifest": sum(row["size_bytes"] for row in rows),
        "roles": dict(sorted(Counter(row["role"] for row in rows).items())),
        "excluded": ["credentials_and_dotenv", "user_database_and_sidecars", "virtual_environment",
                     "model_weights_and_cache", "node_modules", "whole_evaluation_history", "evaluation_executable_code"],
        "pending": ["independent_python_environment_installation_and_dependency_check",
                    "relocated_cli_http_browser_lifecycle_acceptance", "local_package_user_acceptance",
                    "third_party_media_and_data_public_distribution_rights"],
        "files": list(rows)}


def materialize(root, target, rows):
    validate_rows(rows)
    root = plain_path(root).resolve(strict=True)
    target = plain_path(target)
    if target == root or target.is_relative_to(root) or root.is_relative_to(target) or target == Path(target.anchor):
        raise DemoError("package_destination_must_be_outside_source_tree")
    if target.exists():
        raise DemoError("package_destination_exists")
    if not target.parent.is_dir():
        raise DemoError("package_destination_parent_missing")
    target.mkdir()
    for row in rows:
        original = repo_path(root, row["source_path"])
        with original.open("rb") as stream:
            raw = stream.read(32 * 1024 * 1024 + 1)
        if raw is None or len(raw) != row["size_bytes"] or digest(original) != row["sha256"]:
            raise DemoError("package_source_drift")
        if sha256(raw).hexdigest() != row["sha256"]:
            raise DemoError("package_source_changed_during_copy")
        destination = target / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(raw)
    manifest = manifest_for(rows)
    with (target / MANIFEST).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    verify(target, rows)
    return manifest


def verify(target, rows):
    """Compare with caller's trusted inventory, never trust a manifest's self-report."""
    expected = manifest_for(rows)
    target = plain_path(target).resolve(strict=True)
    actual = set()
    for number, path in enumerate(target.rglob("*")):
        if number >= 512:
            raise DemoError("package_entry_limit")
        plain_path(path)
        if path.is_file():
            plain_path(path, file=True)
            actual.add(path.relative_to(target).as_posix())
    if actual != {MANIFEST, *(row["path"] for row in rows)}:
        raise DemoError("package_unexpected_member")
    if read_json(target / MANIFEST, maximum=512 * 1024) != expected:
        raise DemoError("package_manifest_drift")
    for row in rows:
        path = repo_path(target, row["path"])
        if path.stat().st_size != row["size_bytes"] or digest(path) != row["sha256"]:
            raise DemoError("package_member_drift")
    return expected


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = source_inventory()
        result = verify(args.destination, rows) if args.check else materialize(ROOT, args.destination, rows)
        print(json.dumps({"event": "local_demo_candidate_verified" if args.check else "local_demo_candidate_prepared",
            "files": result["file_count_excluding_manifest"], "bytes": result["total_bytes_excluding_manifest"],
            "m4_complete": False, "provider_enabled": False}, ensure_ascii=False))
        return 0
    except (DemoError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"event": "local_demo_package_blocked", "code": getattr(error, "code", "package_io_or_input_error"),
                          "failure_type": type(error).__name__, "m4_complete": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
