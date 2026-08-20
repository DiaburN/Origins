#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SCHEMA = "origins.zircon.web-atlas.v1"
MERGED_PROFILE = "MERGED_PLAYER_LIBRARIES"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_child(root: Path, relative: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"Manifest path escapes bundle root: {relative}")
    return candidate


def fingerprint(manifest: dict) -> tuple:
    return (
        manifest.get("libraryFile"),
        manifest.get("sourceSha256"),
        int(manifest.get("imageCount", -1)),
        int(manifest.get("exportedImageCount", -1)),
        int(manifest.get("atlasSize", -1)),
    )


def validate_library(bundle_root: Path, entry: dict) -> tuple[dict, Path]:
    library = entry.get("libraryFile")
    manifest_rel = entry.get("manifest")
    if not isinstance(library, str) or not library:
        raise ValueError("Bundle contains a library entry without libraryFile")
    if not isinstance(manifest_rel, str) or not manifest_rel:
        raise ValueError(f"{library}: missing manifest path")

    manifest_path = safe_child(bundle_root, manifest_rel)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{library}: manifest does not exist: {manifest_path}")
    manifest = load_json(manifest_path)
    if manifest.get("schema") != SCHEMA:
        raise ValueError(f"{library}: unexpected manifest schema {manifest.get('schema')!r}")
    if manifest.get("libraryFile") != library:
        raise ValueError(f"{library}: manifest libraryFile mismatch: {manifest.get('libraryFile')!r}")
    if int(manifest.get("exportedImageCount", 0)) <= 0:
        raise ValueError(f"{library}: exportedImageCount must be positive")
    images = manifest.get("images")
    pages = manifest.get("pages")
    if not isinstance(images, list) or not isinstance(pages, list) or not pages:
        raise ValueError(f"{library}: incomplete manifest images/pages")
    for page in pages:
        if not isinstance(page, str) or not page:
            raise ValueError(f"{library}: invalid atlas page name")
        page_path = safe_child(manifest_path.parent, page)
        if not page_path.is_file() or page_path.stat().st_size <= 0:
            raise FileNotFoundError(f"{library}: missing/empty atlas page: {page_path}")
    return manifest, manifest_path


def merge(input_roots: list[Path], output_root: Path) -> dict:
    if len(input_roots) < 1:
        raise ValueError("At least one --input-root is required")

    zircon_commit: str | None = None
    atlas_size: int | None = None
    selected: dict[str, tuple[dict, Path, Path]] = {}
    duplicates: list[dict] = []
    input_summary: list[dict] = []

    for bundle_root in input_roots:
        bundle_root = bundle_root.resolve()
        master_path = bundle_root / "player-assets.json"
        if not master_path.is_file():
            raise FileNotFoundError(f"Missing player-assets.json in {bundle_root}")
        master = load_json(master_path)
        if master.get("schema") != SCHEMA:
            raise ValueError(f"Unexpected master schema in {bundle_root}: {master.get('schema')!r}")
        commit = master.get("zirconCommit")
        size = int(master.get("atlasSize", -1))
        if not isinstance(commit, str) or not commit:
            raise ValueError(f"Missing zirconCommit in {master_path}")
        if size <= 0:
            raise ValueError(f"Invalid atlasSize in {master_path}: {size}")
        if zircon_commit is None:
            zircon_commit = commit
            atlas_size = size
        elif commit != zircon_commit:
            raise ValueError(f"Zircon commit mismatch: {commit} != {zircon_commit}")
        elif size != atlas_size:
            raise ValueError(f"Atlas size mismatch: {size} != {atlas_size}")

        entries = master.get("libraries")
        if not isinstance(entries, list):
            raise ValueError(f"Master libraries must be an array: {master_path}")
        input_summary.append({"root": str(bundle_root), "profile": master.get("profile"), "libraryCount": len(entries)})

        for entry in entries:
            manifest, manifest_path = validate_library(bundle_root, entry)
            library = manifest["libraryFile"]
            current = selected.get(library)
            if current is None:
                selected[library] = (manifest, manifest_path, bundle_root)
                continue
            current_manifest, current_path, current_root = current
            if fingerprint(current_manifest) != fingerprint(manifest):
                raise ValueError(
                    f"Conflicting duplicate library {library}: {current_path} vs {manifest_path}; "
                    f"fingerprints {fingerprint(current_manifest)!r} != {fingerprint(manifest)!r}"
                )
            duplicates.append({
                "libraryFile": library,
                "keptRoot": str(current_root),
                "duplicateRoot": str(bundle_root),
                "sourceSha256": manifest.get("sourceSha256"),
            })

    if not selected:
        raise ValueError("No player libraries were found in input bundles")

    output_root = output_root.resolve()
    staging = output_root.with_name(output_root.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=False)

    master_entries: list[dict] = []
    total_bytes = 0
    try:
        for library in sorted(selected, key=str.casefold):
            manifest, manifest_path, _ = selected[library]
            source_dir = manifest_path.parent
            destination = staging / library
            shutil.copytree(source_dir, destination)
            for file in destination.rglob("*"):
                if file.is_file():
                    total_bytes += file.stat().st_size
            master_entries.append({
                "libraryFile": library,
                "manifest": f"{library}/manifest.json",
                "imageCount": int(manifest["imageCount"]),
                "exportedImageCount": int(manifest["exportedImageCount"]),
            })

        merged_master = {
            "schema": SCHEMA,
            "zirconCommit": zircon_commit,
            "atlasSize": atlas_size,
            "profile": MERGED_PROFILE,
            "libraries": master_entries,
        }
        master_text = json.dumps(merged_master, indent=2) + "\n"
        (staging / "player-assets.json").write_text(master_text, encoding="utf-8")
        total_bytes += len(master_text.encode("utf-8"))

        if output_root.exists():
            shutil.rmtree(output_root)
        staging.rename(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return {
        "schema": "origins.zircon.web-player-asset-merge.v1",
        "status": "PASS",
        "zirconCommit": zircon_commit,
        "atlasSize": atlas_size,
        "inputCount": len(input_roots),
        "inputs": input_summary,
        "libraryCount": len(master_entries),
        "libraries": [entry["libraryFile"] for entry in master_entries],
        "deduplicatedCount": len(duplicates),
        "duplicates": duplicates,
        "outputRoot": str(output_root),
        "outputBytes": total_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge compatible exported Zircon player web-asset bundles without altering atlas/frame data.")
    parser.add_argument("--input-root", action="append", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = merge(args.input_root, args.output_root)
    text = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
