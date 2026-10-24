#!/usr/bin/env python3
"""Minimal index-preserving Zircon legacy .Zl writer.

This writer intentionally targets the legacy DXT1 container because the current
ORIGINS repo already contains a reader that supports both legacy ZL and ZL2.
The writer keeps image slot IDs and X/Y offsets exactly as supplied.

It does NOT infer animation semantics and does NOT compact sparse slot IDs.
"""
from __future__ import annotations

import csv
import math
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from PIL import Image


class ZlWriterError(RuntimeError):
    pass


@dataclass
class FrameMeta:
    index: int
    width: int = 0
    height: int = 0
    offset_x: int = 0
    offset_y: int = 0
    shadow_type: int = 0
    shadow_width: int = 0
    shadow_height: int = 0
    shadow_offset_x: int = 0
    shadow_offset_y: int = 0
    overlay_width: int = 0
    overlay_height: int = 0
    png: Optional[Path] = None


def _int(v, default=0):
    if v is None:
        return default
    s = str(v).strip()
    if not s:
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def _lookup(row: Dict[str, str], *names: str, default=""):
    # Case/underscore-insensitive column lookup so old analyzer CSV variants work.
    normalized = {re.sub(r"[^a-z0-9]", "", k.lower()): v for k, v in row.items()}
    for name in names:
        k = re.sub(r"[^a-z0-9]", "", name.lower())
        if k in normalized:
            return normalized[k]
    return default


def read_image_metadata(csv_path: Path) -> Dict[int, FrameMeta]:
    if not csv_path.exists():
        raise ZlWriterError(f"No existe IMAGE_METADATA.csv: {csv_path}")

    out: Dict[int, FrameMeta] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            idx = _int(_lookup(row, "index", "id", "image_index", "source_index"), -1)
            if idx < 0:
                continue
            out[idx] = FrameMeta(
                index=idx,
                width=_int(_lookup(row, "width", "w")),
                height=_int(_lookup(row, "height", "h")),
                offset_x=_int(_lookup(row, "x", "offset_x", "offsetx")),
                offset_y=_int(_lookup(row, "y", "offset_y", "offsety")),
                shadow_type=_int(_lookup(row, "shadow", "shadow_type", "shadowtype")),
                shadow_width=_int(_lookup(row, "shadow_width", "shadowwidth")),
                shadow_height=_int(_lookup(row, "shadow_height", "shadowheight")),
                shadow_offset_x=_int(_lookup(row, "shadow_x", "shadow_offset_x", "shadowoffsetx")),
                shadow_offset_y=_int(_lookup(row, "shadow_y", "shadow_offset_y", "shadowoffsety")),
                overlay_width=_int(_lookup(row, "overlay_width", "overlaywidth")),
                overlay_height=_int(_lookup(row, "overlay_height", "overlayheight")),
            )
    return out


def discover_pngs(frames_dir: Path) -> Dict[int, Path]:
    if not frames_dir.exists():
        raise ZlWriterError(f"No existe la carpeta de frames: {frames_dir}")
    result: Dict[int, Path] = {}
    for p in frames_dir.rglob("*.png"):
        m = re.search(r"(\d+)(?=\.png$)", p.name, re.IGNORECASE)
        if not m:
            continue
        idx = int(m.group(1))
        # Prefer files directly under FRAMES_PNG if duplicate previews exist.
        if idx not in result or len(p.parts) < len(result[idx].parts):
            result[idx] = p
    return result


