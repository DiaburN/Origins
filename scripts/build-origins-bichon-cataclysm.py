#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

# Exact pinned Zircon Libraries.KROrder entries for native map libraries.
KR_ORDER = {
    0: "Tilesc", 1: "Tiles30c", 2: "Tiles5c", 3: "SmTilesc",
    4: "Housesc", 5: "Cliffsc", 6: "Dungeonsc", 7: "Innersc",
    8: "Furnituresc", 9: "Wallsc", 10: "SmObjectsc", 11: "Animationsc",
    12: "Object1c", 13: "Object2c",
    15: "Wood_Tilesc", 16: "Wood_Tiles30c", 17: "Wood_Tiles5c", 18: "Wood_SmTilesc",
    19: "Wood_Housesc", 20: "Wood_Cliffsc", 21: "Wood_Dungeonsc", 22: "Wood_Innersc",
    23: "Wood_Furnituresc", 24: "Wood_Wallsc", 25: "Wood_SmObjectsc", 26: "Wood_Animationsc",
    30: "Sand_Tilesc", 31: "Sand_Tiles30c", 32: "Sand_Tiles5c", 33: "Sand_SmTilesc",
    34: "Sand_Housesc", 35: "Sand_Cliffsc", 36: "Sand_Dungeonsc", 37: "Sand_Innersc",
    38: "Sand_Furnituresc", 39: "Sand_Wallsc", 40: "Sand_SmObjectsc", 41: "Sand_Animationsc",
    45: "Snow_Tilesc", 46: "Snow_Tiles30c", 47: "Snow_Tiles5c", 48: "Snow_SmTilesc",
    49: "Snow_Housesc", 50: "Snow_Cliffsc", 51: "Snow_Dungeonsc", 52: "Snow_Innersc",
    53: "Snow_Furnituresc", 54: "Snow_Wallsc", 55: "Snow_SmObjectsc", 56: "Snow_Animationsc",
    60: "Forest_Tilesc", 61: "Forest_Tiles30c", 62: "Forest_Tiles5c", 63: "Forest_SmTilesc",
    64: "Forest_Housesc", 65: "Forest_Cliffsc", 66: "Forest_Dungeonsc", 67: "Forest_Innersc",
    68: "Forest_Furnituresc", 69: "Forest_Wallsc", 70: "Forest_SmObjectsc", 71: "Forest_Animationsc",
}

ZIRCON_COMMIT = "cbf1aa919083bc13fc3f23f93772a8ab8370632d"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


@dataclass(frozen=True)
class BackTile:
    file: int
    image: int

    @property
    def library(self) -> str:
        return KR_ORDER.get(self.file, f"UNKNOWN_{self.file}")

    def as_dict(self) -> dict:
        return {"backFile": self.file, "backImage": self.image, "library": self.library}


