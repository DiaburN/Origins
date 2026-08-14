#!/usr/bin/env python3
"""Export drawable Mir2 2010 map placements using Crystal MapEditor rules.

The JSON output is intended for ORIGINS theme classification. Each record keeps
cell coordinates, source library slot/name, zero-based .Lib image ID, rendered
pixel position/size, layer, and door metadata.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
RENDER_PATH = HERE / "render_mir2_2010_reference.py"
spec = importlib.util.spec_from_file_location("origins_mir2_renderer_export", RENDER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {RENDER_PATH}")
r = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r
spec.loader.exec_module(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    lib_dir = r.base.resolve_wemade_mir2_dir(args.data)
    width, height, cells = r.parse_map(args.map)
    cache = r.LibCache(lib_dir)
    records = []

    try:
        # Back layer, exact even/even rule.
        for y in range(height):
            if y % 2:
                continue
            for x in range(width):
                if x % 2:
                    continue
                c = cells[(x, y)]
                image_id = (c.back_image & 0x1FFFFFFF) - 1
                if image_id < 0:
                    continue
                im = cache.get_image(c.back_index, image_id)
                if not im:
                    continue
                iw, ih, _rgba = im
                records.append({
                    "layer": "BACK",
                    "cell_x": x,
                    "cell_y": y,
                    "library_slot": c.back_index,
                    "library": r.base.library_name_for_slot(c.back_index),
                    "image_id": image_id,
                    "width": iw,
                    "height": ih,
                    "draw_x": x * r.CELL_W,
                    "draw_y": y * r.CELL_H,
                    "door_index": 0,
                    "door_offset": 0,
                })

        for layer in ("MIDDLE", "FRONT"):
            for y in range(height):
                for x in range(width):
                    c = cells[(x, y)]
                    if layer == "MIDDLE":
                        slot = c.middle_index
                        image_id = c.middle_image - 1
                    else:
                        slot = c.front_index
                        image_id = (c.front_image & 0x7FFF) - 1
                    if slot < 0 or image_id < 0:
                        continue
                    im = cache.get_image(slot, image_id)
                    if not im:
                        continue
                    iw, ih, _rgba = im
                    dx = x * r.CELL_W
                    if (iw == r.CELL_W and ih == r.CELL_H) or (iw == 2 * r.CELL_W and ih == 2 * r.CELL_H):
                        dy = y * r.CELL_H
                        anchor = "CELL_ORIGIN"
                    else:
                        dy = (y + 1) * r.CELL_H - ih
                        anchor = "BOTTOM_CELL"
                    records.append({
                        "layer": layer,
                        "cell_x": x,
                        "cell_y": y,
                        "library_slot": slot,
                        "library": r.base.library_name_for_slot(slot),
                        "image_id": image_id,
                        "width": iw,
                        "height": ih,
                        "draw_x": dx,
                        "draw_y": dy,
                        "anchor": anchor,
                        "door_index": c.door_index if layer == "FRONT" else 0,
                        "door_offset": c.door_offset if layer == "FRONT" else 0,
                    })
    finally:
        cache.close()

    payload = {
        "map": args.map.name,
        "width_cells": width,
        "height_cells": height,
        "cell_width": r.CELL_W,
        "cell_height": r.CELL_H,
        "placements": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Exported {len(records)} placements -> {args.out}")


if __name__ == "__main__":
    main()
