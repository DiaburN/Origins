#!/usr/bin/env python3
"""Build the full ORIGINS X in-game Zircon UI from original MIR3 .Zl libraries.

No artwork is generated or redrawn. Every visual is decoded from Interface.Zl,
GameInter.Zl or GameInter2.Zl and packed losslessly for the browser. The only
compositing performed mirrors Zircon's own DXButton/DXWindow assembly logic.

Typical use:
    py tools/mir3/build_full_zircon_ui.py

If auto-discovery cannot find the libraries:
    py tools/mir3/build_full_zircon_ui.py --source "C:\\path\\to\\Zircon\\Data"
"""
from __future__ import annotations

import argparse
import io
import json
import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required to decode the original ZL textures; installing it once...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image


class ZLImage:
    def __init__(self, idx: int, **values):
        self.idx = idx
        self.__dict__.update(values)


def dds_image(raw: bytes, width: int, height: int, dxt5: bool) -> Image.Image:
    fourcc = b"DXT5" if dxt5 else b"DXT1"
    block = 16 if dxt5 else 8
    size = ((width + 3) // 4) * ((height + 3) // 4) * block
    raw = raw[:size]
    flags = 0x00081007
    pixel_format = struct.pack("<II4sIIIII", 32, 0x4, fourcc, 0, 0, 0, 0, 0)
    header = (
        struct.pack("<I", 124)
        + struct.pack("<I", flags)
        + struct.pack("<I", height)
        + struct.pack("<I", width)
        + struct.pack("<I", size)
        + struct.pack("<I", 0)
        + struct.pack("<I", 0)
        + struct.pack("<11I", *([0] * 11))
        + pixel_format
        + struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
    )
    return Image.open(io.BytesIO(b"DDS " + header + raw)).convert("RGBA")


def parse_legacy(data: bytes):
    header_size = struct.unpack_from("<i", data, 0)[0]
    header = data[4 : 4 + header_size]
    value = struct.unpack_from("<i", header, 0)[0]
    count = value & 0x1FFFFFF
    version = (value >> 25) & 0x7F
    if version == 0:
        count = value
    pos = 4
    images = []
    for idx in range(count):
        exists = header[pos]
        pos += 1
        if not exists:
            images.append(None)
            continue
        payload_pos, width, height, ox, oy = struct.unpack_from("<ihhhh", header, pos)
        pos += 12
        shadow_type = header[pos]
        pos += 1
        sw, sh, sox, soy, ow, oh = struct.unpack_from("<hhhhhh", header, pos)
        pos += 12
        images.append(
            ZLImage(
                idx,
                pos=payload_pos,
                w=width,
                h=height,
                ox=ox,
                oy=oy,
                shadow_type=shadow_type,
                sw=sw,
                sh=sh,
                sox=sox,
                soy=soy,
                ow=ow,
                oh=oh,
                version=version,
            )
        )
    return version, images


def parse_zl2(data: bytes):
    pos = 3
    version, image_count, atlas_count = struct.unpack_from("<iii", data, pos)
    pos += 12
    _default_compression = data[pos]
    _flags = data[pos + 1]
    pos += 4
    metadata_offset = struct.unpack_from("<q", data, pos)[0]
    pos += 8
    metadata_size = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    index_offset = struct.unpack_from("<q", data, pos)[0]
    pos += 8
    index_size = struct.unpack_from("<i", data, pos)[0]

    index_data = data[index_offset : index_offset + index_size]
    entry_count = struct.unpack_from("<i", index_data, 0)[0]
    pos = 4
    entries = {}
    for _ in range(entry_count):
        entry_type = index_data[pos]
        ident, uncompressed, compressed = struct.unpack_from("<iii", index_data, pos + 1)
        offset = struct.unpack_from("<q", index_data, pos + 13)[0]
        compression = index_data[pos + 21]
        codec = index_data[pos + 22]
        pos += 23
        entries[ident] = (entry_type, uncompressed, compressed, offset, compression, codec)

    metadata = data[metadata_offset : metadata_offset + metadata_size]
    metadata_version, count, _atlas_group_count, _atlas_page_size = struct.unpack_from("<iiii", metadata, 0)
    pos = 16
    images = []
    for idx in range(count):
        exists = metadata[pos]
        pos += 1
        if not exists:
            images.append(None)
            continue
        payload_pos, width, height, ox, oy = struct.unpack_from("<ihhhh", metadata, pos)
        pos += 12
        shadow_type = metadata[pos]
        pos += 1
        sw, sh, sox, soy, ow, oh = struct.unpack_from("<hhhhhh", metadata, pos)
        pos += 12
        atlas = struct.unpack_from("<i", metadata, pos)[0]
        pos += 4
        source_rect = struct.unpack_from("<hhhh", metadata, pos)
        pos += 8
        visible_bounds = struct.unpack_from("<hhhh", metadata, pos)
        pos += 8
        codecs = tuple(metadata[pos : pos + 3])
        pos += 3
        preferences = tuple(metadata[pos : pos + 3])
        pos += 3
        sizes = struct.unpack_from("<9i", metadata, pos)
        pos += 36
        images.append(
            ZLImage(
                idx,
                pos=payload_pos,
                w=width,
                h=height,
                ox=ox,
                oy=oy,
                shadow_type=shadow_type,
                sw=sw,
                sh=sh,
                sox=sox,
                soy=soy,
                ow=ow,
                oh=oh,
                version=metadata_version,
                atlas=atlas,
                src=source_rect,
                vis=visible_bounds,
                codecs=codecs,
                prefs=preferences,
                sizes=sizes,
            )
        )
    return version, images, entries


def read_zl2_payload(data: bytes, entry):
    _entry_type, uncompressed_size, compressed_size, offset, compression, _codec = entry
    payload = data[offset : offset + compressed_size]
    if compression == 0:
        decoded = payload
    elif compression in (1, 2):
        decoded = zlib.decompress(payload, -15)
    else:
        raise ValueError(f"Unsupported ZL2 payload compression: {compression}")
    if len(decoded) != uncompressed_size:
        raise ValueError(f"ZL2 payload size mismatch: {len(decoded)} != {uncompressed_size}")
    return decoded


class ZLLibrary:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if self.data[:3] == b"ZL2":
            self.mode = "zl2"
            self.version, self.images, self.entries = parse_zl2(self.data)
        else:
            self.mode = "legacy"
            self.version, self.images = parse_legacy(self.data)
            self.entries = None

    def decode(self, index: int) -> Image.Image:
        if index < 0 or index >= len(self.images) or self.images[index] is None:
            raise ValueError(f"Missing index {index} in {self.path.name}")
        meta = self.images[index]
        if self.mode == "legacy":
            block = 16 if self.version == 1 else 8
            size = ((meta.w + 3) // 4) * ((meta.h + 3) // 4) * block
            return dds_image(self.data[meta.pos : meta.pos + size], meta.w, meta.h, self.version == 1)

        if meta.pos < 0 or meta.pos not in self.entries:
            raise ValueError(f"Missing payload for index {index} in {self.path.name}")
        payload = read_zl2_payload(self.data, self.entries[meta.pos])
        stored_size = meta.sizes[0]
        codec = meta.codecs[0]
        payload = payload[:stored_size]
        if codec == 4:
            return Image.open(io.BytesIO(payload)).convert("RGBA")
        if codec in (0, 1):
            return dds_image(payload, meta.w, meta.h, codec == 1)
        if codec == 2:
            return Image.frombytes("RGBA", (meta.w, meta.h), payload[: meta.w * meta.h * 4], "raw", "BGRA")
        raise ValueError(f"Unsupported ZL image codec {codec} at index {index} in {self.path.name}")


def candidate_roots(repo: Path, explicit: Path | None):
    roots = []
    if explicit:
        roots.append(explicit.resolve())
    roots += [repo, repo.parent]
    home = Path.home()
    roots += [home / "Desktop", home / "Downloads"]
    seen = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        yield resolved


def find_library(repo: Path, explicit: Path | None, names: list[str]) -> Path:
    for root in candidate_roots(repo, explicit):
        for name in names:
            direct = root / name
            if direct.is_file():
                return direct
        for current, dirs, files in os.walk(root):
            rel_depth = len(Path(current).relative_to(root).parts)
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"} and not d.startswith(".")]
            if rel_depth > 5:
                dirs[:] = []
                continue
            lower = {f.lower(): f for f in files}
            for name in names:
                hit = lower.get(name.lower())
                if hit:
                    return Path(current) / hit
    raise FileNotFoundError(" / ".join(names))


def save_lossless(image: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, "WEBP", lossless=True, method=6)


def stretch_three(left: Image.Image, middle: Image.Image, right: Image.Image, width: int, height: int) -> Image.Image:
    left = left.convert("RGBA")
    middle = middle.convert("RGBA")
    right = right.convert("RGBA")
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(left, (0, 0))
    middle_width = max(0, width - left.width - right.width)
    if middle_width:
        resized = middle.resize((middle_width, middle.height), Image.Resampling.NEAREST)
        canvas.alpha_composite(resized, (left.width, 0))
    canvas.alpha_composite(right, (width - right.width, 0))
    return canvas


def build_belt_frame(interface: ZLLibrary, width: int = 239, height: int = 54) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (16, 8, 8, 255))
    top = interface.decode(2)
    side = interface.decode(1)
    top_left = interface.decode(25)
    top_right = interface.decode(26)
    bottom_left = interface.decode(8)
    bottom_right = interface.decode(9)

    def stretch(image: Image.Image, w: int, h: int) -> Image.Image:
        return image.resize((w, h), Image.Resampling.NEAREST)

    canvas.alpha_composite(stretch(top, width, top.height), (0, 0))
    y = top.height
    side_height = max(0, height - y)
    canvas.alpha_composite(stretch(side, side.width, side_height), (0, y))
    canvas.alpha_composite(stretch(side, side.width, side_height), (width - side.width, y))
    canvas.alpha_composite(top_left, (0, 0))
    canvas.alpha_composite(top_right, (width - top_right.width, 0))
    canvas.alpha_composite(stretch(top, width, top.height), (0, height - top.height))
    canvas.alpha_composite(bottom_left, (0, height - bottom_left.height))
    canvas.alpha_composite(bottom_right, (width - bottom_right.width, height - bottom_right.height))
    return canvas


def pack(items: list[tuple[str, Image.Image]], path: Path, max_width: int):
    x = y = row_height = 0
    placements = {}
    placed = []
    for name, image in items:
        image = image.convert("RGBA")
        width, height = image.size
        if x and x + width > max_width:
            y += row_height + 2
            x = 0
            row_height = 0
        placements[name] = (x, y, width, height)
        placed.append((image, x, y))
        x += width + 2
        row_height = max(row_height, height)
    atlas_height = max(1, y + row_height)
    atlas = Image.new("RGBA", (max_width, atlas_height), (0, 0, 0, 0))
    for image, px, py in placed:
        atlas.alpha_composite(image, (px, py))
    save_lossless(atlas, path)
    return placements


def build(repo: Path, source: Path | None):
    interface_path = find_library(repo, source, ["Interface.Zl", "Interface(1).Zl"])
    gameinter_path = find_library(repo, source, ["GameInter.Zl", "GameInter(1).Zl"])
    gameinter2_path = find_library(repo, source, ["GameInter2.Zl"])

    print(f"Interface : {interface_path}")
    print(f"GameInter : {gameinter_path}")
    print(f"GameInter2: {gameinter2_path}")

    interface = ZLLibrary(interface_path)
    gameinter = ZLLibrary(gameinter_path)
    gameinter2 = ZLLibrary(gameinter2_path)

    interface_fixed = [15, 60, 61, 62, 160, 161, 162, 163, 164, 165, *range(166, 196), 241, 242, 243]
    gameinter_fixed = [82, 87, 92, 97, 102, 107, 112, 117, 122, 130, 131, 132, 137, 240, 241, 354, 358, 360, 364]
    gameinter2_fixed = [812, 815, 816]

    fixed_items = [(f"interface-{idx}", interface.decode(idx)) for idx in interface_fixed]
    fixed_items += [(f"gameinter-{idx}", gameinter.decode(idx)) for idx in gameinter_fixed]
    fixed_items += [(f"gameinter2-{idx}", gameinter2.decode(idx)) for idx in gameinter2_fixed]
    fixed_items += [
        ("button-default-100", stretch_three(interface.decode(16), interface.decode(18), interface.decode(17), 100, 24)),
        ("button-default-172", stretch_three(interface.decode(16), interface.decode(18), interface.decode(17), 172, 27)),
        ("button-small-68", stretch_three(interface.decode(41), interface.decode(43), interface.decode(42), 68, 18)),
        ("tab-selected-60", stretch_three(interface.decode(56), interface.decode(58), interface.decode(57), 60, 24)),
        ("tab-deselected-60", stretch_three(interface.decode(53), interface.decode(55), interface.decode(54), 60, 21)),
        ("belt-frame", build_belt_frame(interface)),
    ]

    out_dir = repo / "assets" / "ui" / "zircon"
    fixed = pack(fixed_items, out_dir / "ui-full-fixed.webp", 2048)
    core_ids = [110, 130, 200, 201, 202, 203, 204, 205, 240, 279]
    core = pack([(f"interface-{idx}", interface.decode(idx)) for idx in core_ids], out_dir / "ui-windows-core.webp", 2048)
    quest_ids = [291, 292, 293]
    quest = pack([(f"interface-{idx}", interface.decode(idx)) for idx in quest_ids], out_dir / "ui-windows-quest.webp", 2048)
    store = pack([("interface-310", interface.decode(310))], out_dir / "ui-window-store.webp", 800)

    sheets = {
        "fixed": "assets/ui/zircon/ui-full-fixed.webp",
        "core": "assets/ui/zircon/ui-windows-core.webp",
        "quest": "assets/ui/zircon/ui-windows-quest.webp",
        "store": "assets/ui/zircon/ui-window-store.webp",
    }
    sprites = {}
    for sheet, placements in [("fixed", fixed), ("core", core), ("quest", quest), ("store", store)]:
        for name, (x, y, width, height) in placements.items():
            sprites[name] = {"sheet": sheet, "x": x, "y": y, "w": width, "h": height}

    asset_js = "window.G = window.G || {};\n\nG.GameUiAssets = Object.freeze(" + json.dumps(
        {"sheets": sheets, "sprites": sprites}, separators=(",", ":")
    ) + ");\n"
    asset_js_path = repo / "js" / "ui" / "game-ui-assets.js"
    asset_js_path.parent.mkdir(parents=True, exist_ok=True)
    asset_js_path.write_text(asset_js, encoding="utf-8")

    save_lossless(gameinter.decode(50), out_dir / "main-panel.webp")
    save_lossless(gameinter.decode(130), out_dir / "minimap-opacity.webp")
    save_lossless(gameinter.decode(132), out_dir / "minimap-size.webp")
    save_lossless(gameinter.decode(137), out_dir / "minimap-bigmap.webp")

    print("Generated exact Zircon browser UI:")
    for name in ["ui-full-fixed.webp", "ui-windows-core.webp", "ui-windows-quest.webp", "ui-window-store.webp"]:
        path = out_dir / name
        print(f"  {path.relative_to(repo)} ({path.stat().st_size:,} bytes)")
    print("  js/ui/game-ui-assets.js")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Directory containing Interface.Zl, GameInter.Zl and GameInter2.Zl")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2], help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        build(args.repo.resolve(), args.source)
    except FileNotFoundError as exc:
        print("\nCould not find one of the original Zircon libraries:")
        print(f"  {exc}")
        print("Run again with --source pointing to the folder that contains the .Zl files.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
