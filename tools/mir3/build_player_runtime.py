#!/usr/bin/env python3
"""Build a browser runtime sprite pack from one MIR3 player appearance block.

Example:
    python tools/mir3/build_player_runtime.py \
        --library "Data/M-Hum.Zl" \
        --appearance-slot 0 \
        --id human_common_male_base_m001 \
        --race human --class-name common --gender male \
        --appearance-code M001 \
        --out assets/players/human/common/male/base_m001

Requires Pillow. Player appearance blocks use 5000 logical source frames in Zircon.
The output preserves original frame sizes and OffSetX/OffSetY values.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image

# Reuse the exact ZL decoder/packer used by the map runtime builder.
from build_map_runtime import DEFAULT_PAGE_SIZE, PADDING, LegacyZlLibrary, PagePacker

SHAPE_OFFSET = 5000


def pack_frames(library: LegacyZlLibrary, frame_base: int, page_size: int):
    frames = []
    offsets = {}

    for logical_frame in range(SHAPE_OFFSET):
        source_index = frame_base + logical_frame
        header = library.header(source_index)
        if not header or header[1] <= 0 or header[2] <= 0:
            continue

        width, height = header[1], header[2]
        offsets[str(logical_frame)] = {"x": header[3], "y": header[4]}
        frames.append((max(width, height), height, width, logical_frame, source_index))

    frames.sort(reverse=True)
    packers = []
    placements = {}

    for _, height, width, logical_frame, source_index in frames:
        padded_width = width + PADDING
        padded_height = height + PADDING
        placement = None

        for page_index, packer in enumerate(packers):
            point = packer.place(padded_width, padded_height)
            if point is not None:
                placement = (page_index, point[0], point[1])
                break

        if placement is None:
            packer = PagePacker(page_size)
            point = packer.place(padded_width, padded_height)
            if point is None:
                raise ValueError(f"Frame {source_index} ({width}x{height}) does not fit a {page_size}px atlas")
            packers.append(packer)
            placement = (len(packers) - 1, point[0], point[1])

        placements[logical_frame] = [placement[0], placement[1], placement[2], width, height]

    return frames, offsets, placements, len(packers)


def build(args):
    library_path = args.library.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    library = LegacyZlLibrary(library_path)
    frame_base = args.appearance_slot * SHAPE_OFFSET
    if frame_base >= len(library.images):
        raise ValueError(
            f"Appearance slot {args.appearance_slot} starts at {frame_base}, "
            f"but {library_path.name} has only {len(library.images)} entries"
        )

    frames, offsets, placements, page_count = pack_frames(library, frame_base, args.page_size)
    if not frames:
        raise ValueError(f"Appearance slot {args.appearance_slot} has no images in {library_path.name}")

    by_page = defaultdict(list)
    for _, _, _, logical_frame, source_index in frames:
        placement = placements[logical_frame]
        by_page[placement[0]].append((logical_frame, source_index, placement))

    page_names = []
    for page_index in range(page_count):
        page_name = "atlas.webp" if page_count == 1 else f"atlas-{page_index}.webp"
        page_names.append(page_name)
        canvas = Image.new("RGBA", (args.page_size, args.page_size), (0, 0, 0, 0))

        for logical_frame, source_index, placement in by_page[page_index]:
            image = library.decode(source_index)
            if image is None:
                continue
            canvas.alpha_composite(image, (placement[1], placement[2]))

        canvas.save(out / page_name, "WEBP", lossless=True, method=1)

    if page_count == 1:
        frame_cfg = {
            "mode": "atlas",
            "image": page_names[0],
            "rects": {
                str(logical): placement[1:]
                for logical, placement in sorted(placements.items())
            },
        }
    else:
        frame_cfg = {
            "mode": "atlas",
            "images": page_names,
            "rects": {
                str(logical): placement
                for logical, placement in sorted(placements.items())
            },
        }

    manifest = {
        "id": args.id,
        "kind": "player-body",
        "race": args.race,
        "class": args.class_name,
        "gender": args.gender,
        "appearanceCode": args.appearance_code,
        "ready": True,
        "source": {
            "library": library_path.name,
            "appearanceSlot": args.appearance_slot,
            "frameBase": frame_base,
            "shapeOffset": SHAPE_OFFSET,
        },
        "frames": frame_cfg,
        "frameOffsets": offsets,
        "render": {
            "offsetMode": "zircon-frame-offsets",
            "defaultOffset": {"x": 0, "y": 0},
            "scale": 1,
        },
    }

    (out / "manifest.json").write_text(
        json.dumps(manifest, separators=(",", ":")), encoding="utf-8"
    )

    print(
        f"Built {args.appearance_code}: {len(frames)} frames from {library_path.name} "
        f"slot {args.appearance_slot}, {page_count} atlas page(s)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--appearance-slot", type=int, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--race", required=True)
    parser.add_argument("--class-name", required=True)
    parser.add_argument("--gender", required=True)
    parser.add_argument("--appearance-code", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    build(parser.parse_args())


if __name__ == "__main__":
    main()