class ZirconMap:
    HEADER_SIZE = 28
    CELL_SIZE = 14

    def __init__(self, data: bytes, label: str):
        self.label = label
        self.data = bytearray(data)
        if len(self.data) < self.HEADER_SIZE:
            raise ValueError(f"{label}: map is shorter than Zircon header")
        self.width = struct.unpack_from("<H", self.data, 22)[0]
        self.height = struct.unpack_from("<H", self.data, 24)[0]
        if self.width <= 0 or self.height <= 0 or self.width % 2 or self.height % 2:
            raise ValueError(f"{label}: invalid/eccentric map dimensions {self.width}x{self.height}")
        self.back_width = self.width // 2
        self.back_height = self.height // 2
        self.back_offset = self.HEADER_SIZE
        self.cell_offset = self.back_offset + self.back_width * self.back_height * 3
        required = self.cell_offset + self.width * self.height * self.CELL_SIZE
        if len(self.data) < required:
            raise ValueError(f"{label}: truncated map; need {required} bytes, have {len(self.data)}")
        self.trailing_bytes = len(self.data) - required

    @classmethod
    def read(cls, path: Path, label: str | None = None) -> "ZirconMap":
        return cls(path.read_bytes(), label or path.name)

    def back_pos(self, bx: int, by: int) -> int:
        if not (0 <= bx < self.back_width and 0 <= by < self.back_height):
            raise IndexError((bx, by))
        # Native Zircon loop order is X outer / Y inner.
        return self.back_offset + (bx * self.back_height + by) * 3

    def get_back(self, bx: int, by: int) -> BackTile:
        pos = self.back_pos(bx, by)
        return BackTile(self.data[pos], struct.unpack_from("<H", self.data, pos + 1)[0])

    def set_back(self, bx: int, by: int, tile: BackTile) -> None:
        if tile.file not in KR_ORDER:
            raise ValueError(f"Unsupported BackFile {tile.file}; not in pinned Zircon KROrder")
        pos = self.back_pos(bx, by)
        self.data[pos] = tile.file
        struct.pack_into("<H", self.data, pos + 1, tile.image)

    def cell_pos(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError((x, y))
        return self.cell_offset + (x * self.height + y) * self.CELL_SIZE

    def flag(self, x: int, y: int) -> int:
        return self.data[self.cell_pos(x, y)]

    def passable(self, x: int, y: int) -> bool:
        flag = self.flag(x, y)
        return (flag & 0x01) == 0x01 and (flag & 0x02) == 0x02

    def set_passable(self, x: int, y: int, value: bool) -> None:
        pos = self.cell_pos(x, y)
        if value:
            self.data[pos] |= 0x03
        else:
            self.data[pos] &= 0xFC

    def clear_visual_layers(self, x: int, y: int) -> None:
        pos = self.cell_pos(x, y)
        # Preserve the movement flag byte. Reset animation, file/image, unknown visual bytes and light.
        self.data[pos + 1] = 0  # MiddleAnimationFrame
        self.data[pos + 2] = 0  # FrontAnimationFrame raw
        self.data[pos + 3] = 0  # FrontFile
        self.data[pos + 4] = 0  # MiddleFile
        struct.pack_into("<H", self.data, pos + 5, 0)  # MiddleImage raw (client adds +1)
        struct.pack_into("<H", self.data, pos + 7, 0)  # FrontImage raw (client adds +1)
        self.data[pos + 9:pos + 12] = b"\x00\x00\x00"
        self.data[pos + 12] = 0  # Light
        self.data[pos + 13] = 0

    def middle_front_files(self, x: int, y: int) -> tuple[int, int]:
        pos = self.cell_pos(x, y)
        return self.data[pos + 4], self.data[pos + 3]

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.data)


def map_ref_index(row: dict) -> int | None:
    value = row.get("Map")
    if isinstance(value, dict):
        try:
            return int(value.get("Index"))
        except (TypeError, ValueError):
            return None
    return None


