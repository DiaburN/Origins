#!/usr/bin/env python3
"""Render Mir2 2010 reference maps using Crystal MapEditor placement rules.

Placement follows Suprcode/Crystal.MapEditor Main.cs:
- CellWidth = 48, CellHeight = 32.
- Back layer is drawn only at even X/Y cells.
- Map image values are 1-based and .Lib arrays are 0-based.
- 48x32 and 96x64 images draw at the cell origin.
- Larger Middle/Front objects are bottom-anchored at (y + 1) * 32 - height.
- Layer order: Back -> Middle -> Front.

Animations are represented by their base frame. Door-open alternatives are not
used; this renderer is for visual source analysis, not game runtime playback.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

BASE_PATH = Path(__file__).with_name("extract_theme_assets.py")
spec = importlib.util.spec_from_file_location("origins_theme_extractor_render", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

CELL_W = 48
CELL_H = 32


@dataclass
class Cell:
    back_index: int
    back_image: int
    middle_index: int
    middle_image: int
    front_index: int
    front_image: int
    door_index: int
    door_offset: int


def signed_i16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def parse_map(path: Path) -> Tuple[int, int, Dict[Tuple[int, int], Cell]]:
    data = path.read_bytes()
    if len(data) < 54:
        raise ValueError(f"{path.name}: too small")
    if not (data[0] == 0x10 and data[2] == 0x61 and data[7] == 0x31 and data[14] == 0x31):
        raise ValueError(f"{path.name}: expected Mir2 2010 map")

    xor_value = base.u16(data, 23)
    width = base.u16(data, 21) ^ xor_value
    height = base.u16(data, 25) ^ xor_value
    offset = 54
    cells: Dict[Tuple[int, int], Cell] = {}

    for x in range(width):
        for y in range(height):
            back_image = (base.u32(data, offset) ^ 0xAA38AA38) & 0xFFFFFFFF
            middle_image = signed_i16(base.u16(data, offset + 4) ^ xor_value)
            front_image = (base.u16(data, offset + 6) ^ xor_value) & 0xFFFF
            door_index = data[offset + 8] & 0x7F
            door_offset = data[offset + 9]
            front_index = data[offset + 12] + 2
            if front_index == 102:
                front_index = 90
            if front_index >= 255:
                front_index = -1

            cells[(x, y)] = Cell(
                back_index=0,
                back_image=back_image,
                middle_index=1,
                middle_image=middle_image,
                front_index=front_index,
                front_image=front_image,
                door_index=door_index,
                door_offset=door_offset,
            )
            offset += 15

    return width, height, cells


class LibCache:
    def __init__(self, lib_dir: Path):
        self.lib_dir = lib_dir
        self.libs: Dict[int, base.CrystalLib] = {}
        self.images: Dict[Tuple[int, int], Tuple[int, int, bytes]] = {}

    def get_lib(self, slot: int):
        if slot not in self.libs:
            name = base.library_name_for_slot(slot)
            path = self.lib_dir / name
            if not path.exists():
                raise FileNotFoundError(path)
            self.libs[slot] = base.CrystalLib(path)
        return self.libs[slot]

    def get_image(self, slot: int, image_id: int) -> Optional[Tuple[int, int, bytes]]:
        key = (slot, image_id)
        if key in self.images:
            return self.images[key]
        try:
            w, h, _x, _y, _sx, _sy, _shadow, rgba = self.get_lib(slot).extract(image_id)
        except (ValueError, IndexError):
            return None
        result = (w, h, rgba)
        self.images[key] = result
        return result

    def close(self):
        for lib in self.libs.values():
            lib.close()


def alpha_over(canvas: bytearray, cw: int, ch: int, image: bytes, iw: int, ih: int, dx: int, dy: int):
    for sy in range(ih):
        cy = dy + sy
        if cy < 0 or cy >= ch:
            continue
        for sx in range(iw):
            cx = dx + sx
            if cx < 0 or cx >= cw:
                continue
            sp = (sy * iw + sx) * 4
            sa = image[sp + 3]
            if sa == 0:
                continue
            dp = (cy * cw + cx) * 4
            if sa == 255:
                canvas[dp:dp+4] = image[sp:sp+4]
                continue
            inv = 255 - sa
            sr, sg, sb = image[sp], image[sp+1], image[sp+2]
            dr, dg, db, da = canvas[dp], canvas[dp+1], canvas[dp+2], canvas[dp+3]
            out_a = sa + (da * inv + 127) // 255
            if out_a == 0:
                canvas[dp:dp+4] = b"\x00\x00\x00\x00"
                continue
            # Straight-alpha composition.
            nr = (sr * sa * 255 + dr * da * inv + out_a * 127) // (out_a * 255)
            ng = (sg * sa * 255 + dg * da * inv + out_a * 127) // (out_a * 255)
            nb = (sb * sa * 255 + db * da * inv + out_a * 127) // (out_a * 255)
            canvas[dp:dp+4] = bytes((min(255,nr), min(255,ng), min(255,nb), min(255,out_a)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--crop", nargs=4, type=int, metavar=("X", "Y", "W", "H"), help="cell crop")
    args = ap.parse_args()

    lib_dir = base.resolve_wemade_mir2_dir(args.data)
    width, height, cells = parse_map(args.map)

    if args.crop:
        x0, y0, rw, rh = args.crop
    else:
        x0, y0, rw, rh = 0, 0, width, height
    x1 = min(width, x0 + rw)
    y1 = min(height, y0 + rh)
    x0 = max(0, x0)
    y0 = max(0, y0)

    # Large objects are bottom anchored and can extend above the crop.
    top_margin = 512
    right_margin = 256
    canvas_w = (x1 - x0) * CELL_W + right_margin
    canvas_h = (y1 - y0) * CELL_H + top_margin
    canvas = bytearray(canvas_w * canvas_h * 4)
    # Neutral black, matching Mir's visual treatment for transparent/outside-map space.
    for p in range(0, len(canvas), 4):
        canvas[p:p+4] = b"\x00\x00\x00\xff"

    cache = LibCache(lib_dir)
    try:
        # BACK: exact MapEditor parity rule.
        for y in range(y0, y1):
            if y % 2:
                continue
            for x in range(x0, x1):
                if x % 2:
                    continue
                c = cells[(x, y)]
                image_id = (c.back_image & 0x1FFFFFFF) - 1
                if image_id < 0:
                    continue
                im = cache.get_image(c.back_index, image_id)
                if not im:
                    continue
                iw, ih, rgba = im
                dx = (x - x0) * CELL_W
                dy = top_margin + (y - y0) * CELL_H
                alpha_over(canvas, canvas_w, canvas_h, rgba, iw, ih, dx, dy)

        # MIDDLE then FRONT, preserving Crystal's y-major painter order.
        for layer in ("middle", "front"):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    c = cells[(x, y)]
                    if layer == "middle":
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
                    iw, ih, rgba = im
                    dx = (x - x0) * CELL_W
                    if (iw == CELL_W and ih == CELL_H) or (iw == CELL_W * 2 and ih == CELL_H * 2):
                        dy = top_margin + (y - y0) * CELL_H
                    else:
                        dy = top_margin + (y - y0 + 1) * CELL_H - ih
                    alpha_over(canvas, canvas_w, canvas_h, rgba, iw, ih, dx, dy)
    finally:
        cache.close()

    # Trim unused black margins conservatively only on right; keep top margin for tall objects.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    base.write_rgba_png(args.out, canvas_w, canvas_h, bytes(canvas))
    print(f"Rendered {args.map.name}: {x0},{y0} -> {x1},{y1} at {args.out}")


if __name__ == "__main__":
    main()
