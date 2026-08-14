#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_EXTRACTOR = ROOT / "tools" / "crystal-map-importer" / "extract_theme_assets.py"
spec = importlib.util.spec_from_file_location("crystal_lib_reader", BASE_EXTRACTOR)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
CrystalLib = mod.CrystalLib
write_rgba_png = mod.write_rgba_png


def expand(*values):
    out = set()
    for value in values:
        if isinstance(value, int):
            out.add(value)
        else:
            a, b = value
            out.update(range(a, b + 1))
    return sorted(out)

# Exact indices referenced by the Crystal 1024x768 gameplay HUD and the first
# primary gameplay windows. These are source indices, not hand-drawn replacements.
LIBRARIES = {
    "Prguse.Lib": expand(
        1, 4, 8, 24, 76, 100, 340, 544,
        (826, 828),
        (1900, 1914),
        (1923, 1945),
        (1960, 1962),
        (2004, 2006),
        2012, (2015, 2029), (2034, 2065),
        (2090, 2104),
        (2164, 2169),
        2190, 2193, 2247,
    ),
    "Prguse2.Lib": expand((307, 307), (360, 368), (1200, 1205)),
    "Title.Lib": expand(
        168, 169, (196, 198), (483, 485),
        (500, 508), 737, 738, 739,
    ),
    # Optional in the old public mirror. It is only used here for alternate
    # high-weight bar artwork; the base HUD remains exact without it.
    "UI_32bit.Lib": expand((470, 473)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source": "Suprcode/Crystal + public Crystal patch libraries",
        "resolution": [1024, 768],
        "libraries": {},
    }

    for lib_name, ids in LIBRARIES.items():
        path = args.data / lib_name
        if not path.exists():
            print(f"OPTIONAL LIB NOT PRESENT: {path}")
            manifest["libraries"][lib_name] = {}
            continue
        reader = CrystalLib(path)
        lib_out = args.out / "assets" / path.stem
        entries = {}
        try:
            for image_id in ids:
                try:
                    w, h, x, y, sx, sy, shadow, rgba = reader.extract(image_id)
                except (ValueError, IndexError) as exc:
                    print(f"SKIP {lib_name} #{image_id}: {exc}")
                    continue
                target = lib_out / f"{image_id:05d}.png"
                write_rgba_png(target, w, h, rgba)
                entries[str(image_id)] = {
                    "png": target.relative_to(args.out).as_posix(),
                    "size": [w, h],
                    "offset": [x, y],
                    "shadow_offset": [sx, sy],
                    "shadow": shadow,
                }
        finally:
            reader.close()
        manifest["libraries"][lib_name] = entries
        print(lib_name, len(entries), "images")

    (args.out / "ui-assets.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Wrote", args.out / "ui-assets.json")


if __name__ == "__main__":
    main()