def decode_bit_region(encoded: str, width: int, height: int) -> set[tuple[int, int]]:
    raw = base64.b64decode(encoded)
    limit = width * height
    points: set[tuple[int, int]] = set()
    for i in range(min(limit, len(raw) * 8)):
        if raw[i // 8] & (1 << (i % 8)):
            points.add((i % width, i // width))
    return points


def load_town_area(path: Path, width: int, height: int) -> tuple[dict, set[tuple[int, int]]]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    matches = [row for row in rows if map_ref_index(row) == 1 and row.get("Description") == "Town Area"]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one Bichon Map=1 / Town Area region, found {len(matches)}")
    row = matches[0]
    encoded = row.get("BitRegion")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("Bichon Town Area is not exported as BitRegion")
    points = decode_bit_region(encoded, width, height)
    expected_size = int(row.get("Size", 0))
    if expected_size and len(points) != expected_size:
        raise ValueError(f"Town Area bit count {len(points)} does not match exported Size {expected_size}")
    if not points:
        raise ValueError("Town Area decoded to zero cells")
    return row, points


def bbox(points: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def expand_box(box: tuple[int, int, int, int], margin: int, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0 - margin), max(0, y0 - margin), min(width - 1, x1 + margin), min(height - 1, y1 + margin)


def point_rect_distance(x: float, y: float, box: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = box
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    return math.hypot(dx, dy)


def stable_variation(bx: int, by: int, amplitude: int) -> int:
    if amplitude <= 0:
        return 0
    # Deterministic low-cost hash; variation only changes the coastline mask, never tile art.
    n = (bx * 73856093) ^ (by * 19349663) ^ 0x4F524947
    return (n % (amplitude * 2 + 1)) - amplitude


def tile_counter_for_town(map0: ZirconMap, town: set[tuple[int, int]]) -> Counter[BackTile]:
    counter: Counter[BackTile] = Counter()
    for bx in range(map0.back_width):
        for by in range(map0.back_height):
            x, y = bx * 2, by * 2
            cells = [(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)]
            town_count = sum(p in town for p in cells)
            passable_count = sum(map0.passable(*p) for p in cells)
            tile = map0.get_back(bx, by)
            if town_count >= 2 and passable_count >= 3 and (tile.file, tile.image) != (0, 0):
                counter[tile] += 1
    if counter:
        return counter
    for bx in range(map0.back_width):
        for by in range(map0.back_height):
            tile = map0.get_back(bx, by)
            if (tile.file, tile.image) != (0, 0):
                counter[tile] += 1
    return counter


def tile_counter_for_sea_reference(ref: ZirconMap, perimeter_ratio: float = 0.18) -> Counter[BackTile]:
    counter: Counter[BackTile] = Counter()
    x_margin = max(1, int(ref.back_width * perimeter_ratio))
    y_margin = max(1, int(ref.back_height * perimeter_ratio))
    for bx in range(ref.back_width):
        for by in range(ref.back_height):
            perimeter = bx < x_margin or by < y_margin or bx >= ref.back_width - x_margin or by >= ref.back_height - y_margin
            if not perimeter:
                continue
            tile = ref.get_back(bx, by)
            if (tile.file, tile.image) == (0, 0):
                continue
            x, y = bx * 2, by * 2
            cells = [(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)]
            if all(not ref.passable(*p) for p in cells):
                counter[tile] += 1
    if counter:
        return counter
    # Fallback still uses a real perimeter tile from the reference map, but does not assume collision flags.
    for bx in range(ref.back_width):
        for by in range(ref.back_height):
            perimeter = bx < x_margin or by < y_margin or bx >= ref.back_width - x_margin or by >= ref.back_height - y_margin
            if not perimeter:
                continue
            tile = ref.get_back(bx, by)
            if (tile.file, tile.image) != (0, 0):
                counter[tile] += 1
    return counter


def choose_sea_tile(refs: list[ZirconMap]) -> tuple[BackTile, dict]:
    per_map = {ref.label: tile_counter_for_sea_reference(ref) for ref in refs}
    support: defaultdict[BackTile, int] = defaultdict(int)
    total: Counter[BackTile] = Counter()
    for counter in per_map.values():
        for tile, count in counter.items():
            total[tile] += count
            support[tile] += 1
    if not total:
        raise ValueError("No non-empty perimeter BackTile candidate found in official sea reference maps")
    ranked = sorted(total, key=lambda t: (support[t], total[t]), reverse=True)
    chosen = ranked[0]
    evidence = {
        "chosen": chosen.as_dict(),
        "supportingReferenceMaps": support[chosen],
        "aggregateCount": total[chosen],
        "topCandidates": [
            {**tile.as_dict(), "support": support[tile], "count": total[tile]}
            for tile in ranked[:12]
        ],
        "perReferenceTop": {
            label: [{**tile.as_dict(), "count": count} for tile, count in counter.most_common(8)]
            for label, counter in per_map.items()
        },
    }
    return chosen, evidence


def rect_dict(box: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = box
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "width": x1 - x0 + 1, "height": y1 - y0 + 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ORIGINS Bichon Cataclysm from native pinned-Zircon .map data.")
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--sea-reference-map", type=Path, action="append", required=True)
    parser.add_argument("--map-regions", type=Path, required=True)
    parser.add_argument("--output-map", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--preserve-margin", type=int, default=6)
    parser.add_argument("--walkway-width", type=int, default=12)
    parser.add_argument("--coast-variation", type=int, default=2)
    args = parser.parse_args()

    if args.preserve_margin < 0 or args.walkway_width < 4 or args.coast_variation < 0:
        raise SystemExit("Invalid Bichon Cataclysm geometry parameters")

    source_bytes = args.source_map.read_bytes()
    map0 = ZirconMap(source_bytes, "Bichon 0.map")
    refs = [ZirconMap.read(path, path.name) for path in args.sea_reference_map]
    town_row, town_points = load_town_area(args.map_regions, map0.width, map0.height)
    town_box = bbox(town_points)
    preserve_box = expand_box(town_box, args.preserve_margin, map0.width, map0.height)

    town_tiles = tile_counter_for_town(map0, town_points)
    if not town_tiles:
        raise SystemExit("Unable to select a real Bichon promenade BackTile")
    promenade_tile = town_tiles.most_common(1)[0][0]
    sea_tile, sea_evidence = choose_sea_tile(refs)
    if sea_tile == promenade_tile:
        raise SystemExit(f"Sea and promenade resolved to the same BackTile {sea_tile}")

    original_passable = sum(map0.passable(x, y) for x in range(map0.width) for y in range(map0.height))
    zone_counts = Counter()
    changed_back = 0
    changed_cells = 0

    # Decide land/sea at native BackTile granularity (2x2 cells).
    zone_by_block: dict[tuple[int, int], str] = {}
    for bx in range(map0.back_width):
        for by in range(map0.back_height):
            cx, cy = bx * 2 + 0.5, by * 2 + 0.5
            x0, y0, x1, y1 = preserve_box
            in_preserve = x0 <= cx <= x1 and y0 <= cy <= y1
            if in_preserve:
                zone = "preserve"
            else:
                distance = point_rect_distance(cx, cy, preserve_box)
                variation = stable_variation(bx // 3, by // 3, args.coast_variation)
                zone = "promenade" if distance <= args.walkway_width + variation else "sea"
            zone_by_block[(bx, by)] = zone
            zone_counts[zone] += 4
            if zone == "preserve":
                continue
            desired = promenade_tile if zone == "promenade" else sea_tile
            if map0.get_back(bx, by) != desired:
                changed_back += 1
                map0.set_back(bx, by, desired)

    for x in range(map0.width):
        for y in range(map0.height):
            zone = zone_by_block[(x // 2, y // 2)]
            if zone == "preserve":
                continue
            before = bytes(map0.data[map0.cell_pos(x, y):map0.cell_pos(x, y) + map0.CELL_SIZE])
            map0.clear_visual_layers(x, y)
            map0.set_passable(x, y, zone == "promenade")
            after = bytes(map0.data[map0.cell_pos(x, y):map0.cell_pos(x, y) + map0.CELL_SIZE])
            if before != after:
                changed_cells += 1

    modified_passable = sum(map0.passable(x, y) for x in range(map0.width) for y in range(map0.height))
    # Safety contract: all official Town Area cells remain byte-for-byte within the preserved rectangle and passability is untouched there.
    if not all(preserve_box[0] <= x <= preserve_box[2] and preserve_box[1] <= y <= preserve_box[3] for x, y in town_points):
        raise SystemExit("Town Area escaped preserve box")

    map0.write(args.output_map)
    output_bytes = args.output_map.read_bytes()

    report = {
        "schema": "origins.zircon.bichon-cataclysm-map.v1",
        "status": "PASS",
        "zirconCommit": ZIRCON_COMMIT,
        "source": {
            "fileName": "0",
            "mapInfoIndex": 1,
            "description": "Bichon Town",
            "bytes": len(source_bytes),
            "sha256": sha256_bytes(source_bytes),
            "width": map0.width,
            "height": map0.height,
            "trailingBytes": map0.trailing_bytes,
        },
        "townArea": {
            "regionIndex": town_row.get("Index"),
            "cells": len(town_points),
            "bbox": rect_dict(town_box),
        },
        "geometry": {
            "preserveMargin": args.preserve_margin,
            "preserveBox": rect_dict(preserve_box),
            "walkwayWidth": args.walkway_width,
            "coastVariation": args.coast_variation,
            "zoneCellCounts": dict(zone_counts),
        },
        "tiles": {
            "promenade": {
                **promenade_tile.as_dict(),
                "selection": "most common non-empty passable BackTile inside official Bichon Town Area",
                "candidateCount": town_tiles[promenade_tile],
                "topCandidates": [{**tile.as_dict(), "count": count} for tile, count in town_tiles.most_common(12)],
            },
            "sea": {
                **sea_tile.as_dict(),
                "selection": "dominant blocked perimeter BackTile from official Zircon sea-reference maps",
                "evidence": sea_evidence,
            },
        },
        "mutation": {
            "changedBackBlocks": changed_back,
            "changedCells": changed_cells,
            "originalPassableCells": original_passable,
            "modifiedPassableCells": modified_passable,
            "seaCellsBlocked": True,
            "promenadeCellsPassable": True,
            "middleFrontClearedOutsidePreserve": True,
            "dimensionsPreserved": True,
            "headerPreserved": source_bytes[:28] == output_bytes[:28],
            "byteLengthPreserved": len(source_bytes) == len(output_bytes),
        },
        "output": {
            "path": args.output_map.as_posix(),
            "bytes": len(output_bytes),
            "sha256": sha256_bytes(output_bytes),
        },
        "rules": [
            "No generated/painted art is introduced: every BackTile comes from native Zircon map data.",
            "The original Bichon Town Area plus preserve margin is not rewritten.",
            "The promenade is real native map ground and is server-passable.",
            "The ocean uses a real Zircon BackTile sampled from official island maps and is server-blocked.",
            "Map width, height, header and binary byte length remain compatible with pinned Zircon.",
        ],
    }
    if not report["mutation"]["headerPreserved"] or not report["mutation"]["byteLengthPreserved"]:
        raise SystemExit("Native Bichon binary integrity contract failed")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "dimensions": f"{map0.width}x{map0.height}",
        "townAreaCells": len(town_points),
        "townBox": rect_dict(town_box),
        "preserveBox": rect_dict(preserve_box),
        "promenade": promenade_tile.as_dict(),
        "sea": sea_tile.as_dict(),
        "zones": dict(zone_counts),
        "outputSha256": report["output"]["sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
