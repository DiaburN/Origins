#!/usr/bin/env python3
"""Self-test for ORIGINS HPR -> Zircon builder.

Creates a tiny sparse library (frames 0 and 3), writes a legacy DXT1 .Zl,
then parses/decodes it with the existing ORIGINS zl_extractor parser.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from zl_writer import build_legacy_zl


def load_zl_extractor():
    p = Path(__file__).resolve().parent.parent / "zl_extractor" / "zl_extract.py"
    if not p.exists():
        raise RuntimeError(f"No encuentro el extractor ORIGINS: {p}")
    spec = importlib.util.spec_from_file_location("origins_zl_extract", p)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No puedo cargar {p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def make_png(path: Path, size, rect_color, label):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 2, size[0]-3, size[1]-3), fill=rect_color)
    d.text((3, 3), str(label), fill=(255, 255, 255, 255))
    im.save(path)


def main():
    zlx = load_zl_extractor()
    with tempfile.TemporaryDirectory(prefix="origins_hpr_test_") as td:
        root = Path(td)
        frames = root / "FRAMES_PNG"
        frames.mkdir()
        make_png(frames / "000000.png", (13, 17), (255, 0, 0, 255), 0)
        make_png(frames / "000003.png", (21, 12), (0, 255, 0, 210), 3)

        meta = root / "IMAGE_METADATA.csv"
        with meta.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["index", "width", "height", "x", "y", "shadow_x", "shadow_y", "shadow"])
            w.writeheader()
            w.writerow({"index":0,"width":13,"height":17,"x":-11,"y":-22,"shadow_x":0,"shadow_y":0,"shadow":0})
            w.writerow({"index":3,"width":21,"height":12,"x":7,"y":-5,"shadow_x":0,"shadow_y":0,"shadow":0})

        zl = root / "test.Zl"
        summary = build_legacy_zl(meta, frames, zl, slot_count=5)
        assert summary["slot_count"] == 5
        assert summary["present_count"] == 2

        lib = zlx.parse(zl)
        assert lib.format == "ZL_LEGACY"
        assert lib.version == 0
        assert lib.slots == 5
        assert lib.images[0].present
        assert not lib.images[1].present
        assert not lib.images[2].present
        assert lib.images[3].present
        assert not lib.images[4].present
        assert lib.images[0].offsetX == -11 and lib.images[0].offsetY == -22
        assert lib.images[3].offsetX == 7 and lib.images[3].offsetY == -5

        for idx in (0, 3):
            payload, codec = zlx.image_payload(lib, lib.images[idx])
            im = zlx.decode(payload, lib.images[idx].width, lib.images[idx].height, codec)
            assert im.size == (lib.images[idx].width, lib.images[idx].height)

        print("SELF TEST OK")
        print(f"ZL format={lib.format} version={lib.version} slots={lib.slots} present={summary['present_count']}")
        print("Sparse IDs and X/Y offsets preserved.")


if __name__ == "__main__":
    main()
