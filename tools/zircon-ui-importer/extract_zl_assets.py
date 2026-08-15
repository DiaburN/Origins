#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import struct
import zlib
from pathlib import Path

from PIL import Image

CODEC_DXT1 = 0
CODEC_DXT5 = 1
CODEC_BGRA = 2
CODEC_BC7 = 3
CODEC_PNG = 4


def _dds(raw: bytes, width: int, height: int, fourcc: bytes) -> bytes:
    block = 8 if fourcc == b"DXT1" else 16
    linear = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block
    out = bytearray(b"DDS ")
    out += struct.pack("<I", 124)
    out += struct.pack("<I", 0x0002100F)
    out += struct.pack("<I", height)
    out += struct.pack("<I", width)
    out += struct.pack("<I", linear)
    out += struct.pack("<I", 0) * 2
    out += b"\0" * 44
    out += struct.pack("<I", 32)
    out += struct.pack("<I", 4)
    out += fourcc
    out += struct.pack("<I", 0) * 5
    out += struct.pack("<I", 0x1000)
    out += struct.pack("<I", 0) * 4
    return bytes(out) + raw


def _dds_bc7(raw: bytes, width: int, height: int) -> bytes:
    """Wrap raw BC7 blocks in a DDS DX10 header Pillow can decode.

    DXGI_FORMAT_BC7_UNORM = 98, D3D10_RESOURCE_DIMENSION_TEXTURE2D = 3.
    """
    linear = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 16
    out = bytearray(b"DDS ")
    out += struct.pack("<I", 124)
    out += struct.pack("<I", 0x0002100F)
    out += struct.pack("<I", height)
    out += struct.pack("<I", width)
    out += struct.pack("<I", linear)
    out += struct.pack("<I", 0) * 2
    out += b"\0" * 44
    out += struct.pack("<I", 32)
    out += struct.pack("<I", 4)
    out += b"DX10"
    out += struct.pack("<I", 0) * 5
    out += struct.pack("<I", 0x1000)
    out += struct.pack("<I", 0) * 4
    # DDS_HEADER_DXT10
    out += struct.pack("<I", 98)  # DXGI_FORMAT_BC7_UNORM
    out += struct.pack("<I", 3)   # D3D10_RESOURCE_DIMENSION_TEXTURE2D
    out += struct.pack("<I", 0)   # miscFlag
    out += struct.pack("<I", 1)   # arraySize
    out += struct.pack("<I", 0)   # miscFlags2
    return bytes(out) + raw


def _decode(raw: bytes, width: int, height: int, codec: int) -> Image.Image:
    if codec == CODEC_PNG:
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    if codec == CODEC_BGRA:
        return Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
    if codec in (CODEC_DXT1, CODEC_DXT5):
        fourcc = b"DXT1" if codec == CODEC_DXT1 else b"DXT5"
        return Image.open(io.BytesIO(_dds(raw, width, height, fourcc))).convert("RGBA")
    if codec == CODEC_BC7:
        return Image.open(io.BytesIO(_dds_bc7(raw, width, height))).convert("RGBA")
    raise NotImplementedError(f"Unsupported Zircon image codec {codec}")


