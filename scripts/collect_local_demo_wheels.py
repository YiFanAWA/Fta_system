"""Collect ONLY exact official-SHA wheels from pip's existing read-only HTTP cache."""
from argparse import ArgumentParser
from hashlib import sha224, sha256
import json
import os
from pathlib import Path
import re
from time import monotonic
import urllib.request
from urllib.parse import urlsplit

from pip._vendor.cachecontrol.controller import CacheController
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import parse_wheel_filename
from local_demo_runtime import DemoError, digest, plain_path, read_json
import prepare_local_demo_package as package

MAX_WHEEL = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024


def select_wheel(rows):
    if len(rows) > 512:
        raise DemoError("wheel_release_file_limit")
    ranks = {tag: index for index, tag in enumerate(sys_tags())}
    choices = []
    for row in rows:
        filename = row["filename"]
        if row["packagetype"] != "bdist_wheel" or row.get("yanked") or not filename.endswith(".whl"):
            continue
        package.relative_name(filename)
        if "/" in filename:
            raise DemoError("wheel_filename_not_flat")
        _, _, _, tags = parse_wheel_filename(filename)
        compatible = [ranks[tag] for tag in tags if tag in ranks]
        if compatible:
            choices.append((min(compatible), filename, row))
    if not choices:
        raise DemoError("compatible_pinned_wheel_missing")
    return min(choices, key=lambda row: row[:2])[2]


def verified_cached_body(row, cache):
    parsed = urlsplit(row["url"])
    if parsed.scheme != "https" or parsed.netloc != "files.pythonhosted.org" or parsed.query or parsed.fragment:
        raise DemoError("non_official_wheel_url")
    expected = row["digests"]["sha256"]
    size = row["size"]
    if type(size) is not int or not 0 < size <= MAX_WHEEL or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise DemoError("wheel_size_or_identity_limit")
    key = sha224(CacheController.cache_url(row["url"]).encode()).hexdigest()
    path = plain_path(cache / Path(*key[:5]) / (key + ".body"))
    if not path.is_file():
        return None
    plain_path(path, file=True)
    if path.stat().st_size != size or digest(path) != expected:
        return None
    with path.open("rb") as stream:
        raw = stream.read(MAX_WHEEL + 1)
    if len(raw) != size or sha256(raw).hexdigest() != expected:
        raise DemoError("cached_wheel_changed")
    return raw


def collect(target):
    target = plain_path(target).resolve(strict=True)
    manifest = read_json(target / package.MANIFEST)
    if manifest["baseline"]["sha256"] != package.BASELINE_SHA:
        raise DemoError("wheel_target_baseline_mismatch")
    reference = next(row for row in package.source_inventory() if row["role"] == "base_dependencies")
    requirement_file = plain_path(target / reference["path"], file=True)
    if digest(requirement_file) != reference["sha256"]:
        raise DemoError("wheel_requirements_drift")
    requirements = requirement_file.read_text(encoding="utf-8").splitlines()
    if len(requirements) != 36 or any(not re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+", line) for line in requirements):
        raise DemoError("only_frozen_36_version_pins_allowed")
    output = target / ".m4-wheelhouse-v1"
    output.mkdir()  # Never overwrite prior collection.
    cache = plain_path(Path(os.environ["LOCALAPPDATA"]) / "pip/Cache/http-v2")
    result = {"status": "blocked", "cache_read_only": True, "model_requests": 0,
              "artifact_binary_downloads": 0, "files": [], "missing": []}
    total, metadata_total, start = 0, 0, monotonic()
    try:
        for requirement in requirements:
            if monotonic() - start > 300:
                raise DemoError("wheel_collection_time_limit")
            name, version = requirement.split("==")
            url = f"https://pypi.org/pypi/{name}/{version}/json"
            with urllib.request.urlopen(url, timeout=10) as response:
                if urlsplit(response.url).netloc != "pypi.org":
                    raise DemoError("non_official_metadata_redirect")
                raw = response.read(2 * 1024 * 1024 + 1)
            metadata_total += len(raw)
            if len(raw) > 2 * 1024 * 1024 or metadata_total > 16 * 1024 * 1024:
                raise DemoError("wheel_metadata_size_limit")
            row = select_wheel(json.loads(raw)["urls"])
            body = verified_cached_body(row, cache)
            if body is None:
                result["missing"].append({"requirement": requirement, "filename": row["filename"]})
                continue  # Explicit missing record, never guess or copy installed site-packages.
            total += len(body)
            if total > MAX_TOTAL:
                raise DemoError("wheelhouse_byte_limit")
            with (output / row["filename"]).open("xb") as stream:
                stream.write(body)
            result["files"].append({"requirement": requirement, "filename": row["filename"],
                "size_bytes": len(body), "sha256": row["digests"]["sha256"],
                "official_metadata_url": url, "official_wheel_url": row["url"], "origin": "verified_read_only_pip_http_cache"})
            print(json.dumps({"requirement": requirement, "official_sha_match": True}), flush=True)
        if not result["missing"] and len(result["files"]) == 36:
            result["status"] = "all_36_pinned_wheels_official_sha_verified"
    except Exception as error:
        result.update({"failure_type": type(error).__name__, "code": getattr(error, "code", "metadata_or_cache_unavailable")})
    finally:
        result.update({"total_wheel_bytes": total, "metadata_bytes": metadata_total,
                       "elapsed_seconds": round(monotonic() - start, 3)})
        with (output / "wheelhouse-manifest.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    value = collect(args.package)
    print(json.dumps({"status": value["status"], "verified_wheels": len(value["files"]), "missing": len(value["missing"])}))
    raise SystemExit(0 if value["status"] == "all_36_pinned_wheels_official_sha_verified" else 1)