def _rgb565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _unpack565(c: int) -> Tuple[int, int, int]:
    r = (c >> 11) & 0x1F
    g = (c >> 5) & 0x3F
    b = c & 0x1F
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def _dist2(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return dr * dr + dg * dg + db * db


def _choose_endpoints(opaque: List[Tuple[int, int, int]]) -> Tuple[int, int]:
    if not opaque:
        return 0, 0
    # Fast stable approximation: farthest pair among channel-extreme candidates.
    candidates = []
    for channel in range(3):
        candidates.append(min(opaque, key=lambda p: p[channel]))
        candidates.append(max(opaque, key=lambda p: p[channel]))
    best = (candidates[0], candidates[0])
    best_d = -1
    for a in candidates:
        for b in candidates:
            d = _dist2(a, b)
            if d > best_d:
                best_d = d
                best = (a, b)
    return _rgb565(*best[0]), _rgb565(*best[1])


def _palette(c0: int, c1: int, transparent_mode: bool):
    a = _unpack565(c0)
    b = _unpack565(c1)
    if transparent_mode:
        # DXT1 3-color mode requires c0 <= c1.
        p2 = tuple((a[i] + b[i]) // 2 for i in range(3))
        return [a, b, p2, (0, 0, 0)]
    p2 = tuple((2 * a[i] + b[i]) // 3 for i in range(3))
    p3 = tuple((a[i] + 2 * b[i]) // 3 for i in range(3))
    return [a, b, p2, p3]


def _compress_dxt1_block(px: List[Tuple[int, int, int, int]]) -> bytes:
    if len(px) != 16:
        raise ValueError("DXT1 block must contain 16 pixels")
    has_alpha = any(a < 128 for _, _, _, a in px)
    opaque = [(r, g, b) for r, g, b, a in px if a >= 128]
    c0, c1 = _choose_endpoints(opaque)

    if has_alpha:
        if c0 > c1:
            c0, c1 = c1, c0
    else:
        if c0 <= c1:
            c0, c1 = c1, c0
        if c0 == c1:
            # Keep 4-color mode for solid blocks.
            if c0 < 0xFFFF:
                c0 += 1
            elif c1 > 0:
                c1 -= 1

    pal = _palette(c0, c1, has_alpha)
    bits = 0
    for i, (r, g, b, a) in enumerate(px):
        if has_alpha and a < 128:
            idx = 3
        else:
            max_idx = 2 if has_alpha else 3
            idx = min(range(max_idx + 1), key=lambda j: _dist2((r, g, b), pal[j]))
        bits |= (idx & 0x3) << (2 * i)
    return struct.pack("<HHI", c0, c1, bits)


def encode_dxt1(image: Image.Image) -> bytes:
    im = image.convert("RGBA")
    w, h = im.size
    if w <= 0 or h <= 0:
        return b""
    out = bytearray()
    pix = im.load()
    bw = (w + 3) // 4
    bh = (h + 3) // 4
    for by in range(bh):
        for bx in range(bw):
            block = []
            for yy in range(4):
                sy = min(by * 4 + yy, h - 1)
                for xx in range(4):
                    sx = min(bx * 4 + xx, w - 1)
                    block.append(pix[sx, sy])
            out.extend(_compress_dxt1_block(block))
    return bytes(out)


def build_legacy_zl(
    metadata_csv: Path,
    frames_dir: Path,
    output_path: Path,
    slot_count: Optional[int] = None,
) -> Dict[str, int]:
    """Build a sparse legacy DXT1 ZL while preserving original frame IDs.

    Return summary dict. Shadow/overlay pixel payloads are not invented. Their
    offsets/dimensions are zeroed unless the body metadata explicitly supplies
    them; this avoids claiming visual data that is not present in the exported
    PNG set.
    """
    metas = read_image_metadata(metadata_csv)
    pngs = discover_pngs(frames_dir)

    if not pngs:
        raise ZlWriterError(f"No se han encontrado PNG numerados en {frames_dir}")

    max_idx = max(max(pngs), max(metas) if metas else 0)
    count = max(max_idx + 1, slot_count or 0)
    if count <= 0:
        raise ZlWriterError("slot_count invalido")

    payloads: Dict[int, bytes] = {}
    final_meta: Dict[int, FrameMeta] = {}
    for idx, png in sorted(pngs.items()):
        im = Image.open(png).convert("RGBA")
        w, h = im.size
        m = metas.get(idx, FrameMeta(index=idx))
        m.png = png
        # Pixel dimensions from actual image are authoritative for the ZL body.
        m.width = w
        m.height = h
        # We only write body pixels in this builder. Do not fabricate shadows.
        m.shadow_width = 0
        m.shadow_height = 0
        m.overlay_width = 0
        m.overlay_height = 0
        payloads[idx] = encode_dxt1(im)
        final_meta[idx] = m

    present_count = len(payloads)
    header_size = 4 + count + (25 * present_count)
    position = 4 + header_size

    positions: Dict[int, int] = {}
    for idx in range(count):
        if idx not in payloads:
            continue
        positions[idx] = position
        position += len(payloads[idx])

    header = bytearray()
    # version 0 legacy = DXT1, count is stored directly.
    header.extend(struct.pack("<i", count))
    for idx in range(count):
        if idx not in payloads:
            header.extend(b"\x00")
            continue
        header.extend(b"\x01")
        m = final_meta[idx]
        header.extend(
            struct.pack(
                "<ihhhhBhhhhhh",
                positions[idx],
                int(m.width), int(m.height),
                int(m.offset_x), int(m.offset_y),
                int(m.shadow_type) & 0xFF,
                0, 0,
                int(m.shadow_offset_x), int(m.shadow_offset_y),
                0, 0,
            )
        )

    if len(header) != header_size:
        raise ZlWriterError(f"Internal header size mismatch {len(header)} != {header_size}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        f.write(struct.pack("<i", header_size))
        f.write(header)
        for idx in range(count):
            if idx in payloads:
                f.write(payloads[idx])

    return {
        "slot_count": count,
        "present_count": present_count,
        "output_bytes": output_path.stat().st_size,
    }


__all__ = [
    "FrameMeta",
    "ZlWriterError",
    "read_image_metadata",
    "discover_pngs",
    "encode_dxt1",
    "build_legacy_zl",
]
