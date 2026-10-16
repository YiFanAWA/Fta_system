"""Build a clean local-only delivery from frozen payload plus verified wheels."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import zipfile

import prepare_local_demo_package as candidate
from local_demo_runtime import ROOT, DemoError, digest, plain_path, read_json, repo_path
from verify_local_demo_delivery import MANIFEST, MAX_BYTES, validate_rows, verify

RUNTIME_REPORT = "evaluation/quality_eval/runs/m4_relocated_demo_v3_2026-10-16/report.json"
RUNTIME_SHA = "5283d244a52c575bda2230c92ed5279cbb3f0ce6d71406ba4edad7c8be4b5c25"
UI_REPORT = "evaluation/quality_eval/runs/m4_relocated_demo_v3_2026-10-16/ui/report.json"
UI_SHA = "de16821c41fa272bcc3fe817a367fc999af55f44adae79bb110b53f4d9c5ebec"
WHEEL_REPORT = "evaluation/quality_eval/runs/m4_dependency_wheelhouse_v1_2026-10-16.json"
WHEEL_SHA = "fd84629a7ca1f173118f7177fb4222cb8339b25fe112bd8b6aa96b32ca86389c"
GUIDE = "scripts/assets/local-demo-delivery-readme-v1.md"


def source_plan(wheelhouse):
    runtime = read_json(ROOT / RUNTIME_REPORT, expected=RUNTIME_SHA)
    ui = read_json(ROOT / UI_REPORT, expected=UI_SHA)
    wheels = read_json(ROOT / WHEEL_REPORT, expected=WHEEL_SHA)
    if runtime["status"] != "scoped_relocated_offline_runtime_passed_handoff_pending" \
            or len(runtime["cases"]) != 5 or any(not row["passed"] for row in runtime["cases"]) \
            or runtime["new_provider_requests"] != 0 or ui["external_requests"] or not ui["browser_closed"]:
        raise DemoError("delivery_runtime_evidence_incomplete")
    for row in ui["artifacts"]:
        if digest(ROOT / Path(UI_REPORT).parent / row["file"]) != row["sha256"]:
            raise DemoError("delivery_ui_evidence_drift")
    wheelhouse = plain_path(wheelhouse).resolve(strict=True)
    if read_json(wheelhouse / "wheelhouse-manifest.json", expected=WHEEL_SHA) != wheels \
            or wheels["status"] != "all_36_pinned_wheels_official_sha_verified" \
            or len(wheels["files"]) != 36 or wheels["missing"]:
        raise DemoError("delivery_verified_wheelhouse_required")
    rows, sources = [], {}
    for row in candidate.source_inventory():
        if row["role"] == "user_guide":
            row = candidate.describe(ROOT, GUIDE, "user_guide", target="README.local-demo.md")
        rows.append({key: row[key] for key in ("path", "role", "size_bytes", "sha256")})
        sources[row["path"]] = repo_path(ROOT, row["source_path"])
    verifier = candidate.describe(ROOT, "scripts/verify_local_demo_delivery.py", "delivery_verifier")
    rows.append({key: verifier[key] for key in ("path", "role", "size_bytes", "sha256")})
    sources[verifier["path"]] = ROOT / verifier["path"]
    expected_requirements = set((ROOT / "backend-python/requirements.txt").read_text(encoding="utf-8").splitlines())
    if {row["requirement"] for row in wheels["files"]} != expected_requirements:
        raise DemoError("delivery_wheel_pins_do_not_cover_requirements")
    for item in wheels["files"]:
        name = candidate.relative_name(item["filename"])
        if "/" in name or not name.endswith(".whl"):
            raise DemoError("delivery_flat_wheel_required")
        source = repo_path(wheelhouse, name)
        if source.stat().st_size != item["size_bytes"] or digest(source) != item["sha256"]:
            raise DemoError("delivery_wheel_drift")
        name = "dependencies/wheels/" + name
        rows.append({"path": name, "role": "verified_base_dependency_wheel", "size_bytes": item["size_bytes"],
                     "sha256": item["sha256"]})
        sources[name] = source
    rows.append({"path": "dependencies/wheelhouse-manifest.json", "role": "wheel_provenance",
        "size_bytes": (ROOT / WHEEL_REPORT).stat().st_size, "sha256": WHEEL_SHA})
    sources[rows[-1]["path"]] = ROOT / WHEEL_REPORT
    rows.sort(key=lambda row: row["path"])
    validate_rows(rows)
    return rows, sources


def verify_archive(path, manifest):
    path = plain_path(path, file=True)
    rows = manifest["files"]
    with zipfile.ZipFile(path) as archive:
        items = archive.infolist()
        if len(items) != len(rows) + 1 or len({item.filename for item in items}) != len(items) \
                or {item.filename for item in items} != {MANIFEST, *(row["path"] for row in rows)} \
                or sum(item.file_size for item in items) > MAX_BYTES + 512 * 1024:
            raise DemoError("delivery_archive_inventory_invalid")
        for row in rows:
            if archive.getinfo(row["path"]).file_size != row["size_bytes"]:
                raise DemoError("delivery_archive_size_drift")
            with archive.open(row["path"]) as stream:
                raw = stream.read(32 * 1024 * 1024 + 1)
            if sha256(raw).hexdigest() != row["sha256"]:
                raise DemoError("delivery_archive_member_drift")
        if archive.getinfo(MANIFEST).file_size > 512 * 1024 or json.loads(archive.read(MANIFEST)) != manifest:
            raise DemoError("delivery_archive_manifest_drift")


def build(destination, wheelhouse, *, archive=None):
    rows, sources = source_plan(wheelhouse)
    destination = plain_path(destination)
    if destination == ROOT or destination.is_relative_to(ROOT) or ROOT.is_relative_to(destination) \
            or destination == Path(destination.anchor) or not destination.parent.is_dir():
        raise DemoError("delivery_fresh_external_directory_required")
    if destination.exists():
        raise DemoError("delivery_destination_exists")
    if archive is not None:
        archive = plain_path(archive)
        if archive.parent != destination.parent or archive.suffix != ".zip" or archive.exists():
            raise DemoError("delivery_fresh_adjacent_zip_required")
    destination.mkdir()
    for row in rows:
        source = plain_path(sources[row["path"]], file=True)
        with source.open("rb") as stream:
            raw = stream.read(32 * 1024 * 1024 + 1)
        if len(raw) != row["size_bytes"] or sha256(raw).hexdigest() != row["sha256"]:
            raise DemoError("delivery_source_changed_during_copy")
        target = destination / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    manifest = {"kind": "local_research_demo_delivery_v1", "materials_state": "closed_local_inventory",
        "scope": "same_user_local_research_demo_no_public_distribution", "public_distribution_authorized": False,
        "source_baseline": {"path": candidate.BASELINE, "sha256": candidate.BASELINE_SHA},
        "prior_runtime_acceptance": {"path": RUNTIME_REPORT, "sha256": RUNTIME_SHA,
            "scope": "same_windows_host_new_directory_fresh_venv_not_new_machine"},
        "provider_enabled": False, "fta_ready": False, "production_ready": False,
        "file_count_excluding_manifest": len(rows), "total_bytes_excluding_manifest": validate_rows(rows),
        "files": rows}
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with (destination / MANIFEST).open("xb") as stream:
        stream.write(raw)
    verify(destination, expected_manifest_sha=sha256(raw).hexdigest())
    if archive is not None:
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
            for name in (MANIFEST, *(row["path"] for row in rows)):
                stream.write(repo_path(destination, name), arcname=name)
        verify_archive(archive, manifest)
    return {"status": "local_materials_inventory_and_archive_verified", "files": len(rows),
        "payload_bytes": manifest["total_bytes_excluding_manifest"], "manifest_sha256": sha256(raw).hexdigest(),
        "archive_sha256": digest(archive, maximum=MAX_BYTES) if archive is not None else None,
        "archive_bytes": archive.stat().st_size if archive is not None else None,
        "public_distribution_authorized": False, "new_provider_requests": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = plain_path(args.receipt)
    if receipt.parent != ROOT / "evaluation/quality_eval/runs" or not receipt.name.startswith("m4_delivery_materials_") or receipt.exists():
        parser.error("fresh named local M4 receipt required")
    try:
        result = build(args.destination, args.wheelhouse, archive=args.archive)
        with receipt.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False))
    except (DemoError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(1, json.dumps({"event": "delivery_materials_blocked", "code": getattr(error, "code", "delivery_io_or_input_failure")}) + "\n")
