#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import struct
from pathlib import Path
from PIL import Image


def read_i32(stream):
    raw = stream.read(4)
    if len(raw) != 4:
        raise EOFError("Unexpected EOF reading int32")
    return struct.unpack("<i", raw)[0]


class CrystalLib:
    def __init__(self, path: Path):
        self.path = path
        self.stream = path.open("rb")
        self.version = read_i32(self.stream)
        if self.version < 2:
            raise ValueError(f"Unsupported Crystal .Lib version {self.version}")
        self.count = read_i32(self.stream)
        self.frame_seek = read_i32(self.stream) if self.version >= 3 else 0
        self.offsets = [read_i32(self.stream) for _ in range(self.count)]

    def close(self):
        self.stream.close()

    def extract(self, index: int):
        if index < 0 or index >= self.count:
            raise IndexError(f"frame {index} outside 0..{self.count-1}")
        offset = self.offsets[index]
        if offset <= 0:
            return None
        self.stream.seek(offset)
        header = self.stream.read(17)
        if len(header) != 17:
            raise EOFError(f"frame {index}: truncated header")
        width, height, x, y, shadow_x, shadow_y, shadow, length = struct.unpack("<hhhhhhBi", header)
        payload = self.stream.read(length)
        if width <= 0 or height <= 0 or length <= 0:
            return None
        raw = gzip.decompress(payload)
        expected = width * height * 4
        if len(raw) < expected:
            raise ValueError(f"frame {index}: decoded {len(raw)} bytes, expected >= {expected}")
        image = Image.frombytes("RGBA", (width, height), raw[:expected], "raw", "BGRA")
        return image, {
            "width": width, "height": height, "offset": [x, y],
            "shadowOffset": [shadow_x, shadow_y], "shadow": shadow,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True, type=Path)
    ap.add_argument("--catalog", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    frame_to_skills: dict[int, list[str]] = {}
    for class_name, class_data in catalog["classes"].items():
        for spell in class_data["spells"]:
            if spell["iconFrameNormal"] is None:
                continue
            for frame in (spell["iconFrameNormal"], spell["iconFramePressed"]):
                frame_to_skills.setdefault(int(frame), []).append(f"{class_name}.{spell['spell']}")

    args.out.mkdir(parents=True, exist_ok=True)
    lib = CrystalLib(args.lib)
    manifest = {"source": args.lib.name, "version": lib.version, "count": lib.count, "frames": {}}
    try:
        for frame in sorted(frame_to_skills):
            extracted = lib.extract(frame)
            if extracted is None:
                raise SystemExit(f"Required MagIcon2 frame {frame} is empty: {frame_to_skills[frame]}")
            image, info = extracted
            target = args.out / f"{frame:05d}.png"
            image.save(target)
            manifest["frames"][str(frame)] = {**info, "png": target.name, "skills": frame_to_skills[frame]}
    finally:
        lib.close()

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Extracted {len(manifest['frames'])} exact MagIcon2 frames from {args.lib}")


if __name__ == "__main__":
    main()
