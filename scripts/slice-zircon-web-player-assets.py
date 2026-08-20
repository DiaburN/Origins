#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SCHEMA = "origins.zircon.web-atlas.v1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_child(root: Path, relative: str) -> Path:
    root = root.resolve()
    child = (root / relative).resolve()
    if child != root and root not in child.parents:
        raise ValueError(f"Path escapes root: {relative}")
    return child


def parse_request(text: str) -> tuple[str, list[int]]:
    if ":" not in text:
        raise argparse.ArgumentTypeError("Request must be LibraryFile:index[,index...]")
    name, raw = text.split(":", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("LibraryFile is empty")
    try:
        indices = sorted({int(part.strip()) for part in raw.split(",") if part.strip()})
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not indices or any(index < 0 for index in indices):
        raise argparse.ArgumentTypeError("At least one non-negative frame index is required")
    return name, indices


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy a fail-closed minimal page slice from a generated Zircon player web-asset bundle.")
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--request", action="append", type=parse_request, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    master = load_json(input_root / "player-assets.json")
    if master.get("schema") != SCHEMA:
        raise SystemExit(f"Unexpected master schema: {master.get('schema')!r}")
    by_name = {row.get("libraryFile"): row for row in master.get("libraries", [])}

    requested: dict[str, set[int]] = {}
    for name, indices in args.request:
        requested.setdefault(name, set()).update(indices)

    missing_libraries = sorted(set(requested) - set(by_name))
    if missing_libraries:
        raise SystemExit(f"Requested libraries missing from master: {missing_libraries}")

    output_root = args.output_root.resolve()
    staging = output_root.with_name(output_root.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    output_entries = []
    rows = []
    total_bytes = 0
    try:
        for name in sorted(requested, key=str.casefold):
            entry = by_name[name]
            manifest_path = safe_child(input_root, entry["manifest"])
            manifest = load_json(manifest_path)
            if manifest.get("libraryFile") != name:
                raise SystemExit(f"{name}: manifest identity mismatch")
            images = manifest.get("images")
            if not isinstance(images, list):
                raise SystemExit(f"{name}: images array missing")

            pages: set[str] = set()
            frames = []
            for index in sorted(requested[name]):
                if index >= len(images):
                    raise SystemExit(f"{name}: requested frame {index} >= imageCount {len(images)}")
                image = images[index]
                if image is None:
                    raise SystemExit(f"{name}: requested official frame {index} is empty")
                page = image.get("page")
                if not isinstance(page, str) or not page:
                    raise SystemExit(f"{name}: requested frame {index} has no page")
                pages.add(page)
                frames.append(index)

            dest_dir = staging / name
            dest_dir.mkdir(parents=True)
            shutil.copy2(manifest_path, dest_dir / "manifest.json")
            total_bytes += (dest_dir / "manifest.json").stat().st_size
            page_rows = []
            for page in sorted(pages):
                source_page = safe_child(manifest_path.parent, page)
                if not source_page.is_file() or source_page.stat().st_size <= 0:
                    raise SystemExit(f"{name}: required page missing/empty: {page}")
                destination = dest_dir / page
                shutil.copy2(source_page, destination)
                size = destination.stat().st_size
                total_bytes += size
                page_rows.append({"page": page, "bytes": size})

            output_entries.append({
                "libraryFile": name,
                "manifest": f"{name}/manifest.json",
                "imageCount": int(manifest["imageCount"]),
                "exportedImageCount": int(manifest["exportedImageCount"]),
            })
            rows.append({"libraryFile": name, "frames": frames, "pages": page_rows})

        sliced_master = {
            "schema": SCHEMA,
            "zirconCommit": master.get("zirconCommit"),
            "atlasSize": master.get("atlasSize"),
            "profile": "PLAYER_PROOF_SLICE",
            "libraries": output_entries,
        }
        master_text = json.dumps(sliced_master, indent=2) + "\n"
        (staging / "player-assets.json").write_text(master_text, encoding="utf-8")
        total_bytes += len(master_text.encode("utf-8"))

        if output_root.exists():
            shutil.rmtree(output_root)
        staging.rename(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    report = {
        "schema": "origins.zircon.web-player-proof-slice.v1",
        "status": "PASS",
        "zirconCommit": master.get("zirconCommit"),
        "libraryCount": len(rows),
        "outputBytes": total_bytes,
        "libraries": rows,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
