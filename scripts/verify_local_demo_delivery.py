"""Verify an uninitialized local delivery. Checksums are NOT a digital signature."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath

from local_demo_runtime import DemoError, digest, plain_path, read_json, repo_path

MANIFEST = "local-delivery-manifest.json"
MAX_FILES = 256
MAX_BYTES = 64 * 1024 * 1024


def validate_rows(rows):
    if type(rows) is not list or not 1 <= len(rows) <= MAX_FILES:
        raise DemoError("delivery_inventory_limit")
    seen, total = set(), 0
    for row in rows:
        name = row["path"]
        if type(name) is not str or not name or len(name) > 512 or "\\" in name or ":" in name \
                or name.startswith("/") or name != PurePosixPath(name).as_posix() \
                or any(part in (".", "..") or part.endswith((" ", ".")) for part in name.split("/")):
            raise DemoError("delivery_relative_path_required")
        if name.casefold() in seen or name == MANIFEST:
            raise DemoError("delivery_duplicate_path")
        seen.add(name.casefold())
        size = row["size_bytes"]
        identity = row["sha256"]
        if type(size) is not int or not 0 <= size <= 32 * 1024 * 1024 \
                or type(identity) is not str or len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
            raise DemoError("delivery_size_or_identity_invalid")
        total += size
    if total > MAX_BYTES:
        raise DemoError("delivery_total_byte_limit")
    return total


def verify(root, *, expected_manifest_sha=None):
    root = plain_path(root).resolve(strict=True)
    manifest = read_json(root / MANIFEST, expected=expected_manifest_sha, maximum=512 * 1024)
    if manifest.get("kind") != "local_research_demo_delivery_v1" or manifest.get("public_distribution_authorized") is not False:
        raise DemoError("delivery_scope_mismatch")
    rows = manifest["files"]
    total = validate_rows(rows)
    if manifest["file_count_excluding_manifest"] != len(rows) or manifest["total_bytes_excluding_manifest"] != total:
        raise DemoError("delivery_summary_mismatch")
    actual = set()
    for number, path in enumerate(root.rglob("*")):
        if number >= 640:
            raise DemoError("delivery_entry_limit")
        plain_path(path)
        if path.is_file():
            plain_path(path, file=True)
            actual.add(path.relative_to(root).as_posix())
    if actual != {MANIFEST, *(row["path"] for row in rows)}:
        raise DemoError("delivery_unexpected_or_missing_files")
    for row in rows:
        path = repo_path(root, row["path"])
        if path.stat().st_size != row["size_bytes"] or digest(path) != row["sha256"]:
            raise DemoError("delivery_member_drift")
    return manifest


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--expected-manifest-sha")
    args = parser.parse_args()
    try:
        result = verify(args.root, expected_manifest_sha=args.expected_manifest_sha)
        print(json.dumps({"event": "clean_local_delivery_verified", "files": len(result["files"]),
                          "public_distribution_authorized": False}, ensure_ascii=False))
    except (DemoError, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, json.dumps({"event": "local_delivery_blocked", "code": getattr(error, "code", "delivery_input_or_io_error")}) + "\n")
