#!/usr/bin/env python3
"""Complete ORIGINS Mir2 2010 extraction including Back, Middle and Front layers.

This is a thin compatibility wrapper around extract_theme_assets.py. It patches
its Mir2 2010 parser so the Crystal MiddleIndex/MiddleImage layer (SmTiles.Lib)
is included exactly as defined by Suprcode/Crystal MapCode.cs.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Tuple

BASE_PATH = Path(__file__).with_name("extract_theme_assets.py")
spec = importlib.util.spec_from_file_location("origins_theme_extractor", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
# Python 3.12 dataclasses expects the executing module to already exist here.
sys.modules[spec.name] = base
spec.loader.exec_module(base)


def signed_i16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def parse_mir2_2010_complete(path: Path) -> Tuple[int, int, Dict[int, Counter], Counter]:
    data = path.read_bytes()
    if len(data) < 54:
        raise ValueError(f"{path.name}: file too small")
    if not (data[0] == 0x10 and data[2] == 0x61 and data[7] == 0x31 and data[14] == 0x31):
        raise ValueError(f"{path.name}: expected Mir2 2010 format")

    xor_value = base.u16(data, 23)
    width = base.u16(data, 21) ^ xor_value
    height = base.u16(data, 25) ^ xor_value
    expected = 54 + width * height * 15
    if len(data) < expected:
        raise ValueError(f"{path.name}: truncated map ({len(data)} < {expected})")

    # Crystal MapCode LoadMapType1:
    # BackIndex=0 (Tiles), MiddleIndex=1 (SmTiles), FrontIndex=byte+2.
    used: Dict[int, Counter] = {0: Counter(), 1: Counter()}
    doors: Counter = Counter()
    offset = 54

    for _x in range(width):
        for _y in range(height):
            back_image = (base.u32(data, offset) ^ 0xAA38AA38) & 0xFFFFFFFF
            middle_image = signed_i16(base.u16(data, offset + 4) ^ xor_value)
            front_image = signed_i16(base.u16(data, offset + 6) ^ xor_value)
            door_index = data[offset + 8] & 0x7F
            front_index = data[offset + 12] + 2

            if front_index == 102:
                front_index = 90
            if front_index >= 255:
                front_index = -1

            tile_id = back_image & 0x1FFFFFFF
            if tile_id > 0:
                used[0][tile_id] += 1

            if middle_image > 0:
                used[1][middle_image] += 1

            if front_index >= 0 and front_image > 0:
                used.setdefault(front_index, Counter())[front_image] += 1

            doors[door_index] += 1
            offset += 15

    return width, height, used, doors


base.parse_mir2_2010 = parse_mir2_2010_complete

if __name__ == "__main__":
    base.main()
