#!/usr/bin/env python3
"""Extract only the Crystal .Lib images actually used by two Mir2 2010 maps.

Designed for ORIGINS Map Engine V1. No third-party Python packages required.

Supports Crystal Lib v1 (DXT1 payloads) and v2/v3 (GZip BGRA payloads).
The v1 reader follows Suprcode/Crystal's historical LibraryEditor format.

Example (Windows / Cursor terminal):
    python tools/crystal-map-importer/extract_theme_assets.py \
      --data "D:\\Crystal\\Client\\Data" \
      --maps "D:\\Crystal.Database\\Jev\\Maps" \
      --standard d501.map --king d515.map \
      --theme zuma \
      --out origins/map-engine/themes/zuma/extracted
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import struct
import zlib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass
class ImageMeta:
    library: str
    image_id: int
    category: str
    width: int
    height: int
    offset_x: int
    offset_y: int
    shadow_x: int
    shadow_y: int
    shadow: int
    png: str


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    if len(rgba) != width * height * 4:
        raise ValueError(f"RGBA size mismatch: {len(rgba)} != {width * height * 4}")
    rows = bytearray()
    stride = width * 4
    for y in range(height):
        rows.append(0)
        start = y * stride
        rows.extend(rgba[start : start + stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    payload = (
        PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def bgra_to_rgba(raw: bytes, width: int, height: int) -> bytes:
    expected = width * height * 4
    if len(raw) != expected:
        raise ValueError(f"Unexpected decompressed image size {len(raw)}; expected {expected}")
    out = bytearray(expected)
    for pos in range(0, expected, 4):
        b, g, r, a = raw[pos : pos + 4]
        out[pos : pos + 4] = bytes((r, g, b, a))
    return bytes(out)


def _rgb565(value: int) -> Tuple[int, int, int, int]:
    r = ((value >> 11) & 0x1F) * 255 // 31
    g = ((value >> 5) & 0x3F) * 255 // 63
    b = (value & 0x1F) * 255 // 31
    return r, g, b, 255


def decompress_dxt1(payload: bytes, width: int, height: int) -> bytes:
    """Decode a Crystal Lib v1 DXT1 image to cropped RGBA.

    Historical Crystal padded v1 images to 4x4 block boundaries before DXT1
    compression. The metadata keeps the logical Width/Height, so decode the
    padded surface and crop back to those logical dimensions.
    """
    if width <= 0 or height <= 0:
        return b""

    padded_w = (width + 3) & ~3
    padded_h = (height + 3) & ~3
    blocks_x = padded_w // 4
    blocks_y = padded_h // 4
    required = blocks_x * blocks_y * 8
    if len(payload) < required:
        raise ValueError(f"DXT1 payload too short: {len(payload)} < {required}")

    surface = bytearray(padded_w * padded_h * 4)
    src = 0

    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            c0, c1, indices = struct.unpack_from("<HHI", payload, src)
            src += 8

            p0 = _rgb565(c0)
            p1 = _rgb565(c1)
            if c0 > c1:
                p2 = (
                    (2 * p0[0] + p1[0]) // 3,
                    (2 * p0[1] + p1[1]) // 3,
                    (2 * p0[2] + p1[2]) // 3,
                    255,
                )
                p3 = (
                    (p0[0] + 2 * p1[0]) // 3,
                    (p0[1] + 2 * p1[1]) // 3,
                    (p0[2] + 2 * p1[2]) // 3,
                    255,
                )
            else:
                p2 = (
                    (p0[0] + p1[0]) // 2,
                    (p0[1] + p1[1]) // 2,
                    (p0[2] + p1[2]) // 2,
                    255,
                )
                p3 = (0, 0, 0, 0)

            palette = (p0, p1, p2, p3)
            for pixel in range(16):
                colour = palette[(indices >> (2 * pixel)) & 0x03]
                px = block_x * 4 + (pixel & 3)
                py = block_y * 4 + (pixel >> 2)
                dst = (py * padded_w + px) * 4
                surface[dst : dst + 4] = bytes(colour)

    cropped = bytearray(width * height * 4)
    row_src = padded_w * 4
    row_dst = width * 4
    for y in range(height):
        cropped[y * row_dst : (y + 1) * row_dst] = surface[y * row_src : y * row_src + row_dst]
    return bytes(cropped)


def resolve_wemade_mir2_dir(data_arg: Path) -> Path:
    candidates = [
        data_arg,
        data_arg / "Map" / "WemadeMir2",
        data_arg / "Data" / "Map" / "WemadeMir2",
    ]
    for candidate in candidates:
        if (candidate / "Tiles.Lib").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find Data/Map/WemadeMir2. Point --data to the Crystal Data folder "
        "or directly to the WemadeMir2 folder."
    )


def library_name_for_slot(slot: int) -> str:
    if slot == 0:
        return "Tiles.Lib"
    if slot == 1:
        return "SmTiles.Lib"
    if slot == 2:
        return "Objects.Lib"
    if 3 <= slot <= 28:
        return f"Objects{slot - 1}.Lib"
    if slot == 90:
        return "Objects_32bit.Lib"
    raise ValueError(f"Unsupported WemadeMir2 library slot: {slot}")


def parse_mir2_2010(path: Path) -> Tuple[int, int, Dict[int, Counter], Counter]:
    data = path.read_bytes()
    if len(data) < 54:
        raise ValueError(f"{path.name}: file too small")
    if not (data[0] == 0x10 and data[2] == 0x61 and data[7] == 0x31 and data[14] == 0x31):
        raise ValueError(f"{path.name}: Map Engine V1 extractor expects Mir2 2010 format")

    xor_value = u16(data, 23)
    width = u16(data, 21) ^ xor_value
    height = u16(data, 25) ^ xor_value
    expected = 54 + width * height * 15
    if len(data) < expected:
        raise ValueError(f"{path.name}: truncated map ({len(data)} < {expected})")

    used: Dict[int, Counter] = {0: Counter()}
    doors: Counter = Counter()
    offset = 54

    for _x in range(width):
        for _y in range(height):
            back_image = (u32(data, offset) ^ 0xAA38AA38) & 0xFFFFFFFF
            front_image = (u16(data, offset + 6) ^ xor_value) & 0xFFFF
            door_index = data[offset + 8] & 0x7F
            front_index = data[offset + 12] + 2

            if front_index == 102:
                front_index = 90
            if front_index >= 255:
                front_index = -1

            tile_id = back_image & 0x1FFFFFFF
            if tile_id:
                used[0][tile_id] += 1

            object_id = front_image & 0x7FFF
            if front_index >= 0 and object_id:
                used.setdefault(front_index, Counter())[object_id] += 1

            doors[door_index] += 1
            offset += 15

    return width, height, used, doors


class CrystalLib:
    def __init__(self, path: Path):
        self.path = path
        self.file = path.open("rb")
        self.version = self._read_i32()
        if self.version not in (1, 2, 3):
            raise ValueError(f"{path.name}: unsupported Lib version {self.version}")
        self.count = self._read_i32()
        if self.count < 0 or self.count > 10_000_000:
            raise ValueError(f"{path.name}: invalid image count {self.count}")
        self.frame_seek = self._read_i32() if self.version >= 3 else 0
        self.offsets = [self._read_i32() for _ in range(self.count)]

    def _read_i32(self) -> int:
        raw = self.file.read(4)
        if len(raw) != 4:
            raise EOFError(self.path)
        return struct.unpack("<i", raw)[0]

    def close(self) -> None:
        self.file.close()

    def extract(self, image_id: int) -> Tuple[int, int, int, int, int, int, int, bytes]:
        if image_id < 0 or image_id >= self.count:
            raise IndexError(f"{self.path.name}: image {image_id} outside 0..{self.count - 1}")
        image_offset = self.offsets[image_id]
        if image_offset <= 0:
            raise ValueError(f"{self.path.name}: image {image_id} has no payload")

        self.file.seek(image_offset)
        header = self.file.read(17)
        if len(header) != 17:
            raise EOFError(f"{self.path.name}: truncated image header {image_id}")

        width, height, x, y, shadow_x, shadow_y, shadow, length = struct.unpack("<hhhhhhBi", header)
        if width <= 0 or height <= 0 or length <= 0:
            raise ValueError(f"{self.path.name}: empty image {image_id}")

        compressed = self.file.read(length)
        if len(compressed) != length:
            raise EOFError(f"{self.path.name}: truncated image payload {image_id}")

        if self.version == 1:
            rgba = decompress_dxt1(compressed, width, height)
        else:
            raw = gzip.decompress(compressed)
            rgba = bgra_to_rgba(raw, width, height)
        return width, height, x, y, shadow_x, shadow_y, shadow, rgba


def category_sets(standard: Counter, king: Counter) -> Dict[str, List[int]]:
    a, b = set(standard), set(king)
    return {
        "common": sorted(a & b),
        "standard_only": sorted(a - b),
        "kingroom_only": sorted(b - a),
    }


def generate_gallery(out_dir: Path, manifest: dict) -> None:
    cards = []
    for library, library_data in manifest["libraries"].items():
        for category in ("kingroom_only", "common", "standard_only"):
            images = library_data["images"].get(category, [])
            if not images:
                continue
            cards.append(f"<h2>{html.escape(library)} — {html.escape(category)} ({len(images)})</h2>")
            cards.append('<div class="grid">')
            for item in images:
                src = html.escape(item["png"].replace("\\", "/"))
                label = f'{library} #{item["image_id"]}'
                cards.append(
                    '<div class="card">'
                    f'<div class="image"><img loading="lazy" src="{src}" alt="{html.escape(label)}"></div>'
                    f'<strong>{html.escape(label)}</strong>'
                    f'<small>{item["width"]}×{item["height"]} &nbsp; offset {item["offset_x"]},{item["offset_y"]}</small>'
                    '</div>'
                )
            cards.append("</div>")

    page = """<!doctype html>