def _block_size(width: int, height: int, codec: int) -> int:
    blocks = max(1, (width + 3) // 4) * max(1, (height + 3) // 4)
    if codec == CODEC_DXT1:
        return blocks * 8
    if codec in (CODEC_DXT5, CODEC_BC7):
        return blocks * 16
    if codec == CODEC_BGRA:
        return max(0, width) * max(0, height) * 4
    return 0


class LegacyZL:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        metadata_length = struct.unpack_from("<i", self.data, 0)[0]
        metadata = self.data[4:4 + metadata_length]
        packed = struct.unpack_from("<i", metadata, 0)[0]
        self.count = packed & 0x1FFFFFF
        self.version = (packed >> 25) & 0x7F
        if self.version == 0:
            self.count = packed

        p = 4
        fmt = "<ihhhhBhhhhhh"
        size = struct.calcsize(fmt)
        self.images = [None] * self.count
        keys = (
            "position", "width", "height", "offset_x", "offset_y", "shadow_type",
            "shadow_width", "shadow_height", "shadow_offset_x", "shadow_offset_y",
            "overlay_width", "overlay_height",
        )
        for index in range(self.count):
            present = metadata[p]
            p += 1
            if not present:
                continue
            values = struct.unpack_from(fmt, metadata, p)
            p += size
            self.images[index] = dict(zip(keys, values))

    def extract(self, index: int):
        info = self.images[index]
        if not info or info["width"] <= 0 or info["height"] <= 0:
            return None, info
        codec = CODEC_DXT1 if self.version == 0 else CODEC_DXT5
        length = _block_size(info["width"], info["height"], codec)
        raw = self.data[info["position"]:info["position"] + length]
        return _decode(raw, info["width"], info["height"], codec), {
            **info,
            "codec": codec,
            "version": self.version,
        }


class ZL2:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        p = 3
        self.container_version, self.image_count, self.atlas_count = struct.unpack_from("<iii", self.data, p)
        p += 12
        self.default_compression = self.data[p]
        self.flags = self.data[p + 1]
        p += 4
        self.metadata_offset = struct.unpack_from("<q", self.data, p)[0]
        p += 8
        self.metadata_size = struct.unpack_from("<i", self.data, p)[0]
        p += 4
        self.index_offset = struct.unpack_from("<q", self.data, p)[0]
        p += 8
        self.index_size = struct.unpack_from("<i", self.data, p)[0]

        index_data = self.data[self.index_offset:self.index_offset + self.index_size]
        q = 0
        entry_count = struct.unpack_from("<i", index_data, q)[0]
        q += 4
        self.entries = {}
        for _ in range(entry_count):
            entry_type = index_data[q]
            q += 1
            entry_id, uncompressed, compressed = struct.unpack_from("<iii", index_data, q)
            q += 12
            offset = struct.unpack_from("<q", index_data, q)[0]
            q += 8
            compression = index_data[q]
            codec = index_data[q + 1]
            q += 2
            self.entries[entry_id] = {
                "type": entry_type,
                "id": entry_id,
                "uncompressed": uncompressed,
                "compressed": compressed,
                "offset": offset,
                "compression": compression,
                "codec": codec,
            }

        metadata = self.data[self.metadata_offset:self.metadata_offset + self.metadata_size]
        q = 0
        self.version, self.count, self.atlas_group_count, self.atlas_page_size = struct.unpack_from("<iiii", metadata, q)
        q += 16
        self.images = [None] * self.count
        for index in range(self.count):
            present = metadata[q]
            q += 1
            if not present:
                continue

            position, width, height, offset_x, offset_y = struct.unpack_from("<ihhhh", metadata, q)
            q += 12
            shadow_type = metadata[q]
            q += 1
            shadow_width, shadow_height, shadow_offset_x, shadow_offset_y, overlay_width, overlay_height = struct.unpack_from("<hhhhhh", metadata, q)
            q += 12
            atlas_page = struct.unpack_from("<i", metadata, q)[0]
            q += 4
            source_rectangle = struct.unpack_from("<hhhh", metadata, q)
            q += 8
            visible_bounds = struct.unpack_from("<hhhh", metadata, q)
            q += 8
            image_codec, shadow_codec, overlay_codec = metadata[q:q + 3]
            q += 3
            image_runtime, shadow_runtime, overlay_runtime = metadata[q:q + 3]
            q += 3
            sizes = struct.unpack_from("<iiiiiiiii", metadata, q)
            q += 36

            self.images[index] = {
                "position": position,
                "width": width,
                "height": height,
                "offset_x": offset_x,
                "offset_y": offset_y,
                "shadow_type": shadow_type,
                "shadow_width": shadow_width,
                "shadow_height": shadow_height,
                "shadow_offset_x": shadow_offset_x,
                "shadow_offset_y": shadow_offset_y,
                "overlay_width": overlay_width,
                "overlay_height": overlay_height,
                "atlas_page": atlas_page,
                "source_rectangle": source_rectangle,
                "visible_bounds": visible_bounds,
                "codec": image_codec,
                "runtime_preference": image_runtime,
                "stored_image_size": sizes[0],
                "image_bc7_size": sizes[1],
                "image_fallback_size": sizes[2],
            }

    def payload(self, entry_id: int) -> bytes:
        entry = self.entries[entry_id]
        raw = self.data[entry["offset"]:entry["offset"] + entry["compressed"]]
        if entry["compression"] == 0:
            return raw
        try:
            return zlib.decompress(raw, -15)
        except zlib.error:
            return zlib.decompress(raw)

    def extract(self, index: int):
        info = self.images[index]
        if not info or info["width"] <= 0 or info["height"] <= 0:
            return None, info

        payload = self.payload(info["position"])
        codec = info["codec"]
        if codec == CODEC_PNG:
            length = info["stored_image_size"]
            raw = payload[:length] if length else payload
        elif codec in (CODEC_DXT1, CODEC_DXT5, CODEC_BGRA, CODEC_BC7):
            length = info["stored_image_size"] or _block_size(info["width"], info["height"], codec)
            raw = payload[:length]
        else:
            raise NotImplementedError(f"Unsupported image codec {codec} at image {index}")

        return _decode(raw, info["width"], info["height"], codec), {
            **info,
            "version": self.version,
        }


def open_zl(path: Path):
    return ZL2(path) if path.read_bytes()[:3] == b"ZL2" else LegacyZL(path)


def parse_ids(spec: str | None, count: int):
    if not spec:
        return list(range(count))
    result = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = map(int, part.split("-", 1))
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    return sorted(index for index in result if 0 <= index < count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ids", help="Comma separated image IDs/ranges, e.g. 0-300,358,360")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    library = open_zl(args.input)
    manifest = {
        "source": args.input.name,
        "count": library.count,
        "version": library.version,
        "images": {},
    }

    for index in parse_ids(args.ids, library.count):
        try:
            image, info = library.extract(index)
        except NotImplementedError as error:
            print("SKIP", index, error)
            continue
        if image is None:
            continue
        target = args.output / f"{index:05d}.png"
        image.save(target)
        manifest["images"][str(index)] = {
            **info,
            "png": target.name,
            "size": [image.width, image.height],
        }

    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(args.input.name, "->", len(manifest["images"]), "images")


if __name__ == "__main__":
    main()
