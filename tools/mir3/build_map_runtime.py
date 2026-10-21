#!/usr/bin/env python3
"""Build a browser runtime pack from a MIR3 .map and only the .Zl frames it uses.

Example:
    python tools/mir3/build_map_runtime.py \
        --map "Map/01.map" \
        --map-data "Map Data" \
        --manifest assets/maps/border-village/manifest.json \
        --out assets/maps/border-village/runtime

Requires Pillow. Current source libraries used by ORIGINS X are legacy MIR3 ZL v0/v1
(DXT1/DXT5). The generated runtime format is independent from the source ZL format.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
from collections import defaultdict
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - developer tool dependency
    raise SystemExit("Pillow is required: pip install Pillow") from exc

HEADER_SIZE = 28
CELL_SIZE = 14
EMPTY_FILE = 255
EMPTY_IMAGE = 65536
DEFAULT_PAGE_SIZE = 4096
PADDING = 2


def read_u16(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def parse_map_usage(map_path: Path):
    data = map_path.read_bytes()
    if len(data) < HEADER_SIZE:
        raise ValueError("Invalid MIR3 map header")

    width = read_u16(data, 22)
    height = read_u16(data, 24)
    back_width = width // 2
    back_height = height // 2
    cell_offset = HEADER_SIZE + back_width * back_height * 3
    minimum_size = cell_offset + width * height * CELL_SIZE - 1
    if len(data) < minimum_size:
        raise ValueError(
            f"Invalid MIR3 map size: {len(data)} bytes for {width}x{height}"
        )

    used = defaultdict(set)
    offset = HEADER_SIZE

    for _x in range(back_width):
        for _y in range(back_height):
            library_id = data[offset]
            image_index = read_u16(data, offset + 1)
            offset += 3
            if library_id != EMPTY_FILE:
                used[library_id].add(image_index)

    for x in range(width):
        for y in range(height):
            source = cell_offset + (x * height + y) * CELL_SIZE
            middle_animation = data[source + 1]
            front_animation = data[source + 2]
            front_file = data[source + 3]
            middle_file = data[source + 4]
            middle_image = read_u16(data, source + 5) + 1
            front_image = read_u16(data, source + 7) + 1

            add_animated_frames(used, middle_file, middle_image, middle_animation)
            add_animated_frames(used, front_file, front_image, front_animation)

    return data, width, height, used


def add_animated_frames(used, library_id: int, stored_image: int, animation: int):
    if library_id in (0, EMPTY_FILE) or stored_image in (0, EMPTY_IMAGE):
        return

    base_index = stored_image - 1
    count = (animation & 0x0F) if 1 < animation < 255 else 1
    for frame in range(max(1, count)):
        used[library_id].add(base_index + frame)


class LegacyZlLibrary:
    HEADER_STRUCT = struct.Struct("<ihhhhBhhhhhh")

    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if len(self.data) < 8:
            raise ValueError(f"Invalid ZL library: {path}")

        _, value = struct.unpack_from("<II", self.data, 0)
        self.version = (value >> 25) & 0x7F
        if self.version not in (0, 1):
            raise ValueError(
                f"Unsupported ZL source version {self.version} in {path}. "
                "The runtime format supports it once a source decoder is added."
            )

        count = value if self.version == 0 else value & 0x1FFFFFF
        self.images = [None] * count
        offset = 8

        for index in range(count):
            present = self.data[offset]
            offset += 1
            if not present:
                continue
            self.images[index] = self.HEADER_STRUCT.unpack_from(self.data, offset)
            offset += self.HEADER_STRUCT.size

    def dimensions(self, index: int):
        header = self.header(index)
        return header[1], header[2]

    def header(self, index: int):
        if index < 0 or index >= len(self.images):
            return None
        return self.images[index]

    def decode(self, index: int):
        header = self.header(index)
        if not header:
            return None

        position, width, height = header[0], header[1], header[2]
        if width <= 0 or height <= 0:
            return None

        block_size = 8 if self.version == 0 else 16
        payload_size = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block_size
        payload = self.data[position : position + payload_size]
        if len(payload) != payload_size:
            return None

        dds = make_dds(payload, width, height, self.version)
        return Image.open(io.BytesIO(dds)).convert("RGBA")


def make_dds(payload: bytes, width: int, height: int, version: int) -> bytes:
    fourcc = b"DXT1" if version == 0 else b"DXT5"
    block_size = 8 if version == 0 else 16
    pitch = max(1, (width + 3) // 4) * block_size

    header = bytearray(b"DDS ")
    header += struct.pack("<I", 124)
    header += struct.pack("<I", 0x0002100F)
    header += struct.pack("<III", height, width, pitch)
    header += struct.pack("<II", 0, 0)
    header += b"\0" * 44
    header += struct.pack("<II", 32, 0x4)
    header += fourcc
    header += b"\0" * 20
    header += struct.pack("<I", 0x1000)
    header += b"\0" * 16
    return bytes(header) + payload


class PagePacker:
    """Small deterministic guillotine packer; existing placements never depend on file order."""

    def __init__(self, size: int):
        self.size = size
        self.free = [(0, 0, size, size)]

    def place(self, width: int, height: int):
        best = None

        for i, (x, y, free_w, free_h) in enumerate(self.free):
            if width > free_w or height > free_h:
                continue

            score = (min(free_w - width, free_h - height), max(free_w - width, free_h - height), y, x)
            if best is None or score < best[0]:
                best = (score, i, x, y, free_w, free_h)

        if best is None:
            return None

        _, index, x, y, free_w, free_h = best
        self.free.pop(index)
        right = free_w - width
        bottom = free_h - height

        if right > 0:
            self.free.append((x + width, y, right, height))
        if bottom > 0:
            self.free.append((x, y + height, free_w, bottom))

        self._prune()
        return x, y

    def _prune(self):
        kept = []
        for i, rect in enumerate(self.free):
            x, y, width, height = rect
            contained = False
            for j, other in enumerate(self.free):
                if i == j:
                    continue
                ox, oy, ow, oh = other
                if x >= ox and y >= oy and x + width <= ox + ow and y + height <= oy + oh:
                    contained = True
                    break
            if not contained:
                kept.append(rect)
        self.free = kept


def resolve_library_path(map_data: Path, library_info: dict) -> Path:
    source_path = Path(library_info["path"])
    parts = list(source_path.parts)
    if parts and parts[0].lower() == "map data":
        source_path = Path(*parts[1:])
    return map_data / source_path


def validate_source(manifest: dict, map_data: bytes, width: int, height: int):
    source = manifest.get("source", {})
    sha1 = hashlib.sha1(map_data).hexdigest()

    if source.get("width") and source["width"] != width:
        raise ValueError(f"Manifest width {source['width']} != map width {width}")
    if source.get("height") and source["height"] != height:
        raise ValueError(f"Manifest height {source['height']} != map height {height}")
    if source.get("sha1") and source["sha1"].lower() != sha1:
        raise ValueError(f"Manifest SHA1 {source['sha1']} != map SHA1 {sha1}")

    return sha1


def build(args):
    map_path = args.map.resolve()
    map_data_root = args.map_data.resolve()
    manifest_path = args.manifest.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    map_bytes, width, height, used = parse_map_usage(map_path)
    sha1 = validate_source(manifest, map_bytes, width, height)

    library_defs = {int(item["id"]): item for item in manifest.get("libraries", [])}
    libraries = {}
    frames = []
    missing = []
    max_frame_height = 0

    for library_id in sorted(used):
        if library_id not in library_defs:
            raise ValueError(f"Map uses library id {library_id}, but manifest does not define it")

        info = library_defs[library_id]
        path = resolve_library_path(map_data_root, info)
        if not path.exists():
            raise FileNotFoundError(path)

        library = LegacyZlLibrary(path)
        libraries[library_id] = (info, library)

        for image_index in sorted(used[library_id]):
            header = library.header(image_index)
            if not header or header[1] <= 0 or header[2] <= 0:
                missing.append([library_id, image_index])
                continue

            frame_width, frame_height = header[1], header[2]
            max_frame_height = max(max_frame_height, frame_height)
            frames.append((max(frame_width, frame_height), frame_height, frame_width, library_id, image_index))

    # Largest-first is deterministic and keeps the number of pages low.
    frames.sort(reverse=True)
    packers = []
    placements = {}

    for _, frame_height, frame_width, library_id, image_index in frames:
        padded_width = frame_width + PADDING
        padded_height = frame_height + PADDING
        placement = None

        for page_index, packer in enumerate(packers):
            point = packer.place(padded_width, padded_height)
            if point is not None:
                placement = (page_index, point[0], point[1])
                break

        if placement is None:
            packer = PagePacker(args.page_size)
            point = packer.place(padded_width, padded_height)
            if point is None:
                raise ValueError(f"Frame {library_id}:{image_index} does not fit an atlas page")
            packers.append(packer)
            placement = (len(packers) - 1, point[0], point[1])

        placements[(library_id, image_index)] = [
            placement[0], placement[1], placement[2], frame_width, frame_height
        ]

    by_page = defaultdict(list)
    for key, placement in placements.items():
        by_page[placement[0]].append((key, placement))

    page_names = []
    for page_index in range(len(packers)):
        page_name = f"page-{page_index}.webp"
        page_names.append(page_name)
        canvas = Image.new("RGBA", (args.page_size, args.page_size), (0, 0, 0, 0))

        for (library_id, image_index), placement in by_page[page_index]:
            image = libraries[library_id][1].decode(image_index)
            if image is None:
                continue
            canvas.alpha_composite(image, (placement[1], placement[2]))

        canvas.save(out / page_name, "WEBP", lossless=True, method=1)

    runtime_libraries = {}
    for library_id in sorted(used):
        info, _ = libraries[library_id]
        runtime_libraries[str(library_id)] = {
            "name": info["name"],
            "frames": {
                str(index): placements[(library_id, index)]
                for index in sorted(used[library_id])
                if (library_id, index) in placements
            },
        }

    render_pack = {
        "version": 1,
        "pageSize": args.page_size,
        "pages": page_names,
        "maxFrameHeight": max_frame_height,
        "source": {"map": map_path.name, "width": width, "height": height, "sha1": sha1},
        "libraries": runtime_libraries,
        "missingFrames": missing,
    }

    (out / "render-pack.json").write_text(
        json.dumps(render_pack, separators=(",", ":")), encoding="utf-8"
    )
    (out / map_path.name).write_bytes(map_bytes)

    print(
        f"Built {manifest.get('name', map_path.stem)}: {width}x{height}, "
        f"{len(placements)} frames, {len(page_names)} atlas pages, "
        f"{len(missing)} blank/missing source frames"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--map-data", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    build(parser.parse_args())


if __name__ == "__main__":
    main()