<html><head><meta charset="utf-8"><title>ORIGINS Theme Asset Gallery</title>
<style>
body{font-family:system-ui,sans-serif;background:#151515;color:#eee;margin:24px}h1,h2{margin:24px 0 12px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}.card{background:#222;border:1px solid #444;padding:8px;border-radius:8px;overflow:hidden}.image{height:160px;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#333 0 25%,#292929 0 50%) 50%/20px 20px;overflow:hidden}.image img{max-width:100%;max-height:100%;image-rendering:pixelated}.card strong,.card small{display:block;margin-top:6px}.card small{color:#aaa}
</style></head><body>
<h1>ORIGINS — extracted Crystal theme assets</h1>
<p>Review visually before assigning WALL/FLOOR/DOOR/OBSTACLE/ALTAR roles. Never mix assets from another theme.</p>
""" + "\n".join(cards) + "\n</body></html>"
    (out_dir / "gallery.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path, help="Crystal Data folder or Data/Map/WemadeMir2")
    parser.add_argument("--maps", required=True, type=Path, help="Folder containing the reference .map files")
    parser.add_argument("--standard", default="d501.map")
    parser.add_argument("--king", default="d515.map")
    parser.add_argument("--theme", default="zuma")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    lib_dir = resolve_wemade_mir2_dir(args.data)
    standard_path = args.maps / args.standard
    king_path = args.maps / args.king
    sw, sh, standard_used, standard_doors = parse_mir2_2010(standard_path)
    kw, kh, king_used, king_doors = parse_mir2_2010(king_path)

    all_slots = sorted(set(standard_used) | set(king_used))
    manifest = {
        "theme_id": args.theme,
        "source_family": "WemadeMir2",
        "reference_maps": {
            args.standard: {"role": "STANDARD_FLOOR_REFERENCE", "width": sw, "height": sh, "door_counts": dict(standard_doors)},
            args.king: {"role": "KING_ROOM_REFERENCE", "width": kw, "height": kh, "door_counts": dict(king_doors)},
        },
        "libraries": {},
    }

    args.out.mkdir(parents=True, exist_ok=True)

    for slot in all_slots:
        standard_counter = standard_used.get(slot, Counter())
        king_counter = king_used.get(slot, Counter())
        if not standard_counter and not king_counter:
            continue

        library_name = library_name_for_slot(slot)
        library_path = lib_dir / library_name
        if not library_path.exists():
            raise FileNotFoundError(f"Required library not found: {library_path}")

        categories = category_sets(standard_counter, king_counter)
        lib_manifest = {
            "slot": slot,
            "path": str(library_path),
            "counts": {key: len(value) for key, value in categories.items()},
            "standard_frequency": dict(standard_counter),
            "king_frequency": dict(king_counter),
            "images": {key: [] for key in categories},
        }

        lib = CrystalLib(library_path)
        try:
            for category, ids in categories.items():
                category_dir = args.out / category / library_path.stem
                for image_id in ids:
                    try:
                        width, height, x, y, sx, sy, shadow, rgba = lib.extract(image_id)
                    except (ValueError, IndexError) as exc:
                        print(f"SKIP {library_name} #{image_id}: {exc}")
                        continue
                    png_path = category_dir / f"{image_id:05d}.png"
                    write_rgba_png(png_path, width, height, rgba)
                    rel = png_path.relative_to(args.out).as_posix()
                    meta = ImageMeta(library_name, image_id, category, width, height, x, y, sx, sy, shadow, rel)
                    lib_manifest["images"][category].append(asdict(meta))
        finally:
            lib.close()

        manifest["libraries"][library_name] = lib_manifest
        print(
            f"{library_name}: common={len(categories['common'])}, "
            f"standard_only={len(categories['standard_only'])}, "
            f"kingroom_only={len(categories['kingroom_only'])}"
        )

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    generate_gallery(args.out, manifest)
    print(f"Done. Open: {args.out / 'gallery.html'}")


if __name__ == "__main__":
    main()
